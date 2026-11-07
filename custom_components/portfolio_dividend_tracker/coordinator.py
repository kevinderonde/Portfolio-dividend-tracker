"""PDT summary polling coordinator."""
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from .const import UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

class PDTCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api):
        super().__init__(hass, _LOGGER, name="Portfolio Dividend Tracker", update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES))
        self.api = api

    async def _async_update_data(self):
        try:
            payload = await self.api.get("portfolio")
            summary = payload.get("data", {}).get("summary") if isinstance(payload, dict) else None
            if not isinstance(summary, dict):
                raise UpdateFailed("Onverwachte PDT portfolio response")
            return summary
        except ConfigEntryAuthFailed:
            raise
        except HomeAssistantError as err:
            raise UpdateFailed(str(err)) from err
