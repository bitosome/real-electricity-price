# Real Electricity Price Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![Tests](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml/badge.svg)](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml)
[![License][license-shield]](LICENSE)

A comprehensive Home Assistant integration for real-time electricity pricing from Nord Pool, with advanced cheap price analysis and configurable grid costs for all Nord Pool market areas.

## Version

Current version: v2.0.0

## Latest Features (v1.1.0)
- **NEW**: Advanced Cheapest Prices sensor with pandas-powered analysis
- **NEW**: Configurable cheap price threshold (percentage above minimum price)
- **NEW**: Smart time range grouping for consecutive cheap hours
- **NEW**: Separate coordinator architecture for optimized performance
- **NEW**: Time-based triggers for cheap price calculations (default: 14:30)
- **NEW**: Two service calls for manual data refresh and cheap price recalculation
- **NEW**: Calculate Cheap Hours button for manual price analysis
- **ENHANCED**: Rich sensor attributes with detailed price statistics and analysis infoy Price Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A comprehensive Home Assistant integration for real-time electricity pricing from Nord Pool, with configurable grid costs and supplier charges for Nord Pool market areas.

## Version

Current version: v2.0.0

## Highlights
- Unified hourly refresh at hh:00 for all sensors, in sync with manual refresh
- Manual refresh button triggers immediate coordinator update for all entities
- Removed unused “Current hour” attribute from Current Tariff sensor
- Fixed timezone handling using Home Assistant local time

## Features

### 🏠 Unified Se### Common Issues

### Common Issues

#### Integration Won't Load
```bash
# Check logs for import errors
grep -i "real_electricity_price" /config/home-assistant.log
```

#### No Data Available
1. Verify internet connection and Nord Pool API accessibility
2. Check configuration parameters (area code, API settings)
3. Look for API errors in integration logs
4. Try manual refresh using the "Refresh Data" button

#### Incorrect Prices
1. Verify grid and supplier parameters in configuration
2. Check VAT percentage for your country
3. Validate regional settings (ensure correct Nord Pool area code)
4. Compare calculated prices with official electricity bill

#### Missing Tomorrow's Data
- Tomorrow's prices are published around 14:00 CET
- Check if integration has been updated recently
- Manual refresh may be needed after 14:00
- Cheap price calculations automatically trigger at 14:30 (configurable)

#### Cheapest Prices Sensor Not Updating
1. Check if cheap price threshold is reasonable (default: 10%)
2. Verify trigger time configuration (default: 14:30)
3. Try manual recalculation using "Calculate Cheap Hours" button
4. Check if pandas dependency is installed (`pandas>=1.3.0`)

#### Only Seeing Some Entities
If you see only some entities instead of all 6 sensors + 2 buttons:

1. **Check Entity List**: Settings → Devices & Services → Entities, search for "real_electricity_price"
2. **Check Device View**: Settings → Devices & Services → Real Electricity Price → Click the device
3. **Check Developer Tools**: Developer Tools → States, search for "real_electricity_price"
4. **Verify All Entities**:
   - `sensor.real_electricity_price_current_price`
   - `sensor.real_electricity_price_hourly_prices`
   - `sensor.real_electricity_price_last_sync`
   - `sensor.real_electricity_price_last_cheap_calculation`
   - `sensor.real_electricity_price_current_tariff`
   - `sensor.real_electricity_price_cheap_prices`
   - `button.real_electricity_price_refresh_data`
   - `button.real_electricity_price_calculate_cheap_hours`
5. **Force Refresh**: Restart Home Assistant or reload the integration
### 🏠 Modern Architecture
- **Dual coordinator design** with independent update schedules
- **Main coordinator** for price data (hourly updates)
- **Cheap price coordinator** for analysis (time-triggered)
- **Professional device grouping** with comprehensive sensor suite
- **Service-based control** for manual updates and calculations
- **Optimized performance** with separate analysis pipeline

### 📊 Comprehensive Price Monitoring
- **Current price sensor** with real-time hourly updates
- **Daily price arrays** for today and tomorrow
- **Min/Max aggregates** for both today and tomorrow
- **Last sync tracking** for data freshness monitoring
- **Current tariff detection** (day/night/weekend/holiday)

