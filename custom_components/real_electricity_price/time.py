"""Time entities for Real Electricity Price config options."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    _hass: HomeAssistant, entry: object, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up time entities - no time entities needed anymore."""
    # No time entities needed since we removed the cheap hours calculation time
    pass