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

from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_orchestrator import AIOrchestrator

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


class AutomatedInvestigationRequest(BaseModel):
    """Request model for automated OSINT investigation.

    Attributes:
        username (Optional[str]): Target username for investigation.
        email (Optional[str]): Target email for investigation.
        phone (Optional[str]): Target phone number for investigation.
        name (Optional[str]): Target real name for investigation.
        location (Optional[str]): Target location for investigation.
        context (Optional[str]): Investigation context/purpose.
        image_url (Optional[str]): Target image URL for investigation.
    """

    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    context: Optional[str] = None
    image_url: Optional[str] = None


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
    print(f"[API] Starting OSINT investigation: {request.investigation_type} for {request.query}")
    response = await ai_orchestrator.start_investigation(request.query, request.investigation_type, request.parameters)
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


@app.post("/api/investigate/auto")
async def automated_investigation(
    request: AutomatedInvestigationRequest,
) -> Dict[str, Any]:
    """Executes automated OSINT investigation with AI orchestration.

    This endpoint is the main entry point for comprehensive automated OSINT
    investigations, orchestrating multiple data sources and analyzers based
    on provided identifiers.

    Args:
        request (AutomatedInvestigationRequest): Investigation parameters including
            username, email, phone, name, location, context, and image_url.

    Returns:
        Dict[str, Any]: Comprehensive investigation report including:
            - investigation_id: Unique investigation identifier
            - risk_assessment: Risk level and scoring
            - executive_summary: High-level findings summary
            - patterns_found: Detected behavioral and digital patterns
            - recommendations: AI-generated actionable recommendations
            - data_sources: List of sources consulted
            - confidence_score: Overall confidence in findings (0-100)
            - timestamp: Investigation completion timestamp

    Raises:
        HTTPException: If no valid identifier is provided or investigation fails.
    """
    # Validate at least one identifier is provided
    if not any([
        request.username,
        request.email,
        request.phone,
        request.name,
        request.image_url,
    ]):
        raise HTTPException(
            status_code=400,
            detail="At least one identifier (username, email, phone, name, or image_url) must be provided."
        )

    # Execute automated investigation
    result = await ai_orchestrator.automated_investigation(
        username=request.username,
        email=request.email,
        phone=request.phone,
        name=request.name,
        location=request.location,
        context=request.context,
        image_url=request.image_url,
    )

    return {
        "success": True,
        "data": result,
        "message": "Automated OSINT investigation completed successfully."
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8036)
