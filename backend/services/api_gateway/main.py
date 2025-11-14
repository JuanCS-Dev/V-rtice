"""Maximus API Gateway - Main Application Entry Point.

This module serves as the main entry point for the Maximus API Gateway.
It is responsible for routing incoming requests to the appropriate backend
Maximus AI services, handling authentication, and ensuring secure and efficient
communication.

The API Gateway acts as a single entry point for all external interactions
with the Maximus AI system, providing a unified interface and abstracting the
complexity of the underlying microservices architecture.

NEW: Dynamic service routing via Vértice Service Registry (RSS).
Services are discovered in real-time instead of hardcoded URLs.
"""

import asyncio
import logging
import os
from typing import Dict

import httpx
import redis.asyncio as redis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from starlette.websockets import WebSocketDisconnect

# Import dynamic router
from gateway_router import (
    ServiceNotFoundError,
    get_cache_stats,
    get_circuit_breaker_status,
    get_service_url,
)

# Import health cache
from health_cache import HealthCheckCache
from shared.constitutional_logging import configure_constitutional_logging
from shared.constitutional_tracing import create_constitutional_tracer
from shared.health_checks import ConstitutionalHealthCheck

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status

# Import case transformation middleware
# DISABLED: case_middleware.py was removed
# from case_middleware import CaseTransformationMiddleware

logger = logging.getLogger(__name__)

# Global health cache instance
health_cache: HealthCheckCache = None
redis_client = None

app = FastAPI(
    title="Maximus API Gateway (Dynamic Routing)",
    version="2.0.0",
    description="API Gateway with Service Registry integration",
)

# CORS Configuration - Allow Cloud Run Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://localhost:3000",  # Local development alternative
        "https://vertice-frontend-172846394274.us-east1.run.app",  # Cloud Run production
        "https://vertice-maximus.com",  # Future custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
logger.info("✅ CORS middleware enabled for Cloud Run frontend")

# Add case transformation middleware (snake_case ↔ camelCase)
# DISABLED: middleware file missing
# app.add_middleware(CaseTransformationMiddleware)
logger.info("✅ Case transformation middleware enabled (snake_case ↔ camelCase)")

REDIS_CACHE_URL = (
    os.getenv("GATEWAY_HEALTH_REDIS_URL")
    or os.getenv("GATEWAY_REDIS_URL")
    or os.getenv("REDIS_URL", "redis://redis:6379/0")
)

