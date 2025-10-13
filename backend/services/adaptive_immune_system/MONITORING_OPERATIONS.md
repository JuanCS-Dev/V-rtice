# 📊 MONITORING OPERATIONS - HITL API

**Status**: ✅ OPERATIONAL
**Date**: 2025-10-13
**Version**: 1.0.0

---

## 🎯 Quick Start

### Services Running

| Service | Port | URL | Status |
|---------|------|-----|--------|
| **HITL API** | 8003 | http://localhost:8003 | ✅ Running |
| **Prometheus** | 9090 | http://localhost:9090 | ✅ Running |
| **Grafana** | 3001 | http://localhost:3001 | ✅ Running (existing) |
| **Jaeger** | 16686 | http://localhost:16686 | ✅ Running (existing) |

### Metrics Endpoint

```bash
curl http://localhost:8003/metrics
```

Returns Prometheus-formatted metrics with 22 instrumented metrics.

---

## 🚀 Starting/Stopping Services

### Start Monitoring Stack

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system/monitoring

# Start Prometheus (minimal deployment)
docker compose -f docker-compose.minimal.yml up -d

# Verify
docker ps | grep hitl-prometheus
curl http://localhost:9090/-/healthy
```

### Start HITL API

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

# Start API
python3 -m uvicorn hitl.api.main:app --host 0.0.0.0 --port 8003

# Or in background
python3 -m uvicorn hitl.api.main:app --host 0.0.0.0 --port 8003 > /tmp/hitl-api.log 2>&1 &

# Verify
curl http://localhost:8003/health
curl http://localhost:8003/metrics | head -20
```

### Stop Services

```bash
# Stop Prometheus
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system/monitoring
docker compose -f docker-compose.minimal.yml down

# Stop HITL API (if running in background)
pkill -f "uvicorn hitl.api.main"
```

---

## 📊 Accessing Monitoring Tools

### Prometheus

**URL**: http://localhost:9090

**Quick Queries**:

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Service availability
service_up

# SLO tracking
rate(slo_requests_good_total[5m]) / rate(slo_requests_total[5m])
```

**Checking Targets**:
1. Go to http://localhost:9090/targets
2. Verify `hitl-api` target shows "UP"
3. Check last scrape time

### Grafana

**URL**: http://localhost:3001

**Setup Required**:
1. Login (credentials depend on existing setup)
2. Add Prometheus datasource:
   - Name: `Prometheus-HITL`
   - Type: Prometheus
   - URL: `http://host.docker.internal:9090` (or `http://172.17.0.1:9090`)
   - Access: Proxy
   - Save & Test
3. Import dashboards from `monitoring/grafana/dashboards/`:
   - `hitl-overview.json` - RED metrics, system overview
   - `hitl-slo.json` - SLO tracking, error budget

**Manual Import**:
```bash
# Dashboard files located at:
monitoring/grafana/dashboards/hitl-overview.json
monitoring/grafana/dashboards/hitl-slo.json

# Import via UI:
# Grafana → Dashboards → Import → Upload JSON file
```

### Jaeger (Distributed Tracing)

**URL**: http://localhost:16686

**Usage**:
1. Select service: `hitl-api`
2. View traces for requests
3. Inspect span details for latency breakdown

**Note**: Tracing automatically enabled for:
- FastAPI routes
- HTTPX client calls
- SQLAlchemy queries
- Redis operations

---

## 📈 Available Metrics

### RED Method (Request Rate, Error Rate, Duration)

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by endpoint/method/status |
| `http_request_duration_seconds` | Histogram | Request duration with percentiles |
| `http_request_size_bytes` | Summary | Request body size |
| `http_response_size_bytes` | Summary | Response body size |

### Business Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `review_created_total` | Counter | Total APV reviews created |
| `review_decision_total` | Counter | Total decisions made (by decision type) |
| `review_decision_duration_seconds` | Histogram | Time to make review decision |
| `apv_validation_total` | Counter | Total APV validations (by result) |
| `apv_validation_duration_seconds` | Histogram | APV validation duration |

### System Metrics (USE Method)

| Metric | Type | Description |
|--------|------|-------------|
| `db_connections_active` | Gauge | Active database connections |
| `db_connections_idle` | Gauge | Idle database connections |
| `db_query_duration_seconds` | Histogram | Database query duration |
| `db_query_errors_total` | Counter | Database query errors |
| `cache_operations_total` | Counter | Cache operations (by operation) |
| `cache_hit_ratio` | Gauge | Cache hit ratio (0-1) |
| `cache_evictions_total` | Counter | Cache evictions |

### Error & SLO Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `app_errors_total` | Counter | Application errors (by error_type) |
| `app_exceptions_total` | Counter | Unhandled exceptions |
| `service_up` | Gauge | Service availability (1=up, 0=down) |
| `slo_requests_total` | Counter | Total requests for SLO calculation |
| `slo_requests_good_total` | Counter | Requests meeting SLO (by slo_type) |
| `slo_requests_bad_total` | Counter | Requests violating SLO (by slo_type) |