### ⚡ Smart Automation Ready
### ⚡ Smart Automation Ready
- **Dual update system** with independent coordinators
- **Manual control buttons** for instant data refresh and cheap price recalculation  
- **Rich sensor attributes** with comprehensive price breakdowns and metadata
- **Time-triggered analysis** for optimal cheap period detection
- **Service calls** for automation integration
- **Timezone-aware** tariff detection using Home Assistant local time
- **Weekend and holiday detection** for automatic night tariff application

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
| **Hourly Prices** | `sensor.real_electricity_price_hourly_prices` | Complete price array for up to 3 days (yesterday, today, tomorrow) | EUR/kWh | Hourly |
| **Last Data Sync** | `sensor.real_electricity_price_last_sync` | Timestamp of last successful data update | Timestamp | On each update |
| **Last Cheap Price Calculation** | `sensor.real_electricity_price_last_cheap_calculation` | Timestamp of last cheap price analysis | Timestamp | On cheap price calculation |
| **Current Tariff** | `sensor.real_electricity_price_current_tariff` | Current pricing period (day/night) based on local time | Text | Real-time |
| **Cheapest Prices** | `sensor.real_electricity_price_cheap_prices` | Advanced analysis of cheapest time periods with configurable threshold | EUR/kWh | Time-triggered (default: 14:30) |

### Buttons

| Button | Entity ID | Description | Function |
|--------|-----------|-------------|----------|
| **Refresh Data** | `button.real_electricity_price_refresh_data` | Manual refresh of price data | Triggers immediate API update |
| **Calculate Cheap Hours** | `button.real_electricity_price_calculate_cheap_hours` | Manual cheap price analysis | Recalculates cheap periods immediately |

### Cheapest Prices Sensor

**NEW in v1.1.0** - Advanced price analysis to identify optimal electricity usage periods:

- **State**: Nearest cheap price (current if in a cheap period, or next upcoming cheap price)
- **Device Class**: Monetary (EUR/kWh)
- **Icon**: `mdi:currency-eur-off`
- **Update Schedule**: Time-triggered (configurable, default: 14:30)

#### Key Features
- **Smart Analysis**: Uses pandas for efficient price data analysis
- **Configurable Threshold**: Set percentage above minimum price (default: 10%)
- **Time Range Grouping**: Groups consecutive cheap hours into periods
- **Independent Updates**: Separate coordinator for optimized performance
- **Current Status**: Knows if you're currently in a cheap period
- **Future-Focused**: Analyzes from current hour onwards only

#### Cheap Price Definition
- **Cheapest price**: The absolute minimum price in all available data
- **Other cheap prices**: Prices within X% of the minimum price, where X is configurable
- **Example**: If minimum price is 0.10 EUR/kWh and threshold is 10%, then all prices ≤ 0.11 EUR/kWh are considered cheap

#### Rich Attributes
```json
{
  "cheap_price_ranges": [
    {
      "start_time": "2025-09-01T02:00:00Z",
      "end_time": "2025-09-01T06:00:00Z", 
      "price": 0.105,
      "min_price": 0.100,
      "max_price": 0.110,
      "avg_price": 0.106,
      "hour_count": 4
    }
  ],
  "status_info": {
    "current_status": "in_cheap_period",
    "total_cheap_hours": 8,
    "next_cheap_period": {
      "start_time": "2025-09-01T22:00:00Z",
      "average_price": 0.098
    }
  },
  "analysis_info": {
    "threshold_percent": 10.0,
    "min_price": 0.100,
    "max_cheap_price": 0.110
  }
}
```

### Current Price Sensor

The main sensor provides:
- **State**: Current hour price in EUR/kWh (all costs included)
- **Attributes**:
  - `current_hour_info`: Current hour details (date, start/end times, Nord Pool price, tariff)
  - `price_components`: Complete breakdown of all cost components (grid, supplier, tax)

### Hourly Prices Sensor

The hourly prices sensor provides:
- **State**: Current hour price
- **Attributes**:
  - `hourly_prices`: Array of all hourly price objects from available data
  - `data_sources`: List of available data keys (yesterday, today, tomorrow)
  - `data_sources_info`: Detailed information about each data source

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
- **day**: Peak hours on business days (based on local time)

The tariff determination follows this logic:
1. **Weekends/Holidays**: Always "night" tariff
2. **Business days**: Based on configured night hours (default: 22:00-07:00 local time)
3. **Timezone-aware**: Uses Home Assistant's configured timezone

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

