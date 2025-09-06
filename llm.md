**Overview**
- Purpose: Broaden off-peak calculation scenarios, align tariffs with Nord Pool blocks, expand supported areas, add regional holiday handling, and split config into clear steps to avoid time-input validation issues.
- Integration: Home Assistant custom component `real_electricity_price`.

**Key Features Added**
- Off-peak Strategy selector with two modes:
  - `night_window`: uses a single off-peak time window (existing behavior).
  - `nordpool_blocks`: aligns with Nord Pool blocks (Off-peak 1, Peak, Off-peak 2).
- Block Tariffs configuration step with per-block transmission prices.
- Optional regional holiday subdivision (e.g., state/province) for holiday calendars.
- Extended Nord Pool area list: `DE-LU`, `NL`, `BE`, `FR`, `AT`, `PL`, `GB`.
- Startup migration to set default strategy for existing entries.
- Removal of Selenium UI tests.

**Where Changes Were Made**

1) Constants and Config Keys
- Added off-peak strategy constants and block tariff keys:
  - `custom_components/real_electricity_price/const.py:58`
  - `custom_components/real_electricity_price/const.py:79`
  - `custom_components/real_electricity_price/const.py:82`
  - `custom_components/real_electricity_price/const.py:85`
- Added optional holiday subdivision:
  - `custom_components/real_electricity_price/const.py:141`

2) Config Flow (UI)
- Extended valid area list with additional Nord Pool markets:
  - `custom_components/real_electricity_price/config_flow.py:109`
- New Off-peak Strategy step (branching point):
  - `custom_components/real_electricity_price/config_flow.py:425`
- New Block Tariffs step (per-block prices + weekend/holiday options + subdivision):
  - `custom_components/real_electricity_price/config_flow.py:462`
- Time validation now depends on selected strategy; times only required for `night_window`:
  - `custom_components/real_electricity_price/config_flow.py:160`
- Options flow updated to show either Night Times or Block Tariffs fields based on strategy:
  - `custom_components/real_electricity_price/config_flow.py:993`
- Updated invalid country error copy to reflect extended areas:
  - `custom_components/real_electricity_price/config_flow.py:1445`

3) API Behavior (tariff classification and pricing)
- Strategy-aware tariff classification for placeholder days:
  - `custom_components/real_electricity_price/api.py:300`
- Strategy-aware tariff classification for real data using `blockPriceAggregates` with hour-based fallback:
  - `custom_components/real_electricity_price/api.py:528`
- Per-block transmission price selection (Off-peak 1/2 vs Peak):
  - `custom_components/real_electricity_price/api.py:583`
- Regional holiday subdivision support with safe fallback when unsupported by `holidays`:
  - `custom_components/real_electricity_price/api.py:332`
  - `custom_components/real_electricity_price/api.py:488`

4) Setup and Migration
- Ensure `offpeak_strategy` exists for older entries (default to `night_window`):
  - `custom_components/real_electricity_price/__init__.py:133`

5) Translations / UI Labels
- New steps and fields in translations:
  - Off-peak Strategy step: `custom_components/real_electricity_price/translations/en.json:41`
  - Block Tariffs step: `custom_components/real_electricity_price/translations/en.json:53`
  - Additional user-facing labels for strategy and per-block prices added in the user/options sections:
    - `custom_components/real_electricity_price/translations/en.json:20`

6) Test Cleanup
- Removed Selenium UI tests dir:
  - deleted `tests/selenium/`

**Behavioral Details**
- Strategy selection determines the configuration path:
  - `night_window` → Night Times step (validates off-peak start/end times and weekend/holiday toggles; accepts optional `holiday_subdivision`).
  - `nordpool_blocks` → Block Tariffs step (collects `grid_electricity_transmission_price_offpeak1|peak|offpeak2`, weekend/holiday toggles, optional `holiday_subdivision`). No time validation here.
- Runtime tariff classification:
  - `nordpool_blocks`:
    - Uses Nord Pool `blockPriceAggregates` to determine block per hour; if missing, falls back to hours (00–07 = Off-peak 1, 08–19 = Peak, 20–23 = Off-peak 2).
    - Weekend/holiday (if enabled) → Off-peak all day.
  - `night_window`:
    - Off-peak by configured window, with weekend/holiday override.
- Transmission price selection:
  - `nordpool_blocks`: picks configured price per block and applies VAT day/night flags (Peak uses “day” VAT; Off-peak 1/2 use “night” VAT).
  - `night_window`: uses existing day/night transmission prices.

**Backwards Compatibility and Validations**
- Default strategy is `night_window`, preserving prior behavior.
- Migration writes default `offpeak_strategy` if absent.
- Block tariff numeric inputs validated when provided.
- Time inputs validated only for `night_window` (prevents erroneous validation in blocks mode).

**User-visible Changes**
- New Off-peak Strategy step in the config flow.
- New Block Tariffs step if `nordpool_blocks` is selected.
- Optional `holiday_subdivision` field in Night Times and Block Tariffs steps.
- Expanded area dropdown with additional Nord Pool markets.

**Potential Follow-ups**
- Update README with examples for both strategies and per-block pricing.
- Add tests for strategy branching and per-block math (unit/integration; selenium removed).

