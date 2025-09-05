"""Setup config entities for Real Electricity Price integration."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .config_entities import (
    CheapHoursBasePriceEntity,
    CheapHoursThresholdEntity,
    CheapHoursUpdateTriggerEntity,
)


async def async_setup_config_entities(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up config entities (base price, threshold, update trigger)."""
    entities = [
        CheapHoursBasePriceEntity(entry.runtime_data.coordinator),
        CheapHoursThresholdEntity(entry.runtime_data.coordinator),
        CheapHoursUpdateTriggerEntity(entry.runtime_data.coordinator),
    ]
    async_add_entities(entities, update_before_add=True)
