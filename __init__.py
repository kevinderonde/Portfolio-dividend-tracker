"""Portfolio Dividend Tracker integration."""
from datetime import date, timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PDTApi
from .const import DOMAIN, ALLOWED_RESOURCES, CLIENT_ID, AUTHORIZE_URL, TOKEN_URL
from homeassistant.helpers import config_entry_oauth2_flow
from .coordinator import PDTCoordinator
from .dashboard import async_setup_dashboard

PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the shared public PDT OAuth app with Home Assistant."""
    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN,
        config_entry_oauth2_flow.LocalOAuth2ImplementationWithPkce(
            hass, DOMAIN, CLIENT_ID, authorize_url=AUTHORIZE_URL, token_url=TOKEN_URL,
        ),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if "token" in entry.data and isinstance(entry.data["token"], str):
        api = PDTApi(async_get_clientsession(hass), token=entry.data["token"])
    else:
        implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
        oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

        async def get_access_token():
            await oauth_session.async_ensure_token_valid()
            return oauth_session.token["access_token"]

        api = PDTApi(async_get_clientsession(hass), token_provider=get_access_token)
    coordinator = PDTCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, "get_history"):
        history_schema = vol.Schema({
            vol.Required("period", default="ytd"): vol.In(("1m", "3m", "ytd", "1y", "max")),
            vol.Optional("group_by", default="auto"): vol.In(("auto", "day", "week", "month", "quarter", "year")),
            vol.Optional("entry_id"): str,
        })

        async def handle_history(call):
            entries = hass.data.get(DOMAIN, {})
            requested = call.data.get("entry_id")
            selected = entries.get(requested) if requested else next(iter(entries.values()), None)
            if selected is None:
                raise HomeAssistantError("Geen actieve PDT-integratie gevonden")
            today = date.today()
            period = call.data["period"]
            if period == "1m":
                start = today - timedelta(days=30)
            elif period == "3m":
                start = today - timedelta(days=90)
            elif period == "1y":
                start = today - timedelta(days=365)
            elif period == "ytd":
                start = date(today.year, 1, 1)
            else:
                start = None
            params = {"dateTo": today.isoformat()}
            if start is not None:
                params["dateFrom"] = start.isoformat()
            if call.data["group_by"] != "auto":
                params["groupBy"] = call.data["group_by"]
            result = await selected.api.get("portfolio", "performance/chart", params)
            if not isinstance(result, dict):
                raise HomeAssistantError("Onverwachte historische PDT-response")
            return result

        hass.services.async_register(
            DOMAIN, "get_history", handle_history,
            schema=history_schema, supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, "get_data"):
        schema = vol.Schema({
            vol.Required("resource"): vol.In(ALLOWED_RESOURCES),
            vol.Optional("path", default=""): str,
            vol.Optional("parameters", default={}): dict,
            vol.Optional("entry_id"): str,
        })

        async def handle_get(call):
            entries = hass.data.get(DOMAIN, {})
            requested = call.data.get("entry_id")
            selected = entries.get(requested) if requested else next(iter(entries.values()), None)
            if selected is None:
                raise HomeAssistantError("Geen actieve PDT-integratie gevonden")
            payload = await selected.api.get(
                call.data["resource"], call.data.get("path", ""), call.data.get("parameters", {})
            )
            if not isinstance(payload, (dict, list)):
                return {"data": payload}
            if isinstance(payload, list):
                return {"data": payload}
            return payload

        hass.services.async_register(DOMAIN, "get_data", handle_get, schema=schema, supports_response=SupportsResponse.ONLY)

    # Register the bundled Lovelace card, but never break portfolio sensors if UI setup fails.
    await async_setup_dashboard(hass)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "get_data")
            hass.services.async_remove(DOMAIN, "get_history")
    return unloaded
