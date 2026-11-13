"""PDT OAuth2 (PKCE) and legacy API-token configuration."""
import logging
import voluptuous as vol
from aiohttp import ClientError, ClientTimeout
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, API_URL

_LOGGER = logging.getLogger(__name__)

class PDTConfigFlow(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    DOMAIN = DOMAIN
    VERSION = 1

    @property
    def logger(self):
        return _LOGGER

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_menu(step_id="user", menu_options=["pick_implementation", "api_token"])
        return await self.async_step_pick_implementation()

    async def async_step_api_token(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input["token"].strip()
            try:
                async with async_get_clientsession(self.hass).get(
                    API_URL, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                    timeout=ClientTimeout(total=20),
                ) as response:
                    if response.status in (401, 403):
                        errors["base"] = "invalid_auth"
                    elif response.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        payload = await response.json(content_type=None)
                        if not isinstance(payload, dict) or not isinstance(payload.get("data", {}).get("summary"), dict):
                            errors["base"] = "invalid_response"
                        else:
                            await self.async_set_unique_id("pdt_portfolio")
                            self._abort_if_unique_id_configured()
                            return self.async_create_entry(title="Portfolio Dividend Tracker", data={"token": token})
            except (ClientError, TimeoutError, ValueError, TypeError):
                errors["base"] = "cannot_connect"
        return self.async_show_form(step_id="api_token", data_schema=vol.Schema({vol.Required("token"): str}), errors=errors)

    async def async_oauth_create_entry(self, data):
        await self.async_set_unique_id("pdt_portfolio")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Portfolio Dividend Tracker", data=data)
