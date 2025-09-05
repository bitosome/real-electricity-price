"""Constants for real_electricity_price."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# Integration domain
DOMAIN = "real_electricity_price"
ATTRIBUTION = "Data provided by Real Electricity Price"

# API Configuration
DEFAULT_BASE_URL = "https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices"

# Default provider configurations
GRID_DEFAULT = "Elektrilevi"
SUPPLIER_DEFAULT = "Enefit"
COUNTRY_CODE_DEFAULT = "EE"

# Default pricing values (EUR/kWh)
GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT = 0.0026
GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT = 0.0104
GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT = 0.026
GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT = 0.0458
SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT = 0.00
SUPPLIER_MARGIN_DEFAULT = 0.0105

# Default tax and time settings
VAT_DEFAULT = 24.00  # percent

# Time format defaults (used across the integration)
NIGHT_PRICE_START_TIME_DEFAULT = "22:00"
NIGHT_PRICE_END_TIME_DEFAULT = "07:00"

# Update intervals
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds
# Scan interval bounds for UI/validation
SCAN_INTERVAL_MIN = 300
SCAN_INTERVAL_MAX = 86400
SCAN_INTERVAL_STEP = 300
DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER = "15:00"

# Analysis settings
CHEAP_HOURS_THRESHOLD_DEFAULT = 10.0  # percent above base price
CHEAP_HOURS_BASE_PRICE_DEFAULT = (
    0.150000  # EUR/kWh - base price for cheap hours calculation
)
PRICE_DECIMAL_PRECISION = 6  # Number of decimal places for all price calculations

# Configuration keys
## Basic configuration
CONF_GRID = "grid"
CONF_SUPPLIER = "supplier"
CONF_COUNTRY_CODE = "country_code"
CONF_VAT = "vat"

## Grid costs configuration
CONF_GRID_ELECTRICITY_EXCISE_DUTY = "grid_electricity_excise_duty"
CONF_GRID_RENEWABLE_ENERGY_CHARGE = "grid_renewable_energy_charge"
CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT = (
    "grid_electricity_transmission_price_night"
)
CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY = "grid_electricity_transmission_price_day"

## Supplier costs configuration
CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE = "supplier_renewable_energy_charge"
CONF_SUPPLIER_MARGIN = "supplier_margin"

## Time configuration
CONF_NIGHT_PRICE_START_HOUR = "night_price_start_hour"
CONF_NIGHT_PRICE_END_HOUR = "night_price_end_hour"
CONF_NIGHT_PRICE_START_TIME = "night_price_start_time"
CONF_NIGHT_PRICE_END_TIME = "night_price_end_time"

## Update configuration
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CHEAP_HOURS_UPDATE_TRIGGER = "cheap_hours_update_trigger"
CONF_CHEAP_HOURS_THRESHOLD = "cheap_hours_threshold"
CONF_CHEAP_HOURS_BASE_PRICE = "cheap_hours_base_price"

## API configuration
CONF_DATE = "date"
CONF_CURRENCY = "currency"
CONF_MARKET = "market"
CONF_TOKEN = "token"  # noqa: S105

# VAT configuration for individual components
CONF_VAT_NORD_POOL = "vat_nord_pool"
CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY = "vat_grid_electricity_excise_duty"
CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE = "vat_grid_renewable_energy_charge"
CONF_VAT_GRID_TRANSMISSION_NIGHT = "vat_grid_transmission_night"
CONF_VAT_GRID_TRANSMISSION_DAY = "vat_grid_transmission_day"
CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE = "vat_supplier_renewable_energy_charge"
CONF_VAT_SUPPLIER_MARGIN = "vat_supplier_margin"

# VAT defaults for each component
VAT_NORD_POOL_DEFAULT = True  # Nord Pool raw data always has VAT as specified
VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT = False
VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT = False
VAT_GRID_TRANSMISSION_NIGHT_DEFAULT = False
VAT_GRID_TRANSMISSION_DAY_DEFAULT = False
VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT = False
VAT_SUPPLIER_MARGIN_DEFAULT = False


def parse_time_string(time_str: str) -> tuple[int, int, int]:
    """
    Parse time string in HH:MM or HH:MM:SS format.

    Returns:
        tuple[int, int, int]: (hour, minute, second)

    """
    if not isinstance(time_str, str):
        msg = "Time string must be a string"
        raise ValueError(msg)

    parts = time_str.split(":")
    if len(parts) == 2:
        # HH:MM format
        hour, minute = map(int, parts)
        second = 0
    elif len(parts) == 3:
        # HH:MM:SS format
        hour, minute, second = map(int, parts)
    else:
        msg = "Time string must be in HH:MM or HH:MM:SS format"
        raise ValueError(msg)

    if not (0 <= hour <= 23):
        msg = "Hour must be between 0 and 23"
        raise ValueError(msg)
    if not (0 <= minute <= 59):
        msg = "Minute must be between 0 and 59"
        raise ValueError(msg)
    if not (0 <= second <= 59):
        msg = "Second must be between 0 and 59"
        raise ValueError(msg)

    return hour, minute, second


def time_string_to_hour(time_str: str) -> float:
    """
    Convert time string to hour as float.

    Args:
        time_str: Time string in HH:MM or HH:MM:SS format

    Returns:
        float: Hour as decimal (e.g., "14:30" -> 14.5)

    """
    hour, minute, second = parse_time_string(time_str)
    return hour + minute / 60.0 + second / 3600.0
