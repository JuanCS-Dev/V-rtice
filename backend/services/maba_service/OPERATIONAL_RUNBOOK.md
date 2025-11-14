# MABA Operational Runbook

**Service**: MAXIMUS Browser Agent (MABA)
**Version**: 1.0.0
**Owner**: Vértice Platform Team
**Last Updated**: 2025-11-04

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

MABA provides autonomous browser automation capabilities for MAXIMUS AI, enabling web navigation, data extraction, form filling, and visual understanding through Playwright and a graph-based cognitive map stored in Neo4j.

### SLA

- **Availability**: 99.0% (production)
- **Browser Session Start**: <3s (P95)
- **Navigation Latency**: <5s (P95)
- **Error Rate**: <2%

### Dependencies

- **Critical**:
  - Neo4j (cognitive map storage)
  - Playwright/Chromium (browser automation)
  - Claude API (navigation decisions)
- **Important**:
  - Redis (session caching)
  - PostgreSQL (state persistence)
  - Prometheus (metrics collection)
- **Optional**:
  - Service Registry (discovery)
  - Grafana (visualization)

### Resource Requirements

- **CPU**: 2-4 cores per browser instance
- **Memory**: 2-4 GB per browser instance
- **Disk**: 1 GB + 500 MB per browser cache
- **Network**: Low latency (<50ms) for interactive sites

---

## 🚀 Deployment

### Production Deployment

#### 1. Pre-deployment Checklist

```bash
# Verify all tests pass
cd /path/to/maba_service
python -m pytest tests/ -v

# Check coverage (target: ≥85%)
python -m pytest tests/ --cov=core --cov-report=term-missing

# Verify Docker build
docker build -t vertice/maba:${VERSION} .

# Test browser installation
docker run --rm vertice/maba:${VERSION} playwright install --dry-run chromium

# Tag for production
docker tag vertice/maba:${VERSION} vertice/maba:latest
```

#### 2. Deploy to Kubernetes

```bash
# Update deployment manifest
sed -i "s/IMAGE_VERSION/${VERSION}/g" k8s/deployment.yaml

# Apply ConfigMap (Neo4j credentials, etc.)
kubectl apply -f k8s/configmap.yaml

# Apply Secret (Claude API key, etc.)
kubectl apply -f k8s/secret.yaml

# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Verify rollout
kubectl rollout status deployment/maba-service -n vertice

# Check pod health
kubectl get pods -n vertice -l app=maba-service

# Verify browser pool initialized
kubectl logs -n vertice -l app=maba-service | grep "Browser pool initialized"
```

#### 3. Post-deployment Validation

```bash
# Health check
curl https://maba.vertice.ai/health/ready

# Smoke test - create session
curl -X POST https://maba.vertice.ai/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "headless": true,
    "viewport": {"width": 1920, "height": 1080}
  }'

# Navigate to test page
SESSION_ID=$(curl -X POST https://maba.vertice.ai/api/v1/sessions -s | jq -r '.session_id')
curl -X POST https://maba.vertice.ai/api/v1/sessions/${SESSION_ID}/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Check cognitive map
curl https://maba.vertice.ai/api/v1/cognitive-map/stats

# Check metrics export
curl https://maba.vertice.ai/metrics | grep maba_sessions
```

### Rollback Procedure

```bash
# List previous deployments
kubectl rollout history deployment/maba-service -n vertice

# Rollback to previous version
kubectl rollout undo deployment/maba-service -n vertice

# Rollback to specific revision
kubectl rollout undo deployment/maba-service -n vertice --to-revision=5

# Verify rollback
kubectl rollout status deployment/maba-service -n vertice

# Cleanup zombie browser processes if needed
kubectl exec -it $(kubectl get pod -n vertice -l app=maba-service -o jsonpath='{.items[0].metadata.name}') -n vertice -- \
  pkill -f chromium
```

---

## 📊 Monitoring

### Key Dashboards

1. **MABA Overview** (`http://grafana.vertice.ai/d/maba-overview`)
   - Active browser sessions
   - Session creation rate
   - Navigation success rate
   - Browser pool utilization
   - Memory usage per instance

