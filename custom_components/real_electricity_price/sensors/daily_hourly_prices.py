"""Daily hourly prices sensors for Real Electricity Price integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.util import dt as dt_util

from .base import RealElectricityPriceBaseSensor

if TYPE_CHECKING:
    from homeassistant.components.sensor import SensorEntityDescription

_LOGGER = logging.getLogger(__name__)


class DailyHourlyPricesSensor(RealElectricityPriceBaseSensor):
    """Base sensor for daily hourly electricity prices."""

    def __init__(self, coordinator, description, day_key: str) -> None:
        """Initialize the daily hourly prices sensor."""
        super().__init__(coordinator, description)
        self._day_key = day_key
        _LOGGER.info(
            "DAILY SENSOR CREATED: %s with day_key: %s", description.key, day_key
        )

    @property
    def native_value(self) -> float | None:
        """Return the current hour price for today, or average price for yesterday/tomorrow."""
        if not self.coordinator.data:
            return None

        day_data = self.coordinator.data.get(self._day_key)
        if not isinstance(day_data, dict):
            return None

        data_available = day_data.get("data_available", False)
        if not data_available:
            return None

        hourly_prices = day_data.get("hourly_prices", [])
        if not hourly_prices:
            return None

        # For "today", try to get current hour price
        if self._day_key == "today":
            # Use Home Assistant's datetime utility for consistent timezone handling
            current_time = dt_util.now()
            for price_entry in hourly_prices:
                start_time_str = price_entry.get("start_time")
                end_time_str = price_entry.get("end_time")

                if start_time_str and end_time_str:
                    try:
                        # Parse timezone-aware datetime strings using HA utilities
                        start_time = dt_util.parse_datetime(start_time_str)
                        end_time = dt_util.parse_datetime(end_time_str)

                        if (
                            start_time
                            and end_time
                            and start_time <= current_time < end_time
                        ):
                            price = price_entry.get("actual_price")
                            if price is not None:
                                return self._round_price(price)
                    except (ValueError, TypeError) as e:
                        _LOGGER.debug(
                            "Failed to parse time for current hour lookup: %s", e
                        )
                        continue

        # For yesterday/tomorrow, or if current hour not found for today, return average price
        valid_prices = [
            price_entry.get("actual_price")
            for price_entry in hourly_prices
            if price_entry.get("actual_price") is not None
        ]

        if valid_prices:
            average_price = sum(valid_prices) / len(valid_prices)
            return self._round_price(average_price)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all hourly prices for the day as attributes."""
        if not self.coordinator.data:
            return {}

        day_data = self.coordinator.data.get(self._day_key)
        if not isinstance(day_data, dict):
            return {}

        date = day_data.get("date", "unknown")
        data_available = day_data.get("data_available", False)
        is_holiday = day_data.get("is_holiday", False)
        is_weekend = day_data.get("is_weekend", False)
        hourly_prices = day_data.get("hourly_prices", [])

        # Process hourly prices to include all relevant information
        processed_prices = []
        valid_hours = 0
        for price_entry in hourly_prices:
            actual_price = price_entry.get("actual_price")
            if actual_price is not None:
                valid_hours += 1

            processed_entry = {
                "start_time": price_entry.get("start_time"),
                "end_time": price_entry.get("end_time"),
                "nord_pool_price": self._round_price(price_entry.get("nord_pool_price"))
                if price_entry.get("nord_pool_price") is not None
                else None,
                "actual_price": self._round_price(actual_price)
                if actual_price is not None
                else None,
                "tariff": price_entry.get("tariff"),
                "is_holiday": price_entry.get("is_holiday", is_holiday),
                "is_weekend": price_entry.get("is_weekend", is_weekend),
            }
            processed_prices.append(processed_entry)

        # Calculate statistics for available prices
        valid_prices = [
            entry["actual_price"]
            for entry in processed_prices
            if entry["actual_price"] is not None
        ]

        statistics = {}
        if valid_prices:
            statistics = {
                "min_price": self._round_price(min(valid_prices)),
                "max_price": self._round_price(max(valid_prices)),
                "avg_price": self._round_price(sum(valid_prices) / len(valid_prices)),
                "valid_hours_count": len(valid_prices),
            }

        # State type description based on day key and current value
        state_description = "No data"
        if self.native_value is not None:
            if self._day_key == "today":
                state_description = "Current hour price"
            else:
                state_description = "Average day price"

        return {
            "hourly_prices": processed_prices,
            "statistics": statistics,
            "date": date,
            "data_available": data_available,
            "is_holiday": is_holiday,
            "is_weekend": is_weekend,
            "state_description": state_description,
        }


class HourlyPricesYesterdaySensor(DailyHourlyPricesSensor):
    """Sensor for yesterday's hourly electricity prices."""

    def __init__(self, coordinator: object, description: SensorEntityDescription) -> None:
        """Initialize the yesterday hourly prices sensor."""
        super().__init__(coordinator, description, "yesterday")


class HourlyPricesTodaySensor(DailyHourlyPricesSensor):
    """Sensor for today's hourly electricity prices."""

    def __init__(self, coordinator: object, description: SensorEntityDescription) -> None:
        """Initialize the today hourly prices sensor."""
        super().__init__(coordinator, description, "today")


class HourlyPricesTomorrowSensor(DailyHourlyPricesSensor):
    """Sensor for tomorrow's hourly electricity prices."""

    def __init__(self, coordinator: object, description: SensorEntityDescription) -> None:
        """Initialize the tomorrow hourly prices sensor."""
        super().__init__(coordinator, description, "tomorrow")
