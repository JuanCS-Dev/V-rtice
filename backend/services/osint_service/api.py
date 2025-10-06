"""Maximus OSINT Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus OSINT Service.
It initializes and configures the FastAPI application, sets up event handlers
for startup and shutdown, and defines the API endpoints for initiating OSINT
investigations, querying their status, and retrieving reports.

It orchestrates the entire OSINT workflow, from data collection (scraping) to
analysis and report generation, leveraging specialized scrapers, analyzers,
and AI processing capabilities. This service is crucial for transforming raw
open-source information into actionable intelligence, supporting threat
intelligence, risk assessment, and strategic planning within the Maximus AI system.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_orchestrator import AIOrchestrator
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Maximus OSINT Service", version="1.0.0")

# Initialize OSINT Orchestrator
ai_orchestrator = AIOrchestrator()


class StartInvestigationRequest(BaseModel):
    """Request model for starting an OSINT investigation.

    Attributes:
        query (str): The primary query for the investigation (e.g., username, email, domain).
        investigation_type (str): The type of investigation (e.g., 'person_recon', 'domain_analysis').
        parameters (Optional[Dict[str, Any]]): Additional parameters for the investigation.
    """

    query: str
    investigation_type: str
    parameters: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the OSINT Service."""
    print("🔍 Starting Maximus OSINT Service...")
    print("✅ Maximus OSINT Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the OSINT Service."""
    print("👋 Shutting down Maximus OSINT Service...")
    print("🛑 Maximus OSINT Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the OSINT Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "OSINT Service is operational."}


@app.post("/start_investigation")
async def start_osint_investigation(
    request: StartInvestigationRequest,
) -> Dict[str, Any]:
    """Initiates a new OSINT investigation.

    Args:
        request (StartInvestigationRequest): The request body containing the query and investigation parameters.

    Returns:
        Dict[str, Any]: A dictionary containing the investigation ID and initial status.
    """
    print(
        f"[API] Starting OSINT investigation: {request.investigation_type} for {request.query}"
    )
    response = await ai_orchestrator.start_investigation(
        request.query, request.investigation_type, request.parameters
    )
    return response


@app.get("/investigation/{investigation_id}/status")
async def get_investigation_status(investigation_id: str) -> Dict[str, Any]:
    """Retrieves the current status of a specific OSINT investigation.

    Args:
        investigation_id (str): The ID of the investigation.

    Returns:
        Dict[str, Any]: The current status and details of the investigation.

    Raises:
        HTTPException: If the investigation ID is not found.
    """
    status = ai_orchestrator.get_investigation_status(investigation_id)
    if not status:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return status


@app.get("/investigation/{investigation_id}/report")
async def get_investigation_report(investigation_id: str) -> Dict[str, Any]:
    """Retrieves the final report of a completed OSINT investigation.

    Args:
        investigation_id (str): The ID of the investigation.

    Returns:
        Dict[str, Any]: The final report of the investigation.

    Raises:
        HTTPException: If the investigation ID is not found or the report is not yet available.
    """
    status = ai_orchestrator.get_investigation_status(investigation_id)
    if not status:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    if status["status"] != "completed":
        raise HTTPException(status_code=409, detail="Investigation not yet completed.")
    return status["results"]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8036)
