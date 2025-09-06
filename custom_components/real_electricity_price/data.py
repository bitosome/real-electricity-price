"""Custom types for real_electricity_price."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import RealElectricityPriceApiClient
    from .cheap_hours_coordinator import CheapHoursDataUpdateCoordinator
    from .coordinator import RealElectricityPriceDataUpdateCoordinator

    # Python <3.12 compatibility: define type alias only for type checking
    # to avoid runtime syntax errors.
    RealElectricityPriceConfigEntry = ConfigEntry["RealElectricityPriceData"]


@dataclass
class RealElectricityPriceData:
    """Data for the Real Electricity Price integration."""

    client: RealElectricityPriceApiClient
    coordinator: RealElectricityPriceDataUpdateCoordinator
    cheap_hours_coordinator: CheapHoursDataUpdateCoordinator
    integration: Integration
