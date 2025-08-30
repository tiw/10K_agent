# Makefile for XBRL Financial Service

.PHONY: help install install-dev test lint format clean demo serve docs

# Default target
help:
	@echo "XBRL Financial Service - Available Commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test         Run tests"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean up temporary files"
	@echo ""
	@echo "Usage:"
	@echo "  demo         Run the demo script"
	@echo "  serve        Start MCP server"
	@echo "  docs         Generate documentation"

# Installation targets
install:
	@echo "📦 Installing production dependencies..."
	pip install --upgrade pip
	pip install -r requirements-prod.txt
	pip install -e .
	@echo "✅ Production installation complete!"

install-dev:
	@echo "🔧 Installing development dependencies..."
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	pip install -e .
	@echo "✅ Development installation complete!"

# Development targets
test:
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v --cov=xbrl_financial_service --cov-report=html --cov-report=term-missing

lint:
	@echo "🔍 Running linting checks..."
	flake8 xbrl_financial_service/ tests/
	mypy xbrl_financial_service/
	@echo "✅ Linting complete!"

format:
	@echo "🎨 Formatting code..."
	black xbrl_financial_service/ tests/ *.py
	isort xbrl_financial_service/ tests/ *.py
	@echo "✅ Code formatting complete!"

clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	@echo "✅ Cleanup complete!"

# Usage targets
demo:
	@echo "🎯 Running demo..."
	python demo.py

serve:
	@echo "🌐 Starting MCP server..."
	python -m xbrl_financial_service.mcp_server

docs:
	@echo "📚 Generating documentation..."
	@echo "Documentation generation not implemented yet"

# Quick setup for new developers
setup: install-dev
	@echo "🚀 Setting up development environment..."
	mkdir -p data cache logs
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Download Apple's XBRL files"
	@echo "2. Run: make demo"
	@echo "3. Run: make test"

# CI/CD targets
ci-test: install-dev test lint
	@echo "✅ CI tests complete!"

# Parse Apple files (assuming they're in current directory)
parse-apple:
	@echo "📊 Parsing Apple XBRL files..."
	xbrl-service parse-xbrl --directory . --ratios --verbose