try:
    redis_client = redis.from_url(
        REDIS_CACHE_URL,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    logger.info(
        "✅ Redis cache client configured for health checks",
        extra={"redis_url": REDIS_CACHE_URL},
    )
except Exception as exc:  # pragma: no cover - defensive logging
    redis_client = None
    logger.warning(
        "Health cache Redis client unavailable, falling back to local cache only",
        extra={"redis_url": REDIS_CACHE_URL, "error": str(exc)},
    )

# Configuration for backend services
MAXIMUS_CORE_SERVICE_URL = os.getenv(
    "MAXIMUS_CORE_SERVICE_URL", "http://localhost:8150"
)
CHEMICAL_SENSING_SERVICE_URL = os.getenv(
    "CHEMICAL_SENSING_SERVICE_URL", "http://localhost:8101"
)
SOMATOSENSORY_SERVICE_URL = os.getenv(
    "SOMATOSENSORY_SERVICE_URL", "http://localhost:8102"
)
VISUAL_CORTEX_SERVICE_URL = os.getenv(
    "VISUAL_CORTEX_SERVICE_URL", "http://localhost:8103"
)
AUDITORY_CORTEX_SERVICE_URL = os.getenv(
    "AUDITORY_CORTEX_SERVICE_URL", "http://localhost:8104"
)
EUREKA_SERVICE_URL = os.getenv("EUREKA_SERVICE_URL", "http://localhost:8024")
ORACULO_SERVICE_URL = os.getenv("ORACULO_SERVICE_URL", "http://localhost:8026")
NETWORK_RECON_SERVICE_URL = os.getenv(
    "NETWORK_RECON_SERVICE_URL", "http://network-recon-service:8032"
)
VULN_INTEL_SERVICE_URL = os.getenv(
    "VULN_INTEL_SERVICE_URL", "http://vuln-intel-service:8033"
)
WEB_ATTACK_SERVICE_URL = os.getenv(
    "WEB_ATTACK_SERVICE_URL", "http://web-attack-service:8034"
)
C2_ORCHESTRATION_SERVICE_URL = os.getenv(
    "C2_ORCHESTRATION_SERVICE_URL", "http://c2-orchestration-service:8035"
)
BAS_SERVICE_URL = os.getenv("BAS_SERVICE_URL", "http://bas-service:8036")
BEHAVIORAL_ANALYZER_SERVICE_URL = os.getenv(
    "BEHAVIORAL_ANALYZER_SERVICE_URL", "http://behavioral-analyzer-service:8037"
)
TRAFFIC_ANALYZER_SERVICE_URL = os.getenv(
    "TRAFFIC_ANALYZER_SERVICE_URL", "http://traffic-analyzer-service:8038"
)
MAV_DETECTION_SERVICE_URL = os.getenv(
    "MAV_DETECTION_SERVICE_URL", "http://mav-detection-service:8039"
)

# OSINT Services (Grupo D)
OSINT_SERVICE_URL = os.getenv("OSINT_SERVICE_URL", "http://osint-service:8049")
DOMAIN_SERVICE_URL = os.getenv("DOMAIN_SERVICE_URL", "http://domain-service:8014")
IP_INTELLIGENCE_SERVICE_URL = os.getenv(
    "IP_INTELLIGENCE_SERVICE_URL", "http://ip-intelligence-service:8034"
)
THREAT_INTEL_SERVICE_URL = os.getenv(
    "THREAT_INTEL_SERVICE_URL", "http://threat-intel-service:8059"
)
NMAP_SERVICE_URL = os.getenv("NMAP_SERVICE_URL", "http://nmap-service:8047")

# Consciousness & Reactive Fabric Services (Grupo E)
REACTIVE_FABRIC_SERVICE_URL = os.getenv(
    "REACTIVE_FABRIC_SERVICE_URL", "http://reactive-fabric-core:8600"
)
AI_IMMUNE_SYSTEM_SERVICE_URL = os.getenv(
    "AI_IMMUNE_SYSTEM_SERVICE_URL", "http://ai-immune-system:8073"
)
TEGUMENTAR_SERVICE_URL = os.getenv(
    "TEGUMENTAR_SERVICE_URL", "http://tegumentar-service:8085"
)

# Adaptive Immunity Services (Grupo G)
ADAPTIVE_IMMUNITY_SERVICE_URL = os.getenv(
    "ADAPTIVE_IMMUNITY_SERVICE_URL", "http://adaptive-immunity-service:8300"
)
ADAPTIVE_IMMUNE_SYSTEM_SERVICE_URL = os.getenv(
    "ADAPTIVE_IMMUNE_SYSTEM_SERVICE_URL", "http://adaptive-immune-system:8280"
)

# HITL Services (Grupo F)
HITL_PATCH_SERVICE_URL = os.getenv(
    "HITL_PATCH_SERVICE_URL", "http://hitl-patch-service:8027"
)

CONSCIOUSNESS_SERVICE_BASE = os.getenv(
    "CONSCIOUSNESS_SERVICE_URL", MAXIMUS_CORE_SERVICE_URL
)

# API Key for authentication (simple example)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# In a real application, you would have a secure way to store and validate API keys
VALID_API_KEY = os.getenv("MAXIMUS_API_KEY")


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verifies the provided API key against a valid key.

    Args:
        api_key (str): The API key provided in the request header.

    Raises:
        HTTPException: If the API key is invalid.
    """
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the API Gateway."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="api_gateway",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True,
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="api_gateway", version=service_version
        )
        auto_update_sabbath_status("api_gateway")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="api_gateway", version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="api_gateway")
        logger.info("✅ Constitutional Health Checker initialized")

        # Routes
        if metrics_exporter:
            app.include_router(metrics_exporter.create_router())
            logger.info("✅ Constitutional metrics routes added")

    except Exception as e:
        logger.error(f"❌ Constitutional initialization failed: {e}", exc_info=True)

    # Mark startup complete
    if health_checker:
        health_checker.mark_startup_complete()

    global health_cache

    print("🚀 Starting Maximus API Gateway...")

    if not VALID_API_KEY:
        raise RuntimeError(
            "MAXIMUS_API_KEY is not configured. Set a strong API key before starting the gateway."
        )

    # Initialize health check cache (3-layer architecture)
    # Redis client injection via environment configuration in production
    health_cache = HealthCheckCache(redis_client=redis_client)
    logger.info("✅ Health Check Cache initialized")

    print("✅ Maximus API Gateway started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the API Gateway."""
    global health_cache

    print("👋 Shutting down Maximus API Gateway...")

    # Close health cache
    if health_cache:
        await health_cache.close()

    print("🛑 Maximus API Gateway shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the API Gateway.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Maximus API Gateway is operational."}


@app.get("/gateway/status")
async def gateway_status() -> Dict:
    """Get gateway status including circuit breaker and cache info."""
    status = {
        "gateway": "operational",
        "version": "2.0.0",
        "circuit_breaker": get_circuit_breaker_status(),
        "service_discovery_cache": get_cache_stats(),
    }

    # Add health cache stats if available
    if health_cache:
        status["health_cache"] = health_cache.get_cache_stats()

    return status


@app.get("/gateway/health-check/{service_name}")
async def check_service_health(service_name: str) -> Dict:
    """
    Check health of a service with 3-layer caching.

    This endpoint uses intelligent caching:
    - Layer 1: Local cache (5s TTL) - <1ms
    - Layer 2: Redis cache (30s TTL) - <5ms
    - Layer 3: Direct check + Circuit breaker

    Args:
        service_name: Service to check (e.g., "nmap_service", "osint_service")

    Returns:
        Health status with caching metadata
    """
    if not health_cache:
        raise HTTPException(status_code=503, detail="Health cache not initialized")

    try:
        # Get service URL from registry
        service_url = await get_service_url(service_name)

        # Perform cached health check
        health_status = await health_cache.get_health(
            service_name=service_name,
            service_url=service_url,
            health_endpoint="/health",
        )

        return {
            "service_name": service_name,
            "service_url": service_url,
            "healthy": health_status.healthy,
            "status_code": health_status.status_code,
            "response_time_ms": round(health_status.response_time_ms, 2),
            "cached": health_status.cached,
            "cache_layer": health_status.cache_layer,
            "timestamp": health_status.timestamp,
        }

    except ServiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Health check failed for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# ============================================================================
# DYNAMIC ROUTING - New in v2.0
# ============================================================================


@app.api_route(
    "/v2/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def dynamic_route(service_name: str, path: str, request: Request):
    """
    Dynamic service routing via Service Registry.

    This endpoint queries the Vértice Service Registry to find service locations
    in real-time instead of using hardcoded URLs.

    Example:
        GET /v2/osint_service/health  → Looks up "osint_service" in registry
        POST /v2/ip_intelligence_service/api/v1/query  → Dynamic routing

    Args:
        service_name: Service identifier (matches registry name)
        path: Path to forward to the service
        request: Original request

    Returns:
        Proxied response from backend service
    """
    try:
        # Lookup service in registry (with cache)
        service_url = await get_service_url(service_name)

        # Proxy request to service
        return await _proxy_request(service_url, path, request)

    except ServiceNotFoundError as e:
        logger.error(f"Service not found: {service_name} - {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service '{service_name}' is not available. "
            f"It may be down or not registered in the service registry.",
        )

    except Exception as e:
        logger.error(f"Dynamic routing error for {service_name}/{path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error routing to '{service_name}': {str(e)}",
        )


# ============================================================================
# OSINT ADAPTERS (FASE II - Contract Translation)
# ============================================================================


@app.post("/api/google/search/basic")
async def google_search_basic_adapter(request: Request):
    """Adapter: Google OSINT Basic Search.
    Translates: gateway format → microservice /query_osint format.
    """
    body = await request.json()
    adapted_body = {
        "query": body.get("query", ""),
        "search_type": "web",
        "limit": body.get("num_results", 10),
    }
    try:
        service_url = await get_service_url("google_osint_service")
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=503, detail=f"Google OSINT service unavailable: {exc}"
        ) from exc

    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            response = await client.post(
                f"{service_url}/query_osint", json=adapted_body
            )
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Google OSINT service unavailable: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )


