"""Maximus C2 Orchestration Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Command
and Control (C2) Orchestration Service. It exposes functionalities for managing
and coordinating the activities of various Maximus AI services, acting as a
central nervous system for complex operations.

Endpoints are provided for:
- Submitting high-level operational directives.
- Querying the status of ongoing orchestrated tasks.
- Retrieving results from completed operations.

This API allows external systems or human operators to issue commands and receive
updates on the execution of complex, multi-service operations within the Maximus
AI ecosystem.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from c2_engine import C2Engine
from metrics import MetricsCollector
from services.c2_orchestration_service.models import Command, CommandResult, CommandStatus

app = FastAPI(title="Maximus C2 Orchestration Service", version="1.0.0")

# Initialize C2 components
metrics_collector = MetricsCollector()
c2_engine = C2Engine(metrics_collector)


class ExecuteCommandRequest(BaseModel):
    """Request model for executing a command.

    Attributes:
        command_name (str): The name of the command to execute (e.g., 'recon_scan', 'deploy_agent').
        parameters (Optional[Dict[str, Any]]): Parameters for the command.
        target_service (Optional[str]): The specific Maximus service to target.
    """

    command_name: str
    parameters: Optional[Dict[str, Any]] = None
    target_service: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the C2 Orchestration Service."""
    print("📡 Starting Maximus C2 Orchestration Service...")
    print("✅ Maximus C2 Orchestration Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the C2 Orchestration Service."""
    print("👋 Shutting down Maximus C2 Orchestration Service...")
    print("🛑 Maximus C2 Orchestration Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the C2 Orchestration Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "C2 Orchestration Service is operational."}


@app.post("/execute_command", response_model=Command)
async def execute_command_endpoint(request: ExecuteCommandRequest) -> Command:
    """Executes a high-level command, orchestrating tasks across Maximus services.

    Args:
        request (ExecuteCommandRequest): The request body containing command details.

    Returns:
        Command: The details of the initiated command, including its ID and status.
    """
    print(f"[API] Received command: {request.command_name} (target: {request.target_service})")
    command_id = str(uuid.uuid4())
    command = Command(
        id=command_id,
        name=request.command_name,
        parameters=request.parameters or {},
        target_service=request.target_service,
        status=CommandStatus.PENDING,
        created_at=datetime.now().isoformat(),
    )
    asyncio.create_task(c2_engine.execute_command(command))  # Run in background
    return command


@app.get("/command/{command_id}", response_model=Command)
async def get_command_status(command_id: str) -> Command:
    """Retrieves the current status of an executed command.

    Args:
        command_id (str): The ID of the command to retrieve.

    Returns:
        Command: The current status and details of the command.

    Raises:
        HTTPException: If the command ID is not found.
    """
    command = c2_engine.get_command(command_id)
    if not command:
        raise HTTPException(status_code=404, detail="Command not found.")
    return command


@app.get("/command/{command_id}/results", response_model=CommandResult)
async def get_command_results(command_id: str) -> CommandResult:
    """Retrieves the results of a completed command.

    Args:
        command_id (str): The ID of the command to retrieve results for.

    Returns:
        CommandResult: The results of the command execution.

    Raises:
        HTTPException: If the command ID is not found or results are not yet available.
    """
    results = c2_engine.get_command_results(command_id)
    if not results:
        raise HTTPException(status_code=404, detail="Command results not found or not yet available.")
    return results


@app.get("/metrics")
async def get_c2_metrics() -> Dict[str, Any]:
    """Retrieves overall metrics for the C2 Orchestration service.

    Returns:
        Dict[str, Any]: A dictionary containing various C2 operational metrics.
    """
    return metrics_collector.get_all_metrics()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
