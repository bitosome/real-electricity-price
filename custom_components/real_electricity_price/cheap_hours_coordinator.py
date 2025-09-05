"""Cheap Price DataUpdateCoordinator for real_electricity_price."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CHEAP_HOURS_BASE_PRICE_DEFAULT,
    CHEAP_HOURS_THRESHOLD_DEFAULT,
    CONF_CHEAP_HOURS_BASE_PRICE,
    CONF_CHEAP_HOURS_THRESHOLD,
    CONF_CHEAP_HOURS_UPDATE_TRIGGER,
    DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER,
    PRICE_DECIMAL_PRECISION,
    parse_time_string,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)


class CheapHoursDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching and updating cheap hours data separately from main price data."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        name: str,
        main_coordinator: RealElectricityPriceDataUpdateCoordinator,
        config_entry: RealElectricityPriceConfigEntry,
        update_method: Any = None,
    ) -> None:
        """Initialize the cheap hours coordinator."""
        super().__init__(
            hass=hass,
            logger=logger,
            name=name,
            update_method=update_method,
            # No default update interval - we use time-based triggers
            update_interval=None,
        )

        self.main_coordinator = main_coordinator
        self.config_entry = config_entry
        self._trigger_unsub: Callable[[], None] | None = None
        self._stop_unsub: Callable[[], None] | None = None

        # Runtime storage for UI-configurable values (to avoid config entry reloads)
        self._runtime_base_price: float | None = None
        self._runtime_threshold: float | None = None
        self._runtime_update_trigger: dict | None = None

        # Initialize the time-based trigger
        self.update_trigger_config()

        # Clean up on HA stop
        @callback
        def _on_stop(event) -> None:
            if self._trigger_unsub:
                self._trigger_unsub()
                self._trigger_unsub = None

        self._stop_unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, _on_stop
        )

    def set_runtime_base_price(self, value: float) -> None:
        """Set the runtime base price without triggering config reload."""
        self._runtime_base_price = value
        self.logger.info("Runtime base price updated to %s", value)

    def set_runtime_threshold(self, value: float) -> None:
        """Set the runtime threshold without triggering config reload."""
        self._runtime_threshold = value
        self.logger.info("Runtime threshold updated to %s%%", value)

    def set_runtime_update_trigger(self, value: dict) -> None:
        """Set the runtime update trigger and update the scheduled trigger."""
        self._runtime_update_trigger = value
        try:
            def_h, def_m, _ = parse_time_string(DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER)
        except Exception:
            def_h, def_m = 14, 30
        self.logger.info(
            "Runtime update trigger updated to %02d:%02d",
            value.get("hour", def_h),
            value.get("minute", def_m),
        )
        # Update the actual scheduled trigger with the new time
        self._update_trigger_schedule_from_runtime()

    def get_runtime_base_price(self) -> float:
        """Get the runtime base price, falling back to config if not set."""
        if self._runtime_base_price is not None:
            return self._runtime_base_price
        config = {**self.config_entry.data, **self.config_entry.options}
        return config.get(CONF_CHEAP_HOURS_BASE_PRICE, CHEAP_HOURS_BASE_PRICE_DEFAULT)

    def get_runtime_threshold(self) -> float:
        """Get the runtime threshold, falling back to config if not set."""
        if self._runtime_threshold is not None:
            return self._runtime_threshold
        config = {**self.config_entry.data, **self.config_entry.options}
        return config.get(CONF_CHEAP_HOURS_THRESHOLD, CHEAP_HOURS_THRESHOLD_DEFAULT)

    def get_runtime_update_trigger(self) -> dict:
        """Get the runtime update trigger, falling back to config if not set."""
        if self._runtime_update_trigger is not None:
            return self._runtime_update_trigger
        config = {**self.config_entry.data, **self.config_entry.options}
        trigger = config.get(
            CONF_CHEAP_HOURS_UPDATE_TRIGGER, DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER
        )
        if isinstance(trigger, dict):
            return trigger
        # Convert string format to dict
        if isinstance(trigger, str):
            parts = trigger.split(":")
            return {
                "hour": int(parts[0]),
                "minute": int(parts[1]) if len(parts) > 1 else 0,
            }
        return DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER

    def _update_trigger_schedule_from_runtime(self) -> None:
        """Update the trigger schedule using runtime values (doesn't trigger recalculation)."""
        # Get runtime trigger time
        trigger_time = self.get_runtime_update_trigger()

        # Remove existing trigger
        if self._trigger_unsub:
            self._trigger_unsub()
            self._trigger_unsub = None

        # Parse trigger time and set new schedule
        try:
            if isinstance(trigger_time, dict):
                def_h, def_m, _ = parse_time_string(DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER)
                hour = trigger_time.get("hour", def_h)
                minute = trigger_time.get("minute", def_m)
            else:
                def_h, def_m, _ = parse_time_string(DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER)
                hour = def_h
                minute = def_m

            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                msg = f"Invalid hour/minute: {hour}:{minute}"
                raise ValueError(msg)

            self._trigger_unsub = async_track_time_change(
                self.hass,
                self._handle_trigger,
                hour=hour,
                minute=minute,
                second=0,
            )
            _LOGGER.debug(
                "Cheap price coordinator trigger schedule updated to %02d:%02d",
                hour,
                minute,
            )
        except Exception as e:
            _LOGGER.exception(
                "Invalid runtime trigger time format '%s': %s", trigger_time, e
            )

    def update_trigger_config(self) -> None:
        """Update the trigger configuration based on current config."""
        # Get current config (options override data)
        config = {**self.config_entry.data, **self.config_entry.options}
        trigger_time = config.get(
            CONF_CHEAP_HOURS_UPDATE_TRIGGER, DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER
        )

        # Remove existing trigger
        if self._trigger_unsub:
            self._trigger_unsub()
            self._trigger_unsub = None

        # Parse trigger time (format: "HH:MM" or {"hour": H, "minute": M})
        try:
            # Always expect dict format from config entity
            if isinstance(trigger_time, dict):
                def_h, def_m, _ = parse_time_string(DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER)
                hour = trigger_time.get("hour", def_h)
                minute = trigger_time.get("minute", def_m)
            elif isinstance(trigger_time, str):
                time_parts = trigger_time.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            else:
                hour, minute, _ = parse_time_string(DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                msg = f"Invalid hour/minute: {hour}:{minute}"
                raise ValueError(msg)
            self._trigger_unsub = async_track_time_change(
                self.hass,
                self._handle_trigger,
                hour=hour,
                minute=minute,
                second=0,
            )
            _LOGGER.debug(
                "Cheap price coordinator trigger set for %02d:%02d", hour, minute
            )
        except Exception as e:
            _LOGGER.exception("Invalid trigger time format '%s': %s", trigger_time, e)

    @callback
    def _handle_trigger(self, now: datetime.datetime) -> None:
        """Handle the scheduled trigger to update cheap price data."""
        _LOGGER.debug("Cheap price trigger fired at %s", now)
        # Create a task to update the data
        self.hass.async_create_task(self.async_manual_update())

    async def async_manual_update(self) -> None:
        """Manually trigger an update of cheap price data."""
        _LOGGER.debug("Manual cheap price update requested")

        # Get fresh data from main coordinator if needed
        if not self.main_coordinator.data:
            _LOGGER.debug("No main coordinator data, requesting refresh first")
            await self.main_coordinator.async_request_refresh()

        # Now update our own data
        await self.async_request_refresh()

    async def _async_update_data(self) -> Any:
        """Update cheap price data based on main coordinator data."""
        try:
            # Get data from main coordinator
            main_data = self.main_coordinator.data
            if not main_data:
                _LOGGER.warning(
                    "No data available from main coordinator for cheap price calculation"
                )
                return None

            # Extract cheap price analysis data
            cheap_data = self._analyze_cheap_prices(main_data)

            # Add metadata
            cheap_data["last_update"] = datetime.datetime.now(datetime.UTC)
            cheap_data["trigger_time"] = self._get_trigger_time()

            _LOGGER.debug(
                "Cheap price data updated with %d ranges",
                len(cheap_data.get("cheap_ranges", [])),
            )
            return cheap_data

        except Exception as e:
            _LOGGER.error("Error updating cheap price data: %s", e, exc_info=True)
            return None

    def _get_trigger_time(self) -> str:
        """Get the current trigger time configuration."""
        config = {**self.config_entry.data, **self.config_entry.options}
        return config.get(
            CONF_CHEAP_HOURS_UPDATE_TRIGGER, DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER
        )

    def _analyze_cheap_prices(self, main_data: dict) -> dict[str, Any]:
        """
        Analyze price data to find cheap price ranges.

        This method performs the same analysis as the sensor's _analyze_cheap_prices method
        but returns the data in a format suitable for the coordinator.
        """
        if not main_data:
            return {"cheap_ranges": [], "analysis_info": {}}

        try:
            # Collect all hourly prices with valid data
            all_prices = []
            for data_key in main_data:
                day_data = main_data[data_key]
                if not isinstance(day_data, dict):
                    continue

                # Only include data from days where actual data is available
                data_available = day_data.get("data_available", False)
                if not data_available:
                    continue

                hourly_prices = day_data.get("hourly_prices", [])
                for price_entry in hourly_prices:
                    # Only include entries with valid price data
                    if price_entry.get("actual_price") is not None:
                        all_prices.append(
                            {
                                "start_time": price_entry["start_time"],
                                "end_time": price_entry["end_time"],
                                "price": price_entry["actual_price"],
                                "date": day_data.get("date"),
                            }
                        )

            if not all_prices:
                _LOGGER.debug("No valid price data available for cheap price analysis")
                return {"cheap_ranges": [], "analysis_info": {}}

            # Convert to list of dicts and add parsed datetime for analysis
            price_list = []
            for price in all_prices:
                try:
                    # Parse datetime string
                    start_time_dt = datetime.datetime.fromisoformat(
                        price["start_time"]
                    )
                    price_list.append({**price, "start_time_dt": start_time_dt})
                except Exception as e:
                    _LOGGER.warning(
                        f"Failed to parse datetime {price.get('start_time')}: {e}"
                    )
                    continue

            # Sort by start time
            price_list.sort(key=lambda x: x["start_time_dt"])

            # Filter for future prices only (NOW onwards)
            current_time = datetime.datetime.now(datetime.UTC)
            future_prices = [
                p for p in price_list if p["start_time_dt"] >= current_time
            ]

            if not future_prices:
                _LOGGER.debug("No future price data available for cheap price analysis")
                return {"cheap_ranges": [], "analysis_info": {}}

            # Get base price and threshold from runtime storage or configuration
            base_price = self.get_runtime_base_price()
            threshold_percent = self.get_runtime_threshold()
            # Defensive: ensure base_price and threshold_percent are numbers
            if isinstance(base_price, (dict, str)):
                try:
                    base_price = float(base_price)
                except Exception:
                    base_price = CHEAP_HOURS_BASE_PRICE_DEFAULT
            if isinstance(threshold_percent, (dict, str)):
                try:
                    threshold_percent = float(threshold_percent)
                except Exception:
                    threshold_percent = CHEAP_HOURS_THRESHOLD_DEFAULT

            # Calculate maximum price that's considered "cheap" based on base price and threshold
            # Cheap period: price ≤ base_price OR price ≤ (base_price × (1 + threshold_percent/100))
            max_cheap_price_by_threshold = base_price * (1 + threshold_percent / 100)
            max(base_price, max_cheap_price_by_threshold)

            # Filter cheap prices: price ≤ base_price OR price ≤ (base_price × (1 + threshold_percent/100))
            cheap_prices = [
                p
                for p in future_prices
                if isinstance(p["price"], (int, float))
                and (
                    p["price"] <= base_price
                    or p["price"] <= max_cheap_price_by_threshold
                )
            ]

            if not cheap_prices:
                # Calculate actual price statistics for debugging
                if future_prices:
                    actual_prices = [
                        p["price"]
                        for p in future_prices
                        if isinstance(p["price"], (int, float))
                    ]
                    if actual_prices:
                        min_price = min(actual_prices)
                        max_price = max(actual_prices)
                        avg_price = sum(actual_prices) / len(actual_prices)
                        _LOGGER.warning(
                            "No cheap prices found! Current settings: base_price=%.6f, threshold=%.1f, "
                            "max_cheap_by_threshold=%.6f. Logic: price ≤ %.6f OR price ≤ %.6f. "
                            "Actual price range: %.6f - %.6f (avg: %.6f) for %d future hours. "
                            "Consider lowering base price to %.6f or increasing threshold.",
                            base_price,
                            threshold_percent,
                            max_cheap_price_by_threshold,
                            base_price,
                            max_cheap_price_by_threshold,
                            min_price,
                            max_price,
                            avg_price,
                            len(actual_prices),
                            min_price * 0.9,  # Suggest 90% of minimum price
                        )
                    else:
                        _LOGGER.debug("No valid price data available")
                else:
                    _LOGGER.debug("No future price data available")
                return {
                    "cheap_ranges": [],
                    "analysis_info": {
                        "base_price": base_price,
                        "threshold_percent": threshold_percent,
                        "max_cheap_by_threshold": max_cheap_price_by_threshold,
                    },
                }

            # Group consecutive hours into ranges
            cheap_ranges = self._group_consecutive_hours(cheap_prices)

            # Calculate analysis period based on actual future data analyzed
            analysis_period_hours = len(future_prices)

            analysis_info = {
                "base_price": round(base_price, PRICE_DECIMAL_PRECISION),
                "max_cheap_by_threshold": round(
                    max_cheap_price_by_threshold, PRICE_DECIMAL_PRECISION
                ),
                "threshold_percent": threshold_percent,
                "total_cheap_hours": len(cheap_ranges),
                "analysis_period_hours": analysis_period_hours,
            }

            _LOGGER.debug(
                "Cheap price analysis complete: %d ranges found (base: %.6f, threshold: %.1f, max_cheap_by_threshold: %.6f)",
                len(cheap_ranges),
                base_price,
                threshold_percent,
                max_cheap_price_by_threshold,
            )

            return {
                "cheap_ranges": cheap_ranges,
                "analysis_info": analysis_info,
            }

        except Exception as e:
            _LOGGER.error("Error analyzing cheap prices: %s", e, exc_info=True)
            return {"cheap_ranges": [], "analysis_info": {}}

    def _group_consecutive_hours(
        self, cheap_prices: list[dict]
    ) -> list[dict[str, Any]]:
        """Group consecutive cheap hours into time ranges."""
        if not cheap_prices:
            return []

        ranges = []
        current_range = None

        for price_data in cheap_prices:
            start_time_dt = price_data["start_time_dt"]
            price = price_data["price"]

            if current_range is None:
                # Start new range
                current_range = {
                    "start_time": price_data["start_time"],
                    "end_time": price_data["end_time"],
                    "price": price,  # Use first price in range
                    "min_price": price,
                    "max_price": price,
                    "avg_price": price,
                    "hour_count": 1,
                    "prices": [price],
                }
            else:
                # Check if this hour is consecutive to the current range
                try:
                    current_end_dt = datetime.datetime.fromisoformat(
                        current_range["end_time"]
                    )
                    if start_time_dt == current_end_dt:
                        # Extend current range
                        current_range["end_time"] = price_data["end_time"]
                        current_range["hour_count"] += 1
                        current_range["prices"].append(price)
                        current_range["min_price"] = min(
                            current_range["min_price"], price
                        )
                        current_range["max_price"] = max(
                            current_range["max_price"], price
                        )
                        current_range["avg_price"] = sum(current_range["prices"]) / len(
                            current_range["prices"]
                        )
                    else:
                        # Finish current range and start new one
                        # Remove the prices list before adding to results (too verbose for attributes)
                        current_range.pop("prices", None)
                        ranges.append(current_range)

                        current_range = {
                            "start_time": price_data["start_time"],
                            "end_time": price_data["end_time"],
                            "price": price,
                            "min_price": price,
                            "max_price": price,
                            "avg_price": price,
                            "hour_count": 1,
                            "prices": [price],
                        }
                except Exception as e:
                    _LOGGER.warning(
                        f"Error parsing datetime for consecutive check: {e}"
                    )
                    # Start new range on error
                    current_range.pop("prices", None)
                    ranges.append(current_range)

                    current_range = {
                        "start_time": price_data["start_time"],
                        "end_time": price_data["end_time"],
                        "price": price,
                        "min_price": price,
                        "max_price": price,
                        "avg_price": price,
                        "hour_count": 1,
                        "prices": [price],
                    }

        # Add the last range
        if current_range is not None:
            current_range.pop("prices", None)
            ranges.append(current_range)

        return ranges

    def get_current_cheap_price(self) -> float | None:
        """Get the current cheap price value if we're in a cheap price period."""
        if not self.data or not self.data.get("cheap_ranges"):
            return None

        now = datetime.datetime.now(datetime.UTC)

        # Check if we're currently in a cheap price range
        for range_data in self.data["cheap_ranges"]:
            start_time = datetime.datetime.fromisoformat(range_data["start_time"])
            end_time = datetime.datetime.fromisoformat(range_data["end_time"])

            if start_time <= now < end_time:
                return round(range_data["price"], PRICE_DECIMAL_PRECISION)

        return None

    def get_next_cheap_price(self) -> dict[str, Any] | None:
        """Get information about the next upcoming cheap price period."""
        if not self.data or not self.data.get("cheap_ranges"):
            return None

        now = datetime.datetime.now(datetime.UTC)

        # Find the next cheap price range
        next_range = None
        min_time_diff = None

        for range_data in self.data["cheap_ranges"]:
            start_time = datetime.datetime.fromisoformat(range_data["start_time"])

            if start_time > now:  # Future range
                time_diff = (start_time - now).total_seconds()
                if min_time_diff is None or time_diff < min_time_diff:
                    min_time_diff = time_diff
                    next_range = range_data

        return next_range
