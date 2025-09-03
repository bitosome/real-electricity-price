# Development Scripts

This directory contains all development and utility scripts for the Real Electricity Price integration.

## 🚀 Quick Start

### One-Click Development Setup
```bash
./scripts/dev-setup.sh
```
This script sets up the complete development environment with Home Assistant running in Podman.

## 📋 Available Scripts

### 🏗️ Environment Setup
- **`dev-setup.sh`** - Complete one-click development environment setup with Podman
- **`init-homeassistant.sh`** - Initialize Home Assistant configuration
- **`install-hacs.sh`** - Install HACS (Home Assistant Community Store) automatically

### 🔄 Development Workflow
- **`sync-integration.sh`** - Sync integration files to Podman container
- **`restart-ha.sh`** - Restart Home Assistant with connectivity fixes

### 🚀 Release Management  
- **`release.sh`** - Release management script
- **`generate_password_hash.py`** - Generate password hashes for testing

### 🧪 Testing
Tests are located in the `tests/` directory:
- **`tests/test.sh`** - Run comprehensive integration tests
- **`tests/test_all_comprehensive.py`** - Master test runner with category support
- **`tests/test_config_validation.py`** - Configuration validation tests
- **`tests/test_sensor_calculations.py`** - Sensor calculation tests
- **`tests/test_buttons_calculations.py`** - Button and cheap price calculation tests
- **`tests/test_integration.py`** - Core integration tests
- **`tests/test-hacs-e2e.sh`** - End-to-end HACS tests

## 📖 Script Details

### dev-setup.sh
**One-click development environment setup**

Features:
- ✅ Checks Podman availability
- ✅ Sets up Podman machine (macOS)
- ✅ Syncs integration files to container
- ✅ Installs HACS automatically
- ✅ Starts Home Assistant container
- ✅ Waits for Home Assistant to be ready
- ✅ Shows access information and next steps

Usage:
```bash
./scripts/dev-setup.sh
```

After running, access Home Assistant at http://localhost:8123

### sync-integration.sh
**Sync integration files to Podman container**

Use this when you make changes to integration files and want to test them:

```bash
./scripts/sync-integration.sh
```

Automatically restarts Home Assistant container after syncing.

### restart-ha.sh
**Restart Home Assistant with connectivity fixes**

```bash
./scripts/restart-ha.sh
```

This script includes fixes for proxy connectivity and ensures proper startup.

## 🔧 Development Workflow

### First Time Setup
1. **Start development environment:**
   ```bash
   ./scripts/dev-setup.sh
   ```

2. **Access Home Assistant at http://localhost:8123**

### Daily Development
1. **Make changes to integration files**
2. **Sync and test:**
   ```bash
   ./scripts/sync-integration.sh
   cd tests && ./test.sh
   ```
3. **Check code quality with ruff:**
   ```bash
   ruff check custom_components/real_electricity_price/
   ruff format custom_components/real_electricity_price/
   ```

### Before Committing
```bash
# Format and lint code
ruff check custom_components/real_electricity_price/ --fix
ruff format custom_components/real_electricity_price/

# Run all tests
cd tests && ./test.sh

# Add and commit
git add .
git commit -m "Your commit message"
```

## 🐳 Podman Commands

The development environment provides these useful commands:

```bash
# View logs
podman logs dc --tail 50 -f

# Restart Home Assistant
podman restart dc

# Stop environment
podman-compose down

# Access container shell
podman exec -it dc bash
```

## 🔍 Troubleshooting

### Script Not Executable
```bash
chmod +x scripts/*.sh
```

### Podman Issues
```bash
# Check Podman status
podman ps

# Check container logs
podman logs dc

# Restart Podman container
podman restart dc
```

### Import Errors
```bash
# Check Python path in tests
cd tests && ./test.sh import

# Validate syntax
cd tests && ./test.sh syntax
```

## 📁 File Structure

```
scripts/
├── README.md                 # This file
├── dev-setup.sh             # One-click development setup
├── sync-integration.sh      # Sync files to Podman
├── restart-ha.sh            # Restart HA with fixes
├── init-homeassistant.sh    # Initialize HA configuration
├── install-hacs.sh          # Install HACS automatically
├── release.sh               # Release management
└── generate_password_hash.py # Password hash utility
```

## 🎯 Tips

- **Always run `./scripts/dev-setup.sh` for new development sessions**
- **Use `./scripts/sync-integration.sh` after making changes**
- **Run `cd tests && ./test.sh` before committing**
- **Keep Podman running for faster development cycles**
- **Use ruff directly for code quality: `ruff check . --fix && ruff format .`**
- **All tests are automated via GitHub Actions on push/PR**

Happy coding! 🚀
