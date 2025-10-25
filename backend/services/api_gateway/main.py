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

import os
from typing import Dict

import asyncio
import httpx
import uvicorn
import logging
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from starlette.websockets import WebSocketDisconnect

# Import dynamic router
from gateway_router import get_service_url, ServiceNotFoundError, get_circuit_breaker_status, get_cache_stats

# Import health cache
from health_cache import HealthCheckCache

# Import case transformation middleware
from case_middleware import CaseTransformationMiddleware

logger = logging.getLogger(__name__)

# Global health cache instance
health_cache: HealthCheckCache = None

app = FastAPI(
    title="Maximus API Gateway (Dynamic Routing)",
    version="2.0.0",
    description="API Gateway with Service Registry integration"
)

# Add case transformation middleware (snake_case ↔ camelCase)
app.add_middleware(CaseTransformationMiddleware)
logger.info("✅ Case transformation middleware enabled (snake_case ↔ camelCase)")

# Configuration for backend services
MAXIMUS_CORE_SERVICE_URL = os.getenv("MAXIMUS_CORE_SERVICE_URL", "http://localhost:8100")
CHEMICAL_SENSING_SERVICE_URL = os.getenv("CHEMICAL_SENSING_SERVICE_URL", "http://localhost:8101")
SOMATOSENSORY_SERVICE_URL = os.getenv("SOMATOSENSORY_SERVICE_URL", "http://localhost:8102")
VISUAL_CORTEX_SERVICE_URL = os.getenv("VISUAL_CORTEX_SERVICE_URL", "http://localhost:8103")
AUDITORY_CORTEX_SERVICE_URL = os.getenv("AUDITORY_CORTEX_SERVICE_URL", "http://localhost:8104")
EUREKA_SERVICE_URL = os.getenv("EUREKA_SERVICE_URL", "http://localhost:8024")
ORACULO_SERVICE_URL = os.getenv("ORACULO_SERVICE_URL", "http://localhost:8026")

CONSCIOUSNESS_SERVICE_BASE = os.getenv("CONSCIOUSNESS_SERVICE_URL", MAXIMUS_CORE_SERVICE_URL)

# API Key for authentication (simple example)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# In a real application, you would have a secure way to store and validate API keys
VALID_API_KEY = os.getenv("MAXIMUS_API_KEY", "supersecretkey")


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
    global health_cache

    print("🚀 Starting Maximus API Gateway...")

    # Initialize health check cache (3-layer architecture)
    # Redis client injection via environment configuration in production
    health_cache = HealthCheckCache(redis_client=None)
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
        "service_discovery_cache": get_cache_stats()
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
            health_endpoint="/health"
        )

        return {
            "service_name": service_name,
            "service_url": service_url,
            "healthy": health_status.healthy,
            "status_code": health_status.status_code,
            "response_time_ms": round(health_status.response_time_ms, 2),
            "cached": health_status.cached,
            "cache_layer": health_status.cache_layer,
            "timestamp": health_status.timestamp
        }

    except ServiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Health check failed for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# ============================================================================
# DYNAMIC ROUTING - New in v2.0
# ============================================================================

@app.api_route("/v2/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
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
                   f"It may be down or not registered in the service registry."
        )

    except Exception as e:
        logger.error(f"Dynamic routing error for {service_name}/{path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error routing to '{service_name}': {str(e)}"
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
        "limit": body.get("num_results", 10)
    }
    
    service_url = os.getenv("GOOGLE_OSINT_SERVICE_URL", "http://google_osint_service:8016")
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            response = await client.post(f"{service_url}/query_osint", json=adapted_body)
            response.raise_for_status()
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Google OSINT service unavailable: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


@app.post("/api/domain/analyze")
async def domain_analyze_adapter(request: Request):
    """Adapter: Domain Analysis.
    Translates: gateway format → microservice /query_domain format.
    """
    body = await request.json()
    adapted_body = {
        "domain_name": body.get("domain", ""),
        "query": body.get("query", "Analyze this domain")
    }
    
    service_url = os.getenv("DOMAIN_SERVICE_URL", "http://domain_service:8014")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{service_url}/query_domain", json=adapted_body)
            response.raise_for_status()
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Domain service unavailable: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


