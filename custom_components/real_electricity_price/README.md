# Real Electricity Price - Service Architecture v0.2.0

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.c#### `sensor.real_electricity_prices_today` → `Hourly Prices Today`
- **Purpose**: Contains all 24 hourly prices for today with comprehensive price data
- **Update Logic**: Returns the current hour's price
- **State**: Current hour price in EUR/kWh (including all costs)
- **Attributes**:
  - `hourly_prices`: Array of all 24 hourly prices for today
  - `date`: The date the data is for (YYYY-MM-DD format)

#### `sensor.real_electricity_prices_tomorrow` → `Hourly Prices Tomorrow`
- **Purpose**: Contains all 24 hourly prices for tomorrow with comprehensive price data
- **Update Logic**: Returns the first hour's price of the next day
- **State**: Tomorrow's first hour price in EUR/kWh (including all costs)
- **Attributes**:
  - `hourly_prices`: Array of all 24 hourly prices for tomorrow
  - `date`: The date the data is for (YYYY-MM-DD format)tion)

A **professional Home Assistant integration** for real-time electricity prices with a **Nord Pool-compatible service architecture**. Designed to present as a unified electricity price service similar to the popular Nord Pool integration.

## 🎯 **Service-Oriented Design**

This integration follows the **Nord Pool integration pattern**, creating a **single unified service** instead of multiple scattered entities:

```
🏠 Home Assistant
└── 🎛️ Your Electricity Price Service
    ├── 📊 Main Sensor (current price + comprehensive data)  
    └── 🔘 Manual Refresh Button
```

## ✨ **Key Features**

### 🎛️ **Professional Service Presentation**
- **Single unified device** with manufacturer branding and model info
- **Nord Pool-compatible** attribute structure for easy migration
- **Professional logo and branding** in the device view
- **Service-oriented approach** instead of entity-scattered data

### 📊 **Comprehensive Price Analytics**
- **Current hour price** as the main sensor value
- **Complete 24-hour arrays** for today and tomorrow in attributes
- **Statistical analysis**: average, min, max, peak/off-peak periods
- **Price comparison indicators**: percentage vs average, low-price alerts
- **Raw timestamp data** for advanced automations and charting

### ⚡ **Smart Automation Features**
- **Automatic hourly updates** when the hour changes
- **Manual refresh button** for instant data updates  
- **Configurable low-price thresholds** for automation triggers
- **Multiple country/region support** across Europe
- **Currency and tax handling** with additional cost calculations

## Installation

### HACS (Recommended)

1. Add this repository (`https://github.com/bitosome/real-electricity-price`) as a custom repository in HACS
2. Search for "Real Electricity Price" and install
3. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/real_electricity_price` folder from this repository
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

### Docker Test Environment

For development and testing, you can use the included Docker environment:

```bash
# Start test environment
./test_runner.sh start

# Access Home Assistant at http://localhost:8123
# Add the integration and test functionality

# View logs
./test_runner.sh logs

# Stop environment
./test_runner.sh stop
```

See [docker/README.md](docker/README.md) for detailed testing instructions.

### Dev Container (Recommended for Development)

For the best development experience, use the VS Code Dev Container:

1. **Prerequisites**: VS Code with Dev Containers extension, Docker Desktop
2. **Open project** in VS Code
3. **Reopen in Container**: Press `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"
4. **Wait for setup** (2-3 minutes for first launch)
5. **Access Home Assistant** at http://localhost:8123

**Benefits**:
- ✅ Live file synchronization - changes appear immediately
- ✅ Integrated debugging and testing tools
- ✅ Pre-configured Python environment and VS Code extensions
- ✅ No manual file copying needed

See [.devcontainer/README.md](.devcontainer/README.md) for detailed dev container instructions.

For icon/logo setup, see [BRANDING.md](BRANDING.md).

**❗ Logo/Icon Issue**: Integration icons come from the Home Assistant brands repository, not from local files. Your custom euro coin icon won't appear until you:
1. Convert your image to PNG (256×256 for icon.png, 512×512 for logo.png)
2. Fork https://github.com/home-assistant/brands
3. Create folder: `custom_integrations/real_electricity_price/`
4. Add your PNG files to that folder
5. Submit a Pull Request to the brands repository

**Until then**: The integration shows the default puzzle piece icon. This is normal for custom integrations without approved branding.

