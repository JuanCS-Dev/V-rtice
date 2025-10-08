# MAXIMUS Eureka - Makefile
# Modern Python tooling: uv + ruff

.PHONY: help install dev test lint format check clean update

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "MAXIMUS Eureka - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (production)
	uv pip sync requirements.txt

dev: ## Install dependencies (development)
	uv pip install -e ".[dev]"

test: ## Run all tests
	PYTHONPATH=. python -m pytest -v --tb=short

lint: ## Check code (ruff check)
	ruff check .

format: ## Format code (ruff format)
	ruff format .

check: ## Lint + format check (CI-ready)
	ruff check .
	ruff format --check .

fix: ## Auto-fix problems (ruff check --fix)
	ruff check . --fix
	ruff format .

clean: ## Clean cache and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage coverage.xml
	rm -rf .ruff_cache
	rm -rf dist build *.egg-info

update: ## Update requirements.txt (uv pip compile)
	uv pip compile pyproject.toml -o requirements.txt

upgrade: ## Upgrade all dependencies
	uv pip compile pyproject.toml -o requirements.txt --upgrade

# Development commands
run-api: ## Run API local (development)
	PYTHONPATH=. uvicorn api:app --reload --host 0.0.0.0 --port 8024

# Docker commands
docker-build: ## Build Docker image
	docker build -t maximus-eureka:latest .

docker-run: ## Run Docker container
	docker run -p 8024:8024 maximus-eureka:latest
