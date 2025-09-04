"""Base sensor class for Real Electricity Price integration."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import CONF_NAME

from ..const import PRICE_DECIMAL_PRECISION, CHEAP_HOURS_BASE_PRICE_DEFAULT
from ..entity import RealElectricityPriceEntity
from ..models import IntegrationConfig


class RealElectricityPriceBaseSensor(RealElectricityPriceEntity, SensorEntity):
    """Base sensor class for the integration."""

    def __init__(
        self,
        coordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        # Set unique ID and name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

        # Get device name from config
        config = {**coordinator.config_entry.data, **coordinator.config_entry.options}
        device_name = config.get(CONF_NAME, "Real Electricity Price")
        self._attr_name = f"{device_name} {description.name}"

    @abstractmethod
    def native_value(self) -> Any:
        """Return the native value of the sensor."""

    def get_config(self) -> IntegrationConfig:
        """Get configuration as a structured object."""
        config_data = {
            **self.coordinator.config_entry.data,
            **self.coordinator.config_entry.options,
        }

        return IntegrationConfig(
            name=config_data.get(CONF_NAME, "Real Electricity Price"),
            grid=config_data.get("grid", "elektrilevi"),
            supplier=config_data.get("supplier", "eesti_energia"),
            country_code=config_data.get("country_code", "EE"),
            vat_rate=config_data.get("vat", 24.0),
            grid_electricity_excise_duty=config_data.get(
                "grid_electricity_excise_duty", 0.0026
            ),
            grid_renewable_energy_charge=config_data.get(
                "grid_renewable_energy_charge", 0.0104
            ),
            grid_transmission_price_night=config_data.get(
                "grid_electricity_transmission_price_night", 0.026
            ),
            grid_transmission_price_day=config_data.get(
                "grid_electricity_transmission_price_day", 0.0458
            ),
            supplier_renewable_energy_charge=config_data.get(
                "supplier_renewable_energy_charge", 0.0
            ),
            supplier_margin=config_data.get("supplier_margin", 0.0105),
            night_price_start_time=config_data.get("night_price_start_time", "22:00"),
            night_price_end_time=config_data.get("night_price_end_time", "07:00"),
            scan_interval=config_data.get("scan_interval", 3600),
            cheap_price_update_trigger=config_data.get(
                "cheap_price_update_trigger", "14:30"
            ),
            cheap_price_threshold=config_data.get("cheap_price_threshold", 10.0),
            cheap_hours_base_price=config_data.get("cheap_hours_base_price", CHEAP_HOURS_BASE_PRICE_DEFAULT),
            vat_nord_pool=config_data.get("vat_nord_pool", True),
            vat_grid_electricity_excise_duty=config_data.get(
                "vat_grid_electricity_excise_duty", False
            ),
            vat_grid_renewable_energy_charge=config_data.get(
                "vat_grid_renewable_energy_charge", False
            ),
            vat_grid_transmission_night=config_data.get(
                "vat_grid_transmission_night", False
            ),
            vat_grid_transmission_day=config_data.get(
                "vat_grid_transmission_day", False
            ),
            vat_supplier_renewable_energy_charge=config_data.get(
                "vat_supplier_renewable_energy_charge", False
            ),
            vat_supplier_margin=config_data.get("vat_supplier_margin", False),
        )

    def _round_price(self, price: float) -> float:
        """Round price to the configured precision."""
        return round(price, PRICE_DECIMAL_PRECISION)
