"""Number and time entities for Real Electricity Price config options."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.components.time import TimeEntity

from .const import (
    DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER,
    PRICE_DECIMAL_PRECISION,
    parse_time_string,
)
from .entity import RealElectricityPriceEntity

_LOGGER = logging.getLogger(__name__)


class CheapHoursBasePriceEntity(RealElectricityPriceEntity, NumberEntity):
    """Entity for cheap hour base price."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.config_entry.title} Cheap hour base price"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_cheap_hours_base_price"
        )
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "€/kWh"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 1
        try:
            self._attr_native_step = 10 ** (-PRICE_DECIMAL_PRECISION)
        except Exception:
            self._attr_native_step = 0.000001
        self._attr_mode = "box"
        self._attr_native_value = (
            coordinator._cheap_price_coordinator.get_runtime_base_price()
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        if not isinstance(value, (int, float)) or value < 0 or value > 1:
            _LOGGER.error("Invalid base price value: %s", value)
            return

        try:
            # Update the coordinator's runtime value without triggering config reload
            self.coordinator._cheap_price_coordinator.set_runtime_base_price(value)
            self._attr_native_value = value
            self.async_write_ha_state()
            _LOGGER.info(
                "Base price updated to %s - use Calculate Cheap Hours button to recalculate",
                value,
            )
        except Exception as e:
            _LOGGER.exception("Error setting base price: %s", e)


class CheapHoursThresholdEntity(RealElectricityPriceEntity, NumberEntity):
    """Entity for cheap hour threshold."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.config_entry.title} Cheap hour threshold"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_cheap_hours_threshold"
        )
        self._attr_icon = "mdi:percent"
        self._attr_native_unit_of_measurement = "%"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 0.1
        self._attr_mode = "box"
        self._attr_native_value = (
            coordinator._cheap_price_coordinator.get_runtime_threshold()
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        if not isinstance(value, (int, float)) or value < 0 or value > 100:
            _LOGGER.error("Invalid threshold value: %s", value)
            return

        try:
            # Update the coordinator's runtime value without triggering config reload
            self.coordinator._cheap_price_coordinator.set_runtime_threshold(value)
            self._attr_native_value = value
            self.async_write_ha_state()
            _LOGGER.info(
                "Threshold updated to %s%% - use Calculate Cheap Hours button to recalculate",
                value,
            )
        except Exception as e:
            _LOGGER.exception("Error setting threshold: %s", e)


class CheapHoursUpdateTriggerEntity(RealElectricityPriceEntity, TimeEntity):
    """Entity for cheap hour update trigger time."""

    def __init__(self, coordinator) -> None:

        super().__init__(coordinator)
        self._attr_name = (
            f"{coordinator.config_entry.title} Cheap hours calculation time"
        )
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_cheap_hours_update_trigger"
        )
        self._attr_icon = "mdi:clock-time-three-outline"
        trigger = coordinator._cheap_price_coordinator.get_runtime_update_trigger()
        self._attr_native_value = self._parse_time(trigger)

    def _parse_time(self, value):
        import datetime

        # Always return a datetime.time object for UI, but store as dict
        try:
            def_h, def_m, _ = parse_time_string(DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER)
        except Exception:
            def_h, def_m = 14, 30
        if isinstance(value, dict):
            hour = value.get("hour", def_h)
            minute = value.get("minute", def_m)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return datetime.time(def_h, def_m)
            return datetime.time(hour, minute)
        if isinstance(value, str):
            try:
                parts = value.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    return datetime.time(def_h, def_m)
                return datetime.time(hour, minute)
            except Exception:
                return datetime.time(def_h, def_m)
        elif isinstance(value, datetime.time):
            return value
        return datetime.time(def_h, def_m)

    def set_value(self, value) -> None:
        """Set new time value (synchronous method called by HA)."""
        import datetime

        # Parse the time value
        if isinstance(value, datetime.time):
            hour = value.hour
            minute = value.minute
        elif isinstance(value, dict):
            if "hour" not in value or "minute" not in value:
                _LOGGER.error(
                    f"Rejected dict missing hour/minute for time entity: {value}"
                )
                return
            try:
                def_h, def_m, _ = parse_time_string(DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER)
            except Exception:
                def_h, def_m = 14, 30
            hour = value.get("hour", def_h)
            minute = value.get("minute", def_m)
        elif isinstance(value, str):
            try:
                parts = value.split(":")
                if len(parts) < 2:
                    _LOGGER.error(
                        f"Rejected invalid time string for time entity: {value}"
                    )
                    return
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
            except Exception:
                _LOGGER.exception(f"Invalid time specified for update trigger: {value}")
                return
        else:
            _LOGGER.error(f"Rejected update trigger: type={type(value)} value={value}")
            return

        # Validate time range
        if not (isinstance(hour, int) and isinstance(minute, int)):
            _LOGGER.error(
                f"Rejected update trigger: hour/minute not int: {hour}, {minute}"
            )
            return
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            _LOGGER.error(f"Invalid time specified for update trigger: {hour}:{minute}")
            return

        # Update the coordinator's runtime value without triggering config reload
        trigger_dict = {"hour": hour, "minute": minute}
        self.coordinator._cheap_price_coordinator.set_runtime_update_trigger(
            trigger_dict
        )
        self._attr_native_value = datetime.time(hour, minute)
        self.schedule_update_ha_state()
        _LOGGER.info(
            "Update trigger time updated to %02d:%02d - use Calculate Cheap Hours button to recalculate",
            hour,
            minute,
        )

    async def async_set_native_value(self, value):
        """Set new time value (async wrapper)."""
        return self.set_value(value)
