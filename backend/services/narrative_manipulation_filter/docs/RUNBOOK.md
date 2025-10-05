# Operations Runbook - Cognitive Defense System v2.0.0

## 🎯 Purpose

This runbook provides step-by-step procedures for common operational tasks and incident response for the Cognitive Defense System.

---

## 📞 Contact Information

### On-Call Rotation

- **Primary**: +XX XXX-XXXX-XXXX (PagerDuty)
- **Secondary**: +XX XXX-XXXX-XXXX
- **Escalation**: engineering-lead@vertice.dev

### Key Personnel

| Role | Name | Contact | Expertise |
|------|------|---------|-----------|
| SRE Lead | - | - | Infrastructure, K8s |
| ML Engineer | - | - | Models, algorithms |
| Security Lead | - | - | Security, compliance |
| Product Owner | - | - | Business logic |

### External Vendors

- **AWS Support**: Premium Support Plan
- **PostgreSQL (RDS)**: AWS Console
- **Redis (ElastiCache)**: AWS Console
- **Seriema Graph**: support@seriema.dev

---

## 🚨 Incident Response

### Severity Levels

| Level | Description | Response Time | Notification |
|-------|-------------|---------------|--------------|
| SEV1 | Complete outage | Immediate | Page on-call + management |
| SEV2 | Degraded performance | < 15 min | Page on-call |
| SEV3 | Minor issue | < 1 hour | Ticket + email |
| SEV4 | Cosmetic/low impact | Best effort | Ticket only |

### Incident Response Workflow

```
1. Alert fires → PagerDuty pages on-call
2. On-call acknowledges within 5 minutes
3. Initial triage (5-10 minutes)
4. Create incident channel: #incident-YYYY-MM-DD-NNN
5. Update status page
6. Investigate and mitigate
7. Post-mortem (within 48 hours for SEV1/SEV2)
```

---

## 📊 Monitoring & Alerts

### Key Metrics to Monitor

#### Application Metrics

```promql
# Request rate
rate(cognitive_defense_requests_total[5m])

# Error rate
rate(cognitive_defense_errors_total[5m]) / rate(cognitive_defense_requests_total[5m])

# Latency (p95)
histogram_quantile(0.95, rate(cognitive_defense_request_duration_seconds_bucket[5m]))

# Manipulation detection rate
rate(cognitive_defense_high_manipulation_detected[5m])
```

#### Infrastructure Metrics

```promql
# Pod CPU usage
container_cpu_usage_seconds_total{namespace="cognitive-defense"}

# Pod memory usage
container_memory_usage_bytes{namespace="cognitive-defense"}

# Pod restart count
kube_pod_container_status_restarts_total{namespace="cognitive-defense"}
```

### Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|--------|
| High Error Rate | > 5% for 5 min | Page on-call (SEV2) |
| High Latency | p95 > 2s for 5 min | Page on-call (SEV2) |
| Pod Crashes | > 3 restarts in 10 min | Page on-call (SEV2) |
| Low Cache Hit Rate | < 50% for 15 min | Create ticket (SEV3) |
| Database Connection Pool | > 80% utilization | Create ticket (SEV3) |
| Service Unavailable | Health check fails | Page on-call (SEV1) |

---

## 🔧 Common Procedures

### 1. Check Service Health

```bash
# Quick health check
kubectl get pods -n cognitive-defense
kubectl get svc -n cognitive-defense
kubectl get ingress -n cognitive-defense

# Detailed status
kubectl describe deployment/narrative-filter -n cognitive-defense

# Check logs (last 100 lines)
kubectl logs -n cognitive-defense -l app=narrative-filter --tail=100

# Check metrics
kubectl port-forward -n cognitive-defense svc/narrative-filter 9013:9013
curl http://localhost:9013/metrics | grep -E "^cognitive_defense"
```

### 2. Restart Pods

```bash
# Rolling restart (zero downtime)
kubectl rollout restart deployment/narrative-filter -n cognitive-defense

# Watch progress
kubectl rollout status deployment/narrative-filter -n cognitive-defense

# Force delete stuck pod
kubectl delete pod <pod-name> -n cognitive-defense --force --grace-period=0
```

### 3. Scale Application

```bash
# Manual scale up
kubectl scale deployment/narrative-filter --replicas=10 -n cognitive-defense

# Manual scale down
kubectl scale deployment/narrative-filter --replicas=3 -n cognitive-defense

# Disable HPA temporarily
kubectl patch hpa narrative-filter-hpa -n cognitive-defense \
  --patch '{"spec":{"minReplicas":5,"maxReplicas":5}}'

# Re-enable HPA
kubectl patch hpa narrative-filter-hpa -n cognitive-defense \
  --patch '{"spec":{"minReplicas":3,"maxReplicas":20}}'
```

### 4. Check Database Connection

