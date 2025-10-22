# MAXIMUS AI 3.0 - Test Suite

**Current Coverage:** 0.58% → Target: 90%+
**Test Strategy:** Risk-Based (Critical First) + AI-Assisted
**Philosophy:** DOUTRINA VÉRTICE - Zero Mocks, Production-Ready

---

## Quick Start

```bash
# Start test environment
./scripts/run_testcontainers.sh up

# Run all tests
pytest tests/ -v --cov

# Run smoke tests (validate infrastructure)
pytest tests/integration/test_infrastructure_smoke.py -v
```

---

## Directory Structure

```
tests/
├── conftest.py                  # Shared fixtures (Testcontainers, etc)
├── unit/                        # Fast, isolated tests
│   ├── test_data_orchestrator_coverage.py
│   ├── test_event_collector_coverage.py
│   └── test_metrics_collector_coverage.py
├── integration/                 # Multi-component with real services
│   └── test_infrastructure_smoke.py
├── e2e/                         # Full workflow tests
├── benchmarks/                  # Performance tests
├── stress/                      # Stress & chaos tests
├── fixtures/                    # Test data & configs
│   ├── init_test_db.sql        # PostgreSQL schema
│   └── prometheus.yml          # Metrics config
└── README.md (this file)
```

---

## Coverage Progress

### FASE 1: Infrastructure ✅ COMPLETE
- Testcontainers setup (Kafka, Redis, PostgreSQL, MinIO)
- AI test generator (`scripts/generate_tests.py`)
- Coverage monitoring (`scripts/coverage_report.py`)
- Pre-commit hooks
- Documentation (TESTING.md)

### FASE 2: Critical Modules (In Progress)
**Target:** 95%+ coverage on safety-critical modules

- [ ] Governance (`governance/ethical_guardian.py`, `governance/policy_engine.py`)
- [x] Justice/Constitutional (`justice/constitutional_validator.py` - 100%)
- [ ] Ethics (`ethics/kantian_checker.py`, `ethics/consequentialist_engine.py`)
- [ ] Fairness (`fairness/bias_detector.py`, `fairness/mitigation.py`)

**Expected Coverage after FASE 2:** ~21.5%

### FASE 3-6: Upcoming
- FASE 3: Consciousness & Core (Target: 85%+) → ~51%
- FASE 4: Compliance & ML (Target: 80%+) → ~63%
- FASE 5: Supporting Modules (Target: 75%+) → ~76%
- FASE 6: Long Tail + Edge Cases → **90%+ COMPLETE**

---

## Running Tests

### By Type
```bash
# Unit (fast, no Docker)
pytest tests/unit -v -m unit

# Integration (requires Testcontainers)
./scripts/run_testcontainers.sh up
pytest tests/integration -v -m integration

# E2E (full stack)
pytest tests/e2e -v -m e2e

# Parallel (faster)
pytest tests/ -n auto
```

### By Module
```bash
# Governance tests
pytest tests/ -k "governance" -v

# Constitutional validator
pytest tests/test_constitutional_validator_100pct.py -v

# Justice module
pytest tests/ -k "justice" -v --cov=justice
```

### Coverage
```bash
# Basic coverage report
pytest --cov --cov-report=term-missing

# HTML report
pytest --cov --cov-report=html
open htmlcov/index.html

# Detailed analysis
python scripts/coverage_report.py --current htmlcov --modules
```

---

## Writing New Tests

### Generate with AI
```bash
# Generate unit tests
python scripts/generate_tests.py \
  governance/ethical_guardian.py \
  --test-type unit \
  --coverage-target 95 \
  --validate

# Generate integration tests
python scripts/generate_tests.py \
  consciousness/esgt/coordinator.py \
  --test-type integration \
  --coverage-target 90
```

### Manual Template
```python
"""
Module Name - Test Suite
Coverage Target: 90%+
"""

import pytest
from module_name import YourClass

class TestYourClass:
    """Tests for YourClass."""

    @pytest.mark.unit
    def test_method_success(self):
        """
        SCENARIO: Description
        EXPECTED: Expected outcome
        """
        # Arrange
        instance = YourClass()

        # Act
        result = instance.method()

        # Assert
        assert result == expected_value
```

---

## Test Fixtures

### Testcontainers (Integration/E2E)
```python
def test_with_kafka(kafka_producer, consciousness_topics):
    """Use real Kafka instance."""
    kafka_producer.send("consciousness.global_workspace", value=b"test")
    kafka_producer.flush()

def test_with_redis(redis_client_fixture):
    """Use real Redis instance."""
    redis_client_fixture.set("key", "value")
    assert redis_client_fixture.get("key") == "value"

def test_with_postgres(postgres_connection):
    """Use real PostgreSQL instance."""
    cursor = postgres_connection.cursor()
    cursor.execute("SELECT * FROM governance.audit_trail")
```

### Sample Data
```python
def test_with_sample_data(sample_threat_data, sample_decision_request):
    """Use pre-defined test data."""
    # sample_threat_data has realistic threat info
    # sample_decision_request has governance request
```

---

## Coverage Targets by Module

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| justice | 45.27% | 95%+ | ✅ HIGH |
| governance | 0% | 95%+ | 🔴 CRITICAL |
| ethics | 0% | 95%+ | 🔴 CRITICAL |
| fairness | 0% | 95%+ | 🔴 CRITICAL |
| consciousness | 0% | 85%+ | 🟡 HIGH |
| compliance | 0% | 80%+ | 🟡 HIGH |
| autonomic_core | 0% | 80%+ | 🟢 MEDIUM |

---

## CI/CD

Tests run automatically on:
- Every commit (via pre-commit hooks - fast unit tests)
- Every push (via GitHub Actions - full suite)
- Every PR (with coverage delta check)

**Coverage Gate:** PRs must increase coverage by ≥5% or maintain ≥90% overall.

---

## Troubleshooting

### Docker not running
```bash
docker info  # Check status
./scripts/run_testcontainers.sh up  # Start containers
```

### Port conflicts
```bash
./scripts/run_testcontainers.sh down
./scripts/run_testcontainers.sh clean
```

### Coverage not updating
```bash
rm -rf .coverage htmlcov/
pytest --cov --cov-report=html
```

For more help, see [TESTING.md](../TESTING.md)

---

## Next Steps

1. **Run infrastructure smoke tests:**
   ```bash
   pytest tests/integration/test_infrastructure_smoke.py -v
   ```

2. **Start FASE 2 (Critical Modules):**
   ```bash
   python scripts/generate_tests.py governance/ethical_guardian.py --test-type unit --coverage-target 95
   ```

3. **Monitor progress:**
   ```bash
   python scripts/coverage_report.py --current htmlcov --modules
   ```

**Goal:** 90%+ coverage, production-ready tests, zero mocks! 🚀
