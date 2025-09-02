# HACS Setup Guide for Testing

## Current Status
✅ HACS is automatically installed during environment setup
✅ Home Assistant is running at http://localhost:8123
✅ Real Electricity Price integration is mounted and ready

## Step-by-Step Setup

### 1. Start Development Environment
```bash
./scripts/dev-setup.sh
```
This automatically:
- Sets up Podman containers
- Installs HACS
- Syncs your integration files
- Starts Home Assistant

### 2. Complete Home Assistant Initial Setup
1. Open http://localhost:8123 in your browser
2. Create your user account
3. Complete the initial configuration wizard

### 2. Configure HACS
1. Go to **Settings** → **Devices & Services**
2. Look for **HACS** in the discovered integrations
3. Click **"Configure"** on HACS
4. Follow the GitHub integration setup:
   - You'll need a GitHub account
   - Generate a Personal Access Token if requested
   - Follow the authentication flow

### 3. Add Your Integration via HACS
1. Go to **HACS** in the sidebar
2. Click **"Custom repositories"**
3. Add your repository: `https://github.com/bitosome/real-electricity-price`
4. Select category: **"Integration"**
5. Click **"Add"**
6. Find **"Real Electricity Price"** in HACS
7. Click **"Download"**
8. Restart Home Assistant

### 4. Configure Real Electricity Price Integration
1. Go to **Settings** → **Devices & Services**
2. Click **"Add Integration"**
3. Search for **"Real Electricity Price"**
4. Configure your settings:
   - Grid provider (default: elektrilevi - Estonian)
   - Supplier (default: eesti_energia - Estonian)
   - Area code (EE for Estonia, FI for Finland, SE1-SE4 for Sweden, NO1-NO5 for Norway, DK1-DK2 for Denmark, etc.)
   - All pricing parameters
   - VAT rate (default: 24% for Estonia)
   - Scan interval (default: 1 hour)

### 5. Test the Integration
1. Check that two sensors appear:
   - `sensor.real_electricity_prices_today`
   - `sensor.real_electricity_prices_tomorrow`
2. View the test dashboard for monitoring
3. Check sensor attributes for hourly price data
4. Verify price calculations include all costs

## Alternative: Manual Installation (Skip HACS)

If you prefer to test directly without HACS:

1. The integration is already mounted at `/config/custom_components/real_electricity_price`
2. Restart Home Assistant: `podman restart dc`
3. Go directly to **Settings** → **Devices & Services** → **Add Integration**
4. Search for **"Real Electricity Price"** and configure

## Testing Checklist

- [ ] HACS configured and working
- [ ] Repository added to HACS
- [ ] Integration installed via HACS
- [ ] Integration configured with proper settings
- [ ] Today's sensor shows current hour price
- [ ] Tomorrow's sensor shows data (available after ~14:00 CET)
- [ ] Price calculations are correct
- [ ] Test dashboard displays data properly
- [ ] No errors in Home Assistant logs

## Troubleshooting

### HACS Not Appearing
- Check logs: `podman logs dc | grep -i hacs`
- Verify files: `ls container/config/custom_components/hacs/`
- Restart container: `podman restart dc`

### Integration Not Loading
- Check integration files: `ls container/config/custom_components/real_electricity_price/`
- Check syntax: Run linting on your integration code
- Check logs for specific error messages

### API Issues
- Test Nord Pool API: `curl "https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices?date=$(date +%Y-%m-%d)&market=DayAhead&currency=EUR"`
- Check network connectivity from container
- Verify scan interval isn't too frequent

## Useful Commands

```bash
# View logs
podman logs dc -f

# Restart Home Assistant
podman restart dc

# Check container status
podman-compose ps

# Stop environment
podman-compose down

# Access container shell
podman exec -it dc bash
```

## Next Steps

1. Complete the HACS setup
2. Install your integration
3. Test all functionality
4. Create a GitHub release for HACS users
5. Submit to HACS default repository (optional)