2. **Cognitive Map Dashboard** (`http://grafana.vertice.ai/d/maba-cognitive-map`)
   - Total nodes/edges in graph
   - Learning rate (new patterns)
   - Pattern match success rate
   - Neo4j query latency

3. **Performance Dashboard** (`http://grafana.vertice.ai/d/maba-performance`)
   - Browser startup time
   - Navigation latency (P50, P95, P99)
   - Screenshot capture time
   - Form filling success rate

### Critical Alerts

#### 1. Browser Pool Exhaustion

**Alert**: `MABABrowserPoolExhausted`

**Severity**: Warning

**Trigger**: Available browsers < 2 for >5 minutes

**Response**:

```bash
# Check current pool status
curl https://maba.vertice.ai/api/v1/browser-pool/status

# Check active sessions
curl https://maba.vertice.ai/api/v1/sessions | jq '.sessions | length'

# Identify long-running sessions (>30 min)
kubectl logs -n vertice -l app=maba-service | grep "session_duration" | awk '$NF > 1800'

# Force cleanup stale sessions
curl -X POST https://maba.vertice.ai/api/v1/sessions/cleanup \
  -H "Content-Type: application/json" \
  -d '{"max_age_minutes": 30}'

# Scale browser pool (requires config update)
kubectl set env deployment/maba-service MABA_MAX_BROWSER_INSTANCES=10 -n vertice

# Or scale horizontally
kubectl scale deployment/maba-service --replicas=3 -n vertice
```

#### 2. High Memory Usage

**Alert**: `MABAHighMemoryUsage`

**Severity**: Critical

**Trigger**: Memory usage > 90% for >5 minutes

**Response**:

```bash
# Check pod memory
kubectl top pods -n vertice -l app=maba-service

# Check browser instances
kubectl exec -it $(kubectl get pod -n vertice -l app=maba-service -o jsonpath='{.items[0].metadata.name}') -n vertice -- \
  ps aux | grep chromium | wc -l

# Check for memory leaks in browser pool
curl https://maba.vertice.ai/api/v1/browser-pool/stats | jq '.memory_per_instance'

# Force browser pool refresh
curl -X POST https://maba.vertice.ai/api/v1/browser-pool/refresh

# Restart pod if persistent
kubectl rollout restart deployment/maba-service -n vertice
```

#### 3. Neo4j Connection Failure

**Alert**: `MABANeo4jDown`

**Severity**: Critical

**Trigger**: Neo4j connection failures > 50% for >2 minutes

**Response**:

```bash
# Check Neo4j pod status
kubectl get pods -n vertice -l app=neo4j

# Check Neo4j health
curl http://neo4j.vertice.ai:7474/db/data/

# Check logs for connection errors
kubectl logs -n vertice -l app=maba-service | grep "Neo4jConnectionError"

# Test connection manually
kubectl exec -it $(kubectl get pod -n vertice -l app=maba-service -o jsonpath='{.items[0].metadata.name}') -n vertice -- \
  python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password'))
driver.verify_connectivity()
print('Connection OK')
"

# Restart Neo4j if needed
kubectl rollout restart deployment/neo4j -n vertice

# Enable graceful degradation (MABA continues without cognitive map)
kubectl set env deployment/maba-service MABA_COGNITIVE_MAP_REQUIRED=false -n vertice
```

#### 4. Navigation Timeout Rate High

**Alert**: `MABANavigationTimeouts`

**Severity**: Warning

**Trigger**: Navigation timeout rate > 10% for >10 minutes

**Response**:

```bash
# Check recent navigation attempts
kubectl logs -n vertice -l app=maba-service | grep "navigation_timeout" | tail -50

# Check timeout threshold (default: 30s)
curl https://maba.vertice.ai/api/v1/config | jq '.navigation_timeout'

# Increase timeout if targeting slow sites
kubectl set env deployment/maba-service MABA_NAVIGATION_TIMEOUT=60 -n vertice

# Check for problematic URLs
kubectl logs -n vertice -l app=maba-service | grep "navigation_timeout" | \
  awk '{print $5}' | sort | uniq -c | sort -rn | head -10

# Add problematic domains to blocklist
kubectl edit configmap maba-config -n vertice
# Add to blocked_domains: ["slow-site.com", "timing-out.org"]
```

