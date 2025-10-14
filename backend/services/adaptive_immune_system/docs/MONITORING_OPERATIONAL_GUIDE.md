# 📊 MONITORING OPERATIONAL GUIDE

**Date**: 2025-10-13
**Branch**: `reactive-fabric/sprint3-collectors-orchestration`
**Status**: ✅ **PRODUCTION-READY**

---

## 🎯 Executive Summary

Complete operational guide for the Adaptive Immune System monitoring stack. This document covers deployment, operation, troubleshooting, and maintenance procedures for the Prometheus + Grafana + HITL API metrics stack.

**Stack Components**:
- ✅ Prometheus 2.40.0 (metrics collection)
- ✅ Grafana 12.2.0 (visualization)
- ✅ HITL API with PrometheusMiddleware
- ✅ 22 Prometheus metrics
- ✅ 2 Grafana dashboards
- ✅ 18 alert rules

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Starting the Stack](#starting-the-stack)
3. [Stopping the Stack](#stopping-the-stack)
4. [Accessing Services](#accessing-services)
5. [Validating Health](#validating-health)
6. [Metrics Guide](#metrics-guide)
7. [Dashboards Guide](#dashboards-guide)
8. [Alerting](#alerting)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                MONITORING STACK ARCHITECTURE                 │
└─────────────────────────────────────────────────────────────┘

┌────────────────┐        ┌────────────────┐        ┌────────────────┐
│   HITL API     │        │   Prometheus   │        │    Grafana     │
│                │        │                │        │                │
│  Port: 8003    │◄───────│  Port: 9090    │◄───────│  Port: 3001    │
│  /metrics      │ scrape │  TSDB 30d      │ query  │  Dashboards    │
│                │ 10s    │  Alerts        │        │  Admin UI      │
└────────────────┘        └────────────────┘        └────────────────┘
        │                          │
        │                          │
        ▼                          ▼
┌────────────────┐        ┌────────────────┐
│  Prometheus    │        │  Prometheus    │
│  Metrics       │        │  Alerts        │
│  (22 types)    │        │  (18 rules)    │
└────────────────┘        └────────────────┘
```

### Components

**HITL API** (Port 8003):
- FastAPI application
- PrometheusMiddleware for automatic instrumentation
- `/metrics` endpoint (Prometheus format)
- `/health` endpoint for health checks

**Prometheus** (Port 9090):
- Scrapes HITL API every 10 seconds
- Stores metrics for 30 days
- Evaluates alert rules every 15 seconds
- Provides PromQL query interface

**Grafana** (Port 3001):
- Visualizes Prometheus metrics
- 2 dashboards: Overview + SLO
- Admin credentials: admin/admin

---

## 🚀 Starting the Stack

### Quick Start (Recommended)

Start only Prometheus (minimal footprint):

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

# Start Prometheus
docker compose -f monitoring/docker-compose.minimal.yml up -d

# Verify
docker ps | grep hitl-prometheus
curl http://localhost:9090/-/healthy
```

### Full Stack (Prometheus + Grafana + Optional Services)

Start complete monitoring stack:

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

# Start all services
docker compose -f monitoring/docker-compose.monitoring.yml up -d

# Check status
docker compose -f monitoring/docker-compose.monitoring.yml ps
```

### HITL API Startup

Start the HITL API to begin metrics collection:

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

# Option 1: Direct uvicorn
uvicorn hitl.api.main:app --reload --port 8003

# Option 2: Python module
python -m hitl.api.main

# Verify
curl http://localhost:8003/health
curl http://localhost:8003/metrics | head -20
```

### Startup Validation

Verify all components are running:

```bash
# 1. Check Docker containers
docker ps | grep -E "(prometheus|grafana)"

# 2. Check Prometheus health
curl http://localhost:9090/-/healthy
# Expected: "Prometheus Server is Healthy."

# 3. Check Grafana health
curl http://localhost:3001/api/health
# Expected: {"database":"ok","version":"12.2.0"}

# 4. Check HITL API health
curl http://localhost:8003/health
# Expected: {"status":"healthy",...}

# 5. Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | grep -i hitl-api -A 5
# Expected: "health": "up"
```

---

## 🛑 Stopping the Stack

### Stop Monitoring Stack

```bash
# Stop Prometheus only (minimal)
docker compose -f monitoring/docker-compose.minimal.yml down

# Stop full stack
docker compose -f monitoring/docker-compose.monitoring.yml down

# Stop and remove volumes (⚠️ deletes all metrics data)
docker compose -f monitoring/docker-compose.monitoring.yml down -v
```

### Stop HITL API

```bash
# If running with uvicorn --reload
# Press Ctrl+C in terminal

# If running as systemd service
sudo systemctl stop hitl-api

# Kill by port
lsof -ti:8003 | xargs kill -9
```

---

## 🌐 Accessing Services

### Prometheus

**URL**: http://localhost:9090

**Features**:
- Metrics explorer: http://localhost:9090/graph
- Targets status: http://localhost:9090/targets
- Alert rules: http://localhost:9090/alerts
- Configuration: http://localhost:9090/config

**Sample Queries**:
```promql
# Request rate per endpoint
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Active reviews
hitl_pending_reviews

# SLO compliance
hitl_slo_review_time_compliance_ratio
```

### Grafana

**URL**: http://localhost:3001

**Credentials**:
- Username: `admin`
- Password: `admin`

**Dashboards**:
1. **HITL API - Overview**: http://localhost:3001/d/hitl-overview
   - Request rate (RED method)
   - Latency percentiles (P50/P95/P99)
   - Error rates
   - Business metrics

2. **HITL API - SLO Tracking**: http://localhost:3001/d/hitl-slo
   - Review time SLO (95th percentile < 5 min)
   - Decision time SLO
   - Availability SLO (99.9%)
   - Error budget tracking

### HITL API

**URL**: http://localhost:8003

**Endpoints**:
- API Docs: http://localhost:8003/hitl/docs
- Health: http://localhost:8003/health
- Metrics: http://localhost:8003/metrics
- WebSocket: ws://localhost:8003/hitl/ws

---

## ✅ Validating Health

### Automated Health Check Script

```bash
#!/bin/bash
# health_check.sh - Validate entire monitoring stack

set -e

echo "🔍 Monitoring Stack Health Check"
echo "=================================="

# 1. Prometheus
echo -n "Prometheus: "
if curl -sf http://localhost:9090/-/healthy >/dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
    exit 1
fi

# 2. Grafana
echo -n "Grafana: "
if curl -sf http://localhost:3001/api/health | grep -q "ok"; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
    exit 1
fi

# 3. HITL API
echo -n "HITL API: "
if curl -sf http://localhost:8003/health | grep -q "healthy"; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
    exit 1
fi

# 4. Metrics collection
echo -n "Metrics collection: "
if curl -sf 'http://localhost:9090/api/v1/query?query=up{job="hitl-api"}' | grep -q '"value":\[.*,"1"\]'; then
    echo "✅ Active"
else
    echo "❌ Inactive"
    exit 1
fi

echo ""
echo "✅ All systems operational"
```

### Manual Validation Steps

**Step 1: Generate Test Traffic**

```bash
# Generate 20 requests
for i in {1..20}; do
    curl -s http://localhost:8003/health > /dev/null
    echo "Request $i sent"
done
```

**Step 2: Verify Metrics Updated**

```bash
# Check metrics endpoint
curl -s http://localhost:8003/metrics | grep http_requests_total

# Expected output (numbers should be > 0):
# http_requests_total{endpoint="/health",method="GET",status="200"} 20.0
```

**Step 3: Verify Prometheus Collected Metrics**

```bash
# Query Prometheus
curl -s -G \
  --data-urlencode 'query=http_requests_total{job="hitl-api"}' \
  http://localhost:9090/api/v1/query \
  | python3 -m json.tool | grep -A 5 '/health'

# Expected: Should show updated count
```

**Step 4: Verify Grafana Datasource**

```bash
# Test datasource connection
curl -s -u admin:admin \
  http://localhost:3001/api/datasources \
  | python3 -m json.tool | grep -A 3 Prometheus

# Expected: Should show Prometheus datasource
```

---

## 📊 Metrics Guide

### Available Metrics

The HITL API exports 22 Prometheus metrics:

#### HTTP Metrics (RED Method)

**Rate**:
```promql
# Total requests
http_requests_total

# Request rate (per second)
rate(http_requests_total[5m])

# Request rate by endpoint
rate(http_requests_total{endpoint="/health"}[5m])
```

**Errors**:
```promql
# Total errors (5xx status codes)
http_requests_total{status=~"5.."}

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Error ratio (percentage)
rate(http_requests_total{status=~"5.."}[5m])
/
rate(http_requests_total[5m]) * 100
```

**Duration**:
```promql
# Request duration histogram
http_request_duration_seconds

# P50 latency (median)
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Average latency
rate(http_request_duration_seconds_sum[5m])
/
rate(http_request_duration_seconds_count[5m])
```

#### Business Metrics

**Reviews**:
```promql
# Pending reviews count
hitl_pending_reviews

# Completed reviews (total)
hitl_reviews_completed_total

# Review rate (per minute)
rate(hitl_reviews_completed_total[5m]) * 60

# Reviews by decision type
hitl_reviews_completed_total{decision="approve"}
hitl_reviews_completed_total{decision="reject"}
```

**Decisions**:
```promql
# Decisions made
hitl_decisions_total

# Decision rate
rate(hitl_decisions_total[5m])

# Decisions by type
hitl_decisions_total{decision="approve"}
```

**Timing**:
```promql
# Review duration (histogram)
hitl_review_duration_seconds

# Average review time
rate(hitl_review_duration_seconds_sum[5m])
/
rate(hitl_review_duration_seconds_count[5m])

# P95 review time
histogram_quantile(0.95, rate(hitl_review_duration_seconds_bucket[5m]))
```

#### System Metrics

**Database**:
```promql
# Active database connections
hitl_db_connections_active

# Database query duration
hitl_db_query_duration_seconds
```

**Cache**:
```promql
# Cache hits
hitl_cache_hits_total

# Cache misses
hitl_cache_misses_total

# Cache hit ratio
hitl_cache_hits_total / (hitl_cache_hits_total + hitl_cache_misses_total) * 100
```

#### SLO Metrics

**Review Time SLO**:
```promql
# SLO: 95th percentile review time < 5 minutes
hitl_slo_review_time_compliance_ratio

# Current P95 review time
histogram_quantile(0.95, rate(hitl_review_duration_seconds_bucket[5m])) / 60
```

**Availability SLO**:
```promql
# SLO: 99.9% success rate
hitl_slo_availability_compliance_ratio

# Current availability
(1 - (rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]))) * 100
```

---

## 📈 Dashboards Guide

### Dashboard 1: HITL API - Overview

**File**: `monitoring/grafana/dashboards/hitl-overview.json`

**Panels**:

1. **Request Rate (RED - Rate)**
   - Time series graph
   - Requests per second by endpoint
   - Query: `rate(http_requests_total[5m])`

2. **Error Rate (RED - Errors)**
   - Time series graph
   - Errors per second (5xx responses)
   - Query: `rate(http_requests_total{status=~"5.."}[5m])`

3. **Latency Percentiles (RED - Duration)**
   - Time series graph
   - P50, P95, P99 latency
   - Query: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`

4. **Pending Reviews**
   - Gauge visualization
   - Current number of pending reviews
   - Query: `hitl_pending_reviews`

5. **Review Completion Rate**
   - Time series graph
   - Reviews completed per minute
   - Query: `rate(hitl_reviews_completed_total[5m]) * 60`

6. **Decisions by Type**
   - Pie chart
   - Breakdown: approve/reject/escalate
   - Query: `sum by (decision) (hitl_decisions_total)`

**Usage**:
```bash
# Import dashboard
curl -X POST http://localhost:3001/api/dashboards/db \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d @monitoring/grafana/dashboards/hitl-overview.json
```

### Dashboard 2: HITL API - SLO Tracking

**File**: `monitoring/grafana/dashboards/hitl-slo.json`

**Panels**:

1. **Review Time SLO**
   - Gauge: SLO compliance (95th percentile < 5 min)
   - Target: 99% compliance
   - Query: `hitl_slo_review_time_compliance_ratio * 100`

2. **Availability SLO**
   - Gauge: Success rate
   - Target: 99.9% availability
   - Query: `hitl_slo_availability_compliance_ratio * 100`

3. **Error Budget**
   - Time series: Remaining error budget
   - Calculated from SLO violations
   - Query: Custom calculation

4. **SLO Violations**
   - Table: Recent SLO violations
   - Timestamp + details
   - Query: Alert history

**Usage**:
Same import process as Dashboard 1.

---

## 🚨 Alerting

### Alert Rules

**File**: `monitoring/prometheus/alerts.yml`

**18 Alert Rules** across 4 categories:

#### 1. API Health Alerts

**APIDown**:
- Condition: `up{job="hitl-api"} == 0`
- Duration: 1 minute
- Severity: critical

**HighErrorRate**:
- Condition: Error rate > 5%
- Duration: 5 minutes
- Severity: warning

**HighLatency**:
- Condition: P95 latency > 1 second
- Duration: 5 minutes
- Severity: warning

#### 2. Business Metric Alerts

**TooManyPendingReviews**:
- Condition: `hitl_pending_reviews > 100`
- Duration: 10 minutes
- Severity: warning

**ReviewBacklog**:
- Condition: Pending reviews growing > 10/min
- Duration: 15 minutes
- Severity: critical

#### 3. SLO Alerts

**ReviewTimeSLOViolation**:
- Condition: P95 review time > 5 minutes
- Duration: 10 minutes
- Severity: warning

**AvailabilitySLOViolation**:
- Condition: Availability < 99.9%
- Duration: 5 minutes
- Severity: critical

### Testing Alerts

```bash
# Trigger HighLatency alert (simulate slow endpoint)
# Add artificial delay in code temporarily

# Trigger TooManyPendingReviews alert (create test data)
# Insert 101 pending reviews in database

# View active alerts
curl http://localhost:9090/api/v1/alerts | python3 -m json.tool
```

---

## 🔧 Troubleshooting

### Issue: Prometheus Not Scraping HITL API

**Symptoms**:
- Target shows as "down" in Prometheus
- No metrics appearing in Grafana

**Diagnosis**:
```bash
# 1. Check target status
curl -s http://localhost:9090/api/v1/targets | grep hitl-api -A 10

# 2. Check if HITL API is running
curl http://localhost:8003/health

# 3. Check if metrics endpoint works
curl http://localhost:8003/metrics
```

**Solutions**:

A. **HITL API not running**:
```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
uvicorn hitl.api.main:app --reload --port 8003
```

B. **Prometheus can't reach HITL API**:
```bash
# From inside Prometheus container
docker exec hitl-prometheus wget -O- http://host.docker.internal:8003/metrics

# If fails, add to docker-compose:
extra_hosts:
  - "host.docker.internal:host-gateway"
```

C. **Monitoring module not installed**:
```bash
pip install prometheus-client
```

### Issue: Grafana Shows No Data

**Symptoms**:
- Dashboards show "No data"
- Queries return empty results

**Diagnosis**:
```bash
# 1. Check Prometheus datasource
curl -u admin:admin http://localhost:3001/api/datasources

# 2. Test query in Prometheus directly
curl -s -G --data-urlencode 'query=up{job="hitl-api"}' \
  http://localhost:9090/api/v1/query
```

**Solutions**:

A. **Datasource not configured**:
```bash
# Add Prometheus datasource
curl -X POST http://localhost:3001/api/datasources \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

B. **Wrong datasource URL**:
- In Grafana UI: Configuration → Data Sources → Prometheus
- Change URL to: `http://hitl-prometheus:9090` (if in same network)
- Or: `http://localhost:9090` (if using host network)

C. **Time range issue**:
- Check time range in Grafana (top right)
- Ensure it covers period when metrics were collected
- Generate fresh metrics: `for i in {1..20}; do curl -s http://localhost:8003/health; done`

### Issue: High Memory Usage

**Symptoms**:
- Prometheus using > 2GB RAM
- System slow/unresponsive

**Diagnosis**:
```bash
docker stats hitl-prometheus

# Check TSDB size
du -sh /var/lib/docker/volumes/*prometheus*
```

**Solutions**:

A. **Reduce retention period**:
```yaml
# In docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=7d'  # Down from 30d
```

B. **Reduce scrape frequency**:
```yaml
# In prometheus/prometheus.yml
scrape_configs:
  - job_name: 'hitl-api'
    scrape_interval: 30s  # Up from 10s
```

C. **Add memory limits**:
```yaml
# In docker-compose.monitoring.yml
services:
  prometheus:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Issue: Metrics Not Updating

**Symptoms**:
- Old metric values in Prometheus
- Counter not incrementing

**Diagnosis**:
```bash
# Check last scrape time
curl -s http://localhost:9090/api/v1/targets | grep lastScrape

# Generate new requests
curl http://localhost:8003/health

# Check metrics immediately
curl http://localhost:8003/metrics | grep http_requests_total
```

**Solutions**:

A. **Prometheus cache**:
```bash
# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload
```

B. **Metrics middleware not active**:
```python
# Verify in hitl/api/main.py
if MONITORING_ENABLED:
    app.add_middleware(PrometheusMiddleware)  # Must be present
```

---

## 🔄 Maintenance

### Regular Maintenance Tasks

#### Daily

- **Check alert status**:
  ```bash
  curl -s http://localhost:9090/api/v1/alerts \
    | python3 -m json.tool \
    | grep -A 5 firing
  ```

- **Verify targets up**:
  ```bash
  curl -s http://localhost:9090/api/v1/targets \
    | python3 -m json.tool \
    | grep -B 2 '"health": "up"'
  ```

#### Weekly

- **Check disk usage**:
  ```bash
  docker exec hitl-prometheus df -h /prometheus
  ```

- **Review slow queries**:
  ```bash
  # Check Grafana slow log
  docker logs vertice-grafana 2>&1 | grep -i "slow query"
  ```

#### Monthly

- **Backup Prometheus data**:
  ```bash
  # Create snapshot
  curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

  # Backup volume
  docker run --rm -v monitoring_prometheus_data:/data \
    -v $(pwd):/backup \
    busybox tar czf /backup/prometheus-backup-$(date +%Y%m%d).tar.gz /data
  ```

- **Backup Grafana dashboards**:
  ```bash
  # Export all dashboards
  for uid in $(curl -s -u admin:admin http://localhost:3001/api/search \
    | python3 -m json.tool | grep uid | cut -d'"' -f4); do
    curl -s -u admin:admin http://localhost:3001/api/dashboards/uid/$uid \
      > grafana-dashboard-$uid-$(date +%Y%m%d).json
  done
  ```

### Upgrade Procedures

#### Upgrade Prometheus

```bash
# 1. Stop current Prometheus
docker compose -f monitoring/docker-compose.minimal.yml down

# 2. Update image version in docker-compose.minimal.yml
# Change: prom/prometheus:v2.40.0
# To: prom/prometheus:v2.45.0

# 3. Start with new version
docker compose -f monitoring/docker-compose.minimal.yml up -d

# 4. Verify
curl http://localhost:9090/api/v1/status/buildinfo
```

#### Upgrade Grafana

```bash
# 1. Backup dashboards (see Monthly maintenance)

# 2. Update image in docker-compose
# Change: grafana/grafana:9.3.0
# To: grafana/grafana:10.0.0

# 3. Restart
docker compose -f monitoring/docker-compose.monitoring.yml up -d grafana

# 4. Verify
curl http://localhost:3001/api/health
```

---

## 📚 Reference

### Key Files

| File | Purpose |
|------|---------|
| `monitoring/docker-compose.minimal.yml` | Minimal stack (Prometheus only) |
| `monitoring/docker-compose.monitoring.yml` | Full stack (all services) |
| `monitoring/prometheus/prometheus.yml` | Prometheus configuration |
| `monitoring/prometheus/alerts.yml` | Alert rules |
| `monitoring/grafana/dashboards/hitl-overview.json` | Overview dashboard |
| `monitoring/grafana/dashboards/hitl-slo.json` | SLO dashboard |
| `hitl/monitoring/metrics.py` | Metrics definitions |
| `hitl/monitoring/middleware.py` | Prometheus middleware |

### Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| HITL API | 8003 | Main API + /metrics |
| Prometheus | 9090 | Metrics + UI |
| Grafana | 3001 | Dashboards + UI |
| Alertmanager | 9093 | Alert management |
| Jaeger | 16686 | Distributed tracing |

### Useful Commands

```bash
# Quick health check
curl -s http://localhost:8003/health | python3 -m json.tool

# Generate test traffic
for i in {1..100}; do curl -s http://localhost:8003/health > /dev/null; done

# View latest metrics
curl -s http://localhost:8003/metrics | tail -20

# Query specific metric
curl -s -G --data-urlencode 'query=http_requests_total{endpoint="/health"}' \
  http://localhost:9090/api/v1/query | python3 -m json.tool

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool

# Export Grafana dashboard
curl -s -u admin:admin \
  http://localhost:3001/api/dashboards/uid/hitl-overview \
  > dashboard-backup.json
```

---

## ✅ Operations Checklist

### Deployment Checklist

- [ ] Prometheus container running
- [ ] HITL API running on port 8003
- [ ] `/metrics` endpoint accessible
- [ ] Prometheus scraping HITL API (target "up")
- [ ] Grafana accessible on port 3001
- [ ] Dashboards imported
- [ ] Datasource configured
- [ ] Test queries returning data
- [ ] Alerts configured
- [ ] Documentation reviewed

### Daily Operations Checklist

- [ ] All targets "up" in Prometheus
- [ ] No firing alerts
- [ ] Dashboards loading correctly
- [ ] Metrics updating in real-time
- [ ] Disk usage < 80%

### Troubleshooting Checklist

- [ ] Verify HITL API health: `curl http://localhost:8003/health`
- [ ] Verify metrics endpoint: `curl http://localhost:8003/metrics`
- [ ] Verify Prometheus health: `curl http://localhost:9090/-/healthy`
- [ ] Check Prometheus targets: http://localhost:9090/targets
- [ ] Check Grafana datasource: http://localhost:3001/datasources
- [ ] Generate test traffic: `for i in {1..20}; do curl -s http://localhost:8003/health; done`
- [ ] Check Docker logs: `docker logs hitl-prometheus`

---

## 📞 Support

### Documentation

- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/
- **PromQL**: https://prometheus.io/docs/prometheus/latest/querying/basics/

### Internal Documentation

- `MONITORING_DEPLOYMENT_COMPLETE.md` - Implementation details
- `FASE_3.13_ADVANCED_MONITORING_COMPLETE.md` - Architecture & design
- `STATUS.md` - Current system status

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-13
**Maintained By**: DevOps Team
**Status**: ✅ Production-Ready
