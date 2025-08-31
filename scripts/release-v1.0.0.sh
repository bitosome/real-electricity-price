#!/usr/bin/env bash
#
# Release Preparation Script for v1.0.0
#
# This script creates a clean git history and prepares the v1.0.0 release
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

# Confirm release preparation
confirm_release() {
    print_header "Real Electricity Price v1.0.0 Release Preparation"
    
    echo -e "${YELLOW}This script will:${NC}"
    echo -e "  1. Create a clean git history starting from v1.0.0"
    echo -e "  2. Remove all previous commits and references"
    echo -e "  3. Create an initial commit with current state"
    echo -e "  4. Create and push v1.0.0 tag"
    echo -e "  5. Force push to replace repository history"
    echo -e "\n${RED}⚠️  WARNING: This will PERMANENTLY delete all git history!${NC}"
    echo -e "${RED}⚠️  WARNING: This cannot be undone!${NC}"
    
    read -p "Are you sure you want to proceed? (type 'YES' to confirm): " confirm
    if [ "$confirm" != "YES" ]; then
        print_error "Release preparation cancelled"
        exit 1
    fi
}

# Backup current state
backup_state() {
    print_header "Creating Backup"
    
    local backup_branch="backup-$(date +%Y%m%d-%H%M%S)"
    print_status "Creating backup branch: $backup_branch"
    
    git checkout -b "$backup_branch"
    git push origin "$backup_branch"
    git checkout main
    
    print_success "Backup created on branch: $backup_branch"
}

# Clean git history
clean_history() {
    print_header "Cleaning Git History"
    
    print_status "Removing .git directory..."
    rm -rf .git
    
    print_status "Initializing new git repository..."
    git init
    
    print_status "Adding remote origin..."
    git remote add origin https://github.com/bitosome/real-electricity-price.git
    
    print_success "Git history cleaned"
}

# Create initial commit
create_initial_commit() {
    print_header "Creating Initial Commit"
    
    print_status "Staging all files..."
    git add .
    
    print_status "Creating initial commit..."
    git commit -m "🎉 Initial release v1.0.0

✨ Features:
- Real-time electricity pricing from Nord Pool with Estonian grid costs
- 10 comprehensive sensors (9 sensors + 1 button) for complete price monitoring
- Professional device architecture with grouped sensors and proper branding
- Smart tariff detection with automatic day/night/weekend/holiday recognition
- Configurable pricing structure supporting different grid operators and suppliers
- HACS compatibility with complete integration support

📊 Sensors:
- Current electricity price with real-time hourly updates
- Hourly prices for today and tomorrow (24-hour arrays with rich attributes)
- Min/Max price analytics for today and tomorrow
- Last data sync timestamp for monitoring data freshness
- Current tariff indicator (day/night) with Estonian holiday support
- Manual refresh button for instant data updates

🏗️ Architecture:
- Single device with multiple sensors for clean organization
- Professional manifest with proper dependencies and integration metadata
- Comprehensive error handling and logging throughout
- Efficient data coordinator with automatic updates and rate limiting
- Type-safe implementation with modern Home Assistant patterns

🛠️ Development:
- Complete one-click development environment with Docker
- Automated testing suite (syntax, import, config, docker, quality checks)
- Code quality tools with Ruff formatting and linting
- Makefile with convenient development commands
- Comprehensive scripts for setup, sync, test, and deployment

🎨 User Experience:
- Integration branding with icons and logos ready for Home Assistant brands
- Clear device and entity names with descriptive attributes
- Rich sensor attributes with price breakdowns and metadata
- Automation-friendly design with reliable state updates
- Professional troubleshooting documentation and user guides

🔧 Technical:
- Nord Pool API integration with robust error handling
- Estonian grid cost calculations with configurable parameters
- Holiday detection using Estonian calendar
- Efficient caching and data management
- Home Assistant 2025.8+ compatibility
- Python 3.11+ support with type annotations

This release provides a production-ready, feature-complete integration for Estonian 
electricity users with comprehensive development tooling for contributors."
    
    print_success "Initial commit created"
}

# Create and push tag
create_tag() {
    print_header "Creating Release Tag"
    
    print_status "Creating v1.0.0 tag..."
    git tag -a v1.0.0 -m "Release v1.0.0

Real Electricity Price Integration - Initial Stable Release

This is the first stable release of the Real Electricity Price integration for Home Assistant.

🎯 Key Features:
- Real-time Estonian electricity pricing with Nord Pool integration
- 10 comprehensive sensors for complete price monitoring and analytics
- Professional Home Assistant integration with HACS support
- Smart tariff detection with holiday and weekend recognition
- One-click development environment for contributors

📦 What's Included:
- Complete Home Assistant custom integration
- Professional device architecture with proper entity grouping
- Comprehensive documentation and user guides
- Development tools and testing framework
- HACS compatibility and metadata

🚀 Installation:
- HACS: Search for 'Real Electricity Price' in custom repositories
- Manual: Copy custom_components/real_electricity_price to your HA installation
- Configuration: Add via UI in Settings → Devices & Services

📖 Documentation:
- README.md: Complete user guide and examples
- DEVELOPMENT.md: Quick development setup guide
- scripts/README.md: Development workflow documentation

This release is ready for production use and provides a solid foundation for 
future enhancements and community contributions."
    
    print_success "Tag v1.0.0 created"
}

# Push to GitHub
push_release() {
    print_header "Pushing Release to GitHub"
    
    print_warning "This will force push and replace all repository history!"
    read -p "Continue with force push? (type 'YES' to confirm): " confirm
    if [ "$confirm" != "YES" ]; then
        print_error "Push cancelled"
        exit 1
    fi
    
    print_status "Force pushing to main branch..."
    git push --force origin main
    
    print_status "Pushing tags..."
    git push origin v1.0.0
    
    print_success "Release pushed successfully"
}

# Generate release information
generate_release_info() {
    print_header "Release Information"
    
    local repo_url="https://github.com/bitosome/real-electricity-price"
    local release_url="$repo_url/releases/new?tag=v1.0.0"
    
    echo -e "${GREEN}🎉 Release v1.0.0 is ready!${NC}\n"
    
    echo -e "${BLUE}📋 Release Details:${NC}"
    echo -e "   • Version: ${YELLOW}v1.0.0${NC}"
    echo -e "   • Tag: ${YELLOW}v1.0.0${NC}"
    echo -e "   • Repository: ${YELLOW}$repo_url${NC}"
    
    echo -e "\n${BLUE}🚀 Next Steps:${NC}"
    echo -e "   1. Create GitHub release: ${YELLOW}$release_url${NC}"
    echo -e "   2. Use the changelog content from CHANGELOG.md as release notes"
    echo -e "   3. Mark as 'Latest release'"
    echo -e "   4. Publish the release"
    
    echo -e "\n${BLUE}📖 Release Notes Template:${NC}"
    echo -e "${YELLOW}Copy the content from CHANGELOG.md [1.0.0] section for release notes${NC}"
    
    echo -e "\n${BLUE}🔗 HACS Integration:${NC}"
    echo -e "   • HACS will automatically detect the new release"
    echo -e "   • Users can install via HACS custom repositories"
    echo -e "   • Repository: bitosome/real-electricity-price"
    
    echo -e "\n${GREEN}✅ Release preparation completed successfully!${NC}\n"
}

# Main execution
main() {
    confirm_release
    backup_state
    clean_history
    create_initial_commit
    create_tag
    push_release
    generate_release_info
}

# Run the script
main "$@"
