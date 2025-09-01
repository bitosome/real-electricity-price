#!/usr/bin/env bash
#
# Generic Release Script for Real Electricity Price Integration
#
# This script bumps the version in all relevant files and creates a release
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <version>"
    echo "Example: $0 2.0.0"
    echo "         $0 1.2.3"
    exit 1
}

# Validate version format
validate_version() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format. Use semantic versioning (e.g., 2.0.0)"
        exit 1
    fi
}

# Check if version argument is provided
if [ $# -eq 0 ]; then
    show_usage
fi

VERSION=$1
validate_version $VERSION

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

print_header "Real Electricity Price v$VERSION Release"

# Change to repository root
cd "$REPO_ROOT"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Working directory is not clean. Uncommitted changes detected."
    echo "Please commit or stash your changes before creating a release."
    exit 1
fi

# Get current version from manifest.json
CURRENT_VERSION=$(grep '"version"' custom_components/real_electricity_price/manifest.json | sed -E 's/.*"version": "([^"]+)".*/\1/')
print_status "Current version: $CURRENT_VERSION"
print_status "New version: $VERSION"

# Confirm the release
echo -e "\n${YELLOW}This will:${NC}"
echo -e "  1. Update version in manifest.json"
echo -e "  2. Update version in brands payload manifest.json (if exists)"
echo -e "  3. Create a git tag v$VERSION"
echo -e "  4. Push the tag to origin"
echo -e ""
read -p "Continue with release v$VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Release cancelled"
    exit 0
fi

print_status "Creating release v$VERSION..."

# Update version in manifest.json
print_status "Updating version in custom_components/real_electricity_price/manifest.json"
sed -i.bak "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$VERSION\"/" custom_components/real_electricity_price/manifest.json
rm custom_components/real_electricity_price/manifest.json.bak

# Update version in brands payload manifest.json if it exists
BRANDS_MANIFEST="brands_payload/custom_integrations/real_electricity_price/manifest.json"
if [ -f "$BRANDS_MANIFEST" ]; then
    print_status "Updating version in $BRANDS_MANIFEST"
    sed -i.bak "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$VERSION\"/" "$BRANDS_MANIFEST"
    rm "$BRANDS_MANIFEST.bak"
fi

# Commit the version changes
print_status "Committing version bump"
git add custom_components/real_electricity_price/manifest.json
if [ -f "$BRANDS_MANIFEST" ]; then
    git add "$BRANDS_MANIFEST"
fi
git commit -m "Bump version to v$VERSION"

# Create git tag
print_status "Creating git tag v$VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION

Real Electricity Price Integration v$VERSION

Changes in this release:
- See CHANGELOG.md for detailed changes
- Updated integration components
- Bug fixes and improvements"

# Push changes and tag
print_status "Pushing changes and tag to origin"
git push origin main
git push origin "v$VERSION"

print_success "Release v$VERSION created successfully!"

print_header "Release Summary"
echo -e "   • Version: ${YELLOW}v$VERSION${NC}"
echo -e "   • Tag: ${YELLOW}v$VERSION${NC}"
echo -e "   • Manifest updated: ${GREEN}✓${NC}"
if [ -f "$BRANDS_MANIFEST" ]; then
    echo -e "   • Brands manifest updated: ${GREEN}✓${NC}"
fi
echo -e "   • Git tag created: ${GREEN}✓${NC}"
echo -e "   • Changes pushed: ${GREEN}✓${NC}"

print_header "Next Steps"
echo -e "   1. Create a GitHub release from the tag v$VERSION"
echo -e "   2. Update CHANGELOG.md with release notes"
echo -e "   3. Announce the release if needed"
echo -e "   4. Monitor for any issues"

print_success "Release process completed!"
