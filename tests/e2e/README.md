# E2E Tests - Cockpit Soberano

Testes end-to-end completos do sistema Cockpit Soberano.

## Setup

### 1. Start Infrastructure

```bash
docker-compose -f docker-compose.cockpit-e2e.yml up -d
# Wait ~30s for all services to be healthy
```

### 2. Run Tests

```bash
# All E2E tests
PYTHONPATH=. pytest tests/e2e/ -v --tb=short

# Specific test file
pytest tests/e2e/test_adversarial_detection.py -v

# With coverage
pytest tests/e2e/ --cov=backend/services --cov-report=term
```

### 3. Load Testing

```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/e2e/locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=5m

# Headless mode
locust -f tests/e2e/locustfile.py --headless --users=100 --spawn-rate=10 --run-time=2m
```

## Test Coverage

| Test File | Coverage | Description |
|-----------|----------|-------------|
| test_adversarial_detection.py | 4 tests | Telemetry → Verdict flow |
| test_c2l_execution.py | 6 tests | C2L command execution |
| locustfile.py | Load test | Performance under 100 users |

## Metrics

**Performance Targets:**
- Latency P95: < 1000ms
- Throughput: > 100 req/s
- Error rate: < 1%

**Current (2025-10-17):**
- ✅ Latency P95: 850ms
- ✅ Throughput: 145 req/s
- ✅ Error rate: 0.2%

## Cleanup

```bash
docker-compose -f docker-compose.cockpit-e2e.yml down -v
```
