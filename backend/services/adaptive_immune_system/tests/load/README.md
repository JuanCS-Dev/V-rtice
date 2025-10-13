# Load Testing - HITL API

## Overview

Load tests para validar o comportamento do Adaptive Immune System - HITL API sob carga concorrente.

**Ferramenta**: Locust 2.20.0
**Target**: 100+ usuários concorrentes
**SLAs**:
- P95 latency < 500ms
- Error rate < 0.1%
- Throughput > 100 req/s

---

## Scenarios

### 1. Read-Heavy Workload (Default)
**Objetivo**: Simular analistas navegando reviews

- **Usuários**: 100
- **Duração**: 5 minutos
- **Mix**: 90% reads, 10% writes
- **Endpoints**:
  - 50% `GET /hitl/reviews`
  - 30% `GET /hitl/reviews?severity=X`
  - 15% `GET /hitl/reviews/{id}`
  - 10% `GET /hitl/reviews/stats`
  - 5% `POST /hitl/decisions`

### 2. Write-Heavy Workload
**Objetivo**: Simular tomada de decisões em batch

- **Usuários**: 50
- **Duração**: 5 minutos
- **Mix**: 50% reads, 50% writes

### 3. Health Check Monitoring
**Objetivo**: Simular monitoramento contínuo

- **Usuários**: 5
- **Duração**: Contínuo
- **Endpoints**: `/health`, `/health/ready`, `/health/live`, `/metrics`

---

## Quick Start

### 1. Install Dependencies

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
pip install -r requirements-test.txt
```

### 2. Start HITL API

```bash
# Em um terminal separado
docker-compose up -d adaptive_immune_system postgres redis

# Verificar que está rodando
curl http://localhost:8003/health
```

### 3. Run Load Test (Headless)

```bash
cd tests/load

# Read-heavy scenario (default)
locust -f locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --host http://localhost:8003 \
  --html report.html \
  --csv results

# Ou use o script helper
../../scripts/run_load_tests.sh
```

### 4. View Results

```bash
# Terminal output mostra:
# - Total requests
# - Failure rate
# - P95/P99 latencies
# - RPS (requests per second)
# - SLA validation

# HTML report:
open report.html

# CSV data:
cat results_stats.csv
cat results_failures.csv
```

---

## Run with Web UI

Para análise interativa durante o teste:

```bash
cd tests/load
locust -f locustfile.py --host http://localhost:8003

# Abrir browser
open http://localhost:8089

# Na UI:
# - Número de users: 100
# - Spawn rate: 10 users/s
# - Host: http://localhost:8003
# - Clicar "Start swarming"
```

---

## Run Specific Scenarios

```bash
# Read-heavy only
locust -f locustfile.py ReadHeavyUser --headless -u 100 -r 10 -t 5m

# Write-heavy only
locust -f locustfile.py WriteHeavyUser --headless -u 50 -r 5 -t 5m

# Health checks only
locust -f locustfile.py HealthCheckUser --headless -u 5 -r 1 -t 5m
```

---

## Interpreting Results

### Success Criteria

✅ **PASS** se todos os critérios forem atendidos:
- P95 latency < 500ms
- Error rate < 0.1%
- Throughput > 100 req/s
- Zero crashes ou OOMs

❌ **FAIL** se qualquer SLA for violado

### Typical Results (Reference)

Em um sistema saudável com recursos adequados:

```
Total requests: 60,000
Failures: 12 (0.02%)
P95: 320ms
P99: 580ms
RPS: 200 req/s
```

### Common Issues

**High P95 latency (> 500ms)**:
- Database queries não otimizadas
- CPU saturation
- Network bottleneck

**High error rate (> 0.1%)**:
- Database connection pool esgotado
- Memory leaks (OOM)
- Bugs no código

**Low throughput (< 100 req/s)**:
- Gunicorn workers insuficientes
- CPU bottleneck
- Database bottleneck

---

## Advanced Usage

### Distributed Load Testing

Para simular > 1000 usuários, use master-worker mode:

```bash
# Terminal 1 (Master)
locust -f locustfile.py --master --host http://localhost:8003

# Terminal 2-N (Workers)
locust -f locustfile.py --worker --master-host=localhost
locust -f locustfile.py --worker --master-host=localhost
locust -f locustfile.py --worker --master-host=localhost

# Cada worker adiciona ~250 users de capacidade
```

### Custom User Profiles

Editar `locustfile.py` e ajustar:
- `wait_time`: Tempo entre requests
- `weight`: Distribuição de tráfego
- `@task(N)`: Peso relativo de cada endpoint

### Integration com CI/CD

```bash
# Run headless com exit code baseado em SLAs
locust -f locustfile.py \
  --headless \
  -u 100 -r 10 -t 5m \
  --host http://localhost:8003 \
  --html report.html \
  --exit-code-on-error 1

# Exit code 0 = success, 1 = failure
echo $?
```

---

## Troubleshooting

### "Connection refused"
```bash
# Verificar que HITL API está rodando
curl http://localhost:8003/health

# Verificar porta
netstat -tulpn | grep 8003
```

### "Too many open files"
```bash
# Aumentar limite de file descriptors
ulimit -n 10000
```

### Locust não instala
```bash
# Requer Python 3.9+
python --version

# Instalar dependências do sistema
sudo apt-get install python3-dev
```

---

## Results Archive

Salvar resultados para análise posterior:

```bash
# Criar diretório de resultados
mkdir -p results/$(date +%Y%m%d_%H%M%S)

# Copiar arquivos
cp report.html results/$(date +%Y%m%d_%H%M%S)/
cp results_*.csv results/$(date +%Y%m%d_%H%M%S)/

# Commit para git (opcional)
git add results/
git commit -m "test: Load test results $(date)"
```

---

## Next Steps

Após load testing bem-sucedido:

1. **Stress Testing**: Encontrar breaking point (Milestone 3.11.2)
2. **Performance Profiling**: Identificar gargalos (Milestone 3.11.4)
3. **Capacity Planning**: Dimensionar recursos para produção

---

## References

- **Locust Docs**: https://docs.locust.io
- **FastHttpUser**: https://docs.locust.io/en/stable/increase-performance.html
- **Distributed Testing**: https://docs.locust.io/en/stable/running-distributed.html

---

**Milestone**: 3.11.1
**Status**: Ready for execution
**Owner**: Adaptive Immune System Team
