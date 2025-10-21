# MAXIMUS AI 3.0 - Testing Guide

**Coverage Target:** 90%+ (Mission Critical)
**Philosophy:** DOUTRINA VÉRTICE - Zero Mocks, Production-Ready
**Last Updated:** 2025-10-20

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Environment Setup](#test-environment-setup)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Coverage Monitoring](#coverage-monitoring)
6. [AI-Assisted Test Generation](#ai-assisted-test-generation)
7. [Testcontainers](#testcontainers)
8. [CI/CD Integration](#cicd-integration)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Install dependencies
poetry install --with test

# 2. Start test environment (Testcontainers)
./scripts/run_testcontainers.sh up

# 3. Run tests with coverage
pytest tests/ -v --cov --cov-report=html

# 4. View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# 5. Generate coverage analysis
python scripts/coverage_report.py --current htmlcov --modules
```

---

## Test Environment Setup

### Prerequisites

- **Python 3.11+**
- **Docker** (for Testcontainers)
- **Poetry** (dependency management)

### Installation

```bash
# Install test dependencies
poetry install --with test

# Install pre-commit hooks
pre-commit install

# Verify installation
pytest --version
docker --version
```

### Environment Variables

```bash
# For AI test generation (optional)
export ANTHROPIC_API_KEY="your-api-key"

# Test database credentials (used by Testcontainers)
export POSTGRES_USER="maximus_test"
export POSTGRES_PASSWORD="test_password"
export POSTGRES_DB="maximus_test"
```

---

## Running Tests

### Test Types

We follow a three-tier testing strategy:

1. **Unit Tests** (`tests/unit/`) - Fast, isolated, no external dependencies
2. **Integration Tests** (`tests/integration/`) - Multi-component, real services via Testcontainers
3. **E2E Tests** (`tests/e2e/`) - Full workflows, end-to-end scenarios

### Running Specific Test Types

```bash
# Unit tests only (fast, no Docker required)
pytest tests/unit -v -m unit

# Integration tests (requires Testcontainers)
./scripts/run_testcontainers.sh up
pytest tests/integration -v -m integration

# E2E tests (slow, full stack)
pytest tests/e2e -v -m e2e

# Run all tests
pytest tests/ -v

# Parallel execution (faster)
pytest tests/ -n auto
```

### Coverage Options

```bash
# Basic coverage
pytest --cov

# HTML report
pytest --cov --cov-report=html

# Terminal + HTML
pytest --cov --cov-report=term-missing --cov-report=html

# Fail if below threshold
pytest --cov --cov-fail-under=70

# Coverage for specific module
pytest --cov=governance tests/
```

### Test Selection

```bash
# Run tests matching pattern
pytest -k "test_constitutional"

# Run tests by marker
pytest -m "unit and not slow"

# Run specific file
pytest tests/test_constitutional_validator_100pct.py

# Run specific test
pytest tests/test_constitutional_validator_100pct.py::TestConstitutionalValidatorLeiZero::test_approves_decision_promoting_flourishing
```

---

## Writing Tests

### Test Structure

Follow the **AAA pattern** (Arrange, Act, Assert):

```python
"""
Module Name - Test Suite
Coverage Target: 90%+

Author: Your Name
Date: 2025-10-20
"""

import pytest
from module_name import YourClass

class TestYourClass:
    """Tests for YourClass."""

    @pytest.mark.unit
    def test_method_name_success_case(self):
        """
        SCENARIO: Clear description of what you're testing
        EXPECTED: Expected outcome
        """
        # Arrange: Setup test data and dependencies
        instance = YourClass()
        input_data = {"key": "value"}

        # Act: Execute the code under test
        result = instance.method(input_data)

        # Assert: Verify the outcome
        assert result == expected_value
        assert result.status == "success"
```

### Using Fixtures

```python
@pytest.mark.integration
def test_kafka_message_flow(kafka_producer, consciousness_topics):
    """
    SCENARIO: Visual cortex sends message to Global Workspace via Kafka
    EXPECTED: Message received and processed correctly
    """
    # Arrange
    message = {"type": "visual_input", "data": [1, 2, 3]}

    # Act
    kafka_producer.send("consciousness.visual_cortex", value=message)
    kafka_producer.flush()

    # Assert - consume and verify
    # ... (implementation)
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit  # Fast, isolated
@pytest.mark.integration  # Multi-component
@pytest.mark.e2e  # Full workflow
@pytest.mark.slow  # Takes >5 seconds
@pytest.mark.requires_torch  # Needs PyTorch
@pytest.mark.requires_gpu  # Needs CUDA
```

---

## Coverage Monitoring

### Analyzing Coverage

```bash
# Generate detailed report
python scripts/coverage_report.py --current htmlcov --modules --top-n 30

# Compare against baseline
python scripts/coverage_report.py \
  --current htmlcov \
  --baseline htmlcov_baseline \
  --modules

# Generate coverage badge
python scripts/coverage_report.py \
  --current htmlcov \
  --badge coverage-badge.md
```

### Coverage Targets

| Target | Description | Use Case |
|--------|-------------|----------|
| 70% | Baseline Industry | Minimum acceptable |
| 80% | Good Practice | Standard for most modules |
| 90% | High Confidence | Critical modules (governance, ethics, safety) |
| 95%+ | Mission Critical | Constitutional validator, circuit breakers |

### Module-Specific Targets

```python
# In pytest.ini or pyproject.toml
[tool.coverage.run]
source = ["."]

[tool.coverage.report]
# Fail build if critical modules below threshold
fail_under = 90

[tool.coverage.paths]
governance = ["governance/*"]
justice = ["justice/*"]
ethics = ["ethics/*"]
```

---

## AI-Assisted Test Generation

### Using the Test Generator

```bash
# Generate unit tests for a module
python scripts/generate_tests.py \
  governance/ethical_guardian.py \
  --test-type unit \
  --coverage-target 95

# Generate integration tests
python scripts/generate_tests.py \
  consciousness/esgt/coordinator.py \
  --test-type integration \
  --coverage-target 90 \
  --validate

# Custom output path
python scripts/generate_tests.py \
  justice/constitutional_validator.py \
  --test-type e2e \
  --output tests/e2e/test_constitutional_e2e.py
```

### Review & Refine

**IMPORTANT:** AI-generated tests MUST be reviewed before committing:

1. ✅ Verify test logic is correct
2. ✅ Ensure edge cases are covered
3. ✅ Check assertions are meaningful
4. ✅ Validate fixtures are used correctly
5. ✅ Run tests to ensure they pass
6. ✅ Check coverage actually increased

```bash
# After generating, always run:
pytest <generated_test_file> -v --cov
```

---

## Testcontainers

### Architecture

We use **Testcontainers** for integration/e2e tests to ensure production parity:

- **Kafka** - Consciousness messaging (Global Workspace)
- **Redis** - Hot-path state and streams
- **PostgreSQL** - Governance, audit trails, precedents
- **MinIO** - ML model storage (S3-compatible)
- **Prometheus** - Metrics collection

### Starting Testcontainers

```bash
# Start all services
./scripts/run_testcontainers.sh up

# Check status
./scripts/run_testcontainers.sh ps

# View logs
./scripts/run_testcontainers.sh logs kafka

# Stop services
./scripts/run_testcontainers.sh down

# Clean (removes volumes)
./scripts/run_testcontainers.sh clean
```

### Using in Tests

```python
@pytest.mark.integration
def test_consciousness_integration(
    kafka_producer,
    kafka_consumer,
    redis_client_fixture,
    consciousness_topics
):
    """Full consciousness pipeline test with real services."""
    # Kafka producer/consumer automatically connected
    # Redis client ready to use
    # Topics already created

    # Your test code here...
```

### Performance

- **Session-scoped fixtures** - Containers shared across tests (fast)
- **Function-scoped cleanup** - Data cleaned between tests (isolated)
- **Parallel execution** - Use `pytest -n auto` with `pytest-xdist`

Expected runtime:
- Unit tests: <30 seconds
- Integration tests: 2-5 minutes
- E2E tests: 5-10 minutes

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test & Coverage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      docker:
        image: docker:dind

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with test

      - name: Start Testcontainers
        run: ./scripts/run_testcontainers.sh up

      - name: Run tests
        run: pytest tests/ -v --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

      - name: Coverage check
        run: |
          python scripts/coverage_report.py \
            --current htmlcov \
            --baseline htmlcov_baseline \
            --fail-under 70
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Run specific hook
pre-commit run coverage-delta --all-files
```

---

## Troubleshooting

### Common Issues

#### 1. Docker not running

```
Error: Cannot connect to the Docker daemon
```

**Solution:**
```bash
# Check Docker status
docker info

# Start Docker (Linux)
sudo systemctl start docker

# macOS - ensure Docker Desktop is running
```

#### 2. Port conflicts

```
Error: port 9092 already in use
```

**Solution:**
```bash
# Check what's using the port
lsof -i :9092

# Kill the process or change test port
./scripts/run_testcontainers.sh down
./scripts/run_testcontainers.sh clean
```

#### 3. Testcontainers timeout

```
Error: Container failed to start within timeout
```

**Solution:**
```bash
# Increase timeout in conftest.py
max_retries = 60  # Was 30

# Or check Docker resources (increase RAM/CPU)
```

#### 4. Coverage not updating

```bash
# Clear old coverage data
rm -rf .coverage htmlcov/

# Re-run with clean state
pytest --cov --cov-report=html
```

#### 5. Import errors in tests

```
ModuleNotFoundError: No module named 'governance'
```

**Solution:**
```bash
# Ensure parent path is added (already in conftest.py)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Or run with PYTHONPATH
PYTHONPATH=. pytest tests/
```

---

## Best Practices

### ✅ DO

- Write descriptive test names (`test_blocks_decision_causing_permanent_harm`)
- Use docstrings with SCENARIO/EXPECTED
- Test edge cases and error paths
- Use fixtures for setup/teardown
- Run tests before committing
- Aim for >90% coverage on critical modules

### ❌ DON'T

- Use mocks for integration/e2e tests (violates DOUTRINA VÉRTICE)
- Skip tests with `@pytest.mark.skip` without good reason
- Write tests that depend on execution order
- Hardcode sensitive data in tests
- Commit failing tests
- Ignore coverage warnings

---

## Coverage Goals by Phase

### Phase 1 (Week 1) - Infrastructure ✅
- Target: Tooling setup complete
- Status: DONE

### Phase 2 (Week 1-2) - Critical Modules
- Target: 95%+ coverage
- Modules: governance, justice, ethics, fairness
- Expected: ~21.5% overall coverage

### Phase 3 (Week 2-3) - Consciousness & Core
- Target: 85%+ coverage
- Modules: consciousness, autonomic_core, neuromodulation
- Expected: ~51% overall coverage

### Phase 4 (Week 3-4) - Compliance & ML
- Target: 80%+ coverage
- Modules: compliance, performance, federated_learning
- Expected: ~63% overall coverage

### Phase 5 (Week 4) - Supporting Modules
- Target: 75%+ coverage
- Modules: observability, HITL, predictive_coding
- Expected: ~76% overall coverage

### Phase 6 (Week 4-5) - Long Tail
- Target: 90%+ overall
- Focus: Edge cases, error paths, integration tests
- Expected: **90.5%+ COMPLETE**

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Testcontainers Python](https://testcontainers-python.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Hypothesis (Property-based testing)](https://hypothesis.readthedocs.io/)

---

## Support

For questions or issues:
1. Check this guide
2. Review existing tests in `tests/test_constitutional_validator_100pct.py`
3. Run `./scripts/run_testcontainers.sh --help`
4. Check `pytest --markers` for available markers

**Remember:** Tests are not just for coverage - they're documentation, safety nets, and confidence builders. Write them well! 🚀
