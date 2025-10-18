"""Maximus Integration Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Integration Service.
It initializes and configures the FastAPI application, sets up event handlers
for startup and shutdown, and defines the API endpoints for facilitating
communication and data exchange between various Maximus AI services and external
systems.

It handles API connections, data translation, and workflow orchestration,
providing a unified interface for Maximus AI to interact with the broader
digital ecosystem. This service is crucial for enabling Maximus to leverage
external tools, data sources, and services, extending its capabilities and
operational reach.
"""

import os
from typing import Any, Dict, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Maximus Integration Service", version="1.0.0")

# External service URLs (from environment or defaults)
MOCK_EXTERNAL_CRM_URL = os.getenv("MOCK_EXTERNAL_CRM_URL", "http://localhost:8030/crm")
MOCK_EXTERNAL_SIEM_URL = os.getenv("MOCK_EXTERNAL_SIEM_URL", "http://localhost:8031/siem")


class ExternalServiceRequest(BaseModel):
    """Request model for interacting with an external service.

    Attributes:
        service_name (str): The name of the external service to interact with.
        endpoint (str): The specific endpoint of the external service.
        method (str): The HTTP method to use (e.g., 'GET', 'POST').
        payload (Optional[Dict[str, Any]]): The request payload for POST/PUT methods.
        headers (Optional[Dict[str, str]]): Additional headers for the request.
    """

    service_name: str
    endpoint: str
    method: str = "GET"
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Integration Service."""
    print("🔗 Starting Maximus Integration Service...")
    print("✅ Maximus Integration Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Integration Service."""
    print("👋 Shutting down Maximus Integration Service...")
    print("🛑 Maximus Integration Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Integration Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Integration Service is operational."}


@app.post("/interact_external_service")
async def interact_external_service(request: ExternalServiceRequest) -> Dict[str, Any]:
    """Facilitates interaction with external services.

    Args:
        request (ExternalServiceRequest): The request body containing external service interaction details.

    Returns:
        Dict[str, Any]: The response from the external service.

    Raises:
        HTTPException: If the external service is unknown or an error occurs during interaction.
    """
    print(f"[API] Interacting with external service: {request.service_name} at {request.endpoint}")

    base_url = None
    if request.service_name == "crm":
        base_url = MOCK_EXTERNAL_CRM_URL
    elif request.service_name == "siem":
        base_url = MOCK_EXTERNAL_SIEM_URL
    else:
        raise HTTPException(status_code=400, detail=f"Unknown external service: {request.service_name}")

    url = f"{base_url}/{request.endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response: httpx.Response
            if request.method.upper() == "GET":
                response = await client.get(url, headers=request.headers)
            elif request.method.upper() == "POST":
                response = await client.post(url, json=request.payload, headers=request.headers)
            elif request.method.upper() == "PUT":
                response = await client.put(url, json=request.payload, headers=request.headers)
            elif request.method.upper() == "DELETE":
                response = await client.delete(url, headers=request.headers)
            else:
                raise HTTPException(status_code=405, detail=f"Method {request.method} not allowed.")

            response.raise_for_status()
            return {
                "status": "success",
                "external_response": response.json(),
                "timestamp": datetime.now().isoformat(),
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"External service communication error: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"External service error: {e.response.text}",
            )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8025)
