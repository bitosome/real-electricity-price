#!/usr/bin/env bash
#
# Install HACS (Home Assistant Community Store)

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

# Install HACS
install_hacs() {
    print_header "Installing HACS"
    
    local HACS_DIR="$PROJECT_ROOT/container/config/custom_components/hacs"
    local TEMP_DIR="/tmp/hacs-install"
    
    # Clean up any existing installation
    if [ -d "$HACS_DIR" ]; then
        print_status "Removing existing HACS installation..."
        rm -rf "$HACS_DIR"
    fi
    
    # Create directories
    mkdir -p "$HACS_DIR"
    mkdir -p "$TEMP_DIR"
    
    print_status "Downloading latest HACS release..."
    
    # Get latest release URL
    local LATEST_URL=$(curl -s https://api.github.com/repos/hacs/integration/releases/latest | grep "zipball_url" | cut -d '"' -f 4)
    
    if [ -z "$LATEST_URL" ]; then
        print_error "Failed to get HACS download URL"
        exit 1
    fi
    
    # Download and extract
    cd "$TEMP_DIR"
    curl -L -o hacs.zip "$LATEST_URL"
    unzip -q hacs.zip
    
    # Find the extracted directory (GitHub creates a directory with commit hash)
    local EXTRACTED_DIR=$(find . -name "hacs-integration-*" -type d | head -1)
    
    if [ -z "$EXTRACTED_DIR" ]; then
        print_error "Failed to find extracted HACS directory"
        exit 1
    fi
    
    # Copy HACS files
    print_status "Installing HACS files..."
    cp -r "$EXTRACTED_DIR/custom_components/hacs/"* "$HACS_DIR/"
    
    # Cleanup
    cd "$PROJECT_ROOT"
    rm -rf "$TEMP_DIR"
    
    print_success "HACS installed successfully"
    
    # Verify installation
    if [ -f "$HACS_DIR/manifest.json" ]; then
        local VERSION=$(grep '"version"' "$HACS_DIR/manifest.json" | cut -d '"' -f 4)
        print_success "HACS version $VERSION ready for use"
    else
        print_warning "HACS installation may be incomplete"
    fi
}

# Configure HACS in Home Assistant configuration
configure_hacs() {
    print_header "Configuring HACS"
    
    local CONFIG_FILE="$PROJECT_ROOT/container/config/configuration.yaml"
    
    # Check if HACS is already configured
    if grep -q "^hacs:" "$CONFIG_FILE" 2>/dev/null; then
        print_status "HACS already configured in configuration.yaml"
        return
    fi
    
    print_status "Adding HACS configuration to configuration.yaml..."
    
    # Add HACS configuration if not present
    cat >> "$CONFIG_FILE" << 'EOF'

# Enable HACS (Home Assistant Community Store)
hacs:
  token: !env_var GITHUB_TOKEN ""
  experimental: true
EOF
    
    print_success "HACS configuration added"
    print_warning "Note: Set GITHUB_TOKEN environment variable for full functionality"
}

# Show setup instructions
show_instructions() {
    print_header "Setup Instructions"
    
    echo -e "${GREEN}🎉 HACS installation completed!${NC}\n"
    
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo -e "   1. Access Home Assistant"
    echo -e "   4. Go to Settings → Devices & Services"
    echo -e "   5. Configure HACS integration"
    
    echo -e "\n${BLUE}🔧 Optional GitHub Token Setup:${NC}"
    echo -e "   • Create GitHub Personal Access Token"
    echo -e "   • Set environment variable: ${YELLOW}export GITHUB_TOKEN=your_token${NC}"
    echo -e "   • This increases API rate limits and enables private repos"
    
    echo -e "\n${BLUE}📁 Installation Location:${NC}"
    echo -e "   • HACS files: ${YELLOW}container/config/custom_components/hacs/${NC}"
    
    echo -e "\n${GREEN}Ready for development! 🚀${NC}\n"
}

# Main execution
main() {
    echo -e "\n${GREEN}🏪 Installing HACS (Home Assistant Community Store)${NC}\n"
    
    # Check if curl and unzip are available
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v unzip &> /dev/null; then
        print_error "unzip is required but not installed"
        exit 1
    fi
    
    install_hacs
    configure_hacs
    show_instructions
}

# Run main function
main "$@"
