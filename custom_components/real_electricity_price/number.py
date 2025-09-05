"""Number entities for Real Electricity Price config options."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .config_entities import (
    CheapHoursBasePriceEntity,
    CheapHoursThresholdEntity,
)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up number entities (base price, threshold)."""
    entities = [
        CheapHoursBasePriceEntity(entry.runtime_data.coordinator),
        CheapHoursThresholdEntity(entry.runtime_data.coordinator),
    ]
    async_add_entities(entities, update_before_add=True)
