"""Custom types for real_electricity_price."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import RealElectricityPriceApiClient
    from .coordinator import RealElectricityPriceDataUpdateCoordinator


type RealElectricityPriceConfigEntry = ConfigEntry[RealElectricityPriceData]


@dataclass
class RealElectricityPriceData:
    """Data for the Real Electricity Price integration."""

    client: RealElectricityPriceApiClient
    coordinator: RealElectricityPriceDataUpdateCoordinator
    integration: Integration
