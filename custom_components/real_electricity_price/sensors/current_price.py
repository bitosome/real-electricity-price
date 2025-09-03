"""Current price sensor for Real Electricity Price integration."""

from __future__ import annotations

import logging
import yaml
from datetime import UTC, datetime
from typing import Any

from homeassistant.util import dt as dt_util

from ..const import (
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_TIME,
    NIGHT_PRICE_END_TIME_DEFAULT,
    NIGHT_PRICE_START_TIME_DEFAULT,
    parse_time_string,
)
from ..models import IntegrationConfig
from .base import RealElectricityPriceBaseSensor

_LOGGER = logging.getLogger(__name__)


class CurrentPriceSensor(RealElectricityPriceBaseSensor):
    """Sensor for current electricity price."""

    @property
    def native_value(self) -> float | None:
        """Return the current electricity price."""
        if not self.coordinator.data:
            return None

        return self._get_current_price_value()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        config = self.get_config()
        
        # Get current price components
        components = self._get_price_components(config)
        
        return {
            "price_components": yaml.dump(components, default_flow_style=False, allow_unicode=True),
        }

    def _get_price_components(self, config: IntegrationConfig) -> dict[str, float]:
        """Get all price components used in calculation."""
        grid_name = config.grid
        supplier_name = config.supplier
        
        # Get current Nord Pool price
        nord_pool_price = self._get_current_nord_pool_price()
        
        # Get current tariff to determine transmission price
        current_tariff = self._get_current_tariff()
        transmission_price = (
            config.grid_transmission_price_night 
            if current_tariff == "night" 
            else config.grid_transmission_price_day
        )
        
        return {
            "nord_pool_price": self._round_price(nord_pool_price) if nord_pool_price is not None else None,
            f"{grid_name.lower()}_electricity_excise_duty": self._round_price(config.grid_electricity_excise_duty),
            f"{grid_name.lower()}_renewable_energy_charge": self._round_price(config.grid_renewable_energy_charge),
            f"{grid_name.lower()}_transmission_price_{current_tariff}": self._round_price(transmission_price),
            f"{supplier_name.lower()}_renewable_energy_charge": self._round_price(config.supplier_renewable_energy_charge),
            f"{supplier_name.lower()}_margin": self._round_price(config.supplier_margin),
        }

    def _get_current_nord_pool_price(self) -> float | None:
        """Get current Nord Pool price from hourly data."""
        if not self.coordinator.data:
            return None

        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)

        for data_key in ["yesterday", "today", "tomorrow"]:
            day_data = self.coordinator.data.get(data_key)
            if not isinstance(day_data, dict):
                continue

            hourly_prices = day_data.get("hourly_prices", [])
            for price_entry in hourly_prices:
                try:
                    start_time = datetime.fromisoformat(price_entry["start_time"])
                    end_time = datetime.fromisoformat(price_entry["end_time"])

                    if start_time <= now < end_time:
                        return price_entry.get("nord_pool_price")
                except (ValueError, KeyError):
                    continue

        return None

    def _get_current_tariff(self) -> str:
        """Get current tariff (day/night) for transmission price selection."""
        config = self.get_config()

        # Get time configuration
        config_data = {
            **self.coordinator.config_entry.data,
            **self.coordinator.config_entry.options,
        }
        start_time_str = config_data.get(
            CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT
        )
        end_time_str = config_data.get(
            CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT
        )

        try:
            night_start, _, _ = parse_time_string(start_time_str)
            night_end, _, _ = parse_time_string(end_time_str)
        except ValueError:
            night_start, night_end = 22, 7

        # Get current local time in the configured country
        tz_name = self._get_timezone_for_country(config.country_code)
        try:
            import zoneinfo

            local_tz = zoneinfo.ZoneInfo(tz_name)
            local_time = datetime.now(local_tz)
            local_hour = local_time.hour
        except Exception:
            local_hour = dt_util.now().hour

        # Determine if it's night time
        if night_start > night_end:  # Crosses midnight (e.g., 22:00 to 07:00)
            is_night_time = local_hour >= night_start or local_hour < night_end
        else:  # Does not cross midnight (unusual case)
            is_night_time = night_start <= local_hour < night_end

        return "night" if is_night_time else "day"

    def _get_timezone_for_country(self, country_code: str) -> str:
        """Get timezone for country code."""
        country_timezones = {
            "EE": "Europe/Tallinn",  # Estonia
            "FI": "Europe/Helsinki",  # Finland
            "LV": "Europe/Riga",  # Latvia
            "LT": "Europe/Vilnius",  # Lithuania
            "SE": "Europe/Stockholm",  # Sweden (all SE regions)
            "NO": "Europe/Oslo",  # Norway (all NO regions)
            "DK": "Europe/Copenhagen",  # Denmark (all DK regions)
        }

        # Extract base country code (e.g., SE1 -> SE)
        base_country = country_code[:2] if len(country_code) > 2 else country_code
        return country_timezones.get(base_country, "Europe/Tallinn")

    def _get_current_price_value(self) -> float | None:
        """Get current price from all available hourly prices data."""
        if not self.coordinator.data:
            return None

        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)

        for data_key in ["yesterday", "today", "tomorrow"]:
            day_data = self.coordinator.data.get(data_key)
            if not isinstance(day_data, dict):
                continue

            hourly_prices = day_data.get("hourly_prices", [])
            for price_entry in hourly_prices:
                try:
                    start_time = datetime.fromisoformat(price_entry["start_time"])
                    end_time = datetime.fromisoformat(price_entry["end_time"])

                    if start_time <= now < end_time:
                        price_value = price_entry["actual_price"]
                        if price_value is None:
                            _LOGGER.debug(
                                "Skipping unavailable price entry for time %s in %s data",
                                now,
                                data_key,
                            )
                            continue
                        _LOGGER.debug(
                            "Found current price: %s for time %s in %s data",
                            price_value,
                            now,
                            data_key,
                        )
                        return self._round_price(price_value)
                except (ValueError, KeyError) as e:
                    _LOGGER.warning("Invalid price entry in %s: %s", data_key, e)
                    continue

        _LOGGER.debug("No current price found for time %s in any available data", now)
        return None


