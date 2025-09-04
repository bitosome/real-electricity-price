# Real Electricity Price (Home Assistant)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![Tests](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml/badge.svg)](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml)
[![License][license-shield]](LICENSE)

Real-time electricity prices for Nord Pool delivery areas, with transparent component-based calculation, configurable grid/supplier costs and VAT flags, and a dedicated cheap-hours analysis pipeline.

Current version: v1.1.1

## Recent Updates (v1.1.1)

- **Fixed cheap hours threshold calculation**: Corrected formula from `base_price * threshold_percent` to `base_price * (1 + threshold_percent / 100)` ensuring accurate identification of cheap hours
- **Fixed cheap hours sensor state**: Sensor now correctly shows total cheap hours (e.g., 8) instead of number of ranges (e.g., 3)  
- **Fixed status attributes**: `total_cheap_hours` in sensor attributes now displays actual hour count across all cheap periods
- **Enhanced calculation transparency**: Cheap hours analysis now properly spans multiple days and includes future periods up to 3 days ahead

## Overview

- Current price and full day series (yesterday/today/tomorrow)
- Per-component price model (grid, supplier, market base) with per-component VAT
- Dual coordinators: price data and cheap-hours analysis
- Time-based cheap-hours recalculation (default 14:30) and manual controls
- Weekend/holiday-aware tariff calculation and solid timezone handling

Data source: Nord Pool Day-Ahead Prices.

## Installation

