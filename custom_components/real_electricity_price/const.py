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

# Analysis settings
ACCEPTABLE_PRICE_DEFAULT = 0.150000  # EUR/kWh - maximum acceptable price for cheap hours
PRICE_DECIMAL_PRECISION = 6  # Number of decimal places for all price calculations

# Feature toggles
CALCULATE_CHEAP_HOURS_DEFAULT = True

# Chart color defaults
CHART_COLOR_PAST_HOURS_DEFAULT = "#808080"  # Grey
CHART_COLOR_CURRENT_HOUR_DEFAULT = "#FF6B6B"  # Red
CHART_COLOR_FUTURE_HOURS_DEFAULT = "#4A90E2"  # Blue
CHART_COLOR_CHEAP_HOURS_DEFAULT = "#9B59B6"  # Purple
CHART_COLOR_CHEAP_CURRENT_HOUR_DEFAULT = "#FF8C00"  # Orange

# Tariff state constants
TARIFF_OFF_PEAK = "off_peak"
TARIFF_PEAK = "peak"
TARIFF_FIXED = "fixed"

# Off-peak calculation strategy
CONF_OFFPEAK_STRATEGY = "offpeak_strategy"
OFFPEAK_STRATEGY_NIGHT_WINDOW = "night_window"
OFFPEAK_STRATEGY_NP_BLOCKS = "nord_pool_blocks"
OFFPEAK_STRATEGY_DEFAULT = OFFPEAK_STRATEGY_NIGHT_WINDOW

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

# Extended grid transmission price configuration (for block-aligned tariffs)
CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK1 = (
    "grid_electricity_transmission_price_offpeak1"
)
CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_PEAK = (
    "grid_electricity_transmission_price_peak"
)
CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_OFFPEAK2 = (
    "grid_electricity_transmission_price_offpeak2"
)

## Supplier costs configuration
CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE = "supplier_renewable_energy_charge"
CONF_SUPPLIER_MARGIN = "supplier_margin"

## Time configuration
CONF_HAS_NIGHT_TARIFF = "has_night_tariff"
CONF_NIGHT_PRICE_START_TIME = "night_price_start_time"
CONF_NIGHT_PRICE_END_TIME = "night_price_end_time"
CONF_NIGHT_TARIFF_SATURDAY = "night_tariff_saturday"
CONF_NIGHT_TARIFF_SUNDAY = "night_tariff_sunday"
CONF_NIGHT_TARIFF_PUBLIC_HOLIDAY = "night_tariff_public_holiday"

## Update configuration
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ACCEPTABLE_PRICE = "acceptable_price"
CONF_CALCULATE_CHEAP_HOURS = "calculate_cheap_hours"

## Chart color configuration
CONF_CHART_COLOR_PAST_HOURS = "chart_color_past_hours"
CONF_CHART_COLOR_CURRENT_HOUR = "chart_color_current_hour"
CONF_CHART_COLOR_FUTURE_HOURS = "chart_color_future_hours"
CONF_CHART_COLOR_CHEAP_HOURS = "chart_color_cheap_hours"
CONF_CHART_COLOR_CHEAP_CURRENT_HOUR = "chart_color_cheap_current_hour"

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

# Tariff configuration
HAS_NIGHT_TARIFF_DEFAULT = True  # Most suppliers have night/day tariffs
NIGHT_TARIFF_SATURDAY_DEFAULT = True
NIGHT_TARIFF_SUNDAY_DEFAULT = True
NIGHT_TARIFF_PUBLIC_HOLIDAY_DEFAULT = True

# Regional holiday code for subdivision-specific holidays (e.g., US state codes like CA, NY, DE or Canadian provinces like ON, BC)
CONF_REGIONAL_HOLIDAY_CODE = "regional_holiday_code"
REGIONAL_HOLIDAY_CODE_DEFAULT = ""


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
