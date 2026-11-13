"""Read-only PDT REST API client."""
from urllib.parse import quote
from collections.abc import Callable, Awaitable
from aiohttp import ClientError, ClientTimeout
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from .const import BASE_URL, ALLOWED_RESOURCES

class PDTApi:
    def __init__(self, session, token=None, token_provider=None):
        self.session = session
        self.token = token
        self.token_provider = token_provider

    async def get(self, resource, path="", params=None):
        if resource not in ALLOWED_RESOURCES:
            raise HomeAssistantError("Onbekende PDT-resource")
        path = (path or "").strip("/")
        segments = path.split("/") if path else []
        if any(s in (".", "..") or not s or "?" in s or "#" in s for s in segments):
            raise HomeAssistantError("Ongeldig PDT-pad")
        suffix = "/".join(quote(s, safe="") for s in segments)
        url = f"{BASE_URL}/{resource}" + (f"/{suffix}" if suffix else "")
        token = await self.token_provider() if self.token_provider else self.token
        try:
            async with self.session.get(
                url, params=params or None,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=ClientTimeout(total=35),
                allow_redirects=False,
            ) as response:
                if response.status in (401, 403):
                    raise ConfigEntryAuthFailed("PDT-token geweigerd of onvoldoende rechten")
                if response.status >= 300:
                    raise HomeAssistantError(f"PDT API HTTP {response.status}")
                return await response.json(content_type=None)
        except ConfigEntryAuthFailed:
            raise
        except (ClientError, TimeoutError, ValueError) as err:
            raise HomeAssistantError(f"PDT API-verzoek mislukt: {type(err).__name__}") from err
