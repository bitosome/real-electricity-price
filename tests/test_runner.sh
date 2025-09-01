#!/usr/bin/env bash
#
# Test Runner for Real Electricity Price Integration
#
# Runs various test suites to validate the integration
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

# Show usage
show_usage() {
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Available test types:"
    echo "  basic       - Run basic integration tests (syntax, imports)"
    echo "  config      - Test configuration flow"
    echo "  docker      - Test Docker environment setup"
    echo "  hacs-simple - Run simplified HACS installation test"
    echo "  hacs-full   - Run full HACS E2E test (requires Docker)"
    echo "  all         - Run all tests (default)"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 basic           # Run only basic tests"
    echo "  $0 hacs-simple     # Test HACS installation simulation"
    echo "  $0                 # Run all tests"
}

# Basic tests (syntax, imports, etc.)
run_basic_tests() {
    print_header "Running Basic Tests"
    
    print_status "Testing Python syntax..."
    python3 -m py_compile custom_components/real_electricity_price/*.py
    print_success "✅ Python syntax valid"
    
    print_status "Testing imports..."
    python3 -c "
import sys
import os

# Add the custom_components directory to Python path
sys.path.insert(0, os.path.join(os.getcwd(), 'custom_components'))

try:
    # Import using absolute imports
    import real_electricity_price.const as const
    print(f'✅ Constants imported: PRICE_DECIMAL_PRECISION = {const.PRICE_DECIMAL_PRECISION}')
    
    # Test that we can import the main components
    import real_electricity_price.api
    print('✅ API module imported')
    
    import real_electricity_price.coordinator  
    print('✅ Coordinator module imported')
    
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    print_success "✅ Import tests passed"
}

# Configuration tests
run_config_tests() {
    print_header "Running Configuration Tests"
    
    print_status "Testing configuration flow..."
    python3 test_integration.py
    print_success "✅ Configuration tests passed"
}

# Docker tests
run_docker_tests() {
    print_header "Running Docker Tests"
    
    print_status "Testing Docker environment..."
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            print_success "✅ Docker is available and running"
        else
            print_error "❌ Docker daemon not running"
            return 1
        fi
    else
        print_error "❌ Docker not installed"
        return 1
    fi
}

# Simplified HACS test
run_hacs_simple_test() {
    print_header "Running Simplified HACS Test"
    
    print_status "Installing test dependencies..."
    pip3 install -q docker PyYAML
    
    print_status "Running HACS simulation test..."
    python3 test_hacs_simple.py
    print_success "✅ HACS simple test completed"
}

# Full HACS E2E test
run_hacs_full_test() {
    print_header "Running Full HACS E2E Test"
    
    print_status "Running comprehensive HACS test..."
    ./scripts/test-hacs-e2e.sh
    print_success "✅ HACS E2E test completed"
}

# Decimal precision specific test
run_precision_tests() {
    print_header "Running Decimal Precision Tests"
    
    print_status "Testing decimal precision implementation..."
    python3 -c "
import sys
import os

# Add the custom_components directory to Python path
sys.path.insert(0, os.path.join(os.getcwd(), 'custom_components'))

import real_electricity_price.const as const

# Test precision constant
assert const.PRICE_DECIMAL_PRECISION == 6, f'Expected 6, got {const.PRICE_DECIMAL_PRECISION}'
print(f'✅ Precision constant: {const.PRICE_DECIMAL_PRECISION}')

# Test rounding
test_price = 0.123456789
rounded = round(test_price, const.PRICE_DECIMAL_PRECISION)
expected = 0.123457
assert rounded == expected, f'Expected {expected}, got {rounded}'
print(f'✅ Rounding works: {test_price} → {rounded}')

print('✅ All precision tests passed')
"
    print_success "✅ Decimal precision tests passed"
}

# Run all tests
run_all_tests() {
    local failed_tests=0
    
    print_header "Running All Tests"
    
    # Basic tests
    if ! run_basic_tests; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Precision tests
    if ! run_precision_tests; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Configuration tests
    if ! run_config_tests; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Docker tests (optional)
    if run_docker_tests; then
        # Only run HACS tests if Docker is available
        if ! run_hacs_simple_test; then
            failed_tests=$((failed_tests + 1))
        fi
    else
        print_warning "⚠️ Skipping HACS tests (Docker not available)"
    fi
    
    # Summary
    print_header "Test Summary"
    if [ $failed_tests -eq 0 ]; then
        print_success "🎉 ALL TESTS PASSED!"
        return 0
    else
        print_error "❌ $failed_tests test suite(s) failed"
        return 1
    fi
}

# Main execution
main() {
    local test_type=${1:-all}
    
    case $test_type in
        basic)
            run_basic_tests
            ;;
        config)
            run_config_tests
            ;;
        docker)
            run_docker_tests
            ;;
        precision)
            run_precision_tests
            ;;
        hacs-simple)
            run_hacs_simple_test
            ;;
        hacs-full)
            run_hacs_full_test
            ;;
        all)
            run_all_tests
            ;;
        help|--help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown test type: $test_type"
            show_usage
            exit 1
            ;;
    esac
}

# Run the script
main "$@"