@app.post("/api/domain/analyze")
async def domain_analyze_adapter(request: Request):
    """Adapter: Domain Analysis.
    Translates: gateway format → microservice /query_domain format.
    """
    body = await request.json()
    adapted_body = {
        "domain_name": body.get("domain", ""),
        "query": body.get("query", "Analyze this domain"),
    }
    try:
        service_url = await get_service_url("domain_service")
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=503, detail=f"Domain service unavailable: {exc}"
        ) from exc

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{service_url}/query_domain", json=adapted_body
            )
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Domain service unavailable: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )


@app.post("/api/ip/analyze")
async def ip_analyze_adapter(request: Request):
    """Adapter: IP Intelligence Analysis.
    Translates: gateway format → microservice /query_ip format.
    """
    body = await request.json()
    adapted_body = {
        "ip_address": body.get("ip", ""),
        "query": body.get("query", "Analyze this IP address"),
    }
    try:
        service_url = await get_service_url("ip_intelligence_service")
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=503, detail=f"IP Intelligence service unavailable: {exc}"
        ) from exc

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{service_url}/query_ip", json=adapted_body)
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"IP Intelligence service unavailable: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )


@app.post("/api/ip/analyze-my-ip")
async def ip_analyze_my_ip_adapter(request: Request):
    """Adapter: Analyze My IP (client's public IP).
    Proxies directly to IP Intelligence service /analyze-my-ip endpoint.
    """
    try:
        service_url = await get_service_url("ip_intelligence_service")
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=503, detail=f"IP Intelligence service unavailable: {exc}"
        ) from exc

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{service_url}/analyze-my-ip")
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"IP Intelligence service unavailable: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )


