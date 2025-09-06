# ⚡ Real Electricity Price

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![Tests](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml/badge.svg)](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml)
[![License][license-shield]](LICENSE)

A comprehensive Home Assistant integration providing real-time electricity prices for Nord Pool delivery areas with transparent cost calculations and intelligent cheap-hours analysis.

## ✨ Features

- **Real-time Nord Pool prices** for all delivery areas (EE, FI, LV, LT, SE1-4, NO1-5, DK1-2)
- **Component-based pricing** with separate grid, supplier, and market costs
- **Flexible VAT configuration** per cost component
- **Smart cheap-hours analysis** with intelligent triggering and configurable thresholds
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
- **Country/Area**: Nord Pool delivery area (EE, FI, LV, LT, SE1-4, NO1-5, DK1-2)
- **Grid Provider**: Your grid operator name
- **Supplier**: Your electricity supplier name

### Cost Configuration
Configure your local electricity costs in €/kWh:
- Grid excise duty, renewable charges, transmission prices (day/night)
- Supplier renewable charges and margin
- VAT percentage and per-component VAT flags

### Time Settings
- **Night tariff hours**: Define when night prices apply (default: 22:00-07:00)
- **Update intervals**: Data refresh frequency (default: 1 hour)
- **Cheap hours calculation**: Daily recalculation time (default: 15:00)

### Cheap Hours Analysis
- **Base price**: Reference price for cheap hour calculations (€/kWh)
- **Threshold**: Percentage above base price still considered "cheap"
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
- **Next Cheap Hours Start/End**: When the next cheap period begins/ends
- **Last Sync**: When price data was last updated

### Control Entities
- **Cheap Hours Threshold**: Adjustable threshold percentage
- **Cheap Hours Base Price**: Adjustable base price for calculations
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

## 🐛 Troubleshooting

### Common Issues

**Integration not appearing**
- Ensure HACS is installed and configured
- Check that the repository was added as "Integration" category
- Restart Home Assistant after installation

**No price data**
- Verify your area code is correct (case-sensitive)
- Check internet connectivity
- Nord Pool API may have temporary outages (integration preserves recent data for up to 6 hours)
- For persistent issues, use the "Sync data" button for manual refresh

**Incorrect cheap hours**
- Verify base price and threshold settings match your expectations
- Check that calculation time allows for complete price data
- Use the manual "Calculate Cheap Hours" button for immediate updates
- Calculations now trigger only in 3 scenarios: startup, manual trigger, or scheduled time (15:00 by default)

### Debug Logging
Add to your `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.real_electricity_price: debug
```

**Note**: Recent updates have significantly reduced log noise. Most API-related warnings are now debug-level messages, with only critical issues logged as warnings or errors.

## 🔄 Recent Updates (v1.1.1)

### Bug Fixes & Reliability Improvements
- **Fixed timezone consistency**: Eliminated date mismatch warnings at timezone boundaries
- **Improved API failure handling**: Prevents data gaps during Nord Pool API outages with intelligent data retention
- **Enhanced error categorization**: Reduced log noise while preserving critical error information
- **Fixed cheap hours calculation timing**: Now triggers only when needed (startup, manual, or scheduled time)

### Performance Optimizations  
- **Reduced cheap hours calculations by ~90%**: From 24+ times/day to only when necessary
- **Eliminated cascading API failures**: Coordinators no longer conflict during API outages
- **Improved system stability**: Better handling of API rate limits and temporary outages
- **Smarter data preservation**: Maintains sensor availability during short API failures (up to 6 hours)

### Previous Fixes (v1.0.0)
- **Fixed cheap hours threshold calculation**: Corrected formula ensuring accurate identification
- **Fixed cheap hours sensor state**: Now shows total hours instead of number of ranges
- **Enhanced calculation transparency**: Analysis now spans multiple days with future periods
- **Improved midnight transition handling**: Native Home Assistant time tracking

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
pip install -r tests/test-requirements.txt
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
- Inspired by the need for transparent electricity pricing in the Nordics

---

<div align="center">

**[Documentation](https://github.com/bitosome/real-electricity-price/wiki)** • 
**[Issues](https://github.com/bitosome/real-electricity-price/issues)** • 
**[Discussions](https://github.com/bitosome/real-electricity-price/discussions)**

</div>

[releases-shield]: https://img.shields.io/github/v/release/bitosome/real-electricity-price?style=flat-square
[releases]: https://github.com/bitosome/real-electricity-price/releases
[license-shield]: https://img.shields.io/github/license/bitosome/real-electricity-price?style=flat-square