class CurrentTariffSensor(RealElectricityPriceBaseSensor):
    """Sensor for current tariff (day/night)."""

    @property
    def native_value(self) -> str:
        """Return the current tariff."""
        return self._get_current_tariff_value()

    @property
    def icon(self) -> str:
        """Return icon based on current tariff."""
        current_tariff = self._get_current_tariff_value()
        if current_tariff == "night":
            return "mdi:weather-night"
        return "mdi:weather-sunny"

    def _get_current_tariff_value(self) -> str:
        """Determine the current tariff based on local time."""
        config = self.get_config()

        # Get time configuration
        config_data = {
            **self.coordinator.config_entry.data,
            **self.coordinator.config_entry.options,
        }
        start_time_str = config_data.get(
            CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT
        )
        end_time_str = config_data.get(
            CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT
        )

        try:
            night_start, _, _ = parse_time_string(start_time_str)
            night_end, _, _ = parse_time_string(end_time_str)
        except ValueError:
            _LOGGER.warning("Invalid time format in configuration, using defaults")
            night_start, night_end = 22, 7

        # Get current local time in the configured country
        tz_name = self._get_timezone_for_country(config.country_code)
        try:
            import zoneinfo

            local_tz = zoneinfo.ZoneInfo(tz_name)
            local_time = datetime.now(local_tz)
            local_hour = local_time.hour
        except Exception as e:
            _LOGGER.warning("Could not determine local time for %s: %s", tz_name, e)
            local_hour = dt_util.now().hour

        _LOGGER.debug(
            "Tariff calculation: night_start=%s, night_end=%s, tz=%s, local_hour=%s",
            night_start,
            night_end,
            tz_name,
            local_hour,
        )

        # Determine if it's night time
        if night_start > night_end:  # Crosses midnight (e.g., 22:00 to 07:00)
            is_night_time = local_hour >= night_start or local_hour < night_end
        else:  # Does not cross midnight (unusual case)
            is_night_time = night_start <= local_hour < night_end

        return "night" if is_night_time else "day"

    def _get_timezone_for_country(self, country_code: str) -> str:
        """Get timezone for country code."""
        country_timezones = {
            "EE": "Europe/Tallinn",  # Estonia
            "FI": "Europe/Helsinki",  # Finland
            "LV": "Europe/Riga",  # Latvia
            "LT": "Europe/Vilnius",  # Lithuania
            "SE": "Europe/Stockholm",  # Sweden (all SE regions)
            "NO": "Europe/Oslo",  # Norway (all NO regions)
            "DK": "Europe/Copenhagen",  # Denmark (all DK regions)
        }

        # Extract base country code (e.g., SE1 -> SE)
        base_country = country_code[:2] if len(country_code) > 2 else country_code
        return country_timezones.get(base_country, "Europe/Tallinn")
