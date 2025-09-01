# Changelog

All notable changes to this project will be documented in this file.

## v1.0.0 - Initial release
- Unified hourly refresh at hh:00 for all sensors using centralized coordinator tick
- Manual refresh triggers immediate update for all entities
- Removed unused “Current hour” attribute from Current Tariff sensor
- Fixed timezone handling by using Home Assistant local time
- Documentation refreshed for initial version
