"""Sensor platform for real_electricity_price."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .entity_descriptions import SENSOR_DESCRIPTIONS
from .sensors import (
    CheapHoursSensor,
    CurrentPriceSensor,
    CurrentTariffSensor,
    HourlyPricesTodaySensor,
    HourlyPricesTomorrowSensor,
    HourlyPricesYesterdaySensor,
    LastCheapCalculationSensor,
    LastSyncSensor,
    NextCheapHoursEndSensor,
    NextCheapHoursStartSensor,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)

# Sensor type constants
SENSOR_TYPE_CURRENT_PRICE = "current_price"
SENSOR_TYPE_CURRENT_TARIFF = "current_tariff"
SENSOR_TYPE_HOURLY_PRICES_TODAY = "hourly_prices_today"
SENSOR_TYPE_HOURLY_PRICES_TOMORROW = "hourly_prices_tomorrow"
SENSOR_TYPE_HOURLY_PRICES_YESTERDAY = "hourly_prices_yesterday"
SENSOR_TYPE_LAST_SYNC = "last_sync"
SENSOR_TYPE_LAST_CHEAP_CALCULATION = "last_cheap_calculation"
SENSOR_TYPE_CHEAP_HOURS = "cheap_hours"
SENSOR_TYPE_NEXT_CHEAP_HOURS_START = "next_cheap_hours_start"
SENSOR_TYPE_NEXT_CHEAP_HOURS_END = "next_cheap_hours_end"

# Sensor registry mapping sensor keys to their types and classes
SENSOR_REGISTRY = {
    "real_electricity_price_current_price": (
        SENSOR_TYPE_CURRENT_PRICE,
        CurrentPriceSensor,
    ),
    "real_electricity_price_current_tariff": (
        SENSOR_TYPE_CURRENT_TARIFF,
        CurrentTariffSensor,
    ),
    "real_electricity_price_hourly_prices_today": (
        SENSOR_TYPE_HOURLY_PRICES_TODAY,
        HourlyPricesTodaySensor,
    ),
    "real_electricity_price_hourly_prices_tomorrow": (
        SENSOR_TYPE_HOURLY_PRICES_TOMORROW,
        HourlyPricesTomorrowSensor,
    ),
    "real_electricity_price_hourly_prices_yesterday": (
        SENSOR_TYPE_HOURLY_PRICES_YESTERDAY,
        HourlyPricesYesterdaySensor,
    ),
    "real_electricity_price_last_sync": (
        SENSOR_TYPE_LAST_SYNC,
        LastSyncSensor,
    ),
    "real_electricity_price_last_cheap_calculation": (
        SENSOR_TYPE_LAST_CHEAP_CALCULATION,
        LastCheapCalculationSensor,
    ),
    "real_electricity_price_cheap_hours": (
        SENSOR_TYPE_CHEAP_HOURS,
        CheapHoursSensor,
    ),
    "real_electricity_price_next_cheap_hours_end": (
        SENSOR_TYPE_NEXT_CHEAP_HOURS_END,
        NextCheapHoursEndSensor,
    ),
    "real_electricity_price_next_cheap_hours_start": (
        SENSOR_TYPE_NEXT_CHEAP_HOURS_START,
        NextCheapHoursStartSensor,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RealElectricityPriceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug("Setting up sensor platform")

    entities = []

    # Add main coordinator sensors (excluding cheap hours sensors)
    cheap_hours_keys = {
        "real_electricity_price_cheap_hours",
        "real_electricity_price_next_cheap_hours_start",
        "real_electricity_price_next_cheap_hours_end",
        "real_electricity_price_last_cheap_calculation",
    }

    for description in SENSOR_DESCRIPTIONS:
        key = description.key
        # Skip cheap hours sensors - they'll be added separately with the cheap hours coordinator
        if key in cheap_hours_keys:
            continue

        if key in SENSOR_REGISTRY:
            sensor_type, sensor_class = SENSOR_REGISTRY[key]
            _LOGGER.debug("Creating sensor: %s (type: %s)", key, sensor_type)

            entities.append(
                sensor_class(
                    coordinator=entry.runtime_data.coordinator,
                    description=description,
                )
            )
        else:
            _LOGGER.warning("Unknown sensor key: %s", key)

    # Add cheap hours coordinator sensors
    cheap_hours_sensors = [
        "real_electricity_price_cheap_hours",
        "real_electricity_price_next_cheap_hours_start",
        "real_electricity_price_next_cheap_hours_end",
        "real_electricity_price_last_cheap_calculation",
    ]

    for key in cheap_hours_sensors:
        # Find the description with matching key
        description = None
        for desc in SENSOR_DESCRIPTIONS:
            if desc.key == key:
                description = desc
                break

        if description and key in SENSOR_REGISTRY:
            sensor_type, sensor_class = SENSOR_REGISTRY[key]
            _LOGGER.debug(
                "Creating cheap hours sensor: %s (type: %s)", key, sensor_type
            )

            entities.append(
                sensor_class(
                    coordinator=entry.runtime_data.cheap_hours_coordinator,
                    description=description,
                )
            )

    _LOGGER.debug("Adding %d sensor entities", len(entities))
    async_add_entities(entities, update_before_add=True)
