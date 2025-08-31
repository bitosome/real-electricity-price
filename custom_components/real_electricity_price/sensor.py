"""Sensor platform for real_electricity_price."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .entity import RealElectricityPriceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RealElectricityPriceDataUpdateCoordinator
    from .data import RealElectricityPriceConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="real_electricity_prices_today",
        name="Real Electricity Prices Today",
        icon="mdi:currency-eur",
    ),
    SensorEntityDescription(
        key="real_electricity_prices_tomorrow",
        name="Real Electricity Prices Tomorrow",
        icon="mdi:currency-eur",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: RealElectricityPriceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        RealElectricityPriceSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class RealElectricityPriceSensor(RealElectricityPriceEntity, SensorEntity):
    """Real Electricity Price Sensor class."""

    def __init__(
        self,
        coordinator: RealElectricityPriceDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._data_key = "today" if "today" in entity_description.key else "tomorrow"

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data or self._data_key not in self.coordinator.data:
            return None

        day_data = self.coordinator.data[self._data_key]
        hourly_prices = day_data.get("hourly_prices", [])
        if not hourly_prices:
            return None

        # For today's sensor, return current hour's price
        # For tomorrow's sensor, return the first hour's price (next day's first hour)
        now = datetime.datetime.now(datetime.UTC)

        if self._data_key == "today":
            # Return the current hour's price
            for price in hourly_prices:
                start = datetime.datetime.fromisoformat(price["start_time"])
                end = datetime.datetime.fromisoformat(price["end_time"])
                if start <= now < end:
                    return price["actual_price"]
            return None
        # For tomorrow's sensor, return the first available price
        if hourly_prices:
            return hourly_prices[0]["actual_price"]
        return None @ property

    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._data_key not in self.coordinator.data:
            return {}

        day_data = self.coordinator.data[self._data_key]
        hourly_prices = day_data.get("hourly_prices", [])

        return {
            "hourly_prices": hourly_prices,
            "date": day_data.get("date", self._data_key),
        }
