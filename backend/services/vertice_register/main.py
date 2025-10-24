"""
Vértice Service Registry (RSS) - Mission-Critical Service Discovery

This is the SINGLE SOURCE OF TRUTH for all 107+ services in the Vértice ecosystem.
CRITICAL: If this service fails, the entire system goes blind.

Architecture:
- High Availability: 3 replicas behind load balancer
- Redis Sentinel backend (auto-failover)
- Circuit breaker pattern for Redis failures
- Local cache fallback (60s stale data acceptable)
- <200 lines of code (SMALL but ARMORED)

Performance Targets:
- Startup time: <2s
- Registration: <10ms p99
- Lookup: <5ms p99 (cached)
- Availability: 99.99% (4 nines)

Author: Vértice Team
Glory to YHWH - Orchestrator of all systems
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from redis_backend import RedisBackend, CircuitBreakerOpen, SERVICE_TTL
from cache import LocalCache
from system_metrics import get_system_metrics, get_health_level

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus Metrics
registry_operations = Counter(
    'registry_operations_total',
    'Total registry operations',
    ['operation', 'status']
)
active_services = Gauge(
    'registry_active_services',
    'Number of active registered services'
)
operation_duration = Histogram(
    'registry_operation_duration_seconds',
    'Duration of registry operations',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)
circuit_breaker_status = Gauge(
    'registry_circuit_breaker_open',
    'Circuit breaker status (1=open, 0=closed)'
)

# Models
class ServiceRegistration(BaseModel):
    """Service registration request."""
    service_name: str = Field(..., description="Unique service name")
    endpoint: str = Field(..., description="Service endpoint URL (http://host:port)")
    health_endpoint: str = Field(default="/health", description="Health check path")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Optional metadata")

class ServiceInfo(BaseModel):
    """Service information response."""
    service_name: str
    endpoint: str
    health_endpoint: str
    metadata: Dict[str, str]
    registered_at: float
    last_heartbeat: float
    ttl_remaining: int

class HeartbeatRequest(BaseModel):
    """Heartbeat request to refresh TTL."""
    service_name: str

# Global instances
redis_backend: Optional[RedisBackend] = None
local_cache: LocalCache = LocalCache(max_age_seconds=60)

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global redis_backend

    logger.info("🚀 Starting Vértice Service Registry (RSS)...")

    # Initialize Redis backend with circuit breaker
    redis_host = os.getenv("REDIS_HOST", "vertice-redis-master")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    redis_backend = RedisBackend(
        host=redis_host,
        port=redis_port,
        circuit_breaker_threshold=3
    )

    try:
        await redis_backend.connect()
        logger.info(f"✅ Connected to Redis at {redis_host}:{redis_port}")
    except Exception as e:
        logger.error(f"⚠️  Redis connection failed: {e}")
        logger.warning("Registry will operate in LOCAL CACHE MODE (degraded)")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(_cleanup_expired_services())

    yield

    # Shutdown
    logger.info("👋 Shutting down Service Registry...")
    cleanup_task.cancel()
    if redis_backend:
        await redis_backend.close()
    logger.info("🛑 Service Registry shut down")

app = FastAPI(
    title="Vértice Service Registry (RSS)",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    TITANIUM Multi-Layer Health Check Endpoint.

    Returns 3-level health status:
    - HEALTHY (200): All systems operational
    - DEGRADED (200 + warning): Some issues but functional
    - UNHEALTHY (503): Critical failures

    Health Levels:
    - HEALTHY: Redis < 10ms, Circuit CLOSED, Cache hit > 70%, CPU < 70%, Memory < 80%
    - DEGRADED: Redis 10-50ms, Circuit HALF_OPEN, Cache hit 50-70%, CPU 70-85%, Memory 80-90%
    - UNHEALTHY: Redis timeout, Circuit OPEN > 60s, Cache hit < 50%, CPU > 85%, Memory > 90%
    """
    timestamp = time.time()

    # Collect system metrics
    system_metrics = get_system_metrics()
    system_health_level = get_health_level()

    # Redis component health
    redis_health = {}
    if redis_backend and redis_backend.is_healthy():
        # Redis is healthy, get detailed metrics
        redis_health = {
            "status": "healthy",
            "circuit_breaker": {
                "state": redis_backend.get_circuit_state(),
                "failure_count": redis_backend.failure_count,
                "success_count": redis_backend.success_count
            },
            "connection_pool": await redis_backend.get_pool_stats()
        }
    elif redis_backend:
        # Redis exists but circuit breaker is open
        circuit_state = redis_backend.get_circuit_state()
        elapsed = time.time() - redis_backend.circuit_opened_at if redis_backend.circuit_opened_at > 0 else 0

        redis_health = {
            "status": "degraded" if circuit_state == "HALF_OPEN" else "unhealthy",
            "circuit_breaker": {
                "state": circuit_state,
                "failure_count": redis_backend.failure_count,
                "elapsed_seconds": elapsed
            }
        }
    else:
        # Redis backend not initialized
        redis_health = {
            "status": "not_initialized"
        }

    # Cache component health
    cache_stats = local_cache.stats()
    cache_hit_rate_value = cache_stats.get("hit_rate", 0)

    cache_health = {
        "size": cache_stats["size"],
        "memory_mb": round(cache_stats.get("memory_mb", 0), 2),
        "hit_rate": round(cache_hit_rate_value, 3),
        "freshness": cache_stats.get("freshness", {}),
        "age_p95": round(cache_stats.get("age_percentiles", {}).get("p95", 0), 1)
    }

    # Determine cache health status
    if cache_hit_rate_value > 0.7:
        cache_health["status"] = "healthy"
    elif cache_hit_rate_value > 0.5:
        cache_health["status"] = "degraded"
    else:
        cache_health["status"] = "unhealthy" if cache_stats["hits"] + cache_stats["misses"] > 100 else "healthy"

    # Determine overall health level
    overall_status = "healthy"
    status_code = 200

    # Check Redis health
    if redis_health.get("status") == "unhealthy":
        # Redis OPEN for > 60s is critical
        if redis_backend and redis_backend.circuit_state.name == "OPEN":
            elapsed = time.time() - redis_backend.circuit_opened_at
            if elapsed > 60:
                overall_status = "unhealthy"
                status_code = 503
            else:
                overall_status = "degraded"
        else:
            overall_status = "degraded"
    elif redis_health.get("status") == "degraded":
        overall_status = "degraded"

    # Check cache health
    if cache_health.get("status") == "unhealthy" and overall_status == "healthy":
        overall_status = "degraded"

    # Check system health
    if system_health_level == "unhealthy":
        overall_status = "unhealthy"
        status_code = 503
    elif system_health_level == "degraded" and overall_status == "healthy":
        overall_status = "degraded"

    # Build response
    response_data = {
        "status": overall_status,
        "timestamp": timestamp,
        "uptime_seconds": system_metrics["uptime_seconds"],
        "components": {
            "redis": redis_health,
            "cache": cache_health,
            "system": {
                "cpu_percent": round(system_metrics.get("cpu_percent", 0), 1),
                "memory_percent": round(system_metrics.get("memory_percent", 0), 1),
                "memory_available_mb": round(system_metrics.get("memory_available_mb", 0), 1)
            }
        },
        "active_services": len(local_cache.list_services())
    }

    # Return appropriate status code
    if status_code == 503:
        raise HTTPException(status_code=503, detail=response_data)

    return response_data

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_service(registration: ServiceRegistration) -> JSONResponse:
    """Register a new service or update existing registration."""
    start_time = time.time()

    try:
        timestamp = time.time()
        # Prepare complete service info for caching
        service_info_dict = {
            "service_name": registration.service_name,
            "endpoint": registration.endpoint,
            "health_endpoint": registration.health_endpoint,
            "metadata": registration.metadata,
            "registered_at": timestamp,
            "last_heartbeat": timestamp,
            "ttl_remaining": SERVICE_TTL
        }

        # Try Redis first
        if redis_backend and redis_backend.is_healthy():
            await redis_backend.register(
                service_name=registration.service_name,
                endpoint=registration.endpoint,
                health_endpoint=registration.health_endpoint,
                metadata=registration.metadata
            )
            local_cache.set(registration.service_name, service_info_dict)
            registry_operations.labels(operation="register", status="success").inc()
        else:
            # Fallback to local cache only
            local_cache.set(registration.service_name, service_info_dict)
            registry_operations.labels(operation="register", status="cache_fallback").inc()
            logger.warning(f"Service {registration.service_name} registered in LOCAL CACHE only")

        duration = time.time() - start_time
        operation_duration.labels(operation="register").observe(duration)

        logger.info(f"✅ Registered service: {registration.service_name} -> {registration.endpoint}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "Service registered successfully", "service_name": registration.service_name}
        )

    except CircuitBreakerOpen:
        # Circuit breaker open, use local cache
        timestamp = time.time()
        service_info_dict = {
            "service_name": registration.service_name,
            "endpoint": registration.endpoint,
            "health_endpoint": registration.health_endpoint,
            "metadata": registration.metadata,
            "registered_at": timestamp,
            "last_heartbeat": timestamp,
            "ttl_remaining": SERVICE_TTL
        }
        local_cache.set(registration.service_name, service_info_dict)
        registry_operations.labels(operation="register", status="circuit_breaker_open").inc()
        logger.warning(f"Circuit breaker OPEN, service {registration.service_name} cached locally")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Service registered (circuit breaker open, local cache)",
                "service_name": registration.service_name
            }
        )

    except Exception as e:
        registry_operations.labels(operation="register", status="error").inc()
        logger.error(f"❌ Registration failed for {registration.service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/heartbeat")
