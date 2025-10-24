"""Maximus Vulnerability Scanner Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Vulnerability Scanner
Service. It initializes and configures the FastAPI application, sets up event
handlers for startup and shutdown, and defines the API endpoints for initiating
vulnerability scans and retrieving their results.

It orchestrates the integration with external vulnerability scanning tools,
manages various types of scans (e.g., network, web application, host-based),
analyzes scan results, and correlates them with threat intelligence. This service
is crucial for providing detailed vulnerability reports to other Maximus AI
services for risk assessment, patch management, and proactive defense.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import database
import models
import schemas
from database import get_db
from scanners.nmap_scanner import NmapScanner
from scanners.web_scanner import WebScanner

app = FastAPI(title="Maximus Vulnerability Scanner Service", version="1.0.0")

# Initialize scanners
nmap_scanner = NmapScanner()
web_scanner = WebScanner()


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Vulnerability Scanner Service."""
    print("🔍 Starting Maximus Vulnerability Scanner Service...")
    database.create_db_and_tables()
    print("✅ Maximus Vulnerability Scanner Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Vulnerability Scanner Service."""
    print("👋 Shutting down Maximus Vulnerability Scanner Service...")
    print("🛑 Maximus Vulnerability Scanner Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Vulnerability Scanner Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {
        "status": "healthy",
        "message": "Vulnerability Scanner Service is operational.",
    }


@app.post("/scans/", response_model=schemas.ScanTask)
async def create_scan_task(scan_request: schemas.ScanTaskCreate, db: Session = Depends(get_db)):
    """Creates and initiates a new vulnerability scan task.

    Args:
        scan_request (schemas.ScanTaskCreate): The scan task details.
        db (Session): The database session.

    Returns:
        schemas.ScanTask: The created scan task.
    """
    # Create database model from Pydantic schema
    db_scan_task = database.ScanTask(
        target=scan_request.target,
        scan_type=scan_request.scan_type,
        parameters=json.dumps(scan_request.parameters),  # Store as JSON string
    )
    db.add(db_scan_task)
    db.commit()
    db.refresh(db_scan_task)

    # Start scan in background
    asyncio.create_task(
        run_scan(
            db_scan_task.id,
            db_scan_task.target,
            db_scan_task.scan_type,
            scan_request.parameters,  # Use original dict from request
            db,
        )
    )

    return db_scan_task


@app.get("/scans/", response_model=List[schemas.ScanTask])
async def read_scan_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieves a list of vulnerability scan tasks.

    Args:
        skip (int): Number of items to skip.
        limit (int): Maximum number of items to return.
        db (Session): The database session.

    Returns:
        List[schemas.ScanTask]: A list of scan tasks.
    """
    scan_tasks = db.query(database.ScanTask).offset(skip).limit(limit).all()
    return scan_tasks


@app.get("/scans/{scan_id}", response_model=schemas.ScanTask)
async def read_scan_task(scan_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific scan task by ID.

    Args:
        scan_id (int): The ID of the scan task.
        db (Session): The database session.

    Returns:
        schemas.ScanTask: The scan task details.

    Raises:
        HTTPException: If the scan task is not found.
    """
    scan_task = db.query(database.ScanTask).filter(database.ScanTask.id == scan_id).first()
    if scan_task is None:
        raise HTTPException(status_code=404, detail="Scan task not found")
    return scan_task


@app.get("/scans/{scan_id}/vulnerabilities", response_model=List[schemas.Vulnerability])
async def read_scan_vulnerabilities(scan_id: int, db: Session = Depends(get_db)):
    """Retrieves vulnerabilities found for a specific scan task.

    Args:
        scan_id (int): The ID of the scan task.
        db (Session): The database session.

    Returns:
        List[schemas.Vulnerability]: A list of vulnerabilities.
    """
    vulnerabilities = db.query(database.Vulnerability).filter(database.Vulnerability.scan_task_id == scan_id).all()
    return vulnerabilities


async def run_scan(
    scan_task_id: int,
    target: str,
    scan_type: str,
    parameters: Dict[str, Any],
    db: Session,
):
    """Executes the actual scan using the appropriate scanner and updates the database.

    Args:
        scan_task_id (int): The ID of the scan task.
        target (str): The target for the scan.
        scan_type (str): The type of scan.
        parameters (Dict[str, Any]): Additional scan parameters.
        db (Session): The database session.
    """
    print(f"[ScannerService] Running scan {scan_task_id} ({scan_type}) on {target}")
    scan_task = db.query(database.ScanTask).filter(database.ScanTask.id == scan_task_id).first()
    if not scan_task:
        return

    scan_task.status = "running"
    db.add(scan_task)
    db.commit()
    db.refresh(scan_task)

    try:
        scan_results: Dict[str, Any] = {}
        if scan_type == "nmap_network":
            scan_results = await nmap_scanner.scan_network(target, parameters.get("ports", []))
        elif scan_type == "web_application":
            scan_results = await web_scanner.scan_web_application(target, parameters.get("depth", 1))
        else:
            raise ValueError(f"Unsupported scan type: {scan_type}")

        # Process results and store vulnerabilities
        for vuln_data in scan_results.get("vulnerabilities", []):
            db_vulnerability = database.Vulnerability(
                scan_task_id=scan_task_id,
                cve_id=vuln_data.get("cve_id"),
                name=vuln_data.get("name", "Unknown Vulnerability"),
                severity=vuln_data.get("severity", "medium"),
                description=vuln_data.get("description", ""),
                solution=vuln_data.get("solution"),
                host=vuln_data.get("host", target),
                port=vuln_data.get("port"),
                protocol=vuln_data.get("protocol"),
            )
            db.add(db_vulnerability)
        db.commit()

        scan_task.status = "completed"
        scan_task.end_time = datetime.now()
        scan_task.raw_results = str(scan_results)  # Store raw results as string
        db.add(scan_task)
        db.commit()
        db.refresh(scan_task)
        print(f"[ScannerService] Scan {scan_task_id} completed successfully.")

    except Exception as e:
        scan_task.status = "failed"
        scan_task.end_time = datetime.now()
        scan_task.raw_results = str({"error": str(e)})
        db.add(scan_task)
        db.commit()
        db.refresh(scan_task)
        print(f"[ScannerService] Scan {scan_task_id} failed: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8046)
