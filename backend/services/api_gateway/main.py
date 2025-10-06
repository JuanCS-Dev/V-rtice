"""Maximus API Gateway - Main Application Entry Point.

This module serves as the main entry point for the Maximus API Gateway.
It is responsible for routing incoming requests to the appropriate backend
Maximus AI services, handling authentication, and ensuring secure and efficient
communication.

The API Gateway acts as a single entry point for all external interactions
with the Maximus AI system, providing a unified interface and abstracting the
complexity of the underlying microservices architecture.
"""

import os
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
import httpx
import uvicorn

app = FastAPI(title="Maximus API Gateway", version="1.0.0")

# Configuration for backend services
MAXIMUS_CORE_SERVICE_URL = os.getenv(
    "MAXIMUS_CORE_SERVICE_URL", "http://localhost:8000"
)
CHEMICAL_SENSING_SERVICE_URL = os.getenv(
    "CHEMICAL_SENSING_SERVICE_URL", "http://localhost:8001"
)
SOMATOSENSORY_SERVICE_URL = os.getenv(
    "SOMATOSENSORY_SERVICE_URL", "http://localhost:8002"
)
VISUAL_CORTEX_SERVICE_URL = os.getenv(
    "VISUAL_CORTEX_SERVICE_URL", "http://localhost:8003"
)
AUDITORY_CORTEX_SERVICE_URL = os.getenv(
    "AUDITORY_CORTEX_SERVICE_URL", "http://localhost:8004"
)

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
    print("🚀 Starting Maximus API Gateway...")
    print("✅ Maximus API Gateway started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the API Gateway."""
    print("👋 Shutting down Maximus API Gateway...")
    print("🛑 Maximus API Gateway shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the API Gateway.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Maximus API Gateway is operational."}


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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
