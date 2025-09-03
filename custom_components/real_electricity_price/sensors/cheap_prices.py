"""Cheap prices sensor for Real Electricity Price integration."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from homeassistant.util import dt as dt_util

from .base import RealElectricityPriceBaseSensor

_LOGGER = logging.getLogger(__name__)


class CheapPricesSensor(RealElectricityPriceBaseSensor):
    """Sensor for cheap electricity prices."""

    def __init__(self, coordinator, description):
        """Initialize the cheap prices sensor."""
        super().__init__(coordinator, description)
        # This sensor should use the cheap price coordinator when available
        self._use_cheap_coordinator = hasattr(coordinator, "get_current_cheap_price")

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of the next cheap price period."""
        if self._use_cheap_coordinator:
            return self._get_next_cheap_period_from_coordinator()

        # Fallback to checking ranges manually
        return self._get_next_cheap_period_from_ranges()

    def _get_next_cheap_period_from_coordinator(self) -> datetime | None:
        """Get next cheap period timestamp from cheap price coordinator."""
        if not (hasattr(self.coordinator, "data") and self.coordinator.data):
            return None

        cheap_data = self.coordinator.data
        cheap_ranges = cheap_data.get("cheap_ranges", [])
        
        if not cheap_ranges:
            return None

        now = datetime.now(UTC)

        # Find the next cheap period start time
        for range_data in cheap_ranges:
            try:
                start_time = datetime.fromisoformat(range_data["start_time"])
                end_time = datetime.fromisoformat(range_data["end_time"])

                # If we're currently in a cheap period, return its end time
                if start_time <= now < end_time:
                    return dt_util.as_local(end_time)

                # If this is a future cheap period, return its start time
                if start_time > now:
                    return dt_util.as_local(start_time)
            except (ValueError, KeyError):
                continue

        return None

    def _get_next_cheap_period_from_ranges(self) -> datetime | None:
        """Get next cheap period timestamp by checking ranges manually."""
        cheap_ranges = self._analyze_cheap_prices()
        
        if not cheap_ranges:
            return None

        now = datetime.now(UTC)

        # Find the next cheap period start time
        for range_data in cheap_ranges:
            try:
                start_time = datetime.fromisoformat(range_data["start_time"])
                end_time = datetime.fromisoformat(range_data["end_time"])

                # If we're currently in a cheap period, return its end time
                if start_time <= now < end_time:
                    return dt_util.as_local(end_time)

                # If this is a future cheap period, return its start time
                if start_time > now:
                    return dt_util.as_local(start_time)
            except (ValueError, KeyError):
                continue

        return None

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
        now = datetime.now(UTC)
        current_status = "inactive"
        next_cheap_info = None

        for range_data in cheap_ranges:
            start_time = datetime.fromisoformat(range_data["start_time"])
            end_time = datetime.fromisoformat(range_data["end_time"])

            if start_time <= now < end_time:
                current_status = "active"
            elif start_time > now and next_cheap_info is None:
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
            "cheap_price_ranges": json.dumps(cheap_ranges_serializable, indent=2),
            "status_info": json.dumps(status_info_serializable, indent=2),
            "analysis_info": json.dumps(analysis_info_serializable, indent=2),
        }

    def _get_manual_analysis_attributes(self) -> dict[str, Any]:
        """Get attributes from manual cheap price analysis."""
        cheap_ranges = self._analyze_cheap_prices()

        config = self.get_config()
        threshold = config.cheap_price_threshold

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
            "analysis_info": json.dumps(analysis_info, indent=2),
        }

    def _get_current_cheap_price_from_ranges(self) -> float | None:
        """Get current cheap price by checking ranges manually."""
        cheap_ranges = self._analyze_cheap_prices()
        now = datetime.now(UTC)

        for range_data in cheap_ranges:
            start_time = datetime.fromisoformat(range_data["start_time"])
            end_time = datetime.fromisoformat(range_data["end_time"])

            if start_time <= now < end_time:
                return range_data["avg_price"]

        return None

    def _analyze_cheap_prices(self) -> list[dict[str, Any]]:
        """Analyze price data to find cheap price ranges from NOW onwards."""
        if not self.coordinator.data:
            return []

        try:
            # Collect all hourly prices with valid data from current hour onwards
            now = datetime.now(UTC)
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
                            start_time = datetime.fromisoformat(
                                price_entry["start_time"]
                            )
                            # Include current hour and future hours only
                            if start_time >= current_hour_start:
                                all_prices.append(
                                    {
                                        "start_time": price_entry["start_time"],
                                        "end_time": price_entry["end_time"],
                                        "price": price_entry["actual_price"],
                                    }
                                )
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
            config = self.get_config()
            threshold_percent = config.cheap_price_threshold

            # Calculate maximum price that's considered "cheap"
            max_cheap_price = min_price * (1 + threshold_percent / 100)

            # Filter cheap prices
            cheap_df = df[df["price"] <= max_cheap_price].copy()

            if cheap_df.empty:
                _LOGGER.debug(
                    "No cheap prices found with threshold %s%%", threshold_percent
                )
                return []

            # Group consecutive hours into ranges
            cheap_ranges = self._group_consecutive_hours(cheap_df)

            _LOGGER.debug(
                "Found %d cheap price ranges (min: %.6f, max_cheap: %.6f, threshold: %.1f%%)",
                len(cheap_ranges),
                min_price,
                max_cheap_price,
                threshold_percent,
            )

            return cheap_ranges

        except Exception:
            _LOGGER.exception("Error analyzing cheap prices")
            return []

    def _group_consecutive_hours(self, cheap_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Group consecutive cheap price hours into ranges."""
        if cheap_df.empty:
            return []

        ranges = []
        current_range = None

        for _, row in cheap_df.iterrows():
            start_time = pd.to_datetime(row["start_time"])
            price = row["price"]

            if current_range is None:
                # Start new range
                current_range = {
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "hour_count": 1,
                    "min_price": self._round_price(price),
                    "max_price": self._round_price(price),
                    "avg_price": self._round_price(price),
                    "prices": [price],
                }
            else:
                # Check if this hour is consecutive to the current range
                current_end_time = pd.to_datetime(current_range["end_time"])
                if start_time == current_end_time:
                    # Extend current range
                    current_range["end_time"] = row["end_time"]
                    current_range["hour_count"] += 1
                    current_range["prices"].append(price)
                    current_range["min_price"] = self._round_price(
                        min(current_range["min_price"], price)
                    )
                    current_range["max_price"] = self._round_price(
                        max(current_range["max_price"], price)
                    )
                    current_range["avg_price"] = self._round_price(
                        sum(current_range["prices"]) / len(current_range["prices"])
                    )
                else:
                    # Finish current range and start new one
                    # Remove the prices list before adding to results (too verbose for attributes)
                    current_range.pop("prices", None)
                    ranges.append(current_range)

                    current_range = {
                        "start_time": row["start_time"],
                        "end_time": row["end_time"],
                        "hour_count": 1,
                        "min_price": self._round_price(price),
                        "max_price": self._round_price(price),
                        "avg_price": self._round_price(price),
                        "prices": [price],
                    }

        # Add the last range
        if current_range is not None:
            current_range.pop("prices", None)
            ranges.append(current_range)

        return ranges

    def _get_price_analysis_info(self) -> dict[str, Any]:
        """Get price analysis information."""
        if not self.coordinator.data:
            return {}

        try:
            # Collect all valid prices from NOW onwards only
            now = datetime.now(UTC)
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
                            start_time = datetime.fromisoformat(
                                price_entry["start_time"]
                            )
                            # Include current hour and future hours only
                            if start_time >= now.replace(
                                minute=0, second=0, microsecond=0
                            ):
                                future_prices.append(price_entry["actual_price"])
                        except (ValueError, KeyError):
                            continue

                if future_prices:
                    all_prices.extend(future_prices)
                    future_data_sources.append(
                        {
                            "source": data_key,
                            "date": day_data.get("date", "unknown"),
                            "hours_count": len(future_prices),
                        }
                    )

            if not all_prices:
                return {"data_sources": future_data_sources}

            # Calculate statistics
            min_price = min(all_prices)
            config = self.get_config()
            threshold_percent = config.cheap_price_threshold
            max_cheap_price = min_price * (1 + threshold_percent / 100)

            # Calculate actual analysis period based on future hours only
            total_future_hours = sum(
                source["hours_count"] for source in future_data_sources
            )

            return {
                "min_price": self._round_price(min_price),
                "max_cheap_price": self._round_price(max_cheap_price),
                "analysis_period_hours": total_future_hours,
                "data_sources": future_data_sources,
            }

        except Exception:
            _LOGGER.exception("Error getting price analysis info")
            return {}


class CheapPriceEndSensor(RealElectricityPriceBaseSensor):
    """Sensor for the end time of the next cheap price period."""

    def __init__(self, coordinator, description):
        """Initialize the cheap price end sensor."""
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

        now = datetime.now(UTC)

        # Find the next cheap period and return its end time
        for range_data in cheap_ranges:
            try:
                start_time = datetime.fromisoformat(range_data["start_time"])
                end_time = datetime.fromisoformat(range_data["end_time"])

                # If we're currently in a cheap period, return its end time
                if start_time <= now < end_time:
                    return dt_util.as_local(end_time)

                # If this is a future cheap period, return its end time
                if start_time > now:
                    return dt_util.as_local(end_time)
            except (ValueError, KeyError):
                continue

        return None

    def _get_next_cheap_period_end_from_ranges(self) -> datetime | None:
        """Get next cheap period end timestamp by checking ranges manually."""
        cheap_ranges = self._analyze_cheap_prices()
        
        if not cheap_ranges:
            return None

        now = datetime.now(UTC)

        # Find the next cheap period and return its end time
        for range_data in cheap_ranges:
            try:
                start_time = datetime.fromisoformat(range_data["start_time"])
                end_time = datetime.fromisoformat(range_data["end_time"])

                # If we're currently in a cheap period, return its end time
                if start_time <= now < end_time:
                    return dt_util.as_local(end_time)

                # If this is a future cheap period, return its end time
                if start_time > now:
                    return dt_util.as_local(end_time)
            except (ValueError, KeyError):
                continue

        return None

    def _analyze_cheap_prices(self) -> list[dict[str, Any]]:
        """Reuse the analysis from CheapPricesSensor."""
        # Create a temporary instance to reuse the analysis logic
        temp_sensor = CheapPricesSensor(self.coordinator, None)
        return temp_sensor._analyze_cheap_prices()
