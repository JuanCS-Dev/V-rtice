# Testing Strategy - Active Immune Core
**Version**: 2.0.0 - Test Environment Management
**Date**: 2025-10-09
**Conformidade**: 100% Doutrina Vértice v2.0

---

## 📊 Overview

Active Immune Core follows a **Quality-First** testing approach with **zero mocks** in production code. All tests use real components and services, ensuring production parity and catching integration bugs early.

---

## 🎯 Test Categories

### 1. Unit Tests
**Marker**: `@pytest.mark.unit` (or no marker)
**Scope**: Individual functions, classes, and components
**Dependencies**: None (no external services required)
**Execution**: Always runs (fast feedback loop)
**Environment**: Minimal - only requires `VERTICE_LYMPHNODE_SHARED_SECRET`

**Examples**:
- Agent behavior tests
- Utility function tests
- Model validation tests
- Singleton pattern tests
- Status and lifecycle tests

**How to run**:
```bash
# Fast unit tests only
make test-unit

# Or directly with pytest
VERTICE_LYMPHNODE_SHARED_SECRET=test-secret \
python -m pytest -v -m "not integration" --tb=short
```

---

### 2. Integration Tests
**Marker**: `@pytest.mark.integration`
**Scope**: Component interactions with real external services
**Dependencies**: Kafka, Redis, PostgreSQL (via docker-compose.test.yml)
**Execution**: Conditional (skips if services unavailable)
**Environment**: Full test stack required

**Examples**:
- CoreManager initialization with real services
- Kafka producer/consumer workflows
- Redis pub/sub operations
- Database CRUD operations
- Full lifecycle tests (initialize → start → stop)

**How to run**:
```bash
# Start test environment
make test-env-up

# Run integration tests
make test-integration

# Stop test environment
make test-env-down

# Or full cycle
make test-full
```

---

### 3. End-to-End Tests
**Marker**: `@pytest.mark.e2e` (future)
**Scope**: Complete system workflows
**Dependencies**: Full application stack
**Execution**: Manual or CI/CD
**Environment**: Staging or production-like

**Examples** (future implementation):
- Agent lifecycle: create → patrol → detect → neutralize → destroy
- Coordination workflows end-to-end
- API request → agent action → event publish

---

## 🏗️ Test Infrastructure

### Docker Compose Test Environment

**File**: `docker-compose.test.yml`

**Services**:
- **Kafka** (KRaft mode, port 9092)
- **Redis** (port 6379)
- **PostgreSQL** (port 5432)

**Usage**:
```bash
# Start
docker-compose -f docker-compose.test.yml up -d

# Check health
docker-compose -f docker-compose.test.yml ps

# Logs
docker-compose -f docker-compose.test.yml logs -f

# Stop and clean
docker-compose -f docker-compose.test.yml down -v
```

---

### Test Fixtures (conftest.py)

#### Service Availability Checkers
- `check_kafka_available()` - Quick Kafka connectivity test
- `check_redis_available()` - Quick Redis ping test
- `check_postgres_available()` - Quick PostgreSQL connection test

#### Session-Scoped Fixtures
- `services_availability` - Checks all services once per session
- `integration_env_available` - Boolean flag for integration test availability

#### CoreManager Fixtures
- `core_manager_initialized` - Provides initialized CoreManager with real services
- `core_manager_started` - Provides fully started CoreManager

#### Auto-Cleanup
- `cleanup_core` (autouse=True) - Ensures test isolation by cleaning up before/after each test

---

## ✅ Test Execution Strategy

### Local Development (Fast Feedback)

```bash
# Quick unit tests (no setup required)
make test-unit
# ~0.2 seconds

# Full test suite (requires test environment)
make test-full
# ~2-3 minutes (includes environment startup)
```

### Continuous Integration (CI/CD)

