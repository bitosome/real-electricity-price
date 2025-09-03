# Development Environment Guide for Real Electricity Price Integration

## Overview
This is a Home Assistant custom integration for real electricity pricing with Nord Pool API integration. The development environment uses Podman containers for testing and includes automated sync scripts for deployment.

## Environment Architecture

### Container Setup
- **Runtime**: Podman (container environment)
- **Home Assistant Version**: 2025.8.3
- **Python Version**: 3.13
- **Container Name**: `dc` (Home Assistant container)

### Directory Structure
```
├── custom_components/real_electricity_price/    # Main integration code
├── container/config/custom_components/          # Container deployment target
├── scripts/                                     # Development automation scripts
├── tests/                                       # Test suite
└── examples/                                    # Configuration examples
```

## Key Development Workflow

### 1. Code Editing
- Edit files in: `/custom_components/real_electricity_price/`
- Main files:
  - `__init__.py` - Integration initialization
  - `config_flow.py` - Configuration UI flow
  - `coordinator.py` - Data coordination
  - `cheap_hours_coordinator.py` - Cheap hours analysis
  - `sensor.py` - Sensor platform setup
  - `entity_descriptions.py` - Entity definitions
  - `sensors/` directory - Individual sensor implementations

### 2. Deployment to Container
**CRITICAL**: Always use the sync script for deployment:
```bash
./scripts/sync-integration.sh
```

This script:
- Copies all integration files to container
- Restarts the Home Assistant container
- Ensures proper file permissions

### 3. Monitoring and Debugging
```bash
# Check container logs (last 50 lines)
podman logs dc --tail=50

# Follow logs in real-time
podman logs dc -f

# Search for specific errors
podman logs dc --tail=100 | grep -E "(ERROR|Exception|500)"

# Check integration-specific logs
podman logs dc --tail=100 | grep "real_electricity_price"
```

### 4. Container Management
```bash
# Restart container
podman restart dc

# Enter container for debugging
podman exec -it dc /bin/bash

# Check container status
podman ps
```

## Integration Status & Architecture

### Entity Configuration
The integration creates 10 sensors:
1. **Current Price** - Real-time electricity price
2. **Hourly Prices** - 24-hour price array
3. **Daily Hourly Prices** - Extended price data
4. **Cheap Hours Start** - When cheap period begins (timestamp)
5. **Cheap Hours End** - When cheap period ends (timestamp)
6. **Cheap Hours Duration** - Length of cheap period
7. **Cheap Hours Prices** - Prices during cheap hours
8. **Cheap Hours Average Price** - Average price during cheap period
9. **Next Update** - When data refreshes next (timestamp)
10. **Cheap Hours Count** - Number of cheap hours identified

### Key Technical Details

#### Entity Descriptions (entity_descriptions.py)
- Timestamp sensors use `SensorDeviceClass.TIMESTAMP`
- Internal diagnostic sensors have `EntityCategory.DIAGNOSTIC`
- Monetary sensors use `SensorDeviceClass.MONETARY` without conflicting state classes
- Proper friendly naming conventions: "Cheap hours *" format

#### Dependencies
- **Required**: `holidays>=0.21` (only external dependency)
- **Removed**: pandas (replaced with native Python datetime handling)
- **Core**: Standard Home Assistant libraries

#### Configuration Constants
All configuration constants are properly defined in `const.py`:
- `CONF_CHEAP_HOURS_UPDATE_TRIGGER` - When to update cheap hours analysis
- `CONF_CHEAP_HOURS_THRESHOLD` - Percentage threshold for cheap hour detection
- All grid, supplier, and VAT configuration options

## Common Development Tasks

### 1. Adding New Sensors
1. Define sensor in `entity_descriptions.py`:
```python
"new_sensor": REPSensorEntityDescription(
    key="new_sensor",
    name="New Sensor",
    device_class=SensorDeviceClass.APPROPRIATE_CLASS,
    entity_category=EntityCategory.DIAGNOSTIC,  # if internal
)
```

