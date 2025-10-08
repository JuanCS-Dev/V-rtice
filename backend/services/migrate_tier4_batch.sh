#!/bin/bash
# Batch Migration Script - TIER 4 Experimental Services
# Usage: ./migrate_tier4_batch.sh

set -e

SERVICES=(
    "maximus_predict"
    "maximus_integration_service"
    "maximus_oraculo"
    "atlas_service"
    "cloud_coordinator_service"
    "cyber_service"
    "domain_service"
    "network_monitor_service"
    "nmap_service"
)

PYPROJECT_TEMPLATE='[project]
name = "SERVICE_NAME"
version = "1.0.0"
description = "SERVICE_DESC"
requires-python = ">=3.11"
dependencies = [
    DEPS_PLACEHOLDER
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.13.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "B", "C90", "UP", "S", "T20", "RET", "SIM"]
ignore = ["E501", "S101", "S311", "B008"]

[tool.ruff.lint.per-file-ignores]
"test_*.py" = ["S101", "ANN001", "ANN201", "D103"]
"__init__.py" = ["F401", "D104"]

[tool.pytest.ini_options]
testpaths = ["."]
python_files = ["test_*.py"]
addopts = ["--verbose", "--tb=short"]
asyncio_mode = "auto"
'

MAKEFILE_TEMPLATE='# SERVICE_NAME - Makefile
.PHONY: help install dev test lint format fix clean update

.DEFAULT_GOAL := help

help:
	@echo "SERVICE_NAME - Available commands:"
	@grep -E '\''^[a-zA-Z_-]+:.*?## .*$$'\'' $(MAKEFILE_LIST) | awk '\''BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'\''

install: ## Install dependencies
	uv pip sync requirements.txt

dev: ## Install dev dependencies
	uv pip install -e ".[dev]"

test: ## Run tests
	PYTHONPATH=. python -m pytest -v --tb=short

lint: ## Check code
	ruff check .

format: ## Format code
	ruff format .

fix: ## Auto-fix issues
	ruff check . --fix && ruff format .

clean: ## Clean artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache

update: ## Update requirements
	uv pip compile pyproject.toml -o requirements.txt
'

echo "🚀 TIER 4 Batch Migration Started"
echo "=================================="

for service in "${SERVICES[@]}"; do
    echo ""
    echo "📦 Migrating: $service"

    cd "/home/juan/vertice-dev/backend/services/$service"

    # Extract dependencies from requirements.txt
    if [ -f "requirements.txt" ]; then
        echo "  ├─ Extracting dependencies..."
        deps=$(grep -v '^#' requirements.txt | grep -v '^$' | sed 's/^/    "/;s/$/",/' | tr '\n' ' ')
        # Remove trailing comma
        deps=${deps%, }
    else
        echo "  ├─ No requirements.txt found, using minimal deps..."
        deps='"fastapi>=0.115.0", "uvicorn>=0.32.0"'
    fi

    # Get first line of any README or main file for description
    desc="MAXIMUS Service"
    if [ -f "README.md" ]; then
        desc=$(head -n1 README.md | sed 's/^# //')
    fi

    # Create pyproject.toml
    echo "  ├─ Creating pyproject.toml..."
    echo "$PYPROJECT_TEMPLATE" | sed "s/SERVICE_NAME/$service/g; s/SERVICE_DESC/$desc/g; s|DEPS_PLACEHOLDER|$deps|g" > pyproject.toml

    # Compile with uv
    echo "  ├─ Compiling dependencies with uv..."
    if uv pip compile pyproject.toml -o requirements-new.txt 2>&1 | grep -q "Resolved"; then
        # Backup old requirements
        if [ -f "requirements.txt" ]; then
            mv requirements.txt requirements.txt.old
        fi
        mv requirements-new.txt requirements.txt
        echo "  ├─ ✅ Dependencies compiled"
    else
        echo "  ├─ ⚠️  Compilation failed, keeping old requirements.txt"
    fi

    # Run ruff
    echo "  ├─ Running ruff check --fix..."
    ruff check . --fix > /dev/null 2>&1 || true

    echo "  ├─ Running ruff format..."
    ruff format . > /dev/null 2>&1 || true

    # Create Makefile
    echo "  ├─ Creating Makefile..."
    echo "$MAKEFILE_TEMPLATE" | sed "s/SERVICE_NAME/$service/g" > Makefile

    echo "  └─ ✅ $service migrated"
done

echo ""
echo "=================================="
echo "✅ TIER 4 Batch Migration Complete"
echo "Migrated ${#SERVICES[@]} services"
