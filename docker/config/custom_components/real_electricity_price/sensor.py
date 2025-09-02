"""Sensor platform for real_electricity_price."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Any

import pandas as pd
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.const import CONF_NAME
from homeassistant.util import dt as dt_util

from .const import (
    # Price precision
    PRICE_DECIMAL_PRECISION,
    
    # Configuration keys
    CONF_GRID,
    CONF_SUPPLIER,
    CONF_VAT,
    CONF_CHEAP_PRICE_THRESHOLD,
    
    # Grid configuration
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    
    # Supplier configuration
    CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    CONF_SUPPLIER_MARGIN,
    
    # VAT configuration
    CONF_VAT_NORD_POOL,
    CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT_GRID_TRANSMISSION_DAY,
    CONF_VAT_GRID_TRANSMISSION_NIGHT,
    CONF_VAT_SUPPLIER_MARGIN,
    CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    
    # Default values
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
    CHEAP_PRICE_THRESHOLD_DEFAULT,
)
from .entity import RealElectricityPriceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .cheap_price_coordinator import CheapPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)


def datetime_serializer(obj):
    """Convert datetime objects to ISO format strings for JSON serialization recursively."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: datetime_serializer(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [datetime_serializer(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(datetime_serializer(item) for item in obj)
    else:
        return obj


