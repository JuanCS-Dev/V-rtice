# 🛡️ VÉRTICE SERVICE REGISTRY - DESIGN TITÂNIO (2025)

**Status**: DESIGN PHASE - PRANCHETA
**Objetivo**: Serviço de registro BLINDADO, INABALÁVEL, DE DIAMANTE PURO
**Data**: 2025-10-24
**Autores**: Juan & Claude

---

## 🎯 FILOSOFIA: TITÂNIO vs CONFIÁVEL

**CONFIÁVEL** = Funciona 99% do tempo
**TITÂNIO** = Funciona 99.99% do tempo + Degrada graciosamente quando falha + Auto-recupera

Este serviço é o **PONTO CENTRAL** do ecossistema (107 serviços). Se ele falhar, TUDO falha.
Portanto: **ZERO COMPROMISSOS** com qualidade.

---

## 📚 FUNDAMENTAÇÃO TEÓRICA (2025 Best Practices)

### 1. **Service Registry Pattern** (CNCF 2024)
- **83%** das organizações com orquestração de containers reportam eficiência operacional melhorada
- **Self-registration** com heartbeats obrigatórios (30s)
- **Health checks ativos** (não apenas passivos)
- **Auto-cleanup** de serviços mortos

### 2. **High Availability Architecture** (HashiCorp Consul)
- **5 nós** distribuídos em 3 availability zones (pode perder 2 nós)
- **3-5 nós** para consensus (Raft algorithm)
- **Odd number** de réplicas para quorum
- **Gossip protocol** para propagação rápida

### 3. **Circuit Breaker Pattern** (AWS Prescriptive Guidance)
- **3 estados**: Closed → Open → Half-Open
- **Exponential backoff**: 1s → 2s → 4s → 8s
- **Retry limit**: Máximo 10% de requests em Half-Open
- **Fail-fast**: Não sobrecarregar serviços downstream

### 4. **Graceful Degradation** (GeeksforGeeks 2025)
- **28%** dos outages poderiam ser mitigados com degradação graciosa
- **Load shedding**: Dropar requests quando sobrecarga
- **Fallback cascata**: Cache local → Env vars → Static config
- **Partial availability**: Preferir dados stale (60s) a erro 503

### 5. **Resilience Patterns** (Microsoft Azure Architecture)
- **Retry pattern**: Para falhas transitórias
- **Timeout pattern**: Para prevenir waiting infinito
- **Bulkhead pattern**: Isolar falhas
- **Rate limiting**: Prevenir resource exhaustion

---

## 🏗️ ARQUITETURA TITÂNIO

### Topologia: 5 Nós em 3 Zonas

```
┌─────────────────────────────────────────────────────────────────┐
│                      NGINX LOAD BALANCER                        │
│         (Round-robin + Health checks 5s + Auto-failover)       │
│                        Port: 8888                               │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
    ┌────────┴────────┐              ┌────────┴────────┐
    │   ZONE A (2x)   │              │   ZONE B (2x)   │
    │  ┌──────────┐   │              │  ┌──────────┐   │
    │  │ Replica1 │   │              │  │ Replica3 │   │
    │  └──────────┘   │              │  └──────────┘   │
    │  ┌──────────┐   │              │  ┌──────────┐   │
    │  │ Replica2 │   │              │  │ Replica4 │   │
    │  └──────────┘   │              │  └──────────┘   │
    └─────────────────┘              └─────────────────┘
             │                                │
             └────────────────┬───────────────┘
                              │
                    ┌─────────┴─────────┐
                    │    ZONE C (1x)    │
                    │   ┌──────────┐    │
                    │   │ Replica5 │    │
                    │   └──────────┘    │
                    └───────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Redis Sentinel   │
                    │  (3 masters + 6   │
                    │  replicas = 9 nós)│
                    └───────────────────┘
```

**Fault Tolerance:**
- ✅ Perde ZONA inteira → Sistema continua (4 nós restantes)
- ✅ Perde 2 réplicas → Sistema continua (quorum: 3 nós)
- ✅ Perde Redis master → Sentinel promove replica (< 1s)
- ✅ Perde TODOS os nós → Clients usam cache local (survival mode)

---

## 🔧 COMPONENTES TITÂNIO

### 1. **Redis Backend com Circuit Breaker BLINDADO**

