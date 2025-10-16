# TRACK 1: BIBLIOTECAS COMPARTILHADAS

**Executor:** Dev Sênior A  
**Especialidade:** Python, Testing, Library Design  
**Duração:** 7 dias (Dias 4-10)  
**Branch:** `backend-transformation/track1-libs`

---

## MISSÃO

Criar 3 bibliotecas compartilhadas production-ready que eliminarão 30% de duplicação de código:
1. `vertice_core` - logging, tracing, config, exceptions
2. `vertice_api` - FastAPI utilities, health checks, middleware
3. `vertice_db` - Database patterns, repositories

---

## PRÉ-REQUISITOS

### Aguardar GATE 1
- [ ] Port registry completo (Track 2)
- [ ] Aprovação do Arquiteto-Chefe

### Verificar Ambiente
```bash
python --version  # >= 3.11
uv --version      # >= 0.1.0
docker --version  # >= 24.0
```

---

## PRINCÍPIOS DE EXECUÇÃO

### 1. Zero Dependências Circulares
- vertice_core: ZERO deps internas
- vertice_api: pode depender de vertice_core
- vertice_db: pode depender de vertice_core

### 2. Production-Ready desde v1.0.0
- ❌ TODO/FIXME proibidos
- ✅ Coverage ≥95%
- ✅ Type hints completos (mypy --strict)
- ✅ Docstrings Google style

### 3. Versionamento Semântico
- v1.0.0 = primeira release estável
- Breaking changes = major bump
- Features = minor bump
- Bugfixes = patch bump

---

## DIA 4: vertice_core - Estrutura Base

### 4.1 Criar Projeto (1h)

```bash
cd /home/juan/vertice-dev/backend
mkdir -p libs/vertice_core/{src/vertice_core,tests}
cd libs/vertice_core
```

**Criar `pyproject.toml`:**
```toml
[project]
name = "vertice-core"
version = "1.0.0"
description = "Core utilities for Vértice services"
requires-python = ">=3.11"
authors = [
    {name = "Vértice Team", email = "dev@vertice.ai"}
]
readme = "README.md"
license = {text = "MIT"}
dependencies = [
    "structlog>=24.0.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
    "opentelemetry-instrumentation-httpx>=0.41b0",
    "opentelemetry-instrumentation-redis>=0.41b0",
    "opentelemetry-exporter-otlp>=1.20.0",
    "prometheus-client>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.13.0",
    "mypy>=1.8.0",
    "types-pyyaml",
]

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--cov=src/vertice_core",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-fail-under=95",
    "-v",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
]

[tool.coverage.run]
source = ["src/vertice_core"]
omit = ["tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]

[tool.ruff]
line-length = 100
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "UP",  # pyupgrade
    "ANN", # flake8-annotations
    "S",   # flake8-bandit
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "DTZ", # flake8-datetimez
    "RUF", # ruff-specific
]
ignore = [
    "ANN101", # Missing type annotation for self
    "ANN102", # Missing type annotation for cls
    "S101",   # Use of assert (pytest uses it)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ANN201", "ANN001"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_unreachable = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
show_error_codes = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[[tool.mypy.overrides]]
module = "structlog.*"
ignore_missing_imports = true
```

**Instalar dependências:**
```bash
uv sync --group dev
```

**Criar estrutura:**
```bash
touch src/vertice_core/__init__.py
touch src/vertice_core/{logging.py,config.py,tracing.py,exceptions.py,metrics.py}
touch tests/{conftest.py,test_logging.py,test_config.py,test_tracing.py,test_exceptions.py,test_metrics.py}
touch README.md .gitignore
```

**`.gitignore`:**
```
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
dist/
build/
*.egg-info/
.venv/
venv/
```

**Checkpoint:**
```bash
git add .
git commit -m "chore(vertice-core): initialize project structure"
```

---

### 4.2 Implementar logging.py (2h)

