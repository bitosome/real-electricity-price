"""Cheap hours sensor for Real Electricity Price integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

from ..cheap_hours_analysis import (
    collect_hourly_price_entries,
    group_consecutive_price_entries,
)

from .base import RealElectricityPriceBaseSensor

_LOGGER = logging.getLogger(__name__)


def _analyze_cheap_prices_for_entity(
    entity: RealElectricityPriceBaseSensor,
) -> list[dict[str, Any]]:
    """Analyze cheap price ranges for any sensor using main price coordinator data."""
    if not entity.coordinator.data:
        return []

    try:
        now = dt_util.now()
        current_hour_start = now.replace(minute=0, second=0, microsecond=0)
        all_prices = collect_hourly_price_entries(
            entity.coordinator.data,
            min_start_time=current_hour_start,
        )

        if not all_prices:
            _LOGGER.debug("No valid price data available for cheap price analysis")
            return []

        acceptable_price = entity.get_config().acceptable_price
        cheap_prices = [
            price_entry
            for price_entry in all_prices
            if price_entry["price"] <= acceptable_price
        ]

        if not cheap_prices:
            _LOGGER.debug(
                "No cheap prices found with acceptable price %.6f",
                acceptable_price,
            )
            return []

        cheap_ranges = group_consecutive_price_entries(
            cheap_prices,
            round_price=entity._round_price,
        )
        _LOGGER.debug(
            "Found %d cheap price ranges (acceptable_price: %.6f)",
            len(cheap_ranges),
            acceptable_price,
        )
        return cheap_ranges
    except Exception:
        _LOGGER.exception("Error analyzing cheap prices")
        return []


def _get_price_analysis_info_for_entity(
    entity: RealElectricityPriceBaseSensor,
) -> dict[str, Any]:
    """Get manual price analysis info for a sensor using main coordinator data."""
    if not entity.coordinator.data:
        return {}

    try:
        now = dt_util.now()
        current_hour_start = now.replace(minute=0, second=0, microsecond=0)
        all_prices = collect_hourly_price_entries(
            entity.coordinator.data,
            min_start_time=current_hour_start,
        )

        future_data_sources: list[dict[str, Any]] = []
        for data_key, day_data in entity.coordinator.data.items():
            if not isinstance(day_data, dict) or not day_data.get(
                "data_available", False
            ):
                continue
            count = 0
            for price_entry in day_data.get("hourly_prices", []):
                if price_entry.get("actual_price") is None:
                    continue
                try:
                    start_time = dt_util.parse_datetime(price_entry["start_time"])
                except (TypeError, ValueError, KeyError):
                    continue
                if start_time and start_time >= current_hour_start:
                    count += 1
            if count:
                future_data_sources.append(
                    {
                        "source": data_key,
                        "date": day_data.get("date", "unknown"),
                        "hours_count": count,
                    }
                )

        if not all_prices:
            return {"data_sources": future_data_sources}

        acceptable_price = entity.get_config().acceptable_price
        total_future_hours = sum(
            source["hours_count"] for source in future_data_sources
        )

        return {
            "acceptable_price": entity._round_price(acceptable_price),
            "analysis_period_hours": total_future_hours,
            "data_sources": future_data_sources,
        }
    except Exception:
        _LOGGER.exception("Error getting price analysis info")
        return {}


def _iter_valid_cheap_ranges(cheap_ranges: list[dict[str, Any]]):
    """Yield cheap ranges with parsed start/end datetimes."""
    for range_data in cheap_ranges:
        try:
            start_time = dt_util.parse_datetime(range_data["start_time"])
            end_time = dt_util.parse_datetime(range_data["end_time"])
        except (TypeError, ValueError, KeyError):
            continue
        if not start_time or not end_time:
            continue
        yield range_data, start_time, end_time


def _get_current_or_next_cheap_period_time(
    cheap_ranges: list[dict[str, Any]],
    now: datetime,
    *,
    return_future: str,
) -> datetime | None:
    """Return current cheap period end or the next cheap period boundary."""
    for _, start_time, end_time in _iter_valid_cheap_ranges(cheap_ranges):
        if start_time <= now < end_time:
            return dt_util.as_local(end_time)
        if start_time > now:
            target_time = start_time if return_future == "start" else end_time
            return dt_util.as_local(target_time)
    return None


def _get_next_cheap_period_start_time(
    cheap_ranges: list[dict[str, Any]],
    now: datetime,
) -> datetime | None:
    """Return the next future cheap period start time (skip active period)."""
    for _, start_time, end_time in _iter_valid_cheap_ranges(cheap_ranges):
        if start_time > now:
            return dt_util.as_local(start_time)
        if start_time <= now < end_time:
            continue
    return None


def _get_current_cheap_avg_price(
    cheap_ranges: list[dict[str, Any]],
    now: datetime,
) -> float | None:
    """Return average price for the currently active cheap range."""
    for range_data, start_time, end_time in _iter_valid_cheap_ranges(cheap_ranges):
        if start_time <= now < end_time:
            avg_price = range_data.get("avg_price")
            return avg_price if isinstance(avg_price, (int, float)) else None
    return None


def _summarize_cheap_ranges(
    cheap_ranges: list[dict[str, Any]],
    *,
    now: datetime,
    round_price: Any,
) -> tuple[str, dict[str, Any] | None, int]:
    """Return status, next-period metadata, and total cheap hours for ranges."""
    current_status = "inactive"
    next_cheap_info: dict[str, Any] | None = None
    total_hours = 0

    for range_data, start_time, end_time in _iter_valid_cheap_ranges(cheap_ranges):
        total_hours += range_data.get("hour_count", 1)
        if start_time <= now < end_time:
            current_status = "active"
            continue
        if start_time > now and next_cheap_info is None:
            next_cheap_info = {
                "start_time": range_data["start_time"],
                "end_time": range_data["end_time"],
                "average_price": round_price(range_data["avg_price"]),
            }

    return current_status, next_cheap_info, total_hours


class CheapHoursSensor(RealElectricityPriceBaseSensor):
    """Sensor for cheap electricity hours."""

    def __init__(self, coordinator, description) -> None:
        """Initialize the cheap hours sensor."""
        super().__init__(coordinator, description)
        # This sensor should use the cheap hours coordinator when available
        self._use_cheap_coordinator = hasattr(coordinator, "get_current_cheap_price")

    @property
    def native_value(self) -> int | None:
        """Return the count of next cheap hours."""
        if self._use_cheap_coordinator:
            return self._get_next_cheap_hours_from_coordinator()

        # Fallback to checking ranges manually
        return self._get_next_cheap_hours_from_ranges()

    def _get_next_cheap_hours_from_coordinator(self) -> int | None:
        """Get count of next cheap hours from cheap price coordinator."""
        if not (hasattr(self.coordinator, "data") and self.coordinator.data):
            return None

        cheap_data = self.coordinator.data
        cheap_ranges = cheap_data.get("cheap_ranges", [])

        if not cheap_ranges:
            return 0

        # Sum all cheap hours from all ranges
        return sum(
            range_data.get("hour_count", 1) for range_data in cheap_ranges
        )

    def _get_next_cheap_hours_from_ranges(self) -> int | None:
        """Get count of next cheap hours by checking ranges manually."""
        cheap_ranges = self._analyze_cheap_prices()

        if not cheap_ranges:
            return 0

        # Sum all cheap hours from all ranges
        return sum(
            range_data.get("hour_count", 1) for range_data in cheap_ranges
        )

    def _get_next_cheap_period_from_coordinator(self) -> datetime | None:
        """Get next cheap period timestamp from cheap price coordinator."""
        if not (hasattr(self.coordinator, "data") and self.coordinator.data):
            return None

        cheap_data = self.coordinator.data
        cheap_ranges = cheap_data.get("cheap_ranges", [])

        if not cheap_ranges:
            return None

        now = dt_util.now()

        return _get_current_or_next_cheap_period_time(
            cheap_ranges, now, return_future="start"
        )

    def _get_next_cheap_period_from_ranges(self) -> datetime | None:
        """Get next cheap period timestamp by checking ranges manually."""
        cheap_ranges = self._analyze_cheap_prices()

        if not cheap_ranges:
            return None

        now = dt_util.now()

        return _get_current_or_next_cheap_period_time(
            cheap_ranges, now, return_future="start"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return cheap price analysis as attributes."""
        if (
            self._use_cheap_coordinator
            and hasattr(self.coordinator, "data")
            and self.coordinator.data
        ):
            return self._get_cheap_coordinator_attributes()

        # Fallback to manual analysis
        return self._get_manual_analysis_attributes()

    def _get_cheap_coordinator_attributes(self) -> dict[str, Any]:
        """Get attributes from cheap price coordinator."""
        cheap_data = self.coordinator.data
        cheap_ranges = cheap_data.get("cheap_ranges", [])
        analysis_info = cheap_data.get("analysis_info", {})

        # Find current status and next cheap period
        now = dt_util.now()
        current_status, next_cheap_info, total_hours = _summarize_cheap_ranges(
            cheap_ranges,
            now=now,
            round_price=self._round_price,
        )

        # Build comprehensive status info
        last_update = cheap_data.get("last_update")
        trigger_time = cheap_data.get("trigger_time")

        status_info = {
            "current_status": current_status,
            "total_cheap_hours": total_hours,
            "last_calculation": last_update.isoformat()
            if isinstance(last_update, datetime)
            else last_update,
            "trigger_time": trigger_time.isoformat()
            if isinstance(trigger_time, datetime)
            else trigger_time,
        }

        # Add next cheap period info if available
        if next_cheap_info:
            status_info["next_cheap_period"] = next_cheap_info

        # Convert all datetime objects to strings before JSON serialization
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: datetime_serializer(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [datetime_serializer(item) for item in obj]
            return obj

        cheap_ranges_serializable = datetime_serializer(cheap_ranges)
        status_info_serializable = datetime_serializer(status_info)
        analysis_info_serializable = datetime_serializer(analysis_info)
        return {
            "cheap_ranges": cheap_ranges_serializable,
            "status_info": status_info_serializable,
            "analysis_info": analysis_info_serializable,
        }

    def _get_manual_analysis_attributes(self) -> dict[str, Any]:
        """Get attributes from manual cheap price analysis."""
        cheap_ranges = self._analyze_cheap_prices()

        # Get analysis info
        analysis_info = self._get_price_analysis_info()

        # Build status info similar to coordinator-backed sensor
        now = dt_util.now()
        current_status, next_cheap_info, total_hours = _summarize_cheap_ranges(
            cheap_ranges,
            now=now,
            round_price=self._round_price,
        )

        status_info = {
            "current_status": current_status,
            "total_cheap_hours": total_hours,
        }
        if next_cheap_info:
            status_info["next_cheap_period"] = next_cheap_info

        return {
            "cheap_ranges": cheap_ranges,
            "status_info": status_info,
            "analysis_info": analysis_info,
        }

    def _get_current_cheap_price_from_ranges(self) -> float | None:
        """Get current cheap price by checking ranges manually."""
        cheap_ranges = self._analyze_cheap_prices()
        now = dt_util.now()
        return _get_current_cheap_avg_price(cheap_ranges, now)

    def _analyze_cheap_prices(self) -> list[dict[str, Any]]:
        """Analyze price data to find cheap price ranges from NOW onwards."""
        return _analyze_cheap_prices_for_entity(self)

    def _group_consecutive_hours(
        self, cheap_prices: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Group consecutive cheap price hours into ranges."""
        if not cheap_prices:
            return []
        return group_consecutive_price_entries(
            cheap_prices,
            round_price=self._round_price,
        )

    def _get_price_analysis_info(self) -> dict[str, Any]:
        """Get price analysis information."""
        return _get_price_analysis_info_for_entity(self)


class NextCheapHoursEndSensor(RealElectricityPriceBaseSensor):
    """Sensor for the end time of the next cheap hours period."""

    def __init__(self, coordinator, description) -> None:
        """Initialize the next cheap hours end sensor."""
        super().__init__(coordinator, description)
        # This sensor should use the cheap price coordinator when available
        self._use_cheap_coordinator = hasattr(coordinator, "get_current_cheap_price")

    @property
    def native_value(self) -> datetime | None:
        """Return the end timestamp of the next cheap price period."""
        if self._use_cheap_coordinator:
            return self._get_next_cheap_period_end_from_coordinator()

        # Fallback to checking ranges manually
        return self._get_next_cheap_period_end_from_ranges()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return no attributes for this sensor."""
        return {}

    def _get_next_cheap_period_end_from_coordinator(self) -> datetime | None:
        """Get next cheap period end timestamp from cheap price coordinator."""
        if not (hasattr(self.coordinator, "data") and self.coordinator.data):
            return None

        cheap_data = self.coordinator.data
        cheap_ranges = cheap_data.get("cheap_ranges", [])

        if not cheap_ranges:
            return None

        now = dt_util.now()

        return _get_current_or_next_cheap_period_time(
            cheap_ranges, now, return_future="end"
        )

    def _get_next_cheap_period_end_from_ranges(self) -> datetime | None:
        """Get next cheap period end timestamp by checking ranges manually."""
        cheap_ranges = self._analyze_cheap_prices()

        if not cheap_ranges:
            return None

        now = dt_util.now()

        return _get_current_or_next_cheap_period_time(
            cheap_ranges, now, return_future="end"
        )

    def _analyze_cheap_prices(self) -> list[dict[str, Any]]:
        """Reuse the analysis from CheapHoursSensor."""
        return _analyze_cheap_prices_for_entity(self)


class NextCheapHoursStartSensor(RealElectricityPriceBaseSensor):
    """Sensor for next cheap electricity hours period start."""

    def __init__(self, coordinator, description) -> None:
        """Initialize the next cheap hours start sensor."""
        super().__init__(coordinator, description)
        # This sensor should use the cheap hours coordinator when available
        self._use_cheap_coordinator = hasattr(coordinator, "get_current_cheap_price")

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp when the next cheap price period starts."""
        if self._use_cheap_coordinator:
            return self._get_next_cheap_period_start_from_coordinator()

        # Fallback to checking ranges manually
        return self._get_next_cheap_period_start_from_ranges()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return no attributes for this sensor."""
        return {}

    def _get_next_cheap_period_start_from_coordinator(self) -> datetime | None:
        """Get next cheap period start timestamp from cheap price coordinator."""
        if not (hasattr(self.coordinator, "data") and self.coordinator.data):
            return None

        cheap_data = self.coordinator.data
        cheap_ranges = cheap_data.get("cheap_ranges", [])

        if not cheap_ranges:
            return None

        now = dt_util.now()

        return _get_next_cheap_period_start_time(cheap_ranges, now)

    def _get_next_cheap_period_start_from_ranges(self) -> datetime | None:
        """Get next cheap period start timestamp by checking ranges manually."""
        cheap_ranges = self._analyze_cheap_prices()

        if not cheap_ranges:
            return None

        now = dt_util.now()

        return _get_next_cheap_period_start_time(cheap_ranges, now)

    def _analyze_cheap_prices(self) -> list[dict[str, Any]]:
        """Reuse the analysis from CheapHoursSensor."""
        return _analyze_cheap_prices_for_entity(self)
