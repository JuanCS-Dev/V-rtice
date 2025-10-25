"""Maximus Chemical Sensing Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Chemical
Sensing Service. It exposes functionalities for chemical detection, sensor data
processing, and retrieval of chemical analysis results.

Endpoints are provided for:
- Triggering simulated chemical scans.
- Retrieving the status of chemical sensors.
- Accessing historical chemical detection data.

This API allows other Maximus AI services or external applications to interact
with the chemical sensing capabilities in a standardized and efficient manner.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from gustatory_system import GustatorySystem
from olfactory_system import OlfactorySystem

app = FastAPI(title="Maximus Chemical Sensing Service", version="1.0.0")

# Initialize sensing systems
olfactory_system = OlfactorySystem()
gustatory_system = GustatorySystem()


class ChemicalScanRequest(BaseModel):
    """Request model for triggering a chemical scan.

    Attributes:
        scan_type (str): The type of scan to perform (e.g., 'olfactory', 'gustatory', 'full').
        target_area (Optional[str]): The specific area to scan.
    """

    scan_type: str
    target_area: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Chemical Sensing Service."""
    print("🧪 Starting Maximus Chemical Sensing Service...")
    # Potentially start background tasks for continuous monitoring
    print("✅ Maximus Chemical Sensing Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Chemical Sensing Service."""
    print("👋 Shutting down Maximus Chemical Sensing Service...")
    # Clean up resources if any
    print("🛑 Maximus Chemical Sensing Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Chemical Sensing Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Chemical Sensing Service is operational."}


@app.post("/scan")
async def trigger_chemical_scan(request: ChemicalScanRequest) -> Dict[str, Any]:
    """Triggers a simulated chemical scan based on the request.

    Args:
        request (ChemicalScanRequest): The request body containing scan type and target area.

    Returns:
        Dict[str, Any]: The results of the simulated chemical scan.

    Raises:
        HTTPException: If an invalid scan type is provided.
    """
    print(f"[API] Received chemical scan request: {request.scan_type} for {request.target_area}")
    results = {
        "timestamp": datetime.now().isoformat(),
        "scan_type": request.scan_type,
        "target_area": request.target_area,
    }

    if request.scan_type == "olfactory":
        olfactory_results = await olfactory_system.perform_scan(request.target_area)
        results["olfactory_results"] = olfactory_results
    elif request.scan_type == "gustatory":
        gustatory_results = await gustatory_system.perform_analysis(request.target_area)
        results["gustatory_results"] = gustatory_results
    elif request.scan_type == "full":
        olfactory_results = await olfactory_system.perform_scan(request.target_area)
        gustatory_results = await gustatory_system.perform_analysis(request.target_area)
        results["olfactory_results"] = olfactory_results
        results["gustatory_results"] = gustatory_results
    else:
        raise HTTPException(status_code=400, detail=f"Invalid scan type: {request.scan_type}")

    return results


@app.get("/olfactory/status")
async def get_olfactory_status() -> Dict[str, Any]:
    """Retrieves the current status of the olfactory system.

    Returns:
        Dict[str, Any]: The status of the olfactory system.
    """
    return await olfactory_system.get_status()


@app.get("/gustatory/status")
async def get_gustatory_status() -> Dict[str, Any]:
    """Retrieves the current status of the gustatory system.

    Returns:
        Dict[str, Any]: The status of the gustatory system.
    """
    return await gustatory_system.get_status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
