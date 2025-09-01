#!/usr/bin/env bash
#
# HACS E2E Test Runner
#
# This script runs the end-to-end test for HACS installation
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

# Check dependencies
check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    print_status "✅ Python 3 found"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    print_status "✅ Docker found"
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_status "✅ Docker daemon running"
    
    # Check if port 8123 is available
    if lsof -Pi :8123 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 8123 is already in use. The test will try to use it anyway."
    else
        print_status "✅ Port 8123 is available"
    fi
}

# Install Python dependencies
install_dependencies() {
    print_header "Installing Python Dependencies"
    
    if [ -f "test-requirements.txt" ]; then
        print_status "Installing test requirements..."
        pip3 install -r test-requirements.txt
        print_success "Dependencies installed"
    else
        print_warning "test-requirements.txt not found, installing manually..."
        pip3 install aiohttp docker PyYAML pytest pytest-asyncio
        print_success "Dependencies installed manually"
    fi
}

# Clean up any existing test containers
cleanup_existing() {
    print_header "Cleaning Up Existing Test Containers"
    
    # Stop and remove existing test containers
    if docker ps -a --format "table {{.Names}}" | grep -q "hass-e2e-test"; then
        print_status "Stopping existing test container..."
        docker stop hass-e2e-test 2>/dev/null || true
        docker rm hass-e2e-test 2>/dev/null || true
        print_success "Existing container cleaned up"
    else
        print_status "No existing test containers found"
    fi
    
    # Clean up test config directory
    if [ -d "/tmp/hass-e2e-config" ]; then
        print_status "Cleaning up test configuration..."
        rm -rf /tmp/hass-e2e-config
        print_success "Test configuration cleaned up"
    fi
}

# Run the test
run_test() {
    print_header "Running HACS E2E Test"
    
    print_status "Starting comprehensive integration test..."
    print_status "This test will:"
    echo "  1. 🚀 Start Home Assistant in Docker"
    echo "  2. 📦 Install Real Electricity Price via HACS simulation"
    echo "  3. ⚙️ Configure the integration"
    echo "  4. 🔍 Verify all entities are created"
    echo "  5. 📊 Test entity data and attributes"
    echo "  6. 🧹 Clean up resources"
    echo ""
    
    if python3 test_hacs_e2e.py; then
        print_success "🎉 HACS E2E Test PASSED!"
        return 0
    else
        print_error "❌ HACS E2E Test FAILED!"
        return 1
    fi
}

# Show test results
show_results() {
    local exit_code=$1
    
    print_header "Test Results Summary"
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
        echo -e "${GREEN}✅ Integration successfully installed via HACS simulation${NC}"
        echo -e "${GREEN}✅ All expected entities created and functional${NC}"
        echo -e "${GREEN}✅ Entity data validation completed${NC}"
        echo -e "${GREEN}✅ Decimal precision verification passed${NC}"
    else
        echo -e "${RED}❌ SOME TESTS FAILED!${NC}"
        echo -e "${RED}Please check the detailed output above for specific failures${NC}"
        echo -e "${YELLOW}Common issues:${NC}"
        echo -e "  • Docker permissions (try: sudo usermod -aG docker \$USER)"
        echo -e "  • Port 8123 already in use"
        echo -e "  • Network connectivity issues"
        echo -e "  • Insufficient system resources"
    fi
    
    echo -e "\n${BLUE}📋 Test Coverage:${NC}"
    echo -e "  • HACS installation simulation"
    echo -e "  • Integration configuration flow"
    echo -e "  • Entity creation verification"
    echo -e "  • Sensor data validation"
    echo -e "  • Attribute completeness check"
    echo -e "  • Decimal precision validation"
}

# Main execution
main() {
    print_header "Real Electricity Price - HACS E2E Test"
    
    check_dependencies
    install_dependencies
    cleanup_existing
    
    if run_test; then
        show_results 0
        exit 0
    else
        show_results 1
        exit 1
    fi
}

# Handle interruption
trap 'echo -e "\n${YELLOW}Test interrupted by user${NC}"; cleanup_existing; exit 130' INT

# Run the script
main "$@"
