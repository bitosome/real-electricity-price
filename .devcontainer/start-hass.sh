#!/bin/bash

# Start Home Assistant in the dev container

echo "🏠 Starting Home Assistant..."

# Wait a moment for the container to be fully ready
sleep 2

# Start Home Assistant in the background
nohup python -m homeassistant --config /config > /config/logs/homeassistant.log 2>&1 &

# Wait for Home Assistant to start
echo "⏳ Waiting for Home Assistant to start..."
sleep 10

# Check if Home Assistant is running
if pgrep -f "python -m homeassistant" > /dev/null; then
    echo "✅ Home Assistant started successfully!"
    echo "🌐 Access at: http://localhost:8123"
    echo "📋 Logs: tail -f /config/logs/homeassistant.log"
else
    echo "❌ Failed to start Home Assistant"
    echo "📋 Check logs: cat /config/logs/homeassistant.log"
fi
