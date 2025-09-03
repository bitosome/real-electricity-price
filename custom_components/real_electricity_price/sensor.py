"""Sensor platform for real_electricity_price."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity_descriptions import SENSOR_DESCRIPTIONS
from .sensors import (
    CheapPricesSensor,
    CurrentPriceSensor,
    CurrentTariffSensor,
    HourlyPricesSensor,
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
SENSOR_TYPE_HOURLY_PRICES = "hourly_prices"
SENSOR_TYPE_CHEAP_PRICES = "cheap_prices"

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
    "real_electricity_price_hourly_prices": (
        SENSOR_TYPE_HOURLY_PRICES,
        HourlyPricesSensor,
    ),
    "real_electricity_price_cheap_prices": (
        SENSOR_TYPE_CHEAP_PRICES,
        CheapPricesSensor,
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
    cheap_price_coordinator = entry.runtime_data.cheap_price_coordinator

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
            SENSOR_TYPE_CHEAP_PRICES,
            SENSOR_TYPE_LAST_CHEAP_CALCULATION,
        ):
            coord = cheap_price_coordinator  # Use separate coordinator for cheap prices
        else:
            coord = coordinator  # Use main coordinator for other sensors

        _LOGGER.debug(
            "Creating sensor entity: %s -> %s", entity_description.key, sensor_type
        )

        entities.append(sensor_class(coord, entity_description))

    _LOGGER.debug("Adding %s sensor entities to Home Assistant", len(entities))
    async_add_entities(entities)
