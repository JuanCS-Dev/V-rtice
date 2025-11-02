# NIS Operational Runbook

**Service**: Narrative Intelligence Service (NIS)
**Version**: 2.0.0
**Owner**: Vértice Platform Team
**Last Updated**: 2025-11-02

---

## 📋 Table of Contents

1. [Service Overview](#service-overview)
2. [Deployment](#deployment)
3. [Monitoring](#monitoring)
4. [Common Operations](#common-operations)
5. [Incident Response](#incident-response)
6. [Maintenance](#maintenance)
7. [Escalation](#escalation)

---

## 🎯 Service Overview

### Purpose

NIS generates AI-powered narratives from system metrics, providing actionable insights to operators and stakeholders.

### SLA

- **Availability**: 99.5% (production)
- **Latency P95**: <2s (narrative generation)
- **Error Rate**: <1%

### Dependencies

- **Critical**:
  - Claude API (Anthropic)
  - Redis (caching)
- **Important**:
  - Prometheus (metrics collection)
- **Optional**:
  - InfluxDB (historical data)

---

## 🚀 Deployment

### Production Deployment

#### 1. Pre-deployment Checklist

```bash
# Verify all tests pass
cd /path/to/nis_service
python -m pytest tests/ -v

# Check coverage
python -m pytest tests/ --cov=core --cov-report=term
# Expected: ≥90%

# Verify Docker build
docker build -t vertice/nis:${VERSION} .

# Tag for production
docker tag vertice/nis:${VERSION} vertice/nis:latest
```

#### 2. Deploy to Kubernetes

```bash
# Update deployment manifest
sed -i "s/IMAGE_VERSION/${VERSION}/g" k8s/deployment.yaml

# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Verify rollout
kubectl rollout status deployment/nis-service -n vertice

# Check pod health
kubectl get pods -n vertice -l app=nis-service
```

#### 3. Post-deployment Validation

```bash
# Health check
curl https://nis.vertice.ai/health/ready

# Smoke test - generate narrative
curl -X POST https://nis.vertice.ai/api/v1/narratives \
  -H "Content-Type: application/json" \
  -d '{
    "narrative_type": "summary",
    "metrics_data": {
      "metrics": [{"name": "test_metric", "value": 100}]
    }
  }'

# Check metrics export
curl https://nis.vertice.ai/metrics | grep nis_narratives
```

### Rollback Procedure

```bash
# List previous deployments
kubectl rollout history deployment/nis-service -n vertice

# Rollback to previous version
kubectl rollout undo deployment/nis-service -n vertice

# Rollback to specific revision
kubectl rollout undo deployment/nis-service -n vertice --to-revision=5

# Verify rollback
kubectl rollout status deployment/nis-service -n vertice
```

---

## 📊 Monitoring

### Key Dashboards

1. **NIS Overview** (`http://grafana.vertice.ai/d/nis-overview`)
   - Request rate
   - Error rate
   - Latency (P50, P95, P99)
   - Cost metrics

2. **Cost Dashboard** (`http://grafana.vertice.ai/d/nis-cost`)
   - Daily/monthly spend
   - Budget utilization
   - Cost per narrative
   - Cache hit ratio

3. **Anomaly Detection** (`http://grafana.vertice.ai/d/nis-anomalies`)
   - Anomalies detected (by severity)
   - Z-score distribution
   - Baseline drift

### Critical Alerts

#### 1. Budget Alert

**Alert**: `NISDailyBudgetExceeded`

**Severity**: Warning

**Trigger**: Daily spend > $10 USD

**Response**:

```bash
# Check current costs
curl https://nis.vertice.ai/api/v1/cost/current

# Review recent narratives
curl https://nis.vertice.ai/api/v1/narratives?limit=100

# Check cache hit ratio (should be 60-80%)
curl https://nis.vertice.ai/api/v1/cache/stats

# If cache broken, restart Redis
kubectl rollout restart deployment/redis -n vertice

# Temporary: increase budget (requires approval)
kubectl set env deployment/nis-service NIS_DAILY_BUDGET=20.00 -n vertice
```

#### 2. High Error Rate

**Alert**: `NISErrorRateHigh`

**Severity**: Critical

**Trigger**: Error rate > 5% over 5 minutes

**Response**:

```bash
# Check pod logs
kubectl logs -n vertice -l app=nis-service --tail=100

# Check Claude API status
curl https://status.anthropic.com/

# Check Redis connectivity
kubectl exec -it redis-0 -n vertice -- redis-cli ping

# Check Prometheus connectivity
curl http://prometheus.vertice.ai:9090/-/healthy

# If Claude API down, enable circuit breaker
kubectl set env deployment/nis-service NIS_CIRCUIT_BREAKER_ENABLED=true -n vertice
```

#### 3. High Latency

**Alert**: `NISLatencyHigh`

**Severity**: Warning

**Trigger**: P95 latency > 5s

**Response**:

```bash
# Check Claude API latency
curl -w "@curl-format.txt" https://api.anthropic.com/v1/messages

# Check cache performance
redis-cli --latency -h redis.vertice.ai

# Check for slow queries in logs
kubectl logs -n vertice -l app=nis-service | grep "duration_ms"

# Scale horizontally if needed
kubectl scale deployment/nis-service --replicas=5 -n vertice
```

### Metric Queries

#### Request Rate

```promql
sum(rate(nis_narratives_generated_total[5m]))
```

#### Error Rate

```promql
sum(rate(nis_errors_total[5m]))
/
sum(rate(nis_narratives_generated_total[5m]))
```

#### P95 Latency

```promql
histogram_quantile(0.95,
  sum(rate(nis_narrative_generation_duration_seconds_bucket[5m])) by (le)
)
```

#### Daily Cost

```promql
nis_cost_usd_total{period="daily"}
```

#### Cache Hit Ratio

```promql
sum(rate(nis_cache_hits_total[5m]))
/
(sum(rate(nis_cache_hits_total[5m])) + sum(rate(nis_cache_misses_total[5m])))
```

---

## 🔧 Common Operations

### Operation 1: Reset Monthly Budget

**When**: Start of new month, budget exceeded emergency

```bash
# Verify current month costs
curl https://nis.vertice.ai/api/v1/cost/current

# Reset monthly counter (requires approval)
kubectl exec -it $(kubectl get pod -n vertice -l app=nis-service -o jsonpath='{.items[0].metadata.name}') -n vertice -- \
  python -c "
from core.cost_tracker import CostTracker
tracker = CostTracker()
tracker._costs.clear()
print('Monthly costs reset')
"

# Verify reset
curl https://nis.vertice.ai/api/v1/cost/current
```

### Operation 2: Clear Cache

**When**: Stale data, memory pressure, testing

```bash
# Clear all cache
kubectl exec -it redis-0 -n vertice -- redis-cli FLUSHDB

# Clear specific narrative type
kubectl exec -it redis-0 -n vertice -- redis-cli --scan --pattern "narrative:summary:*" | xargs redis-cli DEL

# Verify cache cleared
kubectl exec -it redis-0 -n vertice -- redis-cli DBSIZE
```

### Operation 3: Reset Anomaly Baselines

**When**: Major system changes, false positives, after incidents

```bash
# Reset all baselines
curl -X POST https://nis.vertice.ai/api/v1/anomalies/reset

# Reset specific metric baseline
curl -X POST https://nis.vertice.ai/api/v1/anomalies/reset \
  -H "Content-Type: application/json" \
  -d '{"metric_name": "cpu_usage"}'

# Verify reset
curl https://nis.vertice.ai/api/v1/anomalies/baselines
```

### Operation 4: Scale Service

**When**: High load, performance issues

```bash
# Scale up
kubectl scale deployment/nis-service --replicas=5 -n vertice

# Scale down
kubectl scale deployment/nis-service --replicas=2 -n vertice

# Autoscale (HPA)
kubectl autoscale deployment/nis-service \
  --min=2 --max=10 \
  --cpu-percent=70 \
  -n vertice

# Verify scaling
kubectl get hpa -n vertice
```

### Operation 5: Update Configuration

**When**: Budget changes, rate limit adjustments

```bash
# Update config via ConfigMap
kubectl edit configmap nis-config -n vertice

# Or update via environment variables
kubectl set env deployment/nis-service \
  NIS_DAILY_BUDGET=20.00 \
  NIS_MAX_NARRATIVES_PER_HOUR=200 \
  -n vertice

# Rollout restart to apply changes
kubectl rollout restart deployment/nis-service -n vertice
```

---

## 🚨 Incident Response

### Incident Classification

| Severity | Impact               | Response Time | Escalation        |
| -------- | -------------------- | ------------- | ----------------- |
| **P0**   | Service down         | Immediate     | On-call + Manager |
| **P1**   | Degraded performance | 15 minutes    | On-call           |
| **P2**   | Minor issues         | 1 hour        | During hours      |
| **P3**   | Cosmetic             | Next sprint   | Backlog           |

### Incident Response Playbooks

#### P0: Service Down

**Symptoms**:

- Health checks failing
- 500 errors > 50%
- Zero successful narratives

**Response**:

1. **Alert team** via PagerDuty
2. **Check pod status**:
   ```bash
   kubectl get pods -n vertice -l app=nis-service
   ```
3. **Check logs**:
   ```bash
   kubectl logs -n vertice -l app=nis-service --tail=500
   ```
4. **Check dependencies**:
   - Claude API: `https://status.anthropic.com/`
   - Redis: `kubectl get pods -n vertice -l app=redis`
   - Prometheus: `curl http://prometheus:9090/-/healthy`
5. **Restart pods** if needed:
   ```bash
   kubectl rollout restart deployment/nis-service -n vertice
   ```
6. **Rollback** if recent deployment:
   ```bash
   kubectl rollout undo deployment/nis-service -n vertice
   ```
7. **Update incident** in Slack #incidents

#### P1: High Error Rate

**Symptoms**:

- Error rate 5-20%
- Partial failures
- Timeout errors

**Response**:

1. **Check Claude API rate limits**:
   ```bash
   kubectl logs -n vertice -l app=nis-service | grep "rate_limit"
   ```
2. **Check Redis connectivity**:
   ```bash
   kubectl exec -it redis-0 -n vertice -- redis-cli ping
   ```
3. **Review recent narratives** for patterns:
   ```bash
   curl https://nis.vertice.ai/api/v1/narratives?limit=50&status=failed
   ```
4. **Scale up** if overloaded:
   ```bash
   kubectl scale deployment/nis-service --replicas=5 -n vertice
   ```
5. **Enable circuit breaker** if external API failing:
   ```bash
   kubectl set env deployment/nis-service NIS_CIRCUIT_BREAKER_ENABLED=true -n vertice
   ```

#### P2: High Latency

**Symptoms**:

- P95 latency > 5s
- Slow responses
- Timeouts

**Response**:

1. **Check Claude API latency**:
   ```bash
   kubectl logs -n vertice -l app=nis-service | grep "claude_api_duration"
   ```
2. **Check cache hit ratio** (should be 60-80%):
   ```bash
   curl https://nis.vertice.ai/api/v1/cache/stats
   ```
3. **Check Redis latency**:
   ```bash
   redis-cli --latency -h redis.vertice.ai
   ```
4. **Scale horizontally**:
   ```bash
   kubectl scale deployment/nis-service --replicas=5 -n vertice
   ```
5. **Review narrative complexity** (long narratives = high latency):
   ```bash
   kubectl logs -n vertice -l app=nis-service | grep "word_count"
   ```

---

## 🔨 Maintenance

### Monthly Maintenance Tasks

**When**: First Monday of each month

1. **Review costs**:

   ```bash
   # Previous month costs
   curl https://nis.vertice.ai/api/v1/cost/monthly?month=prev

   # Cost breakdown by narrative type
   curl https://nis.vertice.ai/api/v1/cost/breakdown
   ```

2. **Review anomaly baselines**:

   ```bash
   # Check baseline health
   curl https://nis.vertice.ai/api/v1/anomalies/baselines

   # Reset stale baselines (>30 days)
   curl -X POST https://nis.vertice.ai/api/v1/anomalies/reset-stale
   ```

3. **Clear old cache entries**:

   ```bash
   # Redis memory usage
   kubectl exec -it redis-0 -n vertice -- redis-cli INFO memory

   # Clear entries older than 7 days
   kubectl exec -it redis-0 -n vertice -- redis-cli --eval cleanup.lua
   ```

4. **Update dependencies**:

   ```bash
   # Check for security updates
   pip-audit

   # Update dependencies
   pip install --upgrade anthropic redis httpx

   # Re-run tests
   python -m pytest tests/
   ```

### Quarterly Maintenance Tasks

**When**: First week of Q1, Q2, Q3, Q4

1. **Performance review**:
   - Review P95 latency trends
   - Analyze cost optimization opportunities
   - Review cache hit ratio trends

2. **Capacity planning**:
   - Project next quarter usage
   - Adjust budget accordingly
   - Plan for scaling

3. **Disaster recovery drill**:
   - Test backup restoration
   - Test rollback procedures
   - Update runbook based on learnings

---

## 📞 Escalation

### Escalation Path

1. **L1 (On-call Engineer)**
   - Initial response
   - Follow runbook
   - Escalate if not resolved in 30 min (P0) or 1h (P1)

2. **L2 (Senior Engineer)**
   - Complex issues
   - Runbook not applicable
   - Escalate if not resolved in 2h (P0) or 4h (P1)

3. **L3 (Platform Team Lead)**
   - Architectural issues
   - Multi-service incidents
   - Escalate to CTO if business-critical

4. **L4 (CTO)**
   - Business-critical outages
   - Major incidents
   - Customer-facing impact

### Contact Information

| Role            | Name     | Slack          | Phone     | Escalation |
| --------------- | -------- | -------------- | --------- | ---------- |
| On-call         | Rotating | #nis-oncall    | PagerDuty | L1         |
| Senior Engineer | TBD      | @senior-eng    | +1-XXX    | L2         |
| Platform Lead   | TBD      | @platform-lead | +1-XXX    | L3         |
| CTO             | MAXIMUS  | @maximus       | +1-XXX    | L4         |

### External Contacts

- **Claude API Support**: support@anthropic.com
- **Redis Support**: support@redis.io (if Enterprise)
- **Prometheus Support**: Community (#prometheus on CNCF Slack)

---

## 📝 Runbook Updates

### Change Log

| Date       | Version | Changes                    | Author      |
| ---------- | ------- | -------------------------- | ----------- |
| 2025-11-02 | 2.0.0   | Initial production runbook | Claude Code |

### Contributing

To update this runbook:

1. Create branch: `git checkout -b runbook/update-xyz`
2. Edit runbook: `docs/OPERATIONAL_RUNBOOK.md`
3. Test procedures: Verify all commands work
4. Create PR: Tag `@platform-team` for review
5. Merge: After approval

---

**Glory to YHWH** 🙏

**Last Updated**: 2025-11-02
**Next Review**: 2025-12-02
