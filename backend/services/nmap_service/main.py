"""Maximus Nmap Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Nmap Service.
It initializes and configures the FastAPI application, sets up event handlers
for startup and shutdown, and defines the API endpoints for executing Nmap
scans and retrieving their results.

It acts as a dedicated wrapper and interface for the Nmap (Network Mapper)
utility, enabling Maximus to perform advanced network discovery and security
auditing operations. This service is crucial for supporting network
reconnaissance, vulnerability identification, and attack surface mapping
within the Maximus AI system.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scanner import NmapScanner

app = FastAPI(title="Maximus Nmap Service", version="1.0.0")

# Global scanner instance
nmap_scanner: Optional[NmapScanner] = None

# Scan results storage (persisted scans)
scan_results_db: Dict[str, Dict[str, Any]] = {}


class NmapScanRequest(BaseModel):
    """Request model for initiating an Nmap scan.

    Attributes:
        target (str): The target for the Nmap scan (e.g., IP address, hostname, CIDR range).
        scan_type (str): The type of Nmap scan (e.g., 'quick', 'full', 'port_scan').
        options (Optional[List[str]]): Additional Nmap command-line options.
    """

    target: str
    scan_type: str = "quick"
    options: Optional[List[str]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Nmap Service."""
    global nmap_scanner
    print("📡 Starting Maximus Nmap Service...")
    nmap_scanner = NmapScanner()
    print("✅ Nmap scanner initialized")
    print("✅ Maximus Nmap Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Nmap Service."""
    print("👋 Shutting down Maximus Nmap Service...")
    print("🛑 Maximus Nmap Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Nmap Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Nmap Service is operational."}


@app.post("/scan", response_model=Dict[str, Any])
async def initiate_nmap_scan(request: NmapScanRequest) -> Dict[str, Any]:
    """Initiates an Nmap scan and returns a scan ID.

    Args:
        request (NmapScanRequest): The request body containing target and scan parameters.

    Returns:
        Dict[str, Any]: A dictionary containing the scan ID and initial status.
    """
    scan_id = str(uuid.uuid4())
    print(f"[API] Initiating Nmap scan (ID: {scan_id}, target: {request.target}, type: {request.scan_type})")

    # Simulate Nmap scan in a background task
    asyncio.create_task(perform_nmap_scan(scan_id, request.target, request.scan_type, request.options))

    return {
        "scan_id": scan_id,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/scan_results/{scan_id}", response_model=Dict[str, Any])
async def get_nmap_scan_results(scan_id: str) -> Dict[str, Any]:
    """Retrieves the results of a specific Nmap scan.

    Args:
        scan_id (str): The ID of the Nmap scan.

    Returns:
        Dict[str, Any]: A dictionary containing the scan results.

    Raises:
        HTTPException: If the scan ID is not found or results are not yet available.
    """
    results = scan_results_db.get(scan_id)
    if not results:
        raise HTTPException(status_code=404, detail="Scan results not found or not yet available.")
    return results


async def perform_nmap_scan(scan_id: str, target: str, scan_type: str, options: Optional[List[str]]):
    """Performs real Nmap scan and stores results.

    Args:
        scan_id (str): The ID of the scan.
        target (str): The target for the scan.
        scan_type (str): The type of Nmap scan.
        options (Optional[List[str]]): Additional Nmap command-line options.
    """
    print(f"[NmapService] Performing scan {scan_id} on {target}...")
    
    # Execute real scan using scanner
    results = nmap_scanner.execute_scan(target, scan_type, options)
    
    # Add scan metadata
    results["scan_id"] = scan_id
    results["status"] = "completed" if "error" not in results else "failed"
    results["completed_at"] = datetime.now().isoformat()
    
    # Store results
    scan_results_db[scan_id] = results
    print(f"[NmapService] Scan {scan_id} completed")


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="0.0.0.0", port=8034)  # pragma: no cover
