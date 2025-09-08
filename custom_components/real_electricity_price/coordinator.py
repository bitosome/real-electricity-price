"""DataUpdateCoordinator for real_electricity_price."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import RealElectricityPriceApiClientError
from .const import (
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_TIME,
    NIGHT_PRICE_END_TIME_DEFAULT,
    NIGHT_PRICE_START_TIME_DEFAULT,
    parse_time_string,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class RealElectricityPriceDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and unified refresh ticks."""

    config_entry: RealElectricityPriceConfigEntry

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the coordinator."""
        super().__init__(*args, **kwargs)
        self._last_update_date = None
        self._hourly_update_unsub: Callable[[], None] | None = None
        self._midnight_update_unsub: Callable[[], None] | None = None
        self._stop_unsub: Callable[[], None] | None = None
        self._cheap_price_coordinator = None  # Will be set after initialization
        self._is_startup = True  # Track if this is initial startup

        # Centralized hourly tick at hh:00 for all sensors (no network call)
        self._hourly_update_unsub = async_track_time_change(
            self.hass,
            self._handle_hourly_tick,
            minute=0,
            second=0,
        )

        # Midnight transition handler for date changes, DST, etc.
        self._midnight_update_unsub = async_track_time_change(
            self.hass,
            self._handle_midnight_transition,
            hour=0,
            minute=0,
            second=0,
        )

        # Clean up the time trackers on HA stop
        @callback
        def _on_stop(event) -> None:
            if self._hourly_update_unsub:
                self._hourly_update_unsub()
                self._hourly_update_unsub = None
            if self._midnight_update_unsub:
                self._midnight_update_unsub()
                self._midnight_update_unsub = None

        self._stop_unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, _on_stop
        )

    @callback
    def _handle_hourly_tick(self, now: datetime.datetime) -> None:
        """Notify listeners to re-render at top of the hour."""
        _LOGGER.debug("Hourly tick at %s -> updating all entity states (no fetch)", now)
        # This does not fetch data; it only tells all entities to update their state
        self.async_update_listeners()

    @callback
    def _handle_midnight_transition(self, now: datetime.datetime) -> None:
        """Handle midnight transition for date changes, DST, etc."""
        _LOGGER.debug(
            "Midnight transition at %s -> scheduling data refresh for date changes", now
        )
        # Schedule a refresh to handle:
        # - Today's data becomes yesterday's data
        # - Tomorrow's data becomes today's data
        # - DST transitions
        # - New year transitions
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            current_date = dt_util.now().date()
            datetime.datetime.now(datetime.UTC)

            # Check if we need to force update due to date change
            force_update = self._last_update_date != current_date
            if force_update:
                _LOGGER.info(
                    "Date changed from %s to %s, forcing data update",
                    self._last_update_date,
                    current_date,
                )

            data = await self.config_entry.runtime_data.client.async_get_data()

            # Handle case where API returns None (failed to fetch today's data)
            if data is None:
                # If we have existing data, preserve it to avoid data gaps (but check if it's not too stale)
                if self.data is not None:
                    last_sync = self.data.get("last_sync")
                    if last_sync:
                        # Only preserve data if it's less than 6 hours old
                        time_since_sync = datetime.datetime.now(datetime.UTC) - last_sync
                        if time_since_sync.total_seconds() < 6 * 3600:  # 6 hours
                            _LOGGER.warning(
                                "API returned no data but preserving recent data from %s to avoid sensor unavailability",
                                last_sync
                            )
                            # Don't trigger cheap hours update when preserving old data
                            return self.data
                        _LOGGER.error("Last data is too stale (%s), not preserving", last_sync)
                    else:
                        _LOGGER.error("No timestamp in existing data, not preserving")
                else:
                    _LOGGER.error("No current data available and no previous data to preserve")
                return None

            # Add the current timestamp and configuration to the data
            if data is not None:
                data["last_sync"] = datetime.datetime.now(datetime.UTC)

                # Include relevant configuration for tariff calculation
                config_data = dict(self.config_entry.data)
                config_data.update(self.config_entry.options)  # Options override data

                # Extract night hours from TimeSelector format
                start_time = config_data.get(CONF_NIGHT_PRICE_START_TIME)
                end_time = config_data.get(CONF_NIGHT_PRICE_END_TIME)
                
                # Extract hours with defaults
                if isinstance(start_time, dict) and "hour" in start_time:
                    start_hour = int(start_time["hour"])
                else:
                    start_hour = parse_time_string(NIGHT_PRICE_START_TIME_DEFAULT)[0]
                    
                if isinstance(end_time, dict) and "hour" in end_time:
                    end_hour = int(end_time["hour"])
                else:
                    end_hour = parse_time_string(NIGHT_PRICE_END_TIME_DEFAULT)[0]

                data["config"] = {
                    "night_price_start_hour": start_hour,
                    "night_price_end_hour": end_hour,
                }

                # Validate data dates and log any issues
                self._validate_data_dates(data, current_date)

            self._last_update_date = current_date

            # Scenario #1: Integration startup with tomorrow's data available
            if self._is_startup and self._cheap_price_coordinator:
                tomorrow_data = data.get("tomorrow")
                if tomorrow_data and isinstance(tomorrow_data, dict):
                    hourly_prices = tomorrow_data.get("hourly_prices", [])
                    # Check if tomorrow's prices are actually available (not just placeholder)
                    has_real_prices = any(
                        entry.get("actual_price") is not None
                        for entry in hourly_prices
                    )
                    if has_real_prices:
                        _LOGGER.info("Integration startup: tomorrow's prices available, triggering cheap hours calculation")
                        await self._cheap_price_coordinator.async_manual_update()
                    else:
                        _LOGGER.debug("Integration startup: tomorrow's prices not yet available")
                else:
                    _LOGGER.debug("Integration startup: no tomorrow data available")

                self._is_startup = False  # Only trigger once at startup

            return data

        except RealElectricityPriceApiClientError as exception:
            # If we have existing data, preserve it during API failures to avoid data gaps
            if self.data is not None:
                last_sync = self.data.get("last_sync")
                if last_sync:
                    time_since_sync = datetime.datetime.now(datetime.UTC) - last_sync
                    if time_since_sync.total_seconds() < 6 * 3600:  # 6 hours
                        _LOGGER.warning(
                            "API failed but preserving recent data from %s to avoid sensor unavailability",
                            last_sync
                        )
                        # Don't trigger cheap hours update when preserving old data
                        return self.data
            raise UpdateFailed(exception) from exception

    def _validate_data_dates(self, data: dict, current_date: datetime.date) -> None:
        """Validate that the data contains the expected dates."""
        yesterday_data = data.get("yesterday")
        today_data = data.get("today")
        tomorrow_data = data.get("tomorrow")

        expected_yesterday = current_date - datetime.timedelta(days=1)
        expected_tomorrow = current_date + datetime.timedelta(days=1)

        if yesterday_data and "date" in yesterday_data:
            try:
                yesterday_date = datetime.datetime.fromisoformat(
                    yesterday_data["date"]
                ).date()
                if yesterday_date != expected_yesterday:
                    _LOGGER.warning(
                        "Yesterday data date mismatch: expected %s, got %s",
                        expected_yesterday,
                        yesterday_date,
                    )
            except (ValueError, TypeError):
                _LOGGER.exception(
                    "Invalid date format in yesterday data: %s",
                    yesterday_data.get("date"),
                )

        if today_data and "date" in today_data:
            try:
                today_date = datetime.datetime.fromisoformat(today_data["date"]).date()
                if today_date != current_date:
                    _LOGGER.warning(
                        "Today data date mismatch: expected %s, got %s",
                        current_date,
                        today_date,
                    )
            except (ValueError, TypeError):
                _LOGGER.exception(
                    "Invalid date format in today data: %s", today_data.get("date")
                )

        if tomorrow_data and "date" in tomorrow_data:
            try:
                tomorrow_date = datetime.datetime.fromisoformat(
                    tomorrow_data["date"]
                ).date()
                if tomorrow_date != expected_tomorrow:
                    _LOGGER.warning(
                        "Tomorrow data date mismatch: expected %s, got %s",
                        expected_tomorrow,
                        tomorrow_date,
                    )
            except (ValueError, TypeError):
                _LOGGER.exception(
                    "Invalid date format in tomorrow data: %s",
                    tomorrow_data.get("date"),
                )

    def set_cheap_price_coordinator(self, coordinator) -> None:
        """Set the cheap price coordinator for automatic updates."""
        self._cheap_price_coordinator = coordinator

    async def async_request_refresh(self) -> None:
        """Request a refresh for all entities and trigger hourly update."""
        _LOGGER.debug("Requested refresh for all entities")
        await super().async_request_refresh()
