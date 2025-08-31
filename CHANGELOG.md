# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-08-31

### 🎉 Initial Release

This is the initial stable release of the Real Electricity Price integration for Home Assistant.

#### ✨ Features
- **Real-time electricity pricing** from Nord Pool with Estonian grid costs
- **10 comprehensive sensors** providing current prices, forecasts, and analytics
- **Professional device architecture** with grouped sensors and proper branding
- **Smart tariff detection** with automatic day/night/weekend/holiday recognition
- **Configurable pricing structure** supporting different grid operators and suppliers
- **HACS compatibility** with complete integration support
- **One-click development environment** with Docker and comprehensive tooling

#### 📊 Sensors
- Current electricity price with real-time updates
- Hourly prices for today and tomorrow (24-hour arrays)
- Min/Max price analytics for today and tomorrow
- Last data sync timestamp for monitoring
- Current tariff indicator (day/night)
- Manual refresh button for instant updates

#### 🏗️ Architecture
- Single device with multiple sensors for clean organization
- Professional manifest with proper dependencies and metadata
- Comprehensive error handling and logging
- Efficient data coordinator with automatic updates
- Type-safe implementation with modern Python patterns

#### 🛠️ Development
- Complete development environment with Docker
- Automated testing suite with syntax, import, and integration checks
- Code quality tools with Ruff formatting and linting
- One-click setup with `make dev` or `./scripts/dev-setup.sh`
- Comprehensive documentation and contribution guidelines

#### 🎨 User Experience
- Integration branding with icons and logos
- Clear device and entity names with descriptive attributes
- Rich sensor attributes with price breakdowns and metadata
- Automation-friendly design with reliable state updates
- Professional troubleshooting documentation

This release provides a production-ready, feature-complete integration for Estonian electricity users with comprehensive development tooling for contributors.

### Features
- **Current Price**: Real-time electricity price with all fees included
- **Price Tomorrow**: Next day pricing at current time
- **Current Tariff**: Day/night tariff determination
- **Last Sync**: Data synchronization tracking
- **Price Data**: Complete raw price information
- **Daily Statistics**: Min/max/average daily prices
- **Tomorrow Statistics**: Next day price statistics
- **State Classification**: Price level categorization
- **Network Fee**: Detailed network cost breakdown

### Technical
- Async/await architecture for optimal performance
- Robust error handling and retry mechanisms
- Configurable update intervals
- Estonian holiday calendar integration
- Nord Pool API integration with rate limiting
- Type-safe Python code with comprehensive annotations
- Modular sensor architecture for easy maintenance

### Documentation
- Complete installation and configuration guide
- Home Assistant automation examples
- Troubleshooting and FAQ section
- Developer setup instructions
- API documentation and usage examples
