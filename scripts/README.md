# Version Management

This directory contains scripts for managing versions and releases.

## Version Bump Script

The `bump_version.py` script automates the process of bumping versions and creating GitHub releases for HACS.

### Usage

```bash
# Patch version (0.1.0 → 0.1.1) - for bug fixes
python scripts/bump_version.py patch -m "Fixed critical bug in sensor"

# Minor version (0.1.0 → 0.2.0) - for new features
python scripts/bump_version.py minor -m "Added new sensor for tomorrow's prices"

# Major version (0.1.0 → 1.0.0) - for breaking changes
python scripts/bump_version.py major -m "Complete rewrite with breaking changes"
```

### What it does

1. **Updates `manifest.json`** with the new version number
2. **Commits all changes** to git
3. **Creates and pushes a git tag** (e.g., `v0.1.1`)
4. **Provides a GitHub release URL** for manual completion
5. **Shows suggested changelog** text

### HACS Integration

After running the script:

1. **Go to the provided GitHub URL** to create the release
2. **Add the suggested changelog** as the release description
3. **Publish the release**
4. **HACS will automatically detect** the new version within a few minutes
5. **Users will get update notifications** in Home Assistant

### Version Numbering

Follow semantic versioning:
- **Patch** (x.x.1): Bug fixes, small improvements
- **Minor** (x.1.x): New features, backward compatible
- **Major** (1.x.x): Breaking changes, major rewrites

### Example Workflow

```bash
# After fixing a bug
git add .
git commit -m "Fix sensor initialization bug"
python scripts/bump_version.py patch -m "Fixed sensor initialization issue"

# Go to GitHub and create the release
# HACS users will get update notification
```
