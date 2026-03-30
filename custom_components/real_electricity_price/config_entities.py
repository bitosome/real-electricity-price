"""Number and time entities for Real Electricity Price config options."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity

from .const import (
    ACCEPTABLE_PRICE_DEFAULT,
    PRICE_DECIMAL_PRECISION,
)
from .entity import RealElectricityPriceEntity

_LOGGER = logging.getLogger(__name__)


class AcceptablePriceEntity(RealElectricityPriceEntity, NumberEntity):
    """Entity for acceptable price."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = "acceptable_price"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_acceptable_price"
        )
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "€/kWh"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 1
        try:
            self._attr_native_step = 10 ** (-PRICE_DECIMAL_PRECISION)
        except Exception:
            self._attr_native_step = 0.000001
        self._attr_mode = "box"
        cheap_coordinator = coordinator.get_cheap_price_coordinator()
        self._attr_native_value = (
            cheap_coordinator.get_runtime_acceptable_price()
            if cheap_coordinator is not None
            else ACCEPTABLE_PRICE_DEFAULT
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        if not isinstance(value, (int, float)) or value < 0 or value > 1:
            _LOGGER.error("Invalid acceptable price value: %s", value)
            return

        try:
            # Update the coordinator's runtime value without triggering config reload
            cheap_coordinator = self.coordinator.get_cheap_price_coordinator()
            if cheap_coordinator is None:
                _LOGGER.error("Cheap hours coordinator unavailable; cannot update acceptable price")
                return

            cheap_coordinator.set_runtime_acceptable_price(value)
            self._attr_native_value = value
            self.async_write_ha_state()
            _LOGGER.info(
                "Acceptable price updated to %s - use Calculate Cheap Hours button to recalculate",
                value,
            )
        except Exception as e:
            _LOGGER.exception("Error setting acceptable price: %s", e)
