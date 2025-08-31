#!/usr/bin/env bash
#
# Local Development with Home Assistant Core
#
# This script runs Home Assistant Core locally with the integration loaded.
# Note: For Docker-based development, use ./dev-setup.sh instead.
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$(dirname "$0")/.."

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Setup local configuration
setup_config() {
    print_header "Setting up Local Configuration"
    
    # Create config dir if not present
    if [[ ! -d "${PWD}/config" ]]; then
        print_status "Creating config directory..."
        mkdir -p "${PWD}/config"
        
        if command -v hass &> /dev/null; then
            hass --config "${PWD}/config" --script ensure_config
        else
            print_warning "Home Assistant Core not installed. Run ./scripts/setup.sh first."
            exit 1
        fi
    fi
    
    print_success "Configuration ready"
}

# Start Home Assistant
start_homeassistant() {
    print_header "Starting Home Assistant Core"
    
    # Set the path to custom_components
    ## This let's us have the structure we want <root>/custom_components/real_electricity_price
    ## while at the same time have Home Assistant configuration inside <root>/config
    ## without resulting to symlinks.
    export PYTHONPATH="${PYTHONPATH}:${PWD}/custom_components"
    
    print_status "Starting Home Assistant in debug mode..."
    print_status "Access Home Assistant at: http://localhost:8123"
    print_status "Press Ctrl+C to stop"
    
    # Start Home Assistant
    hass --config "${PWD}/config" --debug
}

# Main execution
main() {
    echo -e "\n${GREEN}🏠 Starting Local Home Assistant Development${NC}\n"
    
    setup_config
    start_homeassistant
}

# Run main function
main "$@"
