"""Time entities for Real Electricity Price config options."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .config_entities import (
    CheapHoursUpdateTriggerEntity,
)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    """Set up time entities (update trigger)."""
    entities = [
        CheapHoursUpdateTriggerEntity(entry.runtime_data.coordinator),
    ]
    async_add_entities(entities, update_before_add=True)
