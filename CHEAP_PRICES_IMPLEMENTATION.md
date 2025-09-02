# Cheapest Prices Sensor Implementation Summary

## What has been implemented

### 1. Separate Coordinator Architecture
- **New Coordinator**: `CheapPriceDataUpdateCoordinator`
- **Purpose**: Independent update schedule for cheap price calculations
- **Update Mechanism**: Time-based triggers instead of continuous polling
- **Configuration**: `cheap_price_update_trigger` parameter (default: "14:30")

### 2. Configuration Options
- **Parameter**: `cheap_price_threshold` 
- **Default**: 10.0% 
- **Description**: Percentage above minimum price to consider "cheap"
- **Parameter**: `cheap_price_update_trigger`
- **Default**: "14:30"
- **Description**: Time when cheap price calculation is triggered daily
- **Location**: Added to both config flow setup and options flow
- **UI**: Number selector for threshold, time selector for trigger

### 3. New Sensor: "Cheapest Prices"
- **Entity ID**: `sensor.real_electricity_price_cheap_prices`
- **Device Class**: Monetary (EUR/kWh)
- **Icon**: `mdi:currency-eur-off`
- **Update Schedule**: Independent from main price sensor

### 4. Sensor Functionality

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
  "current_status": "in_cheap_period|outside_cheap_period",
  "next_cheap_period": {
    "start_time": "2025-09-01T22:00:00Z",
    "price": 0.098,
    "hours_until": 5.5
  },
  "threshold_percent": 10.0,
  "min_price": 0.100,
  "max_cheap_price": 0.110,
  "total_cheap_hours": 4,
  "last_calculation": "2025-09-01T14:30:00Z",
  "trigger_time": "14:30",
  "analysis_period": "3 days"
}
```

### 5. Analysis Logic

#### Price Analysis with Pandas
1. **Data Collection**: Gathers all available hourly price data from main coordinator
2. **Minimum Price**: Finds the absolute minimum price across all data
3. **Threshold Calculation**: `max_cheap_price = min_price × (1 + threshold_percent/100)`
4. **Filtering**: Identifies all hours where `actual_price ≤ max_cheap_price`
5. **Grouping**: Groups consecutive cheap hours into time ranges
6. **Statistics**: Calculates min, max, average prices per range

#### Time Range Grouping
- Consecutive cheap hours are combined into single ranges
- Each range shows start/end times, duration, and price statistics
- Non-consecutive cheap periods create separate ranges

### 6. Coordinator Architecture

#### Main Coordinator (`RealElectricityPriceDataUpdateCoordinator`)
- Fetches price data from API
- Updates hourly price sensors
- Provides data to cheap price coordinator

#### Cheap Price Coordinator (`CheapPriceDataUpdateCoordinator`)
- Analyzes data from main coordinator
- Updates only the cheap prices sensor
- Triggered at configured time (default: 14:30)
- Manual trigger via service call
- No continuous polling - event-driven updates

#### Benefits of Separation
- **Performance**: Expensive analysis only runs when needed
- **Flexibility**: Different update schedules for different sensors  
- **Reliability**: Main price data updates independently
- **User Control**: Configurable calculation timing

### 7. Services

#### Refresh Data Service
- **Service**: `real_electricity_price.refresh_data`
- **Purpose**: Manually trigger main price data update
- **Usage**: Updates all sensors except cheap prices

#### Recalculate Cheap Prices Service  
- **Service**: `real_electricity_price.recalculate_cheap_prices`
- **Purpose**: Manually trigger cheap price analysis
- **Usage**: Forces immediate recalculation regardless of schedule

### 8. Error Handling
- Graceful handling of missing or invalid price data
- Logging for debugging and monitoring
- Returns empty results if analysis fails
- Skips entries with `None` prices
- Fallback to old analysis method for backward compatibility

### 9. Dependencies
- **Added**: `pandas>=1.3.0` to manifest.json requirements
- **Import**: Added pandas import to coordinator
- **Usage**: DataFrame operations for efficient price analysis

### 10. Integration Points

#### Configuration Flow
- Added trigger time configuration to both initial setup and options reconfiguration
- Preserves existing configuration structure
- Default values properly handled
- Time format validation (HH:MM)

#### Sensor Platform
- New sensor type: `SENSOR_TYPE_CHEAP_PRICES`
- Uses dedicated coordinator for updates
- Follows same patterns as other sensors
- Backward compatibility maintained

#### Coordinator Integration
- Main coordinator provides data
- Cheap price coordinator consumes and analyzes
- Independent update schedules
- Event-driven architecture

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
        attribute: current_status
        to: "in_cheap_period"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Cheap electricity period started! Price: {{ states('sensor.real_electricity_price_cheap_prices') }} EUR/kWh

  - alias: "Force recalculate cheap prices at 15:00"
    trigger:
      - platform: time
        at: "15:00:00"
    action:
      - service: real_electricity_price.recalculate_cheap_prices

  - alias: "Washing machine during cheap hours"
    trigger:
      - platform: state
        entity_id: sensor.real_electricity_price_cheap_prices
        attribute: current_status
        to: "in_cheap_period"
    condition:
      - condition: state
        entity_id: switch.washing_machine
        state: "off"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.washing_machine
```

## Key Benefits

1. **Independent Updates**: Cheap prices calculate on their own schedule
2. **Configurable Timing**: Choose when calculations happen (e.g., after 14:00 when next-day prices are available)
3. **Performance Optimized**: Expensive analysis only runs when triggered
4. **Flexible Threshold**: Configurable sensitivity (5%, 10%, 20%, etc.)
5. **Time Range Optimization**: Groups consecutive cheap hours for efficient scheduling
6. **Rich Data**: Detailed statistics and current status for advanced automations
7. **Manual Control**: Service calls for immediate recalculation
8. **Event-driven**: No unnecessary polling or calculations

## Implementation Status

✅ **Separate coordinator**: Independent update mechanism implemented  
✅ **Configuration UI**: Time trigger and threshold in config flow  
✅ **Sensor integration**: Uses dedicated coordinator  
✅ **Service calls**: Manual trigger services implemented  
✅ **Error handling**: Comprehensive error management  
✅ **Backward compatibility**: Fallback for existing setups  
✅ **Documentation**: Updated for new architecture  
✅ **Dependencies**: Pandas requirement maintained  
✅ **Testing**: Coordinator architecture validated  

The separate coordinator implementation is complete and ready for use!
