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
    CHEAP_HOURS_THRESHOLD_DEFAULT,
    CONF_CHEAP_HOURS_THRESHOLD,
    CONF_CHEAP_HOURS_UPDATE_TRIGGER,
    DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER,
    PRICE_DECIMAL_PRECISION,
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
            if isinstance(trigger_time, dict):
                # Handle TimeSelector format
                hour = trigger_time.get("hour", 14)
                minute = trigger_time.get("minute", 30)
            else:
                # Handle legacy string format (may include seconds like "HH:MM:SS")
                time_parts = str(trigger_time).split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0

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

        except (ValueError, AttributeError, KeyError, IndexError) as e:
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
                    start_time_dt = datetime.datetime.fromisoformat(price["start_time"].replace('Z', '+00:00'))
                    price_list.append({
                        **price,
                        "start_time_dt": start_time_dt
                    })
                except Exception as e:
                    _LOGGER.warning(f"Failed to parse datetime {price.get('start_time')}: {e}")
                    continue

            # Sort by start time
            price_list.sort(key=lambda x: x["start_time_dt"])

            # Filter for future prices only (NOW onwards)
            current_time = datetime.datetime.now(datetime.UTC)
            future_prices = [p for p in price_list if p["start_time_dt"] >= current_time]

            if not future_prices:
                _LOGGER.debug("No future price data available for cheap price analysis")
                return {"cheap_ranges": [], "analysis_info": {}}

            # Find minimum price
            min_price = min(p["price"] for p in future_prices)

            # Get threshold from configuration
            config = {**self.config_entry.data, **self.config_entry.options}
            threshold_percent = config.get(
                CONF_CHEAP_HOURS_THRESHOLD, CHEAP_HOURS_THRESHOLD_DEFAULT
            )

            # Calculate maximum price that's considered "cheap"
            max_cheap_price = min_price * (1 + threshold_percent / 100)

            # Filter cheap prices
            cheap_prices = [p for p in future_prices if p["price"] <= max_cheap_price]

            if not cheap_prices:
                _LOGGER.debug(
                    "No cheap prices found with threshold %s%%", threshold_percent
                )
                return {
                    "cheap_ranges": [],
                    "analysis_info": {
                        "min_price": min_price,
                        "threshold_percent": threshold_percent,
                    },
                }

            # Group consecutive hours into ranges
            cheap_ranges = self._group_consecutive_hours(cheap_prices)

            # Calculate analysis period based on actual future data analyzed
            analysis_period_hours = len(future_prices)

            analysis_info = {
                "min_price": round(min_price, PRICE_DECIMAL_PRECISION),
                "max_cheap_price": round(max_cheap_price, PRICE_DECIMAL_PRECISION),
                "threshold_percent": threshold_percent,
                "total_cheap_hours": len(cheap_ranges),
                "analysis_period_hours": analysis_period_hours,
            }

            _LOGGER.debug(
                "Cheap price analysis complete: %d ranges found (min: %.6f, max_cheap: %.6f, threshold: %.1f%%)",
                len(cheap_ranges),
                min_price,
                max_cheap_price,
                threshold_percent,
            )

            return {
                "cheap_ranges": cheap_ranges,
                "analysis_info": analysis_info,
            }

        except Exception as e:
            _LOGGER.error("Error analyzing cheap prices: %s", e, exc_info=True)
            return {"cheap_ranges": [], "analysis_info": {}}

    def _group_consecutive_hours(self, cheap_prices: list[dict]) -> list[dict[str, Any]]:
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
                    current_end_dt = datetime.datetime.fromisoformat(current_range["end_time"].replace('Z', '+00:00'))
                    if start_time_dt == current_end_dt:
                        # Extend current range
                        current_range["end_time"] = price_data["end_time"]
                        current_range["hour_count"] += 1
                        current_range["prices"].append(price)
                        current_range["min_price"] = min(current_range["min_price"], price)
                        current_range["max_price"] = max(current_range["max_price"], price)
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
                    _LOGGER.warning(f"Error parsing datetime for consecutive check: {e}")
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
