"""Maximus Vulnerability Intelligence Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the
Vulnerability Intelligence Service. It exposes functionalities for gathering,
processing, and providing contextual information about software vulnerabilities,
exploits, and their impact.

Endpoints are provided for:
- Querying for CVE information.
- Correlating vulnerabilities with specific software versions.
- Retrieving exploit availability and details.

This API allows other Maximus AI services or human analysts to leverage the
Vulnerability Intelligence Service's capabilities for risk assessment, patch
management, and proactive defense, enhancing the overall cybersecurity posture.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cve_correlator import CVECorrelator
from nuclei_wrapper import NucleiWrapper

app = FastAPI(title="Maximus Vulnerability Intelligence Service", version="1.0.0")

# Initialize vulnerability intelligence components
cve_correlator = CVECorrelator()
nuclei_wrapper = NucleiWrapper()


class CVEQuery(BaseModel):
    """Request model for querying CVE information.

    Attributes:
        cve_id (str): The CVE ID to query (e.g., 'CVE-2023-1234').
    """

    cve_id: str


class SoftwareVulnerabilityQuery(BaseModel):
    """Request model for correlating vulnerabilities with software.

    Attributes:
        software_name (str): The name of the software.
        software_version (str): The version of the software.
    """

    software_name: str
    software_version: str


class NucleiScanRequest(BaseModel):
    """Request model for initiating a Nuclei scan.

    Attributes:
        target (str): The target for the Nuclei scan (e.g., URL, IP address).
        template_path (Optional[str]): Path to a specific Nuclei template or template directory.
        options (Optional[List[str]]): Additional Nuclei command-line options.
    """

    target: str
    template_path: Optional[str] = None
    options: Optional[List[str]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Vulnerability Intelligence Service."""
    print("🔍 Starting Maximus Vulnerability Intelligence Service...")
    print("✅ Maximus Vulnerability Intelligence Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Vulnerability Intelligence Service."""
    print("👋 Shutting down Maximus Vulnerability Intelligence Service...")
    print("🛑 Maximus Vulnerability Intelligence Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Vulnerability Intelligence Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {
        "status": "healthy",
        "message": "Vulnerability Intelligence Service is operational.",
    }


@app.post("/query_cve")
async def query_cve_info(request: CVEQuery) -> Dict[str, Any]:
    """Queries for detailed information about a specific CVE.

    Args:
        request (CVEQuery): The request body containing the CVE ID.

    Returns:
        Dict[str, Any]: A dictionary containing the CVE information.

    Raises:
        HTTPException: If the CVE is not found.
    """
    print(f"[API] Querying CVE: {request.cve_id}")
    cve_info = await cve_correlator.get_cve_info(request.cve_id)
    if not cve_info:
        raise HTTPException(status_code=404, detail=f"CVE {request.cve_id} not found.")
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "cve_info": cve_info,
    }


@app.post("/correlate_software_vulns")
async def correlate_software_vulnerabilities(
    request: SoftwareVulnerabilityQuery,
) -> Dict[str, Any]:
    """Correlates known vulnerabilities with a specific software and version.

    Args:
        request (SoftwareVulnerabilityQuery): The request body containing software name and version.

    Returns:
        Dict[str, Any]: A dictionary containing the correlated CVEs.
    """
    print(f"[API] Correlating vulnerabilities for {request.software_name} {request.software_version}")
    correlated_cves = await cve_correlator.correlate_vulnerability(request.software_name, request.software_version)
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "correlated_cves": correlated_cves,
    }


@app.post("/nuclei_scan")
async def initiate_nuclei_scan(request: NucleiScanRequest) -> Dict[str, Any]:
    """Initiates a Nuclei scan against a target.

    Args:
        request (NucleiScanRequest): The request body containing target and scan parameters.

    Returns:
        Dict[str, Any]: A dictionary containing the Nuclei scan results.
    """
    print(f"[API] Initiating Nuclei scan on {request.target}")
    scan_results = await nuclei_wrapper.run_scan(request.target, request.template_path, request.options)
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "nuclei_results": scan_results,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8045)
