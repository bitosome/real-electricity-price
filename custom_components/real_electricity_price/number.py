"""Number entities for Real Electricity Price config options."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .config_entities import AcceptablePriceEntity
from .const import CONF_CALCULATE_CHEAP_HOURS

if TYPE_CHECKING:
    from .data import RealElectricityPriceConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RealElectricityPriceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities (acceptable price)."""
    cfg = {**entry.data, **entry.options}
    if not cfg.get(CONF_CALCULATE_CHEAP_HOURS, True):
        return
    entities = [
        AcceptablePriceEntity(entry.runtime_data.coordinator),
    ]
    async_add_entities(entities, update_before_add=True)