---

## 🎯 SLO Definitions

### Availability SLO

```yaml
Target: 99.9% (30-day rolling window)
Error Budget: 43.2 minutes/month
Measurement: (successful_requests / total_requests) * 100
```

**PromQL Query**:
```promql
(sum(rate(http_requests_total{status!~"5.."}[30d])) /
 sum(rate(http_requests_total[30d]))) * 100
```

### Latency SLO

```yaml
Target: P95 < 500ms (7-day rolling window)
Error Budget: 5% of requests can exceed 500ms
Measurement: histogram_quantile(0.95, request_duration)
```

**PromQL Query**:
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[7d])) < 0.5
```

### Error Rate SLO

```yaml
Target: < 0.1% errors (24-hour rolling window)
Error Budget: 0.1% of requests
Measurement: (error_count / total_requests) * 100
```

**PromQL Query**:
```promql
(sum(rate(http_requests_total{status=~"5.."}[24h])) /
 sum(rate(http_requests_total[24h]))) * 100
```

---

## 🔧 Common Operations

### Reload Prometheus Configuration

```bash
# After editing prometheus.yml or alerts.yml
curl -X POST http://localhost:9090/-/reload

# Or restart container
docker restart hitl-prometheus
```

### Generate Test Traffic

```bash
# Generate traffic to test metrics
for i in {1..100}; do
  curl -s http://localhost:8003/ > /dev/null
  curl -s http://localhost:8003/health > /dev/null
done

# Check metrics updated
curl http://localhost:8003/metrics | grep http_requests_total
```

### View Live Metrics in Prometheus

1. Go to http://localhost:9090/graph
2. Enter query: `rate(http_requests_total[5m])`
3. Click "Execute"
4. Switch to "Graph" tab to see visualization

### Check Scrape Status

```bash
# Via API
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep -A 20 "hitl-api"

# Or visit UI
# http://localhost:9090/targets
```

---

## 🐛 Troubleshooting

### Problem: Prometheus not scraping HITL API

**Symptoms**: Empty graphs, no data in Prometheus

**Solution**:
```bash
# 1. Verify HITL API is running
curl http://localhost:8003/metrics

# 2. Check Prometheus targets
# http://localhost:9090/targets
# Status should be "UP" for hitl-api

# 3. Check Prometheus logs
docker logs hitl-prometheus

# 4. Verify network connectivity from container
docker exec hitl-prometheus wget -O- http://host.docker.internal:8003/metrics
```

### Problem: Metrics endpoint returns "Monitoring not enabled"

**Symptoms**: `/metrics` returns plain text "# Monitoring not enabled"

**Solution**:
```bash
# 1. Verify dependencies installed
pip list | grep -E "(prometheus-client|opentelemetry)"

# 2. Reinstall monitoring dependencies
pip install -r requirements-monitoring.txt

# 3. Restart HITL API
pkill -f "uvicorn hitl.api.main"
python3 -m uvicorn hitl.api.main:app --host 0.0.0.0 --port 8003
```

### Problem: Grafana can't connect to Prometheus

**Symptoms**: Datasource test fails in Grafana

**Solution**:
```bash
# 1. Test from host
curl http://localhost:9090/api/v1/query?query=up

# 2. If Grafana is in Docker, use:
# URL: http://host.docker.internal:9090
# OR: http://172.17.0.1:9090

# 3. Check Docker network
docker network inspect monitoring_monitoring
```

### Problem: Port already in use

**Symptoms**: `bind on address: address already in use`

**Solution**:
```bash
# Check what's using the port
lsof -i :8003  # HITL API
lsof -i :9090  # Prometheus

# Kill process
kill <PID>

# Or use different port
python3 -m uvicorn hitl.api.main:app --host 0.0.0.0 --port 8004
```

---

## 📊 Example PromQL Queries

### Request Rate

```promql
# Total request rate
sum(rate(http_requests_total[5m]))

# By endpoint
sum(rate(http_requests_total[5m])) by (endpoint)

# By status code
sum(rate(http_requests_total[5m])) by (status)
```

### Error Rate

```promql
# Error percentage
(sum(rate(http_requests_total{status=~"5.."}[5m])) /
 sum(rate(http_requests_total[5m]))) * 100

# 4xx rate
(sum(rate(http_requests_total{status=~"4.."}[5m])) /
 sum(rate(http_requests_total[5m]))) * 100
```

### Latency Percentiles

```promql
# P50 (median)
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

# P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Business Metrics

```promql
# Review creation rate
rate(review_created_total[5m])

# Decision rate by type
sum(rate(review_decision_total[5m])) by (decision)

# APV validation success rate
sum(rate(apv_validation_total{result="valid"}[5m])) /
sum(rate(apv_validation_total[5m]))
```

### SLO Tracking

