#!/usr/bin/env bash
#
# Bump or set the integration version across the repo.
#
# Updates:
# - custom_components/<domain>/manifest.json (version)
# - CHANGELOG.md: inserts a new stub section if --changelog is provided
#
# Usage:
#   ./scripts/update-versions.sh --bump patch|minor|major [--changelog]
#   ./scripts/update-versions.sh --new 1.2.3 [--changelog]
#
# No commit is made. The script prints the files it modifies.

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERR]${NC}  $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

DOMAIN_DIR="$ROOT_DIR/custom_components"
if [[ ! -d "$DOMAIN_DIR" ]]; then
  error "custom_components directory not found at $DOMAIN_DIR"
  exit 1
fi

# Detect domain folder (first non-hidden dir)
DOMAIN_NAME=""
while IFS= read -r name; do
  DOMAIN_NAME="$name"
  break
done < <(ls -1 "$DOMAIN_DIR" | grep -v '^__' | head -n1)

if [[ -z "$DOMAIN_NAME" ]]; then
  error "Could not detect integration domain under custom_components/"
  exit 1
fi

MANIFEST="$DOMAIN_DIR/$DOMAIN_NAME/manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
  error "manifest.json not found: $MANIFEST"
  exit 1
fi

CHANGELOG="$ROOT_DIR/CHANGELOG.md"

NEW_VERSION=""
BUMP_KIND=""
DO_CHANGELOG=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --new)
      NEW_VERSION="${2:-}"
      shift 2;;
    --bump)
      BUMP_KIND="${2:-}"
      shift 2;;
    --changelog)
      DO_CHANGELOG=true
      shift;;
    -h|--help)
      sed -n '1,60p' "$0" | sed -n '1,40p'
      exit 0;;
    *)
      error "Unknown argument: $1"; exit 2;;
  esac
done

if [[ -z "$NEW_VERSION" && -z "$BUMP_KIND" ]]; then
  error "Provide --new X.Y.Z or --bump patch|minor|major"
  exit 2
fi

# Read current version from manifest.json via Python for safety
CURRENT_VERSION=$(MANIFEST="$MANIFEST" python3 - <<'PY'
import json,sys,os
path=os.environ['MANIFEST']
with open(path,'r',encoding='utf-8') as f:
    data=json.load(f)
print(data.get('version',''))
PY
)

if [[ -z "$CURRENT_VERSION" ]]; then
  error "Could not read current version from manifest.json"
  exit 1
fi

calc_next() {
  local ver="$1" kind="$2"
  IFS='.' read -r MA MI PA <<< "${ver//[^0-9.]/}"
  MA=${MA:-0}; MI=${MI:-0}; PA=${PA:-0}
  case "$kind" in
    patch) PA=$((PA+1));;
    minor) MI=$((MI+1)); PA=0;;
    major) MA=$((MA+1)); MI=0; PA=0;;
    *) error "Unknown bump kind: $kind"; return 1;;
  esac
  echo "$MA.$MI.$PA"
}

TARGET_VERSION="$NEW_VERSION"
if [[ -z "$TARGET_VERSION" ]]; then
  TARGET_VERSION=$(calc_next "$CURRENT_VERSION" "$BUMP_KIND")
fi

info "Domain: $DOMAIN_NAME"
info "Current version: $CURRENT_VERSION"
info "Target version:  $TARGET_VERSION"

# Update manifest.json with the new version
MANIFEST="$MANIFEST" TARGET_VERSION="$TARGET_VERSION" python3 - <<'PY'
import json,sys,os
path=os.environ['MANIFEST']
newv=os.environ['TARGET_VERSION']
with open(path,'r',encoding='utf-8') as f:
    data=json.load(f)
data['version']=newv
with open(path,'w',encoding='utf-8') as f:
    json.dump(data,f,ensure_ascii=False,indent=2)
    f.write('\n')
print(f"Updated {path} -> version={newv}")
PY

ok "manifest.json updated"

# Optionally insert a CHANGELOG stub
if $DO_CHANGELOG; then
  if [[ -f "$CHANGELOG" ]]; then
    ts=$(date +%Y-%m-%d)
    # Insert at top after first line if it starts with '#'
    awk -v ver="$TARGET_VERSION" -v ts="$ts" '
      NR==1 && $0 ~ /^#/ { print; print "\n## v" ver " - " ts "\n- Describe changes here"; next }1
    ' "$CHANGELOG" > "$CHANGELOG.tmp" && mv "$CHANGELOG.tmp" "$CHANGELOG"
    ok "CHANGELOG stub inserted for v$TARGET_VERSION"
  else
    warn "CHANGELOG.md not found; skipping"
  fi
fi

echo ""
ok "Done. Files updated:"
echo " - $MANIFEST"
[[ -f "$CHANGELOG" ]] && $DO_CHANGELOG && echo " - $CHANGELOG (stub inserted)"