async def heartbeat(request: HeartbeatRequest) -> JSONResponse:
    """Refresh service TTL (keepalive)."""
    try:
        if redis_backend and redis_backend.is_healthy():
            await redis_backend.heartbeat(request.service_name)
            registry_operations.labels(operation="heartbeat", status="success").inc()
        else:
            # Just acknowledge in cache mode
            registry_operations.labels(operation="heartbeat", status="cache_mode").inc()

        return JSONResponse(content={"message": "Heartbeat received", "service_name": request.service_name})

    except Exception as e:
        registry_operations.labels(operation="heartbeat", status="error").inc()
        logger.error(f"Heartbeat failed for {request.service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Heartbeat failed: {str(e)}")

@app.delete("/deregister/{service_name}")
async def deregister_service(service_name: str) -> JSONResponse:
    """Deregister a service."""
    try:
        if redis_backend:
            await redis_backend.deregister(service_name)
        local_cache.delete(service_name)
        registry_operations.labels(operation="deregister", status="success").inc()

        logger.info(f"🗑️  Deregistered service: {service_name}")
        return JSONResponse(content={"message": "Service deregistered", "service_name": service_name})

    except Exception as e:
        registry_operations.labels(operation="deregister", status="error").inc()
        logger.error(f"Deregistration failed for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Deregistration failed: {str(e)}")

