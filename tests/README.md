# Comprehensive Test Suite for Real Electricity Price Integration

This directory contains a comprehensive test suite covering all aspects of the Real Electricity Price Home Assistant custom integration.

## � Continuous Integration

All tests are automatically executed on every push and pull request through GitHub Actions:
- **Multiple Python versions**: Tests run on Python 3.11, 3.12, and 3.13
- **Comprehensive coverage**: Unit tests, pytest, and shell script validation
- **Status badge**: [![Tests](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml/badge.svg)](https://github.com/bitosome/real-electricity-price/actions/workflows/test.yml)

## �📁 Test File Organization

All test files are now centralized in this `tests/` directory:

### 🎯 Comprehensive Test Suite (Latest)
- **`test_all_comprehensive.py`** - Master test runner with category support
- **`test_config_validation.py`** - All configuration options and validation (17 tests)
- **`test_sensor_calculations.py`** - All sensor entities and calculations (17 tests)
- **`test_buttons_calculations.py`** - All button entities and cheap price calculations (19 tests)
- **`test_comprehensive.py`** - Integration tests and comprehensive coverage

### 🔧 Legacy Test Files (Specific Components)
- **`test_integration.py`** - Original integration tests
- **`test_area_codes.py`** - Nord Pool area code validation
- **`test_cheap_coordinator.py`** - Cheap price coordinator tests
- **`test_cheap_price_triggers.py`** - Price trigger mechanism tests
- **`test_cheap_prices.py`** - Cheap price calculation algorithm tests
- **`test_holidays.py`** - Holiday detection and handling tests
- **`test_new_implementation.py`** - Tests for new coordinator implementation

### 🛠️ Test Utilities & Scripts
- **`test_runner.sh`** - Shell script test runner
- **`test.sh`** - Basic test execution script
- **`test-hacs-e2e.sh`** - End-to-end HACS testing
- **`test-requirements.txt`** - Python test dependencies
- **`COMPLETION_SUMMARY.py`** - Test suite completion summary

## Test Coverage

The test suite covers **all** configuration options, sensors, entities, buttons, and calculations:

### ✅ Configuration Options & Validation (`test_config_validation.py`)
- **All 25+ configuration keys** with defaults and validation
- **Country codes**: All Nord Pool area codes (EE, FI, LV, LT, SE1-4, NO1-5, DK1-2)
- **VAT rates**: 0-100% validation with edge cases
- **Scan intervals**: 5 minutes to 24 hours validation
- **Time formats**: HH:MM and TimeSelector validation
- **Night hours**: Start/end time validation with midnight crossover
- **Price components**: All grid costs, supplier margins, excise duties
- **VAT application**: Selective VAT on different components
- **Edge cases**: Invalid inputs, extreme values, migration scenarios

### ✅ Sensor Entities & Calculations (`test_sensor_calculations.py`)
- **Current Price Sensor**: Complete price calculation with all components
- **Tariff Sensor**: Day/night determination logic
- **Hourly Prices Sensor**: Data structure and 24/48-hour price arrays
- **Cheap Prices Sensor**: Threshold calculations and range grouping
- **Sync Timestamp Sensors**: ISO format timestamps and sync status
- **Price calculations**: VAT application, precision, rounding, edge cases
- **Data structures**: All sensor attributes and state validation
- **Timezone handling**: UTC conversion and local time handling

### ✅ Button Entities & Functionality (`test_buttons_calculations.py`)
- **Refresh Data Button**: Manual coordinator refresh triggering
- **Calculate Cheap Hours Button**: Cheap price coordinator triggering
- **Button properties**: Stateless entities, availability logic
- **Error handling**: Failed coordinator responses
- **Throttling**: Rapid button press prevention
- **Integration**: Button-coordinator communication

### ✅ Cheap Price Calculations & Algorithms (`test_buttons_calculations.py`)
- **Threshold calculation**: Min price * (1 + threshold%) logic
- **Consecutive hour grouping**: Range detection across midnight
- **Statistical calculations**: Min, max, average prices per range
- **Different thresholds**: 5%, 10%, 15%, 20%, 25% testing
- **Edge cases**: All same prices, single price, empty data
- **Update timing**: Trigger configuration (00:01, 14:30, 23:00)
- **Coordinator behavior**: Data processing, error handling, config updates

### ✅ Integration & Comprehensive Tests (`test_comprehensive.py`)
- **API client**: Initialization, success/failure scenarios, data validation
- **Coordinators**: Main and cheap price coordinator functionality
- **Data flow**: Coordinator → Sensor → Button integration
- **Error scenarios**: Network failures, invalid data, missing components
- **Manifest validation**: Required fields, dependencies, translations
- **Calculation accuracy**: Floating point precision, extreme values
- **End-to-end**: Complete integration workflow testing

## Running Tests

### Run All Tests (Recommended)
```bash
# From repository root
python tests/test_all_comprehensive.py

# Or from tests directory
cd tests
python test_all_comprehensive.py
```

### Run Specific Test Categories
```bash
# From repository root
python tests/test_all_comprehensive.py --config    # Configuration validation only
python tests/test_all_comprehensive.py --sensors   # Sensor calculations only  
python tests/test_all_comprehensive.py --buttons   # Button and cheap price calculations
python tests/test_all_comprehensive.py --integration # Comprehensive integration tests

# Or from tests directory
cd tests
python test_all_comprehensive.py --config
python test_all_comprehensive.py --sensors
python test_all_comprehensive.py --buttons
python test_all_comprehensive.py --integration
```

### Run Individual Test Files
```bash
# From repository root
python tests/test_config_validation.py
python tests/test_sensor_calculations.py  
python tests/test_buttons_calculations.py

# Or from tests directory
cd tests
python test_config_validation.py
python test_sensor_calculations.py
python test_buttons_calculations.py
```

## Test Environment Setup

The tests are designed to run without requiring the full Home Assistant environment:

1. **Mock HA modules**: Tests mock all `homeassistant.*` imports
2. **Standalone validation**: Configuration and calculation logic tested independently
3. **No external dependencies**: Tests don't require actual API connections
4. **Path resolution**: Tests automatically find the integration files

## Test Results Summary

When all tests pass, you should see:

```
🏁 COMPREHENSIVE TEST SUMMARY
================================================================================
📊 Test Modules: 4/4 passed
⏱️  Total Time: X.XX seconds
🎉 ALL TESTS PASSED! Integration is comprehensively tested.

✅ Coverage Summary:
   ✅ Configuration flow options: All validated
   ✅ Sensor entities and calculations: All tested
   ✅ Button entities functionality: All verified
   ✅ Cheap price algorithms: All validated
   ✅ Edge cases and error handling: All covered
   ✅ Integration scenarios: All tested

🔧 The Real Electricity Price integration is ready for production!
```

## What's Tested vs What's Not

### ✅ Fully Tested
- **All configuration options**: Every config key, validation rule, default value
- **All sensors**: Current price, tariff, hourly prices, cheap prices, sync timestamps
- **All buttons**: Refresh data, calculate cheap hours functionality
- **All calculations**: Price formulas, VAT application, thresholds, statistics
- **Error handling**: Invalid data, network failures, edge cases
- **Data structures**: Sensor attributes, state values, coordinator data flow

### ⚠️ Limitations (by design)
- **Home Assistant core**: Tests mock HA infrastructure (not testing HA itself)
- **Nord Pool API**: Tests use mock data (not testing external API reliability)
- **Real hardware**: Tests don't require actual HA installation
- **UI components**: Tests focus on backend logic, not frontend rendering

## Test Architecture

The test suite uses a layered approach:

1. **Unit Tests**: Individual functions and calculations
2. **Component Tests**: Sensors, buttons, coordinators in isolation
3. **Integration Tests**: Component interactions and data flow
4. **End-to-End Tests**: Complete workflows from config to sensor output

This ensures comprehensive coverage while maintaining test reliability and speed.

## Maintenance

When adding new features to the integration:

1. **Add configuration options**: Update `test_config_validation.py`
2. **Add sensors**: Update `test_sensor_calculations.py`
3. **Add calculations**: Update `test_buttons_calculations.py`
4. **Add integration points**: Update `test_comprehensive.py`

The test suite should evolve with the integration to maintain comprehensive coverage.
