# Vértice MAXIMUS - Grafana Dashboards

## Overview

Production-ready dashboards for comprehensive monitoring of the Vértice MAXIMUS ecosystem.

## Dashboards

### 1. Services Overview (`01-services-overview.json`)
**Purpose:** High-level system health and performance metrics

**Panels:**
- Services Up by Category (timeseries)
- Total Services Online (gauge)
- Request Rate by Service (timeseries)
- Error Rate by Service (timeseries with 5% threshold)
- P95 Latency by Service (timeseries with 1s threshold)

**Refresh:** 30s  
**Time Range:** Last 6 hours

---

### 2. MAXIMUS Core (`02-maximus-core.json`)
**Purpose:** MAXIMUS consciousness and decision-making metrics

**Panels:**
- Consciousness Level (gauge, thresholds: <0.3 red, 0.3-0.7 yellow, >0.7 green)
- Ethical Violations (stat, background color based on count)
- MAXIMUS Services Health (timeseries)
- Decision Rate by Type (timeseries with mean calc)
- Decision Latency (timeseries with P95 calc)

**Metrics:**
- `maximus_consciousness_level`
- `ethical_violations_total`
- `maximus_decisions_total`
- `maximus_decision_duration_seconds_bucket`

**Refresh:** 30s  
**Time Range:** Last 6 hours

---

### 3. Immune System (`03-immune-system.json`)
**Purpose:** Immune system health and threat response metrics

**Panels:**
- Active Immune Cells (gauge, thresholds: <10 red, 10-13 yellow, >13 green)
- Immune Response Rate (timeseries by response_type)
- Threat Detection Queue (gauge with 0-1000 range)
- Response Failures (stat, last 5 minutes)
- Response Latency (timeseries P95)

**Metrics:**
- `immune_response_total`
- `immune_response_failures_total`
- `threat_detection_queue_size`
- `immune_response_duration_seconds_bucket`

**Refresh:** 30s  
**Time Range:** Last 6 hours

---

### 4. Infrastructure (`04-infrastructure.json`)
**Purpose:** Container and infrastructure resource metrics

**Panels:**
- CPU Usage by Container (timeseries with 80% threshold)
- Memory Usage by Container (timeseries with 90% threshold)
- PostgreSQL Active Connections (stat)
- Redis Connected Clients (stat)
- Network I/O by Container (timeseries RX/TX)

**Metrics:**
- `container_cpu_usage_seconds_total`
- `container_memory_usage_bytes`
- `pg_stat_database_numbackends`
- `redis_connected_clients`
- `container_network_receive_bytes_total`
- `container_network_transmit_bytes_total`

**Refresh:** 30s  
**Time Range:** Last 6 hours

---

### 5. Wargaming (`05-wargaming.json`)
**Purpose:** Antifragilidade testing and validation metrics

**Panels:**
- Total Wargaming Tests (stat)
- Success Rate (gauge, thresholds: <85% red, 85-95% yellow, >95% green)
- Failures Last Hour (stat)
- Test Rate by Type (timeseries)
- Test Execution Time (timeseries P95)

**Metrics:**
- `wargaming_tests_total`
- `wargaming_failures_total`
- `wargaming_test_duration_seconds_bucket`

**Refresh:** 30s  
**Time Range:** Last 6 hours

---

## Installation

Dashboards are automatically provisioned via Grafana provisioning system.

**Configuration:** `/monitoring/grafana/provisioning/dashboards/dashboards.yml`

```yaml
providers:
  - name: 'Vertice Dashboards'
    folder: ''
    type: file
    path: /etc/grafana/provisioning/dashboards
```

**Volume Mount:** `./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro`

---

## Usage

### Access Dashboards
1. Open Grafana: http://localhost:3001
2. Login: admin / vertice_admin
3. Navigate to Dashboards → Browse
4. Dashboards are tagged with `vertice` for easy filtering

### Dashboard Navigation
- All dashboards have 30s auto-refresh
- Time range: Last 6 hours (configurable)
- Use time picker to adjust range
- Click legend items to hide/show series
- Hover over graphs for detailed tooltips

