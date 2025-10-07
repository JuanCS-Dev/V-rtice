# Prometheus Alerting Rules - Active Immune Core

Enterprise-grade alerting rules for proactive system monitoring and incident response.

## 📋 Overview

This directory contains Prometheus alerting and recording rules for the Active Immune Core system.

### Files

- **`immune_core_alerts.yaml`**: Alerting rules (51 alerts across 11 groups)
- **`recording_rules.yaml`**: Recording rules for query optimization (90+ rules across 7 groups)
- **`README.md`**: This documentation

## 🚨 Alert Groups

### 1. Availability Alerts

Critical alerts for system availability SLO (99.9%).

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `SystemAvailabilityBelowSLO` | critical | 5m | Availability < 99.9% |
| `NoAgentsAlive` | critical | 1m | All agents are dead |
| `LowAgentCount` | warning | 5m | < 5 agents alive |

### 2. Agent Health Alerts

Monitor agent health scores and load.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `LowAgentHealth` | warning | 10m | Avg health < 70% |
| `CriticalAgentHealth` | critical | 5m | Avg health < 50% |
| `HighAgentLoad` | warning | 10m | Avg load > 90% |
| `AgentTypeImbalance` | info | 15m | Type distribution imbalanced |
| `HighHeartbeatTimeouts` | warning | 5m | > 0.1 timeouts/sec |

### 3. Coordination Alerts

Leader election and task coordination monitoring.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `NoLeader` | critical | 2m | No leader elected |
| `HighElectionRate` | warning | 10m | > 0.2 elections/sec |
| `FrequentLeaderChanges` | warning | 10m | > 0.1 changes/sec |
| `HighTaskBacklog` | warning | 5m | > 100 pending tasks |
| `CriticalTaskBacklog` | critical | 5m | > 500 pending tasks |
| `TaskAssignmentLag` | warning | 10m | > 1 task/sec lag |

### 4. Task Execution Alerts

Task performance and SLO compliance.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `HighTaskFailureRate` | warning | 10m | Failure rate > 10% |
| `TaskSuccessRateBelowSLO` | critical | 5m | Success rate < 95% |
| `HighTaskLatency` | warning | 10m | p95 > 30s |
| `CriticalTaskLatency` | critical | 5m | p95 > 60s |
| `HighTaskRetryRate` | warning | 10m | p95 > 3 retries |

### 5. API Performance Alerts

API latency and error rate monitoring.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `HighAPILatency` | critical | 5m | p99 > 500ms |
| `HighAPIErrorRate` | critical | 5m | Error rate > 5% |
| `APIEndpointDown` | critical | 5m | No requests in 5m |

### 6. Fault Tolerance Alerts

Failure detection and recovery monitoring.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `HighFailureDetectionRate` | warning | 10m | > 0.1 failures/sec |
| `RecoveryFailures` | critical | 10m | Failures > recoveries |

### 7. Infrastructure Alerts

Cytokine, hormone, and lymph node monitoring.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `LowCytokineTraffic` | warning | 10m | < 0.1 messages/sec |
| `CytokineFlowImbalance` | warning | 10m | > 30% imbalance |
| `NoHormonePublications` | warning | 10m | No publications in 10m |

### 8. SLO Error Budget Alerts

Error budget tracking and burn rate monitoring.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `ErrorBudgetBurnRateHigh` | critical | 5m | Burn rate > 1.0 |
| `ErrorBudgetLow` | warning | 1h | < 20% budget remaining |
| `ErrorBudgetExhausted` | critical | 1h | Budget exhausted |

### 9. Consensus Alerts

Consensus mechanism monitoring.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `LowProposalApprovalRate` | warning | 10m | < 50% approved |
| `NoConsensusActivity` | info | 15m | No proposals in 15m |

### 10. System Health Alerts

Overall system health indicators.

| Alert | Severity | Duration | Description |
|-------|----------|----------|-------------|
| `SystemDegraded` | warning | 5m | One or more indicators failing |
| `SystemUnhealthy` | critical | 5m | Multiple critical indicators failing |

## 📊 Recording Rules

Recording rules pre-compute expensive queries to improve dashboard and alert performance.

### Groups

1. **Aggregations**: Sum/avg metrics across agents and types
2. **Rates**: Rate calculations for counters (5m window)
3. **Ratios**: Success rates, availability, error rates
4. **Percentiles**: p50/p95/p99 for latency metrics
5. **SLO Metrics**: Pre-computed SLO compliance checks
6. **Health Scores**: Composite health indicators
7. **Agent Types**: Innate vs adaptive immune system metrics

### Examples

```promql
# Pre-computed availability
immune_core:availability:ratio

# Pre-computed task success rate
immune_core:tasks_success_rate:ratio

# Pre-computed API p99 latency
immune_core:api_latency:p99

# Pre-computed SLO breach indicators
immune_core:slo:availability_breached
immune_core:slo:api_latency_breached
immune_core:slo:task_success_rate_breached
```

## 🚀 Installation

### Prometheus Configuration

Add rules to `prometheus.yml`:

```yaml
rule_files:
  - /path/to/active_immune_core/monitoring/alerting/immune_core_alerts.yaml
  - /path/to/active_immune_core/monitoring/alerting/recording_rules.yaml
```

