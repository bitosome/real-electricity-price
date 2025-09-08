"""Current price sensor for Real Electricity Price integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import holidays
from homeassistant.util import dt as dt_util

from ..const import (
    CONF_HAS_NIGHT_TARIFF,
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_TIME,
    CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
    CONF_NIGHT_TARIFF_SATURDAY,
    CONF_NIGHT_TARIFF_SUNDAY,
    HAS_NIGHT_TARIFF_DEFAULT,
    NIGHT_PRICE_END_TIME_DEFAULT,
    NIGHT_PRICE_START_TIME_DEFAULT,
    NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT,
    NIGHT_TARIFF_SATURDAY_DEFAULT,
    NIGHT_TARIFF_SUNDAY_DEFAULT,
    TARIFF_FIXED,
    TARIFF_OFF_PEAK,
    TARIFF_PEAK,
    parse_time_string,
)

from .base import RealElectricityPriceBaseSensor

if TYPE_CHECKING:
    from ..models import IntegrationConfig

_LOGGER = logging.getLogger(__name__)

# Parse default time strings once at module level
try:
    _DEFAULT_NIGHT_START_HOUR, _, _ = parse_time_string(NIGHT_PRICE_START_TIME_DEFAULT)
    _DEFAULT_NIGHT_END_HOUR, _, _ = parse_time_string(NIGHT_PRICE_END_TIME_DEFAULT)
except Exception:
    # Should never happen with hardcoded values, but just in case
    _DEFAULT_NIGHT_START_HOUR = 22
    _DEFAULT_NIGHT_END_HOUR = 7


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

        # Get current price components and VAT-applied values
        base_components = self._get_price_components(config)
        calc = self._get_calculation_details(config)

        # Move VAT-related information under price_components as requested
        price_components: dict[str, Any] = {
            "base": base_components,
        }
        if isinstance(calc, dict):
            # Include components with VAT and VAT settings directly under price_components
            if "components_with_vat" in calc:
                price_components["with_vat"] = calc.get("components_with_vat")
            if "vat_settings" in calc:
                price_components["vat_settings"] = calc.get("vat_settings")

        # Keep calculation summary without verbose formula and without method label
        calculation_details = {
            k: v
            for k, v in calc.items()
            if k in ("price_calculation",)
        }

        return {
            "price_components": price_components,
            "calculation_details": calculation_details,
        }

    def _get_price_components(self, config: IntegrationConfig) -> dict[str, float]:
        """Get all price components used in calculation."""
        grid_name = config.grid
        supplier_name = config.supplier

        # Get current Nord Pool price
        nord_pool_price = self._get_current_nord_pool_price()

        # Get current tariff to determine transmission price
        current_tariff = self._get_current_tariff()
        if current_tariff == TARIFF_FIXED:
            # Use day price as default for fixed tariff
            transmission_price = config.grid_transmission_price_day
        else:
            transmission_price = (
                config.grid_transmission_price_night
                if current_tariff == TARIFF_OFF_PEAK
                else config.grid_transmission_price_day
            )

        return {
            "nord_pool_price": self._round_price(nord_pool_price)
            if nord_pool_price is not None
            else None,
            f"{grid_name.lower()}_electricity_excise_duty": self._round_price(
                config.grid_electricity_excise_duty
            ),
            f"{grid_name.lower()}_renewable_energy_charge": self._round_price(
                config.grid_renewable_energy_charge
            ),
            f"{grid_name.lower()}_transmission_price_{current_tariff}": self._round_price(
                transmission_price
            ),
            f"{supplier_name.lower()}_renewable_energy_charge": self._round_price(
                config.supplier_renewable_energy_charge
            ),
            f"{supplier_name.lower()}_margin": self._round_price(
                config.supplier_margin
            ),
        }

    def _get_calculation_details(self, config: IntegrationConfig) -> dict[str, Any]:
        """Get detailed calculation information including VAT applications and final sum."""
        grid_name = config.grid
        supplier_name = config.supplier

        # Get current Nord Pool price
        nord_pool_price = self._get_current_nord_pool_price()
        if nord_pool_price is None:
            return {"error": "Nord Pool price not available"}

        # Get current tariff
        current_tariff = self._get_current_tariff()
        if current_tariff == TARIFF_FIXED:
            # Use day price as default for fixed tariff
            transmission_price = config.grid_transmission_price_day
        else:
            transmission_price = (
                config.grid_transmission_price_night
                if current_tariff == TARIFF_OFF_PEAK
                else config.grid_transmission_price_day
            )

        # Get VAT configuration
        vat_percentage = config.vat_rate
        vat_nord_pool = config.vat_nord_pool
        vat_grid_excise_duty = config.vat_grid_electricity_excise_duty
        vat_grid_renewable = config.vat_grid_renewable_energy_charge
        vat_transmission_night = config.vat_grid_transmission_night
        vat_transmission_day = config.vat_grid_transmission_day
        vat_supplier_renewable = config.vat_supplier_renewable_energy_charge
        vat_supplier_margin = config.vat_supplier_margin

        # Choose correct transmission VAT based on tariff
        if current_tariff == TARIFF_FIXED:
            # Use day VAT as default for fixed tariff
            vat_transmission = vat_transmission_day
        else:
            vat_transmission = (
                vat_transmission_night
                if current_tariff == TARIFF_OFF_PEAK
                else vat_transmission_day
            )

        # Calculate components with VAT applications
        base_price_component = nord_pool_price
        if vat_nord_pool:
            base_price_component *= 1 + vat_percentage / 100

        excise_component = config.grid_electricity_excise_duty
        if vat_grid_excise_duty:
            excise_component *= 1 + vat_percentage / 100

        renewable_grid_component = config.grid_renewable_energy_charge
        if vat_grid_renewable:
            renewable_grid_component *= 1 + vat_percentage / 100

        renewable_supplier_component = config.supplier_renewable_energy_charge
        if vat_supplier_renewable:
            renewable_supplier_component *= 1 + vat_percentage / 100

        margin_component = config.supplier_margin
        if vat_supplier_margin:
            margin_component *= 1 + vat_percentage / 100

        transmission_component = transmission_price
        if vat_transmission:
            transmission_component *= 1 + vat_percentage / 100

        # Calculate final price
        final_price = (
            base_price_component
            + excise_component
            + renewable_grid_component
            + renewable_supplier_component
            + margin_component
            + transmission_component
        )

        return {
            "vat_settings": {
                "vat_rate": self._round_price(vat_percentage),
                "vat_nord_pool": vat_nord_pool,
                f"vat_{grid_name.lower()}_excise_duty": vat_grid_excise_duty,
                f"vat_{grid_name.lower()}_renewable": vat_grid_renewable,
                f"vat_{grid_name.lower()}_transmission_{current_tariff}": vat_transmission,
                f"vat_{supplier_name.lower()}_renewable": vat_supplier_renewable,
                f"vat_{supplier_name.lower()}_margin": vat_supplier_margin,
            },
            "components_with_vat": {
                "nord_pool_price": self._round_price(base_price_component),
                f"{grid_name.lower()}_electricity_excise_duty": self._round_price(
                    excise_component
                ),
                f"{grid_name.lower()}_renewable_energy_charge": self._round_price(
                    renewable_grid_component
                ),
                f"{grid_name.lower()}_transmission_price_{current_tariff}": self._round_price(
                    transmission_component
                ),
                f"{supplier_name.lower()}_renewable_energy_charge": self._round_price(
                    renewable_supplier_component
                ),
                f"{supplier_name.lower()}_margin": self._round_price(margin_component),
            },
            "price_calculation": {
                "final_price": self._round_price(final_price),
                "current_tariff": current_tariff,
            },
        }

    def _get_current_nord_pool_price(self) -> float | None:
        """Get current Nord Pool price from hourly data."""
        if not self.coordinator.data:
            return None

        # Use Home Assistant's datetime utility for consistent timezone handling
        now = dt_util.now().replace(minute=0, second=0, microsecond=0)

        for data_key in ["yesterday", "today", "tomorrow"]:
            day_data = self.coordinator.data.get(data_key)
            if not isinstance(day_data, dict):
                continue

            hourly_prices = day_data.get("hourly_prices", [])
            for price_entry in hourly_prices:
                try:
                    # Native datetime objects from attributes (no string parsing needed)
                    start_time_str = price_entry["start_time"]
                    end_time_str = price_entry["end_time"]

                    # Parse ISO format datetime strings consistently
                    start_time = dt_util.parse_datetime(start_time_str)
                    end_time = dt_util.parse_datetime(end_time_str)

                    if start_time and end_time and start_time <= now < end_time:
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

        # Check if night tariff is enabled
        has_night_tariff = config_data.get(CONF_HAS_NIGHT_TARIFF, HAS_NIGHT_TARIFF_DEFAULT)
        if not has_night_tariff:
            return TARIFF_FIXED

        start_val = config_data.get(
            CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT
        )
        end_val = config_data.get(
            CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT
        )

        # Extract hours from TimeSelector format
        if isinstance(start_val, dict) and "hour" in start_val:
            night_start = int(start_val["hour"])
        else:
            night_start = _DEFAULT_NIGHT_START_HOUR
            
        if isinstance(end_val, dict) and "hour" in end_val:
            night_end = int(end_val["hour"])
        else:
            night_end = _DEFAULT_NIGHT_END_HOUR

        # Get current local time in the configured country
        tz_name = self._get_timezone_for_country(config.country_code)
        # Use Home Assistant's timezone utilities for consistent handling
        try:
            local_tz = dt_util.get_time_zone(tz_name)
            local_time = dt_util.now(local_tz)
            local_hour = local_time.hour
        except Exception:
            local_time = dt_util.now()
            local_hour = local_time.hour

        # Weekend/holiday detection: configurable night tariff for whole day
        base_country = (
            config.country_code[:2]
            if len(config.country_code) > 2
            else config.country_code
        )
        try:
            country_holidays = holidays.country_holidays(
                base_country, years=local_time.year
            )
        except Exception:
            country_holidays = {}
        # Read rules from config (merge data+options)
        config_data = {
            **self.coordinator.config_entry.data,
            **self.coordinator.config_entry.options,
        }
        use_sat = config_data.get(
            CONF_NIGHT_TARIFF_SATURDAY, NIGHT_TARIFF_SATURDAY_DEFAULT
        )
        use_sun = config_data.get(
            CONF_NIGHT_TARIFF_SUNDAY, NIGHT_TARIFF_SUNDAY_DEFAULT
        )
        use_holiday = config_data.get(
            CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY, NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT
        )
        dow = local_time.weekday()
        is_sat = dow == 5
        is_sun = dow == 6
        is_holiday = local_time.date() in country_holidays
        if (is_sat and use_sat) or (is_sun and use_sun) or (is_holiday and use_holiday):
            return TARIFF_OFF_PEAK

        # Determine if it's night time
        if night_start > night_end:  # Crosses midnight (e.g., 22:00 to 07:00)
            is_night_time = local_hour >= night_start or local_hour < night_end
        else:  # Does not cross midnight (unusual case)
            is_night_time = night_start <= local_hour < night_end

        return TARIFF_OFF_PEAK if is_night_time else TARIFF_PEAK

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

        # Use Home Assistant's datetime utility for consistent timezone handling
        now = dt_util.now().replace(minute=0, second=0, microsecond=0)

        for data_key in ["yesterday", "today", "tomorrow"]:
            day_data = self.coordinator.data.get(data_key)
            if not isinstance(day_data, dict):
                continue

            hourly_prices = day_data.get("hourly_prices", [])
            for price_entry in hourly_prices:
                try:
                    # Parse ISO format datetime strings consistently
                    start_time_str = price_entry["start_time"]
                    end_time_str = price_entry["end_time"]

                    start_time = dt_util.parse_datetime(start_time_str)
                    end_time = dt_util.parse_datetime(end_time_str)

                    if start_time and end_time and start_time <= now < end_time:
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
        if current_tariff == TARIFF_OFF_PEAK:
            return "mdi:weather-night"
        if current_tariff == TARIFF_FIXED:
            return "mdi:calendar-clock"
        return "mdi:weather-sunny"

    def _get_current_tariff_value(self) -> str:
        """Determine the current tariff based on local time."""
        config = self.get_config()

        # Get time configuration
        config_data = {
            **self.coordinator.config_entry.data,
            **self.coordinator.config_entry.options,
        }

        # Check if night tariff is enabled
        has_night_tariff = config_data.get(CONF_HAS_NIGHT_TARIFF, HAS_NIGHT_TARIFF_DEFAULT)
        if not has_night_tariff:
            return TARIFF_FIXED

        start_val = config_data.get(
            CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT
        )
        end_val = config_data.get(
            CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT
        )

        # Extract hours from TimeSelector format
        if isinstance(start_val, dict) and "hour" in start_val:
            night_start = int(start_val["hour"])
        else:
            night_start = _DEFAULT_NIGHT_START_HOUR
            
        if isinstance(end_val, dict) and "hour" in end_val:
            night_end = int(end_val["hour"])
        else:
            night_end = _DEFAULT_NIGHT_END_HOUR

        # Get current local time in the configured country
        tz_name = self._get_timezone_for_country(config.country_code)
        # Use Home Assistant's timezone utilities for consistent handling
        try:
            local_tz = dt_util.get_time_zone(tz_name)
            local_time = dt_util.now(local_tz)
            local_hour = local_time.hour
        except Exception as e:
            _LOGGER.warning("Could not determine local time for %s: %s", tz_name, e)
            local_time = dt_util.now()
            local_hour = local_time.hour

        # Weekend/holiday detection: configurable night tariff for whole day
        base_country = (
            config.country_code[:2]
            if len(config.country_code) > 2
            else config.country_code
        )
        try:
            country_holidays = holidays.country_holidays(
                base_country, years=local_time.year
            )
        except Exception:
            country_holidays = {}
        config_data = {
            **self.coordinator.config_entry.data,
            **self.coordinator.config_entry.options,
        }
        use_sat = config_data.get(
            CONF_NIGHT_TARIFF_SATURDAY, NIGHT_TARIFF_SATURDAY_DEFAULT
        )
        use_sun = config_data.get(
            CONF_NIGHT_TARIFF_SUNDAY, NIGHT_TARIFF_SUNDAY_DEFAULT
        )
        use_holiday = config_data.get(
            CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY, NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT
        )
        dow = local_time.weekday()
        is_sat = dow == 5
        is_sun = dow == 6
        is_holiday = local_time.date() in country_holidays
        if (is_sat and use_sat) or (is_sun and use_sun) or (is_holiday and use_holiday):
            return TARIFF_OFF_PEAK

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

        return TARIFF_OFF_PEAK if is_night_time else TARIFF_PEAK

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
