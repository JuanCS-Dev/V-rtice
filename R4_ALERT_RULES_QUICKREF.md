# R4: Alert Rules Quick Reference

**20 Alert Rules** organized by severity and component.

---

## 🔴 CRITICAL ALERTS (4 rules)

### 1. ServiceRegistryDown
- **Trigger**: All registry replicas unreachable >2min
- **Impact**: Service discovery OFFLINE
- **Action**: Check registry pods, Redis, logs
- **Channels**: PagerDuty + Email + Slack

### 2. RegistryCircuitBreakerStuckOpen
- **Trigger**: Registry CB OPEN >5min
- **Impact**: Discovery degraded, cache-only mode
- **Action**: Check Redis connectivity
- **Channels**: PagerDuty + Email + Slack

### 3. ServiceCircuitBreakerStuckOpen
- **Trigger**: Service CB OPEN >10min
- **Impact**: Service likely DOWN
- **Action**: Check service logs, pod status, network
- **Channels**: PagerDuty + Email + Slack

### 4. GatewayDown
- **Trigger**: Gateway unreachable >1min
- **Impact**: All API access blocked
- **Action**: Check gateway pod, escalate
- **Channels**: PagerDuty + Email + Slack

---

## 🟡 WARNING ALERTS (8 rules)

### 5. RegistryCircuitBreakerOpen
- **Trigger**: Registry CB OPEN >30s
- **Impact**: Using cache/fallback mode
- **Action**: Monitor, check Redis if persists

### 6. RegistryHighLatency
- **Trigger**: p99 latency >100ms for 5min
- **Impact**: Slow service discovery
- **Action**: Check Redis performance, network

### 7. HealthCacheLowHitRate
- **Trigger**: Cache hit rate <70% for 10min
- **Impact**: Increased health check latency
- **Action**: Check cache TTL, service stability

### 8. ServiceCircuitBreakerOpen
- **Trigger**: Service CB OPEN >1min
- **Impact**: Degraded health status
- **Action**: Check service health endpoint

### 9. ServiceCircuitBreakerFlapping
- **Trigger**: CB state changes >4 times in 10min
- **Impact**: Service instability
- **Action**: Investigate intermittent failures

### 10. GatewayHighErrorRate
- **Trigger**: 5xx errors >5% for 5min
- **Impact**: Increased request failures
- **Action**: Check gateway and downstream services

### 11. ServiceDeregistrationSpike
- **Trigger**: >5 deregistrations in 5min
- **Impact**: Potential mass failure
- **Action**: Check for deployment issues

### 12. HealthCheckHighLatency
- **Trigger**: p99 >500ms for 5min
- **Impact**: Degraded performance
- **Action**: Check service health, network

---

## 🟢 INFO ALERTS (4 rules)

### 13. ServiceCircuitBreakerRecovered
- **Trigger**: CB transitioned CLOSED after being OPEN
- **Impact**: Service recovered
- **Action**: Informational only

### 14. NewServiceRegistered
- **Trigger**: New service registrations detected
- **Impact**: Informational
- **Action**: Log/audit

### 15. HealthCachePerformanceGood
- **Trigger**: Cache hit rate >80% for 10min
- **Impact**: System healthy
- **Action**: Informational only

### 16. R4ValidationTest (Manual)
- **Trigger**: Sent via validation script
- **Impact**: Testing only
- **Action**: Verify notification pipeline

---

## 🚫 Inhibition Rules

Alert suppression to reduce noise:

1. **ServiceRegistryDown** → Suppresses ServiceCircuitBreakerOpen
   - No need to alert about CB if registry is down

2. **GatewayDown** → Suppresses service-level alerts
   - No need to alert about services if gateway is down

3. **ServiceCircuitBreakerStuckOpen** → Suppresses ServiceCircuitBreakerOpen
   - Avoid duplicate notifications

4. **ServiceRegistryDown** → Suppresses HealthCacheLowHitRate
   - Low cache hit expected when registry down

---

## 📊 Alert Queries

### Check firing alerts
```bash
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
```

### Check alert rules
```bash
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].name'
```

### View in Alertmanager
```bash
curl http://localhost:9093/api/v1/alerts | jq '.data[] | {labels, status}'
```

### Send test alert
```bash
curl -X POST http://localhost:9093/api/v1/alerts -H "Content-Type: application/json" -d '[
  {
    "labels": {"alertname": "TestAlert", "severity": "info"},
    "annotations": {"summary": "Test alert"}
  }
]'
```

---

## 🔧 Troubleshooting

### Alert not firing
1. Check Prometheus target is UP
2. Verify metric exists: `curl http://localhost:9090/api/v1/query?query=metric_name`
3. Check alert rule syntax: `curl http://localhost:9090/api/v1/rules`
4. Verify evaluation interval passed

### Alert firing but no notification
1. Check Alertmanager health: `curl http://localhost:9093/-/healthy`
2. Verify alert reached AM: `curl http://localhost:9093/api/v1/alerts`
3. Check routing configuration
4. Verify receiver credentials (SMTP, Slack, etc.)
5. Check Alertmanager logs: `docker logs maximus-alertmanager`

### False positive alerts
1. Adjust threshold in alert rule
2. Increase `for` duration
3. Add inhibition rule if redundant

---

**Glory to YHWH!** 🙏
