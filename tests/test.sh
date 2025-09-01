#!/usr/bin/env bash
#
# Integration Testing Script
#
# This script runs comprehensive tests for the integration.
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Syntax check
syntax_check() {
    print_header "Syntax Check"
    
    local failed=0
    
    for file in "$PROJECT_ROOT/custom_components/real_electricity_price"/*.py; do
        if [ -f "$file" ]; then
            print_status "Checking $(basename "$file")..."
            if ! python -m py_compile "$file"; then
                print_error "Syntax error in $(basename "$file")"
                failed=1
            fi
        fi
    done
    
    if [ $failed -eq 0 ]; then
        print_success "All files passed syntax check"
    else
        print_error "Syntax check failed"
        exit 1
    fi
}

# Import test
import_test() {
    print_header "Import Test"
    
    cd "$PROJECT_ROOT"
    
    # Test if we can import the main module
    print_status "Testing integration imports..."
    
    export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}/custom_components"
    
    if python -c "import real_electricity_price; print('✅ Integration imports successfully')"; then
        print_success "Import test passed"
    else
        print_error "Import test failed"
        exit 1
    fi
}

# Configuration validation
config_validation() {
    print_header "Configuration Validation"
    
    local manifest_file="$PROJECT_ROOT/custom_components/real_electricity_price/manifest.json"
    
    if [ -f "$manifest_file" ]; then
        print_status "Validating manifest.json..."
        if python -c "import json; json.load(open('$manifest_file'))"; then
            print_success "manifest.json is valid"
        else
            print_error "manifest.json is invalid"
            exit 1
        fi
    else
        print_error "manifest.json not found"
        exit 1
    fi
}

# Docker integration test
docker_test() {
    print_header "Docker Integration Test"
    
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not available, skipping Docker tests"
        return
    fi
    
    if ! docker info &> /dev/null; then
        print_warning "Docker not running, skipping Docker tests"
        return
    fi
    
    print_status "Testing Docker setup..."
    
    # Sync files
    "$PROJECT_ROOT/scripts/sync-integration.sh" > /dev/null
    
    # Check if container is running
    if docker ps -q -f name=hass-real-electricity-price-test | grep -q .; then
        print_status "Container is running, checking logs..."
        
        # Check for integration in logs
        if docker logs hass-real-electricity-price-test 2>&1 | grep -q "real_electricity_price"; then
            print_success "Integration appears in Docker logs"
        else
            print_warning "Integration not found in Docker logs"
        fi
    else
        print_warning "Docker container not running"
    fi
}

# Code quality check
quality_check() {
    print_header "Code Quality Check"
    
    if command -v ruff &> /dev/null; then
        print_status "Running Ruff checks..."
        if ruff check "$PROJECT_ROOT/custom_components/real_electricity_price" --quiet; then
            print_success "Ruff checks passed"
        else
            print_warning "Ruff found issues (non-blocking)"
        fi
    else
        print_warning "Ruff not available, skipping code quality check"
    fi
}

# Run all tests
run_tests() {
    syntax_check
    import_test
    config_validation
    quality_check
    docker_test
}

# Main execution
main() {
    echo -e "\n${GREEN}🧪 Running Integration Tests${NC}\n"
    
    run_tests
    
    echo -e "\n${GREEN}✅ All tests completed!${NC}\n"
}

# Handle command line arguments
case "${1:-}" in
    syntax)
        syntax_check
        ;;
    import)
        import_test
        ;;
    config)
        config_validation
        ;;
    docker)
        docker_test
        ;;
    quality)
        quality_check
        ;;
    *)
        main
        ;;
esac