## Configuration

After installation, configure the integration through the Home Assistant UI:

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Real Electricity Price"
3. Configure the following parameters:

### Grid Parameters
- **Grid Provider**: Your electricity grid provider name (default: elektrilevi)
- **Electricity Excise Duty**: Grid's electricity excise duty in EUR/kWh (default: 0.0026)
- **Renewable Energy Charge**: Grid's renewable energy charge in EUR/kWh (default: 0.0104)
- **Transmission Price (Night)**: Night transmission price in EUR/kWh (default: 0.026)
- **Transmission Price (Day)**: Day transmission price in EUR/kWh (default: 0.0458)

### Supplier Parameters
- **Supplier**: Your electricity supplier name (default: eesti_energia)
- **Renewable Energy Charge**: Supplier's renewable energy charge in EUR/kWh (default: 0.00)
- **Margin**: Supplier's margin in EUR/kWh (default: 0.0105)

### Regional Settings
- **Country Code**: Country code for pricing (default: EE for Estonia)
- **VAT**: Value Added Tax percentage (default: 24%)
- **Night Price Start Hour**: Hour when night pricing starts (default: 22)
- **Night Price End Hour**: Hour when night pricing ends (default: 7)

### Update Settings
- **Scan Interval**: How often to fetch new data in seconds (default: 3600 = 1 hour, min: 300 = 5 minutes, max: 86400 = 24 hours)

## Sensors

The integration provides multiple sensors that update based on your configured scan interval:

### Core Price Sensors

#### `sensor.real_electricity_price_current_price` → `Current Price`
- **Purpose**: Shows the current hour's electricity price
- **Update Logic**: Automatically updates at the start of each hour
- **State**: Current hour's total price in EUR/kWh (including all costs)
- **Attributes**: Minimal current hour data only

#### `sensor.real_electricity_prices_today` → `Hourly Prices Today`
- **Purpose**: Contains all 24 hourly prices for today with comprehensive price data
- **Update Logic**: Returns the current hour's price based on UTC time
- **State**: Current hour's total price in EUR/kWh (including all costs)
- **Attributes**:
  - `hourly_prices`: Array of all 24 hourly prices for the day
  - `date`: The date the data is for (YYYY-MM-DD format)

#### `sensor.real_electricity_prices_tomorrow` → `Hourly Prices Tomorrow`
- **Purpose**: Contains all 24 hourly prices for tomorrow with comprehensive price data
- **Update Logic**: Returns the first hour's price of the next day
- **State**: Tomorrow's first hour price in EUR/kWh (including all costs)
- **Attributes**:
  - `hourly_prices`: Array of all 24 hourly prices for tomorrow
  - `date`: The date the data is for (YYYY-MM-DD format)

### Aggregate Sensors

These sensors provide quick min/max values for use in dashboards and automations:

- `sensor.real_electricity_price_max_today`: Maximum price for today (EUR/kWh)
- `sensor.real_electricity_price_min_today`: Minimum price for today (EUR/kWh)
- `sensor.real_electricity_price_max_tomorrow`: Maximum price for tomorrow (EUR/kWh)
- `sensor.real_electricity_price_min_tomorrow`: Minimum price for tomorrow (EUR/kWh)

### Control & Status Sensors

- `sensor.real_electricity_price_last_sync`: Shows when data was last successfully updated (timestamp)
- `sensor.real_electricity_price_current_tariff`: Shows current tariff period ("day" or "night")
- `button.real_electricity_price_refresh_data`: Manual refresh button to force data update

**💡 How it works**: When you press the refresh button, it triggers the coordinator to fetch new data from Nord Pool. Upon successful data retrieval, the `last_sync` sensor automatically updates to show the current timestamp, and all price sensors refresh with the latest data.

### Tariff Sensor Details

The **Current Tariff** sensor (`sensor.real_electricity_price_current_tariff`):
- **Values**: `"day"` or `"night"`
- **Icon**: Changes automatically (☀️ for day, 🌙 for night)
- **Logic**: Based on your configured night hours (default: 22:00-07:00)
- **Attributes**: Shows current hour and configured night/day hour boundaries
- **Usage**: Perfect for automations to schedule energy-intensive tasks during cheaper night hours

### Price Calculation Details

