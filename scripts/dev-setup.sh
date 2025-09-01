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

# Check if Docker is running
check_docker() {
    print_header "Checking Docker"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker is running"
}

# Sync integration files to docker config
sync_integration() {
    print_header "Syncing Integration Files"
    
    SOURCE_DIR="$PROJECT_ROOT/custom_components/real_electricity_price"
    TARGET_DIR="$PROJECT_ROOT/docker/config/custom_components/real_electricity_price"
    
    # Create target directory if it doesn't exist
    mkdir -p "$TARGET_DIR"
    
    # Copy all files
    print_status "Copying integration files..."
    cp -r "$SOURCE_DIR/"* "$TARGET_DIR/"
    
    print_success "Integration files synced"
}

# Stop any existing containers
stop_existing() {
    print_header "Stopping Existing Containers"
    
    if docker ps -q -f name=hass-real-electricity-price-test | grep -q .; then
        print_status "Stopping existing container..."
        docker stop hass-real-electricity-price-test > /dev/null
        docker rm hass-real-electricity-price-test > /dev/null
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
    docker compose up -d
    
    print_status "Waiting for Home Assistant to start..."
    sleep 10
    
    # Wait for Home Assistant to be ready
    local retries=30
    while [ $retries -gt 0 ]; do
        if curl -s -f http://localhost:8123 > /dev/null 2>&1; then
            break
        fi
        print_status "Waiting for Home Assistant... ($retries seconds left)"
        sleep 1
        retries=$((retries - 1))
    done
    
    if [ $retries -eq 0 ]; then
        print_warning "Home Assistant took longer than expected to start"
        print_status "Check status with: docker logs hass-real-electricity-price-test"
    else
        print_success "Home Assistant is running"
    fi
}

# Check integration status
check_integration() {
    print_header "Checking Integration Status"
    
    print_status "Checking if integration is loaded..."
    sleep 5
    
    # Check logs for integration loading
    if docker logs hass-real-electricity-price-test 2>&1 | grep -q "real_electricity_price"; then
        print_success "Integration appears to be loaded"
    else
        print_warning "Integration may not be loaded yet"
    fi
    
    print_status "Recent logs:"
    docker logs hass-real-electricity-price-test --tail 10
}

# Show final information
show_info() {
    print_header "Development Environment Ready"
    
    echo -e "${GREEN}🎉 Your development environment is ready!${NC}\n"
    
    echo -e "${BLUE}📋 Access Information:${NC}"
    echo -e "   • Home Assistant UI: ${YELLOW}http://localhost:8123${NC}"
    echo -e "   • Default Login: ${YELLOW}admin / admin${NC}"
    echo -e "   • Container Name: ${YELLOW}hass-real-electricity-price-test${NC}"
    
    echo -e "\n${BLUE}🛠️  Development Commands:${NC}"
    echo -e "   • View logs: ${YELLOW}docker logs hass-real-electricity-price-test --tail 50 -f${NC}"
    echo -e "   • Restart HA: ${YELLOW}docker restart hass-real-electricity-price-test${NC}"
    echo -e "   • Stop environment: ${YELLOW}docker compose down${NC}"
    echo -e "   • Sync files: ${YELLOW}./scripts/sync-integration.sh${NC}"
    echo -e "   • Run linting: ${YELLOW}./scripts/lint.sh${NC}"
    
    echo -e "\n${BLUE}📁 Integration Setup:${NC}"
    echo -e "   • Go to Settings → Devices & Services"
    echo -e "   • Click 'Add Integration'"
    echo -e "   • Search for 'Real Electricity Price'"
    echo -e "   • Configure your settings"
    
    echo -e "\n${BLUE}🔧 File Changes:${NC}"
    echo -e "   • Edit files in: ${YELLOW}custom_components/real_electricity_price/${NC}"
    echo -e "   • Run sync script to update container"
    echo -e "   • Restart Home Assistant to see changes"
    
    echo -e "\n${GREEN}Happy coding! 🚀${NC}\n"
}

# Main execution
main() {
    echo -e "\n${GREEN}🏠 Real Electricity Price - Development Setup${NC}\n"
    
    check_docker
    sync_integration
    stop_existing
    start_homeassistant
    check_integration
    show_info
}

# Run main function
main "$@"
