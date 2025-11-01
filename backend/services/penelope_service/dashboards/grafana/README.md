# PENELOPE Grafana Dashboards

## Overview

This directory contains Grafana dashboard configurations for monitoring the PENELOPE (Platform for Enlightened Networked Execution with Love, Obedience, Prudence, and Eternal-mindedness) autonomous healing service.

## Available Dashboards

### 1. PENELOPE Overview (`penelope_overview.json`)

**Purpose**: Comprehensive operational metrics for PENELOPE service

**Panels**:
1. **Decision Rate** - Decisions per hour (gauge)
2. **Decision Breakdown** - Breakdown by type: observe/intervene/escalate (timeseries)
3. **Circuit Breaker Status** - State by service: CLOSED/OPEN/HALF_OPEN (table)
4. **Pending Approvals** - Number of patches awaiting human approval (gauge)
5. **Patch Success Rate** - Success rate over 1h window (gauge)
6. **Risk Score Distribution** - p50/p90/p99 risk scores (timeseries)
7. **Decision Duration** - p50/p90/p99 decision latency (timeseries)
8. **Approval Requests** - Breakdown by status: approved/rejected/expired (timeseries)
9. **Healing Velocity** - Patches deployed per hour (timeseries)

**Key Metrics**:
- `penelope_decisions_total` - Counter of Sophia Engine decisions
- `penelope_circuit_breaker_state` - Circuit breaker state (0=closed, 1=open, 2=half_open)
- `penelope_approval_pending` - Gauge of pending approval requests
- `penelope_patch_deployments_total` - Counter of patch deployments
- `penelope_decision_risk_scores_bucket` - Histogram of risk scores
- `penelope_decision_duration_seconds_bucket` - Histogram of decision latency
- `penelope_approval_requests_total` - Counter of approval requests

### 2. PENELOPE Biblical Compliance (`penelope_biblical_compliance.json`)

**Purpose**: Monitor adherence to the 7 Biblical Articles that govern PENELOPE

**Panels**:

1. **Artigo I: Sophia (Wisdom)** - Proverbs 9:10
   - Metric: Percentage of decisions that are "observe" (waiting wisely)
   - Good: >80% (most anomalies self-heal, wisdom prevails)
   - Warning: <50% (intervening too much)

2. **Artigo II: Praotes (Gentleness)** - James 1:21
   - Metric: Average patch size in lines
   - Good: <5 lines (surgical patches)
   - Warning: >15 lines (too aggressive)

3. **Artigo III: Tapeinophrosyne (Humility)** - James 4:6
   - Metric: Percentage of decisions that escalate to humans
   - Good: 10-20% (knows limits, asks for help)
   - Warning: <5% (overconfident) or >50% (underconfident)

4. **Artigo IV: Prudence** - Proverbs 14:15
   - Metric: Number of circuit breakers currently OPEN
   - Good: 0 (no services blocked)
   - Warning: >3 (multiple services having issues)

5. **Artigo V: Agape (Love)** - 1 Corinthians 13:4-7
   - Metric: Successful healing rate over time
   - Shows love-driven service through consistent healing

6. **Artigo VI: Sabbath (Rest)** - Exodus 20:8-10
   - Metric: Average cooldown time remaining
   - Shows system respects rest periods and boundaries

7. **Artigo VII: Aletheia (Truth)** - John 14:6
   - Metric: Total decisions logged to audit trail
   - Shows complete transparency

8. **Wise Counsel** - Proverbs 15:22
   - Metric: Human approval requests by status
   - Shows seeking counsel for high-risk operations

9. **Overall Biblical Compliance Score**
   - Composite metric (0-100%) combining all articles
   - Weighted formula:
     - Sophia (20%): Observe ratio
     - Praotes (15%): Inverse of patch size
     - Tapeinophrosyne (15%): Escalation ratio
     - Prudence (15%): Inverse of open circuits
     - Agape (15%): Success rate
     - Sabbath (10%): Fixed 100% (respects cooldowns)
     - Aletheia (10%): Binary (logging enabled)
   - Good: >90% (excellent compliance)
   - Warning: <70% (review needed)

## Installation

