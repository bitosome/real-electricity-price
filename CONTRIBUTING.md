# Contributing

Thanks for your interest in contributing! 🎉

## Quick Start

1. **Fork** the repository
2. **Create a branch** from `main`
3. **Make your changes**
4. **Test your changes**: `cd tests && ./test.sh`
5. **Format code**: `ruff check . --fix && ruff format .`
6. **Submit a pull request**

## Development Environment

```bash
# One-click setup
./scripts/dev-setup.sh

# Access Home Assistant at http://localhost:8080
# Make changes and sync with:
./scripts/sync-integration.sh
```

## Code Quality

- **Format**: `ruff format custom_components/real_electricity_price/`
- **Lint**: `ruff check custom_components/real_electricity_price/ --fix`
- **Test**: `cd tests && ./test.sh`
- **All tests run automatically** on GitHub Actions for every PR

## Bug Reports

Use [GitHub Issues](../../issues/new/choose) to report bugs with:
- Steps to reproduce
- Expected vs actual behavior  
- Home Assistant version
- Integration configuration

## License

All contributions are under the [MIT License](LICENSE).

For detailed development info, see [`scripts/README.md`](scripts/README.md).