**`src/vertice_core/logging.py`:**
```python
"""Structured JSON logging for all Vértice services.

This module provides structured logging using structlog with JSON output,
ISO8601 timestamps, context variables, and automatic exception formatting.

Example:
    Basic usage::

        from vertice_core.logging import get_logger

        logger = get_logger("my_service")
        logger.info("user_login", user_id=123, ip="192.168.1.1")
        logger.error("database_error", error="connection timeout", retry_count=3)

    Output (JSON)::

        {
            "event": "user_login",
            "user_id": 123,
            "ip": "192.168.1.1",
            "timestamp": "2025-10-16T14:30:00.123456Z",
            "level": "info",
            "logger": "my_service"
        }

    Context variables::

        import structlog

        structlog.contextvars.bind_contextvars(request_id="abc-123")
        logger.info("processing_request")  # request_id automatically included
        structlog.contextvars.clear_contextvars()

Note:
    All services MUST use this logger instead of stdlib logging.
    This ensures consistent log format across the entire system.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import FilteringBoundLogger


_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_logger(
    service_name: str,
    level: str = "INFO",
) -> FilteringBoundLogger:
    """Get a configured structured logger for a service.

    Args:
        service_name: Name of the service (e.g., "maximus_core", "api_gateway").
                     This will appear in the "logger" field of all log entries.
        level: Minimum log level. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
              Defaults to INFO.

    Returns:
        A configured structlog BoundLogger ready for use.

    Raises:
        ValueError: If level is not a valid log level name.

    Example:
        >>> logger = get_logger("api_gateway", level="DEBUG")
        >>> logger.debug("request_received", method="POST", path="/api/v1/query")
        >>> logger.info("request_processed", duration_ms=45.2, status=200)
        >>> logger.error("external_api_failed", service="osint", error="timeout")

    Note:
        The logger automatically includes:
        - timestamp (ISO8601 format)
        - log level
        - logger name (service_name)
        - exception info (when logging from except block)
        - context variables (set via structlog.contextvars)
    """
    level_upper = level.upper()
    if level_upper not in _LOG_LEVELS:
        raise ValueError(
            f"Invalid log level: {level}. "
            f"Must be one of: {', '.join(_LOG_LEVELS.keys())}"
        )

    # Configure standard library logging (structlog backend)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=_LOG_LEVELS[level_upper],
    )

    # Configure structlog processors
    structlog.configure(
        processors=[
            # Merge context variables (request_id, user_id, etc)
            structlog.contextvars.merge_contextvars,
            # Add log level
            structlog.stdlib.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Add ISO8601 timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add stack info (if requested)
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.dev.set_exc_info,
            structlog.processors.format_exc_info,
            # Render as JSON
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger(service_name)
```

