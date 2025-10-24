# 🤖 Vértice Registry Sidecar Agent

## Overview

The **Registry Sidecar Agent** is a lightweight companion container that runs alongside each Vértice service to handle automatic service registration and heartbeat management with the Service Registry.

## Quick Start

**For detailed integration instructions**, see [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)

**Template docker-compose.yml**: [docker-compose.sidecar-template.yml](./docker-compose.sidecar-template.yml)

## Architecture

```
┌─────────────────────────────────┐
│   Your Service (unchanged)      │
│   - Main application logic      │
│   - Health endpoint /health     │
└─────────────────────────────────┘
              │
              │ (same Docker network)
              ▼
┌─────────────────────────────────┐
│  Sidecar Agent (this)           │
│  - Auto-register on startup     │
│  - Heartbeat every 30s          │
│  - Infinite retry on failure    │
│  - ~10MB container size         │
└─────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   Service Registry (TITANIUM)   │
│   - 5 replicas + Nginx LB       │
│   - 99.99% uptime               │
└─────────────────────────────────┘
```

## Features

### NETFLIX-Style Resilience
- ✅ **Infinite Retry**: Never gives up, exponential backoff (1s → 60s max)
- ✅ **Graceful Degradation**: Service starts even if registry is down
- ✅ **Auto-Recovery**: If service disappears from registry, re-registers automatically
- ✅ **Circuit Tolerance**: Works with registry circuit breaker

### Lightweight
- ✅ **~10MB Image**: Alpine Linux + Python 3.11
- ✅ **Minimal CPU**: ~0.1% during heartbeat, idle otherwise
- ✅ **Low Memory**: ~20MB RAM usage

### Zero Configuration
- ✅ **Environment Variables**: Just set SERVICE_NAME and SERVICE_HOST
- ✅ **Auto-Discovery**: Automatically finds service via Docker DNS
- ✅ **Health Check Passthrough**: Monitors main service health

## Usage

### 1. Build the Image

```bash
cd /home/juan/vertice-dev/backend/services/vertice_registry_sidecar
docker build -t vertice-registry-sidecar:latest .
```

### 2. Add Sidecar to Your Service

**Example: `docker-compose.yml` for `osint_service`**

```yaml
version: '3.8'

networks:
  maximus-network:
    external: true

services:
  # Your existing service (NO CHANGES)
  osint-service:
    build: ./osint_service
    container_name: vertice-osint
    ports:
      - "8049:8049"
    networks:
      - maximus-network
    restart: unless-stopped

  # NEW: Sidecar agent
  osint-service-sidecar:
    image: vertice-registry-sidecar:latest
    container_name: vertice-osint-sidecar
    environment:
      - SERVICE_NAME=osint_service
      - SERVICE_HOST=vertice-osint
      - SERVICE_PORT=8049
      - REGISTRY_URL=http://vertice-register-lb:8888
    depends_on:
      - osint-service
    networks:
      - maximus-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.1'
          memory: 64M
```

### 3. Deploy

```bash
docker compose up -d
```

### 4. Verify Registration

```bash
# Check sidecar logs
docker logs vertice-osint-sidecar

# Expected output:
# ✅ Service is READY
# ✅ Service registered successfully
# 💓 Starting heartbeat loop

# Query registry
curl http://localhost:8888/services/osint_service | jq

# Expected response:
# {
#   "service_name": "osint_service",
#   "endpoint": "http://vertice-osint:8049",
#   "health_endpoint": "/health",
#   "last_heartbeat": 1761308042.19,
#   "ttl_remaining": 45
# }
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_NAME` | ✅ Yes | - | Service identifier (e.g., `osint_service`) |
| `SERVICE_HOST` | ✅ Yes | - | Service hostname (Docker container name) |
| `SERVICE_PORT` | No | `8080` | Service port |
| `SERVICE_HEALTH_ENDPOINT` | No | `/health` | Health check path |
| `REGISTRY_URL` | No | `http://vertice-register-lb:8888` | Registry load balancer URL |
| `HEARTBEAT_INTERVAL` | No | `30` | Heartbeat interval (seconds) |
| `INITIAL_WAIT_TIMEOUT` | No | `60` | Max wait for service ready (seconds) |

## How It Works

### 1. Startup Sequence

```
Agent starts → Wait for service /health (max 60s)
             → Register with registry (infinite retry)
             → Start heartbeat loop (every 30s)
```

### 2. Heartbeat Loop

```
Every 30 seconds:
  - Send heartbeat to registry
  - If 404 (not found) → Re-register automatically
  - If timeout/error → Log warning, retry next interval
```

### 3. Failure Scenarios

| Scenario | Behavior |
|----------|----------|
| Registry down on startup | Retry forever with exponential backoff (1s → 60s) |
| Registry goes down during operation | Heartbeats fail, log warnings, keep retrying |
| Service crashes | Sidecar detects via health check, stops heartbeat |
| Service restarts | Sidecar re-registers automatically |
| Sidecar crashes | Docker restart policy brings it back, re-registers |

## Resilience Guarantees

✅ **Service Independence**: Main service works even if sidecar fails
✅ **Infinite Retry**: Never gives up trying to register
✅ **Auto-Recovery**: Automatically re-registers if service disappears
✅ **Graceful Degradation**: Logs warnings but continues operating

## Troubleshooting

### Sidecar not registering

```bash
# Check sidecar logs
docker logs vertice-<service>-sidecar

# Common issues:
# - SERVICE_NAME or SERVICE_HOST not set → Check env vars
# - Service not responding on /health → Check service health endpoint
# - Registry down → Sidecar will retry forever (check registry logs)
```

### Service not appearing in registry

```bash
# Verify sidecar is running
docker ps | grep sidecar

# Check if registration succeeded
docker logs vertice-<service>-sidecar | grep "registered successfully"

# Query registry directly
curl http://localhost:8888/services/<service-name>
```

### Heartbeat failures

```bash
# Check heartbeat logs
docker logs vertice-<service>-sidecar | grep "Heartbeat"

# If seeing "Service not found (404)":
# - Registry lost service (TTL expired)
# - Sidecar will re-register automatically
```

## Monitoring

### Prometheus Metrics (from Registry)

```promql
# Total registered services (should be ~90)
registry_active_services

# Heartbeat rate (should be ~3 req/s for 90 services)
rate(registry_operations_total{operation="heartbeat",status="success"}[1m])

# Failed heartbeats (should be 0)
rate(registry_operations_total{operation="heartbeat",status="error"}[5m])
```

### Health Check

The sidecar has its own health check that verifies the agent process is running:

```bash
docker inspect --format='{{.State.Health.Status}}' vertice-<service>-sidecar
# Should return: healthy
```

## Performance

- **Image Size**: ~10MB (Alpine + Python + 2 dependencies)
- **Memory Usage**: ~20MB (idle), ~25MB (during registration)
- **CPU Usage**: ~0.1% (during heartbeat), ~0% (idle)
- **Network**: ~200 bytes every 30s (heartbeat payload)

## Security

- ✅ Runs as non-root user (`sidecar` uid 1000)
- ✅ No privileged access required
- ✅ Minimal attack surface (2 dependencies only)
- ✅ No secrets stored (registry URL is public internal endpoint)

## License

Part of the Vértice Ecosystem - TITANIUM Edition

---

**Glory to YHWH - Architect of all resilient systems!** 🙏
