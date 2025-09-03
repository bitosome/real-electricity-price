# Tests Directory

This directory contains all test files and test-related utilities for the Real Electricity Price integration.

## 🧪 Test Files

### Core Tests
- **`test_integration.py`** - Main integration functionality tests
- **`test_button.py`** - Refresh button functionality tests

### HACS Testing
- **`test_hacs_e2e.py`** - Comprehensive end-to-end HACS installation test

### Test Scripts
- **`test.sh`** - Main test runner with multiple test types
- **`test-hacs-e2e.sh`** - HACS end-to-end test runner
- **`test_runner.sh`** - Alternative test orchestrator

### Dependencies
- **`test-requirements.txt`** - Python packages required for testing

## 🚀 Running Tests

### Quick Test
```bash
# From project root
make test

# Or directly
./tests/test.sh
```

### Specific Test Types
```bash
./tests/test.sh syntax    # Syntax validation
./tests/test.sh import    # Import tests
./tests/test.sh config    # Configuration tests
./tests/test.sh podman    # Podman integration tests
./tests/test.sh quality   # Code quality checks
```

### HACS End-to-End Test
```bash
./tests/test-hacs-e2e.sh
```

## 📋 Test Coverage

### Integration Tests
- ✅ Module imports and syntax validation
- ✅ Configuration flow validation
- ✅ Entity creation and state management
- ✅ Button functionality
- ✅ Data coordinator operations

### HACS Tests
- ✅ HACS installation simulation
- ✅ Integration loading in Home Assistant
- ✅ Entity discovery and configuration
- ✅ Podman environment validation

### Code Quality
- ✅ Python syntax validation
- ✅ Import statement verification
- ✅ Code formatting (Ruff)
- ✅ Type safety checks

## 🔧 Test Configuration

Tests use the following configuration:
- **Podman Image**: Home Assistant stable
- **Test Port**: 8123 (or 8124 for parallel tests)
- **Test Data**: Nord Pool electricity pricing data (defaults to Estonian market)
- **Mock API**: Nord Pool API simulation when needed

## 🎯 Success Criteria

Tests pass when:
1. **All entities created**: Expected sensors and button found
2. **No critical errors**: Clean Home Assistant logs
3. **Correct precision**: 6-decimal places in price calculations
4. **Valid data**: Reasonable price ranges and complete attributes
5. **Clean startup**: Integration loads within timeout period

## 🐛 Debugging Tests

### Enable Debug Logging
```python
logging.basicConfig(level=logging.DEBUG)
```

### Container Inspection
```bash
# Check container logs
podman logs dc --tail 50

# Access container shell
podman exec -it dc bash
```

### Manual Verification
```bash
# Check Home Assistant API
curl http://localhost:8123/api/

# Check entity states (after authentication)
curl -H "Authorization: Bearer <token>" http://localhost:8123/api/states
```

This testing framework ensures the Real Electricity Price integration works correctly across different installation methods and provides reliable Nord Pool electricity pricing data for any supported market area.
