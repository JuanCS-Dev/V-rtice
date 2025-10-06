"""Maximus Immunis API Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Immunis
API Service. It acts as the central gateway for interacting with the entire
Immunis (AI Immune System) ecosystem, exposing a unified API for managing
immune responses, monitoring AI health, and adapting to new threats.

Endpoints are provided for:
- Submitting threat alerts or anomaly reports.
- Triggering specific immune responses.
- Querying the status of the AI immune system.
- Retrieving threat intelligence and immune system logs.

This API allows other Maximus AI services or external security systems to
integrate with and leverage the advanced self-defense capabilities of the
Maximus AI Immune System.
"""

import asyncio
from datetime import datetime
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Maximus Immunis API Service", version="1.0.0")

# Configuration for Immunis sub-services (mock URLs)
IMMUNIS_BCELL_SERVICE_URL = os.getenv(
    "IMMUNIS_BCELL_SERVICE_URL", "http://localhost:8022"
)
IMMUNIS_TCELL_SERVICE_URL = os.getenv(
    "IMMUNIS_TCELL_SERVICE_URL", "http://localhost:8023"
)
IMMUNIS_MACROPHAGE_SERVICE_URL = os.getenv(
    "IMMUNIS_MACROPHAGE_SERVICE_URL", "http://localhost:8024"
)
IMMUNIS_NK_CELL_SERVICE_URL = os.getenv(
    "IMMUNIS_NK_CELL_SERVICE_URL", "http://localhost:8025"
)
IMMUNIS_NEUTROPHIL_SERVICE_URL = os.getenv(
    "IMMUNIS_NEUTROPHIL_SERVICE_URL", "http://localhost:8026"
)
IMMUNIS_DENDRITIC_SERVICE_URL = os.getenv(
    "IMMUNIS_DENDRITIC_SERVICE_URL", "http://localhost:8027"
)
IMMUNIS_HELPER_T_SERVICE_URL = os.getenv(
    "IMMUNIS_HELPER_T_SERVICE_URL", "http://localhost:8028"
)
IMMUNIS_CYTOTOXIC_T_SERVICE_URL = os.getenv(
    "IMMUNIS_CYTOTOXIC_T_SERVICE_URL", "http://localhost:8029"
)


class ThreatAlert(BaseModel):
    """Request model for submitting a threat alert.

    Attributes:
        threat_id (str): Unique identifier for the threat.
        threat_type (str): The type of threat (e.g., 'malware', 'intrusion', 'anomaly').
        severity (str): The severity of the threat (e.g., 'low', 'medium', 'high', 'critical').
        details (Dict[str, Any]): Detailed information about the threat.
        source (str): The source that detected the threat.
    """

    threat_id: str
    threat_type: str
    severity: str
    details: Dict[str, Any]
    source: str


class ImmuneResponseTrigger(BaseModel):
    """Request model for triggering a specific immune response.

    Attributes:
        response_type (str): The type of immune response to trigger (e.g., 'b_cell_activation', 't_cell_attack').
        target_id (str): The ID of the entity to target (e.g., 'malware_hash', 'compromised_host_id').
        parameters (Optional[Dict[str, Any]]): Additional parameters for the response.
    """

    response_type: str
    target_id: str
    parameters: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Immunis API Service."""
    print("🧬 Starting Maximus Immunis API Service...")
    print("✅ Maximus Immunis API Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Immunis API Service."""
    print("👋 Shutting down Maximus Immunis API Service...")
    print("🛑 Maximus Immunis API Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Immunis API Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Immunis API Service is operational."}


@app.post("/threat_alert")
async def submit_threat_alert(alert: ThreatAlert) -> Dict[str, Any]:
    """Submits a threat alert to the Immunis system for processing.

    Args:
        alert (ThreatAlert): The threat alert details.

    Returns:
        Dict[str, Any]: A dictionary confirming the alert submission and initial Immunis action.
    """
    print(
        f"[API] Received threat alert: {alert.threat_type} (Severity: {alert.severity}) from {alert.source}"
    )

    # Simulate routing to appropriate Immunis sub-service based on threat type/severity
    target_service_url = IMMUNIS_MACROPHAGE_SERVICE_URL  # Default for general threats
    if alert.threat_type == "malware":
        target_service_url = IMMUNIS_BCELL_SERVICE_URL  # B-cells for antibody production (signature generation)
    elif alert.threat_type == "intrusion":
        target_service_url = (
            IMMUNIS_CYTOTOXIC_T_SERVICE_URL  # Cytotoxic T-cells for direct attack
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{target_service_url}/process_threat", json=alert.dict()
            )
            response.raise_for_status()
            return {
                "status": "success",
                "message": "Threat alert submitted to Immunis.",
                "immunis_response": response.json(),
            }
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Error communicating with Immunis sub-service: {e}"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Immunis sub-service error: {e.response.text}",
        )


@app.post("/trigger_immune_response")
async def trigger_immune_response(trigger: ImmuneResponseTrigger) -> Dict[str, Any]:
    """Triggers a specific immune response within the Immunis system.

    Args:
        trigger (ImmuneResponseTrigger): The immune response trigger details.

    Returns:
        Dict[str, Any]: A dictionary confirming the response trigger and its status.
    """
    print(
        f"[API] Triggering immune response: {trigger.response_type} for target {trigger.target_id}"
    )

    target_service_url = IMMUNIS_MACROPHAGE_SERVICE_URL  # Default
    if "b_cell" in trigger.response_type.lower():
        target_service_url = IMMUNIS_BCELL_SERVICE_URL
    elif "t_cell" in trigger.response_type.lower():
        target_service_url = IMMUNIS_CYTOTOXIC_T_SERVICE_URL

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{target_service_url}/activate_response", json=trigger.dict()
            )
            response.raise_for_status()
            return {
                "status": "success",
                "message": "Immune response triggered.",
                "immunis_action": response.json(),
            }
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Error communicating with Immunis sub-service: {e}"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Immunis sub-service error: {e.response.text}",
        )


@app.get("/immunis_status")
async def get_immunis_status() -> Dict[str, Any]:
    """Retrieves the overall status of the AI Immune System.

    Returns:
        Dict[str, Any]: A dictionary summarizing the health and activity of the Immunis system.
    """
    # In a real system, this would aggregate status from all sub-services
    return {
        "timestamp": datetime.now().isoformat(),
        "overall_health": "optimal",
        "active_responses": 2,
        "threat_level": "low",
        "b_cell_status": "active",
        "t_cell_status": "monitoring",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8021)
