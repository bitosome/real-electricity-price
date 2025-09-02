#!/bin/bash
# Script to restart Home Assistant and fix nginx connectivity
# This script ensures nginx can connect to Home Assistant after IP changes

set -e

echo "🔄 Restarting Home Assistant with proxy fix..."

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "[INFO] Finding Home Assistant container..."
HA_CONTAINER=$(podman ps --filter "ancestor=ghcr.io/home-assistant/home-assistant:stable" --format "{{.ID}}" | head -1)

if [ -z "$HA_CONTAINER" ]; then
    echo "[ERROR] Home Assistant container not found"
    exit 1
fi

echo "[INFO] Found Home Assistant container: $HA_CONTAINER"

echo "[INFO] Restarting Home Assistant..."
podman restart "$HA_CONTAINER"

echo "[INFO] Waiting for Home Assistant to start..."
sleep 10

echo "[INFO] Checking Home Assistant health..."
for i in {1..12}; do
    if podman exec "$HA_CONTAINER" curl -f -s http://localhost:8123 > /dev/null 2>&1; then
        echo "[SUCCESS] Home Assistant is healthy"
        break
    fi
    if [ $i -eq 12 ]; then
        echo "[WARNING] Home Assistant may not be fully ready yet"
    fi
    echo "[INFO] Waiting for Home Assistant... ($i/12)"
    sleep 5
done

echo "[INFO] Finding nginx proxy container..."
NGINX_CONTAINER=$(podman ps --filter "ancestor=nginx:alpine" --format "{{.ID}}" | head -1)

if [ -z "$NGINX_CONTAINER" ]; then
    echo "[ERROR] Nginx container not found"
    exit 1
fi

echo "[INFO] Found nginx container: $NGINX_CONTAINER"

echo "[INFO] Restarting nginx proxy to refresh network connections..."
podman restart "$NGINX_CONTAINER"

echo "[INFO] Waiting for nginx to start..."
sleep 3

echo "[INFO] Testing connectivity..."
for i in {1..6}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200\|405"; then
        echo "[SUCCESS] ✅ Home Assistant is accessible at http://localhost:8080"
        break
    fi
    if [ $i -eq 6 ]; then
        echo "[WARNING] ⚠️  Home Assistant may still be starting up"
        echo "[INFO] Try accessing http://localhost:8080 in a few minutes"
    fi
    echo "[INFO] Testing connection... ($i/6)"
    sleep 5
done

echo ""
echo "🎉 Restart complete!"
echo "📱 Access Home Assistant: http://localhost:8080"
echo ""