```yaml
# Stage 1: Unit tests (always)
- name: Unit Tests
  run: |
    VERTICE_LYMPHNODE_SHARED_SECRET=test-secret \
    pytest -m "not integration" --tb=short

# Stage 2: Integration tests (with Docker)
- name: Start Test Environment
  run: docker-compose -f docker-compose.test.yml up -d

- name: Integration Tests
  run: |
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
    REDIS_URL=redis://localhost:6379/0 \
    ACTIVE_IMMUNE_POSTGRES_HOST=localhost \
    ACTIVE_IMMUNE_POSTGRES_DB=immunis_memory_test \
    ACTIVE_IMMUNE_POSTGRES_USER=immune_user \
    ACTIVE_IMMUNE_POSTGRES_PASSWORD=immune_pass_test \
    VERTICE_LYMPHNODE_SHARED_SECRET=test-secret \
    pytest api/core_integration/ -m integration --tb=short

- name: Stop Test Environment
  run: docker-compose -f docker-compose.test.yml down -v
```

---

## 📊 Coverage Requirements

### Targets
- **Unit tests**: > 90% line coverage
- **Integration tests**: > 80% critical path coverage
- **Overall**: > 85% coverage

### How to measure
```bash
# Generate coverage report
make test-coverage

# View HTML report
open htmlcov/index.html

# View terminal report
coverage report
```

---

## 🚫 What We DON'T Do (Doutrina Vértice)

### ❌ NO MOCKS in Production Code
- Production code is **100% mock-free**
- Tests use **real services** (Kafka, Redis, PostgreSQL)
- When services unavailable, tests **skip gracefully** (not fail with mocks)

### ❌ NO PLACEHOLDERS
- No `pass` statements in production code
- No `NotImplementedError` without implementation
- Every function is fully implemented

### ❌ NO TODOs
- No `# TODO:` comments in production code
- Technical debt is resolved immediately
- If something is incomplete, it's documented in issues, not code

---

## ✅ What We DO (Quality-First)

### ✅ Real Services
- Integration tests use **real Kafka, Redis, PostgreSQL**
- Tests validate **actual behavior**, not mocked behavior
- Catches integration bugs early

### ✅ Graceful Skip
- If services unavailable, tests **skip with clear message**
- Developer experience: unit tests always run (fast)
- CI/CD: integration tests run with Docker

### ✅ Clean Fixtures
- Automatic cleanup before/after each test
- No test pollution or side effects
- Reproducible test runs

### ✅ Comprehensive
- Tests cover happy paths AND error paths
- Tests cover edge cases
- Tests validate both success and failure scenarios

---

## 🔍 Troubleshooting

### "Integration tests skipped"
**Cause**: Test environment not running
**Solution**:
```bash
make test-env-up
make test-integration
```

### "Kafka connection refused"
**Cause**: Kafka not healthy yet
**Solution**:
```bash
# Wait for health checks
docker-compose -f docker-compose.test.yml ps

# Check logs
docker-compose -f docker-compose.test.yml logs kafka-test
```

### "Tests hanging"
**Cause**: Async cleanup not completing
**Solution**: Ctrl+C and restart test environment
```bash
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
```

---

## 📚 Examples

### Example: Unit Test
```python
@pytest.mark.unit
def test_component_initialization():
    """Unit test - no external dependencies"""
    component = MyComponent()
    assert component.is_ready is False
```

### Example: Integration Test
```python
@pytest.mark.integration
async def test_kafka_integration(core_manager_started):
    """Integration test - uses real Kafka via fixture"""
    manager = core_manager_started
    
    # This uses REAL Kafka, not a mock
    await manager.lymphnode.publish_cytokine(...)
    
    # Test will skip if Kafka unavailable
```

---

## 🎯 Best Practices

1. **Mark your tests**: Use `@pytest.mark.unit` or `@pytest.mark.integration`
2. **Use fixtures**: Reuse `core_manager_initialized` and `core_manager_started`
3. **Test isolation**: Don't rely on test execution order
4. **Clear assertions**: Use descriptive assertion messages
5. **Clean up**: Let fixtures handle cleanup (don't manual cleanup unless necessary)

---

## 🚀 Quick Reference

```bash
# Unit tests (fast, always works)
make test-unit

# Integration tests (requires test environment)
make test-env-up
make test-integration

# Full validation
make test-full

# With coverage
make test-coverage

# E2E validation script
./scripts/validate_e2e.sh
```

---

**Conformidade**: 100% Doutrina Vértice v2.0
**Status**: ✅ PRODUCTION-READY
**NO MOCKS, NO PLACEHOLDERS, NO TODOS**
