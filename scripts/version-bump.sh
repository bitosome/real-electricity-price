#!/bin/bash

# Real Electricity Price - Version Bump Script
# This script handles version bumping, changelog generation, and release automation

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Script directory and project root
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# File paths that need version updates
readonly MANIFEST_PATH="${PROJECT_ROOT}/custom_components/real_electricity_price/manifest.json"
readonly README_PATH="${PROJECT_ROOT}/README.md"
readonly CHANGELOG_PATH="${PROJECT_ROOT}/CHANGELOG.md"
readonly DEV_GUIDE_PATH="${PROJECT_ROOT}/DEV_ENVIRONMENT_GUIDE.md"
readonly WORKSPACE_PATH="${PROJECT_ROOT}/real-electricity-price.code-workspace"

# Utility functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_status() {
    echo -e "${YELLOW}➜${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Real Electricity Price Version Bump Script

This script will:
  1. Prompt for new version number
  2. Update all version references in project files
  3. Generate changelog entry
  4. Commit changes and create git tag
  5. Push to remote repository

OPTIONS:
  -h, --help          Show this help message
  -v, --version VER   Set version number (skips prompt)
  -n, --dry-run       Show what would be done without making changes
  -y, --yes           Auto-confirm all prompts
  --no-push           Skip pushing to remote repository

EXAMPLES:
  $0                  Interactive mode with prompts
  $0 -v 1.2.0         Set version to 1.2.0
  $0 -v 1.2.0 -y      Set version to 1.2.0 without prompts
  $0 --dry-run        Show changes without applying them

EOF
}

# Validate version format (semantic versioning)
validate_version() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format. Use semantic versioning (e.g., 1.2.0)"
    fi
}

# Get current version from manifest.json
get_current_version() {
    if [[ ! -f "$MANIFEST_PATH" ]]; then
        print_error "manifest.json not found at $MANIFEST_PATH"
    fi
    
    grep '"version"' "$MANIFEST_PATH" | sed -E 's/.*"version": "([^"]+)".*/\1/' || {
        print_error "Could not extract version from manifest.json"
    }
}

# Compare versions (returns 0 if new > current, 1 otherwise)
version_greater() {
    local new_version=$1
    local current_version=$2
    
    # Split versions into arrays
    IFS='.' read -ra NEW_VER <<< "$new_version"
    IFS='.' read -ra CURR_VER <<< "$current_version"
    
    # Compare each part
    for i in {0..2}; do
        if [[ ${NEW_VER[i]} -gt ${CURR_VER[i]} ]]; then
            return 0
        elif [[ ${NEW_VER[i]} -lt ${CURR_VER[i]} ]]; then
            return 1
        fi
    done
    
    # Versions are equal
    return 1
}

# Update version in a file
update_file_version() {
    local file_path=$1
    local current_version=$2
    local new_version=$3
    local description=$4
    
    if [[ ! -f "$file_path" ]]; then
        print_info "Skipping $description - file not found: $file_path"
        return
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would update $description"
        return
    fi
    
    # Create backup
    cp "$file_path" "${file_path}.backup"
    
    # Update version references
    case "$file_path" in
        *manifest.json)
            sed -i.tmp "s/\"version\": \"$current_version\"/\"version\": \"$new_version\"/" "$file_path"
            ;;
        *README.md)
            sed -i.tmp "s/Current version: v$current_version/Current version: v$new_version/g" "$file_path"
            ;;
        *DEV_ENVIRONMENT_GUIDE.md)
            sed -i.tmp "s/Current version: $current_version/Current version: $new_version/g" "$file_path"
            ;;
        *real-electricity-price.code-workspace)
            sed -i.tmp "s/\"version\": \"$current_version\"/\"version\": \"$new_version\"/" "$file_path"
            ;;
    esac
    
    # Remove temporary file
    rm -f "${file_path}.tmp"
    
    print_success "Updated $description"
}

# Generate changelog entry
generate_changelog_entry() {
    local version=$1
    local current_date=$(date +"%Y-%m-%d")
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would generate changelog entry for v$version"
        return
    fi
    
    # Create temporary changelog content
    local temp_changelog=$(mktemp)
    
    cat << EOF > "$temp_changelog"
# Changelog

> **Note**: Starting with v1.2.0, changelogs are maintained in [GitHub Releases](../../releases).

All notable changes to this project will be documented in this file.

## v$version - $(date +"%Y-%m-%d")
- Version bump to v$version
- For detailed changes, see [GitHub Releases](../../releases/tag/v$version)

EOF
    
    # Append existing changelog content (skip the first few lines)
    if [[ -f "$CHANGELOG_PATH" ]]; then
        tail -n +8 "$CHANGELOG_PATH" >> "$temp_changelog"
    fi
    
    # Replace original changelog
    mv "$temp_changelog" "$CHANGELOG_PATH"
    
    print_success "Generated changelog entry for v$version"
}

# Check git status and ensure clean working directory
check_git_status() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
    fi
    
    # Check for unstaged changes (excluding our backup files)
    if git diff --quiet && git diff --cached --quiet; then
        return # Working directory is clean
    fi
    
    print_error "Working directory is not clean. Please commit or stash your changes first."
}