**Estados do Circuit Breaker:**
```python
CLOSED (Normal):
  - Todas requests vão para Redis
  - Monitora failures (threshold: 3)
  - Latência normal: < 10ms

OPEN (Failure detected):
  - NENHUMA request vai para Redis
  - Retorna IMEDIATAMENTE de cache local
  - Timeout: 30s
  - Log: WARNING "Circuit breaker OPEN - Redis unavailable"

HALF-OPEN (Testing recovery):
  - 10% de requests testam Redis
  - Se 2 sucessos consecutivos → CLOSED
  - Se 1 falha → OPEN novamente
  - Duration: 10s
```

**Retry Logic (Exponential Backoff):**
```python
Attempt 1: Wait 1s   (total: 1s)
Attempt 2: Wait 2s   (total: 3s)
Attempt 3: Wait 4s   (total: 7s)
Attempt 4: GIVE UP   (max: 3 attempts)

Timeout: 5s por operação
```

**Connection Pooling:**
```python
min_idle_connections: 5
max_connections: 50
socket_keepalive: True
socket_keepalive_options: {
    socket.TCP_KEEPIDLE: 60,
    socket.TCP_KEEPINTVL: 10,
    socket.TCP_KEEPCNT: 3
}
health_check_interval: 10s
```

---

### 2. **Local Cache com TTL Inteligente**

**Estratégia de Cache:**
```python
FRESH (< 30s):   Usa sem hesitação
STALE (30-60s):  Usa + async refresh
EXPIRED (> 60s): Força refresh (se Redis up) OU usa stale (se Redis down)
```

**Cache Eviction (LRU):**
```python
max_size: 1000 entradas
eviction_policy: LRU (Least Recently Used)
memory_limit: 50MB
auto_cleanup: A cada 60s
```

**Metrics:**
```python
cache_hits_total
cache_misses_total
cache_evictions_total
cache_size_bytes
cache_age_seconds_p50/p95/p99
```

---

### 3. **Health Checks MULTI-LAYER**

**Níveis de Health:**

```python
HEALTHY (200):
  - Redis: Responding (PING/PONG < 10ms)
  - Circuit Breaker: CLOSED
  - Cache: Hit rate > 70%
  - Memory: < 80% used
  - CPU: < 70% used

DEGRADED (200 + warning):
  - Redis: Responding MAS slow (10-50ms)
  - Circuit Breaker: HALF-OPEN
  - Cache: Hit rate 50-70%
  - Memory: 80-90% used
  - CPU: 70-85% used

UNHEALTHY (503):
  - Redis: Not responding OU timeout
  - Circuit Breaker: OPEN > 60s
  - Cache: Hit rate < 50%
  - Memory: > 90% used
  - CPU: > 85% used
```

**Health Check Response (JSON):**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": 1729770000,
  "uptime_seconds": 86400,
  "components": {
    "redis": {
      "status": "healthy",
      "latency_ms": 2.5,
      "connection_pool": {
        "active": 5,
        "idle": 10,
        "max": 50
      }
    },
    "circuit_breaker": {
      "state": "closed",
      "failure_count": 0,
      "last_failure": null
    },
    "cache": {
      "size": 342,
      "hit_rate": 0.87,
      "memory_mb": 12.5,
      "oldest_entry_age_s": 45
    },
    "system": {
      "cpu_percent": 15.2,
      "memory_percent": 62.3,
      "goroutines": 42
    }
  },
  "active_services": 107
}
```

---

### 4. **Service Registration com Validation**

**Campos Obrigatórios:**
```python
service_name: str       # Único, lowercase, a-z0-9_-
host: str               # IPv4 ou hostname válido
port: int               # 1024-65535
health_endpoint: str    # Path começando com /
```

**Campos Opcionais:**
```python
metadata: dict          # Tags, version, category, etc
tags: list[str]         # Para filtering
version: str            # Semantic versioning
protocol: str           # http, https, grpc, tcp
weight: int             # Load balancing weight (1-100)
```

**Validation Rules:**
```python
# Regex para service_name
^[a-z0-9][a-z0-9_-]{2,63}$

# Validação de host
- IPv4 válido OU
- Hostname válido (RFC 1123) OU
- Container name (Docker)

# Validação de porta
- 1024-65535 (excluir well-known ports)
- Não conflitar com outras registrations

