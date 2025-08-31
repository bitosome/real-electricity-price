#!/usr/bin/env bash
#
# Code Quality and Linting Script
#
# This script runs all code quality checks and formatting tools.
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

# Check if tools are available
check_tools() {
    print_header "Checking Tools"
    
    if ! command -v ruff &> /dev/null; then
        print_warning "Ruff not found. Installing..."
        pip install ruff
    fi
    
    print_success "All tools available"
}

# Format code
format_code() {
    print_header "Formatting Code"
    
    print_status "Running Ruff formatter..."
    ruff format .
    
    print_success "Code formatting completed"
}

# Lint code
lint_code() {
    print_header "Linting Code"
    
    print_status "Running Ruff linter..."
    ruff check . --fix
    
    print_success "Code linting completed"
}

# Check specific integration files
check_integration() {
    print_header "Integration File Check"
    
    INTEGRATION_DIR="custom_components/real_electricity_price"
    
    if [ -d "$INTEGRATION_DIR" ]; then
        print_status "Checking integration syntax..."
        python -m py_compile "$INTEGRATION_DIR"/*.py
        print_success "Integration files syntax OK"
    else
        print_warning "Integration directory not found"
    fi
}

# Main execution
main() {
    echo -e "\n${GREEN}🔍 Running Code Quality Checks${NC}\n"
    
    check_tools
    format_code
    lint_code
    check_integration
    
    echo -e "\n${GREEN}✅ All checks completed!${NC}\n"
}

# Run main function
main "$@"
