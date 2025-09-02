#!/usr/bin/env bash
#
# Real Electricity Price - One-Click Development Setup
# 
# This script sets up the complete development environment with Home Assistant
# running in Docker and the integration ready for testing.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

# Check if Podman is available
check_podman() {
    print_header "Checking Podman"
    
    if ! command -v podman &> /dev/null; then
        print_error "Podman is not installed. Please install Podman first."
        print_status "On macOS: brew install podman"
        print_status "On Linux: https://podman.io/getting-started/installation"
        exit 1
    fi
    
    if ! command -v podman-compose &> /dev/null; then
        print_error "podman-compose is not installed. Please install it first."
        print_status "Install with: pip install podman-compose"
        exit 1
    fi
    
    # Start podman machine if on macOS and not running
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! podman machine list --format="{{.Name}}" | grep -q "podman-machine-default"; then
            print_status "Initializing Podman machine..."
            podman machine init
        fi
        
        if ! podman machine list --format="{{.Running}}" | grep -q "true"; then
            print_status "Starting Podman machine..."
            podman machine start
        fi
    fi
    
    print_success "Podman is ready"
}

# Sync integration files to container config
sync_integration() {
    print_header "Syncing Integration Files"
    
    SOURCE_DIR="$PROJECT_ROOT/custom_components/real_electricity_price"
    TARGET_DIR="$PROJECT_ROOT/container/config/custom_components/real_electricity_price"
    
    # Create target directory if it doesn't exist
    mkdir -p "$TARGET_DIR"
    
    # Copy all files
    print_status "Copying integration files..."
    cp -r "$SOURCE_DIR/"* "$TARGET_DIR/"
    
    print_success "Integration files synced"
}

# Install HACS if not already present
install_hacs() {
    print_header "Installing HACS"
    
    local HACS_DIR="$PROJECT_ROOT/container/config/custom_components/hacs"
    
    if [ -d "$HACS_DIR" ] && [ -f "$HACS_DIR/manifest.json" ]; then
        print_status "HACS already installed"
        return
    fi
    
    print_status "Installing HACS..."
    "$PROJECT_ROOT/scripts/install-hacs.sh"
    print_success "HACS installation completed"
}

# Stop any existing containers
stop_existing() {
    print_header "Stopping Existing Containers"
    
    if podman ps -q -f name=dc | grep -q .; then
        print_status "Stopping existing container..."
        podman stop dc > /dev/null
        podman rm dc > /dev/null
        print_success "Existing container stopped"
    else
        print_status "No existing container found"
    fi
}

# Start Home Assistant container
start_homeassistant() {
    print_header "Starting Home Assistant"
    
    cd "$PROJECT_ROOT"
    
    print_status "Starting Home Assistant container..."
    podman-compose up -d
    
    print_status "Waiting for Home Assistant to start..."
    sleep 10
    
    # Wait for Home Assistant to be ready through proxy
    local retries=30
    while [ $retries -gt 0 ]; do
        if curl -s -f http://localhost:8080 > /dev/null 2>&1; then
            break
        fi
        print_status "Waiting for proxy and Home Assistant... ($retries seconds left)"
        sleep 1
        retries=$((retries - 1))
    done
    
    if [ $retries -eq 0 ]; then
        print_warning "Home Assistant took longer than expected to start"
        print_status "Check proxy status with: podman logs web"
        print_status "Check HA status with: podman logs dc"
    else
        print_success "Home Assistant is running behind proxy"
    fi
}

# Check integration status
check_integration() {
    print_header "Checking Integration Status"
    
    print_status "Checking if integration is loaded..."
    sleep 5
    
    # Check logs for integration loading
    if podman logs dc 2>&1 | grep -q "real_electricity_price"; then
        print_success "Integration appears to be loaded"
    else
        print_warning "Integration may not be loaded yet"
    fi
    
    print_status "Recent logs:"
    podman logs dc --tail 10
}

# Show final information
show_info() {
    print_header "Development Environment Ready"
    
    echo -e "${GREEN}🎉 Your development environment is ready!${NC}\n"
    
    echo -e "${BLUE}📋 Access Information:${NC}"
    echo -e "   • Home Assistant UI: ${YELLOW}http://localhost:8080${NC}"
    echo -e "   • Direct Access (internal): ${YELLOW}http://localhost:8123${NC}"
    echo -e "   • Container Name: ${YELLOW}dc${NC}"
    echo -e "   • Proxy Container: ${YELLOW}web${NC}"
    
    echo -e "\n${BLUE}🛠️  Development Commands:${NC}"
    echo -e "   • View HA logs: ${YELLOW}podman logs dc --tail 50 -f${NC}"
    echo -e "   • View proxy logs: ${YELLOW}podman logs web --tail 50 -f${NC}"
    echo -e "   • Restart HA: ${YELLOW}podman restart dc${NC}"
    echo -e "   • Restart proxy: ${YELLOW}podman restart web${NC}"
    echo -e "   • Stop environment: ${YELLOW}podman-compose down${NC}"
    echo -e "   • Sync files: ${YELLOW}./scripts/sync-integration.sh${NC}"
    echo -e "   • Run linting: ${YELLOW}./scripts/lint.sh${NC}"
    
    echo -e "\n${BLUE}📁 Integration Setup:${NC}"
    echo -e "   • Go to Settings → Devices & Services"
    echo -e "   • Click 'Add Integration'"
    echo -e "   • Search for 'Real Electricity Price'"
    echo -e "   • Configure your settings"
    
    echo -e "\n${BLUE}🛡️  Network Discretion:${NC}"
    echo -e "   • Access via proxy: ${YELLOW}port 8080 (generic web server)${NC}"
    echo -e "   • Home Assistant hidden: ${YELLOW}no direct access on 8123${NC}"
    echo -e "   • Server identity: ${YELLOW}appears as 'Web Server'${NC}"
    echo -e "   • Container names: ${YELLOW}'dc' and 'web' (non-descriptive)${NC}"
    
    echo -e "\n${BLUE}🏪 HACS Setup:${NC}"
    echo -e "   • HACS is pre-installed and ready"
    echo -e "   • Go to Settings → Devices & Services"
    echo -e "   • Configure HACS integration"
    echo -e "   • Add custom repository: ${YELLOW}https://github.com/bitosome/real-electricity-price${NC}"
    
    echo -e "\n${BLUE}🔧 File Changes:${NC}"
    echo -e "   • Edit files in: ${YELLOW}custom_components/real_electricity_price/${NC}"
    echo -e "   • Run sync script to update container"
    echo -e "   • Restart Home Assistant to see changes"
    
    echo -e "\n${GREEN}Happy coding! 🚀${NC}\n"
}

# Main execution
main() {
    echo -e "\n${GREEN}🏠 Real Electricity Price - Development Setup${NC}\n"
    
    check_podman
    sync_integration
    install_hacs
    stop_existing
    start_homeassistant
    check_integration
    show_info
}

# Run main function
main "$@"
