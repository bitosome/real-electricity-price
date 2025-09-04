"""RealElectricityPriceEntity class."""

from __future__ import annotations

from homeassistant.const import CONF_NAME
from awesomeversion import AwesomeVersion
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

    def __init__(self, coordinator: RealElectricityPriceDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id

        # Register a single service-like device per config entry so entities
        # are grouped under the integration device in the UI.
        config = {**coordinator.config_entry.data, **coordinator.config_entry.options}
        device_name = config.get(CONF_NAME, "Real Electricity Price")

        version = getattr(
            coordinator.config_entry.runtime_data.integration, "version", None
        )
        model_name = (
            f"Real Electricity Price {version}" if isinstance(version, str) else "Real Electricity Price"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=device_name,
            manufacturer="bitosome",
            model=model_name,
            sw_version=None,
            entry_type=DeviceEntryType.SERVICE,
        )
