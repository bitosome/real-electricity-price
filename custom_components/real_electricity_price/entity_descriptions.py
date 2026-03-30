"""
Entity descriptions for Real Electricity Price integration.
"""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy
from homeassistant.helpers.entity import EntityCategory

from .const import PRICE_DECIMAL_PRECISION

# Price sensors
SENSOR_CURRENT_PRICE = SensorEntityDescription(
    key="real_electricity_price_current_price",
    translation_key="current_price",
    icon="mdi:currency-eur",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
    suggested_display_precision=PRICE_DECIMAL_PRECISION,
)

SENSOR_CURRENT_TARIFF = SensorEntityDescription(
    key="real_electricity_price_current_tariff",
    translation_key="current_tariff",
    icon="mdi:timeline-clock",
)

SENSOR_LAST_SYNC = SensorEntityDescription(
    key="real_electricity_price_last_sync",
    translation_key="last_sync",
    icon="mdi:cloud-refresh-outline",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
)

SENSOR_LAST_CHEAP_CALCULATION = SensorEntityDescription(
    key="real_electricity_price_last_cheap_calculation",
    translation_key="last_cheap_calculation",
    icon="mdi:calculator-variant-outline",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
)

SENSOR_HOURLY_PRICES_YESTERDAY = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_yesterday",
    translation_key="hourly_prices_yesterday",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=PRICE_DECIMAL_PRECISION,
)

SENSOR_HOURLY_PRICES_TODAY = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_today",
    translation_key="hourly_prices_today",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=PRICE_DECIMAL_PRECISION,
)

SENSOR_HOURLY_PRICES_TOMORROW = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_tomorrow",
    translation_key="hourly_prices_tomorrow",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=PRICE_DECIMAL_PRECISION,
)

SENSOR_CHEAP_HOURS = SensorEntityDescription(
    key="real_electricity_price_cheap_hours",
    translation_key="cheap_hours",
    icon="mdi:timelapse",
    native_unit_of_measurement="h",
    state_class=SensorStateClass.MEASUREMENT,
)

SENSOR_NEXT_CHEAP_HOURS_END = SensorEntityDescription(
    key="real_electricity_price_next_cheap_hours_end",
    translation_key="next_cheap_hours_end",
    icon="mdi:clock-end",
    device_class=SensorDeviceClass.TIMESTAMP,
)

SENSOR_NEXT_CHEAP_HOURS_START = SensorEntityDescription(
    key="real_electricity_price_next_cheap_hours_start",
    translation_key="next_cheap_hours_start",
    icon="mdi:clock-start",
    device_class=SensorDeviceClass.TIMESTAMP,
)

SENSOR_CHART_DATA = SensorEntityDescription(
    key="real_electricity_price_chart_data",
    translation_key="chart_data",
    icon="mdi:chart-bar",
    entity_category=EntityCategory.DIAGNOSTIC,
)

# All sensor entity descriptions
SENSOR_DESCRIPTIONS = (
    SENSOR_CURRENT_PRICE,
    SENSOR_CURRENT_TARIFF,
    SENSOR_LAST_SYNC,
    SENSOR_LAST_CHEAP_CALCULATION,
    SENSOR_HOURLY_PRICES_YESTERDAY,
    SENSOR_HOURLY_PRICES_TODAY,
    SENSOR_HOURLY_PRICES_TOMORROW,
    SENSOR_CHEAP_HOURS,
    SENSOR_NEXT_CHEAP_HOURS_END,
    SENSOR_NEXT_CHEAP_HOURS_START,
    SENSOR_CHART_DATA,
)
