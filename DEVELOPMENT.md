# 🚀 Quick Development Setup

To get started with development in **one click**:

```bash
# Clone the repository
git clone https://github.com/bitosome/real-electricity-price.git
cd real-electricity-price

# Start development environment (Podman-based)
./scripts/dev-setup.sh
```

This automatically:
- ✅ Sets up Podman containers  
- ✅ Installs HACS
- ✅ Syncs integration files
- ✅ Starts Home Assistant with Nginx proxy
- ✅ Provides maximum network discretion

Then access Home Assistant at **http://localhost:8080** (via proxy)

## 📋 Development Scripts

| Script | Description |
|---------|-------------|
| `./scripts/dev-setup.sh` | Start complete development environment (Podman) |
| `./scripts/sync-integration.sh` | Sync integration files to container |
| `./scripts/restart-ha.sh` | Restart Home Assistant with connectivity fixes |
| `cd tests && ./test.sh` | Run all tests |
| `ruff check . --fix && ruff format .` | Format and lint code |

## 🐳 Container Commands

| Command | Description |
|---------|-------------|
| `podman-compose up -d` | Start containers manually |
| `podman logs dc -f` | View Home Assistant logs |
| `podman logs web -f` | View proxy logs |
| `podman restart dc` | Restart HA |
| `podman restart web` | Restart proxy |
| `podman-compose down` | Stop all containers |

## 📁 Project Structure

- **`custom_components/real_electricity_price/`** - Main integration code
- **`scripts/`** - Development and utility scripts  
- **`container/config/`** - Podman container configuration
- **`docker-compose.yml`** - Container orchestration using podman-compose
- **`README.md`** - Full documentation and user guide

## 🏪 HACS Integration

HACS is **automatically installed** in the development environment:

1. Configure HACS in Home Assistant
2. Add custom repository: `https://github.com/bitosome/real-electricity-price`
3. Download integration via HACS
4. Test HACS installation workflow

## 📖 Full Documentation

See **[README.md](README.md)** for complete integration documentation, usage examples, and installation instructions.

## 🛠️ Development Workflow

1. **Make changes** to integration files
2. **Sync to container**: `./scripts/sync-integration.sh`
3. **Run tests**: `cd tests && ./test.sh`
4. **Check code quality**: `ruff check . --fix && ruff format .`
5. **Commit changes**: `git commit`

Happy coding! 🎉
