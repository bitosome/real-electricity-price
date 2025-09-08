"""Data models for Real Electricity Price integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class PriceData:
    """Represents a single price data point."""

    start_time: datetime
    end_time: datetime
    price: float
    actual_price: float | None = None


@dataclass
class DayPriceData:
    """Represents price data for a single day."""

    date: str
    data_available: bool
    hourly_prices: list[PriceData]


@dataclass
class CheapPriceRange:
    """Represents a cheap price range."""

    start_time: datetime
    end_time: datetime
    hour_count: int
    min_price: float
    max_price: float
    avg_price: float


@dataclass
class PriceAnalysis:
    """Analysis results for price data."""

    min_price: float
    max_price: float
    avg_price: float
    cheap_threshold: float
    analysis_period_hours: int
    data_sources: list[dict[str, Any]]


@dataclass
class CheapPriceData:
    """Complete cheap price analysis data."""

    cheap_ranges: list[CheapPriceRange]
    analysis: PriceAnalysis
    last_update: datetime
    trigger_time: datetime | None = None
    current_status: str = "inactive"


@dataclass
class IntegrationConfig:
    """Configuration data for the integration."""

    # Basic settings
    name: str
    grid: str
    supplier: str
    country_code: str
    vat_rate: float

    # Grid costs
    grid_electricity_excise_duty: float
    grid_renewable_energy_charge: float
    grid_transmission_price_night: float
    grid_transmission_price_day: float

    # Supplier costs
    supplier_renewable_energy_charge: float
    supplier_margin: float

    # Time settings
    night_price_start_time: str
    night_price_end_time: str

    # Update settings
    scan_interval: int
    cheap_price_update_trigger: str
    acceptable_price: float

    # VAT settings
    vat_nord_pool: bool = True
    vat_grid_electricity_excise_duty: bool = False
    vat_grid_renewable_energy_charge: bool = False
    vat_grid_transmission_night: bool = False
    vat_grid_transmission_day: bool = False
    vat_supplier_renewable_energy_charge: bool = False
    vat_supplier_margin: bool = False
