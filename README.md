# Real Electricity Price Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A comprehensive Home Assistant integration for real-time electricity pricing from Nord Pool, with Estonian grid costs and supplier charges included.

## Features

### 🏠 Unified Se### Common Issues

#### Integration Won't Load
```bash
# Check logs for import errors
grep -i "real_electricity_price" /config/home-assistant.log
```

#### Integration Logo/Icon Not Displaying
The integration includes icon and logo files locally, but for official display in Home Assistant:

1. **Local Display**: Icon/logo files are included in the integration directory
2. **Official Branding**: Submit to [Home Assistant brands repository](https://github.com/home-assistant/brands)
3. **Submission Guide**: See `BRAND_SUBMISSION.md` for complete instructions
4. **Timeline**: 1-7 days for review, automatic display after merge

The integration works perfectly without custom branding - icons are cosmetic improvements only.

#### Only One Entity Visible
If you see only one entity instead of 10 (9 sensors + 1 button):

1. **Check Entity List**: Go to Settings → Devices & Services → Entities, search for "real_electricity_price"
2. **Check Device View**: Go to Settings → Devices & Services → Real Electricity Price → Click the device
3. **Check Developer Tools**: Go to Developer Tools → States, search for "real_electricity_price"
4. **Verify All Entities**:
   - `sensor.real_electricity_price_current_price`
   - `sensor.real_electricity_price_hourly_prices_today`
   - `sensor.real_electricity_price_hourly_prices_tomorrow`
   - `sensor.real_electricity_price_max_today`
   - `sensor.real_electricity_price_min_today`
   - `sensor.real_electricity_price_max_tomorrow`
   - `sensor.real_electricity_price_min_tomorrow`
   - `sensor.real_electricity_price_last_sync`
   - `sensor.real_electricity_price_current_tariff`
   - `button.real_electricity_price_refresh_data`
5. **Force Refresh**: Try restarting Home Assistant or reloading the integration

#### No Data Availablehitecture
- **Single device** with multiple sensors grouped together
- **Professional branding** as a real electricity price service
- **Device-level information** including manufacturer and model

### 📊 Comprehensive Price Monitoring
- **Current price sensor** with real-time hourly updates
- **Daily price arrays** for today and tomorrow
- **Min/Max aggregates** for both today and tomorrow
- **Last sync tracking** for data freshness monitoring
- **Current tariff detection** (day/night/weekend/holiday)

### ⚡ Smart Automation Ready
- **Automatic hourly updates** when price changes
- **Manual refresh button** for instant data updates
- **Rich attributes** with price breakdowns and metadata
- **Tariff-aware pricing** based on market blocks and holidays
- **Weekend and holiday detection** for Estonian calendar

### 🌍 Configurable Pricing Structure
- **Grid costs**: Excise duty, renewable energy charges, transmission prices
- **Supplier costs**: Margins and renewable energy charges  
- **Tax handling**: VAT calculation and regional adjustments
- **Market integration**: Nord Pool API with authentication support

## Sensors

The integration creates the following sensors under a single device:

| Sensor | Entity ID | Description | Unit | Update Frequency |
|--------|-----------|-------------|------|------------------|
| **Current Price** | `sensor.real_electricity_price_current_price` | Real-time electricity price for current hour | EUR/kWh | Hourly (automatic) |
| **Hourly Prices Today** | `sensor.real_electricity_price_hourly_prices_today` | Complete price array for today (24 hours) | EUR/kWh | Daily at midnight |
| **Hourly Prices Tomorrow** | `sensor.real_electricity_price_hourly_prices_tomorrow` | Complete price array for tomorrow (24 hours) | EUR/kWh | Daily at ~14:00 CET |
| **Max Price Today** | `sensor.real_electricity_price_max_today` | Highest price for today | EUR/kWh | Daily at midnight |
| **Min Price Today** | `sensor.real_electricity_price_min_today` | Lowest price for today | EUR/kWh | Daily at midnight |
| **Max Price Tomorrow** | `sensor.real_electricity_price_max_tomorrow` | Highest price for tomorrow | EUR/kWh | Daily at ~14:00 CET |
| **Min Price Tomorrow** | `sensor.real_electricity_price_min_tomorrow` | Lowest price for tomorrow | EUR/kWh | Daily at ~14:00 CET |
| **Last Data Sync** | `sensor.real_electricity_price_last_sync` | Timestamp of last successful data update | Timestamp | On each update |
| **Current Tariff** | `sensor.real_electricity_price_current_tariff` | Current pricing period (day/night) | Text | Real-time |
| **Refresh Data** | `button.real_electricity_price_refresh_data` | Manual refresh button | Button | Manual |

### Current Price Sensor

The main sensor provides:
- **State**: Current hour price in EUR/kWh (all costs included)
- **Attributes**:
  - `date`: Data date (YYYY-MM-DD)
  - `hour_start`: Current hour start time (ISO format)
  - `hour_end`: Current hour end time (ISO format)
  - `nord_pool_price`: Base market price before additions

### Hourly Prices Sensors

Complete daily data sensors provide:
- **State**: Current/first hour price
- **Attributes**:
  - `hourly_prices`: Array of 24 hourly price objects
  - `date`: Data date (YYYY-MM-DD)

Each hourly price object contains:
```json
{
  \"start_time\": \"2025-08-31T19:00:00Z\",
  \"end_time\": \"2025-08-31T20:00:00Z\",
  \"nord_pool_price\": 0.14131,
  \"actual_price\": 0.236604,
  \"tariff\": \"night\",
  \"is_holiday\": false,
  \"is_weekend\": true
}
```

### Current Tariff Sensor

Shows the current pricing period:
- **night**: Off-peak hours, weekends, holidays
- **day**: Peak hours on business days (based on Nord Pool blocks)

The tariff determination follows this logic:
1. **Weekends/Holidays**: Always \"night\" tariff
2. **Business days**: Based on Nord Pool block aggregates:
   - \"Peak\" blocks → \"day\" tariff
   - All other blocks → \"night\" tariff

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS:
   - HACS → Integrations → ⋮ → Custom repositories
   - Repository: `https://github.com/bitosome/real-electricity-price`
   - Category: Integration
2. Search for \"Real Electricity Price\" and install
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Search for \"Real Electricity Price\" and configure

### Manual Installation

1. Download the `custom_components/real_electricity_price` folder from this repository
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant
4. Add the integration through the UI

## Configuration

### Basic Setup

The integration can be configured entirely through the Home Assistant UI:

1. **Device Name**: Custom name for your electricity price device
2. **Grid Provider**: Your electricity grid operator (default: elektrilevi)
3. **Supplier**: Your electricity supplier (default: eesti_energia)
4. **Update Interval**: How often to fetch new data (default: 1 hour)

### Advanced Configuration

#### Grid Costs (EUR/kWh)
- **Electricity Excise Duty**: Government tax (default: 0.0026)
- **Renewable Energy Charge**: Grid renewable fee (default: 0.0104)
- **Transmission Price (Night)**: Grid fee for off-peak (default: 0.026)
- **Transmission Price (Day)**: Grid fee for peak hours (default: 0.0458)

#### Supplier Costs (EUR/kWh)
- **Renewable Energy Charge**: Supplier renewable fee (default: 0.00)
- **Supplier Margin**: Supplier profit margin (default: 0.0105)

#### Regional Settings
- **Country Code**: Market area (default: EE for Estonia)
- **VAT**: Value Added Tax percentage (default: 24.0%)
- **Night Start Hour**: When night tariff begins (default: 22)
- **Night End Hour**: When night tariff ends (default: 7)

### Configuration Example

```yaml
# Example configuration.yaml entry (optional - UI configuration recommended)
# This integration is primarily configured through the UI
real_electricity_price:
  name: \"My Electricity Price\"
  grid: \"elektrilevi\"
  supplier: \"eesti_energia\"
  grid_electricity_excise_duty: 0.0026
  grid_renewable_energy_charge: 0.0104
  vat: 24.0
```

## Usage Examples

### Template Sensors

Create custom sensors in your `configuration.yaml`:

```yaml
template:
  - sensor:
      - name: \"Tomorrow First Hour Price\"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices_tomorrow', 'hourly_prices') %}
          {{ prices[0].actual_price if prices else 'N/A' }}
        unit_of_measurement: \"EUR/kWh\"

      - name: \"Average Price Today\"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices_today', 'hourly_prices') %}
          {% if prices %}
            {{ (prices | map(attribute='actual_price') | list | sum / prices | length) | round(4) }}
          {% else %}
            unavailable
          {% endif %}
        unit_of_measurement: \"EUR/kWh\"
```

### Automations

#### High Price Alert

```yaml
automation:
  - alias: \"High Electricity Price Alert\"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_current_price
    condition:
      - condition: numeric_state
        entity_id: sensor.real_electricity_price_current_price
        above: 0.25  # 25 cents per kWh
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: \"⚡ High electricity price: {{ states('sensor.real_electricity_price_current_price') }} EUR/kWh\"
```

#### Night Tariff Automation

```yaml
automation:
  - alias: \"Start Dishwasher During Night Tariff\"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_current_tariff
        to: \"night\"
    condition:
      - condition: state
        entity_id: switch.dishwasher_ready
        state: \"on\"
    action:
      - service: switch.turn_on
        entity_id: switch.dishwasher
      - service: notify.home_assistant
        data:
          message: \"🌙 Dishwasher started automatically during night tariff ({{ states('sensor.real_electricity_price_current_price') }} EUR/kWh)\"
```

#### EV Charging Optimization

```yaml
automation:
  - alias: \"EV Charging - Pause During Expensive Hours\"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_current_tariff
        to: \"day\"
    condition:
      - condition: state
        entity_id: switch.ev_charger
        state: \"on\"
    action:
      - service: switch.turn_off
        entity_id: switch.ev_charger
      - service: notify.mobile_app_your_phone
        data:
          message: \"⚡ EV charging paused - expensive day rate: {{ states('sensor.real_electricity_price_current_price') }} EUR/kWh\"
```

### Lovelace Cards

#### Simple Price Display

```yaml
type: entities
title: \"Electricity Price\"
entities:
  - sensor.real_electricity_price_current_price
  - sensor.real_electricity_price_current_tariff
  - sensor.real_electricity_price_max_today
  - sensor.real_electricity_price_min_today
```

#### Price History Chart

```yaml
type: history-graph
title: \"Electricity Price History\"
entities:
  - sensor.real_electricity_price_current_price
hours_to_show: 24
refresh_interval: 0
```

#### ApexCharts Advanced Chart

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: \"Electricity Prices\"
graph_span: 48h
span:
  end: day
all_series_config:
  stroke_width: 2
  curve: stepline
series:
  - entity: sensor.real_electricity_price_hourly_prices_today
    type: column
    name: \"Today\"
    data_generator: |
      const prices = entity.attributes.hourly_prices || [];
      return prices.map((hour) => {
        return [new Date(hour.start_time).getTime(), hour.actual_price];
      });
  - entity: sensor.real_electricity_price_hourly_prices_tomorrow
    type: column
    name: \"Tomorrow\"
    data_generator: |
      const prices = entity.attributes.hourly_prices || [];
      return prices.map((hour) => {
        return [new Date(hour.start_time).getTime(), hour.actual_price];
      });
```

## API Information

### Data Source
- **Provider**: Nord Pool (Europe's leading power exchange)
- **API**: `https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices`
- **Market**: Day-ahead electricity market
- **Area**: EE (Estonia)
- **Currency**: EUR
- **Update Schedule**: Daily around 14:00 CET for next day

### Price Calculation

The integration calculates the final price by adding various components to the base Nord Pool price:

```
Final Price = (Nord Pool Price + Grid Costs + Supplier Costs) × (1 + VAT%)
```

Where:
- **Nord Pool Price**: Base market price (EUR/MWh → EUR/kWh)
- **Grid Costs**: Excise duty + Renewable charge + Transmission (day/night)
- **Supplier Costs**: Renewable charge + Margin
- **VAT**: Value Added Tax (typically 24% in Estonia)

### Tariff Logic

The system determines day/night tariffs as follows:

1. **Weekends and Holidays**: Always night tariff
2. **Business Days**: Based on Nord Pool block aggregates:
   - If current time falls within a \"Peak\" block → day tariff
   - Otherwise → night tariff
3. **Fallback**: If no block data available, uses configured hours (22:00-07:00 = night)

## Development

### Requirements
- Python 3.11+
- Home Assistant 2025.8+
- Dependencies: `aiohttp`, `holidays`

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/bitosome/real-electricity-price.git
   cd real-electricity-price
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Testing

The project includes comprehensive testing support:

#### Docker Test Environment

```bash
# Start test environment
docker compose up -d

# Access Home Assistant at http://localhost:8123
# Default login: admin / admin

# View logs
docker logs hass-dev-test --tail 50 -f

# Stop environment
docker compose down
```

#### Manual Testing

1. Copy the integration to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via UI
4. Monitor logs for any issues

### Code Quality

The project uses automated code quality tools:

```bash
# Check code formatting
python -m black custom_components/real_electricity_price/

# Run linting
python -m ruff check custom_components/real_electricity_price/

# Type checking
python -m mypy custom_components/real_electricity_price/
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests and linting
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Troubleshooting

### Common Issues

#### Integration Won't Load
```bash
# Check logs for import errors
grep -i \"real_electricity_price\" /config/home-assistant.log
```

#### No Data Available
1. Verify internet connection
2. Check if Nord Pool API is accessible
3. Validate configuration parameters
4. Check integration logs for API errors

#### Incorrect Prices
1. Verify grid and supplier parameters
2. Check VAT percentage
3. Validate regional settings (country code)
4. Compare with official electricity bill

#### Missing Tomorrow's Data
- Tomorrow's prices are published around 14:00 CET
- Check if the integration has been updated recently
- Manual refresh may be needed after 14:00

### Debug Logging

Enable detailed logging in `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.real_electricity_price: debug
    custom_components.real_electricity_price.api: debug
    custom_components.real_electricity_price.coordinator: debug
```

### Reset Integration

If the integration becomes unresponsive:

1. Go to Settings → Devices & Services
2. Find \"Real Electricity Price\" integration
3. Click the three dots → \"Delete\"
4. Restart Home Assistant
5. Re-add the integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Nord Pool](https://www.nordpoolgroup.com/) for providing electricity market data
- [Home Assistant](https://www.home-assistant.io/) community for the excellent platform
- Estonian grid operators and suppliers for transparent pricing information

## Support

- **Issues**: [GitHub Issues](https://github.com/bitosome/real-electricity-price/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bitosome/real-electricity-price/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

---

**Disclaimer**: This integration is not officially affiliated with Nord Pool or any electricity suppliers. Price data is provided as-is for informational purposes. Always verify prices with your official electricity bill.

[releases-shield]: https://img.shields.io/github/release/bitosome/real-electricity-price.svg?style=for-the-badge
[releases]: https://github.com/bitosome/real-electricity-price/releases
[license-shield]: https://img.shields.io/github/license/bitosome/real-electricity-price.svg?style=for-the-badge