# Health endpoint
- Começar com /
- Responder 200 OK
- Timeout: 5s
```

**Rejection (400 Bad Request):**
```json
{
  "error": "ValidationError",
  "field": "service_name",
  "message": "Service name must match ^[a-z0-9][a-z0-9_-]{2,63}$",
  "provided": "MyService-123!",
  "example": "my-service-123"
}
```

---

### 5. **TTL Management com Auto-Cleanup**

**TTL Strategy:**
```python
REGISTRATION:
  - Initial TTL: 60s
  - Requere heartbeat a cada 30s (50% do TTL)
  - Grace period: 15s (se heartbeat atrasado)

HEARTBEAT:
  - Renova TTL para 60s
  - Atualiza last_seen timestamp
  - Valida que serviço ainda existe (opcional: ping health)

CLEANUP:
  - Background task a cada 30s
  - Remove services com TTL expirado
  - Log: INFO "Removed expired services: [service1, service2]"
  - Metrics: expired_services_total
```

**Auto-Deregistration:**
```python
# Quando serviço para gracefully
1. Service envia DELETE /deregister/{name}
2. Registry remove IMEDIATAMENTE (não espera TTL)
3. Notifica subscribers (opcional: webhooks)

# Quando serviço crasha
1. Heartbeat para de chegar
2. TTL expira após 60s + 15s grace = 75s
3. Auto-cleanup remove
4. Subscribers descobrem na próxima query
```

---

### 6. **Observability FULL-STACK**

**Prometheus Metrics:**
```python
# Operações
registry_operations_total{operation, status}
registry_operation_duration_seconds{operation}

# Estado
registry_active_services
registry_circuit_breaker_state{state}  # 0=closed, 1=open, 2=half-open
registry_cache_hit_rate
registry_cache_size_bytes

# Performance
registry_request_duration_seconds{endpoint, method, status}
registry_redis_latency_seconds
registry_health_check_failures_total

# Resource usage
registry_memory_bytes
registry_cpu_percent
registry_goroutines
```

**Structured Logging (JSON):**
```json
{
  "timestamp": "2025-10-24T08:19:31Z",
  "level": "INFO",
  "component": "redis_backend",
  "event": "circuit_breaker_opened",
  "details": {
    "failure_count": 3,
    "last_error": "connection timeout",
    "threshold": 3,
    "timeout_seconds": 30
  },
  "trace_id": "abc123def456"
}
```

**Distributed Tracing (OpenTelemetry):**
```python
Spans:
  - registry.register (duração total)
    - redis.set (latência Redis)
    - cache.set (latência cache)
    - validation (tempo de validação)
```

---

## 🚨 FAILURE MODES & RECOVERY

### Scenario 1: Redis Master Fails
**Detection**: < 1s (Sentinel heartbeat)
**Action**: Sentinel promove replica automaticamente
**Registry**: Circuit breaker detecta (3 failures) → OPEN → Usa cache local
**Recovery**: Sentinel reconfigura → Registry reconnect → Circuit breaker → HALF-OPEN → CLOSED
**Downtime**: **0s** (cache local previne)
**Data loss**: **0** (Redis replication síncrona)

### Scenario 2: 1 Registry Replica Fails
**Detection**: 5s (NGINX health check)
**Action**: NGINX remove do pool automaticamente
**Impact**: **ZERO** (4 réplicas restantes)
**Recovery**: Docker restart → Auto-rejoin pool
**Downtime**: **0s**

### Scenario 3: 2 Registry Replicas Fail (Quorum = 3)
**Detection**: 5s (NGINX health check)
**Action**: NGINX usa 3 réplicas restantes
**Impact**: **Performance degradation** (67% capacidade)
**Alert**: CRITICAL - "Only 3/5 replicas available"
**Recovery**: Restart failed replicas
**Downtime**: **0s** (degraded mode)

### Scenario 4: ZONA inteira cai (2 replicas perdidas)
**Detection**: 5s (NGINX health check)
**Action**: NGINX usa réplicas de outras zonas
**Impact**: **Performance degradation** (60% capacidade)
**Alert**: CRITICAL - "Zone A unavailable - 3/5 replicas"
**Recovery**: Restart zona
**Downtime**: **0s** (cross-zone redundancy)

### Scenario 5: TODAS as replicas caem (catastrófico)
**Detection**: NGINX retorna 503
**Action**: Clients usam **cache local** (stale data OK)
**Impact**: **No registrations/updates** (read-only mode)
**Duration**: Máximo 60s (cache TTL)
**Alert**: **P0 - "REGISTRY DOWN - ALL REPLICAS FAILED"**
**Recovery**: Restart QUALQUER replica → Sistema volta
**Downtime**: **60s** (depois disso clients começam falhar)

### Scenario 6: Network Partition (Split Brain)
**Detection**: Raft consensus failure
**Action**: Minority partition rejeita writes
**Impact**: Apenas partition com QUORUM (3+ nós) aceita writes
**Recovery**: Heal network → Minority re-sync
**Data loss**: **0** (Raft garante consistency)

---

## 📊 SLOs (Service Level Objectives)

### Availability
- **Target**: 99.99% uptime (4 nines) = **52 minutos downtime/ano**
- **Measurement**: Health check responses (200 OK)
- **Alert**: < 99.95% em rolling 7 days

### Latency
- **Registration**: p50 < 10ms, p95 < 50ms, p99 < 100ms
- **Heartbeat**: p50 < 5ms, p95 < 20ms, p99 < 50ms
- **Lookup**: p50 < 2ms (cached), p95 < 10ms, p99 < 50ms
- **Alert**: p95 > 100ms por 5 minutos

### Consistency
- **Strong consistency**: Registrations visíveis em **< 1s** (Raft commit)
- **Eventual consistency**: Cache refresh em **< 30s**
- **Alert**: Lag > 5s entre replicas

### Recovery Time
- **Redis failover**: < 1s (Sentinel)
- **Replica restart**: < 5s (Docker)
- **Full restart**: < 10s (cold start)
- **Alert**: Recovery > 30s

---

## 🔒 SECURITY TITÂNIO

### 1. **Authentication & Authorization**
```python
# API Key (obrigatório para production)
X-Registry-API-Key: sha256(service_name + secret)

