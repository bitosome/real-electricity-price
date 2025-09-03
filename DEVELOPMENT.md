# 🚀 Quick Development Setup

To get started with development in **one click**:

```bash
# Clone the repository
git clone https://github.com/bitosome/real-electricity-price.git
cd real-electricity-price

# Start development environment (Podman-based)
make dev
# OR
./scripts/dev-setup.sh
```

This automatically:
- ✅ Sets up Podman containers  
- ✅ Installs HACS
- ✅ Syncs integration files
- ✅ Starts Home Assistant with Nginx proxy
- ✅ Provides maximum network discretion

Then access Home Assistant at **http://localhost:8080** (via proxy)

## 📋 Development Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start complete development environment (Podman) |
| `make sync` | Sync integration files to container |
| `make test` | Run all tests |
| `make lint` | Format and lint code |
| `make status` | Check environment status |
| `make logs` | View container logs |
| `make restart` | Restart Home Assistant container |
| `make logs-proxy` | View proxy logs |
| `make restart-proxy` | Restart proxy container |
| `make shell-proxy` | Access proxy container shell |
| `make stop` | Stop development environment |
| `make help` | Show all available commands |

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
2. **Sync to container**: `make sync`
3. **Run tests**: `make test`
4. **Check code quality**: `make lint`
5. **Commit changes**: `git commit`

Happy coding! 🎉
