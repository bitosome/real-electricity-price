# Podman Test Environment with Nginx Reverse Proxy

This directory contains a complete Podman-based Home Assistant test environment with maximum network discretion using an Nginx reverse proxy.

## 🛡️ Maximum Network Discretion

**What makes this discrete:**
- ✅ **Non-descriptive container names**: `dc` and `web`
- ✅ **Custom port**: Access on `8080` instead of standard `8123`
- ✅ **Proxy masking**: Nginx hides Home Assistant identity
- ✅ **Generic server headers**: Appears as "Web Server"
- ✅ **No direct HA exposure**: Port 8123 not accessible externally
- ✅ **Internal network**: Containers communicate on private bridge

## Quick Start

1. **Start the test environment:**
   ```bash
   ./scripts/dev-setup.sh
   ```
   OR manually:
   ```bash
   podman-compose up -d
   ```

2. **Access Home Assistant:**
   - Open http://localhost:8080 in your browser (via proxy)
   - Complete the initial setup (create user account)

3. **Configure HACS (pre-installed):**
   - Go to Settings → Devices & Services
   - Configure HACS integration
   - Add custom repository: `https://github.com/bitosome/real-electricity-price`

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

## What's Included

### 🏠 **Home Assistant Setup**
- Latest stable Home Assistant container via Podman
- Estonian timezone and location (Tallinn)
- Debug logging enabled for the integration
- HACS pre-installed and ready to configure
- **Hidden behind Nginx proxy for maximum discretion**

### 🛡️ **Nginx Reverse Proxy**
- Generic "Web Server" identification
- Custom port 8080 (not standard HA port 8123)
- Header masking and security headers
- WebSocket support for real-time updates
- Static asset caching for performance

### 🧪 **Test Features**
- HACS integration for testing (pre-installed)
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
container/
├── config/                # Home Assistant configuration
│   ├── configuration.yaml # Main HA configuration
│   ├── ui-lovelace.yaml   # Test dashboard
│   ├── automations.yaml   # Empty, ready for testing
│   ├── scenes.yaml        # Empty scenes file
│   ├── scripts.yaml       # Empty scripts file
│   └── custom_components/ # Pre-installed integrations
│       ├── hacs/          # HACS files (auto-installed)
│       └── real_electricity_price/  # Your integration (synced)
└── nginx/                 # Nginx proxy configuration
    ├── nginx.conf         # Main Nginx config
    └── default.conf       # Proxy configuration
```

## Usage

### Starting the Environment
```bash
# Start complete development environment (recommended)
./scripts/dev-setup.sh

# Or start manually in background
podman-compose up -d

# Start with logs (for debugging)
podman-compose up

# Stop the environment
podman-compose down

# Reset everything (removes data)
podman-compose down -v
```

### Viewing Logs
```bash
# View all logs
podman-compose logs -f

# View Home Assistant logs
podman logs dc -f

# View proxy logs
podman logs web -f

# View integration logs specifically
podman exec dc grep "real_electricity_price" /config/home-assistant.log
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
# Check Podman is running
podman --version

# On macOS, check Podman machine
podman machine list

# Start Podman machine if not running
podman machine start

# Check for port conflicts
lsof -i :8123

# View detailed logs
podman-compose logs homeassistant
```

### Integration Not Available in HACS
```bash
# Check HACS is properly installed
podman logs dc | grep -i hacs

# Verify repository is accessible
curl -s https://api.github.com/repos/bitosome/real-electricity-price

# Check HACS custom repositories (if added manually)
# Go to HACS → Settings → Custom repositories
```

### HACS Download Errors
```bash
# Check for file permission errors
podman logs dc | grep -i "read-only\|permission"

# Restart HACS
# Go to HACS → Settings → Restart
```

### API Issues
```bash
# Test Nord Pool API directly
curl "https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices?date=$(date +%Y-%m-%d)&market=DayAhead&currency=EUR"

# Check network connectivity from container
podman exec dc ping google.com
```

## Cleanup

To completely remove the test environment:
```bash
# Stop and remove containers, networks, and volumes
podman-compose down -v

# Remove the container directory
rm -rf container/
```