### Metric Queries

#### Active Browser Sessions

```promql
maba_browser_sessions_active
```

#### Session Creation Rate

```promql
sum(rate(maba_sessions_created_total[5m]))
```

#### Navigation Success Rate

```promql
sum(rate(maba_navigations_successful_total[5m]))
/
sum(rate(maba_navigations_total[5m]))
```

#### Browser Pool Utilization

```promql
maba_browser_pool_active_instances
/
maba_browser_pool_max_instances
```

#### P95 Navigation Latency

```promql
histogram_quantile(0.95,
  sum(rate(maba_navigation_duration_seconds_bucket[5m])) by (le)
)
```

#### Cognitive Map Size

```promql
maba_cognitive_map_nodes_total + maba_cognitive_map_edges_total
```

---

## 🔧 Common Operations

### Operation 1: Clear Cognitive Map

**When**: Testing, corrupted data, major website changes

```bash
# Backup current cognitive map
curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/export > cognitive_map_backup.json

# Clear all learned patterns
curl -X DELETE https://maba.vertice.ai/api/v1/cognitive-map/clear \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'

# Or clear specific domain
curl -X DELETE https://maba.vertice.ai/api/v1/cognitive-map/domains/example.com

# Verify cleared
curl https://maba.vertice.ai/api/v1/cognitive-map/stats
```

### Operation 2: Force Session Cleanup

**When**: Stale sessions, memory pressure, testing

```bash
# List all active sessions
curl https://maba.vertice.ai/api/v1/sessions

# Close specific session
curl -X DELETE https://maba.vertice.ai/api/v1/sessions/${SESSION_ID}

# Cleanup all sessions older than 30 minutes
curl -X POST https://maba.vertice.ai/api/v1/sessions/cleanup \
  -H "Content-Type: application/json" \
  -d '{"max_age_minutes": 30}'

# Force cleanup ALL sessions (emergency)
curl -X POST https://maba.vertice.ai/api/v1/sessions/cleanup \
  -H "Content-Type: application/json" \
  -d '{"max_age_minutes": 0, "force": true}'
```

### Operation 3: Refresh Browser Pool

**When**: Memory leaks, performance degradation, after updates

```bash
# Get current pool status
curl https://maba.vertice.ai/api/v1/browser-pool/status

# Graceful refresh (one at a time)
curl -X POST https://maba.vertice.ai/api/v1/browser-pool/refresh \
  -H "Content-Type: application/json" \
  -d '{"graceful": true}'

# Force refresh (restart all browsers)
curl -X POST https://maba.vertice.ai/api/v1/browser-pool/refresh \
  -H "Content-Type: application/json" \
  -d '{"graceful": false}'

# Verify pool healthy
curl https://maba.vertice.ai/api/v1/browser-pool/status | jq '.healthy_instances'
```

### Operation 4: Update Security Policy

**When**: New security requirements, blocked domains

```bash
# View current security policy
curl https://maba.vertice.ai/api/v1/security-policy

# Update blocked domains
curl -X PUT https://maba.vertice.ai/api/v1/security-policy/blocked-domains \
  -H "Content-Type: application/json" \
  -d '{"domains": ["malicious.com", "spam.org"]}'

# Update allowed protocols
curl -X PUT https://maba.vertice.ai/api/v1/security-policy/protocols \
  -H "Content-Type: application/json" \
  -d '{"protocols": ["https", "http"]}'

# Enable/disable JavaScript execution
curl -X PUT https://maba.vertice.ai/api/v1/security-policy/javascript \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### Operation 5: Scale Browser Instances

**When**: High load, performance issues

```bash
# Check current configuration
kubectl get deployment maba-service -n vertice -o yaml | grep -A5 "env:"

