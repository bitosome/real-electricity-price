"""Entity descriptions for Real ElSENSOR_LAST_CHEAP_CALCULATION = SensorEntityDescription(
    key="real_electricity_price_last_cheap_calculation",tricity Price integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy
from .const import PRICE_DECIMAL_PRECISION
from homeassistant.helpers.entity import EntityCategory

# Price sensors
SENSOR_CURRENT_PRICE = SensorEntityDescription(
    key="real_electricity_price_current_price",
    name="Current Price",
    icon="mdi:currency-eur",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
    suggested_display_precision=PRICE_DECIMAL_PRECISION,
)

SENSOR_CURRENT_TARIFF = SensorEntityDescription(
    key="real_electricity_price_current_tariff",
    name="Current Tariff",
    icon="mdi:timeline-clock",
)

SENSOR_LAST_SYNC = SensorEntityDescription(
    key="real_electricity_price_last_sync",
    name="Last Sync",
    icon="mdi:cloud-refresh-outline",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
)

SENSOR_LAST_CHEAP_CALCULATION = SensorEntityDescription(
    key="real_electricity_price_last_cheap_calculation",
    name="Last Cheap Hours Calculation",
    icon="mdi:calculator-variant-outline",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
)

SENSOR_HOURLY_PRICES_YESTERDAY = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_yesterday",
    name="Hourly Prices Yesterday",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=PRICE_DECIMAL_PRECISION,
)

SENSOR_HOURLY_PRICES_TODAY = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_today",
    name="Hourly Prices Today",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=PRICE_DECIMAL_PRECISION,
)

SENSOR_HOURLY_PRICES_TOMORROW = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_tomorrow",
    name="Hourly Prices Tomorrow",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=PRICE_DECIMAL_PRECISION,
)

SENSOR_CHEAP_HOURS = SensorEntityDescription(
    key="real_electricity_price_cheap_hours",
    name="Cheap Hours",
    icon="mdi:timelapse",
    native_unit_of_measurement="h",
    state_class=SensorStateClass.MEASUREMENT,
)

SENSOR_NEXT_CHEAP_HOURS_END = SensorEntityDescription(
    key="real_electricity_price_next_cheap_hours_end",
    name="Next Cheap Hours End",
    icon="mdi:clock-end",
    device_class=SensorDeviceClass.TIMESTAMP,
)

SENSOR_NEXT_CHEAP_HOURS_START = SensorEntityDescription(
    key="real_electricity_price_next_cheap_hours_start",
    name="Next Cheap Hours Start",
    icon="mdi:clock-start",
    device_class=SensorDeviceClass.TIMESTAMP,
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
)
