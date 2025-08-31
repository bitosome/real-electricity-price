"""Sensor platform for real_electricity_price."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_change

from .entity import RealElectricityPriceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)

# Sensor type constants for better maintainability
SENSOR_TYPE_CURRENT_PRICE = "current_price"
SENSOR_TYPE_TODAY_DATA = "today_data"
SENSOR_TYPE_TOMORROW_DATA = "tomorrow_data"
SENSOR_TYPE_AGGREGATE_TODAY = "aggregate_today"
SENSOR_TYPE_AGGREGATE_TOMORROW = "aggregate_tomorrow"
SENSOR_TYPE_LAST_SYNC = "last_sync"
SENSOR_TYPE_CURRENT_TARIFF = "current_tariff"

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="real_electricity_price",
        name="Real Electricity Price",
        icon="mdi:currency-eur",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR/kWh",
    ),
    SensorEntityDescription(
        key="real_electricity_prices_today",
        name="Hourly Prices Today",
        icon="mdi:chart-line",
    ),
    SensorEntityDescription(
        key="real_electricity_prices_tomorrow",
        name="Hourly Prices Tomorrow", 
        icon="mdi:chart-line",
    ),
    SensorEntityDescription(
        key="real_electricity_price_max_today",
        name="Maximum Price Today",
        icon="mdi:arrow-up-bold",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR/kWh",
    ),
    SensorEntityDescription(
        key="real_electricity_price_min_today",
        name="Minimum Price Today",
        icon="mdi:arrow-down-bold",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR/kWh",
    ),
    SensorEntityDescription(
        key="real_electricity_price_max_tomorrow",
        name="Maximum Price Tomorrow",
        icon="mdi:arrow-up-bold",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR/kWh",
    ),
    SensorEntityDescription(
        key="real_electricity_price_min_tomorrow",
        name="Minimum Price Tomorrow",
        icon="mdi:arrow-down-bold",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR/kWh",
    ),
    SensorEntityDescription(
        key="real_electricity_price_last_sync",
        name="Last Data Sync",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="real_electricity_price_current_tariff",
        name="Current Tariff",
        icon="mdi:weather-night",
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
        
        _LOGGER.debug("Initializing sensor: %s", entity_description.key)
        
        # Get device name from config (options override data)
        config = {**coordinator.config_entry.data, **coordinator.config_entry.options}
        device_name = config.get(CONF_NAME, "Real Electricity Price")
        
        # Configure sensor properties based on key
        self._configure_sensor_properties(entity_description.key, device_name)
        
        # Set up hourly updates for current price sensor
        self._hourly_update_unsub = None
        if self._sensor_type == SENSOR_TYPE_CURRENT_PRICE:
            self._setup_hourly_updates()

    def _configure_sensor_properties(self, key: str, device_name: str) -> None:
        """Configure sensor properties based on entity key."""
        # Map entity keys to sensor types and properties
        sensor_config = {
            "real_electricity_price": {
                "suffix": "current_price",
                "sensor_type": SENSOR_TYPE_CURRENT_PRICE,
                "data_key": "today",
                "aggregate_mode": None,
            },
            "real_electricity_prices_today": {
                "suffix": "hourly prices today",
                "sensor_type": SENSOR_TYPE_TODAY_DATA,
                "data_key": "today",
                "aggregate_mode": None,
            },
            "real_electricity_prices_tomorrow": {
                "suffix": "hourly prices tomorrow",
                "sensor_type": SENSOR_TYPE_TOMORROW_DATA,
                "data_key": "tomorrow",
                "aggregate_mode": None,
            },
            "real_electricity_price_max_today": {
                "suffix": "max today",
                "sensor_type": SENSOR_TYPE_AGGREGATE_TODAY,
                "data_key": "today",
                "aggregate_mode": "max",
            },
            "real_electricity_price_min_today": {
                "suffix": "min today",
                "sensor_type": SENSOR_TYPE_AGGREGATE_TODAY,
                "data_key": "today",
                "aggregate_mode": "min",
            },
            "real_electricity_price_max_tomorrow": {
                "suffix": "max tomorrow",
                "sensor_type": SENSOR_TYPE_AGGREGATE_TOMORROW,
                "data_key": "tomorrow",
                "aggregate_mode": "max",
            },
            "real_electricity_price_min_tomorrow": {
                "suffix": "min tomorrow",
                "sensor_type": SENSOR_TYPE_AGGREGATE_TOMORROW,
                "data_key": "tomorrow",
                "aggregate_mode": "min",
            },
            "real_electricity_price_last_sync": {
                "suffix": "last sync",
                "sensor_type": SENSOR_TYPE_LAST_SYNC,
                "data_key": None,
                "aggregate_mode": None,
            },
            "real_electricity_price_current_tariff": {
                "suffix": "current tariff",
                "sensor_type": SENSOR_TYPE_CURRENT_TARIFF,
                "data_key": None,
                "aggregate_mode": None,
            },
        }
        
        config = sensor_config.get(key, {
            "suffix": key,
            "sensor_type": SENSOR_TYPE_CURRENT_PRICE,
            "data_key": "today",
            "aggregate_mode": None,
        })
        
        # Set sensor properties
        self._sensor_type = config["sensor_type"]
        self._data_key = config["data_key"]
        self._aggregate_mode = config["aggregate_mode"]
        
        # Set entity name
        entity_suffix = config["suffix"]
        self._attr_name = f"{device_name} {entity_suffix.replace('_', ' ').title()}"

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        
        # Clean up hourly update tracking
        if self._hourly_update_unsub:
            self._hourly_update_unsub()
            self._hourly_update_unsub = None

    def _setup_hourly_updates(self) -> None:
        """Set up hourly updates for current price sensor."""
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
        # Force update of the sensor state to reflect new current hour price
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        _LOGGER.debug("native_value called for sensor type: %s", self._sensor_type)
        
        if self._sensor_type == SENSOR_TYPE_LAST_SYNC:
            return self._get_last_sync_value()
        elif self._sensor_type == SENSOR_TYPE_CURRENT_TARIFF:
            return self._get_current_tariff_value()
        
        # For regular price sensors, ensure we have data
        if not self.coordinator.data or self._data_key not in self.coordinator.data:
            return None

        day_data = self.coordinator.data[self._data_key]
        hourly_prices = day_data.get("hourly_prices", [])
        if not hourly_prices:
            return None

        if self._sensor_type == SENSOR_TYPE_CURRENT_PRICE:
            return self._get_current_price_value(hourly_prices)
        elif self._sensor_type == SENSOR_TYPE_TODAY_DATA:
            return self._get_current_price_value(hourly_prices)
        elif self._sensor_type == SENSOR_TYPE_TOMORROW_DATA:
            return hourly_prices[0]["actual_price"] if hourly_prices else None
        elif self._sensor_type in (SENSOR_TYPE_AGGREGATE_TODAY, SENSOR_TYPE_AGGREGATE_TOMORROW):
            return self._get_aggregate_value(hourly_prices)
        
        return None

    def _get_last_sync_value(self) -> datetime.datetime:
        """Get the last sync timestamp."""
        _LOGGER.debug("Last sync sensor: coordinator.data = %s", self.coordinator.data)
        if self.coordinator.data and "last_sync" in self.coordinator.data:
            _LOGGER.debug("Last sync found: %s", self.coordinator.data["last_sync"])
            return self.coordinator.data["last_sync"]
        # Fallback to current time if no sync data available
        _LOGGER.debug("No last sync data found, using current time")
        return datetime.datetime.now(datetime.UTC)

    def _get_current_tariff_value(self) -> str:
        """Determine the current tariff (day/night)."""
        current_time = datetime.datetime.now(datetime.UTC)
        _LOGGER.debug("Current tariff calculation: current_time = %s", current_time)

        # Check if today is a holiday or weekend
        today_data = self.coordinator.data.get("today", {})
        is_holiday = today_data.get("is_holiday", False)
        is_weekend = today_data.get("is_weekend", False)

        _LOGGER.debug("Holiday/Weekend check: is_holiday = %s, is_weekend = %s", is_holiday, is_weekend)

        # If it's a holiday or weekend, always return night tariff
        if is_holiday or is_weekend:
            _LOGGER.debug("Returning 'night' tariff due to %s", "holiday" if is_holiday else "weekend")
            return "night"

        # Check the block aggregates for the current time
        block_aggregates = today_data.get("blockPriceAggregates", [])
        if block_aggregates:
            block_names = [block.get("blockName") for block in block_aggregates]
            _LOGGER.debug("Block aggregates: %s", block_names)

            for block in block_aggregates:
                start_str = block.get("deliveryStart")
                end_str = block.get("deliveryEnd")

                if start_str and end_str:
                    start_time = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    end_time = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00'))

                    _LOGGER.debug("Checking block %s: %s to %s", block.get('blockName'), start_time, end_time)

                    if start_time <= current_time < end_time:
                        block_name = block.get("blockName", "")
                        tariff = "day" if block_name == "Peak" else "night"
                        _LOGGER.debug("Found matching block: %s -> %s", block_name, tariff)
                        return tariff

            _LOGGER.debug("No matching block found, defaulting to 'night'")
            return "night"
        else:
            _LOGGER.debug("No block aggregates found, defaulting to 'night'")
            return "night"

    def _get_current_price_value(self, hourly_prices: list[dict[str, Any]]) -> float | None:
        """Get the current hour's price."""
        now = datetime.datetime.now(datetime.UTC)
        for price in hourly_prices:
            start = datetime.datetime.fromisoformat(price["start_time"])
            end = datetime.datetime.fromisoformat(price["end_time"])
            if start <= now < end:
                return price["actual_price"]
        return None

    def _get_aggregate_value(self, hourly_prices: list[dict[str, Any]]) -> float | None:
        """Get min/max aggregate value for the day."""
        prices = [p.get("actual_price") for p in hourly_prices if p.get("actual_price") is not None]
        if not prices:
            return None
        return max(prices) if self._aggregate_mode == "max" else min(prices)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._data_key not in self.coordinator.data:
            return self._get_special_sensor_attributes()

        day_data = self.coordinator.data[self._data_key]
        hourly_prices = day_data.get("hourly_prices", [])

        if self._sensor_type == SENSOR_TYPE_CURRENT_PRICE:
            return self._get_current_price_attributes(hourly_prices, day_data)
        elif self._sensor_type in (SENSOR_TYPE_TODAY_DATA, SENSOR_TYPE_TOMORROW_DATA):
            return self._get_price_data_attributes(hourly_prices, day_data)
        elif self._sensor_type in (SENSOR_TYPE_AGGREGATE_TODAY, SENSOR_TYPE_AGGREGATE_TOMORROW):
            return self._get_aggregate_attributes(hourly_prices, day_data)
        
        return {}

    def _get_special_sensor_attributes(self) -> dict[str, Any]:
        """Get attributes for special sensors (last_sync, current_tariff)."""
        if self._sensor_type == SENSOR_TYPE_LAST_SYNC:
            return {
                "last_update_time": self.coordinator.last_update_success_time,
                "coordinator_available": self.coordinator.last_update_success,
            }
        elif self._sensor_type == SENSOR_TYPE_CURRENT_TARIFF:
            config = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
            night_start = config.get("night_price_start_hour", 22)
            night_end = config.get("night_price_end_hour", 7)
            return {
                "night_price_start_hour": night_start,
                "night_price_end_hour": night_end,
                "current_hour": datetime.datetime.now(datetime.UTC).hour,
            }
        return {}

    def _get_current_price_attributes(self, hourly_prices: list[dict[str, Any]], day_data: dict[str, Any]) -> dict[str, Any]:
        """Get attributes for current price sensor."""
        now = datetime.datetime.now(datetime.UTC)
        current_hour_data = None
        for price in hourly_prices:
            start = datetime.datetime.fromisoformat(price["start_time"])
            end = datetime.datetime.fromisoformat(price["end_time"])
            if start <= now < end:
                current_hour_data = price
                break
        
        return {
            "date": day_data.get("date", self._data_key),
            "hour_start": current_hour_data["start_time"] if current_hour_data else None,
            "hour_end": current_hour_data["end_time"] if current_hour_data else None,
            "nord_pool_price": current_hour_data["nord_pool_price"] if current_hour_data else None,
        }

    def _get_price_data_attributes(self, hourly_prices: list[dict[str, Any]], day_data: dict[str, Any]) -> dict[str, Any]:
        """Get attributes for today/tomorrow price data sensors."""
        return {
            "hourly_prices": hourly_prices,
            "date": day_data.get("date", self._data_key),
        }

    def _get_aggregate_attributes(self, hourly_prices: list[dict[str, Any]], day_data: dict[str, Any]) -> dict[str, Any]:
        """Get attributes for min/max aggregate sensors."""
        if not hourly_prices:
            return {"date": day_data.get("date", self._data_key)}

        # Find the entry matching min/max value
        target_value = self.native_value
        match = None
        if target_value is not None:
            for price in hourly_prices:
                if price.get("actual_price") == target_value:
                    match = price
                    break
        return {
            "date": day_data.get("date", self._data_key),
            "hour_start": match.get("start_time") if match else None,
            "hour_end": match.get("end_time") if match else None,
        }

    @property
    def icon(self) -> str | None:
        """Return the icon for the sensor."""
        if self._sensor_type == SENSOR_TYPE_CURRENT_TARIFF:
            # Change icon based on current tariff
            current_tariff = self.native_value
            if current_tariff == "night":
                return "mdi:weather-night"
            else:
                return "mdi:weather-sunny"
        # Use default icon from entity description for other sensors
        return self.entity_description.icon