**Testes `tests/test_logging.py` (COMPLETOS):**
```python
"""Tests for vertice_core.logging module."""

import json
import logging

import pytest
import structlog
from vertice_core.logging import get_logger


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_structlog_instance(self) -> None:
        """Test that get_logger returns a structlog BoundLogger."""
        logger = get_logger("test_service")
        assert isinstance(logger, structlog.stdlib.BoundLogger)

    def test_accepts_custom_log_level(self) -> None:
        """Test that custom log level can be set."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger = get_logger("test_service", level=level)
            assert logger is not None

    def test_rejects_invalid_log_level(self) -> None:
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log level"):
            get_logger("test_service", level="INVALID")

    def test_case_insensitive_log_level(self) -> None:
        """Test that log level is case-insensitive."""
        logger_upper = get_logger("test1", level="INFO")
        logger_lower = get_logger("test2", level="info")
        logger_mixed = get_logger("test3", level="InFo")
        
        assert logger_upper is not None
        assert logger_lower is not None
        assert logger_mixed is not None


class TestLogOutput:
    """Tests for log output format."""

    def test_outputs_valid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that logger outputs valid JSON."""
        logger = get_logger("test_service", level="INFO")
        logger.info("test_event", user_id=123, action="login")

        captured = capsys.readouterr()
        log_line = captured.out.strip()

        # Must be valid JSON
        log_entry = json.loads(log_line)
        assert isinstance(log_entry, dict)

    def test_includes_required_fields(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that log entry includes all required fields."""
        logger = get_logger("test_service", level="INFO")
        logger.info("test_event", user_id=123)

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        # Required fields
        assert "event" in log_entry
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "logger" in log_entry

        # Values
        assert log_entry["event"] == "test_event"
        assert log_entry["level"] == "info"
        assert log_entry["logger"] == "test_service"
        assert log_entry["user_id"] == 123

    def test_preserves_custom_fields(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that custom fields are preserved."""
        logger = get_logger("test_service", level="INFO")
        
        custom_data = {
            "string": "value",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        
        logger.info("test_event", **custom_data)

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        for key, value in custom_data.items():
            assert log_entry[key] == value


class TestLogLevels:
    """Tests for log level filtering."""

    def test_respects_log_level_filtering(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that log level filtering works correctly."""
        logger = get_logger("test_service", level="WARNING")

        # DEBUG and INFO should NOT appear
        logger.debug("debug_message")
        logger.info("info_message")
        captured = capsys.readouterr()
        assert captured.out == ""

        # WARNING should appear
        logger.warning("warning_message")
        captured = capsys.readouterr()
        assert "warning_message" in captured.out

        # ERROR should appear
        logger.error("error_message")
        captured = capsys.readouterr()
        assert "error_message" in captured.out

    def test_debug_level_shows_all(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that DEBUG level shows all messages."""
        logger = get_logger("test_service", level="DEBUG")

        logger.debug("debug_msg")
        logger.info("info_msg")
        logger.warning("warning_msg")

        captured = capsys.readouterr()
        assert "debug_msg" in captured.out
        assert "info_msg" in captured.out
        assert "warning_msg" in captured.out


class TestExceptionLogging:
    """Tests for exception handling."""

    def test_formats_exceptions_correctly(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that exceptions are properly captured and formatted."""
        logger = get_logger("test_service", level="ERROR")

        try:
            raise ValueError("Test error message")
        except ValueError:
            logger.exception("error_occurred", context="test_operation")

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        assert log_entry["event"] == "error_occurred"
        assert log_entry["context"] == "test_operation"
        assert "exception" in log_entry
        assert "ValueError" in log_entry["exception"]
        assert "Test error message" in log_entry["exception"]

    def test_captures_stack_trace(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that stack trace is included in exception logs."""
        logger = get_logger("test_service", level="ERROR")

        try:
            1 / 0
        except ZeroDivisionError:
            logger.exception("division_error")

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        assert "exception" in log_entry
        assert "ZeroDivisionError" in log_entry["exception"]
        assert "division by zero" in log_entry["exception"]
        # Stack trace should be present
        assert "Traceback" in log_entry["exception"]


class TestContextVariables:
    """Tests for context variables support."""

    def test_context_variables_included(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that context variables are automatically included."""
        logger = get_logger("test_service", level="INFO")

        # Bind context
        structlog.contextvars.bind_contextvars(
            request_id="req-123",
            user_id=456,
        )

        logger.info("test_event", action="login")

        # Clear context for other tests
        structlog.contextvars.clear_contextvars()

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        # Context vars should be present
        assert log_entry["request_id"] == "req-123"
        assert log_entry["user_id"] == 456
        # Event-specific field
        assert log_entry["action"] == "login"

    def test_context_cleared_properly(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that clearing context removes variables."""
        logger = get_logger("test_service", level="INFO")

        # Bind and clear
        structlog.contextvars.bind_contextvars(temp_var="temp_value")
        structlog.contextvars.clear_contextvars()

        logger.info("test_event")

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        # temp_var should NOT be present
        assert "temp_var" not in log_entry


class TestMultipleLoggers:
    """Tests for multiple logger instances."""

    def test_multiple_loggers_independent(self) -> None:
        """Test that multiple loggers can coexist."""
        logger1 = get_logger("service1")
        logger2 = get_logger("service2")

        assert logger1 is not None
        assert logger2 is not None

    def test_loggers_have_correct_names(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that each logger has its correct name."""
        logger1 = get_logger("service_alpha", level="INFO")
        logger2 = get_logger("service_beta", level="INFO")

        logger1.info("event_from_alpha")
        out1 = capsys.readouterr().out
        log1 = json.loads(out1.strip())

        logger2.info("event_from_beta")
        out2 = capsys.readouterr().out
        log2 = json.loads(out2.strip())

        assert log1["logger"] == "service_alpha"
        assert log2["logger"] == "service_beta"
```

