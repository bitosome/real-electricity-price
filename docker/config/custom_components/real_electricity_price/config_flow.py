"""Adds config flow for Real Electricity Price integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .api import RealElectricityPriceApiClient
from .const import (
    CONF_COUNTRY_CODE,
    CONF_GRID,
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_NIGHT_PRICE_END_HOUR,
    CONF_NIGHT_PRICE_START_HOUR,
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_TIME,
    CONF_TIME_FORMAT_24H,
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
    CONF_CHEAP_PRICE_THRESHOLD,
    CONF_UPDATE_TRIGGER,
    CONF_CHEAP_PRICE_UPDATE_TRIGGER,
    COUNTRY_CODE_DEFAULT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UPDATE_TRIGGER,
    DEFAULT_CHEAP_PRICE_UPDATE_TRIGGER,
    DOMAIN,
    GRID_DEFAULT,
    GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
    GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    NIGHT_PRICE_END_HOUR_DEFAULT,
    NIGHT_PRICE_START_HOUR_DEFAULT,
    NIGHT_PRICE_END_TIME_DEFAULT,
    NIGHT_PRICE_START_TIME_DEFAULT,
    TIME_FORMAT_24H_DEFAULT,
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
    CHEAP_PRICE_THRESHOLD_DEFAULT,
    parse_time_string,
    time_string_to_hour,
)

_LOGGER = logging.getLogger(__name__)

# Valid Nord Pool area codes
VALID_COUNTRY_CODES = [
    "EE", "FI", "LV", "LT", "SE1", "SE2", "SE3", "SE4", 
    "NO1", "NO2", "NO3", "NO4", "NO5", "DK1", "DK2"
]


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Validate country code
    country_code = data.get(CONF_COUNTRY_CODE, "").upper()
    if country_code not in VALID_COUNTRY_CODES:
        raise InvalidCountryCode
    
    # Validate VAT rate
    vat_rate = data.get(CONF_VAT, 0)
    if not 0 <= vat_rate <= 100:
        raise InvalidVatRate
    
    # Validate scan interval (legacy support)
    scan_interval = data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    if not 300 <= scan_interval <= 86400:
        raise InvalidScanInterval
    
    # Validate update triggers
    update_trigger = data.get(CONF_UPDATE_TRIGGER, DEFAULT_UPDATE_TRIGGER)
    if not _validate_trigger_config(update_trigger):
        raise InvalidUpdateTrigger
    
    cheap_price_trigger = data.get(CONF_CHEAP_PRICE_UPDATE_TRIGGER, DEFAULT_CHEAP_PRICE_UPDATE_TRIGGER)
    if not _validate_time_string(cheap_price_trigger):
        raise InvalidCheapPriceTrigger
    
    # Validate hour ranges (legacy)
    start_hour = data.get(CONF_NIGHT_PRICE_START_HOUR, 0)
    end_hour = data.get(CONF_NIGHT_PRICE_END_HOUR, 0)
    if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
        raise InvalidHourRange
    
    if start_hour >= end_hour and end_hour != 0:
        raise InvalidNightHours
    
    # Validate time strings (new format)
    start_time_str = data.get(CONF_NIGHT_PRICE_START_TIME)
    end_time_str = data.get(CONF_NIGHT_PRICE_END_TIME)
    
    if start_time_str:
        try:
            start_hour_parsed, _, _ = parse_time_string(start_time_str)
        except ValueError:
            raise InvalidTimeFormat
    
    if end_time_str:
        try:
            end_hour_parsed, _, _ = parse_time_string(end_time_str)
        except ValueError:
            raise InvalidTimeFormat
    
    # Validate time range logic (if both time strings are provided)
    if start_time_str and end_time_str:
        try:
            start_h, _, _ = parse_time_string(start_time_str)
            end_h, _, _ = parse_time_string(end_time_str)
            if start_h >= end_h and end_h != 0:
                raise InvalidNightHours
        except ValueError:
            raise InvalidTimeFormat
    
    # Test connection to Nord Pool API
    try:
        # This would normally test actual API connectivity
        # For now, we'll do basic validation
        return {"title": data.get(CONF_NAME, "Real Electricity Price")}
    except Exception as exc:
        _LOGGER.exception("Unexpected exception: %s", exc)
        raise CannotConnect from exc


def _validate_time_string(time_str: str) -> bool:
    """Validate time string in HH:MM format."""
    if not isinstance(time_str, str):
        return False
    
    try:
        time_parts = time_str.split(":")
        if len(time_parts) != 2:
            return False
        hours, minutes = map(int, time_parts)
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except (ValueError, AttributeError):
        return False


def _validate_trigger_config(trigger_config: dict[str, Any]) -> bool:
    """Validate trigger configuration follows Home Assistant trigger format."""
    if not isinstance(trigger_config, dict):
        return False
    
    trigger_type = trigger_config.get("trigger")
    if trigger_type not in ["time", "time_pattern"]:
        return False
    
    if trigger_type == "time":
        # Must have 'at' field with HH:MM:SS format
        at_time = trigger_config.get("at")
        if not at_time or not isinstance(at_time, str):
            return False
        try:
            # Validate time format HH:MM:SS
            time_parts = at_time.split(":")
            if len(time_parts) != 3:
                return False
            hours, minutes, seconds = map(int, time_parts)
            if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
                return False
        except (ValueError, AttributeError):
            return False
    
    elif trigger_type == "time_pattern":
        # Must have at least one of: hours, minutes, seconds
        has_pattern = any(key in trigger_config for key in ["hours", "minutes", "seconds"])
        if not has_pattern:
            return False
        
        # Validate pattern values if present
        for field in ["hours", "minutes", "seconds"]:
            if field in trigger_config:
                value = trigger_config[field]
                if value is not None:
                    # Can be integer, string with integer, or pattern like "/2"
                    if isinstance(value, int):
                        max_val = 23 if field == "hours" else 59
                        if not (0 <= value <= max_val):
                            return False
                    elif isinstance(value, str):
                        if value.startswith("/"):
                            # Pattern like "/2" - validate divisor
                            try:
                                divisor = int(value[1:])
                                if divisor <= 0:
                                    return False
                            except ValueError:
                                return False
                        else:
                            # Should be a number as string
                            try:
                                val = int(value)
                                max_val = 23 if field == "hours" else 59
                                if not (0 <= val <= max_val):
                                    return False
                            except ValueError:
                                return False
    
    return True


class RealElectricityPriceFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Real Electricity Price."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors: dict[str, str] = {}

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
        self._errors = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidUpdateTrigger:
                self._errors["update_trigger"] = "invalid_update_trigger"
            except InvalidCheapPriceTrigger:
                self._errors["cheap_price_update_trigger"] = "invalid_cheap_price_trigger"
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
                # Create unique ID based on name, grid, and supplier to allow multiple devices
                name = user_input.get(CONF_NAME, "Real Electricity Price")
                grid = user_input.get(CONF_GRID, GRID_DEFAULT)
                supplier = user_input.get(CONF_SUPPLIER, SUPPLIER_DEFAULT)
                country = user_input.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT)
                
                unique_id = f"real_electricity_price_{name}_{grid}_{supplier}_{country}".lower().replace(" ", "_")
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_user_schema(user_input),
            errors=self._errors,
        )

    def _get_user_schema(self, user_input: dict | None = None) -> vol.Schema:
        """Get the user input schema."""
        user_input = user_input or {}
        
        return vol.Schema({
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
                default=user_input.get(CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY, VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                default=user_input.get(CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE, VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_GRID_TRANSMISSION_NIGHT,
                default=user_input.get(CONF_VAT_GRID_TRANSMISSION_NIGHT, VAT_GRID_TRANSMISSION_NIGHT_DEFAULT),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_GRID_TRANSMISSION_DAY,
                default=user_input.get(CONF_VAT_GRID_TRANSMISSION_DAY, VAT_GRID_TRANSMISSION_DAY_DEFAULT),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                default=user_input.get(CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE, VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_SUPPLIER_MARGIN,
                default=user_input.get(CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT),
            ): selector.BooleanSelector(),
            # Time format preference
            vol.Optional(
                CONF_TIME_FORMAT_24H,
                default=user_input.get(CONF_TIME_FORMAT_24H, TIME_FORMAT_24H_DEFAULT),
            ): selector.BooleanSelector(),
            # Time settings - new natural format
            vol.Optional(
                CONF_NIGHT_PRICE_START_TIME,
                default=user_input.get(
                    CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT
                ),
            ): selector.TimeSelector(),
            vol.Optional(
                CONF_NIGHT_PRICE_END_TIME,
                default=user_input.get(
                    CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT
                ),
            ): selector.TimeSelector(),
            # Legacy hour settings (for backward compatibility)
            vol.Optional(
                CONF_NIGHT_PRICE_START_HOUR,
                default=user_input.get(
                    CONF_NIGHT_PRICE_START_HOUR, NIGHT_PRICE_START_HOUR_DEFAULT
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")
            ),
            vol.Optional(
                CONF_NIGHT_PRICE_END_HOUR,
                default=user_input.get(
                    CONF_NIGHT_PRICE_END_HOUR, NIGHT_PRICE_END_HOUR_DEFAULT
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")
            ),
            # Update interval
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=300, max=86400, step=300, mode="box"
                )  # 5 min to 24 hours
            ),
            # Update triggers (new approach)
            vol.Optional(
                CONF_UPDATE_TRIGGER,
                default=user_input.get(CONF_UPDATE_TRIGGER, DEFAULT_UPDATE_TRIGGER),
            ): selector.ObjectSelector(),
            vol.Optional(
                CONF_CHEAP_PRICE_UPDATE_TRIGGER,
                default=user_input.get(CONF_CHEAP_PRICE_UPDATE_TRIGGER, DEFAULT_CHEAP_PRICE_UPDATE_TRIGGER),
            ): selector.TimeSelector(),
            # Cheap price analysis
            vol.Optional(
                CONF_CHEAP_PRICE_THRESHOLD,
                default=user_input.get(
                    CONF_CHEAP_PRICE_THRESHOLD, CHEAP_PRICE_THRESHOLD_DEFAULT
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.1, mode="box")
            ),
        })


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
            except InvalidUpdateTrigger:
                self._errors["update_trigger"] = "invalid_update_trigger"
            except InvalidCheapPriceTrigger:
                self._errors["cheap_price_update_trigger"] = "invalid_cheap_price_trigger"
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
        return vol.Schema({
            vol.Optional(
                CONF_NAME,
                default=options_data.get(
                    CONF_NAME, current_data.get(CONF_NAME, "Real Electricity Price")
                ),
            ): selector.TextSelector(),
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
                    CONF_VAT_NORD_POOL, current_data.get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT)
                ),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                default=options_data.get(
                    CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY, 
                    current_data.get(CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY, VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT)
                ),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                default=options_data.get(
                    CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE, 
                    current_data.get(CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE, VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT)
                ),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_GRID_TRANSMISSION_NIGHT,
                default=options_data.get(
                    CONF_VAT_GRID_TRANSMISSION_NIGHT, 
                    current_data.get(CONF_VAT_GRID_TRANSMISSION_NIGHT, VAT_GRID_TRANSMISSION_NIGHT_DEFAULT)
                ),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_GRID_TRANSMISSION_DAY,
                default=options_data.get(
                    CONF_VAT_GRID_TRANSMISSION_DAY, 
                    current_data.get(CONF_VAT_GRID_TRANSMISSION_DAY, VAT_GRID_TRANSMISSION_DAY_DEFAULT)
                ),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                default=options_data.get(
                    CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE, 
                    current_data.get(CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE, VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT)
                ),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_VAT_SUPPLIER_MARGIN,
                default=options_data.get(
                    CONF_VAT_SUPPLIER_MARGIN, 
                    current_data.get(CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT)
                ),
            ): selector.BooleanSelector(),
            # Time format preference
            vol.Optional(
                CONF_TIME_FORMAT_24H,
                default=options_data.get(
                    CONF_TIME_FORMAT_24H, current_data.get(CONF_TIME_FORMAT_24H, TIME_FORMAT_24H_DEFAULT)
                ),
            ): selector.BooleanSelector(),
            # Time settings - new natural format
            vol.Optional(
                CONF_NIGHT_PRICE_START_TIME,
                default=options_data.get(
                    CONF_NIGHT_PRICE_START_TIME,
                    current_data.get(CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT),
                ),
            ): selector.TimeSelector(),
            vol.Optional(
                CONF_NIGHT_PRICE_END_TIME,
                default=options_data.get(
                    CONF_NIGHT_PRICE_END_TIME,
                    current_data.get(CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT),
                ),
            ): selector.TimeSelector(),
            # Legacy hour settings (for backward compatibility)
            vol.Optional(
                CONF_NIGHT_PRICE_START_HOUR,
                default=options_data.get(
                    CONF_NIGHT_PRICE_START_HOUR,
                    current_data.get(
                        CONF_NIGHT_PRICE_START_HOUR, NIGHT_PRICE_START_HOUR_DEFAULT
                    ),
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")
            ),
            vol.Optional(
                CONF_NIGHT_PRICE_END_HOUR,
                default=options_data.get(
                    CONF_NIGHT_PRICE_END_HOUR,
                    current_data.get(
                        CONF_NIGHT_PRICE_END_HOUR, NIGHT_PRICE_END_HOUR_DEFAULT
                    ),
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")
            ),
            # Update interval
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=options_data.get(
                    CONF_SCAN_INTERVAL,
                    current_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=300, max=86400, step=300, mode="box"
                )  # 5 min to 24 hours
            ),
            # Update triggers (new approach)
            vol.Optional(
                CONF_UPDATE_TRIGGER,
                default=options_data.get(
                    CONF_UPDATE_TRIGGER,
                    current_data.get(CONF_UPDATE_TRIGGER, DEFAULT_UPDATE_TRIGGER),
                ),
            ): selector.ObjectSelector(),
            vol.Optional(
                CONF_CHEAP_PRICE_UPDATE_TRIGGER,
                default=options_data.get(
                    CONF_CHEAP_PRICE_UPDATE_TRIGGER,
                    current_data.get(CONF_CHEAP_PRICE_UPDATE_TRIGGER, DEFAULT_CHEAP_PRICE_UPDATE_TRIGGER),
                ),
            ): selector.TimeSelector(),
            # Cheap price analysis
            vol.Optional(
                CONF_CHEAP_PRICE_THRESHOLD,
                default=options_data.get(
                    CONF_CHEAP_PRICE_THRESHOLD,
                    current_data.get(CONF_CHEAP_PRICE_THRESHOLD, CHEAP_PRICE_THRESHOLD_DEFAULT),
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.1, mode="box")
            ),
        })


class CannotConnect(data_entry_flow.AbortFlow):
    """Error to indicate we cannot connect."""


class InvalidCountryCode(data_entry_flow.AbortFlow):
    """Error to indicate invalid country code."""


class InvalidVatRate(data_entry_flow.AbortFlow):
    """Error to indicate invalid VAT rate."""


class InvalidScanInterval(data_entry_flow.AbortFlow):
    """Error to indicate invalid scan interval."""
    
    def __init__(self):
        super().__init__("invalid_scan_interval")


class InvalidHourRange(data_entry_flow.AbortFlow):
    """Error to indicate invalid hour range."""
    
    def __init__(self):
        super().__init__("invalid_hour_range")


class InvalidNightHours(data_entry_flow.AbortFlow):
    """Error to indicate invalid night hour configuration."""
    
    def __init__(self):
        super().__init__("invalid_night_hours")


class InvalidUpdateTrigger(data_entry_flow.AbortFlow):
    """Error to indicate invalid update trigger configuration."""
    
    def __init__(self):
        super().__init__("invalid_update_trigger")


class InvalidCheapPriceTrigger(data_entry_flow.AbortFlow):
    """Error to indicate invalid cheap price update trigger configuration."""
    
    def __init__(self):
        super().__init__("invalid_cheap_price_trigger")


class InvalidTimeFormat(data_entry_flow.AbortFlow):
    """Error to indicate invalid time format."""
    
    def __init__(self):
        super().__init__("invalid_time_format")
