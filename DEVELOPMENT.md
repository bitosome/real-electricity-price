# 🚀 Quick Development Setup

To get started with development in **one click**:

```bash
# Clone the repository
git clone https://github.com/bitosome/real-electricity-price.git
cd real-electricity-price

# Start development environment
make dev
# OR
./scripts/dev-setup.sh
```

Then access Home Assistant at **http://localhost:8123** (admin/admin)

## 📋 Development Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start complete development environment |
| `make sync` | Sync integration files to container |
| `make test` | Run all tests |
| `make lint` | Format and lint code |
| `make status` | Check environment status |
| `make help` | Show all available commands |

## 📁 Project Structure

- **`custom_components/real_electricity_price/`** - Main integration code
- **`scripts/`** - Development and utility scripts
- **`docker/`** - Docker configuration for testing
- **`README.md`** - Full documentation and user guide

## 📖 Full Documentation

See **[README.md](README.md)** for complete integration documentation, usage examples, and installation instructions.

## 🛠️ Development Workflow

1. **Make changes** to integration files
2. **Sync to container**: `make sync`
3. **Run tests**: `make test`
4. **Check code quality**: `make lint`
5. **Commit changes**: `git commit`

Happy coding! 🎉
