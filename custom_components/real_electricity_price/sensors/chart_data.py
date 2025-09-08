"""Chart data sensor for ApexCharts display."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

from ..const import (
    CHART_COLOR_CHEAP_CURRENT_HOUR_DEFAULT,
    CHART_COLOR_CHEAP_HOURS_DEFAULT,
    CHART_COLOR_CURRENT_HOUR_DEFAULT,
    CHART_COLOR_FUTURE_HOURS_DEFAULT,
    CHART_COLOR_PAST_HOURS_DEFAULT,
    CONF_CALCULATE_CHEAP_HOURS,
    CONF_CHART_COLOR_CHEAP_CURRENT_HOUR,
    CONF_CHART_COLOR_CHEAP_HOURS,
    CONF_CHART_COLOR_CURRENT_HOUR,
    CONF_CHART_COLOR_FUTURE_HOURS,
    CONF_CHART_COLOR_PAST_HOURS,
)
from ..entity_descriptions import SENSOR_CHART_DATA
from .base import RealElectricityPriceBaseSensor

_LOGGER = logging.getLogger(__name__)


class ChartDataSensor(RealElectricityPriceBaseSensor):
    """Sensor providing pre-processed data for ApexCharts display."""

    def __init__(self, coordinator, description) -> None:
        """Initialize the chart data sensor."""
        super().__init__(coordinator, description)
        self._chart_data = []
        self._last_update_iso: str | None = None

    @property
    def native_value(self) -> int:
        """Return the count of data points."""
        return len(self._chart_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return chart data with colors as attributes."""
        return {
            "chart_data": self._chart_data,
            "last_update": self._last_update_iso,
        }

    def _handle_coordinator_update(self) -> None:  # type: ignore[override]
        """Recalculate chart data when the main coordinator notifies listeners."""
        try:
            self._update_chart_data()
        finally:
            # Call parent to write state
            super()._handle_coordinator_update()

    def _update_chart_data(self) -> None:
        """Update the chart data with proper coloring."""
        if not self.coordinator.data:
            self._chart_data = []
            self._last_update_iso = dt_util.now().isoformat()
            return

        now = dt_util.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        current_hour_ts = int(current_hour.timestamp() * 1000)
        next_hour_ts = current_hour_ts + 3600000

        # Get cheap hours data
        cheap_ranges = self._get_cheap_hour_ranges()

        # Collect hourly price data for 48 hours: today + tomorrow only
        all_data = []
        
        # Only process today and tomorrow data for 48-hour chart display
        for data_key in ["today", "tomorrow"]:
            if data_key not in self.coordinator.data:
                continue
                
            day_data = self.coordinator.data[data_key]
            if not isinstance(day_data, dict) or not day_data.get("data_available", False):
                continue

            hourly_prices = day_data.get("hourly_prices", [])
            for price_entry in hourly_prices:
                if price_entry.get("actual_price") is not None:
                    try:
                        start_time = dt_util.parse_datetime(price_entry["start_time"])
                        if start_time:
                            ts = int(start_time.timestamp() * 1000)
                            price = float(price_entry["actual_price"])
                            
                            # Determine color based on time and cheap hours
                            color = self._get_bar_color(ts, current_hour_ts, next_hour_ts, cheap_ranges)
                            
                            all_data.append({
                                "x": ts,
                                "y": price,
                                "fillColor": color,
                                "start_time": price_entry["start_time"],
                                "formatted_time": start_time.strftime("%H:%M"),
                                "formatted_price": f"{price:.4f} €/kWh"
                            })
                    except (ValueError, KeyError, TypeError):
                        continue

        # Sort by timestamp
        all_data.sort(key=lambda x: x["x"])
        self._chart_data = all_data
        self._last_update_iso = dt_util.now().isoformat()
        
        # Debug logging for the first few data points
        if all_data:
            _LOGGER.debug(f"Chart data generated: {len(all_data)} points. Sample: {all_data[:3]}")

    def _get_cheap_hour_ranges(self) -> list[dict]:
        """Get cheap hour ranges from the cheap hours sensor."""
        try:
            # Respect configuration: if cheap hours are disabled, don't compute ranges
            cfg = {}
            if hasattr(self.coordinator, 'config_entry') and self.coordinator.config_entry:
                cfg.update(self.coordinator.config_entry.data or {})
                cfg.update(self.coordinator.config_entry.options or {})
            if not cfg.get(CONF_CALCULATE_CHEAP_HOURS, True):
                return []

            # Try to pull from the cheap-hours coordinator if linked via the main coordinator
            if hasattr(self.coordinator, 'data') and self.coordinator.data:
                for attr in ('_cheap_price_coordinator', 'cheap_hours_coordinator', '_cheap_coordinator'):
                    if hasattr(self.coordinator, attr):
                        cheap_coord = getattr(self.coordinator, attr)
                        if cheap_coord and getattr(cheap_coord, 'data', None):
                            return cheap_coord.data.get('cheap_ranges', [])

            # Fallback: compute manually using acceptable price
            return self._analyze_cheap_prices()
        except Exception:
            _LOGGER.debug("Could not get cheap hours data, using empty ranges")
            return []

    def _get_bar_color(self, timestamp: int, current_hour_ts: int, next_hour_ts: int, cheap_ranges: list) -> str:
        """Determine the color for a bar based on time and cheap hour status."""
        try:
            # Get configured colors from raw config data
            config_data = {}
            if hasattr(self.coordinator, 'config_entry') and self.coordinator.config_entry:
                config_data.update(self.coordinator.config_entry.data or {})
                config_data.update(self.coordinator.config_entry.options or {})
            
            # Get colors with fallbacks to defaults
            color_cheap = self._convert_color_to_hex(config_data.get(CONF_CHART_COLOR_CHEAP_HOURS, CHART_COLOR_CHEAP_HOURS_DEFAULT))
            color_cheap_current = self._convert_color_to_hex(config_data.get(CONF_CHART_COLOR_CHEAP_CURRENT_HOUR, CHART_COLOR_CHEAP_CURRENT_HOUR_DEFAULT))
            color_current = self._convert_color_to_hex(config_data.get(CONF_CHART_COLOR_CURRENT_HOUR, CHART_COLOR_CURRENT_HOUR_DEFAULT))
            color_future = self._convert_color_to_hex(config_data.get(CONF_CHART_COLOR_FUTURE_HOURS, CHART_COLOR_FUTURE_HOURS_DEFAULT))
            color_past = self._convert_color_to_hex(config_data.get(CONF_CHART_COLOR_PAST_HOURS, CHART_COLOR_PAST_HOURS_DEFAULT))
        except Exception as e:
            _LOGGER.error(f"Error getting color configuration: {e}")
            # Use all defaults if config fails
            color_cheap = CHART_COLOR_CHEAP_HOURS_DEFAULT
            color_cheap_current = CHART_COLOR_CHEAP_CURRENT_HOUR_DEFAULT
            color_current = CHART_COLOR_CURRENT_HOUR_DEFAULT
            color_future = CHART_COLOR_FUTURE_HOURS_DEFAULT
            color_past = CHART_COLOR_PAST_HOURS_DEFAULT
        
        # Check if this is a cheap hour
        is_cheap_hour = False
        for range_data in cheap_ranges:
            try:
                start_time = dt_util.parse_datetime(range_data["start_time"])
                end_time = dt_util.parse_datetime(range_data["end_time"])
                if start_time and end_time:
                    start_ts = int(start_time.timestamp() * 1000)
                    end_ts = int(end_time.timestamp() * 1000)
                    if start_ts <= timestamp < end_ts:
                        is_cheap_hour = True
                        break
            except (ValueError, KeyError, TypeError):
                continue

        # Determine color based on time and cheap hour status
        if timestamp == current_hour_ts:
            # Current hour: use cheap current hour color if it's cheap, otherwise current hour color
            return color_cheap_current if is_cheap_hour else color_current
        elif is_cheap_hour:
            # Non-current cheap hour: use cheap hour color
            return color_cheap
        elif timestamp >= next_hour_ts:
            # Future non-cheap hour: use future hour color
            return color_future
        else:
            # Past non-cheap hour: use past hour color
            return color_past

    def _analyze_cheap_prices(self) -> list[dict[str, Any]]:
        """Analyze price data to find cheap price ranges (fallback method)."""
        if not self.coordinator.data:
            return []

        try:
            # Collect all hourly prices with valid data from current hour onwards
            now = dt_util.now()
            current_hour_start = now.replace(minute=0, second=0, microsecond=0)
            all_prices = []

            # Only process today and tomorrow data for 48-hour analysis
            for data_key in ["today", "tomorrow"]:
                if data_key not in self.coordinator.data:
                    continue
                    
                day_data = self.coordinator.data[data_key]
                if not isinstance(day_data, dict):
                    continue

                data_available = day_data.get("data_available", False)
                if not data_available:
                    continue

                hourly_prices = day_data.get("hourly_prices", [])
                for price_entry in hourly_prices:
                    if price_entry.get("actual_price") is not None:
                        try:
                            start_time = dt_util.parse_datetime(price_entry["start_time"])
                            if start_time >= current_hour_start:
                                all_prices.append({
                                    "start_time": price_entry["start_time"],
                                    "end_time": price_entry["end_time"],
                                    "price": price_entry["actual_price"],
                                })
                        except (ValueError, KeyError):
                            continue

            if not all_prices:
                return []

            # Sort prices by start time
            all_prices.sort(key=lambda x: dt_util.parse_datetime(x["start_time"]))

            # Get acceptable price from configuration
            config = self.get_config()
            acceptable_price = config.acceptable_price

            # Filter cheap prices: price ≤ acceptable_price
            cheap_prices = [
                price_entry
                for price_entry in all_prices
                if price_entry["price"] <= acceptable_price
            ]

            if not cheap_prices:
                return []

            # Group consecutive hours into ranges
            return self._group_consecutive_hours(cheap_prices)

        except Exception:
            _LOGGER.exception("Error analyzing cheap prices")
            return []

    def _group_consecutive_hours(self, cheap_prices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Group consecutive cheap price hours into ranges."""
        if not cheap_prices:
            return []

        ranges = []
        current_range = None

        for price_entry in cheap_prices:
            start_time = dt_util.parse_datetime(price_entry["start_time"])
            price = price_entry["price"]

            if current_range is None:
                # Start new range
                current_range = {
                    "start_time": price_entry["start_time"],
                    "end_time": price_entry["end_time"],
                    "hour_count": 1,
                    "min_price": self._round_price(price),
                    "max_price": self._round_price(price),
                    "avg_price": self._round_price(price),
                    "prices": [price],
                }
            else:
                # Check if this hour is consecutive to the current range
                current_end_time = dt_util.parse_datetime(current_range["end_time"])
                if start_time == current_end_time:
                    # Extend current range
                    current_range["end_time"] = price_entry["end_time"]
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
                    current_range.pop("prices", None)
                    ranges.append(current_range)
                    
                    current_range = {
                        "start_time": price_entry["start_time"],
                        "end_time": price_entry["end_time"],
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

    def _convert_color_to_hex(self, color) -> str:
        """Convert color from various formats to hex string."""
        try:
            if color is None:
                # Handle None values
                return "#808080"
            
            if isinstance(color, str):
                # Already a hex string, validate and return
                if color.startswith("#") and len(color) in [4, 7]:
                    return color
                else:
                    _LOGGER.warning(f"Invalid hex color format: {color}")
                    return "#808080"
            
            elif isinstance(color, (list, tuple)) and len(color) >= 3:
                # RGB array [r, g, b], convert to hex
                try:
                    r, g, b = float(color[0]), float(color[1]), float(color[2])
                    # Ensure values are in 0-255 range
                    r = max(0, min(255, int(r)))
                    g = max(0, min(255, int(g)))
                    b = max(0, min(255, int(b)))
                    return f"#{r:02x}{g:02x}{b:02x}"
                except (ValueError, TypeError, IndexError) as e:
                    _LOGGER.warning(f"Invalid RGB color values: {color}, error: {e}")
                    return "#808080"
            
            elif isinstance(color, dict):
                # Handle dict format that might come from color picker
                if "r" in color and "g" in color and "b" in color:
                    try:
                        r = max(0, min(255, int(float(color["r"]))))
                        g = max(0, min(255, int(float(color["g"]))))
                        b = max(0, min(255, int(float(color["b"]))))
                        return f"#{r:02x}{g:02x}{b:02x}"
                    except (ValueError, TypeError, KeyError) as e:
                        _LOGGER.warning(f"Invalid RGB dict color values: {color}, error: {e}")
                        return "#808080"
            
            else:
                # Unknown format
                _LOGGER.warning(f"Unknown color format: {type(color)} = {color}")
                return "#808080"
                
        except Exception as e:
            _LOGGER.error(f"Error converting color {color}: {e}")
            return "#808080"

    async def async_update(self) -> None:
        """Update the sensor."""
        await super().async_update()
        self._update_chart_data()
