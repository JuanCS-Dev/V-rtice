"""Maximus Chemical Sensing Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Chemical
Sensing Service. It exposes functionalities for chemical detection, sensor data
processing, and retrieval of chemical analysis results.

Endpoints are provided for:
- Triggering simulated chemical scans.
- Retrieving the status of chemical sensors.
- Accessing historical chemical detection data.

FASE 3 Enhancement: Integrates with Digital Thalamus for Global Workspace
broadcasting of salient chemical perceptions.

This API allows other Maximus AI services or external applications to interact
with the chemical sensing capabilities in a standardized and efficient manner.
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add shared directory to path for Thalamus client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../shared"))

from gustatory_system import GustatorySystem
from olfactory_system import OlfactorySystem
from thalamus_client import ThalamusClient

app = FastAPI(title="Maximus Chemical Sensing Service", version="2.0.0")

# Initialize sensing systems
olfactory_system = OlfactorySystem()
gustatory_system = GustatorySystem()

# Initialize Thalamus client for Global Workspace integration
thalamus_url = os.getenv("DIGITAL_THALAMUS_URL", "http://digital_thalamus_service:8012")
thalamus_client = ThalamusClient(
    thalamus_url=thalamus_url,
    sensor_id="chemical_sensor_primary",
    sensor_type="chemical"
)


class ChemicalScanRequest(BaseModel):
    """Request model for triggering a chemical scan.

    Attributes:
        scan_type (str): The type of scan to perform (e.g., 'olfactory', 'gustatory', 'full').
        target_area (Optional[str]): The specific area to scan.
        priority (int): The priority of the scan (1-10, 10 being highest).
    """

    scan_type: str
    target_area: Optional[str] = None
    priority: int = 5


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Chemical Sensing Service."""
    print("👃 Starting Maximus Chemical Sensing Service v2.0...")
    print(f"   Thalamus URL: {thalamus_url}")
    print("✅ Maximus Chemical Sensing Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Chemical Sensing Service."""
    print("👋 Shutting down Maximus Chemical Sensing Service...")
    await thalamus_client.close()
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

    # FASE 3: Submit perception to Digital Thalamus for Global Workspace broadcasting
    try:
        thalamus_response = await thalamus_client.submit_perception(
            data=results,
            priority=request.priority,
            timestamp=results["timestamp"]
        )
        results["thalamus_broadcast"] = {
            "submitted": True,
            "broadcasted_to_global_workspace": thalamus_response.get("broadcasted_to_global_workspace", False),
            "salience": thalamus_response.get("salience", 0.0)
        }
        print(f"   📡 Chemical perception submitted to Thalamus (salience: {thalamus_response.get('salience', 0.0):.2f})")
    except Exception as e:
        print(f"   ⚠️  Failed to submit to Thalamus: {e}")
        results["thalamus_broadcast"] = {
            "submitted": False,
            "error": str(e)
        }

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
