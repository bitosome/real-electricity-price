#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/prepare_brand_assets.sh path/to/source_image.png [output_dir]
# Requires: ImageMagick `convert`

SRC=${1:-}
OUT=${2:-brands_payload}
DOMAIN=real_electricity_price

if [[ -z "${SRC}" || ! -f "${SRC}" ]]; then
  echo "Usage: $0 path/to/source_image.(png|jpg|webp|svg) [output_dir]" >&2
  exit 1
fi

mkdir -p "${OUT}/custom_integrations/${DOMAIN}"
DEST="${OUT}/custom_integrations/${DOMAIN}"

# Function to create square PNG with transparent padding, then resize
mk_png() {
  local size=$1
  local name=$2
  magick "${SRC}" \
    -background none \
    -gravity center \
    -resize ${size}x${size} \
    "${DEST}/${name}"
}

echo "Generating brand assets in ${DEST}..."
mk_png 256 icon.png
mk_png 512 logo.png

echo "Done. Next steps:"
echo "1) Commit ${OUT}/custom_integrations/${DOMAIN} to your fork of home-assistant/brands"
echo "2) Open a PR in https://github.com/home-assistant/brands"
