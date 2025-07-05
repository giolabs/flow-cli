# Makefile for Flow CLI

.PHONY: help install install-dev test test-cov lint format type-check clean build release docs

# Default target
help:
	@echo "Flow CLI Development Commands:"
	@echo ""
	@echo "  install       Install package in production mode"
	@echo "  install-dev   Install package in development mode with dev dependencies"
	@echo "  test          Run tests"
	@echo "  test-cov      Run tests with coverage report"
	@echo "  test-fast     Run tests in parallel"
	@echo "  lint          Run all linting tools"
	@echo "  format        Format code with black and isort"
	@echo "  type-check    Run mypy type checking"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build distribution packages"
	@echo "  release       Build and upload to PyPI"
	@echo "  docs          Generate documentation"
	@echo "  pre-commit    Install pre-commit hooks"
	@echo ""

# Installation targets
install:
	pip install .

install-dev:
	pip install -e ".[dev]"

# Testing targets
test:
	pytest

test-cov:
	pytest --cov=flow_cli --cov-report=html --cov-report=term-missing

test-fast:
	pytest -n auto

test-performance:
	pytest -m performance

# Code quality targets
lint: format type-check flake8

format:
	black flow_cli tests
	isort flow_cli tests

type-check:
	mypy flow_cli

flake8:
	flake8 flow_cli tests

# Build targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

release: build
	python -m twine upload dist/*

# Development setup
pre-commit:
	pre-commit install
	pre-commit install --hook-type commit-msg

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "Documentation will be generated in docs/ directory"

# CI/CD helpers
ci-install:
	pip install -e ".[dev]"
	pre-commit install

ci-test:
	pytest --cov=flow_cli --cov-report=xml --junitxml=pytest.xml

ci-lint:
	black --check flow_cli tests
	isort --check-only flow_cli tests
	flake8 flow_cli tests
	mypy flow_cli

# Version management
version-patch:
	@echo "Current version: $$(python -c 'import flow_cli; print(flow_cli.__version__)')"
	@echo "Use semantic versioning to update version in flow_cli/__init__.py"

version-minor:
	@echo "Current version: $$(python -c 'import flow_cli; print(flow_cli.__version__)')"
	@echo "Use semantic versioning to update version in flow_cli/__init__.py"

version-major:
	@echo "Current version: $$(python -c 'import flow_cli; print(flow_cli.__version__)')"
	@echo "Use semantic versioning to update version in flow_cli/__init__.py"

# Security checks
security:
	pip-audit
	bandit -r flow_cli/

# Performance profiling
profile:
	python -m cProfile -o profile.stats -m flow_cli.main --help
	python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Local development server (if applicable)
dev:
	@echo "Flow CLI is a command-line tool. Use 'flow' command after installation."
	@echo "For development, use: pip install -e ."