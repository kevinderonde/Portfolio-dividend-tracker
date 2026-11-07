import voluptuous as vol
from aiohttp import ClientError, ClientTimeout
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, API_URL

class PDTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input["token"].strip()
            try:
                async with async_get_clientsession(self.hass).get(API_URL, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=ClientTimeout(total=20)) as response:
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
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required("token"): str}), errors=errors)
