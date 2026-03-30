"""Cheap Price DataUpdateCoordinator for real_electricity_price."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cheap_hours_analysis import (
    collect_hourly_price_entries,
    group_consecutive_price_entries,
)
from .const import (
    ACCEPTABLE_PRICE_DEFAULT,
    CONF_ACCEPTABLE_PRICE,
    PRICE_DECIMAL_PRECISION,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)


class CheapHoursDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage cheap hours data synchronized with main price data."""

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
            # No default update interval - we sync with main coordinator
            update_interval=None,
        )

        self.main_coordinator = main_coordinator
        self.config_entry = config_entry
        # Runtime storage for UI-configurable values (to avoid config entry reloads)
        self._runtime_acceptable_price: float | None = None

    def set_runtime_acceptable_price(self, value: float) -> None:
        """Set the runtime acceptable price without triggering config reload."""
        self._runtime_acceptable_price = value
        self.logger.info("Runtime acceptable price updated to %s", value)

    def get_runtime_acceptable_price(self) -> float:
        """Get the runtime acceptable price, falling back to config if not set."""
        if self._runtime_acceptable_price is not None:
            return self._runtime_acceptable_price
        config = {**self.config_entry.data, **self.config_entry.options}
        return config.get(CONF_ACCEPTABLE_PRICE, ACCEPTABLE_PRICE_DEFAULT)


    async def async_manual_update(self) -> None:
        """
        Manually trigger cheap hours calculation.

        This should only be called in 2 scenarios:
        1) Integration startup (when tomorrow's prices are available)
        2) Manual trigger via button/service call
        """
        _LOGGER.debug("Cheap hours calculation requested")

        # If called after successful main coordinator sync, data should be available
        # Don't trigger additional API calls to avoid cascading failures
        if not self.main_coordinator.data:
            _LOGGER.debug("No main coordinator data available, skipping cheap hours update to avoid API conflicts")
            return

        # Now update our own data
        await self.async_request_refresh()

        # Notify main-coordinator entities (e.g., chart) to re-render using new ranges
        try:
            if self.main_coordinator is not None:
                # This does not fetch; it only triggers dependent entities to recalc
                self.main_coordinator.async_update_listeners()
        except Exception as e:
            self.logger.debug(
                "Could not notify main coordinator listeners after cheap-hours update: %s",
                e,
            )

    async def _async_update_data(self) -> Any:
        """Update cheap price data based on main coordinator data."""
        # Get data from main coordinator
        main_data = self.main_coordinator.data
        if not main_data:
            _LOGGER.debug(
                "No data available from main coordinator for cheap price calculation - waiting for API data"
            )
            return self.data  # Preserve previous data if available

        try:
            # Extract cheap price analysis data
            cheap_data = self._analyze_cheap_prices(main_data)

            # Add metadata
            cheap_data["last_update"] = datetime.datetime.now(datetime.UTC)

            _LOGGER.debug(
                "Cheap price data updated with %d ranges",
                len(cheap_data.get("cheap_ranges", [])),
            )
            return cheap_data

        except Exception as exception:
            raise UpdateFailed(
                f"Error updating cheap price data: {exception}"
            ) from exception


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
            all_prices = collect_hourly_price_entries(main_data)

            if not all_prices:
                _LOGGER.debug("No valid price data available for cheap price analysis")
                return {"cheap_ranges": [], "analysis_info": {}}

            # Filter for future prices only (NOW onwards)
            current_time = datetime.datetime.now(datetime.UTC)
            future_prices = [
                p for p in all_prices if p["start_time_dt"] >= current_time
            ]

            if not future_prices:
                _LOGGER.debug("No future price data available for cheap price analysis")
                return {"cheap_ranges": [], "analysis_info": {}}

            # Get acceptable price from runtime storage or configuration
            acceptable_price = self.get_runtime_acceptable_price()
            # Defensive: ensure acceptable_price is a number
            if isinstance(acceptable_price, (dict, str)):
                try:
                    acceptable_price = float(acceptable_price)
                except Exception:
                    acceptable_price = ACCEPTABLE_PRICE_DEFAULT

            # Simple logic: any price <= acceptable_price is considered cheap
            # Filter cheap prices: price ≤ acceptable_price
            cheap_prices = [
                p
                for p in future_prices
                if isinstance(p["price"], (int, float))
                and p["price"] <= acceptable_price
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
                            "No cheap prices found! Current acceptable price: %.6f. "
                            "Actual price range: %.6f - %.6f (avg: %.6f) for %d future hours. "
                            "Consider raising acceptable price to at least %.6f.",
                            acceptable_price,
                            min_price,
                            max_price,
                            avg_price,
                            len(actual_prices),
                            min_price,  # Suggest the minimum price
                        )
                    else:
                        _LOGGER.debug("No valid price data available")
                else:
                    _LOGGER.debug("No future price data available")
                return {
                    "cheap_ranges": [],
                    "analysis_info": {
                        "acceptable_price": acceptable_price,
                    },
                }

            # Group consecutive hours into ranges
            cheap_ranges = group_consecutive_price_entries(
                cheap_prices,
                include_first_price_field=True,
            )

            # Calculate analysis period based on actual future data analyzed
            analysis_period_hours = len(future_prices)

            analysis_info = {
                "acceptable_price": round(acceptable_price, PRICE_DECIMAL_PRECISION),
                "total_cheap_hours": len(cheap_ranges),
                "analysis_period_hours": analysis_period_hours,
            }

            _LOGGER.debug(
                "Cheap price analysis complete: %d ranges found (acceptable_price: %.6f)",
                len(cheap_ranges),
                acceptable_price,
            )

            return {
                "cheap_ranges": cheap_ranges,
                "analysis_info": analysis_info,
            }

        except Exception as e:
            _LOGGER.error("Error analyzing cheap prices: %s", e, exc_info=True)
            return {"cheap_ranges": [], "analysis_info": {}}

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
