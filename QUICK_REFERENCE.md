# Quick Reference - Real Electricity Price Development

## Essential Commands
```bash
# Deploy changes to container
./scripts/sync-integration.sh

# Check logs
podman logs dc --tail=50

# Follow logs
podman logs dc -f

# Restart container
podman restart dc

# Search for errors
podman logs dc --tail=100 | grep -E "(ERROR|Exception|500)"
```

## Key File Locations
- **Integration Code**: `/custom_components/real_electricity_price/`
- **Container Target**: `/container/config/custom_components/real_electricity_price/`
- **Sync Script**: `./scripts/sync-integration.sh`

## Current Status (Sept 2025)
✅ **PRODUCTION READY**
- 10 sensors working
- No pandas dependency
- Config flow functional
- All HA conventions followed

## Critical Constants (const.py)
- `CONF_CHEAP_HOURS_UPDATE_TRIGGER`
- `CONF_CHEAP_HOURS_THRESHOLD`
- All other config constants properly defined

## Testing Config Flow
```bash
# Should return 401 (not 500) - this is correct
curl -X POST http://localhost:8123/api/config/config_entries/flow \
  -H "Content-Type: application/json" \
  -d '{"handler": "real_electricity_price"}'
```

## Entity Types Created
1. Current Price (monetary)
2. Hourly Prices (array)
3. Daily Hourly Prices (array)
4. Cheap Hours Start (timestamp)
5. Cheap Hours End (timestamp)
6. Cheap Hours Duration (duration)
7. Cheap Hours Prices (array)
8. Cheap Hours Average Price (monetary)
9. Next Update (timestamp)
10. Cheap Hours Count (numeric)

## Dependencies
- **Only**: `holidays>=0.21`
- **Removed**: pandas (pure Python now)

## Emergency Procedures
1. **Integration won't load**: Check logs for import errors
2. **Config flow 500 error**: Verify constants in config_flow.py match const.py
3. **Changes not reflected**: Run sync script, restart container
4. **Entity duplicates**: Check sensor.py platform setup