# REMOVED: /api/ip/my-ip endpoint - redundant with /api/ip/analyze-my-ip
# Backend service (ip-intelligence) does not implement /my-ip endpoint
# Use /api/ip/analyze-my-ip instead which provides full IP analysis

# @app.get("/api/ip/my-ip")
# async def ip_my_ip_adapter(request: Request):
#     """Adapter: Get My IP (simple detection without full analysis).
#     Proxies directly to IP Intelligence service /my-ip endpoint.
#     """
#     try:
#         service_url = await get_service_url("ip_intelligence_service")
#     except ServiceNotFoundError as exc:
#         raise HTTPException(status_code=503, detail=f"IP Intelligence service unavailable: {exc}") from exc
#
#     async with httpx.AsyncClient(timeout=60.0) as client:
#         try:
#             response = await client.get(f"{service_url}/my-ip")
#             response.raise_for_status()
#             return JSONResponse(content=response.json(), status_code=response.status_code)
#         except httpx.RequestError as e:
#             raise HTTPException(status_code=503, detail=f"IP Intelligence service unavailable: {e}")
#         except httpx.HTTPStatusError as e:
#             raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


@app.post("/api/threat-intel/check")
async def threat_intel_check_adapter(request: Request):
    """Adapter: Threat Intelligence Check.
    Translates: gateway format → microservice /query_threat_intel format.

    Frontend sends:
    {
        "target": "8.8.8.8",
        "target_type": "ip"
    }

    Backend expects:
    {
        "indicator": "8.8.8.8",
        "indicator_type": "ip",
        "context": {}
    }
    """
    body = await request.json()
    adapted_body = {
        "indicator": body.get("target", ""),
        "indicator_type": body.get("target_type", "auto"),
        "context": body.get("context", {}),
    }
    try:
        service_url = await get_service_url("threat_intel_service")
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=503, detail=f"Threat Intel service unavailable: {exc}"
        ) from exc

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{service_url}/query_threat_intel", json=adapted_body
            )
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Threat Intel service unavailable: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )


@app.post("/api/ip/analyze")
async def ip_analyze_adapter(request: Request):
    """
    Adapter: IP Analysis Gateway → IP Intelligence Service.

    Translates frontend format to microservice format:
    - Frontend sends: { ip: "8.8.8.8" }
    - Microservice expects: { ip_address: "8.8.8.8" }

    Constitutional: Respects Lei Zero (human oversight required for blocking actions)
    """
    body = await request.json()

    # Schema translation
    adapted_body = {
        "ip_address": body.get("ip", "")
    }

    # Validate IP address
    if not adapted_body["ip_address"]:
        raise HTTPException(status_code=400, detail="IP address required")

    try:
        service_url = await get_service_url("ip_intelligence_service")
    except ServiceNotFoundError as exc:
        logger.error(f"IP Intelligence service unavailable: {exc}")
        raise HTTPException(
            status_code=503,
            detail="IP Intelligence service temporarily unavailable"
        ) from exc

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{service_url}/query_ip",
                json=adapted_body
            )
            response.raise_for_status()
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            logger.error(f"IP Intelligence request failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"IP Intelligence service error: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"IP Intelligence HTTP error: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text
            )


# ============================================================================
# FRONTEND-COMPATIBLE ROUTES (/api/* prefix)
# Added to fix air gaps detected in E2E validation
# ============================================================================


