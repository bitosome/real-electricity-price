# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-08-31

### Added
- Initial stable release of Real Electricity Price integration
- Real-time electricity pricing for Estonia from Nord Pool
- 9 comprehensive sensor types for complete price monitoring
- Day/night tariff support with Estonian holidays
- Manual refresh button for forced data updates
- Complete Home Assistant configuration flow
- Comprehensive documentation and usage examples
- Docker development environment
- HACS compatibility

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
