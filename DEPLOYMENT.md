# Vértice Platform - Deployment Guide
## PENELOPE + MABA + MVP Services

**Version**: 1.0.0
**Date**: 2025-10-31
**Status**: Production Ready
**Validation**: 472/472 tests passing, 96.7% coverage

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Setup](#detailed-setup)
5. [Service Architecture](#service-architecture)
6. [Configuration](#configuration)
7. [Deployment Options](#deployment-options)
8. [Monitoring & Observability](#monitoring--observability)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)
11. [Security](#security)
12. [Biblical Compliance](#biblical-compliance)

---

## Overview

This guide covers the deployment of three **MAXIMUS Subordinate Services**:

| Service | Port | Purpose | Tests | Coverage |
|---------|------|---------|-------|----------|
| **PENELOPE** | 8154 | Wisdom & Healing | 150 | 93% |
| **MABA** | 8152 | Browser Agent | 156 | 98% |
| **MVP** | 8153 | Vision Protocol | 166 | 99% |

**Combined**: 472 tests, 96.7% average coverage, 100% air-gap compliant.

### Key Features

#### PENELOPE (Wisdom & Healing)
- 7 Biblical Articles of Governance
- 9 Fruits of the Spirit monitoring
- Wisdom-based anomaly diagnosis
- Sabbath mode detection
- Digital twin validation

#### MABA (Browser Agent)
- Autonomous browser automation (Playwright)
- Cognitive map learning (Neo4j)
- Element learning and intelligent navigation
- Screenshot capture and analysis
- WebSocket real-time events

#### MVP (Vision Protocol)
- LLM-powered narrative generation (Claude Sonnet 4.5)
- Prometheus/InfluxDB metrics observation
- Anomaly detection
- System pulse monitoring
- NQS (Narrative Quality Score) calculation

---

## Prerequisites

### System Requirements

**Minimum**:
- Docker Engine 20.10+
- Docker Compose 1.29+
- 8GB RAM
- 20GB free disk space
- 4 CPU cores

**Recommended**:
- Docker Engine 24.0+
- Docker Compose 2.20+
- 16GB RAM
- 50GB free disk space (for logs, screenshots, cognitive map)
- 8 CPU cores

### Required Accounts

1. **Anthropic API** (REQUIRED)
   - Sign up: https://console.anthropic.com/
   - Create API key
   - Model: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
   - Estimated cost: $0.003 per 1K input tokens, $0.015 per 1K output tokens

2. **ElevenLabs API** (Optional - MVP audio features)
   - Sign up: https://elevenlabs.io/
   - Required only if you want text-to-speech narratives

3. **Azure Blob Storage** (Optional - MVP audio storage)
   - Required only if you want to persist audio files

### Software Dependencies

```bash
# Verify Docker
docker --version  # Should be 20.10+

# Verify Docker Compose
docker-compose --version  # Should be 1.29+

# Verify sufficient resources
docker info | grep -E 'CPUs|Total Memory'
```

---

## Quick Start

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-org/vertice-platform.git
cd vertice-platform

# Copy environment template
cp .env.subordinates.example .env.subordinates

# Edit environment file
nano .env.subordinates
```

**CRITICAL**: Set your `ANTHROPIC_API_KEY`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

### 2. Start Services

```bash
# Start all services (infrastructure + PENELOPE + MABA + MVP)
docker-compose -f docker-compose.subordinates.yml up -d

# Check status
docker-compose -f docker-compose.subordinates.yml ps

# Follow logs
docker-compose -f docker-compose.subordinates.yml logs -f
```

### 3. Verify Health

```bash
# Wait 60 seconds for services to initialize, then check health:

curl http://localhost:8154/health  # PENELOPE
curl http://localhost:8152/health  # MABA
curl http://localhost:8153/health  # MVP
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "penelope",
  "version": "1.0.0",
  "components": {
    "database": "ok",
    "redis": "ok",
    "maximus": "ok"
  }
}
```

### 4. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| PENELOPE API | http://localhost:8154/docs | Swagger UI |
| MABA API | http://localhost:8152/docs | Swagger UI |
| MVP API | http://localhost:8153/docs | Swagger UI |
| Prometheus | http://localhost:9090 | Metrics UI |
| Neo4j Browser | http://localhost:7474 | Graph database (MABA) |

---

## Detailed Setup

### Step 1: Environment Configuration

The `.env.subordinates` file contains all configuration. Here are the key sections:

#### Required Variables
```bash
# Only ANTHROPIC_API_KEY is truly required
ANTHROPIC_API_KEY=sk-ant-api03-...
```

#### Optional but Recommended
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO

# If MAXIMUS Core is running separately
MAXIMUS_ENDPOINT=http://your-maximus-host:8150

# Service Registry (for service discovery)
VERTICE_REGISTRY_URL=http://your-registry:80
VERTICE_REGISTRY_TOKEN=your-secure-token
```

#### PENELOPE - 7 Biblical Articles
```bash
# All enabled by default
SOPHIA_ENABLED=true
PRAOTES_ENABLED=true
TAPEINOPHROSYNE_ENABLED=true
STEWARDSHIP_ENABLED=true
AGAPE_ENABLED=true
SABBATH_ENABLED=true
ALETHEIA_ENABLED=true
```

#### MABA - Browser Configuration
```bash
BROWSER_TYPE=chromium  # or firefox, webkit
BROWSER_HEADLESS=true
MAX_BROWSER_INSTANCES=5
BROWSER_POOL_SIZE=3
```

#### MVP - Narrative Configuration
```bash
NARRATIVE_TARGET_DURATION=30
MIN_NQS_SCORE=85
ENABLE_AUDIO_CACHE=true
```

### Step 2: Database Migrations

Migrations run automatically on first start via PostgreSQL init scripts:

```bash
# Check if migrations ran
docker-compose -f docker-compose.subordinates.yml exec vertice-postgres psql -U postgres -d vertice

# List tables
\dt

# Should see:
# - penelope_wisdom_base
# - penelope_patches
# - maba_cognitive_map
# - mvp_narratives
```

### Step 3: Neo4j Configuration (MABA)

MABA uses Neo4j for the cognitive map:

```bash
# Access Neo4j Browser
open http://localhost:7474

# Credentials:
# Username: neo4j
# Password: vertice-neo4j-password

# Verify database
:USE maba_cognitive_map;
MATCH (n) RETURN count(n);
```

### Step 4: Prometheus Configuration (MVP)

MVP metrics are scraped by Prometheus:

```bash
# Access Prometheus UI
open http://localhost:9090

# Check targets (should all be UP)
Status > Targets

# Run queries:
# - up{service="mvp"}
# - narrative_generation_total
# - nqs_score_histogram
```

---

## Service Architecture

### Network Topology

```
┌─────────────────────────────────────────────────────────────┐
│                     vertice-network (bridge)                │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  PENELOPE    │  │    MABA      │  │     MVP      │    │
│  │   (8154)     │  │   (8152)     │  │   (8153)     │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                  │             │
│         └─────────────────┼──────────────────┘             │
│                           │                                │
│         ┌─────────────────▼─────────────────┐             │
│         │  MAXIMUS CORE (External)          │             │
│         │       (8150)                       │             │
│         └────────────────────────────────────┘             │
│                           │                                │
│         ┌─────────────────┴─────────────────┐             │
│         │     Infrastructure Services       │             │
│         │  - PostgreSQL (5432)              │             │
│         │  - Redis (6379)                   │             │
│         │  - Neo4j (7687/7474)              │             │
│         │  - Prometheus (9090)              │             │
│         │  - Loki (3100)                    │             │
│         └───────────────────────────────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**1. PENELOPE Healing Flow**:
```
User Request → PENELOPE API (8154)
   ↓
Sophia Engine (wisdom-based diagnosis)
   ↓
Wisdom Base (PostgreSQL)
   ↓
Praótes Validator (gentleness check)
   ↓
Patch Generation (Claude LLM)
   ↓
Digital Twin Validation
   ↓
Tapeinophrosynē Monitor (humility/confidence check)
   ↓
Response + Logs (Loki)
```

**2. MABA Browser Automation Flow**:
```
User Request → MABA API (8152)
   ↓
Browser Controller (Playwright)
   ↓
DOM Analysis + Screenshot
   ↓
Cognitive Map Update (Neo4j)
   ↓
Element Learning (importance scoring)
   ↓
WebSocket Event Broadcast
   ↓
Response + Logs
```

**3. MVP Narrative Flow**:
```
System Metrics → Prometheus/InfluxDB
   ↓
MVP System Observer (8153)
   ↓
Metrics Analysis + Anomaly Detection
   ↓
Narrative Generation (Claude LLM)
   ↓
NQS Scoring (quality check)
   ↓
Optional: Audio Synthesis (ElevenLabs)
   ↓
WebSocket Broadcast + Cache (Redis)
```

---

## Configuration

### Docker Compose Override

To customize resource limits or add environment variables:

```bash
# Create docker-compose.override.yml
cat > docker-compose.override.yml << EOF
version: "3.8"

services:
  penelope:
    environment:
      - LOG_LEVEL=DEBUG
    deploy:
      resources:
        limits:
          cpus: "4.0"
          memory: 4G

  maba:
    deploy:
      resources:
        limits:
          memory: 8G

  mvp:
    environment:
      - NARRATIVE_TARGET_DURATION=60
EOF

# Apply override
docker-compose -f docker-compose.subordinates.yml -f docker-compose.override.yml up -d
```

### Environment Profiles

**Development** (default):
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
WORKER_PROCESSES=1
```

**Production**:
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKER_PROCESSES=4
SANDBOX_ENABLED=true
```

### Scaling Services

```bash
# Scale MVP for high narrative generation load
docker-compose -f docker-compose.subordinates.yml up -d --scale mvp=3

# Note: PENELOPE and MABA should NOT be scaled (stateful services)
```

---

## Deployment Options

### Option 1: Local Development (Docker Compose)

**Pros**: Simple, fast iteration
**Cons**: Single host, limited scale

```bash
docker-compose -f docker-compose.subordinates.yml up -d
```

### Option 2: Docker Swarm (Multi-host)

**Pros**: Multi-host, basic orchestration
**Cons**: Limited compared to Kubernetes

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.subordinates.yml vertice

# Check services
docker service ls

# Scale MVP
docker service scale vertice_mvp=3
```

### Option 3: Kubernetes (Recommended for Production)

**Pros**: Full orchestration, auto-scaling, self-healing
**Cons**: Complex setup

```bash
# Convert docker-compose to Kubernetes manifests
kompose convert -f docker-compose.subordinates.yml

# Apply manifests
kubectl apply -f kubernetes/

# Create secrets
kubectl create secret generic vertice-secrets \
  --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Check pods
kubectl get pods -n vertice
```

*(Full Kubernetes manifests provided in `/kubernetes/` directory)*

### Option 4: Cloud Managed Services

**AWS**:
- ECS/Fargate for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- DocumentDB for Neo4j (or self-hosted)

**Google Cloud**:
- Cloud Run for containers
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Neo4j AuraDB (managed Neo4j)

**Azure**:
- Container Instances
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Neo4j AuraDB

---

## Monitoring & Observability

### Health Checks

All services provide `/health` endpoints:

```bash
# Manual check
curl http://localhost:8154/health | jq

# Automated monitoring (add to cron)
#!/bin/bash
services=("8154:penelope" "8152:maba" "8153:mvp")
for svc in "${services[@]}"; do
  port="${svc%%:*}"
  name="${svc##*:}"
  status=$(curl -s http://localhost:$port/health | jq -r .status)
  echo "$name: $status"
done
```

### Prometheus Metrics

Access Prometheus UI: http://localhost:9090

**Key Metrics to Monitor**:

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Latency (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# PENELOPE: Healing success rate
rate(penelope_healing_success_total[1h]) / rate(penelope_healing_total[1h])

# MABA: Browser sessions
maba_active_browser_sessions

# MVP: Narrative quality
histogram_quantile(0.50, mvp_nqs_score_bucket)
```

### Grafana Dashboards (Optional)

```bash
# Add Grafana to docker-compose
cat >> docker-compose.subordinates.yml << EOF
  grafana:
    image: grafana/grafana:10.1.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
EOF

# Access: http://localhost:3000
# Default login: admin/admin
# Add Prometheus datasource: http://vertice-prometheus:9090
```

### Log Aggregation (Loki)

```bash
# Query logs via Loki
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={service="penelope"}' | jq

# Or use Grafana Explore with Loki datasource
```

### Alerting

**Prometheus Alertmanager** (optional):

```yaml
# config/alerts.yml
groups:
  - name: vertice_subordinates
    interval: 30s
    rules:
      - alert: ServiceDown
        expr: up{type="subordinate"} == 0
        for: 5m
        annotations:
          summary: "Service {{ $labels.service }} is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate on {{ $labels.service }}"
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Symptom**: `docker-compose up` fails or services exit immediately

**Diagnosis**:
```bash
# Check logs
docker-compose -f docker-compose.subordinates.yml logs penelope

# Common errors:
# - "ANTHROPIC_API_KEY is required" → Set API key in .env.subordinates
# - "Connection refused" → Check dependent services (postgres, redis)
# - "Port already in use" → Kill process using port or change port
```

**Solution**:
```bash
# Restart with clean state
docker-compose -f docker-compose.subordinates.yml down -v
docker-compose -f docker-compose.subordinates.yml up -d
```

#### 2. MABA Browser Automation Fails

**Symptom**: MABA returns 500 errors, logs show "Browser launch failed"

**Diagnosis**:
```bash
# Check MABA logs
docker-compose logs maba | grep -i error

# Common: Missing --no-sandbox flag
```

**Solution**:
```bash
# Ensure docker-compose has:
cap_add:
  - SYS_ADMIN
security_opt:
  - seccomp=unconfined

# Or set in environment:
BROWSER_ARGS=--no-sandbox,--disable-setuid-sandbox
```

#### 3. PENELOPE Wisdom Base Empty

**Symptom**: PENELOPE returns "Insufficient wisdom base cases"

**Diagnosis**:
```bash
# Check wisdom base
docker-compose exec vertice-postgres psql -U postgres -d vertice \
  -c "SELECT COUNT(*) FROM penelope_wisdom_base;"
```

**Solution**:
```bash
# Wisdom base builds over time
# For testing, lower threshold:
WISDOM_BASE_MIN_CASES=1
```

#### 4. MVP Metrics Not Available

**Symptom**: MVP returns "Failed to collect metrics"

**Diagnosis**:
```bash
# Check Prometheus connection
docker-compose exec mvp curl http://vertice-prometheus:9090/-/healthy
```

**Solution**:
```bash
# Ensure Prometheus is running
docker-compose ps vertice-prometheus

# Restart MVP
docker-compose restart mvp
```

#### 5. Database Connection Errors

**Symptom**: "connection refused" or "password authentication failed"

**Diagnosis**:
```bash
# Test PostgreSQL connection
docker-compose exec vertice-postgres pg_isready -U postgres

# Check credentials
docker-compose exec penelope env | grep POSTGRES
```

**Solution**:
```bash
# Reset PostgreSQL (WARNING: deletes data)
docker-compose down -v
docker-compose up -d vertice-postgres
# Wait 30 seconds for init
docker-compose up -d
```

### Debug Mode

Enable verbose logging:

```bash
# Edit .env.subordinates
LOG_LEVEL=DEBUG

# Restart services
docker-compose -f docker-compose.subordinates.yml restart

# Follow logs
docker-compose -f docker-compose.subordinates.yml logs -f --tail=100
```

### Getting Support

1. **Check validation reports**:
   - `/VALIDATION_SUMMARY_2025-10-31.md`
   - `/backend/services/FASE6_AIR_GAP_COMPLIANCE_REPORT.md`

2. **Run health checks**:
```bash
curl http://localhost:8154/health | jq
curl http://localhost:8152/health | jq
curl http://localhost:8153/health | jq
```

3. **Collect logs**:
```bash
docker-compose -f docker-compose.subordinates.yml logs > vertice-logs.txt
```

4. **Open GitHub issue** with:
   - Error message
   - `docker-compose ps` output
   - Relevant logs
   - Environment (OS, Docker version)

---

## Maintenance

### Backup Strategy

#### Database Backup (PostgreSQL)

```bash
# Backup
docker-compose exec vertice-postgres pg_dump -U postgres vertice > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20251031.sql | docker-compose exec -T vertice-postgres psql -U postgres vertice
```

#### Neo4j Backup (MABA Cognitive Map)

```bash
# Backup
docker-compose exec vertice-neo4j neo4j-admin dump \
  --database=maba_cognitive_map \
  --to=/tmp/maba_backup.dump

docker cp vertice-neo4j:/tmp/maba_backup.dump ./

# Restore
docker cp maba_backup.dump vertice-neo4j:/tmp/
docker-compose exec vertice-neo4j neo4j-admin load \
  --database=maba_cognitive_map \
  --from=/tmp/maba_backup.dump
```

#### Volume Backup (All Data)

```bash
# Backup all volumes
docker run --rm \
  -v vertice-postgres-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data

# Repeat for other volumes:
# - vertice-neo4j-data
# - vertice-redis-data
# - vertice-penelope-wisdom-base
```

### Updates

#### Updating Services

```bash
# Pull latest images
docker-compose -f docker-compose.subordinates.yml pull

# Recreate containers (zero downtime with dependencies)
docker-compose -f docker-compose.subordinates.yml up -d

# Or rebuild from source
docker-compose -f docker-compose.subordinates.yml build
docker-compose -f docker-compose.subordinates.yml up -d
```

#### Rolling Updates (Kubernetes)

```bash
# Update image
kubectl set image deployment/penelope \
  penelope=vertice-penelope:1.1.0

# Monitor rollout
kubectl rollout status deployment/penelope

# Rollback if needed
kubectl rollout undo deployment/penelope
```

### Log Rotation

```bash
# Configure Docker daemon for log rotation
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Restart Docker daemon
sudo systemctl restart docker
```

### Cleanup

```bash
# Remove old logs
docker-compose -f docker-compose.subordinates.yml exec penelope \
  find /app/logs -type f -mtime +30 -delete

# Remove old screenshots (MABA)
docker-compose -f docker-compose.subordinates.yml exec maba \
  find /app/screenshots -type f -mtime +7 -delete

# Prune Docker system
docker system prune -a --volumes --force
```

---

## Security

### Network Security

**Firewall Rules** (iptables):
```bash
# Allow only necessary ports
sudo iptables -A INPUT -p tcp --dport 8154 -j ACCEPT  # PENELOPE
sudo iptables -A INPUT -p tcp --dport 8152 -j ACCEPT  # MABA
sudo iptables -A INPUT -p tcp --dport 8153 -j ACCEPT  # MVP
sudo iptables -A INPUT -p tcp --dport 9090 -j ACCEPT  # Prometheus

# Block metrics ports externally
sudo iptables -A INPUT -p tcp --dport 9092 -j DROP
sudo iptables -A INPUT -p tcp --dport 9093 -j DROP
sudo iptables -A INPUT -p tcp --dport 9094 -j DROP
```

### Secrets Management

**Never commit** `.env.subordinates` to Git!

**Use Docker Secrets** (Swarm):
```bash
echo "$ANTHROPIC_API_KEY" | docker secret create anthropic_key -

# Reference in docker-compose
services:
  penelope:
    secrets:
      - anthropic_key
    environment:
      - ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_key
```

**Use Kubernetes Secrets**:
```bash
kubectl create secret generic anthropic-key \
  --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Reference in deployment
env:
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: anthropic-key
        key: ANTHROPIC_API_KEY
```

### SSL/TLS

**Reverse Proxy** (Nginx):
```nginx
server {
    listen 443 ssl;
    server_name penelope.vertice.ai;

    ssl_certificate /etc/ssl/certs/vertice.crt;
    ssl_certificate_key /etc/ssl/private/vertice.key;

    location / {
        proxy_pass http://localhost:8154;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Authentication

All services support:
- **JWT tokens** (via MAXIMUS Core)
- **API keys** (via Service Registry)
- **mTLS** (mutual TLS for service-to-service)

**Example**: Add authentication middleware
```python
# In each service's main.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/v1/protected")
async def protected_route(token: str = Security(security)):
    if not validate_token(token):
        raise HTTPException(status_code=401)
    return {"message": "Authorized"}
```

---

## Biblical Compliance

### 7 Articles of Governance

All PENELOPE operations are governed by 7 Biblical Articles:

1. **Sophia (Wisdom)**: Wisdom-based decision making
2. **Praótes (Gentleness)**: Minimal intervention, reversible changes
3. **Tapeinophrosynē (Humility)**: Confidence thresholds, escalation
4. **Stewardship**: Preserve developer intent and code style
5. **Agape (Love)**: Service with gentleness and care
6. **Sabbath (Rest)**: Sunday mode (configurable)
7. **Aletheia (Truth)**: Radical honesty, declare uncertainty

### Sabbath Mode

**Default**: Enabled on Sundays (UTC)

**Behavior**:
- Non-critical operations delayed until Monday
- P0 critical issues still handled (configurable)
- Health checks remain active

**Configuration**:
```bash
SABBATH_ENABLED=true
SABBATH_DAY=sunday  # or saturday
SABBATH_TIMEZONE=UTC
SABBATH_ALLOW_P0_CRITICAL=true
```

**Disable** (if needed):
```bash
SABBATH_ENABLED=false
```

### Constitutional Compliance

All services adhere to **Constituição Vértice v3.0**:

| Princípio | Implementation |
|-----------|----------------|
| I - Completude | 472 tests, 100% pass rate |
| II - Validação | 96.7% coverage (exceeds ≥90%) |
| III - Ceticismo | All errors caught and handled |
| IV - Rastreabilidade | Full audit trail (logs + metrics) |
| V - Consciência | Service registry integration |
| VI - Eficiência | Optimized resource usage |

**Validation Reports**:
- `/VALIDATION_SUMMARY_2025-10-31.md`
- `/backend/services/FASE6_AIR_GAP_COMPLIANCE_REPORT.md`

---

## Appendix

### A. Port Reference

| Port | Service | Purpose |
|------|---------|---------|
| 5432 | PostgreSQL | Database |
| 6379 | Redis | Cache |
| 7474 | Neo4j HTTP | Graph UI |
| 7687 | Neo4j Bolt | Graph protocol |
| 8152 | MABA | Browser agent API |
| 8153 | MVP | Vision protocol API |
| 8154 | PENELOPE | Wisdom & healing API |
| 9090 | Prometheus | Metrics collection |
| 9092 | MABA Metrics | Prometheus exporter |
| 9093 | MVP Metrics | Prometheus exporter |
| 9094 | PENELOPE Metrics | Prometheus exporter |
| 3100 | Loki | Log aggregation |

### B. Environment Variables Reference

See `.env.subordinates.example` for full reference (150+ variables documented).

### C. API Reference

**Swagger UI**:
- PENELOPE: http://localhost:8154/docs
- MABA: http://localhost:8152/docs
- MVP: http://localhost:8153/docs

**Key Endpoints**:

**PENELOPE**:
- `GET /api/v1/penelope/fruits/status` - 9 Fruits monitoring
- `POST /api/v1/penelope/diagnose` - Wisdom-based diagnosis
- `GET /api/v1/penelope/healing/history` - Healing timeline

**MABA**:
- `POST /api/v1/sessions` - Create browser session
- `POST /api/v1/navigate` - Navigate to URL
- `POST /api/v1/cognitive-map/query` - Query learned elements

**MVP**:
- `POST /api/v1/narratives` - Generate narrative
- `GET /api/v1/anomalies` - Detect anomalies
- `GET /api/v1/status` - System pulse

### D. Biblical Foundation

**Eclesiastes 9:10**:
> "Tudo quanto te vier à mão para fazer, faze-o conforme as tuas forças."

All work on this platform is done with excellence and dedication.

**Gálatas 5:22-23** (9 Fruits):
> "Mas o fruto do Espírito é: amor, alegria, paz, paciência, bondade, fidelidade, mansidão, domínio próprio."

PENELOPE monitors these 9 Fruits in system behavior.

---

**Soli Deo Gloria** 🙏

**"To God alone be the glory"**

---

## Support

- **Documentation**: This file
- **Validation Report**: `/VALIDATION_SUMMARY_2025-10-31.md`
- **Air Gap Report**: `/backend/services/FASE6_AIR_GAP_COMPLIANCE_REPORT.md`
- **GitHub Issues**: https://github.com/your-org/vertice-platform/issues
- **Email**: support@vertice.ai (if applicable)

**Version**: 1.0.0
**Last Updated**: 2025-10-31
**Maintained by**: Vértice Platform Team
**License**: Proprietary