#### Cheap Price Analysis
- **Cheap Price Threshold**: Percentage above minimum price to consider "cheap" (default: 10.0%)
  - Example: If minimum price is 0.10 EUR/kWh and threshold is 10%, then prices ≤ 0.11 EUR/kWh are considered cheap
  - Used by the Cheapest Prices sensor to identify optimal time periods
- **Cheap Price Update Trigger**: Time when daily cheap price calculation runs (default: "14:30")
  - Automatically recalculates when tomorrow's prices become available
  - Can be configured to any time in HH:MM format

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

## Services

The integration provides two services for manual control:

### Refresh Data Service
- **Service**: `real_electricity_price.refresh_data`
- **Purpose**: Manually refresh electricity price data from Nord Pool API
- **Usage**: Updates all main sensors (current price, hourly prices, tariff, sync status)
- **Trigger**: Can be called via service call, automation, or "Refresh Data" button

### Recalculate Cheap Prices Service
- **Service**: `real_electricity_price.recalculate_cheap_prices`
- **Purpose**: Manually recalculate cheap price periods based on current configuration
- **Usage**: Updates the Cheapest Prices sensor immediately
- **Trigger**: Can be called via service call, automation, or "Calculate Cheap Hours" button

### Service Usage Examples

```yaml
# Manual refresh of price data
service: real_electricity_price.refresh_data

# Manual recalculation of cheap prices
service: real_electricity_price.recalculate_cheap_prices

# Automation to refresh prices at specific times
automation:
  - alias: "Refresh prices at 14:00"
    trigger:
      - platform: time
        at: "14:00:00"
    action:
      - service: real_electricity_price.refresh_data
      
  - alias: "Recalculate cheap prices after refresh"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_last_sync
    action:
      - delay: "00:01:00"  # Wait a minute after data refresh
      - service: real_electricity_price.recalculate_cheap_prices
```

## Usage Examples

### Automations for Cheap Electricity Periods

```yaml
# Get notified when cheap electricity period starts
automation:
  - alias: "Notify cheap electricity period"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_cheap_prices
        attribute: current_status
        to: "in_cheap_period"
    action:
      - service: notify.mobile_app
        data:
          title: "⚡ Cheap Electricity!"
          message: >
            Cheap period started! Price: {{ states('sensor.real_electricity_price_cheap_prices') }} EUR/kWh
            Period ends: {{ state_attr('sensor.real_electricity_price_cheap_prices', 'cheap_price_ranges')[0].end_time | as_datetime | as_local }}

# Start energy-intensive devices during cheap periods
automation:
  - alias: "Auto washing machine during cheap hours"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_cheap_prices
        attribute: current_status
        to: "in_cheap_period"
    condition:
      - condition: state
        entity_id: switch.washing_machine
        state: "off"
      - condition: time
        after: "06:00:00"
        before: "22:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.washing_machine
      - service: notify.mobile_app
        data:
          message: "🧺 Washing machine started during cheap electricity period"

# Set up EV charging during cheapest hours
automation:
  - alias: "EV charging during cheapest hours"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_cheap_prices
        attribute: current_status
        to: "in_cheap_period"
    condition:
      - condition: numeric_state
        entity_id: sensor.car_battery_level
        below: 80
      - condition: state
        entity_id: device_tracker.car
        state: "home"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.ev_charger
```

### Template Sensors

Create custom sensors in your `configuration.yaml`:

