# Docker Test Environment for Real Electricity Price Integration

This directory contains a complete Docker-based Home Assistant test environment for testing the Real Electricity Price integration via HACS.

## Quick Start

1. **Start the test environment:**
   ```bash
   docker-compose up -d
   ```

2. **Access Home Assistant:**
   - Open http://localhost:8123 in your browser
   - Complete the initial setup (create user account)

3. **Install HACS (if not already done):**
   - Follow the guide in `HACS_SETUP.md`
   - Or run: `./install_hacs.sh` (if available)

4. **Install the integration via HACS:**
   - Go to HACS → Integrations
   - Search for "Real Electricity Price" 
   - Click "Download" to install
   - Restart Home Assistant

5. **Add the integration:**
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Real Electricity Price"
   - Configure with your preferred settings

4. **View the test dashboard:**
   - Go to the "Real Electricity Price Test" dashboard
   - Monitor sensors and debug information

## What's Included

### 🏠 **Home Assistant Setup**
- Latest stable Home Assistant container
- Estonian timezone and location (Tallinn)
- Debug logging enabled for the integration

### 🧪 **Test Features**
- HACS integration for testing
- Current and tomorrow's price displays
- Price status indicators
- Average price calculations
- Debug information panel
- Interactive price threshold slider

### 🔧 **Development Features**
- HACS integration management
- Debug logging enabled
- Configuration validation
- Health checks

## File Structure

```
docker/
├── config/
│   ├── configuration.yaml    # Main HA configuration
│   ├── ui-lovelace.yaml     # Test dashboard
│   ├── automations.yaml     # Empty, ready for testing
│   ├── scenes.yaml          # Empty scenes file
│   └── scripts.yaml         # Empty scripts file
└── docker-compose.yml       # Container configuration
```

## Usage

### Starting the Environment
```bash
# Start in background
docker-compose up -d

# Start with logs (for debugging)
docker-compose up

# Stop the environment
docker-compose down

# Reset everything (removes data)
docker-compose down -v
```

### Viewing Logs
```bash
# View all logs
docker-compose logs -f

# View just Home Assistant logs
docker-compose logs -f homeassistant

# View integration logs specifically
docker-compose exec homeassistant grep "real_electricity_price" /config/home-assistant.log
```

### Development Workflow

1. Make changes to the integration code
2. Sync into container using scripts/sync-integration.sh
3. Verify changes work correctly
4. Check the logs for any errors

### Integration Testing Checklist

- [ ] Integration loads without errors
- [ ] Config flow completes successfully
- [ ] Today's sensor shows current price
- [ ] Tomorrow's sensor shows data (after 14:00 CET)
- [ ] Hourly prices attribute contains 24 entries
- [ ] Price calculations include all costs
- [ ] Time-based pricing works (day/night rates)
- [ ] Holiday detection works correctly
- [ ] Scan interval is respected
- [ ] Error handling works gracefully

## Configuration Options

The test environment includes default settings for Estonian market:
- **Grid:** elektrilevi
- **Supplier:** eesti_energia
- **Country Code:** EE (Estonia)
- **VAT:** 24%
- **Night hours:** 22:00 - 07:00
- **Update interval:** 1 hour

Modify these in the integration settings to test different configurations for other Nord Pool market areas.

## Troubleshooting

### Container Won't Start
```bash
# Check Docker is running
docker --version

# Check for port conflicts
lsof -i :8123

# View detailed logs
docker-compose logs homeassistant
```

### Integration Not Available in HACS
```bash
# Check HACS is properly installed
docker-compose logs homeassistant | grep -i hacs

# Verify repository is accessible
curl -s https://api.github.com/repos/bitosome/real-electricity-price

# Check HACS custom repositories (if added manually)
# Go to HACS → Settings → Custom repositories
```

### HACS Download Errors
```bash
# Check for file permission errors
docker-compose logs homeassistant | grep -i "read-only\|permission"

# Restart HACS
# Go to HACS → Settings → Restart
```

### API Issues
```bash
# Test Nord Pool API directly
curl "https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices?date=$(date +%Y-%m-%d)&market=DayAhead&currency=EUR"

# Check network connectivity from container
docker-compose exec homeassistant ping google.com
```

## Cleanup

To completely remove the test environment:
```bash
# Stop and remove containers, networks, and volumes
docker-compose down -v

# Remove the docker directory
rm -rf docker/
```
