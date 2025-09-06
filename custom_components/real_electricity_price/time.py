"""Time entities for Real Electricity Price config options."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .config_entities import (
    CheapHoursUpdateTriggerEntity,
)
from .const import CONF_CALCULATE_CHEAP_HOURS


async def async_setup_entry(
    _hass: HomeAssistant, entry: object, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up time entities (update trigger)."""
    cfg = {**entry.data, **entry.options}
    if not cfg.get(CONF_CALCULATE_CHEAP_HOURS, True):
        return
    entities = [
        CheapHoursUpdateTriggerEntity(entry.runtime_data.coordinator),
    ]
    async_add_entities(entities, update_before_add=True)