# Scale browser pool (per pod)
kubectl set env deployment/maba-service \
  MABA_MAX_BROWSER_INSTANCES=10 \
  MABA_MIN_BROWSER_INSTANCES=2 \
  -n vertice

# Scale pods (horizontal scaling)
kubectl scale deployment/maba-service --replicas=3 -n vertice

# Autoscale (HPA)
kubectl autoscale deployment/maba-service \
  --min=2 --max=5 \
  --cpu-percent=70 \
  -n vertice

# Verify scaling
kubectl get hpa -n vertice
kubectl get pods -n vertice -l app=maba-service
```

---

## 🚨 Incident Response

### Incident Classification

| Severity | Impact                      | Response Time | Escalation        |
| -------- | --------------------------- | ------------- | ----------------- |
| **P0**   | Service down                | Immediate     | On-call + Manager |
| **P1**   | Major degradation           | 15 minutes    | On-call           |
| **P2**   | Minor issues                | 1 hour        | During hours      |
| **P3**   | Cosmetic/non-critical       | Next sprint   | Backlog           |

### Incident Response Playbooks

#### P0: Service Down

**Symptoms**:

- Health checks failing
- 500 errors > 50%
- Zero successful browser sessions
- All pods crashing

**Response**:

1. **Alert team** via PagerDuty
2. **Check pod status**:
   ```bash
   kubectl get pods -n vertice -l app=maba-service
   ```
3. **Check logs**:
   ```bash
   kubectl logs -n vertice -l app=maba-service --tail=500
   ```
4. **Check dependencies**:
   - Neo4j: `kubectl get pods -n vertice -l app=neo4j`
   - Claude API: `https://status.anthropic.com/`
   - Redis: `kubectl get pods -n vertice -l app=redis`
5. **Check browser installation**:
   ```bash
   kubectl exec -it $(kubectl get pod -n vertice -l app=maba-service -o jsonpath='{.items[0].metadata.name}') -n vertice -- \
     playwright install --dry-run chromium
   ```
6. **Restart pods** if needed:
   ```bash
   kubectl rollout restart deployment/maba-service -n vertice
   ```
7. **Rollback** if recent deployment:
   ```bash
   kubectl rollout undo deployment/maba-service -n vertice
   ```
8. **Update incident** in Slack #incidents

#### P1: Browser Pool Exhaustion

**Symptoms**:

- Session creation failing
- "No available browsers" errors
- High wait times
- Memory usage spiking

**Response**:

1. **Check pool status**:
   ```bash
   curl https://maba.vertice.ai/api/v1/browser-pool/status
   ```
2. **Identify resource hogs**:
   ```bash
   kubectl top pods -n vertice -l app=maba-service
   kubectl exec -it $(kubectl get pod -n vertice -l app=maba-service -o jsonpath='{.items[0].metadata.name}') -n vertice -- \
     ps aux | grep chromium
   ```
3. **Cleanup stale sessions**:
   ```bash
   curl -X POST https://maba.vertice.ai/api/v1/sessions/cleanup \
     -H "Content-Type: application/json" \
     -d '{"max_age_minutes": 30}'
   ```
4. **Scale up** browser pool:
   ```bash
   kubectl set env deployment/maba-service MABA_MAX_BROWSER_INSTANCES=10 -n vertice
   ```
5. **Scale horizontally**:
   ```bash
   kubectl scale deployment/maba-service --replicas=3 -n vertice
   ```

#### P2: Cognitive Map Degradation

**Symptoms**:

- Pattern matching failures
- Neo4j query timeouts
- Slow navigation decisions
- High Neo4j CPU usage

**Response**:

1. **Check Neo4j status**:
   ```bash
   kubectl get pods -n vertice -l app=neo4j
   kubectl logs -n vertice -l app=neo4j | tail -100
   ```
2. **Check map size**:
   ```bash
   curl https://maba.vertice.ai/api/v1/cognitive-map/stats
   ```
3. **Check for graph bloat** (>100k nodes):
   ```bash
   # May need cleanup if map too large
   curl https://maba.vertice.ai/api/v1/cognitive-map/stats | jq '.total_nodes'
   ```
