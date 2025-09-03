#!/usr/bin/env bash
#
# Sync Integration Files to Podman Container
#
# This script syncs the integration files from the development directory
# to the Podman container's custom_components directory.
#

set -e

# Colors for output
GREEN='\033[0;32m'
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

# Sync integration files
sync_files() {
    SOURCE_DIR="$PROJECT_ROOT/custom_components/real_electricity_price"
    TARGET_DIR="$PROJECT_ROOT/container/config/custom_components/real_electricity_price"
    
    print_status "Syncing integration files..."
    print_status "From: $SOURCE_DIR"
    print_status "To: $TARGET_DIR"
    
    # Create target directory if it doesn't exist
    mkdir -p "$TARGET_DIR"
    
    # Copy all files
    cp -r "$SOURCE_DIR/"* "$TARGET_DIR/"
    
    print_success "Integration files synced successfully"
    
    # Restart Home Assistant if container is running
    if podman ps -q -f name=dc | grep -q .; then
        print_status "Restarting Home Assistant container..."
        podman restart dc > /dev/null
        print_success "Home Assistant restarted"
        print_status "Wait 10-15 seconds for Home Assistant to reload"
    else
        print_status "Home Assistant container not running"
    fi
}

# Main execution
main() {
    echo -e "\n${GREEN}🔄 Syncing Integration Files${NC}\n"
    sync_files
    echo -e "\n${GREEN}✅ Sync completed!${NC}\n"
}

# Run main function
main "$@"