---

## Customization

### Modify Existing Dashboards
1. Edit JSON files in `/monitoring/grafana/dashboards/`
2. Restart Grafana: `docker compose -f docker-compose.observability.yml restart grafana`
3. Changes apply immediately (provisioning enabled)

### Add New Dashboards
1. Create JSON file in `/monitoring/grafana/dashboards/`
2. Name format: `##-dashboard-name.json`
3. Set `"uid": "vertice-dashboardname"` for consistency
4. Add tags: `"tags": ["vertice", "category"]`
5. Restart Grafana

---

## Thresholds and Alerts

### Color Coding
- **Green:** Normal operation
- **Yellow:** Warning threshold
- **Red:** Critical threshold

### Key Thresholds
- **Error Rate:** 5% (warning)
- **Latency:** 1s P95 (warning)
- **CPU Usage:** 80% (critical)
- **Memory Usage:** 90% (critical)
- **Consciousness Level:** <0.5 (critical)
- **Wargaming Success:** <85% (critical)

---

## Compliance with Constituição Vértice

### Article II (Padrão Pagani)
- Zero mocks or placeholders
- Production-ready metrics queries
- Complete dashboard coverage

### Article IV (Antifragilidade)
- Wargaming dashboard for continuous validation
- Proactive threshold alerting
- Real-time health monitoring

### Article III (Zero Trust)
- All dashboards query validated metrics
- Authentication required (Grafana login)
- Read-only access to Prometheus

---

## Troubleshooting

### Dashboard Not Appearing
```bash
# Check provisioning logs
docker logs vertice-grafana | grep provisioning

# Verify file permissions
ls -la monitoring/grafana/dashboards/

# Restart Grafana
docker compose -f docker-compose.observability.yml restart grafana
```

### No Data Showing
```bash
# Verify Prometheus is scraping
curl http://localhost:9090/api/v1/targets | jq

# Check metric exists
curl 'http://localhost:9090/api/v1/query?query=up' | jq

# Verify datasource connection in Grafana
# Settings → Data Sources → Prometheus → Test
```

### Slow Dashboard Load
- Reduce time range (6h → 1h)
- Increase refresh interval (30s → 1m)
- Simplify queries (remove unnecessary aggregations)

---

## Metrics Reference

### Required Service Metrics
All services MUST expose these metrics:

```python
from prometheus_client import Counter, Histogram, Gauge

# Standard HTTP metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', 
                              ['method', 'endpoint', 'status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 
                                          'HTTP request duration')

# Health metric
up = Gauge('up', 'Service health status')
```

### MAXIMUS-Specific Metrics
```python
maximus_consciousness_level = Gauge('maximus_consciousness_level', 
                                     'Current consciousness level')
ethical_violations_total = Counter('ethical_violations_total', 
                                    'Total ethical violations')
maximus_decisions_total = Counter('maximus_decisions_total', 
                                   'Decisions made', ['decision_type'])
maximus_decision_duration_seconds = Histogram('maximus_decision_duration_seconds',
                                               'Decision processing time')
```

### Immune System Metrics
```python
immune_response_total = Counter('immune_response_total', 
                                'Immune responses', ['response_type'])
immune_response_failures_total = Counter('immune_response_failures_total',
                                          'Failed immune responses')
threat_detection_queue_size = Gauge('threat_detection_queue_size',
                                     'Threats in detection queue')
immune_response_duration_seconds = Histogram('immune_response_duration_seconds',
                                              'Response processing time')
```

### Wargaming Metrics
```python
wargaming_tests_total = Counter('wargaming_tests_total', 
                                'Total wargaming tests', ['test_type'])
wargaming_failures_total = Counter('wargaming_failures_total',
                                    'Failed wargaming tests')
wargaming_test_duration_seconds = Histogram('wargaming_test_duration_seconds',
                                             'Test execution time')
```

---

**Version:** 1.0  
**Last Updated:** 2025-10-16  
**Status:** Days 15-16 Complete - Production Ready
