# Grafana Dashboards - Active Immune Core

Enterprise-grade Grafana dashboards for comprehensive system monitoring.

## 📊 Dashboards

### 1. Overview Dashboard (`overview.json`)

**Purpose**: High-level system health and performance overview

**Key Metrics**:
- System health status
- Active agents by type
- Tasks pending
- Leader status
- Task completion rate
- Agent health and load distribution
- Elections and leader changes
- Task duration percentiles (p50, p95)
- Failure detection and recovery
- API request rate and latency

**Use Cases**:
- Quick health check
- Executive dashboards
- NOC/SOC displays
- Initial troubleshooting

### 2. Agents Dashboard (`agents.json`)

**Purpose**: Detailed agent performance and health monitoring

**Key Metrics**:
- Agent distribution by type (innate vs adaptive)
- Alive vs dead agents
- Agent health score heatmap
- Health and load by type
- Tasks completed/failed per agent type
- Top/bottom agents by health score
- Agent success rate
- Heartbeat timeouts
- Load distribution

**Use Cases**:
- Agent performance analysis
- Capacity planning
- Identifying problematic agents
- Load balancing evaluation

### 3. Coordination Dashboard (`coordination.json`)

**Purpose**: Leader election, consensus, and task coordination metrics

**Key Metrics**:
- Leadership status
- Total elections and leader changes
- Tasks submitted vs assigned
- Task assignment lag
- Tasks pending
- Task completion rate by type
- Consensus proposals by type
- Proposal approval rate
- Votes cast by decision
- Task success rate
- Task duration distribution
- Task retry rate
- Coordination health score

**Use Cases**:
- Coordination system health
- Leader stability monitoring
- Task queue analysis
- Consensus mechanism evaluation
- Performance troubleshooting

**Alerts**:
- High election rate (> 10 elections/5m)
- High task backlog (> 100 pending)

### 4. Infrastructure Dashboard (`infrastructure.json`)

**Purpose**: Cytokine messaging, hormone publications, and lymph node monitoring

**Key Metrics**:
- Cytokine traffic overview (sent/received)
- Hormone publications
- Cytokines by type (sent/received)
- Cytokine flow balance
- Cytokine type distribution
- Top cytokine types
- Hormones by type
- Lymph node registrations
- Cytokine latency
- Infrastructure health score
- Message throughput heatmap
- Traffic by hour

**Use Cases**:
- Message flow analysis
- Communication bottleneck detection
- Infrastructure health monitoring
- Traffic pattern analysis

### 5. SLA Dashboard (`sla.json`)

**Purpose**: Service Level Agreement monitoring and SLO compliance

**Key SLOs**:
- **Availability**: 99.9% (Three Nines)
- **API Latency**: p99 < 500ms
- **Task Success Rate**: > 95%
- **Task Duration**: < 30s for 95% of tasks

**Key Metrics**:
- Overall system availability
- API latency p99
- Task success rate
- SLO compliance (24h)
- Availability trend (7 days)
- API latency trend (p50, p95, p99)
- Error budget remaining
- MTBF (Mean Time Between Failures)
- MTTR (Mean Time To Recovery)
- API success rate by endpoint
- Task duration SLO compliance
- SLO violation events
- Downtime minutes (30 days)
- Nines of availability
- SLO budget burn rate

**Alerts**:
- Availability SLO breach (< 99.9%)
- API latency SLO breach (> 500ms)
- Task success rate SLO breach (< 95%)
- High error budget burn rate

**Use Cases**:
- SLA compliance reporting
- Error budget management
- Production incident response
- Executive reporting
- Capacity planning

## 🚀 Installation

### Option 1: Manual Import

1. Access Grafana UI
2. Navigate to Dashboards → Import
3. Upload JSON file or paste JSON content
4. Select Prometheus data source
5. Click Import

### Option 2: Provisioning (Recommended)

Create Grafana provisioning configuration:

```yaml
# /etc/grafana/provisioning/dashboards/immune-core.yaml
apiVersion: 1

providers:
  - name: 'Active Immune Core'
    orgId: 1
    folder: 'Immune System'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /path/to/active_immune_core/monitoring/grafana
```

Restart Grafana:
```bash
sudo systemctl restart grafana-server
```

### Option 3: Docker Compose

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./monitoring/grafana:/etc/grafana/provisioning/dashboards/immune-core:ro
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🔧 Configuration

