"""Constants for real_electricity_price."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "real_electricity_price"
ATTRIBUTION = "Data provided by Real Electricity Price"

# Nord Pool API
DEFAULT_BASE_URL = "https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices"

# Default values from the example script
GRID_DEFAULT = "elektrilevi"
SUPPLIER_DEFAULT = "eesti_energia"
GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT = 0.0026  # EUR/kWh
GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT = 0.0104  # EUR/kWh
GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT = 0.026  # EUR/kWh
GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT = 0.0458  # EUR/kWh
SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT = 0.00  # EUR/kWh
SUPPLIER_MARGIN_DEFAULT = 0.0105  # EUR/kWh
# Nord Pool area code (used for API calls) - can include area numbers like EE, FI, SE1, SE2, NO1, NO2, etc.
COUNTRY_CODE_DEFAULT = "EE"
VAT_DEFAULT = 24.00  # percent
NIGHT_PRICE_START_HOUR_DEFAULT = 22  # Hour when night price starts (22:00)
NIGHT_PRICE_END_HOUR_DEFAULT = 7  # Hour when night price ends (07:00)

# Config keys matching the script variables
CONF_GRID = "grid"
CONF_SUPPLIER = "supplier"
CONF_GRID_ELECTRICITY_EXCISE_DUTY = "grid_electricity_excise_duty"
CONF_GRID_RENEWABLE_ENERGY_CHARGE = "grid_renewable_energy_charge"
CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT = (
    "grid_electricity_transmission_price_night"
)
CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY = "grid_electricity_transmission_price_day"
CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE = "supplier_renewable_energy_charge"
CONF_SUPPLIER_MARGIN = "supplier_margin"
CONF_COUNTRY_CODE = "country_code"
CONF_VAT = "vat"
CONF_NIGHT_PRICE_START_HOUR = "night_price_start_hour"
CONF_NIGHT_PRICE_END_HOUR = "night_price_end_hour"
CONF_DATE = "date"
CONF_CURRENCY = "currency"
CONF_MARKET = "market"
CONF_TOKEN = "token"  # noqa: S105

# Individual VAT configuration for each price component
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

# Decimal precision for price calculations
PRICE_DECIMAL_PRECISION = 6  # Number of decimal places for all price calculations

# Cheap price analysis
CONF_CHEAP_PRICE_THRESHOLD = "cheap_price_threshold"
CHEAP_PRICE_THRESHOLD_DEFAULT = 10.0  # percent above minimum price

# Update triggers - when to recalculate prices
CONF_UPDATE_TRIGGER = "update_trigger"
CONF_CHEAP_PRICE_UPDATE_TRIGGER = "cheap_price_update_trigger"
DEFAULT_UPDATE_TRIGGER = "14:00"  # Default time for main data update
DEFAULT_CHEAP_PRICE_UPDATE_TRIGGER = "14:30"  # Default time for cheap price calculation

# Time configuration
CONF_NIGHT_PRICE_START_TIME = "night_price_start_time"
CONF_NIGHT_PRICE_END_TIME = "night_price_end_time"
CONF_TIME_FORMAT_24H = "time_format_24h"

# Time defaults
NIGHT_PRICE_START_TIME_DEFAULT = "22:00"  # Night price start time in HH:MM format
NIGHT_PRICE_END_TIME_DEFAULT = "07:00"    # Night price end time in HH:MM format  
TIME_FORMAT_24H_DEFAULT = True            # Use 24-hour time format by default

# Scan interval
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds
CONF_SCAN_INTERVAL = "scan_interval"


def parse_time_string(time_str: str) -> tuple[int, int, int]:
    """Parse time string in HH:MM or HH:MM:SS format.
    
    Returns:
        tuple[int, int, int]: (hour, minute, second)
    """
    if not isinstance(time_str, str):
        raise ValueError("Time string must be a string")
    
    parts = time_str.split(":")
    if len(parts) == 2:
        # HH:MM format
        hour, minute = map(int, parts)
        second = 0
    elif len(parts) == 3:
        # HH:MM:SS format
        hour, minute, second = map(int, parts)
    else:
        raise ValueError("Time string must be in HH:MM or HH:MM:SS format")
    
    if not (0 <= hour <= 23):
        raise ValueError("Hour must be between 0 and 23")
    if not (0 <= minute <= 59):
        raise ValueError("Minute must be between 0 and 59")
    if not (0 <= second <= 59):
        raise ValueError("Second must be between 0 and 59")
    
    return hour, minute, second


def time_string_to_hour(time_str: str) -> float:
    """Convert time string to hour as float.
    
    Args:
        time_str: Time string in HH:MM or HH:MM:SS format
        
    Returns:
        float: Hour as decimal (e.g., "14:30" -> 14.5)
    """
    hour, minute, second = parse_time_string(time_str)
    return hour + minute / 60.0 + second / 3600.0
