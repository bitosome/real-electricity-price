"""Button platform for real_electricity_price."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_NAME

from .entity import RealElectricityPriceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: RealElectricityPriceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    async_add_entities([
        RealElectricityPriceRefreshButton(
            coordinator=entry.runtime_data.coordinator,
        )
    ])


class RealElectricityPriceRefreshButton(RealElectricityPriceEntity, ButtonEntity):
    """Button to refresh electricity price data."""

    def __init__(self, coordinator: RealElectricityPriceDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        
        # Get device name from config (options override data)
        config = {**coordinator.config_entry.data, **coordinator.config_entry.options}
        device_name = config.get(CONF_NAME, "Real Electricity Price")
        
        self._attr_name = f"{device_name} Refresh Data"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_refresh_button"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Refresh button pressed, requesting data update")
        # Force a refresh of the coordinator data
        await self.coordinator.async_request_refresh()