Each hourly price includes:
1. **Nord Pool Base Price**: Raw market price converted from EUR/MWh to EUR/kWh
2. **Grid Costs**:
   - Electricity excise duty
   - Renewable energy charge
   - Time-based transmission price (day/night rates)
3. **Supplier Costs**:
   - Renewable energy charge
   - Supplier margin
4. **Taxes**: VAT applied to the total price

### Time-Based Pricing Logic

The integration automatically applies different transmission rates based on:
- **Weekdays**: Day rate (07:00-22:00), Night rate (22:00-07:00)
- **Weekends**: Always night rate
- **Holidays**: Always night rate (uses Estonian holiday calendar)

## Usage Examples

### Basic Price Display
```yaml
# Display current electricity price
sensor:
  - platform: template
    sensors:
      current_price:
        friendly_name: "Current Electricity Price"
        unit_of_measurement: "EUR/kWh"
        value_template: "{{ states('sensor.real_electricity_price_current_price') }}"
        icon_template: "mdi:currency-eur"
```

### Price Monitoring Dashboard
```yaml
# Get tomorrow's first hour price
sensor:
  - platform: template
    sensors:
      tomorrow_first_hour:
        friendly_name: "Tomorrow First Hour Price"
        unit_of_measurement: "EUR/kWh"
        value_template: "{{ state_attr('sensor.real_electricity_prices_tomorrow', 'hourly_prices')[0].actual_price if state_attr('sensor.real_electricity_prices_tomorrow', 'hourly_prices') else 'N/A' }}"
```

### Automation Examples
```yaml
# High price warning
automation:
  - alias: "High Electricity Price Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.real_electricity_price_current_price
      above: 0.25  # EUR/kWh
    action:
      service: notify.notify
      data:
        message: "⚡ High electricity price: {{ states('sensor.real_electricity_price_current_price') }} EUR/kWh"

# Night time cheap energy notification
automation:
  - alias: "Cheap Night Energy Available"
    trigger:
      platform: time
      at: "22:00:00"
    condition:
      condition: numeric_state
      entity_id: sensor.real_electricity_price_current_price
      below: 0.15  # EUR/kWh
    action:
      service: notify.notify
      data:
        message: "🌙 Cheap night electricity available: {{ states('sensor.real_electricity_price_current_price') }} EUR/kWh"

# Start high-energy devices during night tariff
automation:
  - alias: "Auto Start Dishwasher During Night Tariff"
    trigger:
      platform: state
      entity_id: sensor.real_electricity_price_current_tariff
      to: "night"
    condition:
      - condition: numeric_state
        entity_id: sensor.real_electricity_price_current_price
        below: 0.20  # EUR/kWh
      - condition: state
        entity_id: switch.dishwasher_ready
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.dishwasher
      - service: notify.notify
        data:
          message: "🌙 Dishwasher started automatically during night tariff ({{ states('sensor.real_electricity_price_current_price') }} EUR/kWh)"

# Stop energy-intensive devices during expensive day hours
automation:
  - alias: "Pause EV Charging During Expensive Day Hours"
    trigger:
      platform: state
      entity_id: sensor.real_electricity_price_current_tariff
      to: "day"
    condition:
      condition: numeric_state
      entity_id: sensor.real_electricity_price_current_price
      above: 0.30  # EUR/kWh
    action:
      - service: switch.turn_off
        entity_id: switch.ev_charger
      - service: notify.notify
        data:
          message: "⚡ EV charging paused - expensive day rate: {{ states('sensor.real_electricity_price_current_price') }} EUR/kWh"
```

### Advanced Price Analysis
```yaml
# Calculate average daily price
sensor:
  - platform: template
    sensors:
      avg_daily_price:
        friendly_name: "Average Daily Price"
        unit_of_measurement: "EUR/kWh"
        value_template: >
          {% set prices = state_attr('sensor.real_electricity_prices_today', 'hourly_prices') %}
          {% if prices %}
            {{ (prices | map(attribute='actual_price') | list | sum / prices | length) | round(4) }}
          {% else %}
            unknown
          {% endif %}

# Tariff-aware cost calculation
sensor:
  - platform: template
    sensors:
      current_tariff_info:
        friendly_name: "Current Tariff Info"
        value_template: >
          {% set tariff = states('sensor.real_electricity_price_current_tariff') %}
          {% set price = states('sensor.real_electricity_price_current_price') %}
          {{ tariff | title }} Tariff: {{ price }} EUR/kWh
        icon_template: >
          {% if states('sensor.real_electricity_price_current_tariff') == 'night' %}
            mdi:weather-night
          {% else %}
            mdi:weather-sunny
          {% endif %}
        unit_of_measurement: "EUR/kWh"
        value_template: >
          {% set prices = state_attr('sensor.real_electricity_prices_today', 'hourly_prices') %}
          {% if prices %}
            {{ (prices | map(attribute='actual_price') | list | sum / prices | length) | round(4) }}
          {% else %}
            unknown
          {% endif %}
```