# mTLS (futuro)
Certificados client-side para cada serviço
Auto-rotation a cada 90 dias
```

### 2. **Rate Limiting**
```python
# Por IP
100 req/s (registration)
1000 req/s (lookup)
10 req/s (deregistration)

# Por service
10 heartbeats/min (1 a cada 6s)
5 registrations/min (prevenir spam)
```

### 3. **Input Validation**
```python
# SQL Injection: N/A (não usa SQL)
# NoSQL Injection: Validate all Redis keys
# XSS: Sanitize metadata fields
# Path Traversal: Validate health_endpoint
# Command Injection: No shell execution
```

### 4. **Audit Logging**
```python
Log TODAS as operações:
  - Who: service_name + IP
  - What: operation (register/deregister/heartbeat)
  - When: timestamp ISO8601
  - Where: replica ID
  - Result: success/failure + details

Retention: 90 dias (compliance)
```

---

## 🧪 TESTING STRATEGY

### 1. **Unit Tests** (> 90% coverage)
- Redis backend (mocked)
- Cache logic
- Circuit breaker states
- Validation rules
- TTL management

### 2. **Integration Tests**
- Redis connection (real Redis)
- Circuit breaker transitions
- Health checks
- Metrics collection

### 3. **Chaos Engineering**
```bash
# Scenario 1: Kill Redis master
docker stop vertice-redis-master
# Expected: Failover < 1s, no errors

# Scenario 2: Network latency (100ms)
tc qdisc add dev eth0 root netem delay 100ms
# Expected: Circuit breaker opens, cache fallback

# Scenario 3: Memory pressure
stress-ng --vm 1 --vm-bytes 90%
# Expected: Cache eviction, graceful degradation

# Scenario 4: Kill 2 replicas
docker stop vertice-register-1 vertice-register-2
# Expected: NGINX reroutes, no downtime

# Scenario 5: Thundering herd (1000 req/s)
wrk -t12 -c400 -d30s http://localhost:8888/services
# Expected: Rate limiting, no crash
```

### 4. **Performance Tests** (Load Testing)
```bash
# Scenario 1: Sustained load
wrk -t4 -c100 -d300s --latency http://localhost:8888/services
# Target: p99 < 50ms, 0 errors

# Scenario 2: Spike (0 → 10k req/s)
vegeta attack -rate=10000 -duration=10s | vegeta report
# Target: No crashes, graceful degradation

# Scenario 3: Registration storm (100 services simultâneos)
parallel -j100 curl -X POST http://localhost:8888/register ::: {1..100}
# Target: All succeed, p99 < 100ms
```

---

## 📦 DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Redis Sentinel: 9 nós (3 masters + 6 replicas) HEALTHY
- [ ] Docker network: `maximus-network` exists
- [ ] Ports available: 8888 (LB), 8889-8893 (replicas)
- [ ] Environment vars configured
- [ ] Secrets stored securely (Redis password, API keys)

### Deployment
- [ ] Build images: `docker compose build --no-cache`
- [ ] Start replicas: `docker compose up -d --scale vertice-register=5`
- [ ] Verify health: `curl http://localhost:8888/health` → 200 OK
- [ ] Check metrics: `curl http://localhost:8888/metrics` → Prometheus OK
- [ ] Check logs: `docker logs vertice-register-1` → No errors