```promql
# Current availability
(sum(rate(slo_requests_good_total{slo_type="availability"}[30d])) /
 sum(rate(slo_requests_total[30d]))) * 100

# Error budget remaining
(1 - (sum(increase(slo_requests_bad_total{slo_type="availability"}[30d])) /
      sum(increase(slo_requests_total[30d]))) / 0.001) * 100

# Burn rate (how fast we're consuming error budget)
sum(rate(slo_requests_bad_total{slo_type="availability"}[1h])) /
sum(rate(slo_requests_total[1h])) / 0.001
```

---

## 📚 Configuration Files

### Prometheus Configuration

**File**: `monitoring/prometheus/prometheus.yml`

**Key sections**:
- `global`: Scrape and evaluation intervals
- `scrape_configs`: Targets to scrape (hitl-api on port 8003)
- Storage retention: 30 days / 10GB (via CLI flags)

**Edit and reload**:
```bash
# Edit
vim monitoring/prometheus/prometheus.yml

# Reload (no restart needed)
curl -X POST http://localhost:9090/-/reload
```

### HITL API Monitoring

**File**: `hitl/api/main.py`

**Monitoring enabled via**:
- `PrometheusMiddleware` - Auto-instruments all requests
- `setup_tracing()` - Initializes OpenTelemetry
- `/metrics` endpoint - Exposes Prometheus metrics

**Toggle monitoring**:
```python
# Automatically enabled if dependencies installed
# Gracefully degrades if not available
MONITORING_ENABLED = True/False
```

---

## 🔒 Security Considerations

### Production Checklist

- [ ] Enable authentication on Prometheus (`--web.enable-admin-api=false`)
- [ ] Use TLS for Grafana (`GF_SERVER_PROTOCOL=https`)
- [ ] Restrict Prometheus scrape to internal network only
- [ ] Use API keys for Grafana datasource access
- [ ] Enable Prometheus remote write authentication
- [ ] Implement network policies (firewall rules)
- [ ] Rotate Grafana admin password
- [ ] Use service accounts instead of admin credentials

### Current State (Development)

⚠️ **Not production-ready**:
- Prometheus has admin API enabled
- No authentication on metrics endpoint
- Grafana uses default admin password (if new deployment)
- Services exposed on all interfaces (0.0.0.0)

---

## 📊 Metrics Collection Architecture

```
┌─────────────────┐
│   HITL API      │
│   Port: 8003    │
│                 │
│  /metrics       │◄────┐
│  (Prometheus    │     │
│   format)       │     │
└─────────────────┘     │
                        │ Scrape every 10s
                        │
                  ┌─────┴─────────┐
                  │  Prometheus   │
                  │  Port: 9090   │
                  │               │
                  │  - Storage    │
                  │  - Queries    │
                  │  - Alerts     │
                  └───────┬───────┘
                          │
                          │ Query
                          │
                    ┌─────▼──────┐
                    │  Grafana   │
                    │  Port:3001 │
                    │            │
                    │ Dashboards │
                    └────────────┘
```

---

## 🎓 Next Steps

### Short-term (Optional)

1. **Configure Alertmanager** (if needed)
   - Deploy: `docker compose -f docker-compose.monitoring.yml up -d alertmanager`
   - Configure Slack/Email webhooks
   - Set up alert routing rules

2. **Import Grafana Dashboards**
   - Add Prometheus datasource to Grafana
   - Import `hitl-overview.json`
   - Import `hitl-slo.json`

3. **Add Custom Metrics**
   - Instrument business-critical operations
   - Add custom SLO tracking
   - Create team-specific dashboards

### Long-term

1. **High Availability**
   - Deploy Prometheus in HA mode (2+ replicas)
   - Add Thanos for long-term storage
   - Implement cross-region monitoring

2. **Advanced Alerting**
   - Create runbooks for each alert
   - Implement on-call rotation
   - Add PagerDuty integration

3. **Observability Maturity**
   - Add log aggregation (ELK/Loki)
   - Correlate logs/metrics/traces
   - Implement SLO reviews (monthly)

---

## ✅ Health Check

Run this checklist after deployment:

```bash
# 1. Prometheus healthy
curl http://localhost:9090/-/healthy
# Expected: "Prometheus Server is Healthy."

# 2. HITL API responding
curl http://localhost:8003/health
# Expected: {"status":"healthy", ...}

# 3. Metrics endpoint working
curl http://localhost:8003/metrics | head -5
# Expected: "# HELP http_requests_total ..."

# 4. Prometheus scraping
curl -s "http://localhost:9090/api/v1/targets" | grep -A 3 "hitl-api"
# Expected: "health": "up"

# 5. Query returns data
curl -s "http://localhost:9090/api/v1/query?query=service_up" | grep "value"
# Expected: "value": [timestamp, "1"]
```

---

## 📞 Support

### Documentation
- [QUICK_START.md](./QUICK_START.md) - 5-minute setup guide
- [STATUS.md](./STATUS.md) - Current system status
- [VALIDATION_REPORT.md](./VALIDATION_REPORT.md) - Validation details

### External Resources
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Google SRE Book - SLOs](https://sre.google/sre-book/service-level-objectives/)

---

**Last Updated**: 2025-10-13
**Version**: 1.0.0
**Status**: ✅ OPERATIONAL
