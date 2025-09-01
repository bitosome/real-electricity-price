# Real Electricity Price Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A comprehensive Home Assistant integration for real-time electricity pricing from Nord Pool, with configurable grid costs and supplier charges for Nord Pool market areas.

## Version

Current version: v1.0.0

## Highlights
- Unified hourly refresh at hh:00 for all sensors, in sync with manual refresh
- Manual refresh button triggers immediate coordinator update for all entities
- Removed unused “Current hour” attribute from Current Tariff sensor
- Fixed timezone handling using Home Assistant local time

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
If you see only one entity instead of 5 (4 sensors + 1 button):

1. **Check Entity List**: Go to Settings → Devices & Services → Entities, search for "real_electricity_price"
2. **Check Device View**: Go to Settings → Devices & Services → Real Electricity Price → Click the device
3. **Check Developer Tools**: Go to Developer Tools → States, search for "real_electricity_price"
4. **Verify All Entities**:
   - `sensor.real_electricity_price_current_price`
   - `sensor.real_electricity_price_hourly_prices`
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
- **Weekend and holiday detection** for selected country calendar

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
| **Hourly Prices** | `sensor.real_electricity_price_hourly_prices` | Complete price array for 3 days (yesterday, today, tomorrow) | EUR/kWh | Hourly |
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
  - All additional cost components with their current values
  - `tariff`: Current tariff (day/night)
  - `is_holiday`: Whether current date is a holiday
  - `is_weekend`: Whether current date is a weekend

### Hourly Prices Sensor

The hourly prices sensor provides:
- **State**: Current hour price
- **Attributes**:
  - `hourly_prices`: Array of all hourly price objects from yesterday, today, and tomorrow
  - `data_sources`: List of available data keys (yesterday, today, tomorrow)

Each hourly price object contains:
```json
{
  "start_time": "2025-08-31T19:00:00Z",
  "end_time": "2025-08-31T20:00:00Z",
  "nord_pool_price": 0.14131,
  "actual_price": 0.236604,
  "tariff": "night",
  "is_holiday": false,
  "is_weekend": true
}
```

### Current Tariff Sensor

Shows the current pricing period:
- **night**: Off-peak hours, weekends, holidays
- **day**: Peak hours on business days (based on Nord Pool blocks)

The tariff determination follows this logic:
1. **Weekends/Holidays**: Always "night" tariff
2. **Business days**: Based on Nord Pool block aggregates:
   - "Peak" blocks → "day" tariff
   - All other blocks → "night" tariff

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

### Country Support

This integration supports all Nord Pool market areas, including specific regional areas. Simply set the **Area Code** during setup:

| Country | Area Codes | Default Grid | Default Supplier | VAT % |
|---------|------------|--------------|------------------|-------|
| Estonia | EE | elektrilevi | eesti_energia | 24.0% |
| Finland | FI | (configurable) | (configurable) | 25.5% |
| Latvia | LV | (configurable) | (configurable) | 21.0% |
| Lithuania | LT | (configurable) | (configurable) | 21.0% |
| Sweden | SE1, SE2, SE3, SE4 | (configurable) | (configurable) | 25.0% |
| Norway | NO1, NO2, NO3, NO4, NO5 | (configurable) | (configurable) | 25.0% |
| Denmark | DK1, DK2 | (configurable) | (configurable) | 25.0% |

**Note**: 
- For countries with multiple areas (SE1-SE4, NO1-NO5, DK1-DK2), specify the exact area code for accurate pricing
- Holiday detection automatically uses the country part (e.g., "SE" from "SE1") 
- Default values are Estonian-focused since this integration was initially developed for Estonia

**Area Code vs Holiday Detection:**
- **Nord Pool API**: Uses the full area code (e.g., "SE1", "NO2") for pricing data
- **Holiday Detection**: Automatically extracts the country code (e.g., "SE", "NO") for calendar-based features

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
- **Area Code**: Nord Pool market area (EE, FI, SE1, SE2, NO1, NO2, DK1, DK2, etc.)
- **VAT**: Value Added Tax percentage (default: 24.0%)
- **Night Start Hour**: When night tariff begins (default: 22)
- **Night End Hour**: When night tariff ends (default: 7)