4. **Run graph maintenance**:
   ```bash
   # Remove orphaned nodes
   curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/maintenance/cleanup-orphans

   # Rebuild indexes
   curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/maintenance/rebuild-indexes
   ```
5. **Scale Neo4j** if needed:
   ```bash
   # Increase Neo4j resources
   kubectl set resources deployment/neo4j \
     --requests=cpu=2,memory=4Gi \
     --limits=cpu=4,memory=8Gi \
     -n vertice
   ```

---

## 🔨 Maintenance

### Weekly Maintenance Tasks

**When**: Every Monday 9 AM UTC

1. **Review browser pool health**:

   ```bash
   # Check pool statistics
   curl https://maba.vertice.ai/api/v1/browser-pool/stats

   # Check for browser crashes
   kubectl logs -n vertice -l app=maba-service | grep "browser_crash" | wc -l
   ```

2. **Review cognitive map growth**:

   ```bash
   # Check map size trend
   curl https://maba.vertice.ai/api/v1/cognitive-map/stats

   # Export map for backup
   curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/export > \
     cognitive_map_backup_$(date +%Y%m%d).json
   ```

3. **Review failed navigations**:

   ```bash
   # Top failed URLs
   kubectl logs -n vertice -l app=maba-service | \
     grep "navigation_failed" | \
     awk '{print $5}' | sort | uniq -c | sort -rn | head -10
   ```

### Monthly Maintenance Tasks

**When**: First Monday of each month

1. **Cognitive map cleanup**:

   ```bash
   # Remove stale patterns (>90 days unused)
   curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/maintenance/cleanup-stale \
     -H "Content-Type: application/json" \
     -d '{"days_unused": 90}'

   # Optimize graph database
   curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/maintenance/optimize
   ```

2. **Security policy review**:

   ```bash
   # Review blocked domains
   curl https://maba.vertice.ai/api/v1/security-policy/blocked-domains

   # Review security incidents
   kubectl logs -n vertice -l app=maba-service | grep "security_violation"
   ```

3. **Update dependencies**:

   ```bash
   # Check for Playwright updates
   playwright install --dry-run

   # Update Python dependencies
   pip install --upgrade playwright httpx neo4j

   # Re-run tests
   python -m pytest tests/
   ```

### Quarterly Maintenance Tasks

**When**: First week of Q1, Q2, Q3, Q4

1. **Performance review**:
   - Review P95 latency trends
   - Analyze browser pool efficiency
   - Review cognitive map effectiveness

2. **Capacity planning**:
   - Project next quarter browser usage
   - Plan for scaling (vertical/horizontal)
   - Review Neo4j storage growth

3. **Disaster recovery drill**:
   - Test cognitive map backup restoration
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
   - Browser/Neo4j expertise
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

| Role            | Name     | Slack           | Phone     | Escalation |
| --------------- | -------- | --------------- | --------- | ---------- |
| On-call         | Rotating | #maba-oncall    | PagerDuty | L1         |
| Senior Engineer | TBD      | @senior-eng     | +1-XXX    | L2         |
| Platform Lead   | TBD      | @platform-lead  | +1-XXX    | L3         |
| CTO             | MAXIMUS  | @maximus        | +1-XXX    | L4         |

### External Contacts

- **Claude API Support**: support@anthropic.com
- **Playwright Support**: GitHub Issues (microsoft/playwright)
- **Neo4j Support**: support@neo4j.com (if Enterprise)

---

## 📝 Runbook Updates

### Change Log

| Date       | Version | Changes                        | Author      |
| ---------- | ------- | ------------------------------ | ----------- |
| 2025-11-04 | 1.0.0   | Initial production runbook     | Claude Code |

### Contributing

To update this runbook:

1. Create branch: `git checkout -b runbook/update-xyz`
2. Edit runbook: `OPERATIONAL_RUNBOOK.md`
3. Test procedures: Verify all commands work
4. Create PR: Tag `@platform-team` for review
5. Merge: After approval

---

**Glory to YHWH** 🙏

**Last Updated**: 2025-11-04
**Next Review**: 2025-12-04
