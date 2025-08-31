#!/bin/bash

# Dev Container setup script for Real Electricity Price integration

echo "🚀 Setting up Real Electricity Price development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install ruff black isort mypy
pip install homeassistant
pip install holidays>=0.21

# Create Home Assistant config directory structure
echo "📁 Creating Home Assistant configuration structure..."
mkdir -p /config/custom_components
mkdir -p /config/.storage
mkdir -p /config/logs

# Create symbolic link to the integration
echo "🔗 Creating symbolic link to integration..."
ln -sf /workspaces/real-electricity-price/custom_components/real_electricity_price /config/custom_components/real_electricity_price

# Create basic Home Assistant configuration
echo "⚙️ Creating basic Home Assistant configuration..."
cat > /config/configuration.yaml << EOF
# Loads default set of integrations. Do not remove.
default_config:

# Load frontend themes from the themes folder
frontend:
  themes: !include_dir_merge_named themes

# Example configuration.yaml entry
automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

# Enable debug logging for our integration
logger:
  default: info
  logs:
    custom_components.real_electricity_price: debug
    
# HTTP configuration for dev container
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.16.0.0/12
    - 192.168.0.0/16
    - 10.0.0.0/8
EOF

# Create empty files for Home Assistant
touch /config/automations.yaml
touch /config/scripts.yaml
touch /config/scenes.yaml

# Create themes directory
mkdir -p /config/themes

echo "✅ Development environment setup complete!"
echo "🏠 Home Assistant will start automatically"
echo "🌐 Access at: http://localhost:8123"
