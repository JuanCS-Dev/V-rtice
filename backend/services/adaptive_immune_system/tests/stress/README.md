# Stress Testing - HITL API

## Overview

Stress tests para validar comportamento sob condições extremas e encontrar limites do sistema.

**Objetivo**: Identificar breaking point e validar degradação graciosa
**Ferramentas**: pytest + asyncio + httpx + docker stats

---

## Test Suites

### 1. Resource Limits (`test_resource_limits.py`)
**Objetivo**: Validar comportamento sob restrições de recursos

**Testes**:
- ✅ CPU limits - Degradação graciosa sob limite de CPU
- ✅ Memory limits - Sem OOM kill sob pressão de memória
- ✅ DB connection pool - Graceful handling de pool esgotado
- ✅ Network latency - Timeouts funcionando corretamente
- ✅ Combined stress - Resiliência sob múltiplos stressors

**Critérios de Sucesso**:
- Container não reinicia (sem OOM kill)
- Pelo menos 70% requests succeed sob stress
- Erros 503 (não 500) quando sobrecarregado
- Auto-recovery após remoção de stress

### 2. Breaking Point (`test_breaking_point.py`)
**Objetivo**: Encontrar limites de capacidade

**Testes**:
- ✅ Ramp-up gradual (10 → 500 users)
- ✅ Identificação de breaking point
- ✅ Capacity report com recomendações
- ✅ Quick stress check (CI/CD)

**Output**:
- Maximum capacity (users, RPS)
- Performance degradation curve
- Resource usage at breaking point
- Production recommendations

---

## Quick Start

### 1. Prerequisites

```bash
# Instalar dependências
pip install -r requirements-test.txt

# Verificar Docker
docker ps | grep adaptive-immune

# HITL API deve estar rodando
curl http://localhost:8003/health
```

### 2. Run Resource Limits Tests

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

# Run all resource tests
pytest tests/stress/test_resource_limits.py -v -s

# Run specific test
pytest tests/stress/test_resource_limits.py::TestCPULimits::test_cpu_limit_graceful_degradation -v -s

# Skip slow tests
pytest tests/stress/test_resource_limits.py -v -m "not slow"
```

### 3. Run Breaking Point Test

```bash
# Full breaking point test (~10 minutes)
pytest tests/stress/test_breaking_point.py::test_find_breaking_point -v -s

# Quick stress check (~3 minutes, CI/CD friendly)
pytest tests/stress/test_breaking_point.py::test_quick_stress_check -v -s
```

### 4. Run All Stress Tests

```bash
# Run via helper script
./scripts/run_stress_tests.sh

# Or pytest directly
pytest tests/stress/ -v -s --tb=short
```

---

## Understanding Results

### Resource Limits

#### CPU Limits Test
```
Success: 42/50
5xx errors: 0
Timeouts: 8
Final CPU: 95.23%

✅ PASS: System degraded gracefully (no crashes)
```

**Interpretation**:
- 84% success rate under CPU pressure ✅
- 16% timeouts (acceptable) ✅
- Zero 500 errors (no crashes) ✅
- CPU utilization high but stable ✅

#### Memory Limits Test
```
Final memory: 1847.32MB (92.4%)

✅ PASS: Container still running
✅ PASS: Memory usage < 100%
```

**Interpretation**:
- Memory usage high but not exhausted ✅
- No OOM kill ✅
- Graceful handling of memory pressure ✅

#### DB Connection Pool Test
```
Success: 35/50
503 errors: 12
Timeouts: 3

✅ PASS: All requests handled
✅ PASS: Some requests succeeded (queue working)
```

**Interpretation**:
- 70% success rate ✅
- 24% received 503 (service unavailable) ✅
- 6% timeouts ✅
- Zero crashes (500 errors) ✅

### Breaking Point

#### Sample Output
```
============================================================
CAPACITY REPORT
============================================================

✅ Maximum Capacity:
  Users: 200
  RPS: 187.45
  P95 latency: 423ms
  Error rate: 0.12%

❌ Breaking Point:
  Users: 300
  RPS: 142.31
  P95 latency: 1873ms
  Error rate: 3.45%

📊 Degradation:
  Latency increase: 4.4x
  Throughput decrease: 0.8x
  Error rate increase: 3.33%

📈 Performance Curve:
  Users | RPS    | P95 (ms) | Error % | CPU %
  10    | 93.2   | 87       | 0.00    | 12.3
  25    | 117.8  | 145      | 0.01    | 23.4
  50    | 153.4  | 234      | 0.03    | 45.6
  100   | 176.2  | 342      | 0.08    | 78.9
  200   | 187.5  | 423      | 0.12    | 94.2
  300   | 142.3  | 1873     | 3.45    | 99.1  ← Breaking point

