# Real Electricity Price Integration - Development Makefile
#
# This Makefile provides convenient shortcuts for common development tasks.
#

.PHONY: help setup dev sync test lint clean docker-logs docker-restart docker-stop brand-assets install-deps

# Default target
help: ## Show this help message
	@echo "Real Electricity Price Integration - Development Commands"
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup    # Install dependencies"
	@echo "  make dev      # Start development environment"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Environment
setup: ## Install development dependencies
	@echo "🔧 Setting up development environment..."
	@./scripts/setup.sh

dev: ## Start complete development environment with Podman
	@echo "🚀 Starting development environment..."
	@./scripts/dev-setup.sh

develop: ## Start local Home Assistant Core development
	@echo "🏠 Starting local Home Assistant development..."
	@./scripts/develop.sh

restart-ha: ## Restart Home Assistant with automatic proxy fix
	@echo "🔄 Restarting Home Assistant..."
	@./scripts/restart-ha.sh

# File Management
sync: ## Sync integration files to Podman container
	@echo "🔄 Syncing integration files..."
	@./scripts/sync-integration.sh

# Testing and Quality
test: ## Run comprehensive integration tests
	@echo "🧪 Running tests..."
	@./tests/test.sh

test-syntax: ## Run syntax check only
	@./tests/test.sh syntax

test-import: ## Run import test only
	@./tests/test.sh import

test-config: ## Run configuration validation only
	@./tests/test.sh config

test-docker: ## Run Podman integration test only
	@./tests/test.sh docker

test-quality: ## Run code quality check only
	@./tests/test.sh quality

lint: ## Format and lint code
	@echo "🔍 Running code quality checks..."
	@./scripts/lint.sh

# Podman Management
podman-logs: ## View Podman container logs
	@echo "📋 Viewing container logs..."
	@podman logs dc --tail 50 -f

podman-logs-proxy: ## View Nginx proxy logs
	@echo "📋 Viewing proxy logs..."
	@podman logs web --tail 50 -f

podman-restart: ## Restart Home Assistant container
	@echo "🔄 Restarting Home Assistant container..."
	@podman restart dc

podman-restart-proxy: ## Restart Nginx proxy container
	@echo "🔄 Restarting proxy container..."
	@podman restart web

podman-restart-all: ## Restart both Home Assistant and proxy containers
	@echo "🔄 Restarting Home Assistant container..."
	@podman restart dc
	@echo "⏳ Waiting for Home Assistant to start..."
	@sleep 3
	@echo "🔄 Restarting proxy container..."
	@podman restart web
	@echo "✅ Both containers restarted"

podman-stop: ## Stop development environment
	@echo "🛑 Stopping development environment..."
	@podman-compose down

podman-shell: ## Access container shell
	@echo "🐚 Accessing container shell..."
	@podman exec -it dc bash

podman-shell-proxy: ## Access proxy container shell
	@echo "🐚 Accessing proxy container shell..."
	@podman exec -it web sh

# Utilities
brand-assets: ## Generate brand assets for Home Assistant brands repository
	@echo "🎨 Generating brand assets..."
	@./scripts/prepare_brand_assets.sh

clean: ## Clean up temporary files and caches
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"

install-deps: ## Install Python requirements only
	@echo "📦 Installing Python requirements..."
	@pip install -r requirements.txt

# Git helpers
commit-check: ## Run checks before committing
	@echo "✅ Running pre-commit checks..."
	@make lint
	@make test
	@echo "🎉 Ready to commit!"

# Status checks
status: ## Show development environment status
	@echo "📊 Development Environment Status"
	@echo "=================================="
	@echo ""
	@echo "🐳 Podman Status:"
	@if podman ps -q -f name=dc | grep -q .; then \
		echo "  ✅ Home Assistant container (dc) is running"; \
	else \
		echo "  ❌ Home Assistant container (dc) is not running"; \
	fi
	@if podman ps -q -f name=web | grep -q .; then \
		echo "  ✅ Proxy container (web) is running"; \
		echo "  🌐 Home Assistant: http://localhost:8080 (via proxy)"; \
	else \
		echo "  ❌ Proxy container (web) is not running"; \
		echo "  💡 Run 'make dev' to start"; \
	fi
	@echo ""
	@echo "📁 Integration Files:"
	@if [ -d "custom_components/real_electricity_price" ]; then \
		echo "  ✅ Integration directory exists"; \
		echo "  📄 Files: $$(ls custom_components/real_electricity_price/*.py | wc -l | tr -d ' ') Python files"; \
	else \
		echo "  ❌ Integration directory missing"; \
	fi
	@echo ""
	@echo "🔧 Available Scripts:"
	@ls scripts/*.sh | sed 's|scripts/||' | sed 's|^|  📜 |'

# Quick development cycle
quick: sync test ## Quick development cycle: sync + test
	@echo "⚡ Quick development cycle completed!"

# Full development cycle
full: lint test sync ## Full development cycle: lint + test + sync
	@echo "🎯 Full development cycle completed!"

# Aliases for convenience
start: dev ## Alias for 'dev'
logs: podman-logs ## Alias for 'podman-logs'
logs-proxy: podman-logs-proxy ## Alias for 'podman-logs-proxy'
restart: restart-ha ## Alias for 'restart-ha' (restarts both containers with connectivity fix)
restart-basic: podman-restart-all ## Basic restart of both containers without health checks
restart-proxy: podman-restart-proxy ## Alias for 'podman-restart-proxy'
stop: podman-stop ## Alias for 'podman-stop'
shell: podman-shell ## Alias for 'podman-shell'
shell-proxy: podman-shell-proxy ## Alias for 'podman-shell-proxy'
