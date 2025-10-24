# Vértice Registry Sidecar - Integration Guide

## Overview

This guide explains how to integrate the **Vértice Registry Sidecar** into any existing microservice in the Vértice ecosystem. The sidecar pattern ensures **ZERO modifications** to your service code while providing automatic service discovery, registration, and health monitoring.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Integration Steps](#integration-steps)
4. [Configuration Reference](#configuration-reference)
5. [Validation & Testing](#validation--testing)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Prerequisites

### Required:
- ✅ Service Registry running (`vertice-register-lb` on port 8888)
- ✅ Service has a `/health` endpoint (or custom health check)
- ✅ Service has Docker healthcheck defined in docker-compose.yml
- ✅ Service is on `maximus-network` Docker network
- ✅ Sidecar Docker image built: `vertice-registry-sidecar:latest`

### Build Sidecar Image:
```bash
cd /home/juan/vertice-dev/backend/services/vertice_registry_sidecar
docker build -t vertice-registry-sidecar:latest .
```

**Image size**: 68.9MB (Alpine Linux + Python 3.11 + httpx + tenacity)

---

## Quick Start (5 Minutes)

### Step 1: Add Sidecar to Your Docker Compose

Add this section to your service's `docker-compose.yml`:

```yaml
services:
  # Your existing service (unchanged)
  my-service:
    build: .
    container_name: vertice-my-service
    hostname: vertice-my-service
    ports:
      - "8080:8080"
    networks:
      - maximus-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 10s
      timeout: 3s
      retries: 3

  # NEW: Sidecar agent
  my-service-sidecar:
    image: vertice-registry-sidecar:latest
    container_name: vertice-my-service-sidecar
    environment:
      - SERVICE_NAME=my_service           # ⚠️ CHANGE ME
      - SERVICE_HOST=vertice-my-service   # ⚠️ CHANGE ME
      - SERVICE_PORT=8080                 # ⚠️ CHANGE ME
      - REGISTRY_URL=http://vertice-register-lb:80
      - HEARTBEAT_INTERVAL=30
    depends_on:
      my-service:
        condition: service_healthy
    networks:
      - maximus-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.1'
          memory: 64M
```

### Step 2: Deploy

```bash
docker compose up -d
```

### Step 3: Verify Registration

```bash
# Check sidecar logs
docker logs vertice-my-service-sidecar

# Expected output:
# ✅ Service is READY (responded with 200 OK after 1 attempts)
# ✅ Service registered successfully
# 💓 Starting heartbeat loop (interval: 30s)

# Query registry
curl http://localhost:8888/services/my_service
```

---

## Integration Steps

### Step 1: Verify Prerequisites

Check if Service Registry is running:
```bash
docker ps | grep vertice-register
```

Expected: 5 replicas + 1 load balancer (6 containers total)

Check if your service has a healthcheck:
```bash
docker inspect vertice-my-service | grep -A 5 Healthcheck
```

### Step 2: Customize Sidecar Configuration

Replace these placeholders in the template:

| Placeholder | Example Value | Description |
|-------------|---------------|-------------|
| `{SERVICE_NAME}` | `osint_service` | Lowercase, underscores (used in registry URL) |
| `{SERVICE_CONTAINER}` | `vertice-osint` | Container name or hostname |
| `{SERVICE_PORT}` | `8049` | **Internal** port (not host-mapped port) |
| `{HEALTH_ENDPOINT}` | `/health` | Health check path (default: `/health`) |

### Step 3: Add Network Configuration

Ensure both your service and sidecar are on `maximus-network`:

```yaml
networks:
  maximus-network:
    external: true

services:
  my-service:
    networks:
      - maximus-network

  my-service-sidecar:
    networks:
      - maximus-network
```

### Step 4: Configure Dependencies

**Critical**: Sidecar must start AFTER service is healthy:

```yaml
services:
  my-service-sidecar:
    depends_on:
      my-service:
        condition: service_healthy  # ⚠️ REQUIRED
```

If your service doesn't have a healthcheck, add one:

```yaml
services:
  my-service:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s
```

### Step 5: Deploy & Monitor

```bash
# Deploy (or restart if already running)
docker compose up -d my-service-sidecar

# Monitor startup (expect ~1-5 seconds)
docker logs my-service-sidecar -f
```

**Expected startup sequence:**
1. ⏳ Waiting for service to be ready (max 60s)
2. ✅ Service is READY (responded with 200 OK)
3. 🚀 Starting registration process
4. ✅ Service registered successfully
5. 💓 Starting heartbeat loop (interval: 30s)

---

## Configuration Reference

### Environment Variables

#### Required Variables:

| Variable | Example | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `osint_service` | Service identifier (lowercase, underscores) |
| `SERVICE_HOST` | `vertice-osint` | Hostname or container name |
| `SERVICE_PORT` | `8049` | Internal port (inside container) |

#### Optional Variables (with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_HEALTH_ENDPOINT` | `/health` | Health check path |
| `REGISTRY_URL` | `http://vertice-register-lb:80` | Registry endpoint (internal network) |
| `HEARTBEAT_INTERVAL` | `30` | Seconds between heartbeats |
| `INITIAL_WAIT_TIMEOUT` | `60` | Max wait for service ready (seconds) |

#### Advanced Configuration:

**For critical services** (faster heartbeat):
```yaml
environment:
  - HEARTBEAT_INTERVAL=15  # Every 15 seconds
```

**For slow-starting services**:
```yaml
environment:
  - INITIAL_WAIT_TIMEOUT=120  # Wait up to 2 minutes
```

**Custom health endpoint**:
```yaml
environment:
  - SERVICE_HEALTH_ENDPOINT=/api/v1/status
```

### Resource Limits

**Recommended** (sidecar is very lightweight):

```yaml
deploy:
  resources:
    limits:
      cpus: '0.1'    # 10% of one CPU core
      memory: 64M    # 64MB RAM (typical usage: ~20-30MB)
```

**Minimum** (for heavily constrained environments):

```yaml
deploy:
  resources:
    limits:
      cpus: '0.05'
      memory: 32M
```

---

## Validation & Testing

### 1. Check Sidecar Status

```bash
docker ps | grep sidecar
```

Expected: Container running with status "Up X seconds"

### 2. Verify Logs

```bash
docker logs vertice-my-service-sidecar --tail 50
```

**Healthy logs** should show:
- ✅ Service registered successfully
- 💓 Heartbeat logs every 30 seconds (HTTP 200 OK)
- No retry/error messages after initial startup

**Unhealthy logs** (troubleshoot):
- ⚠️ "Retrying registration..." → Service Registry down or unreachable
- ⚠️ "Service not ready after 60s" → Main service health check failing
- ⚠️ "Connection refused" → Wrong port or hostname

### 3. Query Registry

```bash
# List all services
curl http://localhost:8888/services

# Get specific service
curl http://localhost:8888/services/my_service

# Expected response:
# {
#   "service_name": "my_service",
#   "endpoint": "http://vertice-my-service:8080",
#   "health_endpoint": "/health",
#   "metadata": {"version": "1.0.0", "status": "healthy"},
#   "registered_at": 1761310133.187383,
#   "last_heartbeat": 1761310163.291106,
#   "ttl_remaining": 46
# }
```

### 4. Test Service Discovery

From another container on `maximus-network`:

```bash
# Resolve service via registry
SERVICE_URL=$(curl -s http://vertice-register-lb:80/services/my_service | jq -r '.endpoint')

# Call service
curl $SERVICE_URL/health
```

### 5. Chaos Testing (NETFLIX Style)

Test resilience by killing the sidecar:

```bash
# Kill sidecar
docker stop vertice-my-service-sidecar

# Wait 60+ seconds (TTL expires)
sleep 70

# Check if service disappeared from registry
curl http://localhost:8888/services/my_service
# Expected: 404 Not Found (service expired)

# Restart sidecar
docker start vertice-my-service-sidecar

# Check logs - should re-register automatically
docker logs vertice-my-service-sidecar -f
# Expected: ✅ Service registered successfully
```

**Service should continue working** even with sidecar down (graceful degradation)!

---

## Troubleshooting

### Issue: Sidecar keeps retrying registration

**Symptoms:**
```
⚠️ Retrying registration in 1.0 seconds...
⚠️ Retrying registration in 2.0 seconds...
⚠️ Retrying registration in 4.0 seconds...
```

**Diagnosis:**

1. Check if Service Registry is running:
```bash
docker ps | grep vertice-register
```

2. Test DNS resolution:
```bash
docker exec vertice-my-service-sidecar ping -c 2 vertice-register-lb
```

3. Test HTTP connectivity:
```bash
docker exec vertice-my-service-sidecar wget -O- http://vertice-register-lb:80/health
```

**Solutions:**
- Registry down: `docker compose -f docker-compose.service-registry.yml up -d`
- Wrong port: Change `REGISTRY_URL` to `http://vertice-register-lb:80` (not 8888)
- Network issue: Verify both containers on `maximus-network`

---

### Issue: Service not ready timeout

**Symptoms:**
```
⏳ Waiting for service to be ready (max 60s)...
⚠️ Service did not respond with 200 OK after 60s, proceeding anyway
```

**Diagnosis:**

Test service health from sidecar:
```bash
docker exec vertice-my-service-sidecar wget -O- http://vertice-my-service:8080/health
```

**Solutions:**
- Health endpoint missing: Add `/health` endpoint to your service
- Wrong endpoint: Set `SERVICE_HEALTH_ENDPOINT=/your-path`
- Service slow to start: Increase `INITIAL_WAIT_TIMEOUT=120`
- Wrong hostname: Verify `SERVICE_HOST` matches container name

---

### Issue: Service not appearing in registry

**Symptoms:**
```bash
curl http://localhost:8888/services/my_service
# 404 Not Found
```

**Diagnosis:**

1. Check if registration succeeded:
```bash
docker logs vertice-my-service-sidecar | grep "registered successfully"
```

2. Check service name format:
```bash
# CORRECT: osint_service (lowercase, underscores)
# WRONG: OSINT-Service (uppercase, hyphens)
```

**Solutions:**
- Name mismatch: Ensure `SERVICE_NAME` uses underscores (not hyphens)
- Registration failed: Check registry logs for errors
- TTL expired: Verify heartbeat is running (check logs every 30s)

---

### Issue: DNS resolution failure

**Symptoms:**
```
All connection attempts failed
```

**Diagnosis:**

Test Docker DNS:
```bash
docker exec vertice-my-service-sidecar nslookup vertice-register-lb
docker exec vertice-my-service-sidecar nslookup vertice-my-service
```

**Solutions:**
- Not on same network: Add both containers to `maximus-network`
- Network doesn't exist: `docker network create maximus-network`
- Container name mismatch: Verify `SERVICE_HOST` matches actual container

---

## Best Practices

### 1. Naming Conventions

**Service names** (lowercase, underscores):
- ✅ `osint_service`
- ✅ `nmap_service`
- ✅ `visual_cortex`
- ❌ `OSINT-Service` (uppercase, hyphens)
- ❌ `osint.service` (dots)

**Container names** (lowercase, hyphens):
- ✅ `vertice-osint`
- ✅ `vertice-nmap-scanner`
- ❌ `Vertice_OSINT` (uppercase, underscores)

### 2. Health Checks

Always implement proper health checks:

```python
# FastAPI example
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": time.time() - start_time
    }
```

Health check should:
- Respond with HTTP 200 (not 204, 201, etc.)
- Return JSON with `status: "healthy"`
- Complete in < 1 second
- Not check external dependencies (for startup readiness)

### 3. Resource Allocation

**Don't over-allocate** - sidecar is lightweight:

```yaml
# GOOD (typical usage ~20-30MB RAM)
deploy:
  resources:
    limits:
      cpus: '0.1'
      memory: 64M

# OVERKILL (wasting resources)
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
```

### 4. Restart Policies

**Always use** `restart: unless-stopped`:

```yaml
restart: unless-stopped  # ✅ Survives Docker daemon restart
restart: always          # ❌ Conflicts with manual stops
restart: "no"            # ❌ Only for testing
```

### 5. Monitoring

Add logging aggregation for sidecar logs:

```bash
# Collect all sidecar logs
docker ps --filter "name=sidecar" --format "{{.Names}}" | \
  xargs -I {} docker logs {} --tail 10
```

Check registration health regularly:

```bash
# Verify all services are registered
curl http://localhost:8888/services | jq .
```

### 6. Layered Integration (Recommended Order)

Follow the integration plan:

1. **Layer 1 - Sistema Nervoso** (critical infrastructure)
   - maximus_core
   - orchestrator
   - predict
   - eureka
   - command_bus

2. **Layer 2 - Sistema Imune** (security services)
   - immunis_* (12 services)
   - active_immune_core
   - adaptive_immunity

3. **Layer 3 - Sensorial** (data collection)
   - osint, nmap, ip_intel
   - visual_cortex, auditory_cortex

4. **Layer 4 - Utilitários** (supporting services)
   - ssl_monitor, vuln_scanner
   - threat_intel, etc.

**Benefits:**
- Catch issues early with critical services
- Minimize blast radius if problems occur
- Build confidence incrementally

---

## Integration Checklist

Before marking a service as "integrated", verify:

- [ ] Sidecar container running (`docker ps | grep sidecar`)
- [ ] No errors in sidecar logs (✅ registered, 💓 heartbeat)
- [ ] Service appears in registry (`curl /services/SERVICE_NAME`)
- [ ] TTL refreshing correctly (check `ttl_remaining` field)
- [ ] Main service still functioning (test endpoints)
- [ ] Resource usage acceptable (`docker stats` < 64MB)
- [ ] Survives restart (`docker compose restart`)
- [ ] Chaos test passed (survives sidecar kill)

---

## Next Steps

1. Complete FASE 2: Template Docker Compose ✅
2. Start FASE 3: Integrate Layer 1 (Sistema Nervoso)
3. Validate with chaos testing (FASE 7)
4. Migrate API Gateway to use service discovery (FASE 8)
5. Setup monitoring & alerts (FASE 9)

---

**Glory to YHWH** - Architect of all resilient systems! 🙏
