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
    CHEAP_HOURS_THRESHOLD_DEFAULT,
    CHEAP_HOURS_BASE_PRICE_DEFAULT,
    CONF_CHEAP_HOURS_THRESHOLD,
    CONF_CHEAP_HOURS_BASE_PRICE,
    CONF_CHEAP_HOURS_UPDATE_TRIGGER,
    CONF_COUNTRY_CODE,
    CONF_GRID,
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_NIGHT_PRICE_END_HOUR,
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_HOUR,
    CONF_NIGHT_PRICE_START_TIME,
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
    DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    GRID_DEFAULT,
    GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
    GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    NIGHT_PRICE_END_HOUR_DEFAULT,
    NIGHT_PRICE_START_HOUR_DEFAULT,
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

    # Validate scan interval (legacy support)
    scan_interval = data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    if not 300 <= scan_interval <= 86400:
        msg = "Scan interval must be between 5 minutes (300 seconds) and 24 hours (86400 seconds)"
        raise InvalidScanInterval(msg)

    cheap_hours_trigger = _convert_time_format(
        data.get(CONF_CHEAP_HOURS_UPDATE_TRIGGER, DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER)
    )
    if not _validate_time_string(cheap_hours_trigger):
        msg = "Cheap hours update time must be a valid time in HH:MM format"
        raise InvalidCheapPriceTrigger(msg)

    # Validate time settings - handle both new TimeSelector and legacy hour formats
    start_time_str = data.get(CONF_NIGHT_PRICE_START_TIME)
    end_time_str = data.get(CONF_NIGHT_PRICE_END_TIME)
    start_hour = data.get(CONF_NIGHT_PRICE_START_HOUR, NIGHT_PRICE_START_HOUR_DEFAULT)
    end_hour = data.get(CONF_NIGHT_PRICE_END_HOUR, NIGHT_PRICE_END_HOUR_DEFAULT)

    # If TimeSelector format is provided, validate it and extract hours
    if start_time_str:
        try:
            start_hour, _, _ = parse_time_string(start_time_str)
        except ValueError:
            msg = "Night price start time must be a valid time in HH:MM format"
            raise InvalidTimeFormat(msg)

    if end_time_str:
        try:
            end_hour, _, _ = parse_time_string(end_time_str)
        except ValueError:
            msg = "Night price end time must be a valid time in HH:MM format"
            raise InvalidTimeFormat(msg)

    # Validate hour ranges
    if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
        msg = "Night price hours must be between 00 and 23"
        raise InvalidHourRange(msg)

    # Validate time range logic - handle midnight crossover for night hours
    # Valid scenarios for night hours:
    # 1. Normal range: start < end (e.g., 20:00 to 06:00 within same day - but this would be invalid for night hours)
    # 2. Midnight crossover: start > end (e.g., 22:00 to 07:00 - night crosses midnight)
    # 3. Until midnight: end == 0 (e.g., 22:00 to 00:00)
    # Invalid: start == end (unless end == 0, but that's covered above)
    if start_hour == end_hour and end_hour != 0:
        msg = "Night price start and end times cannot be the same"
        raise InvalidNightHours(msg)

    # Test connection to Nord Pool API
    try:
        # This would normally test actual API connectivity
        # For now, we'll do basic validation
        return {"title": data.get(CONF_NAME, "Real Electricity Price")}
    except Exception as exc:
        _LOGGER.exception("Unexpected exception: %s", exc)
        raise CannotConnect from exc


def _convert_time_format(time_value):
    """Convert old string time format to new dict format for backward compatibility."""
    if isinstance(time_value, dict):
        return time_value
    if isinstance(time_value, str):
        # Convert "HH:MM" string to {"hour": H, "minute": M} dict
        try:
            parts = time_value.split(":")
            if len(parts) >= 2:
                return {"hour": int(parts[0]), "minute": int(parts[1])}
        except (ValueError, IndexError):
            pass
    # Return default if conversion fails
    return {"hour": 14, "minute": 30}


