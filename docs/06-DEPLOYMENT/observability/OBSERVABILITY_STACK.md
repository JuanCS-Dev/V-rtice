# Observability Stack Documentation

## Overview

Complete observability stack for Vértice MAXIMUS backend ecosystem with metrics, logs, traces, and alerting.

## Stack Components

### Prometheus (Metrics)
**Endpoint:** http://localhost:9090  
**Purpose:** Time-series metrics collection and alerting

**Scrape Targets:**
- All 83 backend services (organized by category)
- Infrastructure exporters (postgres, redis, node, cadvisor)
- Self-monitoring (prometheus, grafana, loki)

**Configuration:** `/monitoring/prometheus/prometheus.yml`
- Scrape interval: 15s (default), 10s (services)
- Retention: 30 days
- Alert evaluation: 15s

**Alert Rules:** `/monitoring/prometheus/rules/vertice_alerts.yml`
- Service health monitoring
- Resource usage thresholds
- MAXIMUS-specific alerts
- Immune system monitoring
- Database and cache alerts

---

### Grafana (Visualization)
**Endpoint:** http://localhost:3001  
**Credentials:** admin / vertice_admin (configurable via env)

**Data Sources (auto-provisioned):**
- Prometheus (metrics)
- Loki (logs)
- Jaeger (traces)

**Dashboards Location:** `/monitoring/grafana/dashboards/`

---

### Loki (Logs)
**Endpoint:** http://localhost:3100  
**Purpose:** Log aggregation and querying

**Storage:**
- Engine: BoltDB + Filesystem
- Retention: 7 days (168h)
- Ingestion rate: 16MB/s (burst: 32MB/s)

**Configuration:** `/monitoring/loki/loki-config.yml`

---

### Promtail (Log Shipper)
**Purpose:** Collects logs from Docker containers and ships to Loki

**Scrape Configs:**
- System logs: `/var/log/*log`
- Docker containers (auto-discovery via Docker socket)

**Label Extraction:**
- `container`: Container name
- `service`: From `vertice.service` label
- `category`: From `vertice.category` label
- `stream`: stdout/stderr

**Configuration:** `/monitoring/promtail/promtail-config.yml`

---

### Jaeger (Distributed Tracing)
**UI:** http://localhost:16686  
**Collector:** OTLP-enabled (gRPC: 4317, HTTP: 4318)

**Storage:** Badger (persistent)

**Endpoints:**
- UI: 16686
- Collector HTTP: 14268
- Collector gRPC: 14250
- OTLP gRPC: 4317
- OTLP HTTP: 4318

---

### Alertmanager
**Endpoint:** http://localhost:9093  
**Purpose:** Alert routing and notification

**Receivers:**
- `vertice-default`: Webhook to MAXIMUS Core (8100)
- `vertice-critical`: Critical alerts to MAXIMUS
- `vertice-maximus`: MAXIMUS-specific alerts
- `vertice-immune`: Immune system alerts to Active Immune Core (8200)

**Routing Logic:**
- Group by: alertname, cluster, service
- Group wait: 10s
- Repeat interval: 12h
- Inhibition: Critical alerts suppress warnings

**Configuration:** `/monitoring/alertmanager/alertmanager.yml`

---

## Exporters

### Postgres Exporter
**Port:** 9187  
**Metrics:** Connection pool, query performance, replication lag

### Redis Exporter
**Port:** 9121  
**Metrics:** Memory usage, connections, command stats

### Node Exporter
**Port:** 9100  
**Metrics:** CPU, memory, disk, network (host-level)

### cAdvisor
**Port:** 8080  
**Metrics:** Container resource usage (per-container CPU, memory, network)

---

## Alert Rules

### Service Health
- `ServiceDown`: Service unavailable >2min → Critical
- `HighErrorRate`: HTTP 5xx >5% for 5min → Warning
- `HighLatency`: p95 latency >1s for 5min → Warning

### Resource Usage
- `HighMemoryUsage`: Container memory >90% for 5min → Warning
- `HighCPUUsage`: Container CPU >80% for 5min → Warning

### MAXIMUS Core
- `MaximusConsciousnessLow`: Consciousness <0.5 for 2min → Critical
- `EthicalGuardianViolation`: Any violation in 5min → Critical

### Immune System
- `ImmuneResponseFailed`: Failure rate >0.1/s for 3min → Critical
- `ThreatDetectionBacklog`: Queue >1000 for 5min → Warning

