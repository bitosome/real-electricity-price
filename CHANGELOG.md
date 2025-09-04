# Changelog

> **Note**: Starting with v1.2.0, changelogs are maintained in [GitHub Releases](../../releases).

All notable changes to this project will be documented in this file.

## v2.0.0 - 2025-09-04
- Version bump to v2.0.0
- For detailed changes, see [GitHub Releases](../../releases/tag/v2.0.0)

- Version bump to v1.5.1
- For detailed changes, see [GitHub Releases](../../releases/tag/v1.5.1)

- Version bump to v1.5.0
- For detailed changes, see [GitHub Releases](../../releases/tag/v1.5.0)

- **NEW**: Added Cheapest Prices sensor with pandas-powered analysis
- **NEW**: Configurable cheap price threshold (default 10% above minimum price)
- **NEW**: Smart time range grouping for consecutive cheap hours
- **NEW**: Rich attributes with detailed price statistics and analysis info
- **FEATURE**: Automatic detection of optimal electricity usage periods
- **DEPENDENCY**: Added pandas>=1.3.0 for efficient data analysis
- **UI**: Added cheap price threshold configuration option
- **DOCS**: Updated README with new sensor documentation and examples

## v1.0.0 - Initial release
- Unified hourly refresh at hh:00 for all sensors using centralized coordinator tick
- Manual refresh triggers immediate update for all entities
- Removed unused “Current hour” attribute from Current Tariff sensor
- Fixed timezone handling by using Home Assistant local time
- Documentation refreshed for initial version