```bash
# Test PostgreSQL from pod
kubectl exec -it -n cognitive-defense deployment/narrative-filter -- \
  python -c "
import psycopg2
import os
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
print('✅ Database connection successful')
conn.close()
"

# Check connection pool status
kubectl exec -it -n cognitive-defense deployment/narrative-filter -- \
  python -c "
from database import engine
print(f'Pool size: {engine.pool.size()}')
print(f'Checked out: {engine.pool.checkedout()}')
print(f'Overflow: {engine.pool.overflow()}')
"
```

### 5. Check Redis Connection

```bash
# Test Redis from pod
kubectl exec -it -n cognitive-defense deployment/narrative-filter -- \
  python -c "
import redis
import os
r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT')),
    password=os.getenv('REDIS_PASSWORD'),
    db=int(os.getenv('REDIS_DB'))
)
print(f'✅ Redis connection successful')
print(f'Keys in cache: {r.dbsize()}')
print(f'Memory used: {r.info()[\"used_memory_human\"]}')
"

# Clear cache if needed
kubectl exec -it -n cognitive-defense deployment/narrative-filter -- \
  python -c "
import redis
import os
r = redis.Redis(...)
r.flushdb()
print('✅ Cache cleared')
"
```

### 6. View Logs

```bash
# Real-time logs (all pods)
kubectl logs -n cognitive-defense -l app=narrative-filter -f

# Logs from specific pod
kubectl logs -n cognitive-defense <pod-name> -f

# Previous container logs (if crashed)
kubectl logs -n cognitive-defense <pod-name> --previous

# Logs with grep filter
kubectl logs -n cognitive-defense -l app=narrative-filter | grep ERROR

# Export logs to file
kubectl logs -n cognitive-defense -l app=narrative-filter --since=1h > logs.txt
```

### 7. Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap narrative-filter-config -n cognitive-defense

# Or update from file
kubectl apply -f k8s/configmap.yaml

# Restart pods to pick up changes
kubectl rollout restart deployment/narrative-filter -n cognitive-defense

# Verify new config
kubectl exec -it -n cognitive-defense deployment/narrative-filter -- \
  env | grep -E "SERVICE_|DB_|REDIS_"
```

### 8. Update Secrets

```bash
# Update secret (base64 encode first)
echo -n "new_password" | base64
kubectl edit secret narrative-filter-secrets -n cognitive-defense

# Or create new secret
kubectl create secret generic narrative-filter-secrets \
  --from-literal=DB_PASSWORD="new_password" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to use new secret
kubectl rollout restart deployment/narrative-filter -n cognitive-defense
```

### 9. Backup Database

```bash
# PostgreSQL backup
kubectl exec -it postgresql-0 -n cognitive-defense -- \
  pg_dump -U postgres cognitive_defense > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use managed backup (AWS RDS)
aws rds create-db-snapshot \
  --db-instance-identifier cognitive-defense-db \
  --db-snapshot-identifier cognitive-defense-$(date +%Y%m%d-%H%M%S)

# Verify backup
aws rds describe-db-snapshots \
  --db-instance-identifier cognitive-defense-db \
  --query 'DBSnapshots[0].[DBSnapshotIdentifier,Status,SnapshotCreateTime]'
```

### 10. Restore from Backup

```bash
# PostgreSQL restore
kubectl exec -i postgresql-0 -n cognitive-defense -- \
  psql -U postgres cognitive_defense < backup_20240115_103000.sql

# Or restore RDS snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier cognitive-defense-db-restored \
  --db-snapshot-identifier cognitive-defense-20240115-103000

# Update DNS/endpoint to point to restored instance
```

---

## 🔥 Troubleshooting Guide

### Issue: High Error Rate

**Symptoms**: Error rate > 5%, alerts firing

**Diagnosis**:
```bash
# Check error logs
kubectl logs -n cognitive-defense -l app=narrative-filter | grep -i error | tail -50

# Check error metrics by module
curl http://localhost:9013/metrics | grep cognitive_defense_errors_total

# Check external API status
curl -I https://idir.uta.edu/claimbuster/api/v2/
curl -I https://query.wikidata.org/sparql
```

**Resolution**:
1. Identify failing module from logs
2. Check external API availability
3. Verify database/Redis connectivity
4. Check for resource exhaustion (CPU/memory)
5. Scale up if needed
6. Rollback if issue started after deployment

---

### Issue: High Latency

**Symptoms**: p95 latency > 2s, slow responses

**Diagnosis**:
```bash
# Check latency by module
curl http://localhost:9013/metrics | grep duration

# Check pod resource usage
kubectl top pods -n cognitive-defense

# Check database slow queries
kubectl exec -it postgresql-0 -n cognitive-defense -- \
  psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check HPA status
