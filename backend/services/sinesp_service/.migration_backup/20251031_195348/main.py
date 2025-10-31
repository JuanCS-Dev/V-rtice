"""Maximus Sinesp Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Sinesp Service.
It initializes and configures the FastAPI application, sets up event handlers
for startup and shutdown, and defines the API endpoints for querying Sinesp
data and performing AI-driven analysis.

It orchestrates the integration with the Sinesp Cidadão API, processes the
retrieved public security data, and leverages a Large Language Model (LLM)
to extract relevant intelligence and provide contextual insights. This service
is crucial for supporting investigations, situational awareness, and law
enforcement support within the Maximus AI system.
"""

from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException

from intelligence_agent import IntelligenceAgent
from llm_client import LLMClient
from models import SinespQuery, VehicleInfo

app = FastAPI(title="Maximus Sinesp Service", version="1.0.0")

# Initialize LLM client and Intelligence Agent
llm_client = LLMClient()
intelligence_agent = IntelligenceAgent(llm_client)


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Sinesp Service."""
    print("🇧🇷 Starting Maximus Sinesp Service...")
    print("✅ Maximus Sinesp Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Sinesp Service."""
    print("👋 Shutting down Maximus Sinesp Service...")
    print("🛑 Maximus Sinesp Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Sinesp Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Sinesp Service is operational."}


@app.post("/query_vehicle", response_model=VehicleInfo)
async def query_vehicle_info(query: SinespQuery) -> VehicleInfo:
    """Queries the Sinesp Cidadão API for vehicle information.

    Args:
        query (SinespQuery): The query object containing the identifier and type.

    Returns:
        VehicleInfo: Detailed information about the vehicle.

    Raises:
        HTTPException: If the Sinesp API returns an error or the vehicle is not found.
    """
    print(f"[API] Received Sinesp query for {query.query_type}: {query.identifier}")
    try:
        vehicle_info = await intelligence_agent.query_sinesp(query)
        return vehicle_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query Sinesp API: {str(e)}")


@app.post("/analyze_vehicle", response_model=Dict[str, Any])
async def analyze_vehicle_details(vehicle_info: VehicleInfo) -> Dict[str, Any]:
    """Analyzes vehicle information using AI to extract insights and recommendations.

    Args:
        vehicle_info (VehicleInfo): The vehicle information to analyze.

    Returns:
        Dict[str, Any]: A dictionary containing AI-generated insights and recommendations.
    """
    print(f"[API] Analyzing vehicle details for plate: {vehicle_info.plate}")
    insights = await intelligence_agent.analyze_vehicle_info(vehicle_info)
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "insights": insights,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8039)