### Import to Grafana

1. **Via UI**:
   ```bash
   # Navigate to Grafana
   # Dashboards → Import → Upload JSON file
   # Select dashboard file and import
   ```

2. **Via API**:
   ```bash
   # Set Grafana URL and API key
   GRAFANA_URL="http://localhost:3000"
   GRAFANA_API_KEY="your-api-key"

   # Import Overview dashboard
   curl -X POST \
     -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
     -H "Content-Type: application/json" \
     -d @penelope_overview.json \
     "${GRAFANA_URL}/api/dashboards/db"

   # Import Biblical Compliance dashboard
   curl -X POST \
     -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
     -H "Content-Type: application/json" \
     -d @penelope_biblical_compliance.json \
     "${GRAFANA_URL}/api/dashboards/db"
   ```

3. **Via Terraform**:
   ```hcl
   resource "grafana_dashboard" "penelope_overview" {
     config_json = file("${path.module}/penelope_overview.json")
   }

   resource "grafana_dashboard" "penelope_biblical_compliance" {
     config_json = file("${path.module}/penelope_biblical_compliance.json")
   }
   ```

### Configure Data Source

1. Ensure Prometheus data source is configured in Grafana
2. Name it "Prometheus" or update the `DS_PROMETHEUS` variable in the dashboards
3. Prometheus should be scraping PENELOPE metrics on default port 8000

## Prometheus Configuration

Add PENELOPE to your Prometheus scrape config:

```yaml
scrape_configs:
  - job_name: 'penelope'
    static_configs:
      - targets: ['penelope:8000']
    scrape_interval: 15s
    metrics_path: '/metrics'
```

## Metrics Reference

### Decision Metrics
```prometheus
# Total decisions made by Sophia Engine
penelope_decisions_total{decision="observe|intervene|escalate"}

# Decision duration histogram
penelope_decision_duration_seconds_bucket{le="0.1|0.5|1.0|5.0"}

# Decisions logged to audit trail
penelope_decisions_logged_total{decision_type="observe|intervene|escalate"}

# Risk score histogram
penelope_decision_risk_scores_bucket{le="0.1|0.3|0.5|0.7|0.9"}
```

### Circuit Breaker Metrics
```prometheus
# Circuit breaker state per service (0=closed, 1=open, 2=half_open)
penelope_circuit_breaker_state{service="api-gateway|user-service|..."}

# Failure count per service
penelope_circuit_breaker_failures{service="..."}

# Circuit state transitions
penelope_circuit_transitions_total{service="...",from_state="...",to_state="..."}

# Cooldown remaining (for dashboard)
penelope_circuit_cooldown_remaining_seconds{service="..."}
```

### Approval Metrics
```prometheus
# Pending approval requests (gauge)
penelope_approval_pending

# Approval requests by status
penelope_approval_requests_total{status="approved|rejected|expired|cancelled"}

# Approval response time histogram
penelope_approval_response_seconds_bucket{le="60|300|600|1800|3600"}
```

### Patch Metrics
```prometheus
# Patch deployments by status
penelope_patch_deployments_total{status="success|failure|rollback"}

# Patch size in lines (for gentleness tracking)
penelope_patch_size_lines{severity="surgical|moderate|redesign"}
```

## Alerting Rules

Recommended Prometheus alerting rules:

```yaml
groups:
  - name: penelope
    rules:
      - alert: PenelopeHighRiskDecisions
        expr: rate(penelope_decision_risk_scores_bucket{le="0.9"}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "PENELOPE making many high-risk decisions"
          description: "More than 10% of decisions have risk score >0.9"

      - alert: PenelopeCircuitBreakerOpen
        expr: penelope_circuit_breaker_state == 1
        for: 5m
        annotations:
          summary: "Circuit breaker OPEN for {{ $labels.service }}"
          description: "Healing blocked for {{ $labels.service }}"

      - alert: PenelopePendingApprovals
        expr: penelope_approval_pending > 5
        for: 10m
        annotations:
          summary: "Many pending approvals ({{ $value }})"
          description: "Check Slack #penelope-approvals channel"

      - alert: PenelopeLowSuccessRate
        expr: |
          sum(rate(penelope_patch_deployments_total{status="success"}[1h]))
          /
          sum(rate(penelope_patch_deployments_total[1h])) < 0.7
        for: 30m
        annotations:
          summary: "Low patch success rate (<70%)"
          description: "Review recent failures in PENELOPE"

      - alert: PenelopeBiblicalComplianceLow
        expr: |
          (
            (sum(rate(penelope_decisions_total{decision="observe"}[1h])) / sum(rate(penelope_decisions_total[1h]))) * 100 * 0.20 +
            (1 - (avg(penelope_patch_size_lines) / 25)) * 100 * 0.15 +
            (sum(rate(penelope_decisions_total{decision="escalate"}[1h])) / sum(rate(penelope_decisions_total[1h]))) * 100 * 0.15 +
            (1 - (count(penelope_circuit_breaker_state == 1) / count(penelope_circuit_breaker_state))) * 100 * 0.15 +
            (sum(rate(penelope_patch_deployments_total{status="success"}[1h])) / sum(rate(penelope_patch_deployments_total[1h]))) * 100 * 0.15 +
            100 * 0.10 +
            (penelope_decisions_logged_total > 0) * 100 * 0.10
          ) < 70
        for: 1h
        annotations:
          summary: "Biblical compliance score below 70%"
          description: "Review PENELOPE biblical compliance dashboard"
```

## Dashboard Variables

Both dashboards support these variables:

- `DS_PROMETHEUS` - Prometheus data source (auto-detected)
- Time range selector (default: last 6 hours)
- Refresh interval (default: 30s)

## Troubleshooting

### No data showing

1. Check Prometheus is scraping PENELOPE:
   ```bash
   curl http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="penelope")'
   ```

2. Check PENELOPE /metrics endpoint:
   ```bash
   curl http://penelope:8000/metrics | grep penelope_
   ```

3. Check Grafana data source connection:
   ```bash
   curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
     "${GRAFANA_URL}/api/datasources" | jq '.[] | select(.type=="prometheus")'
   ```

### Metrics not updating

- Check scrape interval in Prometheus config (should be ≤15s)
- Verify PENELOPE is actively making decisions (check logs)
- Check Grafana dashboard refresh interval

### High cardinality warnings

If you see high cardinality warnings:
- Limit number of services with circuit breakers
- Use recording rules for complex queries
- Increase Prometheus retention or reduce scrape interval

## Recording Rules (Optional)

For better performance on complex queries:

```yaml
groups:
  - name: penelope_recording
    interval: 30s
    rules:
      - record: penelope:decision_rate:5m
        expr: rate(penelope_decisions_total[5m])

      - record: penelope:success_rate:1h
        expr: |
          sum(rate(penelope_patch_deployments_total{status="success"}[1h]))
          /
          sum(rate(penelope_patch_deployments_total[1h]))

      - record: penelope:biblical_compliance:score
        expr: |
          (
            (sum(rate(penelope_decisions_total{decision="observe"}[1h])) / sum(rate(penelope_decisions_total[1h]))) * 100 * 0.20 +
            (1 - (avg(penelope_patch_size_lines) / 25)) * 100 * 0.15 +
            (sum(rate(penelope_decisions_total{decision="escalate"}[1h])) / sum(rate(penelope_decisions_total[1h]))) * 100 * 0.15 +
            (1 - (count(penelope_circuit_breaker_state == 1) / count(penelope_circuit_breaker_state))) * 100 * 0.15 +
            (sum(rate(penelope_patch_deployments_total{status="success"}[1h])) / sum(rate(penelope_patch_deployments_total[1h]))) * 100 * 0.15 +
            100 * 0.10 +
            (penelope_decisions_logged_total > 0) * 100 * 0.10
          )
```

## Support

**Team**: Vértice Platform Team
**Slack**: #penelope-support
**Email**: penelope-support@vertice.ai
**Docs**: https://penelope.vertice.ai/docs

---

**Generated**: 2025-11-01
**Version**: 1.0.0
**Biblical Foundation**: Proverbs 27:23 - "Know well the condition of your flocks, and give attention to your herds"