## Visualization with ApexCharts

The integration provides detailed hourly price data that can be beautifully visualized using the [ApexCharts Card](https://github.com/RomRider/apexcharts-card). Below are examples for displaying today's and tomorrow's electricity prices.

### Quick example (copy-paste)

```yaml
type: custom:apexcharts-card
graph_span: 24h
header:
  title: "Today's Electricity Prices (EUR/kWh)"
  show: true
span:
  start: day
now:
  show: true
  label: Now
yaxis:
  - min: 0
apex_config:
  xaxis:
    labels:
      format: HH:mm
      datetimeUTC: false
  tooltip:
    x:
      format: HH:mm
series:
  - entity: sensor.real_electricity_prices_today
    type: column
    float_precision: 4
    data_generator: |
      const prices = (entity.attributes.hourly_prices || []).map(h => h.actual_price).filter(v => typeof v === 'number');
      const arrMin = prices.length ? Math.min(...prices) : undefined;
      const arrMax = prices.length ? Math.max(...prices) : undefined;
      const sensMin = parseFloat(entities['sensor.real_electricity_price_min_today']?.state);
      const sensMax = parseFloat(entities['sensor.real_electricity_price_max_today']?.state);
      const min = Number.isFinite(arrMin) ? arrMin : (Number.isFinite(sensMin) ? sensMin : undefined);
      const max = Number.isFinite(arrMax) ? arrMax : (Number.isFinite(sensMax) ? sensMax : undefined);
      const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
      const lerp = (a, b, t) => a + (b - a) * t;
      const toColor = (t) => {
        // t in [0,1], 0 = green, 1 = red
        const r = Math.round(lerp(0, 255, t));
        const g = Math.round(lerp(170, 0, t));
        const b = 0;
        return `rgb(${r},${g},${b})`;
      };

      return (entity.attributes.hourly_prices || []).map(h => {
        const x = new Date(h.start_time).getTime();
        const y = h.actual_price;
        if (Number.isFinite(min) && Number.isFinite(max) && max > min) {
          const t = clamp((y - min) / (max - min), 0, 1);
          return { x, y, fillColor: toColor(t) };
        }
        return [x, y];
      });
```

### Simple version (no color coding)

```yaml
type: custom:apexcharts-card
graph_span: 24h
header:
  title: "Today's Electricity Prices (EUR/kWh)"
  show: true
span:
  start: day
now:
  show: true
  label: Now
yaxis:
  - min: 0
apex_config:
  xaxis:
    labels:
      format: HH:mm
      datetimeUTC: false
  tooltip:
    x:
      format: HH:mm
series:
  - entity: sensor.real_electricity_prices_today
    type: column
    float_precision: 4
    data_generator: |
      return (entity.attributes.hourly_prices || []).map(h => {
        return [new Date(h.start_time).getTime(), h.actual_price];
      });
```

### Prerequisites

Install the ApexCharts Card through HACS:
1. Go to HACS → Frontend
2. Search for "ApexCharts Card"
3. Install and add to resources

### Today's Hourly Prices Chart

```yaml
type: custom:apexcharts-card
graph_span: 24h
header:
  title: "Today's Electricity Prices (EUR/kWh)"
  show: true
span:
  start: day
now:
  show: true
  label: Now
yaxis:
  - min: 0
apex_config:
  xaxis:
    labels:
      format: HH:mm
      datetimeUTC: false
  tooltip:
    x:
      format: HH:mm
series:
  - entity: sensor.real_electricity_prices_today
    type: column
    float_precision: 4
    data_generator: |
      return entity.attributes.hourly_prices.map((hour) => {
        return [new Date(hour.start_time).getTime(), hour.actual_price];
      });
```

### Tomorrow's Hourly Prices Chart

```yaml
type: custom:apexcharts-card
graph_span: 24h
header:
  title: "Tomorrow's Electricity Prices (EUR/kWh)"
  show: true
span:
  start: day
  offset: +1d
yaxis:
  - min: 0
apex_config:
  xaxis:
    labels:
      format: HH:mm
      datetimeUTC: false
  tooltip:
    x:
      format: HH:mm
series:
  - entity: sensor.real_electricity_prices_tomorrow
    type: column
    float_precision: 4
    data_generator: |
      return entity.attributes.hourly_prices.map((hour) => {
        return [new Date(hour.start_time).getTime(), hour.actual_price];
      });
```

### Combined Today & Tomorrow Chart

```yaml
type: custom:apexcharts-card
graph_span: 48h
header:
  title: "Electricity Prices - Today & Tomorrow (EUR/kWh)"
  show: true
span:
  start: day
now:
  show: true
  label: Now
yaxis:
  - min: 0
apex_config:
  xaxis:
    labels:
      format: HH:mm
      datetimeUTC: false
  tooltip:
    x:
      format: dd/MM HH:mm
series:
  - entity: sensor.real_electricity_prices_today
    name: "Today"
    type: column
    color: '#1f77b4'
    float_precision: 4
    data_generator: |
      return entity.attributes.hourly_prices.map((hour) => {
        return [new Date(hour.start_time).getTime(), hour.actual_price];
      });
  - entity: sensor.real_electricity_prices_tomorrow
    name: "Tomorrow"
    type: column
    color: '#ff7f0e'
    float_precision: 4
    data_generator: |
      return entity.attributes.hourly_prices.map((hour) => {
        return [new Date(hour.start_time).getTime(), hour.actual_price];
      });
```

### Current Price with Trend

```yaml
type: custom:apexcharts-card
graph_span: 12h
header:
  title: "Current Price Trend (EUR/kWh)"
  show: true
span:
  start: hour
  offset: -6h
now:
  show: true
  label: Now
yaxis:
  - min: 0
series:
  - entity: sensor.real_electricity_price_current_price
    name: "Current Price"
    type: line
    stroke_width: 3
    float_precision: 4
    data_generator: |
      const now = new Date();
      const sixHoursAgo = new Date(now.getTime() - 6 * 60 * 60 * 1000);
      const sixHoursLater = new Date(now.getTime() + 6 * 60 * 60 * 1000);
      
      let data = [];
      
      // Add today's data
      if (entities['sensor.real_electricity_prices_today']?.attributes?.hourly_prices) {
        entities['sensor.real_electricity_prices_today'].attributes.hourly_prices.forEach(hour => {
          const hourTime = new Date(hour.start_time);
          if (hourTime >= sixHoursAgo && hourTime <= sixHoursLater) {
            data.push([hourTime.getTime(), hour.actual_price]);
          }
        });
      }
      
      // Add tomorrow's data if needed
      if (entities['sensor.real_electricity_prices_tomorrow']?.attributes?.hourly_prices) {
        entities['sensor.real_electricity_prices_tomorrow'].attributes.hourly_prices.forEach(hour => {
          const hourTime = new Date(hour.start_time);
          if (hourTime >= sixHoursAgo && hourTime <= sixHoursLater) {
            data.push([hourTime.getTime(), hour.actual_price]);
          }
        });
      }
      
      return data.sort((a, b) => a[0] - b[0]);
```

### Price Comparison Dashboard Card

```yaml
type: vertical-stack
cards:
  - type: custom:apexcharts-card
    graph_span: 24h
    header:
      title: "Price Comparison (EUR/kWh)"
      show: true
    span:
      start: day
    now:
      show: true
      label: Now
    yaxis:
      - min: 0
    series:
      - entity: sensor.real_electricity_prices_today
        name: "Today"
        type: line
        stroke_width: 2
        float_precision: 4
        data_generator: |
          return entity.attributes.hourly_prices.map((hour) => {
            return [new Date(hour.start_time).getTime(), hour.actual_price];
          });
      - entity: sensor.real_electricity_prices_tomorrow
        name: "Tomorrow"
        type: line
        stroke_width: 2
        float_precision: 4
        data_generator: |
          return entity.attributes.hourly_prices.map((hour) => {
            return [new Date(hour.start_time).getTime(), hour.actual_price];
          });
  - type: entities
    entities:
      - entity: sensor.real_electricity_price_current_price
        name: "Current Price"
      - entity: sensor.real_electricity_prices_today
        name: "Today's Average"
      - entity: sensor.real_electricity_prices_tomorrow
        name: "Tomorrow's First Hour"
```

### Price with Tariff Color Coding

```yaml
type: custom:apexcharts-card
graph_span: 48h
header:
  title: "Electricity Prices with Day/Night Tariff"
  show: true
span:
  start: day
now:
  show: true
  label: Now
yaxis:
  - min: 0
series:
  - entity: sensor.real_electricity_prices_today
    name: "Today"
    type: column
    float_precision: 4
    data_generator: |
      return entity.attributes.hourly_prices.map((hour) => {
        const color = hour.tariff === 'day' ? '#FF6B6B' : '#4ECDC4';
        return {
          x: new Date(hour.start_time).getTime(),
          y: hour.actual_price,
          fillColor: color,
          strokeColor: color
        };
      });
  - entity: sensor.real_electricity_prices_tomorrow
    name: "Tomorrow"
    type: column
    float_precision: 4
    data_generator: |
      if (!entity.attributes?.hourly_prices) return [];
      return entity.attributes.hourly_prices.map((hour) => {
        const color = hour.tariff === 'day' ? '#FF6B6B' : '#4ECDC4';
        return {
          x: new Date(hour.start_time).getTime(),
          y: hour.actual_price,
          fillColor: color,
          strokeColor: color
        };
      });
```

**Color Legend:**
- 🔴 Red: Day tariff (Peak hours: 06:00-18:00 UTC)
- 🔵 Blue: Night tariff (Off-peak hours, weekends, holidays)

### Chart Customization Tips

- **Colors**: Modify the `color` property to match your dashboard theme
- **Time Ranges**: Adjust `graph_span` and `span` settings for different views
- **Chart Types**: Use `line`, `column`, or `area` for different visualizations
- **Precision**: Set `float_precision` to control decimal places shown
- **Y-Axis**: Configure `min`/`max` values to focus on relevant price ranges

## Data Source

This integration fetches data from the **Nord Pool Day-Ahead market API**. Nord Pool is Europe's leading power exchange, providing transparent electricity price information across multiple countries.

- **API Endpoint**: `https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices`
- **Market**: Day-ahead market prices
- **Currency**: EUR (Euros)
- **Delivery Area**: EE (Estonia)
- **Update Frequency**: Configurable (default: every hour)

## Technical Details

- **Dependencies**: `holidays>=0.21` for Estonian holiday detection
- **API Client**: Async HTTP client with timeout and error handling
- **Data Processing**: Automatic price conversion and cost calculation
- **Time Zone**: UTC for all time calculations
- **Price Precision**: 6 decimal places for accuracy
- **Error Handling**: Comprehensive error handling for API failures

## Troubleshooting

### Common Issues

1. **Integration won't load**: Check Home Assistant logs for import errors
2. **No data available**: Verify Nord Pool API is accessible and credentials are correct
3. **Wrong prices**: Double-check your grid and supplier parameters
4. **Missing tomorrow's data**: Tomorrow's data becomes available around 14:00 CET

### Debug Information

Enable debug logging by adding this to your `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.real_electricity_price: debug
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a Pull Request

### Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -r requirements.txt`
3. Run linting: `python -m ruff check custom_components/real_electricity_price/`
4. Test in your Home Assistant development environment

### Docker Testing Environment

For easy testing and development:

```bash
# Start the test environment
./test_runner.sh start

# Run integration tests
./test_runner.sh test

# View live logs
./test_runner.sh logs

# Reset environment
./test_runner.sh reset
```

The Docker environment includes:
- Latest Home Assistant with the integration pre-mounted
- Debug logging enabled
- Test dashboard with price monitoring
- Estonian timezone and locale settings
- All dependencies pre-installed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/bitosome/real-electricity-price/issues)
- **Documentation**: [GitHub Wiki](https://github.com/bitosome/real-electricity-price/wiki)
- **HACS**: Install via [HACS](https://hacs.xyz/)

## Credits

- **Nord Pool**: For providing the electricity price data API
- **Home Assistant**: For the amazing smart home platform
- **HACS**: For making custom integration installation easy