```yaml
template:
  - sensor:
      # Check if currently in cheap price period
      - name: "Is Cheap Electricity Period"
        state: >
          {% set status = state_attr('sensor.real_electricity_price_cheap_prices', 'status_info') %}
          {{ status.current_status == 'in_cheap_period' if status else false }}
        icon: >
          {% set status = state_attr('sensor.real_electricity_price_cheap_prices', 'status_info') %}
          {% if status and status.current_status == 'in_cheap_period' %}
            mdi:lightning-bolt
          {% else %}
            mdi:lightning-bolt-outline
          {% endif %}

      # Next cheap period countdown
      - name: "Next Cheap Period In"
        state: >
          {% set status = state_attr('sensor.real_electricity_price_cheap_prices', 'status_info') %}
          {% if status and status.next_cheap_period %}
            {% set next_start = status.next_cheap_period.start_time | as_datetime %}
            {% set diff = (next_start - now()).total_seconds() %}
            {% if diff > 3600 %}
              {{ (diff / 3600) | round(1) }} hours
            {% elif diff > 60 %}
              {{ (diff / 60) | round(0) }} minutes
            {% else %}
              Now
            {% endif %}
          {% else %}
            Unknown
          {% endif %}
        icon: "mdi:clock-outline"

      # Tomorrow's cheapest hour
      - name: "Tomorrow Cheapest Hour Price"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices', 'hourly_prices') %}
          {% set tomorrow_prices = prices | selectattr('start_time', 'match', '^' + (now() + timedelta(days=1)).strftime('%Y-%m-%d') + 'T') | list %}
          {% if tomorrow_prices %}
            {{ (tomorrow_prices | map(attribute='actual_price') | min) | round(4) }}
          {% else %}
            unavailable
          {% endif %}
        unit_of_measurement: "EUR/kWh"

      # Current day price statistics
      - name: "Today Average Price"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices', 'hourly_prices') %}
          {% set today_prices = prices | selectattr('start_time', 'match', '^' + now().strftime('%Y-%m-%d') + 'T') | list %}
          {% if today_prices %}
            {{ (today_prices | map(attribute='actual_price') | list | sum / today_prices | length) | round(4) }}
          {% else %}
            unavailable
          {% endif %}
        unit_of_measurement: "EUR/kWh"

      - name: "Today Price Range"
        state: >
          {% set prices = state_attr('sensor.real_electricity_price_hourly_prices', 'hourly_prices') %}
          {% set today_prices = prices | selectattr('start_time', 'match', '^' + now().strftime('%Y-%m-%d') + 'T') | list %}
          {% if today_prices %}
            {% set price_list = today_prices | map(attribute='actual_price') | list %}
            {{ (price_list | max - price_list | min) | round(4) }}
          {% else %}
            unavailable
          {% endif %}
        unit_of_measurement: "EUR/kWh"
```

### Lovelace Cards

### Lovelace Cards

#### Simple Price Display with Cheap Period Status

```yaml
type: entities
title: "💡 Electricity Price Monitor"
entities:
  - entity: sensor.real_electricity_price_current_price
    name: "Current Price"
  - entity: sensor.real_electricity_price_current_tariff
    name: "Current Tariff"
  - entity: sensor.real_electricity_price_cheap_prices
    name: "Cheap Price Status"
  - entity: sensor.is_cheap_electricity_period
    name: "In Cheap Period"
  - entity: sensor.next_cheap_period_in
    name: "Next Cheap Period"
  - type: divider
  - entity: sensor.real_electricity_price_last_sync
    name: "Last Data Update"
  - entity: sensor.real_electricity_price_last_cheap_calculation
    name: "Last Cheap Calculation"
  - type: divider
  - entity: button.real_electricity_price_refresh_data
    name: "Refresh Prices"
  - entity: button.real_electricity_price_calculate_cheap_hours
    name: "Recalculate Cheap Hours"
```

#### Cheap Price Timeline Card

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: "⚡ Electricity Price Timeline - Next 48h"
  show_states: true
  colorize_states: true
chart_type: column
graph_span: 48h
span:
  start: hour
now:
  show: true
  color: "#FF6B6B"
  label: "Now"
apex_config:
  chart:
    height: 400
  theme:
    mode: dark
  grid:
    show: true
    borderColor: "#404040"
  tooltip:
    theme: dark
    shared: true
    x:
      format: "ddd, MMM dd, HH:mm"
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
  stroke_width: 2
  opacity: 0.9
