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

    from .cheap_price_coordinator import CheapPriceDataUpdateCoordinator
    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: RealElectricityPriceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    async_add_entities(
        [
            RealElectricityPriceRefreshButton(
                coordinator=entry.runtime_data.coordinator,
            ),
            RealElectricityPriceCalculateCheapHoursButton(
                coordinator=entry.runtime_data.coordinator,
                cheap_coordinator=entry.runtime_data.cheap_price_coordinator,
            ),
        ]
    )


class RealElectricityPriceRefreshButton(RealElectricityPriceEntity, ButtonEntity):
    """Button to refresh electricity price data."""

    def __init__(self, coordinator: RealElectricityPriceDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)

        # Get device name from config (options override data)
        config = {**coordinator.config_entry.data, **coordinator.config_entry.options}
        device_name = config.get(CONF_NAME, "Real Electricity Price")

        self._attr_name = f"{device_name} Sync data"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_refresh_button"
        self._attr_icon = "mdi:cloud-refresh-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Refresh button pressed, requesting data update")
        # Force a refresh of the coordinator data
        await self.coordinator.async_request_refresh()


class RealElectricityPriceCalculateCheapHoursButton(
    RealElectricityPriceEntity, ButtonEntity
):
    """Button to manually calculate cheap hours."""

    def __init__(
        self,
        coordinator: RealElectricityPriceDataUpdateCoordinator,
        cheap_coordinator: CheapPriceDataUpdateCoordinator,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)

        # Get device name from config (options override data)
        config = {**coordinator.config_entry.data, **coordinator.config_entry.options}
        device_name = config.get(CONF_NAME, "Real Electricity Price")

        self.cheap_coordinator = cheap_coordinator
        self._attr_name = f"{device_name} Calculate Cheap Hours"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_calculate_cheap_hours_button"
        )
        self._attr_icon = "mdi:calculator-variant-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Calculate cheap hours button pressed, triggering manual update")
        # Trigger manual update of cheap price data
        await self.cheap_coordinator.async_manual_update()