**Validar:**
```bash
cd /home/juan/vertice-dev/backend/libs/vertice_core

# Lint
uv run ruff check src/vertice_core/logging.py tests/test_logging.py
uv run ruff format --check src/vertice_core/logging.py tests/test_logging.py

# Type check
uv run mypy src/vertice_core/logging.py

# Tests
uv run pytest tests/test_logging.py -v --cov=src/vertice_core/logging.py --cov-report=term-missing

# EXPECTED: 100% coverage, all tests pass
```

**Checkpoint:**
```bash
git add src/vertice_core/logging.py tests/test_logging.py
git commit -m "feat(vertice-core): implement structured JSON logging"
```

---

### 4.3 Implementar exceptions.py (1h)

(Continua com implementação completa similar...)

---

## VALIDAÇÃO DIA 4

```bash
# Verificar estrutura
ls -la src/vertice_core/
# EXPECTED: logging.py implementado

# Rodar testes
uv run pytest -v --cov

# EXPECTED: test_logging.py passa, coverage ≥95%

# Commit checkpoint
git log --oneline -3
# EXPECTED: Pelo menos 2 commits (estrutura + logging)
```

---

## DIAS 5-6: Completar vertice_core

**Implementar TODOS os módulos restantes:**
- `config.py` - BaseServiceSettings
- `tracing.py` - OpenTelemetry
- `exceptions.py` - Exception hierarchy
- `metrics.py` - Prometheus helpers

**Processo para cada módulo:**
1. Implementar código (1-2h)
2. Escrever testes completos (1h)
3. Validar (ruff + mypy + pytest)
4. Commit

**Critério de sucesso Dia 6:**
- [ ] 5 módulos implementados
- [ ] Coverage global ≥95%
- [ ] Zero erros de lint/type check
- [ ] README.md completo com examples

---

## DIA 7-9: vertice_api

(Seguir mesmo padrão do vertice_core)

**Módulos:**
- `factory.py` - FastAPI app factory
- `health.py` - Health endpoints
- `middleware.py` - Rate limit, CORS, auth
- `dependencies.py` - Dependency injection
- `versioning.py` - API versioning

---

## DIA 10: vertice_db

**Módulos:**
- `session.py` - AsyncSession manager
- `repository.py` - Generic repository
- `base.py` - SQLAlchemy base

**ATENÇÃO:** Testes com testcontainers PostgreSQL.

---

## VALIDAÇÃO FINAL TRACK 1

```bash
# Lint todas as libs
cd /home/juan/vertice-dev/backend/libs
for lib in */; do
    echo "=== $lib ==="
    cd "$lib"
    uv run ruff check . || exit 1
    uv run mypy src || exit 1
    uv run pytest --cov --cov-fail-under=95 || exit 1
    cd ..
done

# Build packages
cd vertice_core && uv build && cd ..
cd vertice_api && uv build && cd ..
cd vertice_db && uv build && cd ..

# Check no TODOs
! grep -r "TODO\|FIXME\|XXX" libs/*/src/

echo "✅ TRACK 1 COMPLETO"
```

**Entregáveis:**
- [ ] vertice_core v1.0.0
- [ ] vertice_api v1.0.0
- [ ] vertice_db v1.0.0
- [ ] Coverage ≥95% cada
- [ ] Documentação completa
- [ ] PR aberto para merge

---

**PRÓXIMOS PASSOS:**
Aguardar merge → notificar Track 3 → libs disponíveis para uso