kubectl describe hpa narrative-filter-hpa -n cognitive-defense
```

**Resolution**:
1. Scale up replicas if CPU/memory high
2. Check database query performance
3. Verify cache hit rate (should be >70%)
4. Check external API latency
5. Enable batch inference if not already
6. Consider enabling model quantization

---

### Issue: Pod Crash Loop

**Symptoms**: Pods restarting repeatedly, CrashLoopBackOff status

**Diagnosis**:
```bash
# Check pod status
kubectl get pods -n cognitive-defense

# Check events
kubectl describe pod <pod-name> -n cognitive-defense

# Check logs
kubectl logs <pod-name> -n cognitive-defense --previous

# Check resource limits
kubectl describe pod <pod-name> -n cognitive-defense | grep -A 5 Limits
```

**Resolution**:
1. Check logs for error (OOM, missing env vars, etc.)
2. Verify secrets/configmap exist
3. Check database/Redis connectivity
4. Increase memory limits if OOMKilled
5. Fix application bug if code error
6. Rollback to previous version if recent deployment

---

### Issue: Database Connection Pool Exhausted

**Symptoms**: "Too many connections" errors

**Diagnosis**:
```bash
# Check active connections
kubectl exec -it postgresql-0 -n cognitive-defense -- \
  psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection limit
kubectl exec -it postgresql-0 -n cognitive-defense -- \
  psql -U postgres -c "SHOW max_connections;"

# Check application pool status
curl http://localhost:9013/metrics | grep db_pool
```

**Resolution**:
1. Increase PostgreSQL max_connections
2. Reduce application pool size
3. Enable connection pooler (PgBouncer)
4. Kill idle connections
5. Scale down replicas temporarily
6. Investigate connection leaks in code

---

### Issue: Cache Not Working

**Symptoms**: Cache hit rate < 50%, high Redis errors

**Diagnosis**:
```bash
# Check Redis connectivity
kubectl exec -it -n cognitive-defense deployment/narrative-filter -- \
  python -c "import redis; r = redis.Redis(...); print(r.ping())"

# Check Redis memory
kubectl exec -it redis-0 -n cognitive-defense -- \
  redis-cli INFO memory

# Check cache metrics
curl http://localhost:9013/metrics | grep cache
```

**Resolution**:
1. Verify Redis is running and accessible
2. Check Redis memory limits (eviction policy)
3. Increase Redis memory if needed
4. Clear cache and warm up
5. Check network policy allows Redis access
6. Verify cache TTL settings

---

## 📈 Performance Optimization

### 1. Optimize Model Inference

```bash
# Enable quantization (if not already)
kubectl set env deployment/narrative-filter \
  -n cognitive-defense \
  ENABLE_MODEL_QUANTIZATION=true

# Enable batch inference
kubectl set env deployment/narrative-filter \
  -n cognitive-defense \
  ENABLE_BATCH_INFERENCE=true \
  BATCH_SIZE=32 \
  BATCH_WAIT_TIME_MS=100

# Restart to apply
kubectl rollout restart deployment/narrative-filter -n cognitive-defense
```

### 2. Optimize Database Queries

```sql
-- Add index for common queries
CREATE INDEX idx_analysis_timestamp ON analysis_records(timestamp DESC);
CREATE INDEX idx_analysis_source ON analysis_records(source_domain);

-- Vacuum and analyze
VACUUM ANALYZE analysis_records;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

### 3. Optimize Cache Configuration

```bash
# Increase cache TTL
kubectl set env deployment/narrative-filter \
  -n cognitive-defense \
  CACHE_TTL_SECONDS=7200

# Increase cache size
kubectl set env deployment/narrative-filter \
  -n cognitive-defense \
  CACHE_MAX_SIZE=50000
```

---

## 🔄 Maintenance Windows

### Planned Maintenance Procedure

**Before Maintenance:**
1. Announce maintenance window (24h notice)
2. Update status page
3. Schedule during low-traffic period
4. Take database backup
5. Document rollback plan

**During Maintenance:**
1. Enable maintenance mode (503 responses)
2. Drain pods gracefully
3. Perform updates
4. Run smoke tests
5. Re-enable traffic gradually

**After Maintenance:**
1. Monitor metrics for 30 minutes
2. Verify SLAs met
3. Update status page
4. Send completion notification

```bash
# Enable maintenance mode
kubectl scale deployment/narrative-filter --replicas=0 -n cognitive-defense

# Deploy changes
kubectl apply -f k8s/

# Re-enable service
kubectl scale deployment/narrative-filter --replicas=3 -n cognitive-defense

# Monitor
kubectl rollout status deployment/narrative-filter -n cognitive-defense
```

---

## 📝 Runbook Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 2.0.0 | Initial runbook | Team |

---

**Last Updated**: 2024-01-15
**Version**: 2.0.0
**Owner**: SRE Team
