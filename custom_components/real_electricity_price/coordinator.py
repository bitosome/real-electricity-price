"""DataUpdateCoordinator for real_electricity_price."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RealElectricityPriceApiClientError
from .const import (
    CONF_NIGHT_PRICE_START_TIME,
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_HOUR,
    CONF_NIGHT_PRICE_END_HOUR,
    NIGHT_PRICE_START_TIME_DEFAULT,
    NIGHT_PRICE_END_TIME_DEFAULT,
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
        _LOGGER.debug("Midnight transition at %s -> scheduling data refresh for date changes", now)
        # Schedule a refresh to handle:
        # - Today's data becomes yesterday's data
        # - Tomorrow's data becomes today's data
        # - DST transitions
        # - New year transitions
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            current_date = datetime.datetime.now(datetime.UTC).date()
            current_time = datetime.datetime.now(datetime.UTC)

            # Check if we need to force update due to date change
            force_update = self._last_update_date != current_date
            if force_update:
                _LOGGER.info(
                    "Date changed from %s to %s, forcing data update",
                    self._last_update_date,
                    current_date,
                )


            data = await self.config_entry.runtime_data.client.async_get_data()

            # Add the current timestamp and configuration to the data
            if data is not None:
                data["last_sync"] = datetime.datetime.now(datetime.UTC)

                # Include relevant configuration for tariff calculation
                config_data = dict(self.config_entry.data)
                config_data.update(self.config_entry.options)  # Options override data
                # Resolve night hours preferring time string config, fallback to legacy hour fields, then defaults
                def _resolve_hour(cfg: dict, key_time: str, key_hour: str, default_time: str) -> int:
                    val = cfg.get(key_time)
                    if isinstance(val, dict):
                        return int(val.get("hour", parse_time_string(default_time)[0]))
                    if isinstance(val, str):
                        try:
                            h, _, _ = parse_time_string(val)
                            return int(h)
                        except Exception:
                            pass
                    if key_hour in cfg:
                        try:
                            return int(cfg.get(key_hour))
                        except Exception:
                            pass
                    return parse_time_string(default_time)[0]

                start_hour = _resolve_hour(
                    config_data,
                    CONF_NIGHT_PRICE_START_TIME,
                    CONF_NIGHT_PRICE_START_HOUR,
                    NIGHT_PRICE_START_TIME_DEFAULT,
                )
                end_hour = _resolve_hour(
                    config_data,
                    CONF_NIGHT_PRICE_END_TIME,
                    CONF_NIGHT_PRICE_END_HOUR,
                    NIGHT_PRICE_END_TIME_DEFAULT,
                )

                data["config"] = {
                    "night_price_start_hour": start_hour,
                    "night_price_end_hour": end_hour,
                }

                # Validate data dates and log any issues
                self._validate_data_dates(data, current_date)

            self._last_update_date = current_date
            
            # Trigger cheap price coordinator update after successful data sync
            if self._cheap_price_coordinator:
                _LOGGER.debug("Triggering cheap price coordinator update after data sync")
                await self._cheap_price_coordinator.async_manual_update()
            
            return data

        except RealElectricityPriceApiClientError as exception:
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
