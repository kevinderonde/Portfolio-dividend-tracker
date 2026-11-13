"""Serve and register the bundled PDT Lovelace card."""
import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig

_LOGGER = logging.getLogger(__name__)
URL = "/portfolio_dividend_tracker/pdt-dashboard-card.js"
RESOURCE_URL = URL + "?v=040"

async def async_setup_dashboard(hass):
    """Register a static JS endpoint and add its Lovelace resource if supported."""
    if not hass.data.get("pdt_dashboard_static_registered"):
        try:
            await hass.http.async_register_static_paths([
                StaticPathConfig(URL, str(Path(__file__).parent / "frontend" / "pdt-dashboard-card.js"), False)
            ])
            hass.data["pdt_dashboard_static_registered"] = True
        except Exception:
            _LOGGER.exception("Could not serve PDT dashboard card")
            return

    try:
        lovelace = hass.data.get("lovelace")
        resources = getattr(lovelace, "resources", None)
        if resources is None:
            _LOGGER.warning("Lovelace resources unavailable; add %s manually as JavaScript module", RESOURCE_URL)
            return
        if not getattr(resources, "loaded", True):
            await resources.async_load()
        items = resources.async_items()
        for item in items:
            url = item.get("url", "")
            if url.split("?", 1)[0] == URL:
                if url != RESOURCE_URL:
                    await resources.async_update_item(item["id"], {"url": RESOURCE_URL, "res_type": "module"})
                return
        await resources.async_create_item({"url": RESOURCE_URL, "res_type": "module"})
    except Exception:
        # YAML-mode Lovelace or API differences should not prevent the integration loading.
        _LOGGER.exception("Could not automatically register PDT card. Add %s manually as a JavaScript module", RESOURCE_URL)