@app.post("/api/ip/analyze")
async def ip_analyze_adapter(request: Request):
    """Adapter: IP Intelligence Analysis.
    Translates: gateway format → microservice /query_ip format.
    """
    body = await request.json()
    adapted_body = {
        "ip_address": body.get("ip", ""),
        "query": body.get("query", "Analyze this IP address")
    }
    
    service_url = os.getenv("IP_INTELLIGENCE_SERVICE_URL", "http://ip_intelligence_service:8034")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{service_url}/query_ip", json=adapted_body)
            response.raise_for_status()
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"IP Intelligence service unavailable: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


# ============================================================================
# ORIGINAL ROUTES (Maximus Core Services)
# ============================================================================


@app.api_route("/core/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_core_service(path: str, request: Request, api_key: str = Depends(verify_api_key)):
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
async def route_chemical_sensing_service(path: str, request: Request, api_key: str = Depends(verify_api_key)):
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
async def route_somatosensory_service(path: str, request: Request, api_key: str = Depends(verify_api_key)):
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
async def route_visual_cortex_service(path: str, request: Request, api_key: str = Depends(verify_api_key)):
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
async def route_auditory_cortex_service(path: str, request: Request, api_key: str = Depends(verify_api_key)):
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
async def route_eureka_service(path: str, request: Request, api_key: str = Depends(verify_api_key)):
    """Routes requests to the Eureka Service (Automated Remediation).

    Args:
        path (str): The path to the eureka service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Eureka Service.
    """
    return await _proxy_request(EUREKA_SERVICE_URL, f"api/v1/eureka/{path}", request)


@app.api_route("/oraculo/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_oraculo_service(path: str, request: Request, api_key: str = Depends(verify_api_key)):
    """Routes requests to the Oraculo Service (Threat Intelligence).

    Args:
        path (str): The path to the oraculo service endpoint.
        request (Request): The incoming request object.
        api_key (str): The validated API key.

    Returns:
        JSONResponse: The response from the Oraculo Service.
    """
    return await _proxy_request(ORACULO_SERVICE_URL, f"api/v1/oraculo/{path}", request)


@app.get("/stream/consciousness/sse")
async def stream_consciousness_sse(request: Request):
    """Proxy SSE stream da consciência para consumidores externos."""
    if not _is_valid_api_key(request.headers.get(API_KEY_NAME), request.query_params.get("api_key")):
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
    api_key = websocket.headers.get(API_KEY_NAME) or websocket.query_params.get("api_key")
    if not _is_valid_api_key(api_key, None):
        await websocket.close(code=1008)
        return

    await websocket.accept()

    backend_ws_url = _build_consciousness_ws_url(CONSCIOUSNESS_SERVICE_BASE)
    headers = {}

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.websocket_connect(backend_ws_url, headers=headers) as backend_ws:

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
    if not _is_valid_api_key(request.headers.get(API_KEY_NAME), request.query_params.get("api_key")):
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
    api_key = websocket.headers.get(API_KEY_NAME) or websocket.query_params.get("api_key")
    if not _is_valid_api_key(api_key, None):
        await websocket.close(code=1008)
        return

    await websocket.accept()

    backend_ws_url = f"ws://{MAXIMUS_CORE_SERVICE_URL.replace('http://', '').replace('https://', '')}/api/apv/ws"
    headers = {}

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.websocket_connect(backend_ws_url, headers=headers) as backend_ws:

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
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]}

            # Forward the request based on its method
            if request.method == "GET":
                response = await client.get(url, params=request.query_params, headers=headers)
            elif request.method == "POST":
                response = await client.post(url, content=await request.body(), headers=headers)
            elif request.method == "PUT":
                response = await client.put(url, content=await request.body(), headers=headers)
            elif request.method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Service communication error: {e}")
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
