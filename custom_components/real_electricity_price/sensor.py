"""Sensor platform for real_electricity_price."""

from __future_    "real_electricity_price_cheap_hours": (
        SENSOR_TYPE_CHEAP_HOURS,
        CheapHoursSensor,
    ),
    "real_electricity_price_cheap_hours_end": (
        SENSOR_TYPE_CHEAP_HOURS_END,
        CheapHoursEndSensor,
    ),
    "real_electricity_price_cheap_hours_start": (
        SENSOR_TYPE_CHEAP_HOURS_START,
        CheapHoursStartSensor,
    ),otations

import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity_descriptions import SENSOR_DESCRIPTIONS
from .sensors import (
    CheapHoursSensor,
    CheapHoursEndSensor,
    CheapHoursStartSensor,
    CurrentPriceSensor,
    CurrentTariffSensor,
    HourlyPricesYesterdaySensor,
    HourlyPricesTodaySensor,
    HourlyPricesTomorrowSensor,
    LastCheapCalculationSensor,
    LastSyncSensor,
)

if TYPE_CHECKING:
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)

# Sensor type constants
SENSOR_TYPE_CURRENT_PRICE = "current_price"
SENSOR_TYPE_CURRENT_TARIFF = "current_tariff"
SENSOR_TYPE_LAST_SYNC = "last_sync"
SENSOR_TYPE_LAST_CHEAP_CALCULATION = "last_cheap_calculation"
SENSOR_TYPE_HOURLY_PRICES_YESTERDAY = "hourly_prices_yesterday"
SENSOR_TYPE_HOURLY_PRICES_TODAY = "hourly_prices_today"
SENSOR_TYPE_HOURLY_PRICES_TOMORROW = "hourly_prices_tomorrow"
SENSOR_TYPE_CHEAP_HOURS = "cheap_hours"
SENSOR_TYPE_CHEAP_HOURS_END = "cheap_hours_end"
SENSOR_TYPE_CHEAP_HOURS_START = "cheap_hours_start"

# Mapping of entity descriptions to sensor types and classes
SENSOR_MAPPING = {
    "real_electricity_price": (SENSOR_TYPE_CURRENT_PRICE, CurrentPriceSensor),
    "real_electricity_price_current_tariff": (
        SENSOR_TYPE_CURRENT_TARIFF,
        CurrentTariffSensor,
    ),
    "real_electricity_price_last_sync": (SENSOR_TYPE_LAST_SYNC, LastSyncSensor),
    "real_electricity_price_last_cheap_calculation": (
        SENSOR_TYPE_LAST_CHEAP_CALCULATION,
        LastCheapCalculationSensor,
    ),
    "real_electricity_price_hourly_prices_yesterday": (
        SENSOR_TYPE_HOURLY_PRICES_YESTERDAY,
        HourlyPricesYesterdaySensor,
    ),
    "real_electricity_price_hourly_prices_today": (
        SENSOR_TYPE_HOURLY_PRICES_TODAY,
        HourlyPricesTodaySensor,
    ),
    "real_electricity_price_hourly_prices_tomorrow": (
        SENSOR_TYPE_HOURLY_PRICES_TOMORROW,
        HourlyPricesTomorrowSensor,
    ),
    "real_electricity_price_cheap_prices": (
        SENSOR_TYPE_CHEAP_PRICES,
        CheapHoursSensor,
    ),
    "real_electricity_price_cheap_price_end": (
        SENSOR_TYPE_CHEAP_PRICE_END,
        CheapHoursEndSensor,
    ),
    "real_electricity_price_cheap_price_start": (
        SENSOR_TYPE_CHEAP_PRICE_START,
        CheapHoursStartSensor,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RealElectricityPriceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug("Setting up sensor platform for entry: %s", entry.entry_id)

    coordinator = entry.runtime_data.coordinator
    cheap_hours_coordinator = entry.runtime_data.cheap_hours_coordinator

    entities = []

    for entity_description in SENSOR_DESCRIPTIONS:
        _LOGGER.debug("Processing entity description: %s", entity_description.key)

        if entity_description.key not in SENSOR_MAPPING:
            _LOGGER.warning(
                "Unknown entity description key: %s", entity_description.key
            )
            continue

        sensor_type, sensor_class = SENSOR_MAPPING[entity_description.key]

        # Determine which coordinator to use
        if sensor_type in (
            SENSOR_TYPE_CHEAP_HOURS,
            SENSOR_TYPE_CHEAP_HOURS_END,
            SENSOR_TYPE_CHEAP_HOURS_START,
            SENSOR_TYPE_LAST_CHEAP_CALCULATION,
        ):
            coord = cheap_hours_coordinator  # Use separate coordinator for cheap hours
        else:
            coord = coordinator  # Use main coordinator for other sensors

        _LOGGER.debug(
            "Creating sensor entity: %s -> %s", entity_description.key, sensor_type
        )

        entities.append(sensor_class(coord, entity_description))

    _LOGGER.debug("Adding %s sensor entities to Home Assistant", len(entities))
    async_add_entities(entities)
