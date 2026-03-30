"""Current price sensor for Real Electricity Price integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.util import dt as dt_util

from ..const import (
    CONF_HAS_NIGHT_TARIFF,
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_TIME,
    HAS_NIGHT_TARIFF_DEFAULT,
    NIGHT_PRICE_END_TIME_DEFAULT,
    NIGHT_PRICE_START_TIME_DEFAULT,
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


def _read_current_hour_tariff(coordinator) -> str | None:
    """Read tariff from current hour's pre-computed data."""
    if not coordinator.data:
        return None
    now = dt_util.now().replace(minute=0, second=0, microsecond=0)
    for data_key in ["today", "yesterday", "tomorrow"]:
        day_data = coordinator.data.get(data_key)
        if not isinstance(day_data, dict):
            continue
        for price_entry in day_data.get("hourly_prices", []):
            try:
                start_time = dt_util.parse_datetime(price_entry["start_time"])
                end_time = dt_util.parse_datetime(price_entry["end_time"])
                if start_time and end_time and start_time <= now < end_time:
                    tariff = price_entry.get("tariff")
                    if tariff:
                        return tariff
            except (ValueError, KeyError):
                continue
    return None


def _determine_tariff_from_config(coordinator) -> str:
    """Determine current tariff from config without holiday lookup (fallback)."""
    config_data = {
        **coordinator.config_entry.data,
        **coordinator.config_entry.options,
    }
    has_night_tariff = config_data.get(CONF_HAS_NIGHT_TARIFF, HAS_NIGHT_TARIFF_DEFAULT)
    if not has_night_tariff:
        return TARIFF_FIXED

    start_val = config_data.get(
        CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT
    )
    end_val = config_data.get(
        CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT
    )
    night_start = (
        int(start_val["hour"])
        if isinstance(start_val, dict) and "hour" in start_val
        else _DEFAULT_NIGHT_START_HOUR
    )
    night_end = (
        int(end_val["hour"])
        if isinstance(end_val, dict) and "hour" in end_val
        else _DEFAULT_NIGHT_END_HOUR
    )
    local_hour = dt_util.now().hour
    if night_start > night_end:
        is_night_time = local_hour >= night_start or local_hour < night_end
    else:
        is_night_time = night_start <= local_hour < night_end
    return TARIFF_OFF_PEAK if is_night_time else TARIFF_PEAK


def _get_current_tariff(coordinator) -> str:
    """Get current tariff from pre-computed hourly data, with config fallback."""
    tariff = _read_current_hour_tariff(coordinator)
    if tariff is not None:
        return tariff
    return _determine_tariff_from_config(coordinator)


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
        current_tariff = _get_current_tariff(self.coordinator)
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
            f"{grid_name.lower()}_supply_security_fee": self._round_price(
                config.grid_supply_security_fee
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
            f"{supplier_name.lower()}_balancing_capacity_fee": self._round_price(
                config.supplier_balancing_capacity_fee
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
        current_tariff = _get_current_tariff(self.coordinator)
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
        vat_grid_supply_security = config.vat_grid_supply_security_fee
        vat_transmission_night = config.vat_grid_transmission_night
        vat_transmission_day = config.vat_grid_transmission_day
        vat_supplier_renewable = config.vat_supplier_renewable_energy_charge
        vat_supplier_margin = config.vat_supplier_margin
        vat_supplier_balancing_capacity = (
            config.vat_supplier_balancing_capacity_fee
        )

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

        supply_security_component = config.grid_supply_security_fee
        if vat_grid_supply_security:
            supply_security_component *= 1 + vat_percentage / 100

        renewable_supplier_component = config.supplier_renewable_energy_charge
        if vat_supplier_renewable:
            renewable_supplier_component *= 1 + vat_percentage / 100

        margin_component = config.supplier_margin
        if vat_supplier_margin:
            margin_component *= 1 + vat_percentage / 100

        balancing_capacity_component = config.supplier_balancing_capacity_fee
        if vat_supplier_balancing_capacity:
            balancing_capacity_component *= 1 + vat_percentage / 100

        transmission_component = transmission_price
        if vat_transmission:
            transmission_component *= 1 + vat_percentage / 100

        # Calculate final price
        final_price = (
            base_price_component
            + excise_component
            + renewable_grid_component
            + supply_security_component
            + renewable_supplier_component
            + margin_component
            + balancing_capacity_component
            + transmission_component
        )

        return {
            "vat_settings": {
                "vat_rate": self._round_price(vat_percentage),
                "vat_nord_pool": vat_nord_pool,
                f"vat_{grid_name.lower()}_excise_duty": vat_grid_excise_duty,
                f"vat_{grid_name.lower()}_renewable": vat_grid_renewable,
                f"vat_{grid_name.lower()}_supply_security_fee": vat_grid_supply_security,
                f"vat_{grid_name.lower()}_transmission_{current_tariff}": vat_transmission,
                f"vat_{supplier_name.lower()}_renewable": vat_supplier_renewable,
                f"vat_{supplier_name.lower()}_margin": vat_supplier_margin,
                f"vat_{supplier_name.lower()}_balancing_capacity_fee": (
                    vat_supplier_balancing_capacity
                ),
            },
            "components_with_vat": {
                "nord_pool_price": self._round_price(base_price_component),
                f"{grid_name.lower()}_electricity_excise_duty": self._round_price(
                    excise_component
                ),
                f"{grid_name.lower()}_renewable_energy_charge": self._round_price(
                    renewable_grid_component
                ),
                f"{grid_name.lower()}_supply_security_fee": self._round_price(
                    supply_security_component
                ),
                f"{grid_name.lower()}_transmission_price_{current_tariff}": self._round_price(
                    transmission_component
                ),
                f"{supplier_name.lower()}_renewable_energy_charge": self._round_price(
                    renewable_supplier_component
                ),
                f"{supplier_name.lower()}_margin": self._round_price(margin_component),
                f"{supplier_name.lower()}_balancing_capacity_fee": self._round_price(
                    balancing_capacity_component
                ),
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
        """Determine the current tariff from pre-computed hourly data."""
        return _get_current_tariff(self.coordinator)
