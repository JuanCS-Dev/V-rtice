"""Maximus Offensive Gateway Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Offensive
Gateway Service. It acts as a secure and controlled interface for Maximus AI
to interact with external systems for offensive security operations, such as
penetration testing, vulnerability exploitation, and red teaming.

Endpoints are provided for:
- Submitting offensive commands to specialized tools (e.g., Metasploit, Cobalt Strike).
- Querying the status of ongoing offensive operations.
- Retrieving results from executed attacks.

This API allows Maximus AI to execute controlled offensive actions, supporting
its role in proactive cybersecurity defense, while ensuring compliance with
ethical hacking guidelines and legal frameworks.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException
from metrics import MetricsCollector
from models import CommandResult, CommandStatus, OffensiveCommand
from orchestrator import OffensiveOrchestrator
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Maximus Offensive Gateway Service", version="1.0.0")

# Initialize Offensive Gateway components
metrics_collector = MetricsCollector()
offensive_orchestrator = OffensiveOrchestrator(metrics_collector)


class ExecuteOffensiveCommandRequest(BaseModel):
    """Request model for executing an offensive command.

    Attributes:
        command_name (str): The name of the offensive command (e.g., 'exploit_vulnerability', 'run_post_exploit').
        parameters (Optional[Dict[str, Any]]): Parameters for the command.
        target (str): The target for the offensive operation.
        tool (str): The offensive tool to use (e.g., 'metasploit', 'cobalt_strike').
    """

    command_name: str
    parameters: Optional[Dict[str, Any]] = None
    target: str
    tool: str


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Offensive Gateway Service."""
    print("⚔️ Starting Maximus Offensive Gateway Service...")
    print("✅ Maximus Offensive Gateway Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Offensive Gateway Service."""
    print("👋 Shutting down Maximus Offensive Gateway Service...")
    print("🛑 Maximus Offensive Gateway Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Offensive Gateway Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Offensive Gateway Service is operational."}


@app.post("/execute_offensive_command", response_model=OffensiveCommand)
async def execute_offensive_command_endpoint(
    request: ExecuteOffensiveCommandRequest,
) -> OffensiveCommand:
    """Initiates an offensive command using a specified tool against a target.

    Args:
        request (ExecuteOffensiveCommandRequest): The request body containing command details.

    Returns:
        OffensiveCommand: The details of the initiated offensive command.
    """
    command_id = str(uuid.uuid4())
    print(
        f"[API] Initiating offensive command '{request.command_name}' (ID: {command_id}) against {request.target} using {request.tool}"
    )

    command = OffensiveCommand(
        id=command_id,
        name=request.command_name,
        parameters=request.parameters or {},
        target=request.target,
        tool=request.tool,
        status=CommandStatus.PENDING,
        created_at=datetime.now().isoformat(),
    )
    asyncio.create_task(
        offensive_orchestrator.execute_offensive_command(command)
    )  # Run in background

    return command


@app.get("/offensive_command/{command_id}/status", response_model=OffensiveCommand)
async def get_offensive_command_status(command_id: str) -> OffensiveCommand:
    """Retrieves the current status of a specific offensive command.

    Args:
        command_id (str): The ID of the offensive command.

    Returns:
        OffensiveCommand: The current status and details of the command.

    Raises:
        HTTPException: If the command ID is not found.
    """
    command = offensive_orchestrator.get_command(command_id)
    if not command:
        raise HTTPException(status_code=404, detail="Offensive command not found.")
    return command


@app.get("/offensive_command/{command_id}/results", response_model=CommandResult)
async def get_offensive_command_results(command_id: str) -> CommandResult:
    """Retrieves the results of a completed offensive command.

    Args:
        command_id (str): The ID of the offensive command.

    Returns:
        CommandResult: The results of the offensive command.

    Raises:
        HTTPException: If the command ID is not found or results are not yet available.
    """
    results = offensive_orchestrator.get_command_results(command_id)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="Offensive command results not found or not yet available.",
        )
    return results


@app.get("/metrics")
async def get_offensive_metrics() -> Dict[str, Any]:
    """Retrieves overall metrics for the Offensive Gateway service.

    Returns:
        Dict[str, Any]: A dictionary containing various offensive operational metrics.
    """
    return metrics_collector.get_all_metrics()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8035)