2. Implement sensor class in `sensors/` directory
3. Update sensor platform in `sensor.py`
4. Deploy with sync script

### 2. Modifying Config Flow
- Edit `config_flow.py`
- Ensure all constants are properly imported from `const.py`
- Test configuration UI after deployment
- Check for 500 errors in logs

### 3. Updating Coordinators
- Main coordinator: `coordinator.py` (Nord Pool API data)
- Cheap hours: `cheap_hours_coordinator.py` (price analysis)
- Use native Python datetime instead of pandas
- Follow Home Assistant coordinator patterns

### 4. Testing Changes
```bash
# Deploy changes
./scripts/sync-integration.sh

# Check logs for errors
podman logs dc --tail=50

# Test config flow (should return 401, not 500)
curl -X POST http://localhost:8123/api/config/config_entries/flow \
  -H "Content-Type: application/json" \
  -d '{"handler": "real_electricity_price"}'

# Monitor integration startup
podman logs dc -f | grep real_electricity_price
```

## Troubleshooting Guide

### Common Issues

#### 1. Config Flow 500 Errors
- **Cause**: Usually NameError from incorrect constant names
- **Solution**: Verify all constants match exactly between `config_flow.py` and `const.py`
- **Check**: `CONF_CHEAP_HOURS_*` constants specifically

#### 2. Import Errors
- **Cause**: Missing dependencies or incorrect imports
- **Solution**: Check `manifest.json` dependencies and import statements
- **Note**: Pandas has been completely removed

#### 3. Duplicate Entity IDs
- **Cause**: Multiple sensor creation without proper checks
- **Solution**: Verify sensor platform setup in `sensor.py`

#### 4. Timestamp Sensor Issues
- **Cause**: Incorrect device class or state class usage
- **Solution**: Use `SensorDeviceClass.TIMESTAMP` for all timestamp sensors
- **Avoid**: Conflicting state classes with monetary sensors

### Log Analysis
Look for these patterns in logs:
- `Setup of domain real_electricity_price took` - Integration load time
- `Found 1 ranges for cheap price analysis` - Successful cheap hours calculation
- `Creating sensor` - Entity creation process
- Any `ERROR` or `Exception` messages

### File Sync Issues
If changes aren't reflected:
1. Ensure you're editing files in `/custom_components/real_electricity_price/`
2. Run `./scripts/sync-integration.sh`
3. Check sync script output for errors
4. Restart container if needed: `podman restart dc`

## Development Best Practices

### 1. Code Standards
- Follow Home Assistant coding standards
- Use proper type hints
- Include comprehensive logging
- Handle exceptions gracefully

### 2. Testing Workflow
1. Make changes to integration code
2. Run sync script
3. Monitor logs for errors
4. Test configuration flow
5. Verify sensor functionality

### 3. Debugging Strategy
1. Check container logs first
2. Look for integration-specific messages
3. Test config flow endpoint
4. Verify entity creation in HA UI
5. Monitor coordinator updates

### 4. Version Control
- Current version: 1.3.1 (in manifest.json)
- Always test before committing
- Document breaking changes
- Update version appropriately

## Contact Points

### Home Assistant UI Access
- URL: http://localhost:8123
- Config: Settings → Devices & Services → Add Integration → "Real Electricity Price"

### Key Configuration Files
- Integration: `/custom_components/real_electricity_price/`
- Container Config: `/container/config/custom_components/real_electricity_price/`
- HA Config: `/container/config/configuration.yaml`

### Automation Scripts
- Sync: `./scripts/sync-integration.sh`
- Development setup: `./scripts/dev-setup.sh`
- HACS installation: `./scripts/install-hacs.sh`

## Final Notes

This integration is **production-ready** with all major issues resolved. The development environment is stable and properly configured for iterative development. Always use the sync script for deployment and monitor logs after changes.

The integration follows Home Assistant best practices and native conventions throughout. No external dependencies beyond the holidays library are required, making it lightweight and reliable.
