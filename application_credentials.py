"""PKCE OAuth2 implementation for Portfolio Dividend Tracker."""
from homeassistant.components.application_credentials import ClientCredential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2ImplementationWithPkce
from .const import AUTHORIZE_URL, TOKEN_URL

async def async_get_auth_implementation(hass: HomeAssistant, auth_domain: str, credential: ClientCredential):
    return LocalOAuth2ImplementationWithPkce(
        hass, auth_domain, credential.client_id,
        authorize_url=AUTHORIZE_URL, token_url=TOKEN_URL,
        client_secret=credential.client_secret or "",
    )

async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    return {"console_url": "https://build.portfoliodividendtracker.com/"}
