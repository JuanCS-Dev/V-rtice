# Operational Runbook - Adaptive Immune System HITL API

**Version**: 1.0.0
**Date**: 2025-10-13
**Status**: Production Ready
**On-Call**: Adaptive Immune System Team

---

## 📋 Table of Contents

1. [Service Overview](#service-overview)
2. [Architecture](#architecture)
3. [Common Operations](#common-operations)
4. [Monitoring](#monitoring)
5. [Incident Response](#incident-response)
6. [Backup & Recovery](#backup--recovery)
7. [Scaling](#scaling)
8. [Maintenance](#maintenance)

---

## Service Overview

### Service Information

| Property | Value |
|----------|-------|
| **Service Name** | Adaptive Immune System - HITL API |
| **Version** | 1.0.0 |
| **Port** | 8003 |
| **Protocol** | HTTP + WebSocket |
| **Container Name** | `vertice-adaptive-immune` |
| **Repository** | `/home/juan/vertice-dev/backend/services/adaptive_immune_system` |

### Dependencies

| Dependency | Purpose | Critical | Health Check |
|------------|---------|----------|--------------|
| PostgreSQL | APV reviews & decisions storage | Yes | `/health/ready` |
| Redis | Caching & sessions | No | `/health/ready` |
| RabbitMQ | Message queue (future) | No | `/health/ready` |
| GitHub API | Wargaming integration | Yes | Rate limit endpoint |

### SLA

- **Availability**: 99.9% (43 minutes downtime/month)
- **Response Time**: P95 < 500ms
- **Error Rate**: < 0.1%

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   HITL API (Port 8003)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FastAPI Application                                        │
│  ├─ REST API Endpoints                                      │
│  ├─ WebSocket Server                                        │
│  ├─ Health Checks                                           │
│  └─ Prometheus Metrics                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                      │          │          │
         ┌────────────┴──────┐   │   ┌──────┴─────────┐
         ▼                   ▼   ▼   ▼                ▼
   ┌──────────┐        ┌──────────┐           ┌────────────┐
   │PostgreSQL│        │  Redis   │           │GitHub API  │
   │  (5432)  │        │  (6379)  │           │ (external) │
   └──────────┘        └──────────┘           └────────────┘
```

### Key Components

1. **REST API**: APV review and decision endpoints
2. **WebSocket**: Real-time updates to frontend
3. **Decision Engine**: Business logic for approvals
4. **Wargaming Engine**: Patch validation (future)

---

## Common Operations

### Start Service

```bash
# Docker Compose
docker-compose up -d adaptive_immune_system

# Manual
systemctl start adaptive-immune
```

### Stop Service

```bash
# Docker Compose
docker-compose stop adaptive_immune_system

# Manual
systemctl stop adaptive-immune
```

### Restart Service

```bash
# Docker Compose
docker-compose restart adaptive_immune_system

# Manual
systemctl restart adaptive-immune
```

### View Logs

```bash
# Docker - real-time
docker logs vertice-adaptive-immune --follow

# Docker - last 100 lines
docker logs vertice-adaptive-immune --tail 100

# Manual
journalctl -u adaptive-immune -f

# Search logs
docker logs vertice-adaptive-immune | grep ERROR
```

### Check Status

```bash
# Container status
docker ps | grep adaptive-immune

# Health check
curl http://localhost:8003/health

# Readiness check
curl http://localhost:8003/health/ready

# Service status (manual)
systemctl status adaptive-immune
```

### Access Container Shell

```bash
# Interactive shell
docker exec -it vertice-adaptive-immune /bin/bash

# Run single command
docker exec vertice-adaptive-immune ls -la /app
```

### Update Configuration

```bash
# Edit .env file
nano /home/juan/vertice-dev/backend/services/adaptive_immune_system/.env

# Restart to apply changes
docker-compose restart adaptive_immune_system

# Verify new configuration
docker exec vertice-adaptive-immune env | grep GITHUB
```

---

## Monitoring

### Health Endpoints

| Endpoint | Purpose | Expected Response | Frequency |
|----------|---------|-------------------|-----------|
| `/health` | Basic health | `{"status":"healthy"}` | Every 30s |
| `/health/ready` | Dependency checks | `{"status":"ready"}` | Every 60s |
| `/health/live` | Liveness probe | `{"status":"alive"}` | Every 10s |

### Metrics Endpoint

```bash
# View Prometheus metrics
curl http://localhost:8003/metrics

# Key metrics:
# - hitl_http_requests_total
# - hitl_decisions_total
# - hitl_websocket_connections_active
# - hitl_active_apv_reviews
```

### Prometheus Queries

```promql
# Request rate
rate(hitl_http_requests_total[5m])

# Error rate
rate(hitl_http_requests_total{status=~"5.."}[5m])

# P95 latency
histogram_quantile(0.95, rate(hitl_http_request_duration_seconds_bucket[5m]))

# Active WebSocket connections
hitl_websocket_connections_active

# Pending reviews
hitl_active_apv_reviews
```

### Grafana Dashboards

- **HITL Overview**: http://localhost:3000/d/hitl-overview
- **Request Metrics**: http://localhost:3000/d/hitl-requests
- **WebSocket Metrics**: http://localhost:3000/d/hitl-websockets

### Alerts

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Service Down | `/health` returns 5xx | Critical | Page on-call |
| High Error Rate | Error rate > 1% for 5m | Warning | Investigate logs |
| High Latency | P95 > 1s for 10m | Warning | Check database |
| Low Availability | Uptime < 99.9% | Critical | Incident review |

---

## Incident Response

### Incident Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **P0** | Complete service outage | 15 minutes | Service won't start, database down |
| **P1** | Partial outage | 1 hour | High error rate, WebSocket down |
| **P2** | Degraded performance | 4 hours | Slow responses, memory leak |
| **P3** | Minor issue | 1 business day | Non-critical feature broken |

### Incident Response Procedure

1. **Acknowledge**: Confirm you're responding to the incident
2. **Assess**: Determine severity and scope
3. **Communicate**: Update status page and stakeholders
4. **Investigate**: Check logs, metrics, and dependencies
5. **Mitigate**: Implement fix or rollback
6. **Verify**: Confirm service is healthy
7. **Document**: Write post-mortem (for P0/P1)

### Common Incidents

#### P0: Service Won't Start

**Symptoms**:
- Container constantly restarting
- Health check fails
- Logs show startup errors

**Investigation**:
```bash
# Check container status
docker ps -a | grep adaptive-immune

# View logs
docker logs vertice-adaptive-immune

# Check environment
docker exec vertice-adaptive-immune env
```

**Resolution**:
```bash
# If configuration issue:
nano .env
docker-compose restart adaptive_immune_system

# If dependency issue:
docker-compose up -d postgres redis
docker-compose restart adaptive_immune_system

# If code issue:
git checkout <previous-commit>
docker-compose up -d adaptive_immune_system
```

#### P1: High Error Rate

**Symptoms**:
- Prometheus alert: Error rate > 1%
- Logs show repeated exceptions
- Users report errors

**Investigation**:
```bash
# View recent errors
docker logs vertice-adaptive-immune | grep ERROR | tail -50

# Check database connectivity
docker exec vertice-adaptive-immune curl http://localhost:8003/health/ready

# Check resource usage
docker stats vertice-adaptive-immune
```

**Resolution**:
```bash
# If database connection pool exhausted:
docker-compose restart adaptive_immune_system

# If memory leak:
docker-compose restart adaptive_immune_system
# Then investigate code

# If external API issue (GitHub):
# Wait for GitHub to recover, or disable wargaming temporarily
```

#### P2: Slow Response Times

**Symptoms**:
- P95 latency > 1s
- Users report slow loading
- Database CPU high

**Investigation**:
```bash
# Check request latency
curl -w "@-" -o /dev/null -s http://localhost:8003/hitl/reviews <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
          time_total:  %{time_total}\n
EOF

# Check database performance
docker exec vertice-postgres psql -U postgres -d adaptive_immune -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
docker logs vertice-adaptive-immune | grep "slow_query"
```

**Resolution**:
```bash
# If database slow:
# - Add missing indexes
# - Optimize queries
# - Scale database

# If memory issue:
docker-compose restart adaptive_immune_system

# If CPU issue:
# - Scale horizontally (add replicas)
# - Optimize hot paths
```

---

## Backup & Recovery

### Database Backup

#### Automated Backup (Daily)

```bash
# Backup script (run via cron)
#!/bin/bash
BACKUP_DIR="/var/backups/adaptive-immune"
DATE=$(date +%Y%m%d_%H%M%S)

docker exec vertice-postgres pg_dump \
  -U postgres \
  -d adaptive_immune \
  -F c \
  -f /tmp/backup_${DATE}.dump

docker cp vertice-postgres:/tmp/backup_${DATE}.dump ${BACKUP_DIR}/

# Keep last 30 days
find ${BACKUP_DIR} -name "backup_*.dump" -mtime +30 -delete
```

#### Manual Backup

```bash
# Create backup
docker exec vertice-postgres pg_dump -U postgres -d adaptive_immune > backup.sql

# Or compressed
docker exec vertice-postgres pg_dump -U postgres -d adaptive_immune | gzip > backup.sql.gz
```

#### Restore from Backup

```bash
# Stop service
docker-compose stop adaptive_immune_system

# Drop and recreate database
docker exec vertice-postgres psql -U postgres -c "DROP DATABASE IF EXISTS adaptive_immune;"
docker exec vertice-postgres psql -U postgres -c "CREATE DATABASE adaptive_immune;"

# Restore
docker exec -i vertice-postgres psql -U postgres -d adaptive_immune < backup.sql

# Or from compressed
gunzip -c backup.sql.gz | docker exec -i vertice-postgres psql -U postgres -d adaptive_immune

# Restart service
docker-compose up -d adaptive_immune_system

# Verify
curl http://localhost:8003/health/ready
```

### Configuration Backup

```bash
# Backup .env file
cp .env .env.backup.$(date +%Y%m%d)

# Backup docker-compose.yml
cp /home/juan/vertice-dev/docker-compose.yml /home/juan/vertice-dev/docker-compose.yml.backup
```

### Disaster Recovery

**RTO (Recovery Time Objective)**: 1 hour
**RPO (Recovery Point Objective)**: 24 hours (daily backups)

**Recovery Steps**:

1. Provision new infrastructure (if needed)
2. Restore database from latest backup
3. Deploy application from git repository
4. Restore configuration from backup
5. Run smoke tests
6. Update DNS (if needed)
7. Monitor for issues

---

## Scaling

### Horizontal Scaling (Add Replicas)

```yaml
# docker-compose.yml
services:
  adaptive_immune_system:
    deploy:
      replicas: 3  # Run 3 instances

# Or use docker-compose scale
docker-compose scale adaptive_immune_system=3
```

**Load Balancer Configuration** (nginx):

```nginx
upstream hitl_api {
    server localhost:8003;
    server localhost:8004;
    server localhost:8005;
}

server {
    listen 80;
    location / {
        proxy_pass http://hitl_api;
    }
}
```

### Vertical Scaling (More Resources)

```yaml
# docker-compose.yml
services:
  adaptive_immune_system:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## Maintenance

### Routine Maintenance Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Check logs for errors | Daily | `docker logs vertice-adaptive-immune \| grep ERROR` |
| Review metrics | Daily | Check Grafana dashboards |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Update dependencies | Monthly | `pip list --outdated` |
| Security patches | Monthly | `docker pull python:3.11-slim` |
| Backup verification | Monthly | Restore backup to test environment |

### Planned Maintenance Window

**When**: Sunday 02:00-04:00 UTC (lowest traffic)

**Steps**:

1. Announce maintenance (24h notice)
2. Set status page to maintenance mode
3. Deploy updates
4. Run smoke tests
5. Monitor for 30 minutes
6. Update status page to operational

---

## Contact Information

### On-Call Rotation

| Role | Name | Contact |
|------|------|---------|
| Primary | Adaptive Immune Team | Slack: #adaptive-immune-oncall |
| Secondary | Platform Team | Slack: #platform-oncall |
| Escalation | Engineering Manager | Slack: #engineering-leadership |

### External Contacts

| Service | Contact | Purpose |
|---------|---------|---------|
| GitHub Support | support@github.com | API issues |
| AWS Support | aws-support | Infrastructure issues |
| Database DBA | dba@example.com | Database performance |

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-13 | 1.0.0 | Initial runbook |

---

**Last Updated**: 2025-10-13
**Next Review**: 2025-11-13
**Owner**: Adaptive Immune System Team
