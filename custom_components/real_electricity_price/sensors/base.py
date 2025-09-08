"""Base sensor class for Real Electricity Price integration."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import CONF_NAME

from ..const import (
    ACCEPTABLE_PRICE_DEFAULT,
    CONF_ACCEPTABLE_PRICE,
    CONF_CHEAP_HOURS_UPDATE_TRIGGER,
    CONF_COUNTRY_CODE,
    CONF_GRID,
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_TIME,
    CONF_SCAN_INTERVAL,
    CONF_SUPPLIER,
    CONF_SUPPLIER_MARGIN,
    CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT,
    CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT_GRID_TRANSMISSION_DAY,
    CONF_VAT_GRID_TRANSMISSION_NIGHT,
    CONF_VAT_NORD_POOL,
    CONF_VAT_SUPPLIER_MARGIN,
    CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    COUNTRY_CODE_DEFAULT,
    DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER,
    DEFAULT_SCAN_INTERVAL,
    GRID_DEFAULT,
    GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
    GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    NIGHT_PRICE_END_TIME_DEFAULT,
    NIGHT_PRICE_START_TIME_DEFAULT,
    PRICE_DECIMAL_PRECISION,
    SUPPLIER_DEFAULT,
    SUPPLIER_MARGIN_DEFAULT,
    SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    VAT_DEFAULT,
    VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    VAT_GRID_TRANSMISSION_DAY_DEFAULT,
    VAT_GRID_TRANSMISSION_NIGHT_DEFAULT,
    VAT_NORD_POOL_DEFAULT,
    VAT_SUPPLIER_MARGIN_DEFAULT,
    VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
)
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
            grid=config_data.get(CONF_GRID, GRID_DEFAULT),
            supplier=config_data.get(CONF_SUPPLIER, SUPPLIER_DEFAULT),
            country_code=config_data.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT),
            vat_rate=config_data.get(CONF_VAT, VAT_DEFAULT),
            grid_electricity_excise_duty=config_data.get(
                CONF_GRID_ELECTRICITY_EXCISE_DUTY, GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT
            ),
            grid_renewable_energy_charge=config_data.get(
                CONF_GRID_RENEWABLE_ENERGY_CHARGE, GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT
            ),
            grid_transmission_price_night=config_data.get(
                CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
            ),
            grid_transmission_price_day=config_data.get(
                CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
            ),
            supplier_renewable_energy_charge=config_data.get(
                CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
            ),
            supplier_margin=config_data.get(
                CONF_SUPPLIER_MARGIN, SUPPLIER_MARGIN_DEFAULT
            ),
            night_price_start_time=config_data.get(
                CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT
            ),
            night_price_end_time=config_data.get(
                CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT
            ),
            scan_interval=config_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            cheap_price_update_trigger=config_data.get(
                CONF_CHEAP_HOURS_UPDATE_TRIGGER, DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER
            ),
            acceptable_price=config_data.get(
                CONF_ACCEPTABLE_PRICE, ACCEPTABLE_PRICE_DEFAULT
            ),
            vat_nord_pool=config_data.get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT),
            vat_grid_electricity_excise_duty=config_data.get(
                CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
            ),
            vat_grid_renewable_energy_charge=config_data.get(
                CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
            ),
            vat_grid_transmission_night=config_data.get(
                CONF_VAT_GRID_TRANSMISSION_NIGHT, VAT_GRID_TRANSMISSION_NIGHT_DEFAULT
            ),
            vat_grid_transmission_day=config_data.get(
                CONF_VAT_GRID_TRANSMISSION_DAY, VAT_GRID_TRANSMISSION_DAY_DEFAULT
            ),
            vat_supplier_renewable_energy_charge=config_data.get(
                CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
            ),
            vat_supplier_margin=config_data.get(
                CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT
            ),
        )

    def _round_price(self, price: float) -> float:
        """Round price to the configured precision."""
        return round(price, PRICE_DECIMAL_PRECISION)
