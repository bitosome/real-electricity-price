"""Sensor platform for real_electricity_price."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_change

from .entity import RealElectricityPriceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="real_electricity_price",
        name="Real Electricity Price",
        icon="mdi:currency-eur",
        native_unit_of_measurement="EUR/kWh",
    ),
    SensorEntityDescription(
        key="real_electricity_prices_today",
        name="Real Electricity Prices Today",
        icon="mdi:currency-eur",
    ),
    SensorEntityDescription(
        key="real_electricity_prices_tomorrow",
        name="Real Electricity Prices Tomorrow",
        icon="mdi:currency-eur",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: RealElectricityPriceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        RealElectricityPriceSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class RealElectricityPriceSensor(RealElectricityPriceEntity, SensorEntity):
    """Real Electricity Price Sensor class."""

    def __init__(
        self,
        coordinator: RealElectricityPriceDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        
        # Get device name from config (options override data)
        config = {**coordinator.config_entry.data, **coordinator.config_entry.options}
        device_name = config.get(CONF_NAME, "Real Electricity Price")
        
        # Create entity name using device name as prefix
        if entity_description.key == "real_electricity_price":
            entity_suffix = "current_price"
        elif "today" in entity_description.key:
            entity_suffix = "today"
        elif "tomorrow" in entity_description.key:
            entity_suffix = "tomorrow"
        else:
            entity_suffix = entity_description.key
            
        # Set the entity name to device_name + suffix
        self._attr_name = f"{device_name} {entity_suffix.replace('_', ' ').title()}"
        
        # Determine data key based on entity description
        if "today" in entity_description.key:
            self._data_key = "today"
            self._sensor_type = "today_data"
        elif "tomorrow" in entity_description.key:
            self._data_key = "tomorrow"
            self._sensor_type = "tomorrow_data"
        else:
            # This is the current price sensor
            self._data_key = "today"
            self._sensor_type = "current_price"
            
        # Track hourly updates for current price sensor
        self._hourly_update_unsub = None

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        await super().async_added_to_hass()
        
        # For current price sensor, set up hourly updates
        if self._sensor_type == "current_price":
            self._setup_hourly_updates()

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        
        # Clean up hourly update tracking
        if self._hourly_update_unsub:
            self._hourly_update_unsub()
            self._hourly_update_unsub = None

    def _setup_hourly_updates(self) -> None:
        """Set up hourly updates for current price sensor."""
        if self._sensor_type != "current_price":
            return
            
        # Track time changes at the start of each hour (minute=0, second=0)
        self._hourly_update_unsub = async_track_time_change(
            self.hass,
            self._hourly_update_callback,
            minute=0,
            second=0
        )

    @callback
    def _hourly_update_callback(self, now: datetime.datetime) -> None:
        """Handle hourly update for current price sensor."""
        if self._sensor_type == "current_price":
            # Force update of the sensor state to reflect new current hour price
            self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data or self._data_key not in self.coordinator.data:
            return None

        day_data = self.coordinator.data[self._data_key]
        hourly_prices = day_data.get("hourly_prices", [])
        if not hourly_prices:
            return None

        now = datetime.datetime.now(datetime.UTC)

        if self._sensor_type == "current_price":
            # Return the current hour's price for the current price sensor
            for price in hourly_prices:
                start = datetime.datetime.fromisoformat(price["start_time"])
                end = datetime.datetime.fromisoformat(price["end_time"])
                if start <= now < end:
                    return price["actual_price"]
            return None
        elif self._sensor_type == "today_data":
            # For today's sensor, return current hour's price as the main value
            for price in hourly_prices:
                start = datetime.datetime.fromisoformat(price["start_time"])
                end = datetime.datetime.fromisoformat(price["end_time"])
                if start <= now < end:
                    return price["actual_price"]
            return None
        elif self._sensor_type == "tomorrow_data":
            # For tomorrow's sensor, return the first hour's price
            if hourly_prices:
                return hourly_prices[0]["actual_price"]
            return None
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._data_key not in self.coordinator.data:
            return {}

        day_data = self.coordinator.data[self._data_key]
        hourly_prices = day_data.get("hourly_prices", [])

        if self._sensor_type == "current_price":
            # For current price sensor, return minimal attributes - no future data
            now = datetime.datetime.now(datetime.UTC)
            current_hour_data = None
            for price in hourly_prices:
                start = datetime.datetime.fromisoformat(price["start_time"])
                end = datetime.datetime.fromisoformat(price["end_time"])
                if start <= now < end:
                    current_hour_data = price
                    break
            
            # Return only basic current hour information
            attributes = {
                "date": day_data.get("date", self._data_key),
                "hour_start": current_hour_data["start_time"] if current_hour_data else None,
                "hour_end": current_hour_data["end_time"] if current_hour_data else None,
                "nord_pool_price": current_hour_data["nord_pool_price"] if current_hour_data else None,
            }
            
            return attributes
        else:
            # For today/tomorrow sensors, return all hourly data
            return {
                "hourly_prices": hourly_prices,
                "date": day_data.get("date", self._data_key),
            }
