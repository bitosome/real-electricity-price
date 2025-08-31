# Dev Container Setup for Real Electricity Price Integration

This dev container provides a complete development environment for the Real Electricity Price Home Assistant integration.

## Features

- ✅ **Pre-configured Home Assistant** with debug logging
- ✅ **Python development tools** (ruff, black, isort, mypy)
- ✅ **VS Code extensions** for Python and YAML development
- ✅ **Live file synchronization** - changes appear immediately
- ✅ **Port forwarding** - Home Assistant accessible at localhost:8123
- ✅ **Automatic integration linking** via symbolic links

## Quick Start

### Prerequisites

- **VS Code** with Dev Containers extension
- **Docker Desktop** running

### Launch Dev Container

1. **Open in VS Code**: Open this project folder in VS Code
2. **Reopen in Container**: Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and select "Dev Containers: Reopen in Container"
3. **Wait for setup**: The container will build and configure automatically (2-3 minutes)
4. **Access Home Assistant**: Open http://localhost:8123 in your browser

## Development Workflow

### File Changes
- Edit files in VS Code normally
- Changes are immediately reflected in the running Home Assistant instance
- No need to manually copy files or restart containers

### Restart Home Assistant
```bash
# In the VS Code terminal inside the dev container:
pkill -f "python -m homeassistant"
bash .devcontainer/start-hass.sh
```

### View Logs
```bash
# Real-time logs
tail -f /config/logs/homeassistant.log

# Integration-specific logs (debug level)
grep "real_electricity_price" /config/logs/homeassistant.log
```

### Add Integration
1. Go to http://localhost:8123
2. Complete Home Assistant onboarding (create user account)
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Real Electricity Price"
5. Configure and test

## Development Tools

### Code Formatting
```bash
# Format Python code
black custom_components/real_electricity_price/

# Sort imports
isort custom_components/real_electricity_price/

# Lint code
ruff check custom_components/real_electricity_price/
```

### Type Checking
```bash
mypy custom_components/real_electricity_price/
```

## Advantages over Docker

| Feature | Docker Container | Dev Container |
|---------|-----------------|---------------|
| **File Sync** | Manual copy needed | Automatic/instant |
| **VS Code Integration** | None | Full integration |
| **Debugging** | Limited | Full VS Code debugging |
| **Extensions** | Not available | Pre-configured |
| **Terminal** | External | Integrated |
| **Code Completion** | None | Full IntelliSense |
| **Git Integration** | External | Built-in |
| **Port Management** | Manual | Automatic |

## Configuration

### Home Assistant Config
- **Location**: `/config/`
- **Custom Components**: Linked to `/workspaces/real-electricity-price/custom_components/`
- **Logs**: `/config/logs/homeassistant.log`
- **Debug Logging**: Enabled for `custom_components.real_electricity_price`

### VS Code Settings
- **Python**: Black formatter, isort imports, ruff linting
- **Auto-format**: On save
- **Extensions**: Python, YAML, spell checker

## Troubleshooting

### Home Assistant Won't Start
```bash
# Check logs
cat /config/logs/homeassistant.log

# Restart manually
bash .devcontainer/start-hass.sh
```

### Integration Not Loading
```bash
# Check if symbolic link exists
ls -la /config/custom_components/real_electricity_price

# Recreate link if needed
ln -sf /workspaces/real-electricity-price/custom_components/real_electricity_price /config/custom_components/real_electricity_price
```

### Port 8123 Not Accessible
- Ensure Docker Desktop is running
- Check VS Code shows "8123" in the Ports tab
- Try http://127.0.0.1:8123 instead of localhost

## Commands

```bash
# Start Home Assistant
bash .devcontainer/start-hass.sh

# Stop Home Assistant
pkill -f "python -m homeassistant"

# View integration files
ls -la /config/custom_components/real_electricity_price/

# Test integration loading
python -c "import custom_components.real_electricity_price"
```

## Next Steps

1. **Launch the dev container** following the Quick Start guide
2. **Add the integration** in Home Assistant UI  
3. **Make code changes** and see them reflected immediately
4. **Use integrated debugging** and testing tools
5. **Commit changes** using built-in Git integration
