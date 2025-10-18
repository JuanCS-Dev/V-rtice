"""Maximus ADR Core Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Automated Detection
and Response (ADR) Core Service. It initializes and configures the FastAPI
application, sets up event handlers for startup and shutdown, and defines the
API endpoints for interacting with the ADR capabilities.

It orchestrates the integration of various ADR components, including detection
engines, response engines, machine learning models, and external connectors,
to provide a comprehensive and automated cybersecurity defense solution.
"""

from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from connectors.ip_intelligence_connector import IpIntelligenceConnector
from connectors.threat_intel_connector import ThreatIntelConnector

# Assuming these modules exist and are correctly structured within ADR
from engines.detection_engine import DetectionEngine
from engines.ml_engine import MLEngine
from engines.response_engine import ResponseEngine
from models.enums import ResponseActionType
from models.schemas import (
    DetectionResult,
    IpIntelligenceData,
    ResponseAction,
    ThreatIntelData,
)
from playbooks.loader import PlaybookLoader
from utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

app = FastAPI(title="Maximus ADR Core Service", version="1.0.0")

# Initialize engines and connectors
detection_engine = DetectionEngine()
response_engine = ResponseEngine()
ml_engine = MLEngine()
threat_intel_connector = ThreatIntelConnector()
ip_intelligence_connector = IpIntelligenceConnector()
playbook_loader = PlaybookLoader()


class DetectRequest(BaseModel):
    """Request model for triggering a detection.

    Attributes:
        event_data (Dict[str, Any]): The raw event data to be analyzed.
        source (str): The source of the event (e.g., 'siem', 'endpoint').
    """

    event_data: Dict[str, Any]
    source: str


class RespondRequest(BaseModel):
    """Request model for triggering a response action.

    Attributes:
        incident_id (str): The ID of the incident to respond to.
        action_type (ResponseActionType): The type of response action to take.
        parameters (Optional[Dict[str, Any]]): Parameters for the response action.
    """

    incident_id: str
    action_type: ResponseActionType
    parameters: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the ADR Core Service."""
    logger.info("🚀 Starting Maximus ADR Core Service...")
    try:
        await playbook_loader.load_playbooks("playbooks")  # Load playbooks from a directory
        logger.info(f"Loaded {len(playbook_loader.get_all_playbooks())} playbooks.")
    except Exception as e:
        logger.warning(f"⚠️  Could not load playbooks: {e}. Service will run with limited functionality.")
    logger.info("✅ Maximus ADR Core Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the ADR Core Service."""
    logger.info("👋 Shutting down Maximus ADR Core Service...")
    logger.info("🛑 Maximus ADR Core Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the ADR Core Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "ADR Core Service is operational."}


@app.post("/detect", response_model=List[DetectionResult])
async def detect_threat(request: DetectRequest) -> List[DetectionResult]:
    """Analyzes incoming event data for potential threats.

    Args:
        request (DetectRequest): The request body containing event data and source.

    Returns:
        List[DetectionResult]: A list of detected threats.
    """
    logger.info(f"Received detection request from {request.source}")
    try:
        detections = await detection_engine.analyze_event(request.event_data, request.source)
        # Simulate ML analysis for additional context
        for det in detections:
            ml_score = await ml_engine.predict_threat_score(det.event_data)
            det.ml_score = ml_score
        return detections
    except Exception as e:
        logger.error(f"Error during threat detection: {e}")
        raise HTTPException(status_code=500, detail=f"Threat detection failed: {str(e)}")


@app.post("/respond", response_model=ResponseAction)
async def respond_to_incident(request: RespondRequest) -> ResponseAction:
    """Triggers a response action for a given incident.

    Args:
        request (RespondRequest): The request body containing incident ID, action type, and parameters.

    Returns:
        ResponseAction: The details of the executed response action.
    """
    logger.info(f"Received response request for incident {request.incident_id} with action {request.action_type}")
    try:
        # Load relevant playbook
        playbook = playbook_loader.get_playbook_for_incident(request.incident_id)  # Simplified
        if not playbook:
            raise HTTPException(
                status_code=404,
                detail=f"No playbook found for incident {request.incident_id}",
            )

        action_result = await response_engine.execute_action(
            request.incident_id, request.action_type, request.parameters
        )
        return action_result
    except Exception as e:
        logger.error(f"Error during incident response: {e}")
        raise HTTPException(status_code=500, detail=f"Incident response failed: {str(e)}")


@app.get("/threat_intel/{indicator}", response_model=ThreatIntelData)
async def get_threat_intelligence(indicator: str) -> ThreatIntelData:
    """Retrieves threat intelligence data for a given indicator.

    Args:
        indicator (str): The threat indicator (e.g., IP address, hash).

    Returns:
        ThreatIntelData: Threat intelligence information.
    """
    logger.info(f"Retrieving threat intelligence for indicator: {indicator}")
    try:
        data = await threat_intel_connector.get_intelligence(indicator)
        return data
    except Exception as e:
        logger.error(f"Error retrieving threat intelligence: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve threat intelligence: {str(e)}")


@app.get("/ip_intel/{ip_address}", response_model=IpIntelligenceData)
async def get_ip_intelligence(ip_address: str) -> IpIntelligenceData:
    """Retrieves IP intelligence data for a given IP address.

    Args:
        ip_address (str): The IP address to query.

    Returns:
        IpIntelligenceData: IP intelligence information.
    """
    logger.info(f"Retrieving IP intelligence for IP: {ip_address}")
    try:
        data = await ip_intelligence_connector.get_ip_info(ip_address)
        return data
    except Exception as e:
        logger.error(f"Error retrieving IP intelligence: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve IP intelligence: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
