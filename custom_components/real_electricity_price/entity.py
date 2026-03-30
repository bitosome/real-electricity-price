"""RealElectricityPriceEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import RealElectricityPriceDataUpdateCoordinator


class RealElectricityPriceEntity(
    CoordinatorEntity[RealElectricityPriceDataUpdateCoordinator]
):
    """Base entity class for the integration."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: RealElectricityPriceDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id

        version = getattr(
            coordinator.config_entry.runtime_data.integration, "version", None
        )
        model_name = (
            f"Real Electricity Price {version}"
            if isinstance(version, str)
            else "Real Electricity Price"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title or "Real Electricity Price",
            manufacturer="bitosome",
            model=model_name,
            sw_version=None,
            entry_type=DeviceEntryType.SERVICE,
        )