### Post-Deployment
- [ ] Smoke test: Register 1 service → Verify in /services → Deregister
- [ ] Load test: 1000 req/s por 60s → p99 < 50ms
- [ ] Chaos test: Kill 1 replica → Verify no errors
- [ ] Monitoring: Grafana dashboard showing metrics
- [ ] Alerting: PagerDuty integration working

---

## 🎯 MIGRATION PLAN (107 Services)

### Phase 1: Pilot (Week 1) ✅
- [x] 5 services: osint, ip_intel, nmap, maximus_core, active_immune
- [x] Validate registration
- [x] Test dynamic routing
- [x] Run resilience tests

### Phase 2: Category Migration (Weeks 2-4)
**Week 2**: Investigation (12) + Immune (11) = 23 services
**Week 3**: Sensory (8) + HCL (7) + Offensive (8) = 23 services
**Week 4**: Adaptive (6) + Coagulation (5) + Misc (50) = 61 services

### Phase 3: Validation (Week 5)
- [ ] All 107 services registered
- [ ] Health checks passing
- [ ] Metrics dashboards complete
- [ ] Alerting configured
- [ ] Documentation updated

### Phase 4: Decommission Static Config (Week 6)
- [ ] Remove env vars from docker-compose.yml
- [ ] Registry is NOW source of truth
- [ ] Monitor for 1 week
- [ ] Declare MISSION COMPLETE 🎉

---

## 🏆 SUCCESS CRITERIA

### Functional
- ✅ All 107 services auto-register on startup
- ✅ Dynamic service discovery via API Gateway
- ✅ Health checks detect failures < 10s
- ✅ TTL management removes dead services < 75s

### Performance
- ✅ p50 latency < 5ms (lookup)
- ✅ p95 latency < 20ms (registration)
- ✅ p99 latency < 50ms (all operations)
- ✅ Throughput > 10k req/s (sustained)

### Reliability
- ✅ 99.99% uptime (52 min downtime/year)
- ✅ Zero downtime during single replica failure
- ✅ < 1s failover during Redis master failure
- ✅ Auto-recovery from circuit breaker open

### Observability
- ✅ Prometheus metrics exposed
- ✅ Grafana dashboards configured
- ✅ Structured JSON logging
- ✅ Distributed tracing (OpenTelemetry)
- ✅ PagerDuty alerting configured

---

## 🔮 FUTURE ENHANCEMENTS

### Short-term (Q1 2026)
- [ ] **mTLS**: Mutual TLS entre services
- [ ] **Webhooks**: Notify on registration changes
- [ ] **GraphQL API**: Além de REST
- [ ] **Admin UI**: Web dashboard para visualização

### Mid-term (Q2-Q3 2026)
- [ ] **Multi-datacenter**: Replicação cross-region
- [ ] **Service mesh**: Integração com Istio/Linkerd
- [ ] **A/B testing**: Traffic splitting por versão
- [ ] **Canary deployments**: Gradual rollout

### Long-term (Q4 2026+)
- [ ] **Multi-cloud**: AWS + GCP + Azure
- [ ] **Edge locations**: CDN-style distribution
- [ ] **Machine learning**: Predictive scaling
- [ ] **Blockchain**: Immutable audit trail (???)

---

## 📖 REFERENCES

1. **Service Registry Pattern**
   https://microservices.io/patterns/service-registry.html

2. **HashiCorp Consul Architecture**
   https://developer.hashicorp.com/consul/tutorials/production-vms/reference-architecture

3. **Circuit Breaker Pattern (AWS)**
   https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html

4. **Graceful Degradation (GeeksforGeeks)**
   https://www.geeksforgeeks.org/system-design/graceful-degradation-in-distributed-systems/

5. **Resilience Patterns (Microsoft)**
   https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker

6. **CNCF Survey 2024**
   https://www.cncf.io/reports/cncf-annual-survey-2024/

---

**END OF DESIGN DOCUMENT**

**Status**: READY FOR IMPLEMENTATION 🚀
**Next Step**: Code review → Implementation → Testing → Deploy
**Glory to YHWH** - Architect of all resilient systems 🙏