# Sensor type constants for better maintainability
SENSOR_TYPE_CURRENT_PRICE = "current_price"
SENSOR_TYPE_HOURLY_PRICES = "hourly_prices"
SENSOR_TYPE_LAST_SYNC = "last_sync"
SENSOR_TYPE_CURRENT_TARIFF = "current_tariff"
SENSOR_TYPE_CHEAP_PRICES = "cheap_prices"

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
    SensorEntityDescription(
        key="real_electricity_price_cheap_prices",
        name="Cheapest Prices",
        icon="mdi:currency-eur-off",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR/kWh",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: RealElectricityPriceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    cheap_price_coordinator = entry.runtime_data.cheap_price_coordinator

    entities = []
    for entity_description in ENTITY_DESCRIPTIONS:
        if entity_description.key == "real_electricity_price":
            sensor_type = SENSOR_TYPE_CURRENT_PRICE
            coord = coordinator
        elif entity_description.key == "real_electricity_prices":
            sensor_type = SENSOR_TYPE_HOURLY_PRICES
            coord = coordinator
        elif entity_description.key == "real_electricity_price_last_sync":
            sensor_type = SENSOR_TYPE_LAST_SYNC
            coord = coordinator
        elif entity_description.key == "real_electricity_price_current_tariff":
            sensor_type = SENSOR_TYPE_CURRENT_TARIFF
            coord = coordinator
        elif entity_description.key == "real_electricity_price_cheap_prices":
            sensor_type = SENSOR_TYPE_CHEAP_PRICES
            coord = cheap_price_coordinator  # Use separate coordinator for cheap prices
        else:
            continue

        entities.append(
            RealElectricityPriceSensor(
                coordinator=coord,
                entity_description=entity_description,
                sensor_type=sensor_type,
            )
        )

    async_add_entities(entities)


class RealElectricityPriceSensor(RealElectricityPriceEntity, SensorEntity):
    """Real Electricity Price Sensor class."""

    def __init__(
        self,
        coordinator: RealElectricityPriceDataUpdateCoordinator | CheapPriceDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        self._sensor_type = sensor_type
        
        _LOGGER.debug("Initializing sensor: %s (type: %s)", entity_description.key, sensor_type)
        
        # Get device name from config (options override data)
        config = {**coordinator.config_entry.data, **coordinator.config_entry.options}
        device_name = config.get(CONF_NAME, "Real Electricity Price")
        
        # Set entity name
        self._attr_name = f"{device_name} {entity_description.name}"

    def _round_price(self, value: float | None) -> float | None:
        """Round price to configured decimal precision."""
        if value is None:
            return None
        return round(value, PRICE_DECIMAL_PRECISION)

    def _get_price_config_value(self, config: dict, key: str, default: float) -> float:
        """Get a configuration value and return it rounded."""
        return self._round_price(config.get(key, default))

    def _create_price_components(self, config: dict) -> dict[str, Any]:
        """Create price components object for attributes."""
        supplier_name = config.get(CONF_SUPPLIER, "Supplier").replace("_", " ").title()
        grid_name = config.get(CONF_GRID, "Grid").replace("_", " ").title()
        
        return {
            "grid_costs": {
                f"{grid_name.lower()}_electricity_excise_duty": self._get_price_config_value(
                    config, CONF_GRID_ELECTRICITY_EXCISE_DUTY, GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT
                ),
                f"{grid_name.lower()}_renewable_energy_charge": self._get_price_config_value(
                    config, CONF_GRID_RENEWABLE_ENERGY_CHARGE, GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT
                ),
                f"{grid_name.lower()}_transmission_price_night": self._get_price_config_value(
                    config, CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT, GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT
                ),
                f"{grid_name.lower()}_transmission_price_day": self._get_price_config_value(
                    config, CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY, GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT
                ),
            },
            "supplier_costs": {
                f"{supplier_name.lower()}_renewable_energy_charge": self._get_price_config_value(
                    config, CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE, SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT
                ),
                f"{supplier_name.lower()}_margin": self._get_price_config_value(
                    config, CONF_SUPPLIER_MARGIN, SUPPLIER_MARGIN_DEFAULT
                ),
            },
            "tax_info": {
                "vat_percentage": self._get_price_config_value(config, CONF_VAT, VAT_DEFAULT),
                "vat_applied_to": {
                    "nord_pool_price": config.get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT),
                    f"{grid_name.lower()}_electricity_excise_duty": config.get(CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY, VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT),
                    f"{grid_name.lower()}_renewable_energy_charge": config.get(CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE, VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT),
                    f"{grid_name.lower()}_transmission_night": config.get(CONF_VAT_GRID_TRANSMISSION_NIGHT, VAT_GRID_TRANSMISSION_NIGHT_DEFAULT),
                    f"{grid_name.lower()}_transmission_day": config.get(CONF_VAT_GRID_TRANSMISSION_DAY, VAT_GRID_TRANSMISSION_DAY_DEFAULT),
                    f"{supplier_name.lower()}_renewable_energy_charge": config.get(CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE, VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT),
                    f"{supplier_name.lower()}_margin": config.get(CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT),
                }
            }
        }

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
        elif self._sensor_type == SENSOR_TYPE_CHEAP_PRICES:
            return self._get_cheap_prices_value()
        
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
        """Determine the current tariff (day/night) based on local time in the configured country.
        
        Night tariff applies:
        - During configured night hours (default: 22:00 to 07:00) on weekdays
        - All day on weekends and holidays (based on country calendar)
        """
        # Use Home Assistant's configured time zone to determine local time
        tz_name = getattr(self.hass.config, "time_zone", None)
        # Use HA's local time directly; it's already in the configured timezone
        local_time = dt_util.now()
        utc_now = datetime.now(timezone.utc)
        _LOGGER.debug(
            "Current tariff calculation: UTC=%s, local=%s (tz=%s)",
            utc_now,
            local_time,
            tz_name,
        )

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
        
        _LOGGER.debug(
            "Night tariff hours: %s:00 - %s:00 local time (tz=%s), current hour: %s",
            night_start,
            night_end,
            tz_name,
            local_hour,
        )

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
                        return self._round_price(price_value)
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
        elif self._sensor_type == SENSOR_TYPE_CHEAP_PRICES:
            return self._get_cheap_prices_attributes()
        
        return {}

    def _get_special_sensor_attributes(self) -> dict[str, Any]:
        """Get attributes for special sensors (last_sync, current_tariff)."""
        if self._sensor_type == SENSOR_TYPE_LAST_SYNC:
            sync_info = {
                "last_update_time": self.coordinator.last_update_success,
                "coordinator_available": self.coordinator.last_update_success,
            }
            return {
                "sync_info": json.dumps(sync_info, indent=2, default=str),
            }
        elif self._sensor_type == SENSOR_TYPE_CURRENT_TARIFF:
            config = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
            night_start = config.get("night_price_start_hour", 22)
            night_end = config.get("night_price_end_hour", 7)
            tz_name = getattr(self.hass.config, "time_zone", None)
            
            tariff_config = {
                "night_price_start_hour": night_start,
                "night_price_end_hour": night_end,
                "time_zone": tz_name,
            }
            return {
                "tariff_config": json.dumps(tariff_config, indent=2),
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
        
        # Get configuration for price components
        config = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
        
        # Build current hour info object
        current_hour_info = {
            "date": current_date,
            "hour_start": current_hour_data["start_time"] if current_hour_data else None,
            "hour_end": current_hour_data["end_time"] if current_hour_data else None,
            "nord_pool_price": self._round_price(current_hour_data["nord_pool_price"]) if current_hour_data and current_hour_data["nord_pool_price"] is not None else None,
            "tariff": current_hour_data.get("tariff") if current_hour_data else None,
            "is_holiday": current_hour_data.get("is_holiday") if current_hour_data else None,
            "is_weekend": current_hour_data.get("is_weekend") if current_hour_data else None,
        }
        
        # Build price components object
        if current_hour_data:
            price_components = self._create_price_components(config)
        else:
            price_components = {}
        
        return {
            "current_hour_info": json.dumps(current_hour_info, indent=2),
            "price_components": json.dumps(price_components, indent=2),
        }

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
            "hourly_prices": json.dumps(all_hourly_prices, indent=2),
            "data_sources": json.dumps(list(self.coordinator.data.keys()), indent=2),
            "data_sources_info": json.dumps(data_sources_info, indent=2),
        }

    def _get_cheap_prices_value(self) -> float | None:
        """Get nearest cheap price value based on current time."""
        # For cheap prices sensor, use the dedicated coordinator
        if self._sensor_type == SENSOR_TYPE_CHEAP_PRICES:
            # Check if we have a cheap price coordinator (should be the case for cheap prices sensor)
            if hasattr(self.coordinator, 'get_current_cheap_price'):
                current_price = self.coordinator.get_current_cheap_price()
                if current_price is not None:
                    return current_price
                
                # If not in a cheap period, get the next upcoming cheap price
                next_cheap = self.coordinator.get_next_cheap_price()
                if next_cheap:
                    return self._round_price(next_cheap["price"])
                
                return None
        
        # Fallback to old method for sensors still using main coordinator
        cheap_ranges = self._analyze_cheap_prices()
        if not cheap_ranges:
            return None
            
        now = datetime.now(timezone.utc)
        
        # Find the nearest cheap price (current or next upcoming)
        nearest_price = None
        min_time_diff = None
        
        for range_data in cheap_ranges:
            start_time = datetime.fromisoformat(range_data["start_time"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(range_data["end_time"].replace("Z", "+00:00"))
            
            # If we're currently in this range, return its price
            if start_time <= now < end_time:
                return self._round_price(range_data["price"])
            
            # Calculate time difference to this range
            if start_time > now:  # Future range
                time_diff = (start_time - now).total_seconds()
            else:  # Past range
                time_diff = float('inf')  # Don't consider past ranges for "nearest"
            
            if min_time_diff is None or time_diff < min_time_diff:
                min_time_diff = time_diff
                nearest_price = range_data["price"]
        
        return self._round_price(nearest_price) if nearest_price is not None else None

    def _get_cheap_prices_attributes(self) -> dict[str, Any]:
        """Get attributes for cheap prices sensor."""
        # For cheap prices sensor, use the dedicated coordinator
        if self._sensor_type == SENSOR_TYPE_CHEAP_PRICES:
            if hasattr(self.coordinator, 'data') and self.coordinator.data:
                cheap_data = self.coordinator.data
                cheap_ranges = cheap_data.get("cheap_ranges", [])
                analysis_info = cheap_data.get("analysis_info", {})
                
                # Get current status
                now = datetime.now(timezone.utc)
                current_status = "outside_cheap_period"
                next_cheap_info = None
                
                # Check if we're in a cheap period
                for range_data in cheap_ranges:
                    start_time = datetime.fromisoformat(range_data["start_time"].replace("Z", "+00:00"))
                    end_time = datetime.fromisoformat(range_data["end_time"].replace("Z", "+00:00"))
                    
                    if start_time <= now < end_time:
                        current_status = "in_cheap_period"
                        break
                
                # Find next cheap period if not currently in one
                if current_status == "outside_cheap_period":
                    min_time_diff = None
                    for range_data in cheap_ranges:
                        start_time = datetime.fromisoformat(range_data["start_time"].replace("Z", "+00:00"))
                        if start_time > now:
                            time_diff = (start_time - now).total_seconds()
                            if min_time_diff is None or time_diff < min_time_diff:
                                min_time_diff = time_diff
                                next_cheap_info = {
                                    "start_time": range_data["start_time"],
                                    "end_time": range_data["end_time"],
                                    "average_price": self._round_price(range_data["avg_price"]),
                                }
                
                # Build comprehensive status info
                last_update = cheap_data.get("last_update")
                trigger_time = cheap_data.get("trigger_time")
                
                status_info = {
                    "current_status": current_status,
                    "total_cheap_hours": len(cheap_ranges),
                    "last_calculation": last_update.isoformat() if isinstance(last_update, datetime) else last_update,
                    "trigger_time": trigger_time.isoformat() if isinstance(trigger_time, datetime) else trigger_time,
                }
                
                # Add next cheap period info if available
                if next_cheap_info:
                    status_info["next_cheap_period"] = next_cheap_info
                
                # Convert all datetime objects to strings before JSON serialization
                cheap_ranges_serializable = datetime_serializer(cheap_ranges)
                status_info_serializable = datetime_serializer(status_info)
                analysis_info_serializable = datetime_serializer(analysis_info)
                
                return {
                    "cheap_price_ranges": json.dumps(cheap_ranges_serializable, indent=2),
                    "status_info": json.dumps(status_info_serializable, indent=2),
                    "analysis_info": json.dumps(analysis_info_serializable, indent=2),
                }
        
        # Fallback to old method for sensors still using main coordinator
        cheap_ranges = self._analyze_cheap_prices()
        
        # Get configuration
        config = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
        threshold = config.get(CONF_CHEAP_PRICE_THRESHOLD, CHEAP_PRICE_THRESHOLD_DEFAULT)
        
        # Get analysis info
        analysis_info = self._get_price_analysis_info()
        
        # Build summary info
        summary_info = {
            "threshold_percent": threshold,
            "min_price": analysis_info.get("min_price"),
            "max_cheap_price": analysis_info.get("max_cheap_price"),
            "total_cheap_hours": len(cheap_ranges),
            "analysis_period_hours": analysis_info.get("analysis_period_hours"),
        }
        
        return {
            "cheap_price_ranges": json.dumps(cheap_ranges, indent=2),
            "summary_info": json.dumps(summary_info, indent=2),
            "data_sources": json.dumps(analysis_info.get("data_sources", []), indent=2),
        }

    def _analyze_cheap_prices(self) -> list[dict[str, Any]]:
        """Analyze price data with pandas to find cheap price ranges from NOW onwards."""
        if not self.coordinator.data:
            return []
        
        try:
            # Collect all hourly prices with valid data from current hour onwards
            now = datetime.now(timezone.utc)
            current_hour_start = now.replace(minute=0, second=0, microsecond=0)
            all_prices = []
            
            for data_key in self.coordinator.data:
                day_data = self.coordinator.data[data_key]
                if not isinstance(day_data, dict):
                    continue
                    
                hourly_prices = day_data.get("hourly_prices", [])
                for price_entry in hourly_prices:
                    # Only include entries with valid price data from current hour onwards
                    if price_entry.get("actual_price") is not None:
                        try:
                            start_time = datetime.fromisoformat(price_entry["start_time"].replace("Z", "+00:00"))
                            # Include current hour and future hours only
                            if start_time >= current_hour_start:
                                all_prices.append({
                                    "start_time": price_entry["start_time"],
                                    "end_time": price_entry["end_time"],
                                    "price": price_entry["actual_price"],
                                    "date": day_data.get("date"),
                                })
                        except (ValueError, KeyError):
                            continue
            
            if not all_prices:
                _LOGGER.debug("No valid price data available for cheap price analysis")
                return []
            
            # Create pandas DataFrame for analysis
            df = pd.DataFrame(all_prices)
            df["start_time_dt"] = pd.to_datetime(df["start_time"])
            df = df.sort_values("start_time_dt")
            
            # Find minimum price
            min_price = df["price"].min()
            
            # Get threshold from configuration
            config = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
            threshold_percent = config.get(CONF_CHEAP_PRICE_THRESHOLD, CHEAP_PRICE_THRESHOLD_DEFAULT)
            
            # Calculate maximum price that's considered "cheap"
            max_cheap_price = min_price * (1 + threshold_percent / 100)
            
            # Filter cheap prices
            cheap_df = df[df["price"] <= max_cheap_price].copy()
            
            if cheap_df.empty:
                _LOGGER.debug("No cheap prices found with threshold %s%%", threshold_percent)
                return []
            
            # Group consecutive hours into ranges
            cheap_ranges = self._group_consecutive_hours(cheap_df)
            
            _LOGGER.debug(
                "Found %d cheap price ranges (min: %.6f, max_cheap: %.6f, threshold: %.1f%%)",
                len(cheap_ranges),
                min_price,
                max_cheap_price,
                threshold_percent
            )
            
            return cheap_ranges
            
        except Exception as e:
            _LOGGER.error("Error analyzing cheap prices: %s", e)
            return []

    def _group_consecutive_hours(self, cheap_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Group consecutive cheap hours into time ranges."""
        if cheap_df.empty:
            return []
        
        ranges = []
        current_range = None
        
        for _, row in cheap_df.iterrows():
            start_time = pd.to_datetime(row["start_time"])
            end_time = pd.to_datetime(row["end_time"])
            price = row["price"]
            
            if current_range is None:
                # Start new range
                current_range = {
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "price": self._round_price(price),  # Use first price in range
                    "min_price": self._round_price(price),
                    "max_price": self._round_price(price),
                    "avg_price": self._round_price(price),
                    "hour_count": 1,
                    "prices": [price],
                }
            else:
                # Check if this hour is consecutive to the current range
                current_end = pd.to_datetime(current_range["end_time"])
                if start_time == current_end:
                    # Extend current range
                    current_range["end_time"] = row["end_time"]
                    current_range["hour_count"] += 1
                    current_range["prices"].append(price)
                    current_range["min_price"] = self._round_price(min(current_range["min_price"], price))
                    current_range["max_price"] = self._round_price(max(current_range["max_price"], price))
                    current_range["avg_price"] = self._round_price(sum(current_range["prices"]) / len(current_range["prices"]))
                else:
                    # Finish current range and start new one
                    # Remove the prices list before adding to results (too verbose for attributes)
                    current_range.pop("prices", None)
                    ranges.append(current_range)
                    
                    current_range = {
                        "start_time": row["start_time"],
                        "end_time": row["end_time"],
                        "price": self._round_price(price),
                        "min_price": self._round_price(price),
                        "max_price": self._round_price(price),
                        "avg_price": self._round_price(price),
                        "hour_count": 1,
                        "prices": [price],
                    }
        
        # Add the last range
        if current_range is not None:
            current_range.pop("prices", None)
            ranges.append(current_range)
        
        return ranges

    def _get_price_analysis_info(self) -> dict[str, Any]:
        """Get general information about the price analysis."""
        if not self.coordinator.data:
            return {}
        
        try:
            # Collect all valid prices from NOW onwards only
            now = datetime.now(timezone.utc)
            all_prices = []
            future_data_sources = []
            
            for data_key in self.coordinator.data:
                day_data = self.coordinator.data[data_key]
                if not isinstance(day_data, dict):
                    continue
                    
                hourly_prices = day_data.get("hourly_prices", [])
                future_prices = []
                
                # Only include prices from current hour onwards
                for price_entry in hourly_prices:
                    if price_entry.get("actual_price") is not None:
                        try:
                            start_time = datetime.fromisoformat(price_entry["start_time"].replace("Z", "+00:00"))
                            # Include current hour and future hours only
                            if start_time >= now.replace(minute=0, second=0, microsecond=0):
                                future_prices.append(price_entry["actual_price"])
                        except (ValueError, KeyError):
                            continue
                
                if future_prices:
                    all_prices.extend(future_prices)
                    future_data_sources.append({
                        "source": data_key,
                        "date": day_data.get("date"),
                        "hours_count": len(future_prices),
                    })
            
            if not all_prices:
                return {"data_sources": future_data_sources}
            
            # Calculate statistics
            min_price = min(all_prices)
            config = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
            threshold_percent = config.get(CONF_CHEAP_PRICE_THRESHOLD, CHEAP_PRICE_THRESHOLD_DEFAULT)
            max_cheap_price = min_price * (1 + threshold_percent / 100)
            
            # Calculate actual analysis period based on future hours only
            total_future_hours = sum(source["hours_count"] for source in future_data_sources)
            
            return {
                "min_price": self._round_price(min_price),
                "max_cheap_price": self._round_price(max_cheap_price),
                "analysis_period_hours": total_future_hours,
                "data_sources": future_data_sources,
            }
            
        except Exception as e:
            _LOGGER.error("Error getting price analysis info: %s", e)
            return {}

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
