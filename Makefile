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

dev: ## Start complete development environment with Docker
	@echo "🚀 Starting development environment..."
	@./scripts/dev-setup.sh

develop: ## Start local Home Assistant Core development
	@echo "🏠 Starting local Home Assistant development..."
	@./scripts/develop.sh

# File Management
sync: ## Sync integration files to Docker container
	@echo "🔄 Syncing integration files..."
	@./scripts/sync-integration.sh

# Testing and Quality
test: ## Run comprehensive integration tests
	@echo "🧪 Running tests..."
	@./scripts/test.sh

test-syntax: ## Run syntax check only
	@./scripts/test.sh syntax

test-import: ## Run import test only
	@./scripts/test.sh import

test-config: ## Run configuration validation only
	@./scripts/test.sh config

test-docker: ## Run Docker integration test only
	@./scripts/test.sh docker

test-quality: ## Run code quality check only
	@./scripts/test.sh quality

lint: ## Format and lint code
	@echo "🔍 Running code quality checks..."
	@./scripts/lint.sh

# Docker Management
docker-logs: ## View Docker container logs
	@echo "📋 Viewing container logs..."
	@docker logs hass-real-electricity-price-test --tail 50 -f

docker-restart: ## Restart Home Assistant container
	@echo "🔄 Restarting Home Assistant container..."
	@docker restart hass-real-electricity-price-test

docker-stop: ## Stop development environment
	@echo "🛑 Stopping development environment..."
	@docker compose down

docker-shell: ## Access container shell
	@echo "🐚 Accessing container shell..."
	@docker exec -it hass-real-electricity-price-test bash

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
	@echo "🐳 Docker Status:"
	@if docker ps -q -f name=hass-real-electricity-price-test | grep -q .; then \
		echo "  ✅ Container is running"; \
		echo "  🌐 Home Assistant: http://localhost:8123"; \
	else \
		echo "  ❌ Container is not running"; \
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
logs: docker-logs ## Alias for 'docker-logs'
restart: docker-restart ## Alias for 'docker-restart'
stop: docker-stop ## Alias for 'docker-stop'
shell: docker-shell ## Alias for 'docker-shell'
