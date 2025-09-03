"""Entity descriptions for Real Electricity Price integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy

# Price sensors
SENSOR_CURRENT_PRICE = SensorEntityDescription(
    key="real_electricity_price",
    name="Current Price",
    icon="mdi:flash",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
    suggested_display_precision=6,
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
)

SENSOR_LAST_CHEAP_CALCULATION = SensorEntityDescription(
    key="real_electricity_price_last_cheap_calculation",
    name="Last Cheap Hours Calculation",
    icon="mdi:calculator-variant-outline",
    device_class=SensorDeviceClass.TIMESTAMP,
)

SENSOR_HOURLY_PRICES_YESTERDAY = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_yesterday",
    name="Hourly Prices Yesterday",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=6,
)

SENSOR_HOURLY_PRICES_TODAY = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_today",
    name="Hourly Prices Today",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=6,
)

SENSOR_HOURLY_PRICES_TOMORROW = SensorEntityDescription(
    key="real_electricity_price_hourly_prices_tomorrow",
    name="Hourly Prices Tomorrow",
    icon="mdi:chart-line",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement="€/kWh",
    suggested_display_precision=6,
)

SENSOR_CHEAP_PRICES = SensorEntityDescription(
    key="real_electricity_price_cheap_prices",
    name="Cheap hours",
    icon="mdi:clock-time-twelve",
    native_unit_of_measurement="h",
)

SENSOR_CHEAP_PRICE_END = SensorEntityDescription(
    key="real_electricity_price_cheap_price_end",
    name="Next Cheap Price End",
    icon="mdi:clock-end",
    device_class=SensorDeviceClass.TIMESTAMP,
)

SENSOR_CHEAP_PRICE_START = SensorEntityDescription(
    key="real_electricity_price_cheap_price_start",
    name="Next Cheap Price Start",
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
    SENSOR_CHEAP_PRICES,
    SENSOR_CHEAP_PRICE_END,
    SENSOR_CHEAP_PRICE_START,
)