### Configuration Example

```yaml
# Example configuration.yaml entry (optional - UI configuration recommended)
# This integration is primarily configured through the UI
real_electricity_price:
  name: "My Electricity Price"
  grid: "elektrilevi"
  supplier: "eesti_energia"
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
      - name: "Tomorrow First Hour Price"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices', 'hourly_prices') %}
          {% set tomorrow_prices = prices | selectattr('start_time', 'match', '^' + (now() + timedelta(days=1)).strftime('%Y-%m-%d') + 'T00:00:00') | list %}
          {{ tomorrow_prices[0].actual_price if tomorrow_prices else 'N/A' }}
        unit_of_measurement: "EUR/kWh"

      - name: "Average Price Today"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices', 'hourly_prices') %}
          {% set today_prices = prices | selectattr('start_time', 'match', '^' + now().strftime('%Y-%m-%d') + 'T') | list %}
          {% if today_prices %}
            {{ (today_prices | map(attribute='actual_price') | list | sum / today_prices | length) | round(4) }}
          {% else %}
            unavailable
          {% endif %}
        unit_of_measurement: "EUR/kWh"

      - name: "Max Price Today"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices', 'hourly_prices') %}
          {% set today_prices = prices | selectattr('start_time', 'match', '^' + now().strftime('%Y-%m-%d') + 'T') | list %}
          {% if today_prices %}
            {{ today_prices | map(attribute='actual_price') | max }}
          {% else %}
            unavailable
          {% endif %}
        unit_of_measurement: "EUR/kWh"

      - name: "Min Price Today"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices', 'hourly_prices') %}
          {% set today_prices = prices | selectattr('start_time', 'match', '^' + now().strftime('%Y-%m-%d') + 'T') | list %}
          {% if today_prices %}
            {{ today_prices | map(attribute='actual_price') | min }}
          {% else %}
            unavailable
          {% endif %}
        unit_of_measurement: "EUR/kWh"
```

### Lovelace Cards

#### Simple Price Display

```yaml
type: entities
title: "Electricity Price"
entities:
  - sensor.real_electricity_price_current_price
  - sensor.real_electricity_price_current_tariff
  - sensor.real_electricity_price_hourly_prices
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

For ApexCharts Card (latest recommended):

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: "📊 Electricity Prices (72h)"
  show_states: true
  colorize_states: true
chart_type: line
graph_span: 72h
span:
  end: day
now:
  show: true
  color: "#FF6B6B"
  label: "Now"
apex_config:
  chart:
    height: 350
    animations:
      enabled: true
      easing: easeinout
      speed: 800
  theme:
    mode: dark
  grid:
    show: true
    borderColor: "#404040"
  tooltip:
    theme: dark
    shared: true
    x:
      format: "MMM dd, HH:mm"
  xaxis:
    type: datetime
    labels:
      format: "HH:mm"
      datetimeUTC: false
  yaxis:
    - title:
        text: "Price (€/kWh)"
      labels:
        formatter: |
          EVAL:function(value) {
            return value?.toFixed(4) + " €";
          }
      min: 0
  annotations:
    xaxis:
      - x: EVAL:new Date().getTime()
        borderColor: "#FF6B6B"
        label:
          text: "Current Time"
          style:
            color: "#fff"
            background: "#FF6B6B"
all_series_config:
  stroke_width: 3
  curve: stepline
  opacity: 0.8
series:
  - entity: sensor.real_electricity_price_hourly_prices
    type: column
    name: "💡 Electricity Price"
    color: "#4ECDC4"
    data_generator: |
      const prices = entity.attributes.hourly_prices || [];
      const now = new Date();
      
      return prices.map((hour) => {
        const startTime = new Date(hour.start_time);
        const endTime = new Date(hour.end_time);
        const price = hour.actual_price;
        
        // Color coding based on price level and availability
        let color = "#4ECDC4"; // Default blue-green
        
        if (price === null) {
          color = "#95A5A6"; // Gray for unavailable data
        } else if (price < 0.10) {
          color = "#2ECC71"; // Green for very cheap
        } else if (price < 0.15) {
          color = "#F39C12"; // Orange for moderate
        } else if (price < 0.25) {
          color = "#E74C3C"; // Red for expensive  
        } else {
          color = "#8E44AD"; // Purple for very expensive
        }
        
        return {
          x: startTime.getTime(),
          y: price,
          fillColor: color,
          strokeColor: color,
          meta: {
            tariff: hour.tariff,
            nord_pool_price: hour.nord_pool_price,
            is_current: now >= startTime && now < endTime
          }
        };
      }).filter(point => point.y !== null); // Remove unavailable data points
  - entity: sensor.real_electricity_price
    type: line
    name: "🎯 Current Price"
    color: "#FF6B6B"
    stroke_width: 4
    show:
      in_header: true
      name_in_header: false
    data_generator: |
      const currentPrice = parseFloat(entity.state);
      const now = new Date();
      return [[now.getTime(), currentPrice]];
```

