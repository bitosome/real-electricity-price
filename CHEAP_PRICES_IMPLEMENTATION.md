# Cheapest Prices Sensor Implementation Summary

## What has been implemented

### 1. New Configuration Option
- **Parameter**: `cheap_price_threshold` 
- **Default**: 10.0% 
- **Description**: Percentage above minimum price to consider "cheap"
- **Location**: Added to both config flow setup and options flow
- **UI**: Number selector with range 0-100%, step 0.1%

### 2. New Sensor: "Cheapest Prices"
- **Entity ID**: `sensor.real_electricity_price_cheap_prices`
- **Device Class**: Monetary (EUR/kWh)
- **Icon**: `mdi:currency-eur-off`

### 3. Sensor Functionality

#### State Value
Returns the nearest cheap price:
- If currently in a cheap period: current cheap price
- Otherwise: next upcoming cheap price
- `None` if no cheap prices found

#### Attributes
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
  "threshold_percent": 10.0,
  "min_price": 0.100,
  "max_cheap_price": 0.110,
  "total_cheap_hours": 4,
  "analysis_period": "3 days",
  "data_sources": [...]
}
```

### 4. Analysis Logic

#### Price Analysis with Pandas
1. **Data Collection**: Gathers all available hourly price data (yesterday, today, tomorrow)
2. **Minimum Price**: Finds the absolute minimum price across all data
3. **Threshold Calculation**: `max_cheap_price = min_price × (1 + threshold_percent/100)`
4. **Filtering**: Identifies all hours where `actual_price ≤ max_cheap_price`
5. **Grouping**: Groups consecutive cheap hours into time ranges
6. **Statistics**: Calculates min, max, average prices per range

#### Time Range Grouping
- Consecutive cheap hours are combined into single ranges
- Each range shows start/end times, duration, and price statistics
- Non-consecutive cheap periods create separate ranges

### 5. Error Handling
- Graceful handling of missing or invalid price data
- Logging for debugging and monitoring
- Returns empty results if analysis fails
- Skips entries with `None` prices

### 6. Dependencies
- **Added**: `pandas>=1.3.0` to manifest.json requirements
- **Import**: Added pandas import to sensor.py
- **Usage**: DataFrame operations for efficient price analysis

### 7. Integration Points

#### Configuration Flow
- Added to both initial setup and options reconfiguration
- Preserves existing configuration structure
- Default value properly handled

#### Sensor Platform
- New sensor type: `SENSOR_TYPE_CHEAP_PRICES`
- Integrated into existing sensor setup flow
- Follows same patterns as other sensors

### 8. Documentation
- **README.md**: Added sensor description and configuration docs
- **Example data**: Shows expected attribute structure
- **Configuration**: Documents the new threshold parameter
- **Test script**: Demonstrates functionality with sample data

## Usage Example

```yaml
# In Home Assistant, the sensor will appear as:
# sensor.real_electricity_price_cheap_prices

# Automation example:
automation:
  - alias: "Notify of cheap electricity"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_cheap_prices
    condition:
      - condition: template
        value_template: >
          {{ trigger.to_state.state != 'unavailable' and
             trigger.to_state.state != 'unknown' }}
    action:
      - service: notify.mobile_app
        data:
          message: >
            Cheap electricity detected! Price: {{ trigger.to_state.state }} EUR/kWh
            Next cheap periods: {{ trigger.to_state.attributes.total_cheap_hours }} hours total
```

## Key Benefits

1. **Automated Analysis**: No manual price monitoring needed
2. **Flexible Threshold**: Configurable sensitivity (5%, 10%, 20%, etc.)
3. **Time Range Optimization**: Groups consecutive cheap hours for efficient scheduling
4. **Rich Data**: Detailed statistics for advanced automations
5. **Real-time Updates**: Updates with hourly price refreshes
6. **Integration Ready**: Standard Home Assistant sensor with proper attributes

## Implementation Status

✅ **Core functionality**: Implemented and tested  
✅ **Configuration UI**: Added to config flow  
✅ **Sensor integration**: Added to sensor platform  
✅ **Error handling**: Comprehensive error management  
✅ **Documentation**: README and inline docs updated  
✅ **Dependencies**: Pandas requirement added  
✅ **Testing**: Test script validates logic  

The implementation is complete and ready for use!
