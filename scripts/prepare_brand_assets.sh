#!/usr/bin/env bash
#
# Brand Assets Preparation Script
#
# This script generates properly sized brand assets for Home Assistant brands repository.
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

# Usage: scripts/prepare_brand_assets.sh [path/to/source_image.png] [output_dir]
# Requires: ImageMagick `convert`

SRC=${1:-scripts/icon.png}
OUT=${2:-brands_payload}
DOMAIN=real_electricity_price

if [[ -z "${SRC}" || ! -f "${SRC}" ]]; then
  echo -e "${YELLOW}Usage:${NC} $0 [path/to/source_image.(png|jpg|webp|svg)] [output_dir]" >&2
  echo -e "${BLUE}Default source:${NC} scripts/icon.png"
  exit 1
fi

print_status "Preparing brand assets..."
print_status "Source: $SRC"
print_status "Output: $OUT"

mkdir -p "${OUT}/custom_integrations/${DOMAIN}"
DEST="${OUT}/custom_integrations/${DOMAIN}"

# Function to create square PNG with transparent padding, then resize
mk_png() {
  local size=$1
  local name=$2
  print_status "Creating ${name} (${size}x${size})..."
  magick "${SRC}" \
    -background none \
    -gravity center \
    -resize ${size}x${size} \
    "${DEST}/${name}"
}

# Check if ImageMagick is available
if ! command -v magick &> /dev/null; then
    print_warning "ImageMagick not found. Please install ImageMagick first."
    echo "macOS: brew install imagemagick"
    echo "Ubuntu: sudo apt install imagemagick"
    exit 1
fi

print_status "Generating brand assets in ${DEST}..."
mk_png 256 icon.png
mk_png 512 logo.png

print_success "Brand assets created successfully!"

echo -e "\n${BLUE}📁 Generated Files:${NC}"
echo -e "   • ${DEST}/icon.png (256x256)"
echo -e "   • ${DEST}/logo.png (512x512)"

echo -e "\n${BLUE}🚀 Next Steps:${NC}"
echo -e "   1. Review generated assets"
echo -e "   2. Commit ${OUT}/custom_integrations/${DOMAIN} to your fork of home-assistant/brands"
echo -e "   3. Open a PR in https://github.com/home-assistant/brands"
echo -e "   4. See BRAND_SUBMISSION.md for detailed instructions"

echo -e "\n${GREEN}✅ Ready for brand submission!${NC}\n"