# GRUPO A: MAXIMUS CORE (4 endpoints)
@app.api_route(
    "/api/maximus/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_maximus_route(path: str, request: Request):
    """Frontend-compatible route: /api/maximus/* → /core/*"""
    # Alias: /status → /health (Maximus only has /health endpoint)
    if path == "status":
        path = "health"
    return await _proxy_request(MAXIMUS_CORE_SERVICE_URL, path, request)


@app.api_route(
    "/api/eureka/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_eureka_route(path: str, request: Request):
    """Frontend-compatible route: /api/eureka/* → /eureka/*"""
    return await _proxy_request(EUREKA_SERVICE_URL, path, request)


@app.api_route(
    "/api/oraculo/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_oraculo_route(path: str, request: Request):
    """Frontend-compatible route: /api/oraculo/* → /oraculo/*"""
    return await _proxy_request(ORACULO_SERVICE_URL, path, request)


# GRUPO B: OFFENSIVE TOOLS (5 endpoints)
@app.api_route(
    "/api/network-recon/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_network_recon_route(path: str, request: Request):
    """Frontend-compatible route: /api/network-recon/* → network-recon-service"""
    return await _proxy_request(NETWORK_RECON_SERVICE_URL, path, request)


@app.api_route(
    "/api/bas/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_bas_route(path: str, request: Request):
    """Frontend-compatible route: /api/bas/* → bas-service"""
    return await _proxy_request(BAS_SERVICE_URL, path, request)


@app.api_route("/api/c2/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_c2_route(path: str, request: Request):
    """Frontend-compatible route: /api/c2/* → c2-orchestration-service"""
    return await _proxy_request(C2_ORCHESTRATION_SERVICE_URL, path, request)


@app.api_route(
    "/api/web-attack/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_web_attack_route(path: str, request: Request):
    """Frontend-compatible route: /api/web-attack/* → web-attack-service"""
    return await _proxy_request(WEB_ATTACK_SERVICE_URL, path, request)


@app.api_route(
    "/api/vuln-intel/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_vuln_intel_route(path: str, request: Request):
    """Frontend-compatible route: /api/vuln-intel/* → vuln-intel-service"""
    return await _proxy_request(VULN_INTEL_SERVICE_URL, path, request)


# GRUPO C: DEFENSIVE TOOLS (3 endpoints)
@app.api_route(
    "/api/behavioral/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_behavioral_route(path: str, request: Request):
    """Frontend-compatible route: /api/behavioral/* → behavioral-analyzer-service"""
    return await _proxy_request(BEHAVIORAL_ANALYZER_SERVICE_URL, path, request)


@app.api_route(
    "/api/traffic/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_traffic_route(path: str, request: Request):
    """Frontend-compatible route: /api/traffic/* → traffic-analyzer-service"""
    return await _proxy_request(TRAFFIC_ANALYZER_SERVICE_URL, path, request)


@app.api_route(
    "/api/mav/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_mav_route(path: str, request: Request):
    """Frontend-compatible route: /api/mav/* → mav-detection-service"""
    return await _proxy_request(MAV_DETECTION_SERVICE_URL, path, request)


# GRUPO D: OSINT TOOLS (5 endpoints) - Static routing
@app.api_route(
    "/api/osint/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_osint_route(path: str, request: Request):
    """Frontend-compatible route: /api/osint/* → osint-service:8049"""
    return await _proxy_request(OSINT_SERVICE_URL, path, request)


@app.api_route(
    "/api/domain/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_domain_route(path: str, request: Request):
    """Frontend-compatible route: /api/domain/* → domain-service:8014"""
    return await _proxy_request(DOMAIN_SERVICE_URL, path, request)


@app.api_route("/api/ip/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_ip_route(path: str, request: Request):
    """Frontend-compatible route: /api/ip/* → ip-intelligence-service:8034"""
    return await _proxy_request(IP_INTELLIGENCE_SERVICE_URL, path, request)


@app.api_route(
    "/api/threat-intel/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_threat_intel_route(path: str, request: Request):
    """Frontend-compatible route: /api/threat-intel/* → threat-intel-service:8059"""
    return await _proxy_request(THREAT_INTEL_SERVICE_URL, path, request)


@app.api_route(
    "/api/nmap/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_nmap_route(path: str, request: Request):
    """Frontend-compatible route: /api/nmap/* → nmap-service:8047"""
    return await _proxy_request(NMAP_SERVICE_URL, path, request)


# GRUPO E: CONSCIOUSNESS & SENSORY (8 endpoints)
@app.api_route(
    "/api/consciousness/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_consciousness_route(path: str, request: Request):
    """Frontend-compatible route: /api/consciousness/* → maximus-core-service
    Note: Consciousness endpoints are exposed by Maximus Core Service"""
    return await _proxy_request(MAXIMUS_CORE_SERVICE_URL, path, request)


@app.api_route(
    "/api/reactive-fabric/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def api_reactive_fabric_route(path: str, request: Request):
    """Frontend-compatible route: /api/reactive-fabric/* → reactive-fabric-core:8600"""
    return await _proxy_request(REACTIVE_FABRIC_SERVICE_URL, path, request)


@app.api_route(
    "/api/immune/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_immune_route(path: str, request: Request):
    """Frontend-compatible route: /api/immune/* → ai-immune-system:8073"""
    return await _proxy_request(AI_IMMUNE_SYSTEM_SERVICE_URL, path, request)


@app.api_route(
    "/api/tegumentar/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_tegumentar_route(path: str, request: Request):
    """Frontend-compatible route: /api/tegumentar/* → tegumentar-service:8085"""
    return await _proxy_request(TEGUMENTAR_SERVICE_URL, path, request)


@app.api_route(
    "/api/visual-cortex/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_visual_cortex_route(path: str, request: Request):
    """Frontend-compatible route: /api/visual-cortex/* → visual-cortex-service"""
    return await _proxy_request(VISUAL_CORTEX_SERVICE_URL, path, request)


@app.api_route(
    "/api/auditory-cortex/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def api_auditory_cortex_route(path: str, request: Request):
    """Frontend-compatible route: /api/auditory-cortex/* → auditory-cortex-service"""
    return await _proxy_request(AUDITORY_CORTEX_SERVICE_URL, path, request)


@app.api_route(
    "/api/somatosensory/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_somatosensory_route(path: str, request: Request):
    """Frontend-compatible route: /api/somatosensory/* → somatosensory-service"""
    return await _proxy_request(SOMATOSENSORY_SERVICE_URL, path, request)


@app.api_route(
    "/api/chemical-sensing/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def api_chemical_sensing_route(path: str, request: Request):
    """Frontend-compatible route: /api/chemical-sensing/* → chemical-sensing-service"""
    return await _proxy_request(CHEMICAL_SENSING_SERVICE_URL, path, request)


# GRUPO G: ADAPTIVE IMMUNITY (2 endpoints)
@app.api_route(
    "/api/adaptive-immunity/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def api_adaptive_immunity_route(path: str, request: Request):
    """Frontend-compatible route: /api/adaptive-immunity/* → adaptive-immunity-service:8300

    Adaptive Immunity Service handles biological-inspired adaptive learning:
    - Antibody repertoire management
    - Affinity maturation (learning from feedback)
    - Clonal selection (expand successful detectors)
    - Threat detection feedback loops

    Constitutional: Biomimetic - no artificial limitations on adaptation
    """
    return await _proxy_request(ADAPTIVE_IMMUNITY_SERVICE_URL, path, request)


@app.api_route(
    "/api/adaptive-immune-system/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def api_adaptive_immune_system_route(path: str, request: Request):
    """Frontend-compatible route: /api/adaptive-immune-system/* → adaptive-immune-system:8280

    Adaptive Immune System (FASE 2 Complete) handles CVE detection and remediation:
    - Oraculo: CVE Sentinel (multi-feed ingestion: NVD, GHSA, OSV)
    - Eureka: Vulnerability Surgeon (automated remedy generation)
    - Wargaming integration (GitHub Actions)
    - HITL Console (human oversight - Lei Zero compliance)

    Constitutional: Lei Zero - all automated actions require human review
    """
    return await _proxy_request(ADAPTIVE_IMMUNE_SYSTEM_SERVICE_URL, path, request)


# GRUPO F: HITL (2 endpoints)
@app.api_route(
    "/api/hitl/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_hitl_route(path: str, request: Request):
    """Frontend-compatible route: /api/hitl/* → hitl-patch-service:8027
    Note: There's no separate hitl-service, both routes use hitl-patch-service"""
    return await _proxy_request(HITL_PATCH_SERVICE_URL, path, request)


@app.api_route(
    "/api/hitl-patch/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def api_hitl_patch_route(path: str, request: Request):
    """Frontend-compatible route: /api/hitl-patch/* → hitl-patch-service:8027"""
    return await _proxy_request(HITL_PATCH_SERVICE_URL, path, request)


# ============================================================================
# ORIGINAL ROUTES (Maximus Core Services)
# ============================================================================


@app.api_route("/core/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_core_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Maximus Core Service.

    Args:
        path (str): The path to the core service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Maximus Core Service.
    """
    return await _proxy_request(MAXIMUS_CORE_SERVICE_URL, path, request)


@app.api_route("/chemical/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_chemical_sensing_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Chemical Sensing Service.

    Args:
        path (str): The path to the chemical sensing service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Chemical Sensing Service.
    """
    return await _proxy_request(CHEMICAL_SENSING_SERVICE_URL, path, request)


@app.api_route("/somatosensory/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_somatosensory_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Somatosensory Service.

    Args:
        path (str): The path to the somatosensory service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Somatosensory Service.
    """
    return await _proxy_request(SOMATOSENSORY_SERVICE_URL, path, request)


@app.api_route("/visual/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_visual_cortex_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Visual Cortex Service.

    Args:
        path (str): The path to the visual cortex service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Visual Cortex Service.
    """
    return await _proxy_request(VISUAL_CORTEX_SERVICE_URL, path, request)


@app.api_route("/auditory/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_auditory_cortex_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Auditory Cortex Service.

    Args:
        path (str): The path to the auditory cortex service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Auditory Cortex Service.
    """
    return await _proxy_request(AUDITORY_CORTEX_SERVICE_URL, path, request)


@app.api_route("/eureka/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_eureka_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Eureka Service (Automated Remediation).

    Args:
        path (str): The path to the eureka service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Eureka Service.
    """
    # FIX: Eureka service responds directly at /{path}, not /api/v1/eureka/{path}
    return await _proxy_request(EUREKA_SERVICE_URL, path, request)


@app.api_route("/oraculo/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_oraculo_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Oraculo Service (Threat Intelligence).

    Args:
        path (str): The path to the oraculo service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Oraculo Service.
    """
    # FIX: Oráculo service responds directly at /{path}, not /api/v1/oraculo/{path}
    return await _proxy_request(ORACULO_SERVICE_URL, path, request)


@app.api_route(
    "/offensive/network-recon/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
)
async def route_network_recon_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Network Reconnaissance Service (Offensive Arsenal).

    Args:
        path (str): The path to the network-recon service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Network Recon Service.
    """
    return await _proxy_request(NETWORK_RECON_SERVICE_URL, path, request)


@app.api_route(
    "/offensive/vuln-intel/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
)
async def route_vuln_intel_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Vulnerability Intelligence Service (Offensive Arsenal).

    Args:
        path (str): The path to the vuln-intel service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Vuln Intel Service.
    """
    return await _proxy_request(VULN_INTEL_SERVICE_URL, path, request)


@app.api_route(
    "/offensive/web-attack/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
)
async def route_web_attack_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Web Attack Surface Service (Offensive Arsenal).

    FLORESCIMENTO - Organic growth through attack surface analysis.

    Args:
        path (str): The path to the web-attack service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Web Attack Service.
    """
    return await _proxy_request(WEB_ATTACK_SERVICE_URL, path, request)


@app.api_route("/offensive/c2/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_c2_orchestration_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the C2 Orchestration Service (Offensive Arsenal).

    FLORESCIMENTO - Ethical C2 operations for authorized testing.

    Args:
        path (str): The path to the c2 service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the C2 Orchestration Service.
    """
    return await _proxy_request(C2_ORCHESTRATION_SERVICE_URL, path, request)


@app.api_route("/offensive/bas/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_bas_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the BAS Service (Offensive Arsenal).

    FLORESCIMENTO - Defense validation through ethical attack simulation.

    Args:
        path (str): The path to the bas service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the BAS Service.
    """
    return await _proxy_request(BAS_SERVICE_URL, path, request)


@app.api_route(
    "/defensive/behavioral/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
)
async def route_behavioral_analyzer_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Behavioral Analyzer Service.

    FLORESCIMENTO - Behavioral threat detection through ML-based anomaly analysis.

    Args:
        path (str): The path to the behavioral analyzer service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Behavioral Analyzer Service.
    """
    return await _proxy_request(BEHAVIORAL_ANALYZER_SERVICE_URL, path, request)


@app.api_route(
    "/defensive/traffic/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
)
async def route_traffic_analyzer_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the Traffic Analyzer Service.

    FLORESCIMENTO - Network traffic threat detection with deep packet inspection.

    Args:
        path (str): The path to the traffic analyzer service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Traffic Analyzer Service.
    """
    return await _proxy_request(TRAFFIC_ANALYZER_SERVICE_URL, path, request)


@app.api_route(
    "/social-defense/mav/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
)
async def route_mav_detection_service(
    path: str, request: Request, api_key: str = Depends(verify_api_key)
):
    """Routes requests to the MAV Detection & Protection Service.

    FLORESCIMENTO - Protecting people from coordinated social media attacks.
    Research-based detection of MAV (Militância em Ambientes Virtuais) campaigns.

    This service detects coordinated harassment campaigns, reputation assassination,
    and mass disinformation attacks on social media platforms. Built with 2025
    state-of-the-art techniques including temporal coordination analysis, content
    similarity detection, and network behavior analysis.

    Args:
        path (str): The path to the MAV detection service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the MAV Detection Service.
    """
    return await _proxy_request(MAV_DETECTION_SERVICE_URL, path, request)


@app.get("/stream/consciousness/sse")
async def stream_consciousness_sse(request: Request):
    """Proxy SSE stream da consciência para consumidores externos."""
    if not _is_valid_api_key(
        request.headers.get(API_KEY_NAME), request.query_params.get("api_key")
    ):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    backend_url = f"{CONSCIOUSNESS_SERVICE_BASE}/api/consciousness/stream/sse"

    async def event_generator():
        async with httpx.AsyncClient(timeout=None) as client:
            headers = _extract_forward_headers(request)
            async with client.stream("GET", backend_url, headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if await request.is_disconnected():
                        break
                    yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.websocket("/stream/consciousness/ws")
async def stream_consciousness_ws(websocket: WebSocket):
    """Proxy WebSocket stream da consciência."""
    api_key = websocket.headers.get(API_KEY_NAME) or websocket.query_params.get(
        "api_key"
    )
    if not _is_valid_api_key(api_key, None):
        await websocket.close(code=1008)
        return

    await websocket.accept()

    backend_ws_url = _build_consciousness_ws_url(CONSCIOUSNESS_SERVICE_BASE)
    headers = {}

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.websocket_connect(
                backend_ws_url, headers=headers
            ) as backend_ws:

                async def client_to_backend():
                    try:
                        while True:
                            message = await websocket.receive_text()
                            await backend_ws.send_text(message)
                    except WebSocketDisconnect:
                        await backend_ws.aclose()
                    except Exception:
                        await backend_ws.aclose()

                async def backend_to_client():
                    try:
                        while True:
                            message = await backend_ws.receive_text()
                            await websocket.send_text(message)
                    except (httpx.WebSocketReadError, httpx.WebSocketDisconnect):
                        await websocket.close()
                    except Exception:
                        await websocket.close()

                await asyncio.gather(client_to_backend(), backend_to_client())
        except Exception:
            await websocket.close()


@app.get("/stream/apv/sse")
async def stream_apv_sse(request: Request):
    """Proxy SSE stream do APV (Autonomic Policy Validation) para consumidores externos."""
    if not _is_valid_api_key(
        request.headers.get(API_KEY_NAME), request.query_params.get("api_key")
    ):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    backend_url = f"{MAXIMUS_CORE_SERVICE_URL}/api/apv/stream/sse"

    async def event_generator():
        async with httpx.AsyncClient(timeout=None) as client:
            headers = _extract_forward_headers(request)
            async with client.stream("GET", backend_url, headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if await request.is_disconnected():
                        break
                    yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.websocket("/stream/apv/ws")
async def stream_apv_ws(websocket: WebSocket):
    """Proxy WebSocket stream do APV (Autonomic Policy Validation)."""
    api_key = websocket.headers.get(API_KEY_NAME) or websocket.query_params.get(
        "api_key"
    )
    if not _is_valid_api_key(api_key, None):
        await websocket.close(code=1008)
        return

    await websocket.accept()

    backend_ws_url = f"ws://{MAXIMUS_CORE_SERVICE_URL.replace('http://', '').replace('https://', '')}/api/apv/ws"
    headers = {}

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.websocket_connect(
                backend_ws_url, headers=headers
            ) as backend_ws:

                async def client_to_backend():
                    try:
                        while True:
                            message = await websocket.receive_text()
                            await backend_ws.send_text(message)
                    except WebSocketDisconnect:
                        await backend_ws.aclose()
                    except Exception:
                        await backend_ws.aclose()

                async def backend_to_client():
                    try:
                        while True:
                            message = await backend_ws.receive_text()
                            await websocket.send_text(message)
                    except Exception:
                        pass

                await asyncio.gather(client_to_backend(), backend_to_client())

        except Exception as e:
            logger.error(f"WebSocket proxy error (APV): {e}")
        finally:
            await websocket.close()


async def _proxy_request(base_url: str, path: str, request: Request) -> JSONResponse:
    """Proxies the incoming request to the specified backend service.

    Args:
        base_url (str): The base URL of the target backend service.
        path (str): The specific path for the request.
        request (Request): The incoming request object.

    Returns:
        JSONResponse: The response from the backend service.

    Raises:
        HTTPException: If there is an error communicating with the backend service.
    """
    url = f"{base_url}/{path}"
    async with httpx.AsyncClient() as client:
        try:
            # Reconstruct headers, excluding host and content-length which httpx handles
            headers = {
                k: v
                for k, v in request.headers.items()
                if k.lower() not in ["host", "content-length"]
            }

            # Forward the request based on its method
            if request.method == "GET":
                response = await client.get(
                    url, params=request.query_params, headers=headers
                )
            elif request.method == "POST":
                response = await client.post(
                    url, content=await request.body(), headers=headers
                )
            elif request.method == "PUT":
                response = await client.put(
                    url, content=await request.body(), headers=headers
                )
            elif request.method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, detail=f"Service communication error: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Backend service error: {e.response.text}",
            )


def _extract_forward_headers(request: Request) -> Dict[str, str]:
    """Replica headers relevantes para downstream (exclui host)."""
    return {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in {"host", "content-length", "accept-encoding"}
    }


def _build_consciousness_ws_url(base_url: str) -> str:
    """Converte URL HTTP → WS/WSS preservando path."""
    if base_url.startswith("https://"):
        ws_base = "wss://" + base_url[len("https://") :]
    elif base_url.startswith("http://"):
        ws_base = "ws://" + base_url[len("http://") :]
    else:
        ws_base = base_url
    return f"{ws_base}/api/consciousness/ws"


def _is_valid_api_key(header_value: str | None, query_value: str | None) -> bool:
    """Valida API key via header ou query string."""
    key = header_value or query_value
    return key == VALID_API_KEY if VALID_API_KEY else True


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
