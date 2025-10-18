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
import os
from typing import Any, Dict, Optional, List

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_orchestrator import AIOrchestrator
from analyzers.breach_data_analyzer_refactored import BreachDataAnalyzer
from analyzers.google_dork_scanner_refactored import GoogleDorkScanner
from analyzers.dark_web_monitor_refactored import DarkWebMonitor

# ============================================
# MAXIMUS AI INTEGRATION
# ============================================

MAXIMUS_PREDICT_URL = os.getenv("MAXIMUS_PREDICT_URL", "http://maximus_predict:80")

async def get_maximus_strategy(target: str, target_type: str, depth: str = "medium") -> Dict[str, Any]:
    """Get investigation strategy from MAXIMUS AI."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MAXIMUS_PREDICT_URL}/osint/analyze",
                json={"target": target, "target_type": target_type, "investigation_depth": depth}
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        print(f"[MAXIMUS] Error: {e}")
        return {}

app = FastAPI(title="Maximus OSINT Service - MAXIMUS AI Orchestrated", version="2.0.0")

# Initialize OSINT Orchestrator
ai_orchestrator = AIOrchestrator()

# Initialize World-Class OSINT Tools
breach_analyzer = BreachDataAnalyzer(api_key=None)  # Will use env var
google_scanner = GoogleDorkScanner()
darkweb_monitor = DarkWebMonitor()


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


class BreachDataRequest(BaseModel):
    """Request model for breach data analysis.

    Attributes:
        target (str): Email or username to search for.
        search_type (str): Type of search ('email', 'username', 'domain', 'ip').
        include_unverified (bool): Include unverified breaches.
    """

    target: str
    search_type: str = "email"
    include_unverified: bool = False


class GoogleDorkRequest(BaseModel):
    """Request model for Google dorking.

    Attributes:
        target (str): Target domain or search term.
        categories (Optional[List[str]]): Dork categories to use.
        engines (Optional[List[str]]): Search engines to query.
        max_results_per_dork (int): Maximum results per dork.
    """

    target: str
    categories: Optional[List[str]] = None
    engines: Optional[List[str]] = None
    max_results_per_dork: int = 10


class DarkWebMonitorRequest(BaseModel):
    """Request model for dark web monitoring.

    Attributes:
        target (str): Target keyword, domain, or identifier.
        search_depth (str): Search depth ('surface', 'deep').
    """

    target: str
    search_depth: str = "surface"


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

    # Determine primary target for MAXIMUS strategy
    target = request.username or request.email or request.phone or request.name or "unknown"
    target_type = "username" if request.username else "email" if request.email else "phone" if request.phone else "name" if request.name else "unknown"
    
    # Get MAXIMUS AI strategic recommendations
    maximus_strategy = await get_maximus_strategy(target, target_type, "medium")
    if maximus_strategy:
        print(f"[MAXIMUS OSINT] Strategy: {maximus_strategy.get('maximus_intelligence', {}).get('recommended_strategy', 'comprehensive')}")

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

    # Enhance with MAXIMUS intelligence
    if maximus_strategy and "maximus_intelligence" in maximus_strategy:
        result["maximus_orchestration"] = {
            "strategy": maximus_strategy["maximus_intelligence"].get("recommended_strategy", "comprehensive"),
            "threat_prediction": maximus_strategy["maximus_intelligence"].get("predicted_threat_level", "unknown"),
            "confidence": maximus_strategy["maximus_intelligence"].get("confidence", 0.75),
            "priority": maximus_strategy["maximus_intelligence"].get("investigation_priority", "medium"),
            "orchestrator": "MAXIMUS AI v2.0"
        }

    return {
        "success": True,
        "data": result,
        "message": "MAXIMUS AI-orchestrated OSINT investigation completed successfully."
    }


# ============================================
# WORLD-CLASS OSINT TOOLS ENDPOINTS
# ============================================


@app.post("/api/tools/breach-data/analyze")
async def analyze_breach_data(request: BreachDataRequest) -> Dict[str, Any]:
    """Analyzes breach data for a target using BreachDataAnalyzer.

    Args:
        request (BreachDataRequest): Target and search parameters.

    Returns:
        Dict[str, Any]: Breach analysis results with risk scoring.
    """
    try:
        result = await breach_analyzer.query(
            target=request.target,
            search_type=request.search_type,
            include_unverified=request.include_unverified,
        )
        return {
            "status": "success",
            "data": result,
            "tool": "BreachDataAnalyzer",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Breach analysis failed: {str(e)}")


@app.post("/api/tools/google-dork/scan")
async def scan_with_google_dorks(request: GoogleDorkRequest) -> Dict[str, Any]:
    """Executes Google dorking scan using GoogleDorkScanner.

    Args:
        request (GoogleDorkRequest): Target and scanning parameters.

    Returns:
        Dict[str, Any]: Dorking results with discovered URLs and risk scoring.
    """
    try:
        result = await google_scanner.scan(
            target=request.target,
            categories=request.categories,
            engines=request.engines,
            max_results_per_dork=request.max_results_per_dork,
        )
        return {
            "status": "success",
            "data": result,
            "tool": "GoogleDorkScanner",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google dork scan failed: {str(e)}")


@app.post("/api/tools/darkweb/monitor")
async def monitor_dark_web(request: DarkWebMonitorRequest) -> Dict[str, Any]:
    """Monitors dark web for target-related threats using DarkWebMonitor.

    Args:
        request (DarkWebMonitorRequest): Target and monitoring parameters.

    Returns:
        Dict[str, Any]: Dark web monitoring results with threat intelligence.
    """
    try:
        result = await darkweb_monitor.search(
            target=request.target,
            search_depth=request.search_depth,
        )
        return {
            "status": "success",
            "data": result,
            "tool": "DarkWebMonitor",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dark web monitoring failed: {str(e)}")


@app.get("/api/tools/status")
async def get_tools_status() -> Dict[str, Any]:
    """Returns status of all world-class OSINT tools.

    Returns:
        Dict[str, Any]: Status of BreachDataAnalyzer, GoogleDorkScanner, DarkWebMonitor.
    """
    return {
        "status": "operational",
        "tools": {
            "breach_data_analyzer": {
                "name": "BreachDataAnalyzer",
                "status": "ready",
                "description": "12B+ breach records aggregator (HIBP, DeHashed, Intelligence X)",
                "version": "1.0.0",
            },
            "google_dork_scanner": {
                "name": "GoogleDorkScanner",
                "status": "ready",
                "description": "Multi-engine dorking (Google, Bing, DuckDuckGo, Yandex) with 1000+ templates",
                "version": "1.0.0",
            },
            "dark_web_monitor": {
                "name": "DarkWebMonitor",
                "status": "ready",
                "description": "Dark web threat intelligence (Ahmia, Onionland) with onion v2/v3 support",
                "version": "1.0.0",
            },
        },
        "message": "All world-class OSINT tools operational.",
    }


# ============================================
# EMAIL & PHONE ANALYSIS ENDPOINTS
# ============================================


@app.post("/api/email/analyze")
async def analyze_email(request: dict) -> Dict[str, Any]:
    """Analyzes email address with AI-powered insights.
    
    Args:
        request: {"email": "target@example.com"}
    
    Returns:
        Dict with email analysis, breaches, and AI recommendations
    """
    email = request.get("email", "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    try:
        result = await ai_orchestrator.automated_investigation(email=email)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email analysis failed: {str(e)}")


@app.post("/api/phone/analyze")
async def analyze_phone(request: dict) -> Dict[str, Any]:
    """Analyzes phone number with AI-powered insights.
    
    Args:
        request: {"phone": "+5562999999999"}
    
    Returns:
        Dict with phone analysis, carrier info, and AI recommendations
    """
    phone = request.get("phone", "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")
    
    try:
        result = await ai_orchestrator.automated_investigation(phone=phone)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phone analysis failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8036)
