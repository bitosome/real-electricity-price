"""Sensor platform for real_electricity_price."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.const import CONF_NAME
from homeassistant.util import dt as dt_util

from .const import (
    PRICE_DECIMAL_PRECISION,
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    CONF_SUPPLIER_MARGIN,
    CONF_VAT,
    CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT_GRID_TRANSMISSION_DAY,
    CONF_VAT_GRID_TRANSMISSION_NIGHT,
    CONF_VAT_NORD_POOL,
    CONF_VAT_SUPPLIER_MARGIN,
    CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
    SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    SUPPLIER_MARGIN_DEFAULT,
    VAT_DEFAULT,
    VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    VAT_GRID_TRANSMISSION_DAY_DEFAULT,
    VAT_GRID_TRANSMISSION_NIGHT_DEFAULT,
    VAT_NORD_POOL_DEFAULT,
    VAT_SUPPLIER_MARGIN_DEFAULT,
    VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
)
from .entity import RealElectricityPriceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)

# Sensor type constants for better maintainability
SENSOR_TYPE_CURRENT_PRICE = "current_price"
SENSOR_TYPE_HOURLY_PRICES = "hourly_prices"
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
        key="real_electricity_prices",
        name="Hourly Prices",
        icon="mdi:chart-line",
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

    def _configure_sensor_properties(self, key: str, device_name: str) -> None:
        """Configure sensor properties based on entity key."""
        # Map entity keys to sensor types and properties
        sensor_config = {
            "real_electricity_price": {
                "suffix": "current_price",
                "sensor_type": SENSOR_TYPE_CURRENT_PRICE,
                "data_key": None,
                "aggregate_mode": None,
            },
            "real_electricity_prices": {
                "suffix": "hourly prices",
                "sensor_type": SENSOR_TYPE_HOURLY_PRICES,
                "data_key": None,
                "aggregate_mode": None,
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
            "data_key": None,
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
        # Hourly refresh handled by coordinator for all sensors

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        # No per-entity hourly update to clean up

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        _LOGGER.debug("native_value called for sensor type: %s", self._sensor_type)
        
        if self._sensor_type == SENSOR_TYPE_LAST_SYNC:
            return self._get_last_sync_value()
        elif self._sensor_type == SENSOR_TYPE_CURRENT_TARIFF:
            return self._get_current_tariff_value()
        
        # For regular price sensors, ensure we have data
        if not self.coordinator.data:
            return None

        if self._sensor_type == SENSOR_TYPE_CURRENT_PRICE:
            return self._get_current_price_value()
        elif self._sensor_type == SENSOR_TYPE_HOURLY_PRICES:
            return self._get_current_price_value()
        
        return None

    def _get_last_sync_value(self) -> datetime.datetime:
        """Get the last sync timestamp."""
        _LOGGER.debug("Last sync sensor: coordinator.data = %s", self.coordinator.data)
        if self.coordinator.data and "last_sync" in self.coordinator.data:
            _LOGGER.debug("Last sync found: %s", self.coordinator.data["last_sync"])
            return self.coordinator.data["last_sync"]
        # Fallback to current time if no sync data available
        _LOGGER.debug("No last sync data found, using current time")
        return datetime.now(timezone.utc)

    def _get_current_tariff_value(self) -> str:
        """Determine the current tariff (day/night) using Home Assistant's configured time zone.
        
        Night tariff applies:
        - During configured night hours (default: 22:00 to 07:00) on weekdays  
        - All day on weekends and holidays (based on country calendar)
        """
        tz_name = getattr(self.hass.config, "time_zone", None)
        # Use HA's local time directly; it's already in the configured timezone
        local_time = dt_util.now()
        utc_now = datetime.now(timezone.utc)
        _LOGGER.debug("Current tariff calculation: UTC=%s, local=%s (tz=%s)", utc_now, local_time, tz_name)

        # Check if today is a holiday or weekend based on configured country
        today_data = self.coordinator.data.get("today", {})
        is_holiday = today_data.get("is_holiday", False)
        is_weekend = today_data.get("is_weekend", False)

        _LOGGER.debug("Holiday/Weekend check: is_holiday = %s, is_weekend = %s", is_holiday, is_weekend)

        # If it's a holiday or weekend, always return night tariff
        if is_holiday or is_weekend:
            _LOGGER.debug("Returning 'night' tariff due to %s", "holiday" if is_holiday else "weekend")
            return "night"

        # Check if current local time falls within night hours (22:00 - 07:00)
        local_hour = local_time.hour
        
        # Get configured night hours from config (with defaults)
        config = self.coordinator.data.get("config", {})
        night_start = config.get("night_price_start_hour", 22)  # 22:00
        night_end = config.get("night_price_end_hour", 7)       # 07:00
        
        _LOGGER.debug("Night tariff hours: %s:00 - %s:00 local time (tz=%s), current hour: %s", 
                     night_start, night_end, tz_name, local_hour)

        # Night tariff applies from night_start to night_end (crossing midnight)
        if night_start > night_end:  # Crosses midnight (e.g., 22:00 to 07:00)
            is_night_time = local_hour >= night_start or local_hour < night_end
        else:  # Does not cross midnight (unusual case)
            is_night_time = night_start <= local_hour < night_end
        
        tariff = "night" if is_night_time else "day"
        _LOGGER.debug("Local time %s:00 -> %s tariff (tz=%s)", local_hour, tariff, tz_name)
        
        return tariff

    def _get_current_price_value(self) -> float | None:
        """Get current price from all available hourly prices data.
        
        Searches through yesterday, today, and tomorrow data to find the current hour price.
        """
        if not self.coordinator.data:
            return None
            
        now = datetime.now(timezone.utc)
        
        # Search through all available data (yesterday, today, tomorrow)
        for data_key in self.coordinator.data:
            day_data = self.coordinator.data[data_key]
            if not isinstance(day_data, dict):
                continue
                
            hourly_prices = day_data.get("hourly_prices", [])
            if not hourly_prices:
                continue
                
            # Search for current hour in this day's data
            for price_entry in hourly_prices:
                try:
                    start_time = datetime.fromisoformat(price_entry["start_time"].replace("Z", "+00:00"))
                    end_time = datetime.fromisoformat(price_entry["end_time"].replace("Z", "+00:00"))
                    
                    if start_time <= now < end_time:
                        price_value = price_entry["actual_price"]
                        # Skip entries with unavailable data (None values)
                        if price_value is None:
                            _LOGGER.debug(f"Skipping unavailable price entry for time {now} in {data_key} data")
                            continue
                        _LOGGER.debug(f"Found current price: {price_value} for time {now} in {data_key} data")
                        return round(price_value, PRICE_DECIMAL_PRECISION)
                except (ValueError, KeyError) as e:
                    _LOGGER.warning(f"Invalid price entry in {data_key}: {e}")
                    continue
                
        _LOGGER.debug(f"No current price found for time {now} in any available data")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        # For special sensors that don't use coordinator data
        if self._sensor_type in (SENSOR_TYPE_LAST_SYNC, SENSOR_TYPE_CURRENT_TARIFF):
            return self._get_special_sensor_attributes()
            
        if not self.coordinator.data:
            return {}

        if self._sensor_type == SENSOR_TYPE_CURRENT_PRICE:
            return self._get_current_price_attributes()
        elif self._sensor_type == SENSOR_TYPE_HOURLY_PRICES:
            return self._get_hourly_prices_attributes()
        
        return {}

    def _get_special_sensor_attributes(self) -> dict[str, Any]:
        """Get attributes for special sensors (last_sync, current_tariff)."""
        if self._sensor_type == SENSOR_TYPE_LAST_SYNC:
            return {
                "last_update_time": self.coordinator.last_update_success,
                "coordinator_available": self.coordinator.last_update_success,
            }
        elif self._sensor_type == SENSOR_TYPE_CURRENT_TARIFF:
            config = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
            night_start = config.get("night_price_start_hour", 22)
            night_end = config.get("night_price_end_hour", 7)
            tz_name = getattr(self.hass.config, "time_zone", None)
            return {
                "night_price_start_hour": night_start,
                "night_price_end_hour": night_end,
                "time_zone": tz_name,
            }
        return {}

    def _get_current_price_attributes(self) -> dict[str, Any]:
        """Get attributes for current price sensor."""
        if not self.coordinator.data:
            return {}
            
        now = datetime.now(timezone.utc)
        current_hour_data = None
        current_date = None
        
        # Find current hour data across all available data
        for data_key in self.coordinator.data:
            day_data = self.coordinator.data[data_key]
            if not isinstance(day_data, dict):
                continue
                
            hourly_prices = day_data.get("hourly_prices", [])
            for price in hourly_prices:
                try:
                    start = datetime.fromisoformat(price["start_time"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(price["end_time"].replace("Z", "+00:00"))
                    if start <= now < end:
                        # Only use this entry if it has actual price data
                        if price.get("actual_price") is not None:
                            current_hour_data = price
                            current_date = day_data.get("date")
                            break
                except (ValueError, KeyError):
                    continue
            if current_hour_data:
                break
        
        attributes = {
            "date": current_date,
            "hour_start": current_hour_data["start_time"] if current_hour_data else None,
            "hour_end": current_hour_data["end_time"] if current_hour_data else None,
            "nord_pool_price": current_hour_data["nord_pool_price"] if current_hour_data else None,
        }
        
        # Add all additional cost components
        if current_hour_data:
            config = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
            attributes.update({
                # Price components with human-readable names
                "Grid electricity excise duty": config.get(CONF_GRID_ELECTRICITY_EXCISE_DUTY, GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT),
                "Grid renewable energy charge": config.get(CONF_GRID_RENEWABLE_ENERGY_CHARGE, GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT),
                "Grid transmission price - night": config.get(CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT, GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT),
                "Grid transmission price - day": config.get(CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY, GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT),
                "Supplier renewable energy charge": config.get(CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE, SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT),
                "Supplier margin": config.get(CONF_SUPPLIER_MARGIN, SUPPLIER_MARGIN_DEFAULT),
                "VAT percentage": config.get(CONF_VAT, VAT_DEFAULT),
                # Individual VAT configuration flags
                "VAT on Nord Pool price": config.get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT),
                "VAT on grid electricity excise duty": config.get(CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY, VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT),
                "VAT on grid renewable energy charge": config.get(CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE, VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT),
                "VAT on grid transmission (night)": config.get(CONF_VAT_GRID_TRANSMISSION_NIGHT, VAT_GRID_TRANSMISSION_NIGHT_DEFAULT),
                "VAT on grid transmission (day)": config.get(CONF_VAT_GRID_TRANSMISSION_DAY, VAT_GRID_TRANSMISSION_DAY_DEFAULT),
                "VAT on supplier renewable energy charge": config.get(CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE, VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT),
                "VAT on supplier margin": config.get(CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT),
                # Tariff and time information
                "tariff": current_hour_data.get("tariff"),
                "is_holiday": current_hour_data.get("is_holiday"),
                "is_weekend": current_hour_data.get("is_weekend"),
            })
            
        return attributes

    def _get_hourly_prices_attributes(self) -> dict[str, Any]:
        """Get attributes for hourly prices sensor."""
        if not self.coordinator.data:
            return {}
            
        all_hourly_prices = []
        data_sources_info = {}
        
        # Collect all hourly prices from yesterday, today, and tomorrow
        for data_key in sorted(self.coordinator.data.keys()):
            day_data = self.coordinator.data[data_key]
            if not isinstance(day_data, dict):
                continue
                
            hourly_prices = day_data.get("hourly_prices", [])
            data_available = day_data.get("data_available", True)  # Default to True for backward compatibility
            date = day_data.get("date", "unknown")
            
            _LOGGER.debug(f"Found {len(hourly_prices)} hourly prices for {data_key} (date: {date}, available: {data_available})")
            all_hourly_prices.extend(hourly_prices)
            
            # Track data availability for each source
            data_sources_info[data_key] = {
                "date": date,
                "data_available": data_available,
                "hours_count": len(hourly_prices)
            }
        
        _LOGGER.debug(f"Total hourly prices collected: {len(all_hourly_prices)}")
        return {
            "hourly_prices": all_hourly_prices,
            "data_sources": list(self.coordinator.data.keys()),
            "data_sources_info": data_sources_info,
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
