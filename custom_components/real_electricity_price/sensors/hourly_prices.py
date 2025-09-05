"""Hourly prices sensor for Real Electricity Price integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.util import dt as dt_util

from .base import RealElectricityPriceBaseSensor

_LOGGER = logging.getLogger(__name__)


class HourlyPricesSensor(RealElectricityPriceBaseSensor):
    """Sensor for hourly electricity prices."""

    @property
    def native_value(self) -> str | None:
        """Return the current hourly price or status."""
        # Try to get current price first
        current_price = self._get_current_hour_price()
        if current_price is not None:
            return str(self._round_price(current_price))

        # Fallback to status
        if not self.coordinator.data:
            return "No data available"

        total_hours = sum(
            len(day_data.get("hourly_prices", []))
            for day_data in self.coordinator.data.values()
            if isinstance(day_data, dict)
        )

        return f"{total_hours} hours available"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return hourly prices as attributes."""
        if not self.coordinator.data:
            return {}

        # Collect summary information instead of all hourly data
        data_sources_info = {}
        current_hour_info = None
        next_hours_preview = []

        for data_key in ["yesterday", "today", "tomorrow"]:
            day_data = self.coordinator.data.get(data_key)
            if not isinstance(day_data, dict):
                continue

            date = day_data.get("date", "unknown")
            data_available = day_data.get("data_available", False)
            hourly_prices = day_data.get("hourly_prices", [])

            _LOGGER.debug(
                "Found %s hourly prices for %s (date: %s, available: %s)",
                len(hourly_prices),
                data_key,
                date,
                data_available,
            )

            # Track data availability for each source
            data_sources_info[data_key] = {
                "date": date,
                "data_available": data_available,
                "hours_count": len(hourly_prices),
            }

            # Get current hour and next few hours for preview
            if data_key in ["today", "tomorrow"] and hourly_prices:
                # Use Home Assistant's datetime utility for consistent timezone handling
                now = dt_util.now().replace(minute=0, second=0, microsecond=0)

                for price_entry in hourly_prices[:12]:  # Limit to first 12 hours
                    try:
                        start_time_str = price_entry["start_time"]
                        start_time = dt_util.parse_datetime(start_time_str)

                        if (
                            start_time
                            and start_time >= now
                            and len(next_hours_preview) < 6
                        ):
                            next_hours_preview.append(
                                {
                                    "start_time": price_entry["start_time"],
                                    "price": self._round_price(
                                        price_entry.get("actual_price")
                                    )
                                    if price_entry.get("actual_price") is not None
                                    else None,
                                }
                            )
                        elif start_time and start_time == now:
                            current_hour_info = {
                                "start_time": price_entry["start_time"],
                                "price": self._round_price(
                                    price_entry.get("actual_price")
                                )
                                if price_entry.get("actual_price") is not None
                                else None,
                            }
                    except (ValueError, KeyError):
                        continue

        result = {"data_sources": data_sources_info}

        if current_hour_info:
            result["current_hour"] = current_hour_info

        if next_hours_preview:
            result["next_hours_preview"] = next_hours_preview

        _LOGGER.debug("Hourly prices attributes size reduced for database efficiency")

        # Return native data structures (no YAML serialization needed)
        return result

    def _get_current_hour_price(self) -> float | None:
        """Get the price for the current hour."""
        if not self.coordinator.data:
            return None

        # Use Home Assistant's datetime utility for consistent timezone handling
        now = dt_util.now().replace(minute=0, second=0, microsecond=0)

        for data_key in ["yesterday", "today", "tomorrow"]:
            day_data = self.coordinator.data.get(data_key)
            if not isinstance(day_data, dict):
                continue

            hourly_prices = day_data.get("hourly_prices", [])
            for price_entry in hourly_prices:
                try:
                    start_time_str = price_entry["start_time"]
                    end_time_str = price_entry["end_time"]

                    start_time = dt_util.parse_datetime(start_time_str)
                    end_time = dt_util.parse_datetime(end_time_str)

                    if (
                        start_time
                        and end_time
                        and start_time <= now < end_time
                        and price_entry.get("actual_price") is not None
                    ):
                        return price_entry["actual_price"]
                except (ValueError, KeyError):
                    continue

        return None