HACS (recommended)
- HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/bitosome/real-electricity-price` (Integration)
- Install “Real Electricity Price”, restart Home Assistant
- Settings → Devices & Services → Add Integration → “Real Electricity Price”

Manual
- Copy `custom_components/real_electricity_price` into your Home Assistant `custom_components` directory
- Restart Home Assistant and add the integration from the UI

## Configuration (UI config flow)

Basic
- Name: Device name for grouping entities (default: “Real Electricity Price”)
- Country/Area code: One of `EE, FI, LV, LT, SE1, SE2, SE3, SE4, NO1, NO2, NO3, NO4, NO5, DK1, DK2` (default: EE)
- Grid: Grid operator name (default: `Elektrilevi`)
- Supplier: Supplier name (default: `Enefit`)

Costs (€/kWh)
- Grid excise duty (`grid_electricity_excise_duty`, default 0.0026)
- Grid renewable charge (`grid_renewable_energy_charge`, default 0.0104)
- Grid transmission night (`grid_electricity_transmission_price_night`, default 0.0260)
- Grid transmission day (`grid_electricity_transmission_price_day`, default 0.0458)
- Supplier renewable charge (`supplier_renewable_energy_charge`, default 0.0000)
- Supplier margin (`supplier_margin`, default 0.0105)

Tax
- VAT % (`vat`, default 24.0)
- VAT flags (apply VAT to component):
  - `vat_nord_pool` (default true)
  - `vat_grid_electricity_excise_duty` (default false)
  - `vat_grid_renewable_energy_charge` (default false)
  - `vat_grid_transmission_night` (default false)
  - `vat_grid_transmission_day` (default false)
  - `vat_supplier_renewable_energy_charge` (default false)
  - `vat_supplier_margin` (default false)

Time & refresh
- Night price start time (`night_price_start_time`, default 22:00)
- Night price end time (`night_price_end_time`, default 07:00)
- Data scan interval seconds (`scan_interval`, 300–86400; default 3600)
- Cheap-hours daily update trigger (`cheap_hours_update_trigger`, default 14:30)

Cheap-hours analysis
- Base price (`cheap_hours_base_price`, default 0.150000 €/kWh)
- Threshold percent (`cheap_hours_threshold`, default 10.0%)
  - A price is "cheap" if `price ≤ base_price` OR `price ≤ base_price × (1 + threshold/100)`.

Validation
- Area code must be one of the supported delivery areas
- VAT must be 0–100
- `scan_interval` must be 300–86400 seconds
- Time selectors accept valid times; start/end times can cross midnight

## Entities

Sensors
- Current Price (`sensor.…_current_price`, €/kWh): Current hour final price. Attributes include `price_components` and `calculation_details`.
- Current Tariff (`sensor.…_current_tariff`): “day” or “night”, weekend/holiday aware, local timezone.
- Hourly Prices Yesterday/Today/Tomorrow (`sensor.…_hourly_prices_*`, €/kWh):
  - Today: state = current hour price; Yesterday/Tomorrow: state = average when available.
  - Attributes: `hourly_prices` (start/end, base price, final price, tariff, holiday/weekend), `statistics` (min/max/avg), `data_available`.
- Last Sync (`sensor.…_last_sync`, timestamp): Time of last successful data fetch. Attributes include `data_sources` summary.
- Last Cheap Hours Calculation (`sensor.…_last_cheap_calculation`, timestamp): From cheap-hours coordinator; attributes include trigger info.
- Cheap Hours (`sensor.…_cheap_hours`, hours): Total count of cheap hours across all upcoming periods. Attributes: `cheap_price_ranges` (detailed periods with times and prices), `status_info`, `analysis_info`, `calculation_info`.
- Cheap Hours Start/End (`sensor.…_cheap_hours_start|end`, timestamp): Next cheap period start/end in local time.

Buttons
- Sync data (`button.…_sync_data`): Triggers an immediate data refresh.
- Calculate Cheap Hours (`button.…_calculate_cheap_hours`): Re-runs cheap-hours analysis immediately.

Runtime config helpers
- Number: Cheap hour base price
- Number: Cheap hour threshold (%)
- Time: Cheap hours calculation time

Note: Entity IDs are derived from your chosen device name; all entities are grouped under a single device.

## Data refresh & timing

- Network fetch: Controlled by `scan_interval` (default hourly). Each fetch pulls yesterday, today, and tomorrow (if available) from Nord Pool.
- Hourly tick: At every hh:00, all entities re-render without network calls to reflect the new hour.
- Midnight: When near midnight (22:00–02:00), an extra refresh is scheduled to catch the date rollover.
- Tomorrow’s data: Usually published around 14:00 CET. Until then, a placeholder for tomorrow is exposed (time ranges, tariffs; prices unavailable).
- Cheap-hours: Recalculated daily at `cheap_hours_update_trigger` and after a successful data sync; can be triggered via button or service.

## Price calculation

Units
- Nord Pool is returned in EUR/MWh and converted to €/kWh.
- All configured costs are €/kWh.

Computation
- Base: `base_kwh = price_mwh / 1000` and if `vat_nord_pool` then `base_kwh *= (1 + vat/100)`.
- Grid components (each optionally VAT’ed): excise, renewable (grid), transmission (night/day).
- Supplier components (each optionally VAT’ed): renewable (supplier), margin.
- Final (€/kWh): Sum of base (after optional VAT) + all components (each with optional VAT). No single VAT is applied to the entire sum.

## Regions

Supported delivery areas: `EE, FI, LV, LT, SE1, SE2, SE3, SE4, NO1, NO2, NO3, NO4, NO5, DK1, DK2`.

## Services

- `real_electricity_price.refresh_data` → refresh data now
- `real_electricity_price.recalculate_cheap_prices` → recompute cheap hours now

## Troubleshooting

- Tomorrow missing: Published ~14:00 CET; press Sync data afterwards.
- No/incorrect prices: Verify delivery area, VAT %, costs, and internet access; check logs.
- Tariff off: Night hours are local-time based; verify `night_price_start_time`/`night_price_end_time`.
- Only some entities visible: Open the device page for the integration and verify all sensors, buttons, and helper entities.

Debug logging
```yaml
logger:
  default: warning
  logs:
    custom_components.real_electricity_price: debug
    custom_components.real_electricity_price.api: debug
    custom_components.real_electricity_price.coordinator: debug
    custom_components.real_electricity_price.cheap_hours_coordinator: debug
```

## Notes

- Weekend/holiday detection uses the country derived from the area code (e.g., `SE` from `SE3`).
- Timezone handling uses Home Assistant’s configured timezone, with explicit per-country defaults where relevant.

## License

MIT License — see `LICENSE`.

[releases-shield]: https://img.shields.io/github/release/bitosome/real-electricity-price.svg?style=for-the-badge
[releases]: https://github.com/bitosome/real-electricity-price/releases
[license-shield]: https://img.shields.io/github/license/bitosome/real-electricity-price.svg?style=for-the-badge
