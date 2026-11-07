"""Portfolio Dividend Tracker integration."""
import json
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import PDTApi
from .const import DOMAIN, ALLOWED_RESOURCES
from .coordinator import PDTCoordinator

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = PDTApi(async_get_clientsession(hass), entry.data["token"])
    coordinator = PDTCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "get_data")
    return unloaded
