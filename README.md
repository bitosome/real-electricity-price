# Real Electricity Price

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration that provides real-time electricity prices from Nord Pool with comprehensive cost calculations including grid fees, supplier margins, and VAT. Optimized for the Estonian electricity market with support for time-based pricing and holiday handling.

## Features

- **Dual Date Pricing**: Fetches both today's and tomorrow's electricity prices from Nord Pool
- **Comprehensive Cost Calculation**: Automatically includes all grid, supplier, and tax costs
- **Time-Based Pricing**: Different transmission rates for day/night hours and holidays
- **Two Sensors**: Separate sensors for current day and next day pricing
- **Configurable Update Frequency**: Set scan interval from 5 minutes to 24 hours
- **Estonian Market Support**: Built-in holiday detection using the `holidays` library
- **Real-Time Updates**: Current hour pricing with hourly data for the entire day
- **Robust Error Handling**: Graceful handling of API failures and network issues

## Installation

### HACS (Recommended)

1. Add this repository (`https://github.com/bitosome/real-electricity-price`) as a custom repository in HACS
2. Search for "Real Electricity Price" and install
3. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/real_electricity_price` folder from this repository
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

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

The integration provides two sensors that update based on your configured scan interval:

### `sensor.real_electricity_prices_today`
- **Purpose**: Shows the current hour's electricity price for today
- **Update Logic**: Returns the price for the current hour based on UTC time
- **State**: Current hour's total price in EUR/kWh (including all costs)
- **Attributes**:
  - `hourly_prices`: Array of all 24 hourly prices for the day
  - `date`: The date the data is for (YYYY-MM-DD format)

### `sensor.real_electricity_prices_tomorrow`
- **Purpose**: Shows pricing data for tomorrow
- **Update Logic**: Returns the first hour's price of the next day
- **State**: Tomorrow's first hour price in EUR/kWh (including all costs)
- **Attributes**:
  - `hourly_prices`: Array of all 24 hourly prices for tomorrow
  - `date`: The date the data is for (YYYY-MM-DD format)

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
        value_template: "{{ states('sensor.real_electricity_prices_today') }}"
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
      entity_id: sensor.real_electricity_prices_today
      above: 0.25  # EUR/kWh
    action:
      service: notify.notify
      data:
        message: "⚡ High electricity price: {{ states('sensor.real_electricity_prices_today') }} EUR/kWh"

# Night time cheap energy notification
automation:
  - alias: "Cheap Night Energy Available"
    trigger:
      platform: time
      at: "22:00:00"
    condition:
      condition: numeric_state
      entity_id: sensor.real_electricity_prices_today
      below: 0.15  # EUR/kWh
    action:
      service: notify.notify
      data:
        message: "🌙 Cheap night electricity available: {{ states('sensor.real_electricity_prices_today') }} EUR/kWh"
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
```

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
