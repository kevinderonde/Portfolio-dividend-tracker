from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

FIELDS = {
    "currentWorth": "Portefeuillewaarde",
    "totalGains": "Totaal resultaat",
    "unrealisedGains": "Ongerealiseerd resultaat",
    "realisedGains": "Gerealiseerd resultaat",
    "dividendsReceived": "Ontvangen dividend",
    "dividendsReceivedWithoutTax": "Bruto dividend",
    "dividendsTax": "Dividendbelasting",
    "dividendsCosts": "Dividendkosten",
    "totalBought": "Totaal aangekocht",
    "cash": "Cash",
    "totalGainsProduct": "Resultaat beleggingen",
    "unrealisedGainsProduct": "Ongerealiseerd resultaat beleggingen",
    "realisedGainsProduct": "Gerealiseerd resultaat beleggingen",
    "totalBoughtPriceTotal": "Totale aankoopprijs",
    "transactionsTaxes": "Transactiebelasting",
    "dividendsGains": "Dividendresultaat",
    "fxConversionCosts": "Valutawisselkosten",
    "fxConversionTaxes": "Valutawisselbelasting",
    "bookingCosts": "Boekingskosten",
    "bookingTaxes": "Boekingsbelasting",
    "brokerIncome": "Brokerinkomsten",
    "totalSoldPriceTotal": "Totale verkoopprijs",
    "totalSoldReceived": "Verkoopopbrengsten",
    "transactionsCosts": "Transactiekosten",
    "brokerCosts": "Brokerkosten",
    "totalGainsExchangeRate": "Valutaresultaat",
    "unrealisedGainsExchangeRate": "Ongerealiseerd valutaresultaat",
    "realisedGainsExchangeRate": "Gerealiseerd valutaresultaat",
    "totalBoughtShares": "Gekochte aandelen",
    "totalSoldShares": "Verkochte aandelen",
    "totalBoughtExpended": "Aankoopuitgaven",
    "totalBoughtExpended": "Aankoopuitgaven",
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(PDTSensor(coordinator, entry.entry_id, key, name) for key, name in FIELDS.items())

class PDTSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id, key, name):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name="Portfolio Dividend Tracker", manufacturer="Portfolio Dividend Tracker")
        if key not in ("totalBoughtShares", "totalSoldShares"):
            self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        value = self.coordinator.data.get(self.key)
        if isinstance(value, dict):
            value = value.get("value")
        if value is None or isinstance(value, bool):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @property
    def native_unit_of_measurement(self):
        value = self.coordinator.data.get(self.key)
        if isinstance(value, dict):
            return value.get("currency") or None
        return None
