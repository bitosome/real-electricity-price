"""DataUpdateCoordinator for real_electricity_price."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Callable

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .api import RealElectricityPriceApiClientError

if TYPE_CHECKING:
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class RealElectricityPriceDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and unified refresh ticks."""

    config_entry: RealElectricityPriceConfigEntry

    def __init__(self, *args, **kwargs):
        """Initialize the coordinator."""
        super().__init__(*args, **kwargs)
        self._last_update_date = None
        self._midnight_check_scheduled = False
        self._hourly_update_unsub: Callable[[], None] | None = None
        self._stop_unsub: Callable[[], None] | None = None

        # Centralized hourly tick at hh:00 for all sensors (no network call)
        self._hourly_update_unsub = async_track_time_change(
            self.hass,
            self._handle_hourly_tick,
            minute=0,
            second=0,
        )

        # Clean up the hourly tick on HA stop
        @callback
        def _on_stop(event) -> None:
            if self._hourly_update_unsub:
                self._hourly_update_unsub()
                self._hourly_update_unsub = None

        self._stop_unsub = self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _on_stop)

    @callback
    def _handle_hourly_tick(self, now: datetime.datetime) -> None:
        """Notify listeners to re-render at top of the hour."""
        _LOGGER.debug("Hourly tick at %s -> updating all entity states (no fetch)", now)
        # This does not fetch data; it only tells all entities to update their state
        self.async_update_listeners()

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            current_date = datetime.datetime.now(datetime.UTC).date()
            current_time = datetime.datetime.now(datetime.UTC)
            
            # Check if we need to force update due to date change
            force_update = self._last_update_date != current_date
            if force_update:
                _LOGGER.info("Date changed from %s to %s, forcing data update", 
                           self._last_update_date, current_date)
                
            # Schedule additional update shortly after midnight if we're close
            self._schedule_midnight_update_if_needed(current_time)
                
            data = await self.config_entry.runtime_data.client.async_get_data()
            
            # Add the current timestamp and configuration to the data
            if data is not None:
                data["last_sync"] = datetime.datetime.now(datetime.UTC)
                
                # Include relevant configuration for tariff calculation
                config_data = dict(self.config_entry.data)
                config_data.update(self.config_entry.options)  # Options override data
                data["config"] = {
                    "night_price_start_hour": config_data.get("night_price_start_hour", 22),
                    "night_price_end_hour": config_data.get("night_price_end_hour", 7),
                }
                
                # Validate data dates and log any issues
                self._validate_data_dates(data, current_date)
                
            self._last_update_date = current_date
            return data
            
        except RealElectricityPriceApiClientError as exception:
            raise UpdateFailed(exception) from exception

    def _schedule_midnight_update_if_needed(self, current_time: datetime.datetime) -> None:
        """Schedule an update shortly after midnight to ensure fresh data."""
        # Check if we're within 2 hours of midnight (22:00-02:00) and haven't scheduled yet
        hour = current_time.hour
        if (hour >= 22 or hour <= 2) and not self._midnight_check_scheduled:
            _LOGGER.debug("Near midnight (hour %d), will check for fresh data more frequently", hour)
            self._midnight_check_scheduled = True
            
            # Schedule a refresh in 15 minutes to catch midnight transition
            def schedule_refresh():
                if self.hass and not self.hass.is_stopping:
                    self.hass.async_create_task(self.async_request_refresh())
                    
            self.hass.loop.call_later(900, schedule_refresh)  # 15 minutes
            
        elif hour > 2 and hour < 22:
            # Reset the flag during normal hours
            self._midnight_check_scheduled = False

    def _validate_data_dates(self, data: dict, current_date: datetime.date) -> None:
        """Validate that the data contains the expected dates."""
        yesterday_data = data.get("yesterday")
        today_data = data.get("today")
        tomorrow_data = data.get("tomorrow")
        
        expected_yesterday = current_date - datetime.timedelta(days=1)
        expected_tomorrow = current_date + datetime.timedelta(days=1)
        
        if yesterday_data and "date" in yesterday_data:
            try:
                yesterday_date = datetime.datetime.fromisoformat(yesterday_data["date"]).date()
                if yesterday_date != expected_yesterday:
                    _LOGGER.warning(
                        "Yesterday data date mismatch: expected %s, got %s", 
                        expected_yesterday, yesterday_date
                    )
            except (ValueError, TypeError):
                _LOGGER.error("Invalid date format in yesterday data: %s", yesterday_data.get("date"))
        
        if today_data and "date" in today_data:
            try:
                today_date = datetime.datetime.fromisoformat(today_data["date"]).date()
                if today_date != current_date:
                    _LOGGER.warning(
                        "Today data date mismatch: expected %s, got %s", 
                        current_date, today_date
                    )
            except (ValueError, TypeError):
                _LOGGER.error("Invalid date format in today data: %s", today_data.get("date"))
                
        if tomorrow_data and "date" in tomorrow_data:
            try:
                tomorrow_date = datetime.datetime.fromisoformat(tomorrow_data["date"]).date()
                if tomorrow_date != expected_tomorrow:
                    _LOGGER.warning(
                        "Tomorrow data date mismatch: expected %s, got %s", 
                        expected_tomorrow, tomorrow_date
                    )
            except (ValueError, TypeError):
                _LOGGER.error("Invalid date format in tomorrow data: %s", tomorrow_data.get("date"))

    async def async_request_refresh(self) -> None:
        """Request a refresh of the data."""
        _LOGGER.debug("Manual refresh requested")
        await super().async_request_refresh()
