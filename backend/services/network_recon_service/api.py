"""Maximus Network Reconnaissance Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Network
Reconnaissance Service. It exposes functionalities for actively gathering
information about target networks, systems, and services to identify potential
attack surfaces, vulnerabilities, and misconfigurations.

Endpoints are provided for:
- Initiating various types of network scans (e.g., port scans, full scans).
- Querying the status of ongoing reconnaissance tasks.
- Retrieving detailed reconnaissance reports.

This API allows other Maximus AI services or human operators to leverage the
Network Reconnaissance Service's capabilities for threat assessment,
vulnerability management, and offensive operations, building a comprehensive
understanding of the network attack surface.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException
from metrics import MetricsCollector
from models import ReconResult, ReconStatus, ReconTask
from pydantic import BaseModel
from recon_engine import ReconEngine
import uvicorn

app = FastAPI(title="Maximus Network Reconnaissance Service", version="1.0.0")

# Initialize Recon components
metrics_collector = MetricsCollector()
recon_engine = ReconEngine(metrics_collector)


class StartReconRequest(BaseModel):
    """Request model for starting a network reconnaissance task.

    Attributes:
        target (str): The target for reconnaissance (e.g., IP address, CIDR range, domain).
        scan_type (str): The type of scan to perform (e.g., 'nmap_full', 'masscan_ports').
        parameters (Optional[Dict[str, Any]]): Additional parameters for the scan (e.g., 'ports' for masscan).
    """

    target: str
    scan_type: str
    parameters: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Network Reconnaissance Service."""
    print("📡 Starting Maximus Network Reconnaissance Service...")
    print("✅ Maximus Network Reconnaissance Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Network Reconnaissance Service."""
    print("👋 Shutting down Maximus Network Reconnaissance Service...")
    print("🛑 Maximus Network Reconnaissance Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Network Reconnaissance Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {
        "status": "healthy",
        "message": "Network Reconnaissance Service is operational.",
    }


@app.post("/start_recon", response_model=ReconTask)
async def start_recon_task_endpoint(request: StartReconRequest) -> ReconTask:
    """Initiates a new network reconnaissance task.

    Args:
        request (StartReconRequest): The request body containing target and scan parameters.

    Returns:
        ReconTask: The details of the initiated reconnaissance task.
    """
    print(f"[API] Starting recon task: {request.scan_type} on {request.target}")
    task_id = str(uuid.uuid4())
    task = ReconTask(
        id=task_id,
        target=request.target,
        scan_type=request.scan_type,
        parameters=request.parameters or {},
        start_time=datetime.now().isoformat(),
        status=ReconStatus.PENDING,
    )
    asyncio.create_task(recon_engine.start_recon_task(task))  # Run in background
    return task


@app.get("/recon_task/{task_id}/status", response_model=ReconTask)
async def get_recon_task_status(task_id: str) -> ReconTask:
    """Retrieves the current status of a specific reconnaissance task.

    Args:
        task_id (str): The ID of the reconnaissance task.

    Returns:
        ReconTask: The current status and details of the task.

    Raises:
        HTTPException: If the task ID is not found.
    """
    task = recon_engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Reconnaissance task not found.")
    return task


@app.get("/recon_task/{task_id}/results", response_model=ReconResult)
async def get_recon_task_results(task_id: str) -> ReconResult:
    """Retrieves the results of a completed reconnaissance task.

    Args:
        task_id (str): The ID of the reconnaissance task.

    Returns:
        ReconResult: The results of the reconnaissance task.

    Raises:
        HTTPException: If the task ID is not found or results are not yet available.
    """
    results = recon_engine.get_task_results(task_id)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="Reconnaissance task results not found or not yet available.",
        )
    return results


@app.get("/metrics")
async def get_recon_metrics() -> Dict[str, Any]:
    """Retrieves overall metrics for the Network Reconnaissance service.

    Returns:
        Dict[str, Any]: A dictionary containing various reconnaissance operational metrics.
    """
    return metrics_collector.get_all_metrics()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8032)
