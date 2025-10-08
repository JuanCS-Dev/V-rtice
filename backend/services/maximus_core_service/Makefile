# MAXIMUS Core Service - Makefile
# Modern Python tooling: uv + ruff
# Quality-first development following Doutrina Vértice v2.0

.PHONY: help install dev test lint format check clean update

# Default target
.DEFAULT_GOAL := help

help: ## Mostra esta mensagem de ajuda
	@echo "MAXIMUS Core Service - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instalar dependências (production)
	uv pip sync requirements.txt

dev: ## Instalar dependências (development)
	uv pip install -e ".[dev]"

test: ## Rodar todos os testes
	PYTHONPATH=. python -m pytest consciousness/ -v --tb=short

test-fast: ## Rodar testes rápidos (skip slow)
	PYTHONPATH=. python -m pytest consciousness/ -v --tb=short -m "not slow"

test-coverage: ## Rodar testes com coverage
	PYTHONPATH=. python -m pytest consciousness/ -v --tb=short --cov=consciousness --cov-report=term-missing

test-biomimetic: ## Rodar apenas testes biomimetic
	PYTHONPATH=. python -m pytest consciousness/test_biomimetic_safety_bridge.py consciousness/test_end_to_end_validation.py -v

lint: ## Verificar código (ruff check)
	ruff check .

format: ## Formatar código (ruff format)
	ruff format .

check: ## Lint + format check (CI-ready)
	ruff check .
	ruff format --check .

fix: ## Auto-fix problemas (ruff check --fix)
	ruff check . --fix
	ruff format .

clean: ## Limpar cache e build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml
	rm -rf .ruff_cache .mypy_cache
	rm -rf dist build *.egg-info

update: ## Atualizar requirements.txt (uv pip compile)
	uv pip compile pyproject.toml -o requirements.txt

upgrade: ## Upgrade all dependencies
	uv pip compile pyproject.toml -o requirements.txt --upgrade

# Development commands
run-api: ## Rodar API local (development)
	PYTHONPATH=. uvicorn api:app --reload --host 0.0.0.0 --port 8000

shell: ## Abrir Python shell com PYTHONPATH configurado
	PYTHONPATH=. python

# Docker commands (if needed)
docker-build: ## Build Docker image
	docker build -t maximus-core:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 maximus-core:latest

# Safety commands
audit: ## Security audit (pip-audit)
	pip-audit || true

validate: ## Validate Padrão Pagani compliance
	@echo "🔍 Checking Padrão Pagani compliance..."
	@echo "1. Checking for MOCK usage..."
	@grep -r "mock\|Mock\|MagicMock\|patch" consciousness/ --include="*.py" --exclude-dir=tests | grep -v "test_" | grep -v "NO MOCK" | wc -l || echo "0"
	@echo "2. Checking for PLACEHOLDER/TODO..."
	@grep -r "TODO\|FIXME\|HACK\|PLACEHOLDER\|NotImplementedError" consciousness/ --include="*.py" | grep -v "test_" | grep -v "NO TODO" | wc -l || echo "0"
	@echo "3. Running tests..."
	@$(MAKE) test-fast
	@echo "✅ Validation complete"
