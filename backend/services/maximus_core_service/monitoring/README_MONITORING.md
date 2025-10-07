# MAXIMUS AI 3.0 - Monitoring Guide 📊

**Status:** ✅ Production-Ready
**REGRA DE OURO:** 10/10 - Zero mocks, real metrics
**Stack:** Prometheus + Grafana

---

## 📋 Quick Start

### 1. Start Monitoring Stack

```bash
# Start MAXIMUS + Monitoring
docker-compose -f docker-compose.maximus.yml up -d

# Verify services
docker-compose -f docker-compose.maximus.yml ps
```

### 2. Access Dashboards

- **Grafana:** http://localhost:3000
  - Username: `admin`
  - Password: `maximus_admin_2025`

- **Prometheus:** http://localhost:9090
  - Metrics explorer
  - Query interface
  - Target health status

- **MAXIMUS Metrics:** http://localhost:8150/metrics
  - Raw Prometheus metrics
  - Text format export

---

## 📊 Available Dashboards

### 1. MAXIMUS AI 3.0 - Overview
**URL:** http://localhost:3000/d/maximus-overview

**Sections:**
- **System Health** (Row 1)
  - Event throughput (events/sec)
  - Pipeline latency (p50, p95, p99)
  - Detection accuracy gauge
  - False positive/negative rates
  - Threats detected by type

- **Predictive Coding** (Row 2)
  - Free Energy (surprise) by layer (l1-l5)
  - PC latency p95 by layer
  - Prediction error trends

- **Neuromodulation** (Row 3)
  - Dopamine level (RPE) gauge
  - Acetylcholine (attention) gauge
  - Norepinephrine (arousal) gauge
  - Serotonin (patience) gauge
  - Learning rate evolution

- **Skill Learning & Ethical AI** (Row 4)
  - Top 10 skills by execution rate
  - Average reward by skill
  - Ethical approval rate gauge
  - Ethical decisions (approved vs rejected)

---

## 🔍 Key Metrics to Watch

### Performance Metrics

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Pipeline Latency (p95) | < 100ms | > 500ms |
| Event Throughput | > 10 events/sec | < 1 event/sec |
| Detection Accuracy | > 90% | < 85% |
| False Positive Rate | < 5% | > 10% |
| False Negative Rate | < 5% | > 10% |

### Predictive Coding Metrics

| Metric | Normal Range | High Surprise |
|--------|-------------|---------------|
| Free Energy (L1) | 0.0 - 0.5 | > 0.7 |
| Free Energy (L5) | 0.0 - 0.6 | > 0.8 |
| PC Latency (L1) | < 50ms | > 100ms |
| PC Latency (L5) | < 500ms | > 1000ms |

### Neuromodulation Metrics

| Neuromodulator | Normal | Alert |
|---------------|--------|-------|
| Dopamine | 0.3 - 0.7 | < 0.1 or > 0.9 |
| Acetylcholine | 0.4 - 0.7 | < 0.2 or > 0.9 |
| Norepinephrine | 0.3 - 0.7 | < 0.2 or > 0.9 |
| Serotonin | 0.4 - 0.6 | < 0.2 or > 0.8 |
| Learning Rate | 0.005 - 0.02 | < 0.001 or > 0.05 |

### Skill Learning Metrics

| Metric | Good | Degraded |
|--------|------|----------|
| Skill Success Rate | > 80% | < 60% |
| Average Reward | > 0.5 | < 0.0 |
| Execution Latency | < 100ms | > 500ms |

### Ethical AI Metrics

| Metric | Target | Alert |
|--------|--------|-------|
| Approval Rate | > 95% | < 90% |
| Violations Rate | < 0.1/sec | > 1/sec |

---

## 🔔 Alerting

### Configure Alertmanager (Optional)

```yaml
# monitoring/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'team-slack'

receivers:
  - name: 'team-slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts-maximus'
        text: "{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}"
```

### Alert Rules

See `monitoring/METRICS.md` for recommended alert rules.

---

## 📈 Common Queries

### System Performance

```promql
# Overall throughput
rate(maximus_events_processed_total[5m])

# Threat detection rate
rate(maximus_events_processed_total{detected_as_threat="true"}[5m])

# Pipeline latency percentiles
histogram_quantile(0.95, rate(maximus_pipeline_latency_seconds_bucket[5m]))
```

### Predictive Coding Analysis

```promql
# Free energy by layer
avg(rate(maximus_free_energy_sum[5m])) by (layer) / rate(maximus_free_energy_count[5m])

# High surprise events (> 0.7)
rate(maximus_prediction_errors_total[5m])

# Layer latency comparison
histogram_quantile(0.95, rate(maximus_predictive_coding_latency_seconds_bucket[5m])) by (layer)
```