# Commit changes and create tag
commit_and_tag() {
    local version=$1
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would commit changes and create tag v$version"
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    # Add files that were modified
    git add "$MANIFEST_PATH" "$README_PATH" "$CHANGELOG_PATH" "$DEV_GUIDE_PATH" "$WORKSPACE_PATH" 2>/dev/null || true
    
    # Create commit
    print_status "Creating commit for version v$version"
    git commit -m "Bump version to v$version

🚀 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>" || {
        print_error "Failed to create commit"
    }
    
    # Create annotated tag
    print_status "Creating git tag v$version"
    git tag -a "v$version" -m "Release v$version

Real Electricity Price Integration v$version

🚀 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>" || {
        print_error "Failed to create git tag"
    }
    
    print_success "Created commit and tag for v$version"
}

# Push to remote repository
push_to_remote() {
    local version=$1
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would push changes and tag to remote repository"
        return
    fi
    
    if [[ "$NO_PUSH" == "true" ]]; then
        print_info "Skipping push to remote (--no-push specified)"
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    print_status "Pushing changes to remote repository"
    git push origin main || {
        print_error "Failed to push changes to remote"
    }
    
    print_status "Pushing tag v$version to remote repository"
    git push origin "v$version" || {
        print_error "Failed to push tag to remote"
    }
    
    print_success "Pushed changes and tag to remote repository"
}

# Cleanup backup files
cleanup_backups() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return
    fi
    
    find "$PROJECT_ROOT" -name "*.backup" -delete 2>/dev/null || true
    print_success "Cleaned up backup files"
}

# Main version bump process
perform_version_bump() {
    local new_version=$1
    local current_version
    
    print_header "Real Electricity Price Version Bump v$new_version"
    
    # Get current version
    current_version=$(get_current_version)
    print_info "Current version: $current_version"
    print_info "New version: $new_version"
    
    # Validate that new version is greater than current
    if ! version_greater "$new_version" "$current_version"; then
        print_error "New version ($new_version) must be greater than current version ($current_version)"
    fi
    
    # Check git status
    print_status "Checking git repository status"
    check_git_status
    
    # Confirm changes unless auto-confirm is enabled
    if [[ "$AUTO_CONFIRM" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
        echo
        print_info "The following changes will be made:"
        echo "  1. Update version in manifest.json"
        echo "  2. Update version in README.md"
        echo "  3. Update version in DEV_ENVIRONMENT_GUIDE.md"
        echo "  4. Update version in workspace file"
        echo "  5. Generate changelog entry"
        echo "  6. Commit changes and create git tag"
        if [[ "$NO_PUSH" != "true" ]]; then
            echo "  7. Push to remote repository"
        fi
        echo
        
        read -p "Continue with version bump to v$new_version? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Version bump cancelled"
            exit 0
        fi
    fi
    
    echo
    print_header "Updating Version References"
    
    # Update all version references
    update_file_version "$MANIFEST_PATH" "$current_version" "$new_version" "manifest.json"
    update_file_version "$README_PATH" "$current_version" "$new_version" "README.md"
    update_file_version "$DEV_GUIDE_PATH" "$current_version" "$new_version" "DEV_ENVIRONMENT_GUIDE.md"
    update_file_version "$WORKSPACE_PATH" "$current_version" "$new_version" "workspace file"
    
    # Generate changelog entry
    print_header "Generating Changelog"
    generate_changelog_entry "$new_version"
    
    # Git operations
    if [[ "$DRY_RUN" != "true" ]]; then
        print_header "Git Operations"
        commit_and_tag "$new_version"
        push_to_remote "$new_version"
        cleanup_backups
        
        print_header "Release Complete!"
        print_success "Version v$new_version released successfully!"
        echo
        print_info "Next steps:"
        echo "   • Create GitHub release: https://github.com/bitosome/real-electricity-price/releases/new?tag=v$new_version"
        echo "   • Update HACS if needed"
        echo "   • Announce the release"
    else
        print_header "Dry Run Complete!"
        print_info "No changes were made. Remove --dry-run to apply changes."
    fi
}

# Parse command line arguments
NEW_VERSION=""
DRY_RUN="false"
AUTO_CONFIRM="false"
NO_PUSH="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--version)
            NEW_VERSION="$2"
            shift 2
            ;;
        -n|--dry-run)
            DRY_RUN="true"
            shift
            ;;
        -y|--yes)
            AUTO_CONFIRM="true"
            shift
            ;;
        --no-push)
            NO_PUSH="true"
            shift
            ;;
        *)
            print_error "Unknown option: $1\nUse --help for usage information."
            ;;
    esac
done

# Change to project root directory
cd "$PROJECT_ROOT"

# Prompt for version if not provided
if [[ -z "$NEW_VERSION" ]]; then
    current_version=$(get_current_version)
    echo
    print_header "Real Electricity Price Version Bump"
    print_info "Current version: $current_version"
    echo
    
    read -p "Enter new version (e.g., 1.2.0): " NEW_VERSION
    
    if [[ -z "$NEW_VERSION" ]]; then
        print_error "Version number is required"
    fi
fi

# Validate version format
validate_version "$NEW_VERSION"

# Perform the version bump
perform_version_bump "$NEW_VERSION"