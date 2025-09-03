"""Timestamp sensors for Real Electricity Price integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from .base import RealElectricityPriceBaseSensor

_LOGGER = logging.getLogger(__name__)


class LastSyncSensor(RealElectricityPriceBaseSensor):
    """Sensor for last sync timestamp."""

    @property
    def native_value(self) -> datetime | None:
        """Return the last sync timestamp."""
        # First try to get from coordinator data (set in _async_update_data)
        if (
            self.coordinator.data 
            and isinstance(self.coordinator.data, dict)
            and "last_sync" in self.coordinator.data
        ):
            return self.coordinator.data["last_sync"]
        
        # Fallback to coordinator's last_update_success_time if it exists
        if hasattr(self.coordinator, "last_update_success_time"):
            return self.coordinator.last_update_success_time
            
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        # Get data sources info
        data_sources_info = {}
        for data_key in ["yesterday", "today", "tomorrow"]:
            day_data = self.coordinator.data.get(data_key)
            if isinstance(day_data, dict):
                date = day_data.get("date", "unknown")
                data_available = day_data.get("data_available", False)
                hourly_prices = day_data.get("hourly_prices", [])

                data_sources_info[data_key] = {
                    "date": date,
                    "data_available": data_available,
                    "hours_count": len(hourly_prices),
                }

        return {
            "data_sources": data_sources_info,
            "coordinator_type": type(self.coordinator).__name__,
        }


class LastCheapCalculationSensor(RealElectricityPriceBaseSensor):
    """Sensor for last cheap price calculation timestamp."""

    def __init__(self, coordinator, description):
        """Initialize the sensor."""
        super().__init__(coordinator, description)
        # This sensor should use the cheap price coordinator
        self._use_cheap_coordinator = hasattr(coordinator, "get_current_cheap_price")

    @property
    def native_value(self) -> datetime | None:
        """Return the last cheap price calculation timestamp."""
        if (
            self._use_cheap_coordinator
            and hasattr(self.coordinator, "data")
            and self.coordinator.data
        ):
            cheap_data = self.coordinator.data
            last_update = cheap_data.get("last_update")
            if isinstance(last_update, datetime):
                return last_update

        # Fallback for main coordinator
        if hasattr(self.coordinator, "last_update_success_time"):
            return self.coordinator.last_update_success_time

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if (
            self._use_cheap_coordinator
            and hasattr(self.coordinator, "data")
            and self.coordinator.data
        ):
            cheap_data = self.coordinator.data
            trigger_time = cheap_data.get("trigger_time")

            return {
                "trigger_time": trigger_time.isoformat()
                if isinstance(trigger_time, datetime)
                else trigger_time,
                "coordinator_type": type(self.coordinator).__name__,
                "calculation_method": "cheap_coordinator",
            }

        return {
            "coordinator_type": type(self.coordinator).__name__,
            "calculation_method": "main_coordinator",
        }