### Wargaming
- `WargamingFailureRatioHigh`: Failure ratio >10% for 10min → Warning

### Database
- `PostgresConnectionPoolExhausted`: Connections >80% for 5min → Warning
- `PostgresReplicationLag`: Lag >10s for 5min → Critical

### Cache
- `RedisMemoryHigh`: Memory >90% for 5min → Warning
- `RedisConnectionsHigh`: Connections >1000 for 5min → Warning

---

## Usage

### Start Observability Stack
```bash
docker compose -f docker-compose.observability.yml up -d
```

### Verify Services
```bash
# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3001/api/health

# Loki
curl http://localhost:3100/ready

# Jaeger
curl http://localhost:16686

# Alertmanager
curl http://localhost:9093/-/healthy
```

### Query Examples

#### Prometheus (PromQL)
```promql
# Request rate per service
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Memory usage by category
sum(container_memory_usage_bytes) by (category)

# MAXIMUS consciousness level
maximus_consciousness_level

# Immune system response time
histogram_quantile(0.95, rate(immune_response_duration_seconds_bucket[5m]))
```

#### Loki (LogQL)
```logql
# All logs from maximus category
{category="maximus"}

# Errors from specific service
{service="maximus_core_service"} |= "ERROR"

# HTTP 500 errors
{category=~"maximus|immune"} | json | status="500"

# Log rate by service
rate({job="docker"}[5m]) by (service)
```

---

## Integration with Services

### Metrics Endpoint (Required)
All services MUST expose `/metrics` endpoint in Prometheus format:

```python
from prometheus_client import Counter, Histogram, generate_latest

http_requests = Counter('http_requests_total', 'HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Structured Logging (Required)
All services MUST emit structured logs (JSON):

```python
import structlog

logger = structlog.get_logger()
logger.info("request_processed", method="POST", path="/api/v1/analyze", duration_ms=150, status=200)
```

### Tracing (Required)
All services MUST instrument with OpenTelemetry:

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
```

---

## Maintenance

### Data Retention
- Prometheus: 30 days (configurable)
- Loki: 7 days (168h)
- Jaeger: No automatic retention (manual cleanup required)

### Storage Volumes
```bash
# Check volume usage
docker volume ls | grep vertice

# Inspect volume
docker volume inspect vertice_prometheus_data

# Backup volume
docker run --rm -v vertice_prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz -C /data .
```

### Troubleshooting
```bash
# Check service logs
docker logs vertice-prometheus
docker logs vertice-grafana
docker logs vertice-loki

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Test alert rules
curl http://localhost:9090/api/v1/rules | jq

# Check Loki ingestion
curl http://localhost:3100/metrics | grep loki_ingester
```

---

## Security

### Network Isolation
All observability services run on `vertice-network` (isolated from public internet).

### Authentication
- Grafana: Basic auth (change default password via env)
- Prometheus: No auth (internal only)
- Loki: No auth (internal only)
- Jaeger: No auth (internal only)

**Production:** Add reverse proxy with TLS + authentication.

---

## Performance Optimization

### Prometheus
- Query timeout: 60s
- HTTP method: POST (better for large queries)
- Time interval: 15s (balance between granularity and load)

### Loki
- Ingestion rate: 16MB/s (adjust based on log volume)
- Max entries per query: 5000 (prevent UI timeouts)
- Chunk cache: 24h

### Jaeger
- Storage: Badger (high-performance embedded DB)
- OTLP enabled (modern protocol)

---

## Compliance with Constituição Vértice

### Article IV (Antifragilidade)
- Continuous health monitoring of all services
- Proactive alerting before failures
- Wargaming test monitoring

### Article II (Padrão Pagani)
- Production-ready configurations (no mocks)
- Complete integration with all 83 services
- Validated alert rules

### Article III (Zero Trust)
- All metrics require authentication in production
- Alert webhooks to trusted services only
- Network isolation enforced

---

## References

- Prometheus: https://prometheus.io/docs
- Grafana: https://grafana.com/docs
- Loki: https://grafana.com/docs/loki
- Jaeger: https://www.jaegertracing.io/docs
- OpenTelemetry: https://opentelemetry.io/docs

---

**Version:** 1.0  
**Last Updated:** 2025-10-16  
**Status:** Days 9-14 Implementation Complete