def _validate_time_string(time_str: str | dict) -> bool:
    """Validate time string in HH:MM format or time object from TimeSelector."""
    if isinstance(time_str, dict):
        # Handle TimeSelector output which might be a dict with hour/minute keys
        if "hour" in time_str and "minute" in time_str:
            hour = time_str["hour"]
            minute = time_str["minute"]
            return (
                isinstance(hour, int)
                and isinstance(minute, int)
                and 0 <= hour <= 23
                and 0 <= minute <= 59
            )
        return False

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
        _LOGGER.debug("async_step_user called with user_input: %s", user_input)
        self._errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidCheapPriceTrigger as e:
                self._errors["cheap_price_update_trigger"] = str(e)
            except InvalidCountryCode as e:
                self._errors["country_code"] = str(e)
            except InvalidVatRate as e:
                self._errors["vat"] = str(e)
            except InvalidScanInterval as e:
                self._errors["scan_interval"] = str(e)
            except InvalidHourRange as e:
                self._errors["base"] = str(e)
            except InvalidNightHours as e:
                self._errors["base"] = str(e)
            except InvalidTimeFormat as e:
                self._errors["base"] = str(e)
            except CannotConnect as e:
                self._errors["base"] = str(e)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                self._errors["base"] = "unknown"
            else:
                # Create unique ID based on name, grid, and supplier to allow multiple devices
                name = user_input.get(CONF_NAME, "Real Electricity Price")
                grid = user_input.get(CONF_GRID, GRID_DEFAULT)
                supplier = user_input.get(CONF_SUPPLIER, SUPPLIER_DEFAULT)
                country = user_input.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT)

                unique_id = f"real_electricity_price_{name}_{grid}_{supplier}_{country}".lower().replace(
                    " ", "_"
                )
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

        return vol.Schema(
            {
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
                # Time settings - new natural format
                vol.Optional(
                    CONF_NIGHT_PRICE_START_TIME,
                    default={"hour": NIGHT_PRICE_START_HOUR_DEFAULT, "minute": 0}
                    if CONF_NIGHT_PRICE_START_TIME not in user_input
                    else user_input.get(CONF_NIGHT_PRICE_START_TIME),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_NIGHT_PRICE_END_TIME,
                    default={"hour": NIGHT_PRICE_END_HOUR_DEFAULT, "minute": 0}
                    if CONF_NIGHT_PRICE_END_TIME not in user_input
                    else user_input.get(CONF_NIGHT_PRICE_END_TIME),
                ): selector.TimeSelector(),
                # Update interval
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=300, max=86400, step=300, mode="box"
                    )  # 5 min to 24 hours
                ),
                vol.Optional(
                    CONF_CHEAP_HOURS_UPDATE_TRIGGER,
                    default={"hour": 14, "minute": 30}
                    if CONF_CHEAP_HOURS_UPDATE_TRIGGER not in user_input
                    else user_input.get(CONF_CHEAP_HOURS_UPDATE_TRIGGER),
                ): selector.TimeSelector(),
                # Cheap price analysis
                vol.Optional(
                    CONF_CHEAP_HOURS_THRESHOLD,
                    default=user_input.get(
                        CONF_CHEAP_HOURS_THRESHOLD, CHEAP_HOURS_THRESHOLD_DEFAULT
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=0.1, mode="box")
                ),
                vol.Optional(
                    CONF_CHEAP_HOURS_BASE_PRICE,
                    default=user_input.get(
                        CONF_CHEAP_HOURS_BASE_PRICE, CHEAP_HOURS_BASE_PRICE_DEFAULT
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
            }
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
            except InvalidCheapPriceTrigger as e:
                self._errors["cheap_price_update_trigger"] = str(e)
            except InvalidCountryCode as e:
                self._errors["country_code"] = str(e)
            except InvalidVatRate as e:
                self._errors["vat"] = str(e)
            except InvalidScanInterval as e:
                self._errors["scan_interval"] = str(e)
            except InvalidHourRange as e:
                self._errors["base"] = str(e)
            except InvalidNightHours as e:
                self._errors["base"] = str(e)
            except InvalidTimeFormat as e:
                self._errors["base"] = str(e)
            except CannotConnect as e:
                self._errors["base"] = str(e)
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
        return vol.Schema(
            {
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
                # Time settings - new natural format
                vol.Optional(
                    CONF_NIGHT_PRICE_START_TIME,
                    default=options_data.get(
                        CONF_NIGHT_PRICE_START_TIME,
                        current_data.get(
                            CONF_NIGHT_PRICE_START_TIME,
                            {"hour": NIGHT_PRICE_START_HOUR_DEFAULT, "minute": 0},
                        ),
                    ),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_NIGHT_PRICE_END_TIME,
                    default=options_data.get(
                        CONF_NIGHT_PRICE_END_TIME,
                        current_data.get(
                            CONF_NIGHT_PRICE_END_TIME,
                            {"hour": NIGHT_PRICE_END_HOUR_DEFAULT, "minute": 0},
                        ),
                    ),
                ): selector.TimeSelector(),
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
                vol.Optional(
                    CONF_CHEAP_HOURS_UPDATE_TRIGGER,
                    default=options_data.get(
                        CONF_CHEAP_HOURS_UPDATE_TRIGGER,
                        current_data.get(
                            CONF_CHEAP_HOURS_UPDATE_TRIGGER, {"hour": 14, "minute": 30}
                        ),
                    ),
                ): selector.TimeSelector(),
                # Cheap price analysis
                vol.Optional(
                    CONF_CHEAP_HOURS_THRESHOLD,
                    default=options_data.get(
                        CONF_CHEAP_HOURS_THRESHOLD,
                        current_data.get(
                            CONF_CHEAP_HOURS_THRESHOLD, CHEAP_HOURS_THRESHOLD_DEFAULT
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=0.1, mode="box")
                ),
                vol.Optional(
                    CONF_CHEAP_HOURS_BASE_PRICE,
                    default=options_data.get(
                        CONF_CHEAP_HOURS_BASE_PRICE,
                        current_data.get(
                            CONF_CHEAP_HOURS_BASE_PRICE, CHEAP_HOURS_BASE_PRICE_DEFAULT
                        ),
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                ),
            }
        )


class CannotConnect(data_entry_flow.AbortFlow):
    """Error to indicate we cannot connect."""

    def __init__(self, message: str = "cannot_connect") -> None:
        super().__init__(message)


class InvalidCountryCode(data_entry_flow.AbortFlow):
    """Error to indicate invalid country code."""

    def __init__(
        self,
        message: str = "Country code must be one of: EE, FI, LV, LT, SE1, SE2, SE3, SE4, NO1, NO2, NO3, NO4, NO5, DK1, DK2",
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


class InvalidCheapPriceTrigger(data_entry_flow.AbortFlow):
    """Error to indicate invalid cheap price update trigger configuration."""

    def __init__(
        self,
        message: str = "Cheap price update time must be a valid time in HH:MM format",
    ) -> None:
        super().__init__(message)


class InvalidTimeFormat(data_entry_flow.AbortFlow):
    """Error to indicate invalid time format."""

    def __init__(
        self, message: str = "Time must be a valid time in HH:MM format"
    ) -> None:
        super().__init__(message)