💡 Recommendations:
  - Production capacity: 140 users (70% of max)
  - Set autoscaling trigger at: 100 users
  - Configure rate limiting at: 149 req/s
```

**Key Insights**:
1. **Maximum Capacity**: 200 users at 187 RPS
2. **Breaking Point**: 300 users (latency 4.4x, errors 3.45%)
3. **Safe Operating Range**: 140 users (70% margin)
4. **Autoscaling Trigger**: 100 users (50% margin)

---

## Common Issues & Solutions

### Issue: "Container not running"
```bash
# Check container status
docker ps -a | grep adaptive-immune

# Restart if needed
docker-compose restart adaptive_immune_system

# Check logs
docker logs vertice-adaptive-immune --tail 50
```

### Issue: "Tests timeout"
```bash
# Increase pytest timeout
pytest tests/stress/ -v --timeout=600

# Or skip slow tests
pytest tests/stress/ -v -m "not slow"
```

### Issue: "Cannot get container stats"
```bash
# Verify Docker is running
docker info

# Check container name
docker ps --format "{{.Names}}" | grep adaptive

# Update container_name in test if different
```

### Issue: "High baseline latency"
```bash
# Check if system is already under load
docker stats vertice-adaptive-immune --no-stream

# Check database performance
docker exec vertice-postgres psql -U postgres -d adaptive_immune -c "SELECT * FROM pg_stat_activity;"

# Restart services to clear state
docker-compose restart adaptive_immune_system postgres redis
```

---

## Advanced Configuration

### Docker Resource Limits

Edit `docker-compose.yml` to set hard limits:

```yaml
services:
  adaptive_immune_system:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Max 2 CPUs
          memory: 2G       # Max 2GB RAM
        reservations:
          cpus: '1.0'      # Guaranteed 1 CPU
          memory: 1G       # Guaranteed 1GB RAM
```

### Custom Breaking Point Levels

Edit `test_breaking_point.py`:

```python
test_levels = [10, 25, 50, 100, 150, 200, 300, 400, 500]
# Change to:
test_levels = [5, 10, 20, 40, 80, 160, 320]  # Doubling pattern
```

### Network Latency Simulation

Use `tc` (traffic control) to add artificial latency:

```bash
# Add 100ms latency to localhost
sudo tc qdisc add dev lo root netem delay 100ms

# Remove latency
sudo tc qdisc del dev lo root
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run stress tests
  run: |
    docker-compose up -d adaptive_immune_system postgres redis
    pytest tests/stress/test_breaking_point.py::test_quick_stress_check -v
```

### Exit Codes

- **0**: All tests passed
- **1**: One or more tests failed
- **5**: No tests collected (check setup)

---

## Capacity Planning

Use breaking point results for production planning:

### Sizing Recommendations

Based on breaking point of **200 users**:

**Small Deployment** (< 70 users):
- 1 container
- 1 CPU, 1GB RAM
- Single PostgreSQL instance

**Medium Deployment** (70-140 users):
- 2 containers (load balanced)
- 2 CPU, 2GB RAM each
- PostgreSQL with read replicas

**Large Deployment** (> 140 users):
- 3+ containers (horizontal scaling)
- Auto-scaling based on CPU > 70%
- PostgreSQL cluster with connection pooling

### Monitoring Thresholds

Set alerts based on capacity:

```yaml
alerts:
  - alert: HighCPU
    expr: container_cpu_usage > 70
    action: Scale up

  - alert: HighLatency
    expr: p95_latency > 400ms
    action: Investigate

  - alert: ApproachingCapacity
    expr: active_users > 140
    action: Scale proactively
```

---

## Next Steps

After stress testing:

1. ✅ Document capacity limits
2. ✅ Configure autoscaling rules
3. ✅ Set up monitoring alerts
4. ✅ Implement rate limiting
5. ✅ Plan infrastructure sizing

Then proceed to:
- **Milestone 3.11.3**: Security Audit
- **Milestone 3.11.4**: Performance Profiling
- **Milestone 3.11.5**: Chaos Engineering

---

## References

- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io
- **httpx**: https://www.python-httpx.org
- **Docker stats**: https://docs.docker.com/engine/reference/commandline/stats/
- **Capacity Planning**: https://aws.amazon.com/architecture/well-architected/

---

**Milestone**: 3.11.2
**Status**: Ready for execution
**Owner**: Adaptive Immune System Team
