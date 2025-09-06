# Changelog

> **Note**: Starting with v1.2.0, changelogs are maintained in [GitHub Releases](../../releases).

All notable changes to this project will be documented in this file.

## v1.1.0 - 2025-09-06

### New Features
- **Dual Off-peak Strategy System**: Choose between traditional night windows or Nord Pool blocks
- **Nord Pool Blocks Alignment**: Off-peak 1 (00-07h), Peak (08-19h), Off-peak 2 (20-23h) 
- **Extended Market Coverage**: Added support for Central-Western Europe areas (DE-LU, NL, BE, FR, AT, PL, GB)
- **Regional Holiday Support**: Subdivision codes for German states, French territories, Norwegian counties
- **Enhanced Translations**: Complete UI with Nord Pool region-specific examples
- **Strategy-aware Configuration**: UI adapts based on selected off-peak method

### Improvements  
- **Comprehensive Test Suite**: 200+ test scenarios covering all strategy combinations
- **All Area Validation**: Tests for all 17 supported Nord Pool areas
- **Code Quality**: Fixed 400+ linting errors and warnings
- **Import System**: Improved relative imports and module structure
- **Documentation**: Updated README with comprehensive feature guide

### Bug Fixes
- Fixed `NameError: strategy is not defined` in api.py
- Corrected dropdown translations for strategy selection
- Fixed magic number constants and exception handling
- Resolved import issues in sensor modules

## v1.0.1 - 2025-09-05
- Version bump for release

## v1.0.0 - 2025-09-05
- Version reset to v1.0.0
- For detailed changes, see [GitHub Releases](../../releases/tag/v1.0.0)