series:
  - entity: sensor.real_electricity_price_hourly_prices
    type: column
    name: "💡 Electricity Price"
    color: "#4ECDC4"
    data_generator: |
      const prices = entity.attributes.hourly_prices || [];
      const now = new Date();
      const currentTime = now.getTime();
      
      // Get cheap price ranges for highlighting
      const cheapPricesEntity = hass.states['sensor.real_electricity_price_cheap_prices'];
      const cheapRanges = cheapPricesEntity?.attributes?.cheap_price_ranges || [];
      
      // Create a map of cheap periods for quick lookup
      const cheapPeriods = new Map();
      cheapRanges.forEach(range => {
        const start = new Date(range.start_time).getTime();
        const end = new Date(range.end_time).getTime();
        for (let time = start; time < end; time += 3600000) { // 1 hour intervals
          cheapPeriods.set(time, true);
        }
      });
      
      return prices.map((hour) => {
        const startTime = new Date(hour.start_time);
        const price = hour.actual_price;
        
        if (price === null) return null; // Skip unavailable data
        
        // Color coding based on cheap periods and price levels
        let color = "#4ECDC4"; // Default blue-green
        
        const isCheap = cheapPeriods.has(startTime.getTime());
        const isCurrent = startTime.getTime() <= currentTime && currentTime < new Date(hour.end_time).getTime();
        
        if (isCheap) {
          color = "#2ECC71"; // Green for cheap periods
        } else if (price < 0.10) {
          color = "#F39C12"; // Orange for low prices
        } else if (price < 0.15) {
          color = "#E67E22"; // Orange for moderate prices
        } else if (price < 0.25) {
          color = "#E74C3C"; // Red for expensive  
        } else {
          color = "#8E44AD"; // Purple for very expensive
        }
        
        // Highlight current hour
        if (isCurrent) {
          color = "#FF6B6B"; // Red for current hour
        }
        
        return {
          x: startTime.getTime(),
          y: price,
          fillColor: color,
          strokeColor: color
        };
      }).filter(point => point !== null);
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

### Dependencies
- Python 3.11+
- Home Assistant 2025.1+
- Dependencies: `aiohttp`, `holidays>=0.21`, `pandas>=1.3.0`

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

3. Install Podman and podman-compose:
   ```bash
   # macOS
   brew install podman
   pip install podman-compose
   
   # Linux (example for Ubuntu/Debian)
   sudo apt-get install podman
   pip install podman-compose
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Testing

The project includes comprehensive testing support with **53+ individual tests** covering all functionality:

#### Automated Testing (GitHub Actions)
- **Continuous Integration**: All tests run automatically on every push/PR
- **Multi-Python Support**: Tests on Python 3.11, 3.12, and 3.13
- **Test Categories**: Configuration validation, sensor calculations, button functionality, integration scenarios
- **Coverage**: [![Tests](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml/badge.svg)](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml)

#### Local Testing
```bash
# Run all tests
cd tests && ./test.sh

# Run comprehensive test suite
python tests/test_all_comprehensive.py

# Run specific test categories
python tests/test_all_comprehensive.py --config    # Configuration tests
python tests/test_all_comprehensive.py --sensors   # Sensor calculation tests  
python tests/test_all_comprehensive.py --buttons   # Button functionality tests
```

#### One-Click Development Environment

```bash
# Start complete development environment (recommended)
./scripts/dev-setup.sh

# This automatically:
# - Sets up Podman containers
# - Installs HACS
# - Syncs integration files
# - Starts Home Assistant with everything configured
```

#### Podman Test Environment

```bash
# Start test environment with one command
./scripts/dev-setup.sh

# This automatically:
# - Sets up Podman containers  
# - Installs HACS
# - Syncs integration files
# - Starts Home Assistant with everything configured
# - Provides proxy access on port 8080

# Access Home Assistant at http://localhost:8080 (via proxy)
# Complete initial setup in browser

# Manual container management:
podman-compose up -d  # Start containers
podman logs dc --tail 50 -f  # View HA logs
podman logs web --tail 50 -f  # View proxy logs  
podman-compose down  # Stop environment
```

#### Manual Testing

1. Copy the integration to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via UI
4. Monitor logs for any issues

### Code Quality

The project uses modern automated code quality tools:

```bash
# Format and lint code (recommended)
ruff check custom_components/real_electricity_price/ --fix
ruff format custom_components/real_electricity_price/

# Run syntax validation
cd tests && ./test.sh syntax

# Check import structure  
cd tests && ./test.sh import
```

**Quality Assurance:**
- ✅ **Automated formatting** with Ruff
- ✅ **Linting** with automatic fixes
- ✅ **GitHub Actions** for CI/CD
- ✅ **Comprehensive test suite** (53+ tests)
- ✅ **Multi-Python compatibility** testing

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
    custom_components.real_electricity_price.cheap_price_coordinator: debug
```

### Reset Integration

If the integration becomes unresponsive:

1. Go to Settings → Devices & Services
2. Find "Real Electricity Price" integration
3. Click the three dots → "Delete"
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
