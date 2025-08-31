#!/usr/bin/env bash
#
# Development Environment Setup
#
# This script installs all required dependencies for development.
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd "$(dirname "$0")/.."

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Install Python dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    print_status "Installing Python requirements..."
    python3 -m pip install --requirement requirements.txt
    
    print_status "Installing development tools..."
    python3 -m pip install ruff black mypy pre-commit
    
    print_success "Dependencies installed"
}

# Setup pre-commit hooks
setup_precommit() {
    print_header "Setting up Pre-commit Hooks"
    
    if [ -f ".pre-commit-config.yaml" ]; then
        print_status "Installing pre-commit hooks..."
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_status "No pre-commit config found, skipping"
    fi
}

# Main execution
main() {
    echo -e "\n${GREEN}🔧 Setting up Development Environment${NC}\n"
    
    install_dependencies
    setup_precommit
    
    echo -e "\n${GREEN}✅ Setup completed!${NC}\n"
    echo -e "Run ${BLUE}./scripts/dev-setup.sh${NC} to start the development environment"
}

# Run main function
main "$@"