### Data Source

All dashboards expect a Prometheus data source named `Prometheus`.

Configure in Grafana:
1. Configuration → Data Sources → Add data source
2. Select Prometheus
3. URL: `http://prometheus:9090`
4. Save & Test

### Refresh Intervals

- **Overview**: 10s
- **Agents**: 10s
- **Coordination**: 10s
- **Infrastructure**: 10s
- **SLA**: 30s (less frequent for long-term metrics)

Adjust in dashboard settings based on your needs.

### Time Ranges

- **Overview**: Last 1 hour (default)
- **Agents**: Last 1 hour
- **Coordination**: Last 1 hour
- **Infrastructure**: Last 1 hour
- **SLA**: Last 24 hours (for SLO compliance)

## 🎨 Customization

### Variables

Add dashboard variables for dynamic filtering:

```json
"templating": {
  "list": [
    {
      "name": "agent_type",
      "type": "query",
      "query": "label_values(immune_core_agents_total, type)"
    }
  ]
}
```

### Annotations

Add annotations for events:

```json
"annotations": {
  "list": [
    {
      "datasource": "Prometheus",
      "expr": "ALERTS{alertname=~\".*\"}",
      "tagKeys": "alertname,severity",
      "textFormat": "{{alertname}}: {{summary}}",
      "titleFormat": "Alert"
    }
  ]
}
```

## 📈 Best Practices

### Dashboard Organization

1. **Overview**: Start here for system health check
2. **Specific Area**: Drill down to agents/coordination/infrastructure
3. **SLA**: Check compliance and error budget

### Alert Configuration

Configure alerts in:
- Coordination dashboard (elections, task backlog)
- Agents dashboard (heartbeat timeouts)
- SLA dashboard (SLO breaches, burn rate)

### Performance

- Use recording rules for expensive queries
- Limit time ranges for heavy queries
- Use downsampling for historical data

## 🔍 Troubleshooting

### No Data Appearing

1. Check Prometheus data source configuration
2. Verify Prometheus is scraping metrics endpoint
3. Check metric names match (`immune_core_*`)
4. Verify time range includes data

### Slow Dashboard Loading

1. Reduce time range
2. Increase refresh interval
3. Use recording rules for complex queries
4. Enable query caching

### Missing Panels

1. Check Grafana version compatibility (v8.0+)
2. Verify all metric names exist in Prometheus
3. Check for PromQL syntax errors

## 📚 Related Documentation

- [Prometheus Exporter](../prometheus_exporter.py)
- [Health Checker](../health_checker.py)
- [Metrics Collector](../metrics_collector.py)
- [Alerting Rules](../alerting/)

## 🎯 SLO Definitions

### Availability SLO: 99.9%

```
Availability = (Agents Alive / Agents Total)
Allowed Downtime: 43.2 minutes/month
```

### API Latency SLO: p99 < 500ms

```
p99 Latency = histogram_quantile(0.99, rate(immune_core_api_latency_seconds_bucket[5m]))
```

### Task Success Rate SLO: > 95%

```
Success Rate = Tasks Completed / (Tasks Completed + Tasks Failed)
```

### Task Duration SLO: < 30s for 95% of tasks

```
Compliance = Tasks < 30s / Total Tasks
```

## 🚨 Critical Alerts

### Availability SLO Breach
**Trigger**: Availability < 99.9% for 5 minutes
**Action**: Investigate agent failures, check coordinator health

### API Latency SLO Breach
**Trigger**: p99 latency > 500ms for 5 minutes
**Action**: Check task queue, agent load, resource constraints

### Task Success Rate SLO Breach
**Trigger**: Success rate < 95% for 5 minutes
**Action**: Investigate task failures, check error logs

### High Error Budget Burn Rate
**Trigger**: Burn rate > 1.0
**Action**: Immediate investigation, potential incident

## 📊 Dashboard Maintenance

### Regular Tasks

- Review and update SLOs quarterly
- Add new metrics as system evolves
- Optimize slow queries
- Update alert thresholds based on patterns
- Archive old dashboards

### Version Control

Keep dashboard JSON files in version control:
```bash
git add monitoring/grafana/*.json
git commit -m "feat(monitoring): Update Grafana dashboards"
```

---

**Authors**: Juan & Claude
**Version**: 1.0.0
**Last Updated**: 2025-10-06