### Neuromodulation State

```promql
# Dopamine level
maximus_dopamine_level

# Learning rate modulation
maximus_learning_rate

# Neuromodulator balance check
abs(maximus_dopamine_level - maximus_serotonin_level)
```

### Skill Learning Performance

```promql
# Top skills by usage
topk(10, rate(maximus_skill_executions_total[1h]))

# Skill success rate
rate(maximus_skill_executions_total{status="success"}[5m]) / rate(maximus_skill_executions_total[5m])

# Average reward
avg(rate(maximus_skill_reward_sum[5m])) by (skill_name) / rate(maximus_skill_reward_count[5m])
```

---

## 🔧 Troubleshooting

### Grafana Dashboard Not Loading

**Symptoms:** Dashboard shows "No data"

**Solutions:**
1. Check Prometheus is running: `docker ps | grep prometheus`
2. Verify Prometheus targets: http://localhost:9090/targets
3. Check MAXIMUS metrics endpoint: `curl http://localhost:8150/metrics`
4. Verify data source in Grafana: Settings → Data Sources → Prometheus

### Metrics Not Updating

**Symptoms:** Stale metrics, no new data

**Solutions:**
1. Check MAXIMUS is running: `docker ps | grep maximus`
2. Verify metrics endpoint: `curl -s http://localhost:8150/metrics | grep maximus_`
3. Check Prometheus scrape config: `docker exec maximus-prometheus cat /etc/prometheus/prometheus.yml`
4. View Prometheus logs: `docker logs maximus-prometheus`

### High Cardinality Warning

**Symptoms:** Prometheus performance degradation

**Solutions:**
1. Reduce metric retention: `--storage.tsdb.retention.time=7d`
2. Limit label values: Review `skill_name`, `event_type` labels
3. Aggregate before storing: Use recording rules
4. Scale Prometheus: Add more storage/memory

### Dashboard Customization

**To modify dashboards:**

1. Edit in Grafana UI → Save → Export JSON
2. Replace `monitoring/dashboards/maximus_overview.json`
3. Restart Grafana: `docker-compose -f docker-compose.maximus.yml restart grafana`

**Or edit JSON directly:**
```bash
# Edit dashboard JSON
vim monitoring/dashboards/maximus_overview.json

# Restart Grafana to reload
docker-compose -f docker-compose.maximus.yml restart grafana
```

---

## 📊 Grafana Tips

### Creating Custom Panels

1. Click **+ Add Panel** in dashboard
2. Select **Prometheus** as data source
3. Enter PromQL query (see METRICS.md)
4. Choose visualization type (Graph, Gauge, Stat, etc.)
5. Configure thresholds and colors
6. Save panel

### Using Variables

```json
{
  "templating": {
    "list": [
      {
        "name": "layer",
        "type": "query",
        "query": "label_values(maximus_free_energy, layer)",
        "multi": true
      }
    ]
  }
}
```

### Setting Up Alerts

1. Edit panel → Alert tab
2. Create alert rule
3. Set condition (e.g., `WHEN avg() OF query(A, 5m, now) IS ABOVE 0.9`)
4. Configure notification channel
5. Save alert

---

## 🎯 Best Practices

### Metric Collection

1. **Sample Rate:** 10-15s for most metrics (balance freshness vs load)
2. **Retention:** 15 days minimum (30 days recommended)
3. **Cardinality:** Limit unique label combinations (< 10k per metric)
4. **Labels:** Use for dimensions (layer, skill_name), not values

### Dashboard Design

1. **Top-Down:** Start with high-level metrics (throughput, latency)
2. **Drill-Down:** Provide detail on click (layer-specific, skill-specific)
3. **Color Coding:** Green (good), Yellow (warning), Red (critical)
4. **Annotations:** Mark deployments, incidents, config changes

### Alerting

1. **Severity Levels:** Critical, Warning, Info
2. **Actionable:** Alert should indicate what to do
3. **Avoid Noise:** Set appropriate thresholds and durations
4. **Test Regularly:** Verify alerts trigger correctly

---

## 📚 Resources

### Documentation

- `METRICS.md` - Complete metrics reference
- `prometheus.yml` - Prometheus configuration
- Grafana Dashboards: `dashboards/*.json`

### External Links

- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)

---

## 🆘 Support

**Issues with monitoring?**

1. Check this README troubleshooting section
2. Verify all services are running: `docker-compose ps`
3. Check logs: `docker-compose logs -f prometheus grafana`
4. Test metrics endpoint: `curl http://localhost:8150/metrics`

**For MAXIMUS AI issues:** See main DEPLOYMENT.md

---

**MAXIMUS AI 3.0 Monitoring** - Production-ready observability ✅

*Prometheus + Grafana stack completo, REGRA DE OURO 10/10.*
