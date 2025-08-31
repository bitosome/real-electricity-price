# Development Scripts

This directory contains all development and utility scripts for the Real Electricity Price integration.

## 🚀 Quick Start

### One-Click Development Setup
```bash
./scripts/dev-setup.sh
```
This script sets up the complete development environment with Home Assistant running in Docker.

## 📋 Available Scripts

### 🏗️ Environment Setup
- **`setup.sh`** - Install all development dependencies and tools
- **`dev-setup.sh`** - Complete one-click development environment setup with Docker

### 🔄 Development Workflow
- **`sync-integration.sh`** - Sync integration files to Docker container
- **`develop.sh`** - Run Home Assistant Core locally (alternative to Docker)
- **`test.sh`** - Run comprehensive integration tests
- **`lint.sh`** - Code formatting and quality checks

### 🎨 Utilities
- **`prepare_brand_assets.sh`** - Prepare branding assets for submission

## 📖 Script Details

### dev-setup.sh
**One-click development environment setup**

Features:
- ✅ Checks Docker availability
- ✅ Syncs integration files
- ✅ Stops existing containers
- ✅ Starts Home Assistant in Docker
- ✅ Waits for startup completion
- ✅ Shows access information and commands

Usage:
```bash
./scripts/dev-setup.sh
```

After running, access Home Assistant at http://localhost:8123 (admin/admin)

### sync-integration.sh
**Sync integration files to Docker container**

Use this when you make changes to integration files and want to test them:

```bash
./scripts/sync-integration.sh
```

Automatically restarts Home Assistant container after syncing.

### test.sh
**Comprehensive testing suite**

Run all tests:
```bash
./scripts/test.sh
```

Run specific tests:
```bash
./scripts/test.sh syntax   # Syntax check only
./scripts/test.sh import   # Import test only
./scripts/test.sh config   # Configuration validation
./scripts/test.sh docker   # Docker integration test
./scripts/test.sh quality  # Code quality check
```

### lint.sh
**Code formatting and quality**

```bash
./scripts/lint.sh
```

Features:
- ✅ Code formatting with Ruff
- ✅ Linting with automatic fixes
- ✅ Syntax validation
- ✅ Integration file checks

### setup.sh
**Development environment setup**

```bash
./scripts/setup.sh
```

Features:
- ✅ Installs Python requirements
- ✅ Installs development tools (ruff, black, mypy)
- ✅ Sets up pre-commit hooks

### develop.sh
**Local Home Assistant Core development**

For development without Docker:

```bash
./scripts/develop.sh
```

Requirements:
- Home Assistant Core installed locally
- Python 3.11+ environment

## 🔧 Development Workflow

### First Time Setup
1. **Install dependencies:**
   ```bash
   ./scripts/setup.sh
   ```

2. **Start development environment:**
   ```bash
   ./scripts/dev-setup.sh
   ```

3. **Access Home Assistant at http://localhost:8123**

### Daily Development
1. **Make changes to integration files**
2. **Sync and test:**
   ```bash
   ./scripts/sync-integration.sh
   ./scripts/test.sh
   ```
3. **Check code quality:**
   ```bash
   ./scripts/lint.sh
   ```

### Before Committing
```bash
./scripts/lint.sh      # Format and lint code
./scripts/test.sh      # Run all tests
git add .
git commit -m "Your commit message"
```

## 🐳 Docker Commands

The development environment provides these useful commands:

```bash
# View logs
docker logs hass-real-electricity-price-test --tail 50 -f

# Restart Home Assistant
docker restart hass-real-electricity-price-test

# Stop environment
docker compose down

# Access container shell
docker exec -it hass-real-electricity-price-test bash
```

## 🔍 Troubleshooting

### Script Not Executable
```bash
chmod +x scripts/*.sh
```

### Docker Issues
```bash
# Check Docker status
docker ps

# Check container logs
docker logs hass-real-electricity-price-test

# Restart Docker
docker restart hass-real-electricity-price-test
```

### Import Errors
```bash
# Check Python path
./scripts/test.sh import

# Validate syntax
./scripts/test.sh syntax
```

## 📁 File Structure

```
scripts/
├── README.md                 # This file
├── dev-setup.sh             # One-click development setup
├── setup.sh                 # Install dependencies
├── sync-integration.sh      # Sync files to Docker
├── develop.sh               # Local HA Core development
├── test.sh                  # Testing suite
├── lint.sh                  # Code quality
└── prepare_brand_assets.sh  # Branding utilities
```

## 🎯 Tips

- **Always run `./scripts/dev-setup.sh` for new development sessions**
- **Use `./scripts/sync-integration.sh` after making changes**
- **Run `./scripts/test.sh` before committing**
- **Keep Docker running for faster development cycles**
- **Use `./scripts/lint.sh` to maintain code quality**

Happy coding! 🚀
