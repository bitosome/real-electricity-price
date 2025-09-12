"""Adds config flow for Real Electricity Price integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    ACCEPTABLE_PRICE_DEFAULT,
    CHART_COLOR_CHEAP_CURRENT_HOUR_DEFAULT,
    CHART_COLOR_CHEAP_HOURS_DEFAULT,
    CHART_COLOR_CURRENT_HOUR_DEFAULT,
    CHART_COLOR_FUTURE_HOURS_DEFAULT,
    CHART_COLOR_PAST_HOURS_DEFAULT,
    CONF_ACCEPTABLE_PRICE,
    CONF_CALCULATE_CHEAP_HOURS,
    CONF_CHART_COLOR_CHEAP_CURRENT_HOUR,
    CONF_CHART_COLOR_CHEAP_HOURS,
    CONF_CHART_COLOR_CURRENT_HOUR,
    CONF_CHART_COLOR_FUTURE_HOURS,
    CONF_CHART_COLOR_PAST_HOURS,
    CONF_COUNTRY_CODE,
    CONF_GRID,
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK1,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK2,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_PEAK,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_HAS_NIGHT_TARIFF,
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_TIME,
    CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
    CONF_NIGHT_TARIFF_SATURDAY,
    CONF_NIGHT_TARIFF_SUNDAY,
    CONF_OFFPEAK_STRATEGY,
    CONF_REGIONAL_HOLIDAY_CODE,
    CONF_SCAN_INTERVAL,
    CONF_SUPPLIER,
    CONF_SUPPLIER_MARGIN,
    CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT,
    CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT_GRID_TRANSMISSION_DAY,
    CONF_VAT_GRID_TRANSMISSION_NIGHT,
    CONF_VAT_NORD_POOL,
    CONF_VAT_SUPPLIER_MARGIN,
    CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    COUNTRY_CODE_DEFAULT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    GRID_DEFAULT,
    GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
    GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    HAS_NIGHT_TARIFF_DEFAULT,
    NIGHT_PRICE_END_TIME_DEFAULT,
    # Use time defaults only; derive hours from time strings
    NIGHT_PRICE_START_TIME_DEFAULT,
    NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT,
    NIGHT_TARIFF_SATURDAY_DEFAULT,
    NIGHT_TARIFF_SUNDAY_DEFAULT,
    OFFPEAK_STRATEGY_DEFAULT,
    OFFPEAK_STRATEGY_NIGHT_WINDOW,
    OFFPEAK_STRATEGY_NP_BLOCKS,
    SCAN_INTERVAL_MAX,
    SCAN_INTERVAL_MIN,
    SCAN_INTERVAL_STEP,
    SUPPLIER_DEFAULT,
    SUPPLIER_MARGIN_DEFAULT,
    SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    VAT_DEFAULT,
    VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    VAT_GRID_TRANSMISSION_DAY_DEFAULT,
    VAT_GRID_TRANSMISSION_NIGHT_DEFAULT,
    VAT_NORD_POOL_DEFAULT,
    VAT_SUPPLIER_MARGIN_DEFAULT,
    VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    parse_time_string,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LOGGER.debug("Config flow module loaded")

# Valid Nord Pool area codes
VALID_COUNTRY_CODES = [
    "EE",
    "FI",
    "LV",
    "LT",
    "SE1",
    "SE2",
    "SE3",
    "SE4",
    "NO1",
    "NO2",
    "NO3",
    "NO4",
    "NO5",
    "DK1",
    "DK2",
    # Extended Central-Western Europe day-ahead areas supported by Nord Pool
    "DE-LU",
    "NL",
    "BE",
    "FR",
    "AT",
    "PL",
    "GB",
]


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Validate country code
    country_code = data.get(CONF_COUNTRY_CODE, "").upper()
    if country_code not in VALID_COUNTRY_CODES:
        msg = f"Country code must be one of: {', '.join(VALID_COUNTRY_CODES)}"
        raise InvalidCountryCode(msg)

    # Validate VAT rate
    vat_rate = data.get(CONF_VAT, 0)
    if not 0 <= vat_rate <= 100:
        msg = "VAT rate must be between 0% and 100%"
        raise InvalidVatRate(msg)

    # Validate scan interval
    scan_interval = data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    if not SCAN_INTERVAL_MIN <= scan_interval <= SCAN_INTERVAL_MAX:
        msg = (
            f"Scan interval must be between 5 minutes ({SCAN_INTERVAL_MIN} seconds) "
            f"and 24 hours ({SCAN_INTERVAL_MAX} seconds)"
        )
        raise InvalidScanInterval(msg)

    # Validate cheap hours configuration if enabled
    calculate_cheap = data.get(CONF_CALCULATE_CHEAP_HOURS, False)
    if calculate_cheap:
        # No additional validation needed for cheap hours
        pass

    # Handle time settings based on night tariff toggle and chosen strategy
    has_night_tariff = data.get(CONF_HAS_NIGHT_TARIFF, HAS_NIGHT_TARIFF_DEFAULT)
    strategy = data.get(CONF_OFFPEAK_STRATEGY, OFFPEAK_STRATEGY_DEFAULT)
    if has_night_tariff and strategy == OFFPEAK_STRATEGY_NIGHT_WINDOW:
        # Validate TimeSelector format: require both start and end time
        start_val = data.get(CONF_NIGHT_PRICE_START_TIME)
        end_val = data.get(CONF_NIGHT_PRICE_END_TIME)

        if start_val is None or end_val is None:
            raise InvalidTimeFormat("Night price start/end time is required")

        # Extract hours from either dict {hour, minute} or string "HH:MM[:SS]"
        try:
            if isinstance(start_val, dict) and "hour" in start_val:
                start_hour = int(start_val["hour"])
            elif isinstance(start_val, str):
                start_hour, _, _ = parse_time_string(start_val)
            else:
                raise InvalidTimeFormat(f"Night price start time format is invalid: {start_val}")

            if isinstance(end_val, dict) and "hour" in end_val:
                end_hour = int(end_val["hour"])
            elif isinstance(end_val, str):
                end_hour, _, _ = parse_time_string(end_val)
            else:
                raise InvalidTimeFormat(f"Night price end time format is invalid: {end_val}")
        except ValueError as e:
            raise InvalidTimeFormat(str(e)) from e

        # Validate hour ranges
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            msg = "Night price hours must be between 00 and 23"
            raise InvalidHourRange(msg)

        # Validate time range logic - handle midnight crossover for night hours
        if start_hour == end_hour and end_hour != 0:
            msg = "Night price start and end times cannot be the same"
            raise InvalidNightHours(msg)
    elif not has_night_tariff:
        # Night tariff is disabled — no time validation needed
        pass
    else:
        # has_night_tariff is True but strategy is block-aligned -> skip window time validation entirely
        # Validate block tariff numeric fields if provided
        for key in (
            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK1,
            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_PEAK,
            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK2,
        ):
            val = data.get(key)
            if val is not None:
                try:
                    float(val)
                except (TypeError, ValueError):
                    msg = f"{key} must be a number"
                    raise InvalidTimeFormat(msg)

    # Normalize times into dict format for consistency across consumers
    def _to_dict_time(val: Any) -> dict[str, int] | None:
        try:
            if isinstance(val, dict) and "hour" in val and "minute" in val:
                return {"hour": int(val["hour"]), "minute": int(val["minute"])}
            if isinstance(val, str):
                h, m, _ = parse_time_string(val)
                return {"hour": h, "minute": m}
        except Exception:
            return None
        return None

    # night window normalization (only when applicable)
    if has_night_tariff and strategy == OFFPEAK_STRATEGY_NIGHT_WINDOW:
        if CONF_NIGHT_PRICE_START_TIME in data and data[CONF_NIGHT_PRICE_START_TIME] is not None:
            norm = _to_dict_time(data[CONF_NIGHT_PRICE_START_TIME])
            if norm is not None:
                data[CONF_NIGHT_PRICE_START_TIME] = norm
        if CONF_NIGHT_PRICE_END_TIME in data and data[CONF_NIGHT_PRICE_END_TIME] is not None:
            norm = _to_dict_time(data[CONF_NIGHT_PRICE_END_TIME])
            if norm is not None:
                data[CONF_NIGHT_PRICE_END_TIME] = norm

    # Normalize color values if present
    color_fields = [
        CONF_CHART_COLOR_PAST_HOURS,
        CONF_CHART_COLOR_CURRENT_HOUR,
        CONF_CHART_COLOR_FUTURE_HOURS,
    ]
    
    color_defaults = {
        CONF_CHART_COLOR_PAST_HOURS: CHART_COLOR_PAST_HOURS_DEFAULT,
        CONF_CHART_COLOR_CURRENT_HOUR: CHART_COLOR_CURRENT_HOUR_DEFAULT,
        CONF_CHART_COLOR_FUTURE_HOURS: CHART_COLOR_FUTURE_HOURS_DEFAULT,
    }
    
    # Add cheap hours colors only if cheap hours calculation is enabled
    if data.get(CONF_CALCULATE_CHEAP_HOURS, False):
        color_fields.extend([
            CONF_CHART_COLOR_CHEAP_HOURS,
            CONF_CHART_COLOR_CHEAP_CURRENT_HOUR,
        ])
        color_defaults.update({
            CONF_CHART_COLOR_CHEAP_HOURS: CHART_COLOR_CHEAP_HOURS_DEFAULT,
            CONF_CHART_COLOR_CHEAP_CURRENT_HOUR: CHART_COLOR_CHEAP_CURRENT_HOUR_DEFAULT,
        })
    
    # Validate acceptable price if present
    if CONF_ACCEPTABLE_PRICE in data:
        acceptable_price = data[CONF_ACCEPTABLE_PRICE]
        try:
            acceptable_price = float(acceptable_price)
            if acceptable_price < 0:
                msg = "Acceptable price must be a non-negative number"
                raise InvalidTimeFormat(msg)
        except (TypeError, ValueError):
            msg = "Acceptable price must be a valid number"
            raise InvalidTimeFormat(msg)
    
    for field in color_fields:
        if field in data:
            data[field] = _validate_and_normalize_color(data[field], color_defaults[field])

    # Test connection to Nord Pool API
    try:
        # This would normally test actual API connectivity
        # For now, we'll do basic validation
        return {"title": data.get(CONF_NAME, "Real Electricity Price")}
    except Exception as exc:
        _LOGGER.exception("Unexpected exception: %s", exc)
        raise CannotConnect from exc



def _validate_and_normalize_color(color_value, default_color: str) -> str:
    """Validate and normalize color value from config."""
    if color_value is None:
        return default_color
    
    if isinstance(color_value, str):
        # Already a hex string
        if color_value.startswith("#") and len(color_value) in [4, 7]:
            return color_value
        else:
            return default_color
    
    elif isinstance(color_value, (list, tuple)) and len(color_value) >= 3:
        # RGB array, convert to hex
        try:
            r = max(0, min(255, int(float(color_value[0]))))
            g = max(0, min(255, int(float(color_value[1]))))
            b = max(0, min(255, int(float(color_value[2]))))
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, TypeError, IndexError):
            return default_color
    
    elif isinstance(color_value, dict):
        # Handle dict format from color picker
        if "r" in color_value and "g" in color_value and "b" in color_value:
            try:
                r = max(0, min(255, int(float(color_value["r"]))))
                g = max(0, min(255, int(float(color_value["g"]))))
                b = max(0, min(255, int(float(color_value["b"]))))
                return f"#{r:02x}{g:02x}{b:02x}"
            except (ValueError, TypeError, KeyError):
                return default_color
    
    return default_color


def _validate_time_string(time_val: Any) -> bool:
    """Validate time from HA TimeSelector: supports dict or "HH:MM[:SS]" string."""
    # Dict format {"hour": int, "minute": int}
    if isinstance(time_val, dict):
        if "hour" in time_val and "minute" in time_val:
            hour = time_val["hour"]
            minute = time_val["minute"]
            return (
                isinstance(hour, int)
                and isinstance(minute, int)
                and 0 <= hour <= 23
                and 0 <= minute <= 59
            )
        return False
    # String format "HH:MM" or "HH:MM:SS"
    if isinstance(time_val, str):
        try:
            hour, minute, _ = parse_time_string(time_val)
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except Exception:
            return False
    return False


class RealElectricityPriceFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Real Electricity Price."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors: dict[str, str] = {}
        self._user_data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.debug("async_step_user called with user_input: %s", user_input)
        self._errors = {}

        if user_input is not None:
            # If night tariff is enabled, branch to choose strategy first
            if user_input.get(CONF_HAS_NIGHT_TARIFF, HAS_NIGHT_TARIFF_DEFAULT):
                self._user_data = user_input
                return await self.async_step_offpeak_strategy()

            # Night tariff disabled; if cheap hours is enabled, go to chart colors step
            if user_input.get(CONF_CALCULATE_CHEAP_HOURS, False):
                self._user_data = user_input
                return await self.async_step_chart_colors()

            # No additional config steps required, go to chart colors step
            self._user_data = user_input
            return await self.async_step_chart_colors()

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_user_schema(user_input),
            errors=self._errors,
        )

    async def async_step_offpeak_strategy(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Choose how to determine off-peak periods."""
        _LOGGER.debug("async_step_offpeak_strategy called with user_input: %s", user_input)
        self._errors = {}

        if user_input is not None:
            merged = {**self._user_data, **user_input}
            self._user_data = merged
            strategy = merged.get(CONF_OFFPEAK_STRATEGY, OFFPEAK_STRATEGY_DEFAULT)
            if strategy == OFFPEAK_STRATEGY_NP_BLOCKS:
                return await self.async_step_block_tariffs()
            # Default to night window times step
            return await self.async_step_night_times()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_OFFPEAK_STRATEGY,
                    default=self._user_data.get(
                        CONF_OFFPEAK_STRATEGY, OFFPEAK_STRATEGY_DEFAULT
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": OFFPEAK_STRATEGY_NIGHT_WINDOW, "label": "Night Window (fixed time periods)"},
                            {"value": OFFPEAK_STRATEGY_NP_BLOCKS, "label": "Nord Pool Blocks (Off-peak 1, Peak, Off-peak 2)"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="offpeak_strategy",
            data_schema=schema,
            errors=self._errors,
        )

    async def async_step_block_tariffs(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect per-block transmission prices when using Nord Pool blocks."""
        _LOGGER.debug("async_step_block_tariffs called with user_input: %s", user_input)
        self._errors = {}

        if user_input is not None:
            merged = {**self._user_data, **user_input}
            try:
                # With block strategy, skip time validation (times may be absent)
                info = await validate_input(self.hass, merged)
            except InvalidCountryCode:
                self._errors["country_code"] = "invalid_country_code"
            except InvalidVatRate:
                self._errors["vat"] = "invalid_vat_rate"
            except InvalidScanInterval:
                self._errors["scan_interval"] = "invalid_scan_interval"
            except CannotConnect:
                self._errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                self._errors["base"] = "unknown"
            else:
                # Proceed to cheap hours step if enabled, otherwise go to chart colors
                if merged.get(CONF_CALCULATE_CHEAP_HOURS, False):
                    self._user_data = merged
                    return await self.async_step_chart_colors()
                else:
                    self._user_data = merged
                    return await self.async_step_chart_colors()

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK1,
                    default=self._user_data.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK1,
                        GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_PEAK,
                    default=self._user_data.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_PEAK,
                        GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK2,
                    default=self._user_data.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK2,
                        GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_NIGHT_TARIFF_SATURDAY,
                    default=self._user_data.get(
                        CONF_NIGHT_TARIFF_SATURDAY, NIGHT_TARIFF_SATURDAY_DEFAULT
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_SUNDAY,
                    default=self._user_data.get(
                        CONF_NIGHT_TARIFF_SUNDAY, NIGHT_TARIFF_SUNDAY_DEFAULT
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                    default=self._user_data.get(
                        CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                        NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT,
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_REGIONAL_HOLIDAY_CODE,
                    default=self._user_data.get(
                        CONF_REGIONAL_HOLIDAY_CODE, ""
                    ),
                ): selector.TextSelector(),
            }
        )

        return self.async_show_form(
            step_id="block_tariffs",
            data_schema=schema,
            errors=self._errors,
        )

    def _get_user_schema(self, user_input: dict | None = None) -> vol.Schema:
        """Get the user input schema."""
        user_input = user_input or {}
        _LOGGER.debug(
            f"Creating user schema (step_user) with user_input keys: {list(user_input.keys())}"
        )

        schema_dict = {
                vol.Optional(
                    CONF_NAME,
                    default=user_input.get(CONF_NAME, "Real Electricity Price"),
                ): selector.TextSelector(),
                # Grid parameters
                vol.Optional(
                    CONF_GRID,
                    default=user_input.get(CONF_GRID, GRID_DEFAULT),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                    default=user_input.get(
                        CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                        GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                    default=user_input.get(
                        CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                        GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                    default=user_input.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                        GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                    default=user_input.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                        GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                # Supplier parameters
                vol.Optional(
                    CONF_SUPPLIER,
                    default=user_input.get(CONF_SUPPLIER, SUPPLIER_DEFAULT),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                    default=user_input.get(
                        CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                        SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_SUPPLIER_MARGIN,
                    default=user_input.get(
                        CONF_SUPPLIER_MARGIN,
                        SUPPLIER_MARGIN_DEFAULT,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                # Regional and tax settings
                vol.Optional(
                    CONF_COUNTRY_CODE,
                    default=user_input.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=VALID_COUNTRY_CODES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="country_code",
                    )
                ),
                vol.Optional(
                    CONF_VAT,
                    default=user_input.get(CONF_VAT, VAT_DEFAULT),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=0.1, mode="box")
                ),
                # Individual VAT controls for each price component
                vol.Optional(
                    CONF_VAT_NORD_POOL,
                    default=user_input.get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                    default=user_input.get(
                        CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                        VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                    default=user_input.get(
                        CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                        VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_GRID_TRANSMISSION_NIGHT,
                    default=user_input.get(
                        CONF_VAT_GRID_TRANSMISSION_NIGHT,
                        VAT_GRID_TRANSMISSION_NIGHT_DEFAULT,
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_GRID_TRANSMISSION_DAY,
                    default=user_input.get(
                        CONF_VAT_GRID_TRANSMISSION_DAY,
                        VAT_GRID_TRANSMISSION_DAY_DEFAULT,
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                    default=user_input.get(
                        CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                        VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_SUPPLIER_MARGIN,
                    default=user_input.get(
                        CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT
                    ),
                ): selector.BooleanSelector(),
                # Night/Day tariff configuration (times collected in next step if enabled)
                vol.Optional(
                    CONF_HAS_NIGHT_TARIFF,
                    default=user_input.get(CONF_HAS_NIGHT_TARIFF, HAS_NIGHT_TARIFF_DEFAULT),
                ): selector.BooleanSelector(),
                # Cheap hours (additional step when enabled)
                vol.Optional(
                    CONF_CALCULATE_CHEAP_HOURS,
                    default=user_input.get(CONF_CALCULATE_CHEAP_HOURS, True),
                ): selector.BooleanSelector(),
                # Update interval
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=SCAN_INTERVAL_MIN,
                        max=SCAN_INTERVAL_MAX,
                        step=SCAN_INTERVAL_STEP,
                        mode="box",
                    )  # 5 min to 24 hours
                ),
        }

        _LOGGER.debug(f"Final schema has {len(schema_dict)} fields")
        return vol.Schema(schema_dict)

    async def async_step_night_times(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect night start/end times when night tariff is enabled."""
        _LOGGER.debug("async_step_night_times called with user_input: %s", user_input)
        self._errors = {}

        if user_input is not None:
            # Merge with previously collected data
            merged = {**self._user_data, **user_input}
            # If cheap hours are enabled, go to cheap_hours step, otherwise go to chart_colors
            if merged.get(CONF_CALCULATE_CHEAP_HOURS, False):
                self._user_data = merged
                return await self.async_step_chart_colors()
            else:
                self._user_data = merged
                return await self.async_step_chart_colors()

        # Show time selectors
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NIGHT_PRICE_START_TIME,
                    default=self._user_data.get(
                        CONF_NIGHT_PRICE_START_TIME,
                        {
                            "hour": parse_time_string(NIGHT_PRICE_START_TIME_DEFAULT)[0],
                            "minute": parse_time_string(NIGHT_PRICE_START_TIME_DEFAULT)[1],
                        },
                    ),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_NIGHT_PRICE_END_TIME,
                    default=self._user_data.get(
                        CONF_NIGHT_PRICE_END_TIME,
                        {
                            "hour": parse_time_string(NIGHT_PRICE_END_TIME_DEFAULT)[0],
                            "minute": parse_time_string(NIGHT_PRICE_END_TIME_DEFAULT)[1],
                        },
                    ),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_SATURDAY,
                    default=self._user_data.get(
                        CONF_NIGHT_TARIFF_SATURDAY, NIGHT_TARIFF_SATURDAY_DEFAULT
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_SUNDAY,
                    default=self._user_data.get(
                        CONF_NIGHT_TARIFF_SUNDAY, NIGHT_TARIFF_SUNDAY_DEFAULT
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                    default=self._user_data.get(
                        CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                        NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT,
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_REGIONAL_HOLIDAY_CODE,
                    default=self._user_data.get(
                        CONF_REGIONAL_HOLIDAY_CODE, ""
                    ),
                ): selector.TextSelector(),
            }
        )

        return self.async_show_form(
            step_id="night_times",
            data_schema=schema,
            errors=self._errors,
        )

    async def async_step_chart_colors(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure chart colors for ApexCharts display."""
        _LOGGER.debug("async_step_chart_colors called with user_input: %s", user_input)
        self._errors = {}

        if user_input is not None:
            merged = {**self._user_data, **user_input}
            try:
                info = await validate_input(self.hass, merged)
            except InvalidCountryCode:
                self._errors["country_code"] = "invalid_country_code"
            except InvalidVatRate:
                self._errors["vat"] = "invalid_vat_rate"
            except InvalidScanInterval:
                self._errors["scan_interval"] = "invalid_scan_interval"
            except InvalidHourRange:
                self._errors["base"] = "invalid_hour_range"
            except InvalidNightHours:
                self._errors["base"] = "invalid_night_hours"
            except InvalidTimeFormat:
                self._errors["base"] = "invalid_time_format"
            except CannotConnect:
                self._errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                self._errors["base"] = "unknown"
            else:
                name = merged.get(CONF_NAME, "Real Electricity Price")
                grid = merged.get(CONF_GRID, GRID_DEFAULT)
                supplier = merged.get(CONF_SUPPLIER, SUPPLIER_DEFAULT)
                country = merged.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT)

                unique_id = f"real_electricity_price_{name}_{grid}_{supplier}_{country}".lower().replace(
                    " ", "_"
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=merged)

        # Create base schema with always-present colors
        schema_dict = {
            vol.Optional(
                CONF_CHART_COLOR_PAST_HOURS,
                default=self._user_data.get(
                    CONF_CHART_COLOR_PAST_HOURS, CHART_COLOR_PAST_HOURS_DEFAULT
                ),
            ): selector.ColorRGBSelector(),
            vol.Optional(
                CONF_CHART_COLOR_CURRENT_HOUR,
                default=self._user_data.get(
                    CONF_CHART_COLOR_CURRENT_HOUR, CHART_COLOR_CURRENT_HOUR_DEFAULT
                ),
            ): selector.ColorRGBSelector(),
            vol.Optional(
                CONF_CHART_COLOR_FUTURE_HOURS,
                default=self._user_data.get(
                    CONF_CHART_COLOR_FUTURE_HOURS, CHART_COLOR_FUTURE_HOURS_DEFAULT
                ),
            ): selector.ColorRGBSelector(),
        }
        
        # Only add cheap hours colors if cheap hours calculation is enabled
        if self._user_data.get(CONF_CALCULATE_CHEAP_HOURS, False):
            schema_dict.update({
                vol.Optional(
                    CONF_CHART_COLOR_CHEAP_HOURS,
                    default=self._user_data.get(
                        CONF_CHART_COLOR_CHEAP_HOURS, CHART_COLOR_CHEAP_HOURS_DEFAULT
                    ),
                ): selector.ColorRGBSelector(),
                vol.Optional(
                    CONF_CHART_COLOR_CHEAP_CURRENT_HOUR,
                    default=self._user_data.get(
                        CONF_CHART_COLOR_CHEAP_CURRENT_HOUR, CHART_COLOR_CHEAP_CURRENT_HOUR_DEFAULT
                    ),
                ): selector.ColorRGBSelector(),
            })
        
        schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="chart_colors",
            data_schema=schema,
            errors=self._errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for Real Electricity Price."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._errors: dict[str, str] = {}

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        self._errors = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except InvalidCountryCode:
                self._errors["country_code"] = "invalid_country_code"
            except InvalidVatRate:
                self._errors["vat"] = "invalid_vat_rate"
            except InvalidScanInterval:
                self._errors["scan_interval"] = "invalid_scan_interval"
            except InvalidHourRange:
                self._errors["base"] = "invalid_hour_range"
            except InvalidNightHours:
                self._errors["base"] = "invalid_night_hours"
            except InvalidTimeFormat:
                self._errors["base"] = "invalid_time_format"
            except CannotConnect:
                self._errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                self._errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="", data=user_input)

        # Get current config values
        current_data = self.config_entry.data
        options_data = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(current_data, options_data),
            errors=self._errors,
        )

    def _get_options_schema(self, current_data: dict, options_data: dict) -> vol.Schema:
        """Get the options schema."""
        # Check if night tariff is enabled to conditionally show fields
        has_night_tariff = options_data.get(
            CONF_HAS_NIGHT_TARIFF,
            current_data.get(CONF_HAS_NIGHT_TARIFF, HAS_NIGHT_TARIFF_DEFAULT),
        )
        strategy = options_data.get(
            CONF_OFFPEAK_STRATEGY,
            current_data.get(CONF_OFFPEAK_STRATEGY, OFFPEAK_STRATEGY_DEFAULT),
        )
        calculate_cheap = options_data.get(
            CONF_CALCULATE_CHEAP_HOURS,
            current_data.get(CONF_CALCULATE_CHEAP_HOURS, True),
        )

        schema_dict = {
                vol.Optional(
                    CONF_NAME,
                    default=options_data.get(
                        CONF_NAME, current_data.get(CONF_NAME, "Real Electricity Price")
                    ),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_OFFPEAK_STRATEGY,
                    default=options_data.get(
                        CONF_OFFPEAK_STRATEGY,
                        current_data.get(
                            CONF_OFFPEAK_STRATEGY, OFFPEAK_STRATEGY_DEFAULT
                        ),
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": OFFPEAK_STRATEGY_NIGHT_WINDOW, "label": "Night Window (fixed time periods)"},
                            {"value": OFFPEAK_STRATEGY_NP_BLOCKS, "label": "Nord Pool Blocks (Off-peak 1, Peak, Off-peak 2)"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                # Grid parameters
                vol.Optional(
                    CONF_GRID,
                    default=options_data.get(
                        CONF_GRID, current_data.get(CONF_GRID, GRID_DEFAULT)
                    ),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                    default=options_data.get(
                        CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                        current_data.get(
                            CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                            GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                    default=options_data.get(
                        CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                        current_data.get(
                            CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                            GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                    default=options_data.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                        current_data.get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                    default=options_data.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                        current_data.get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                # Supplier parameters
                vol.Optional(
                    CONF_SUPPLIER,
                    default=options_data.get(
                        CONF_SUPPLIER, current_data.get(CONF_SUPPLIER, SUPPLIER_DEFAULT)
                    ),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                    default=options_data.get(
                        CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                        current_data.get(
                            CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                            SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_SUPPLIER_MARGIN,
                    default=options_data.get(
                        CONF_SUPPLIER_MARGIN,
                        current_data.get(
                            CONF_SUPPLIER_MARGIN,
                            SUPPLIER_MARGIN_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                # Regional and tax settings
                vol.Optional(
                    CONF_COUNTRY_CODE,
                    default=options_data.get(
                        CONF_COUNTRY_CODE,
                        current_data.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT),
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=VALID_COUNTRY_CODES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="country_code",
                    )
                ),
                vol.Optional(
                    CONF_VAT,
                    default=options_data.get(
                        CONF_VAT, current_data.get(CONF_VAT, VAT_DEFAULT)
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=0.1, mode="box")
                ),
                # Individual VAT controls for each price component
                vol.Optional(
                    CONF_VAT_NORD_POOL,
                    default=options_data.get(
                        CONF_VAT_NORD_POOL,
                        current_data.get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                    default=options_data.get(
                        CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                        current_data.get(
                            CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                            VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                    default=options_data.get(
                        CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                        current_data.get(
                            CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                            VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_GRID_TRANSMISSION_NIGHT,
                    default=options_data.get(
                        CONF_VAT_GRID_TRANSMISSION_NIGHT,
                        current_data.get(
                            CONF_VAT_GRID_TRANSMISSION_NIGHT,
                            VAT_GRID_TRANSMISSION_NIGHT_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_GRID_TRANSMISSION_DAY,
                    default=options_data.get(
                        CONF_VAT_GRID_TRANSMISSION_DAY,
                        current_data.get(
                            CONF_VAT_GRID_TRANSMISSION_DAY,
                            VAT_GRID_TRANSMISSION_DAY_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                    default=options_data.get(
                        CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                        current_data.get(
                            CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                            VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_VAT_SUPPLIER_MARGIN,
                    default=options_data.get(
                        CONF_VAT_SUPPLIER_MARGIN,
                        current_data.get(
                            CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT
                        ),
                    ),
                ): selector.BooleanSelector(),
                # Night/Day tariff configuration
                vol.Optional(
                    CONF_HAS_NIGHT_TARIFF,
                    default=options_data.get(
                        CONF_HAS_NIGHT_TARIFF,
                        current_data.get(CONF_HAS_NIGHT_TARIFF, HAS_NIGHT_TARIFF_DEFAULT),
                    ),
                ): selector.BooleanSelector(),
                # Cheap hours toggle
                vol.Optional(
                    CONF_CALCULATE_CHEAP_HOURS,
                    default=options_data.get(
                        CONF_CALCULATE_CHEAP_HOURS,
                        current_data.get(CONF_CALCULATE_CHEAP_HOURS, True),
                    ),
                ): selector.BooleanSelector(),
                # Update interval
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options_data.get(
                        CONF_SCAN_INTERVAL,
                        current_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=SCAN_INTERVAL_MIN,
                        max=SCAN_INTERVAL_MAX,
                        step=SCAN_INTERVAL_STEP,
                        mode="box",
                    )  # 5 min to 24 hours
                ),
        }

        # Only add time fields when night tariff is enabled; omit entirely when disabled
        if has_night_tariff and strategy == OFFPEAK_STRATEGY_NIGHT_WINDOW:
            schema_dict.update({
                vol.Optional(
                    CONF_NIGHT_PRICE_START_TIME,
                    default=options_data.get(
                        CONF_NIGHT_PRICE_START_TIME,
                        current_data.get(
                            CONF_NIGHT_PRICE_START_TIME,
                            {
                                "hour": parse_time_string(NIGHT_PRICE_START_TIME_DEFAULT)[0],
                                "minute": parse_time_string(NIGHT_PRICE_START_TIME_DEFAULT)[1],
                            },
                        ),
                    ),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_NIGHT_PRICE_END_TIME,
                    default=options_data.get(
                        CONF_NIGHT_PRICE_END_TIME,
                        current_data.get(
                            CONF_NIGHT_PRICE_END_TIME,
                            {
                                "hour": parse_time_string(NIGHT_PRICE_END_TIME_DEFAULT)[0],
                                "minute": parse_time_string(NIGHT_PRICE_END_TIME_DEFAULT)[1],
                            },
                        ),
                    ),
                ): selector.TimeSelector(),
            })
            # Weekend/Public holiday rules for night tariff
            schema_dict.update({
                vol.Optional(
                    CONF_NIGHT_TARIFF_SATURDAY,
                    default=options_data.get(
                        CONF_NIGHT_TARIFF_SATURDAY,
                        current_data.get(
                            CONF_NIGHT_TARIFF_SATURDAY,
                            NIGHT_TARIFF_SATURDAY_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_SUNDAY,
                    default=options_data.get(
                        CONF_NIGHT_TARIFF_SUNDAY,
                        current_data.get(
                            CONF_NIGHT_TARIFF_SUNDAY,
                            NIGHT_TARIFF_SUNDAY_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                    default=options_data.get(
                        CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                        current_data.get(
                            CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                            NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_REGIONAL_HOLIDAY_CODE,
                    default=options_data.get(
                        CONF_REGIONAL_HOLIDAY_CODE,
                        current_data.get(CONF_REGIONAL_HOLIDAY_CODE, ""),
                    ),
                ): selector.TextSelector(),
            })
        elif has_night_tariff and strategy == OFFPEAK_STRATEGY_NP_BLOCKS:
            # Show per-block transmission price fields and weekend/holiday settings
            schema_dict.update({
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK1,
                    default=options_data.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK1,
                        current_data.get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK1,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_PEAK,
                    default=options_data.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_PEAK,
                        current_data.get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_PEAK,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK2,
                    default=options_data.get(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK2,
                        current_data.get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK2,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
                vol.Optional(
                    CONF_NIGHT_TARIFF_SATURDAY,
                    default=options_data.get(
                        CONF_NIGHT_TARIFF_SATURDAY,
                        current_data.get(
                            CONF_NIGHT_TARIFF_SATURDAY, NIGHT_TARIFF_SATURDAY_DEFAULT
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_SUNDAY,
                    default=options_data.get(
                        CONF_NIGHT_TARIFF_SUNDAY,
                        current_data.get(
                            CONF_NIGHT_TARIFF_SUNDAY, NIGHT_TARIFF_SUNDAY_DEFAULT
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                    default=options_data.get(
                        CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                        current_data.get(
                            CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY,
                            NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT,
                        ),
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_REGIONAL_HOLIDAY_CODE,
                    default=options_data.get(
                        CONF_REGIONAL_HOLIDAY_CODE,
                        current_data.get(CONF_REGIONAL_HOLIDAY_CODE, ""),
                    ),
                ): selector.TextSelector(),
            })
        else:
            _LOGGER.debug("Night tariff disabled in options; omitting night time fields")

        # Add cheap hours fields only when enabled
        if calculate_cheap:
            schema_dict.update(
                {
                    vol.Optional(
                        CONF_ACCEPTABLE_PRICE,
                        default=options_data.get(
                            CONF_ACCEPTABLE_PRICE,
                            current_data.get(
                                CONF_ACCEPTABLE_PRICE,
                                ACCEPTABLE_PRICE_DEFAULT,
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0, max=1, step="any", mode="box"
                        )
                    ),
                }
            )

        # Always add chart color options
        schema_dict.update(
            {
                vol.Optional(
                    CONF_CHART_COLOR_PAST_HOURS,
                    default=options_data.get(
                        CONF_CHART_COLOR_PAST_HOURS,
                        current_data.get(
                            CONF_CHART_COLOR_PAST_HOURS,
                            CHART_COLOR_PAST_HOURS_DEFAULT,
                        ),
                    ),
                ): selector.ColorRGBSelector(),
                vol.Optional(
                    CONF_CHART_COLOR_CURRENT_HOUR,
                    default=options_data.get(
                        CONF_CHART_COLOR_CURRENT_HOUR,
                        current_data.get(
                            CONF_CHART_COLOR_CURRENT_HOUR,
                            CHART_COLOR_CURRENT_HOUR_DEFAULT,
                        ),
                    ),
                ): selector.ColorRGBSelector(),
                vol.Optional(
                    CONF_CHART_COLOR_FUTURE_HOURS,
                    default=options_data.get(
                        CONF_CHART_COLOR_FUTURE_HOURS,
                        current_data.get(
                            CONF_CHART_COLOR_FUTURE_HOURS,
                            CHART_COLOR_FUTURE_HOURS_DEFAULT,
                        ),
                    ),
                ): selector.ColorRGBSelector(),
            }
        )

        # Add cheap-hour colors only when cheap-hour calculation is enabled
        if calculate_cheap:
            schema_dict = {
                **schema_dict,  # extract underlying dict for update
                vol.Optional(
                    CONF_CHART_COLOR_CHEAP_HOURS,
                    default=options_data.get(
                        CONF_CHART_COLOR_CHEAP_HOURS,
                        current_data.get(
                            CONF_CHART_COLOR_CHEAP_HOURS,
                            CHART_COLOR_CHEAP_HOURS_DEFAULT,
                        ),
                    ),
                ): selector.ColorRGBSelector(),
                vol.Optional(
                    CONF_CHART_COLOR_CHEAP_CURRENT_HOUR,
                    default=options_data.get(
                        CONF_CHART_COLOR_CHEAP_CURRENT_HOUR,
                        current_data.get(
                            CONF_CHART_COLOR_CHEAP_CURRENT_HOUR,
                            CHART_COLOR_CHEAP_CURRENT_HOUR_DEFAULT,
                        ),
                    ),
                ): selector.ColorRGBSelector(),
            }
            schema_dict = vol.Schema(schema_dict)

        return schema_dict


class CannotConnect(data_entry_flow.AbortFlow):
    """Error to indicate we cannot connect."""

    def __init__(self, message: str = "cannot_connect") -> None:
        super().__init__(message)


class InvalidCountryCode(data_entry_flow.AbortFlow):
    """Error to indicate invalid country code."""

    def __init__(
        self,
        message: str = (
            "Country code must be one of: EE, FI, LV, LT, SE1, SE2, SE3, SE4, "
            "NO1, NO2, NO3, NO4, NO5, DK1, DK2, DE-LU, NL, BE, FR, AT, PL, GB"
        ),
    ) -> None:
        super().__init__(message)


class InvalidVatRate(data_entry_flow.AbortFlow):
    """Error to indicate invalid VAT rate."""

    def __init__(self, message: str = "VAT rate must be between 0% and 100%") -> None:
        super().__init__(message)


class InvalidScanInterval(data_entry_flow.AbortFlow):
    """Error to indicate invalid scan interval."""

    def __init__(
        self,
        message: str = "Scan interval must be between 5 minutes (300 seconds) and 24 hours (86400 seconds)",
    ) -> None:
        super().__init__(message)


class InvalidHourRange(data_entry_flow.AbortFlow):
    """Error to indicate invalid hour range."""

    def __init__(
        self, message: str = "Night price hours must be between 00 and 23"
    ) -> None:
        super().__init__(message)


class InvalidNightHours(data_entry_flow.AbortFlow):
    """Error to indicate invalid night hour configuration."""

    def __init__(
        self, message: str = "Night price start and end times cannot be the same"
    ) -> None:
        super().__init__(message)


class InvalidTimeFormat(data_entry_flow.AbortFlow):
    """Error to indicate invalid time format."""

    def __init__(
        self, message: str = "Time must be a valid time in HH:MM format"
    ) -> None:
        super().__init__(message)