## API Information

### Data Source
- **Provider**: Nord Pool (Europe's leading power exchange)
- **API**: `https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices`
- **Market**: Day-ahead electricity market
- **Area**: Configurable (EE, FI, SE1, SE2, NO1, NO2, DK1, DK2, etc.)
- **Currency**: EUR
- **Data Range**: 3 days (yesterday, today, tomorrow)
- **Update Schedule**: Hourly updates, with tomorrow's data available around 14:00 CET

### Price Calculation

The integration calculates the final price by adding various components to the base Nord Pool price:

```
Final Price = (Nord Pool Price + Grid Costs + Supplier Costs) × (1 + VAT%)
```

Where:
- **Nord Pool Price**: Base market price (EUR/MWh → EUR/kWh)
- **Grid Costs**: Excise duty + Renewable charge + Transmission (day/night)
- **Supplier Costs**: Renewable charge + Margin
- **VAT**: Value Added Tax (varies by country, e.g., 24% in Estonia, 25.5% in Finland)

### Tariff Logic

The system determines day/night tariffs based on **local time in the configured country**:

1. **Country Timezone**: Automatic timezone conversion with DST support based on area code
2. **Night Tariff Hours**: Configurable hours (default: 22:00 to 07:00 local time)
3. **Weekends and Holidays**: Always night tariff (based on country calendar from area code)
4. **Weekdays**: Time-based tariff switching at configured hours

**Example (EE - Estonia)**: At 07:30 Estonian time on a weekday → Day tariff
**Example (SE1 - Sweden South)**: At 23:00 Swedish time on any day → Night tariff  
**Example (NO1 - Norway East)**: Saturday 15:00 Norwegian time → Night tariff (weekend)

This provides accurate electricity pricing according to local tariff rules for the selected Nord Pool market area.

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
3. Validate regional settings (area code - ensure you're using the correct Nord Pool area)
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
- Grid operators and electricity suppliers in Nord Pool areas for transparent pricing information

## Support

- **Issues**: [GitHub Issues](https://github.com/bitosome/real-electricity-price/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bitosome/real-electricity-price/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

---

**Disclaimer**: This integration is not officially affiliated with Nord Pool or any electricity suppliers. Price data is provided as-is for informational purposes. Always verify prices with your official electricity bill.

[releases-shield]: https://img.shields.io/github/release/bitosome/real-electricity-price.svg?style=for-the-badge
[releases]: https://github.com/bitosome/real-electricity-price/releases
[license-shield]: https://img.shields.io/github/license/bitosome/real-electricity-price.svg?style=for-the-badge
