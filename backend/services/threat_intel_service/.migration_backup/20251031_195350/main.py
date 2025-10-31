"""Maximus Threat Intelligence Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Threat Intelligence
Service. It initializes and configures the FastAPI application, sets up event
handlers for startup and shutdown, and defines the API endpoints for gathering,
processing, and disseminating actionable threat intelligence.

It orchestrates the integration with external Threat Intelligence Platforms (TIPs)
and feeds, analyzes raw threat data to identify indicators of compromise (IoCs),
tactics, techniques, and procedures (TTPs), and threat actor profiles. This
service is crucial for enriching internal security events with relevant threat
context and providing real-time threat intelligence to other Maximus AI services.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from offline_engine import OfflineThreatIntelEngine

app = FastAPI(title="Maximus Threat Intelligence Service", version="1.0.0")

# Initialize threat intelligence engines
offline_engine = OfflineThreatIntelEngine()


class ThreatIntelQuery(BaseModel):
    """Request model for querying threat intelligence.

    Attributes:
        indicator (str): The indicator to query (e.g., IP address, domain, hash).
        indicator_type (str): The type of indicator (e.g., 'ip', 'domain', 'hash').
        context (Optional[Dict[str, Any]]): Additional context for the query.
    """

    indicator: str
    indicator_type: str
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Threat Intelligence Service."""
    print("🚨 Starting Maximus Threat Intelligence Service...")
    print("✅ Maximus Threat Intelligence Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Threat Intelligence Service."""
    print("👋 Shutting down Maximus Threat Intelligence Service...")
    print("🛑 Maximus Threat Intelligence Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Threat Intelligence Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {
        "status": "healthy",
        "message": "Threat Intelligence Service is operational.",
    }


@app.post("/query_threat_intel")
async def query_threat_intelligence(request: ThreatIntelQuery) -> Dict[str, Any]:
    """Queries for threat intelligence based on an indicator.

    Args:
        request (ThreatIntelQuery): The request body containing the indicator and its type.

    Returns:
        Dict[str, Any]: A dictionary containing the threat intelligence results.
    """
    print(f"[API] Querying threat intelligence for {request.indicator_type}: {request.indicator}")

    # Simulate querying external TIPs or internal databases
    threat_intel_result = await offline_engine.get_threat_intel(request.indicator, request.indicator_type)

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "threat_intelligence": threat_intel_result,
    }


@app.get("/threat_intel_status")
async def get_threat_intel_status() -> Dict[str, Any]:
    """Retrieves the current status of the Threat Intelligence Service.

    Returns:
        Dict[str, Any]: A dictionary summarizing the service's status.
    """
    return await offline_engine.get_status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8043)
