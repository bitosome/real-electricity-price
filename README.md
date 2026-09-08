# ⚡ Real Electricity Price

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![Tests](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml/badge.svg)](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml)
[![License][license-shield]](LICENSE)

A comprehensive Home Assistant integration providing real-time electricity prices for Nord Pool delivery areas with transparent cost calculations and intelligent cheap-hours analysis.

## ✨ Features

- **Real-time Nord Pool prices** for all delivery areas (Nordic/Baltic + Central-Western Europe)
- **Dual off-peak strategies**: Fixed time windows OR Nord Pool blocks (Off-peak 1, Peak, Off-peak 2)
- **Extended area support**: EE, FI, LV, LT, SE1-4, NO1-5, DK1-2, DE-LU, NL, BE, FR, AT, PL, GB
- **Component-based pricing** with separate grid, supplier, and market costs
- **Flexible VAT configuration** per cost component  
- **Regional holiday support** with subdivision codes (German states, French territories, Norwegian counties)
- **Smart cheap-hours analysis** with intelligent triggering and simple acceptable price configuration
- **High reliability** with intelligent data retention during API outages
- **Weekend/holiday awareness** for accurate tariff calculations
- **Multiple time zones** support with DST handling and timezone consistency
- **Rich sensor data** including current prices, daily series, and price predictions
- **Performance optimized** with reduced API calls and eliminated cascading failures

## 📦 Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bitosome&repository=real-electricity-price&category=integration)

1. Install [HACS](https://hacs.xyz) if you haven't already
2. Click the badge above or manually add this repository to HACS:
   - HACS → Integrations → ⋮ → Custom repositories
   - Repository: `https://github.com/bitosome/real-electricity-price`
   - Category: Integration
3. Search for "Real Electricity Price" and install
4. Restart Home Assistant
5. Add the integration: Settings → Devices & Services → Add Integration → "Real Electricity Price"

### Manual Installation

1. Download the latest release from the [releases page][releases]
2. Copy the `custom_components/real_electricity_price` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Add the integration via the UI

## ⚙️ Configuration

The integration is configured entirely through the Home Assistant UI. After installation:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration** and search for "Real Electricity Price"
3. Follow the configuration steps:

### Basic Settings
- **Name**: Device name for grouping entities
- **Country/Area**: Nord Pool delivery area covering:
  - **Nordic/Baltic**: EE, FI, LV, LT, SE1-4, NO1-5, DK1-2
  - **Central-Western Europe**: DE-LU, NL, BE, FR, AT, PL, GB
- **Grid Provider**: Your grid operator name
- **Supplier**: Your electricity supplier name

### Cost Configuration
Configure your local electricity costs in €/kWh:
- Grid excise duty, renewable charges, transmission prices (day/night)
- Regulated surcharges including the 2026 supply security (grid) and balancing capacity (supplier) fees
- Supplier renewable charges and margin
- VAT percentage and per-component VAT flags  

### Off-peak Strategy Configuration
Choose how off-peak periods are determined:

#### Night Window Strategy (Default)
- **Night tariff hours**: Define when night prices apply (default: 22:00-07:00)
- **Weekend/holiday behavior**: Apply off-peak rates all day on weekends/holidays
- **Regional holidays**: Optional subdivision codes for specific regional holidays:
  - **Germany**: BW (Baden-Württemberg), BY (Bavaria), BE (Berlin), etc.
  - **France**: GP (Guadeloupe), RE (Réunion) for overseas territories
  - **Norway**: 03 (Oslo), 11 (Rogaland) for county-specific holidays

#### Nord Pool Blocks Strategy  
- **Block-based pricing**: Aligns with Nord Pool's Off-peak 1, Peak, Off-peak 2 structure
- **Per-block transmission prices**: Configure separate rates for each block period
- **Automatic block detection**: Uses Nord Pool's `blockPriceAggregates` when available
- **Fallback time mapping**: 00-07h (Off-peak 1), 08-19h (Peak), 20-23h (Off-peak 2)
- **Weekend/holiday override**: Apply off-peak rates all day when enabled

### Update Settings
- **Update intervals**: Data refresh frequency (default: 1 hour)
- **Cheap hours calculation**: Daily recalculation time (default: 15:00)

### Cheap Hours Analysis
- **Acceptable Price**: Maximum price you consider acceptable for cheap hours (€/kWh)
  - Simple logic: any hour with price ≤ acceptable price is considered cheap
  - No complex calculations - straightforward and intuitive
- **Smart calculation**: Only triggers in 3 scenarios for optimal performance:
  1. **Integration startup** (when tomorrow's prices are available)
  2. **Manual trigger** (button press or service call)  
  3. **Scheduled time** (daily at configured time, default: 15:00)

## 🔧 Sensors & Entities

The integration provides comprehensive sensor data:

### Price Sensors
- **Current Price**: Real-time electricity price including all components
- **Current Tariff**: Active tariff (day/night) based on your configuration
- **Hourly Prices**: Yesterday, today, and tomorrow price series

### Analysis Sensors  
- **Cheap Hours**: Number of cheap hours in upcoming periods
- **Cheap Period Start/End**: Boundaries of the active cheap period, or the next
  cheap period when no cheap period is active
- **Last Sync**: When price data was last updated

### Control Entities
- **Acceptable Price**: Adjustable maximum price for cheap hour identification
- **Calculate Cheap Hours**: Manual recalculation button

## 🛠️ Advanced Features

### Dual Coordinator Architecture
- **Price Coordinator**: Handles Nord Pool data fetching with intelligent caching and failure recovery
- **Cheap Hours Coordinator**: Independent analysis scheduling with anti-cascade failure protection

### Smart Scheduling & Reliability
- **Timezone-aware updates**: Consistent date handling across all time zones
- **Intelligent data retention**: Preserves recent data during temporary API outages (up to 6 hours)
- **Anti-cascade protection**: Coordinators don't trigger redundant API calls during failures
- **Optimized calculation timing**: Cheap hours analysis only when necessary, not on every data sync
- **Midnight transition handling**: Native Home Assistant time tracking with DST support

### Transparent Calculations
All price components are clearly separated and configurable:
```
Total Price = Nord Pool + Grid Costs + Supplier Costs + VAT
```

### Recommended Price Card

Use the companion
[Real Electricity Price Card](https://github.com/bitosome/real-electricity-price-card)
to render the hourly data exposed by the yesterday, today, and tomorrow sensors.
The card reads their `hourly_prices` attributes directly, so no intermediate chart
sensor is required.

```yaml
type: custom:real-electricity-price-card
yesterday_entity: sensor.real_electricity_price_hourly_prices_yesterday
today_entity: sensor.real_electricity_price_hourly_prices_today
tomorrow_entity: sensor.real_electricity_price_hourly_prices_tomorrow
current_price_entity: sensor.real_electricity_price_current_price
cheap_price_entity: number.real_electricity_price_acceptable_price
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Development Setup
```bash
git clone https://github.com/bitosome/real-electricity-price.git
cd real-electricity-price
pip install -r requirements.txt
```

### Running Tests
```bash
cd tests
./test.sh
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- Data provided by [Nord Pool](https://www.nordpoolgroup.com/)
- Built for the [Home Assistant](https://www.home-assistant.io/) community

[releases-shield]: https://img.shields.io/github/v/release/bitosome/real-electricity-price?style=flat-square
[releases]: https://github.com/bitosome/real-electricity-price/releases
[license-shield]: https://img.shields.io/github/license/bitosome/real-electricity-price?style=flat-square
