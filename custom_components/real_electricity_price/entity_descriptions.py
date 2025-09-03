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
    suggested_display_precision=4,
)

SENSOR_CURRENT_TARIFF = SensorEntityDescription(
    key="real_electricity_price_current_tariff",
    name="Current Tariff",
    icon="mdi:timeline-clock",
)

SENSOR_LAST_SYNC = SensorEntityDescription(
    key="real_electricity_price_last_sync",
    name="Last Sync",
    icon="mdi:cloud-sync",
    device_class=SensorDeviceClass.TIMESTAMP,
)

SENSOR_LAST_CHEAP_CALCULATION = SensorEntityDescription(
    key="real_electricity_price_last_cheap_calculation",
    name="Last Cheap Price Calculation",
    icon="mdi:calculator-variant",
    device_class=SensorDeviceClass.TIMESTAMP,
)

SENSOR_HOURLY_PRICES = SensorEntityDescription(
    key="real_electricity_price_hourly_prices",
    name="Hourly Prices",
    icon="mdi:chart-line-variant",
    device_class=SensorDeviceClass.MONETARY,
    native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
)

SENSOR_CHEAP_PRICES = SensorEntityDescription(
    key="real_electricity_price_cheap_prices",
    name="Cheap Prices",
    icon="mdi:currency-eur-off",
    device_class=SensorDeviceClass.TIMESTAMP,
)

SENSOR_CHEAP_PRICE_END = SensorEntityDescription(
    key="real_electricity_price_cheap_price_end",
    name="Cheap Price End",
    icon="mdi:clock-time-twelve",
    device_class=SensorDeviceClass.TIMESTAMP,
)

# All sensor entity descriptions
SENSOR_DESCRIPTIONS = (
    SENSOR_CURRENT_PRICE,
    SENSOR_CURRENT_TARIFF,
    SENSOR_LAST_SYNC,
    SENSOR_LAST_CHEAP_CALCULATION,
    SENSOR_HOURLY_PRICES,
    SENSOR_CHEAP_PRICES,
    SENSOR_CHEAP_PRICE_END,
)
