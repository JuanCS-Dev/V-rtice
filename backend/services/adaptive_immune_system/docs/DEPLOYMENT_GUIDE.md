# Deployment Guide - Adaptive Immune System HITL API

**Version**: 1.0.0
**Date**: 2025-10-13
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker Compose)](#quick-start-docker-compose)
3. [Manual Deployment](#manual-deployment)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Rollback](#rollback)

---

## Prerequisites

### Required Software

- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git**: 2.30+
- **PostgreSQL**: 14+ (if running without Docker)
- **Python**: 3.11+ (if running without Docker)

### Required Credentials

- **GitHub Personal Access Token** (for wargaming integration)
  - Create at: https://github.com/settings/tokens
  - Required scopes: `repo` (full control of private repositories)

### System Requirements

- **CPU**: 2 cores minimum, 4 cores recommended
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 10GB free space minimum
- **Network**: Outbound HTTPS access to GitHub API

---

## Quick Start (Docker Compose)

**Recommended for development and production.**

### Step 1: Clone Repository

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

**Required variables**:
```bash
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO_OWNER=your-organization
GITHUB_REPO_NAME=your-repository
```

### Step 3: Start with Docker Compose

```bash
# From project root (/home/juan/vertice-dev)
docker-compose up -d adaptive_immune_system postgres redis
```

### Step 4: Verify Deployment

```bash
# Check container status
docker ps | grep adaptive-immune

# Check logs
docker logs vertice-adaptive-immune

# Test health endpoint
curl http://localhost:8003/health

# Expected response:
# {"status":"healthy","version":"1.0.0",...}
```

### Step 5: Access API Documentation

- **Swagger UI**: http://localhost:8003/hitl/docs
- **ReDoc**: http://localhost:8003/hitl/redoc
- **Health Check**: http://localhost:8003/health
- **Metrics**: http://localhost:8003/metrics

---

## Manual Deployment

**For advanced users or non-Docker deployments.**

### Step 1: Install Dependencies

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
nano .env
```

Set all variables, especially:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/adaptive_immune
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

### Step 3: Database Setup

```bash
# Create database
createdb adaptive_immune

# Run migrations
alembic upgrade head
```

### Step 4: Start Application

```bash
uvicorn hitl.api.main:app --host 0.0.0.0 --port 8003
```

Or use systemd (see [Systemd Service](#systemd-service) section).

---

## Configuration

### Environment Variables

All configuration is done via environment variables. See `.env.example` for full list.

#### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Adaptive Immune System - HITL API | Application name |
| `APP_VERSION` | 1.0.0 | Application version |
| `DEBUG` | false | Debug mode (true/false) |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8003 | Server port |

#### Database Settings

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection URL |

Example:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/adaptive_immune
```

#### GitHub Settings

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub Personal Access Token |
| `GITHUB_REPO_OWNER` | Yes | Repository owner/organization |
| `GITHUB_REPO_NAME` | Yes | Repository name |

#### Observability Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | info | Logging level (debug, info, warning, error) |
| `PROMETHEUS_ENABLED` | true | Enable Prometheus metrics |

### Configuration Validation

Test your configuration:

```bash
# Validate settings
python -m hitl.config

# Should output:
# Configuration loaded successfully!
# Settings (safe dump): ...
```

---

## Database Setup

### Initial Migration

```bash
# Run all migrations
alembic upgrade head

# Verify tables were created
psql -d adaptive_immune -c "\dt"

# Expected tables:
# - apv_reviews
# - hitl_decisions
```

### Create Migration (if schema changes)

```bash
# Generate new migration
alembic revision -m "description of change"

# Edit generated file in alembic/versions/

# Apply migration
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

---

## Verification

### Health Checks

```bash
# Basic health check
curl http://localhost:8003/health

# Readiness check (checks dependencies)
curl http://localhost:8003/health/ready

# Liveness check
curl http://localhost:8003/health/live
```

### API Endpoints

```bash
# List pending reviews
curl http://localhost:8003/hitl/reviews

# Get statistics
curl http://localhost:8003/hitl/reviews/stats

# View metrics
curl http://localhost:8003/metrics
```

### WebSocket Connection

```bash
# Test WebSocket (using websocat)
websocat ws://localhost:8003/hitl/ws

# Send subscribe message:
{"type": "subscribe", "channels": ["apvs", "decisions"]}

# Should receive: {"type": "subscription_confirmed", ...}
```

### Logs

```bash
# Docker logs
docker logs vertice-adaptive-immune --follow

# Manual deployment logs
tail -f /var/log/adaptive-immune/app.log

# Look for:
# - "🚀 HITL API starting up..."
# - "📝 Docs: http://localhost:8003/hitl/docs"
# - "🔌 WebSocket: ws://localhost:8003/hitl/ws"
```

---

## Troubleshooting

### Container Won't Start

**Symptom**: `docker ps` shows container constantly restarting

**Check**:
```bash
docker logs vertice-adaptive-immune

# Common issues:
# - Missing environment variables
# - Database connection failed
# - Port 8003 already in use
```

**Solution**:
```bash
# Check environment variables
docker exec vertice-adaptive-immune env | grep -E "DATABASE|GITHUB"

# Check port usage
lsof -i :8003

# Restart container
docker-compose restart adaptive_immune_system
```

### Database Connection Failed

**Symptom**: `FATAL: password authentication failed for user`

**Check**:
```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection manually
psql "postgresql://postgres:postgres@localhost:5432/adaptive_immune"
```

**Solution**:
```bash
# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://correct_user:correct_password@localhost:5432/adaptive_immune

# Restart
docker-compose restart adaptive_immune_system
```

### Health Check Fails

**Symptom**: `curl http://localhost:8003/health` returns 503 or times out

**Check**:
```bash
# Check if service is listening
netstat -tulpn | grep 8003

# Check readiness check
curl http://localhost:8003/health/ready

# Check logs
docker logs vertice-adaptive-immune --tail 50
```

**Solution**:
```bash
# If dependencies are failing, check:
# - PostgreSQL is running
# - Redis is running
# - Network connectivity

# Restart dependencies
docker-compose restart postgres redis

# Restart service
docker-compose restart adaptive_immune_system
```

### High Memory Usage

**Symptom**: Container using excessive memory

**Check**:
```bash
# Check container stats
docker stats vertice-adaptive-immune

# Check for memory leaks in logs
docker logs vertice-adaptive-immune | grep -i "memory\|leak"
```

**Solution**:
```bash
# Set memory limit in docker-compose.yml
services:
  adaptive_immune_system:
    ...
    deploy:
      resources:
        limits:
          memory: 2G

# Restart with limit
docker-compose up -d adaptive_immune_system
```

---

## Rollback

### Docker Compose Rollback

```bash
# Stop current version
docker-compose stop adaptive_immune_system

# Pull previous image (if using registry)
docker pull your-registry/adaptive-immune:previous-tag

# Update docker-compose.yml to use previous tag
# OR checkout previous git commit

# Start previous version
docker-compose up -d adaptive_immune_system

# Verify health
curl http://localhost:8003/health
```

### Database Rollback

```bash
# Rollback migrations
alembic downgrade -1

# Or rollback to specific version
alembic downgrade <revision_id>

# Verify current version
alembic current
```

### Manual Rollback

```bash
# Stop service
systemctl stop adaptive-immune

# Checkout previous version
git checkout <previous-commit>

# Install dependencies
pip install -r requirements.txt

# Rollback database
alembic downgrade -1

# Start service
systemctl start adaptive-immune

# Verify
curl http://localhost:8003/health
```

---

## Systemd Service

**For manual deployments without Docker.**

### Create Service File

```bash
sudo nano /etc/systemd/system/adaptive-immune.service
```

```ini
[Unit]
Description=Adaptive Immune System - HITL API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/adaptive-immune
Environment="PATH=/opt/adaptive-immune/venv/bin"
EnvironmentFile=/opt/adaptive-immune/.env
ExecStart=/opt/adaptive-immune/venv/bin/uvicorn hitl.api.main:app --host 0.0.0.0 --port 8003
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable adaptive-immune

# Start service
sudo systemctl start adaptive-immune

# Check status
sudo systemctl status adaptive-immune

# View logs
sudo journalctl -u adaptive-immune -f
```

---

## Production Checklist

Before deploying to production, verify:

- [ ] `DEBUG=false` in .env
- [ ] Strong database password set
- [ ] GitHub token configured
- [ ] CORS origins set to production domains
- [ ] SSL/TLS enabled (reverse proxy)
- [ ] Monitoring configured (Prometheus + Grafana)
- [ ] Log aggregation configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Health checks tested
- [ ] Load testing completed
- [ ] Security audit completed

---

## Support

For issues or questions:

- **Documentation**: `/home/juan/vertice-dev/backend/services/adaptive_immune_system/docs/`
- **API Docs**: http://localhost:8003/hitl/docs
- **Operational Runbook**: `docs/OPERATIONAL_RUNBOOK.md`

---

**Last Updated**: 2025-10-13
**Author**: Adaptive Immune System Team