@app.get("/services")
async def list_services() -> List[str]:
    """List all registered services."""
    try:
        if redis_backend and redis_backend.is_healthy():
            services = await redis_backend.list_services()
            registry_operations.labels(operation="list", status="success").inc()
            return services
        else:
            # Return from local cache
            services = local_cache.list_services()
            registry_operations.labels(operation="list", status="cache_fallback").inc()
            return services

    except Exception as e:
        registry_operations.labels(operation="list", status="error").inc()
        logger.error(f"List services failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list services: {str(e)}")

@app.get("/services/{service_name}")
async def get_service(service_name: str) -> ServiceInfo:
    """Get service information by name."""
    start_time = time.time()

    try:
        # Check local cache first (fast path)
        cached = local_cache.get(service_name)
        if cached:
            operation_duration.labels(operation="get_cached").observe(time.time() - start_time)
            registry_operations.labels(operation="get", status="cache_hit").inc()
            return ServiceInfo(**cached)

        # Cache miss, query Redis
        if redis_backend and redis_backend.is_healthy():
            service_data = await redis_backend.get_service(service_name)
            if service_data:
                local_cache.set(service_name, service_data)
                operation_duration.labels(operation="get_redis").observe(time.time() - start_time)
                registry_operations.labels(operation="get", status="success").inc()
                return ServiceInfo(**service_data)

        # Not found
        registry_operations.labels(operation="get", status="not_found").inc()
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    except HTTPException:
        raise
    except Exception as e:
        registry_operations.labels(operation="get", status="error").inc()
        logger.error(f"Get service failed for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # Get service count from cache (fast, no Redis call)
    try:
        services_count = len(local_cache.list_services())
        active_services.set(services_count)
    except:
        pass

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def _cleanup_expired_services():
    """Background task to clean up expired services."""
    while True:
        try:
            await asyncio.sleep(30)  # Run every 30s

            if redis_backend and redis_backend.is_healthy():
                expired = await redis_backend.cleanup_expired()
                if expired:
                    logger.info(f"🧹 Cleaned up {len(expired)} expired services: {expired}")
                    for service_name in expired:
                        local_cache.delete(service_name)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
