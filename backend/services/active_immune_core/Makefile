# ============================================================================
# ACTIVE IMMUNE CORE - MAKEFILE
# ============================================================================
#
# Quality-First development targets following Doutrina Vértice.
#
# NO MOCKS, NO PLACEHOLDERS, NO TODOS.
#
# Authors: Juan & Claude
# Version: 2.0.0 - Test Environment Management
# ============================================================================

.PHONY: help install dev test test-unit test-integration test-all test-coverage
.PHONY: test-env-up test-env-down test-env-status test-full
.PHONY: lint format fix clean update

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║          Active Immune Core - Development Commands           ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install          Install production dependencies"
	@echo "  make dev              Install development dependencies"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test-unit        Run unit tests (fast, no external deps)"
	@echo "  make test-integration Run integration tests (requires test env)"
	@echo "  make test-all         Run all tests"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make test-full        Full cycle: start env → test → stop env"
	@echo ""
	@echo "🐋 Test Environment:"
	@echo "  make test-env-up      Start test environment (Docker)"
	@echo "  make test-env-down    Stop test environment"
	@echo "  make test-env-status  Check test environment status"
	@echo ""
	@echo "🎨 Code Quality:"
	@echo "  make lint             Check code with ruff"
	@echo "  make format           Format code with ruff"
	@echo "  make fix              Fix linting issues and format"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean            Remove cache and build artifacts"
	@echo "  make update           Update requirements.txt"
	@echo ""

# ============================================================================
# INSTALLATION
# ============================================================================

install:
	@echo "📦 Installing production dependencies..."
	uv pip sync requirements.txt

dev:
	@echo "📦 Installing development dependencies..."
	uv pip install -e ".[dev]"

# ============================================================================
# TESTING
# ============================================================================

test-unit:
	@echo "🧪 Running unit tests (no external dependencies)..."
	@echo "════════════════════════════════════════════════════"
	PYTHONPATH=. \
	VERTICE_LYMPHNODE_SHARED_SECRET=test-secret \
	python -m pytest -v -m "not integration" --tb=short
	@echo ""
	@echo "✅ Unit tests completed!"

test-integration:
	@echo "🔗 Running integration tests (requires test environment)..."
	@echo "════════════════════════════════════════════════════════════"
	@echo "🔍 Checking if test environment is running..."
	@docker-compose -f docker-compose.test.yml ps 2>/dev/null | grep -q "Up" || \
		(echo "❌ Test environment not running." && \
		 echo "   Start with: make test-env-up" && exit 1)
	@echo "✅ Test environment is running"
	@echo ""
	PYTHONPATH=. \
	KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
	REDIS_URL=redis://localhost:6379/0 \
	ACTIVE_IMMUNE_POSTGRES_HOST=localhost \
	ACTIVE_IMMUNE_POSTGRES_PORT=5432 \
	ACTIVE_IMMUNE_POSTGRES_DB=immunis_memory_test \
	ACTIVE_IMMUNE_POSTGRES_USER=immune_user \
	ACTIVE_IMMUNE_POSTGRES_PASSWORD=immune_pass_test \
	VERTICE_LYMPHNODE_SHARED_SECRET=test-secret \
	python -m pytest api/core_integration/ -v -m integration --tb=short
	@echo ""
	@echo "✅ Integration tests completed!"

test-all:
	@echo "🧪 Running all tests..."
	@echo "═════════════════════════"
	PYTHONPATH=. python -m pytest -v --tb=short
	@echo ""
	@echo "✅ All tests completed!"

test: test-all

test-coverage:
	@echo "📊 Running tests with coverage..."
	@echo "═════════════════════════════════"
	PYTHONPATH=. python -m pytest \
		--cov=. \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		--tb=short
	@echo ""
	@echo "✅ Coverage report generated!"
	@echo "   HTML: htmlcov/index.html"
	@echo "   XML:  coverage.xml"

test-full:
	@echo "🎯 Full test cycle..."
	@echo "════════════════════════"
	$(MAKE) test-env-up
	@echo ""
	$(MAKE) test-all || ($(MAKE) test-env-down && exit 1)
	@echo ""
	$(MAKE) test-env-down
	@echo ""
	@echo "✅ Full test cycle completed!"

# ============================================================================
# TEST ENVIRONMENT (DOCKER)
# ============================================================================

test-env-up:
	@echo "🚀 Starting test environment..."
	@echo "═══════════════════════════════"
	@docker-compose -f docker-compose.test.yml up -d
	@echo ""
	@echo "⏳ Waiting for services to be healthy..."
	@timeout 60 sh -c '\
		while ! docker-compose -f docker-compose.test.yml ps | grep -q "healthy"; do \
			sleep 2; \
			echo "  Still waiting..."; \
		done' || \
		(echo "❌ Services failed to become healthy" && \
		 echo "Logs:" && \
		 docker-compose -f docker-compose.test.yml logs --tail=50 && \
		 exit 1)
	@echo ""
	@echo "✅ Test environment is ready!"
	@echo ""
	@echo "Services running:"
	@docker-compose -f docker-compose.test.yml ps
	@echo ""
	@echo "Environment variables for integration tests:"
	@echo "  KAFKA_BOOTSTRAP_SERVERS=localhost:9092"
	@echo "  REDIS_URL=redis://localhost:6379/0"
	@echo "  ACTIVE_IMMUNE_POSTGRES_HOST=localhost"
	@echo "  ACTIVE_IMMUNE_POSTGRES_DB=immunis_memory_test"

test-env-down:
	@echo "🛑 Stopping test environment..."
	@echo "═══════════════════════════════"
	docker-compose -f docker-compose.test.yml down -v
	@echo ""
	@echo "✅ Test environment stopped and cleaned!"

test-env-status:
	@echo "📊 Test environment status:"
	@echo "═══════════════════════════"
	@docker-compose -f docker-compose.test.yml ps 2>/dev/null || \
		echo "Test environment is not running"

# ============================================================================
# CODE QUALITY
# ============================================================================

lint:
	@echo "🔍 Checking code with ruff..."
	ruff check .

format:
	@echo "🎨 Formatting code with ruff..."
	ruff format .

fix:
	@echo "🔧 Fixing linting issues and formatting..."
	ruff check . --fix && ruff format .
	@echo "✅ Code fixed and formatted!"

# ============================================================================
# MAINTENANCE
# ============================================================================

clean:
	@echo "🧹 Cleaning cache and build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage coverage.xml htmlcov/ 2>/dev/null || true
	@echo "✅ Cleanup completed!"

update:
	@echo "📦 Updating requirements.txt..."
	uv pip compile pyproject.toml -o requirements.txt
	@echo "✅ Requirements updated!"