### Docker Compose

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/alerting:/etc/prometheus/rules:ro
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
```

Prometheus config:
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/rules/*.yaml

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

scrape_configs:
  - job_name: 'immune-core'
    static_configs:
      - targets: ['immune-core-api:8000']
```

### Validation

Validate rules before deployment:

```bash
# Check alert rules
promtool check rules immune_core_alerts.yaml

# Check recording rules
promtool check rules recording_rules.yaml

# Test alert query
promtool query instant http://localhost:9090 \
  'sum(immune_core_agents_alive) / sum(immune_core_agents_total)'
```

## 🔔 Alertmanager Configuration

### Basic Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity', 'component']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    - match:
        severity: warning
      receiver: 'slack'

    - match:
        severity: info
      receiver: 'email'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .GroupLabels.instance }}'

  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'Active Immune Core Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'

  - name: 'email'
    email_configs:
      - to: 'team@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'YOUR_PASSWORD'
```

### Advanced Routing

```yaml
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']

  routes:
    # Page for critical SLO breaches
    - match:
        severity: critical
        slo: availability
      receiver: 'pagerduty-oncall'
      group_wait: 0s

    # Page for API SLO breaches
    - match:
        severity: critical
        slo: api_latency
      receiver: 'pagerduty-oncall'
      group_wait: 30s

    # Slack for warnings
    - match:
        severity: warning
      receiver: 'slack-warnings'
      group_wait: 5m

    # Email for info
    - match:
        severity: info
      receiver: 'email-team'
      group_wait: 15m
```

## 🎯 SLO Definitions

### Availability SLO: 99.9%

**Objective**: System should be available 99.9% of the time

**Measurement**:
```promql
sum(immune_core_agents_alive) / sum(immune_core_agents_total)
```

**Allowed Downtime**: 43.2 minutes/month

**Error Budget**: 0.1% (43.2 minutes/month)

### API Latency SLO: p99 < 500ms

**Objective**: 99% of API requests complete in < 500ms

**Measurement**:
```promql
histogram_quantile(0.99, rate(immune_core_api_latency_seconds_bucket[5m]))
```

### Task Success Rate SLO: > 95%

**Objective**: 95% of tasks complete successfully

**Measurement**:
```promql
sum(rate(immune_core_tasks_completed_total[5m])) /
(sum(rate(immune_core_tasks_completed_total[5m])) + sum(rate(immune_core_tasks_failed_total[5m])))
```

## 📚 Runbooks

### SystemAvailabilityBelowSLO

**Severity**: Critical
**SLO**: Availability

**Investigation Steps**:
1. Check agent count: `sum(immune_core_agents_alive)`
2. Check agent health: `avg(immune_core_agent_health_score)`
3. Check for failures: `immune_core_failures_detected_total`
4. Review logs for errors
5. Check coordinator status: `immune_core_has_leader`

**Resolution**:
- Restart dead agents
- Scale up if capacity issue
- Fix infrastructure issues
- Review recent deployments

### NoLeader

**Severity**: Critical
**Component**: Coordination

**Investigation Steps**:
1. Check coordinator logs
2. Check network connectivity
3. Verify agent count >= 3 (quorum)
4. Check election metrics

**Resolution**:
- Trigger manual election if stuck
- Check network partitions
- Verify agent health
- Restart coordinator if necessary

### HighAPILatency

**Severity**: Critical
**SLO**: API Latency

**Investigation Steps**:
1. Check task queue: `immune_core_tasks_pending`
2. Check agent load: `avg(immune_core_agent_load)`
3. Check database performance
4. Review slow queries

**Resolution**:
- Scale up agents
- Optimize slow tasks
- Clear task backlog
- Add caching

## 🔍 Troubleshooting

### Alerts Not Firing

1. Check Prometheus is scraping metrics:
   ```promql
   up{job="immune-core"}
   ```

2. Verify alert rule syntax:
   ```bash
   promtool check rules immune_core_alerts.yaml
   ```

3. Check alert state in Prometheus UI:
   `http://prometheus:9090/alerts`

4. Verify Alertmanager connection:
   ```promql
   prometheus_notifications_sent_total
   ```

### Recording Rules Not Working

1. Check evaluation:
   ```promql
   immune_core:availability:ratio
   ```

2. Verify rule syntax:
   ```bash
   promtool check rules recording_rules.yaml
   ```

3. Check Prometheus logs for errors

4. Ensure evaluation interval is set

### False Positives

- Adjust `for` duration to reduce noise
- Tune thresholds based on baseline
- Add conditions to exclude expected states
- Use inhibition rules in Alertmanager

## 📊 Best Practices

### Alert Design

1. **Critical vs Warning**: Reserve critical for actionable, urgent issues
2. **Duration**: Use `for` clause to avoid flapping
3. **Thresholds**: Base on historical data and SLOs
4. **Annotations**: Include context and runbook links

### Recording Rules

1. **Naming**: Use `:` separator (e.g., `job:metric:aggregation`)
2. **Granularity**: Match alert evaluation interval
3. **Optimization**: Pre-compute expensive queries
4. **Documentation**: Comment complex calculations

### Monitoring

- Review alert history monthly
- Tune thresholds based on patterns
- Remove unused alerts
- Update runbooks with learnings
- Track MTTR and MTTA metrics

---

**Authors**: Juan & Claude
**Version**: 1.0.0
**Last Updated**: 2025-10-06
