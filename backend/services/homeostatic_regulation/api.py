"""Maximus Homeostatic Regulation Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Homeostatic
Regulation Service. It exposes functionalities for managing and observing the
Maximus AI's Homeostatic Control Loop (HCL).

Endpoints are provided for:
- Retrieving the current operational status and health of the HCL.
- Submitting operational goals or policy updates.
- Triggering emergency red-line responses.

This API allows other Maximus AI services or external systems to interact with
the HCL, enabling dynamic adaptation, performance optimization, and proactive
management of the entire Maximus AI system.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from homeostatic_regulator import HomeostaticRegulator
from pydantic import BaseModel
from red_line_triggers import RedLineTriggers
import uvicorn

app = FastAPI(title="Maximus Homeostatic Regulation Service", version="1.0.0")

# Initialize HCL components
homeostatic_regulator = HomeostaticRegulator()
red_line_triggers = RedLineTriggers()


class OperationalGoalUpdate(BaseModel):
    """Request model for updating operational goals.

    Attributes:
        goal_name (str): The name of the operational goal to update.
        value (Any): The new value for the operational goal.
        priority (int): The priority of this goal (1-10, 10 being highest).
    """

    goal_name: str
    value: Any
    priority: int = 5


class RedLineTriggerRequest(BaseModel):
    """Request model for manually triggering a red-line event.

    Attributes:
        trigger_type (str): The type of red-line event (e.g., 'critical_failure', 'security_breach').
        details (Optional[Dict[str, Any]]): Additional details about the trigger.
    """

    trigger_type: str
    details: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Homeostatic Regulation Service."""
    print("🧠 Starting Maximus Homeostatic Regulation Service...")
    asyncio.create_task(homeostatic_regulator.start_hcl())
    print("✅ Maximus Homeostatic Regulation Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Homeostatic Regulation Service."""
    print("👋 Shutting down Maximus Homeostatic Regulation Service...")
    await homeostatic_regulator.stop_hcl()
    print("🛑 Maximus Homeostatic Regulation Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Homeostatic Regulation Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {
        "status": "healthy",
        "message": "Homeostatic Regulation Service is operational.",
    }


@app.get("/hcl_status")
async def get_hcl_status() -> Dict[str, Any]:
    """Retrieves the current operational status of the Homeostatic Control Loop.

    Returns:
        Dict[str, Any]: A dictionary summarizing the HCL's status, health, and active goals.
    """
    return await homeostatic_regulator.get_status()


@app.post("/update_operational_goal")
async def update_operational_goal(request: OperationalGoalUpdate) -> Dict[str, Any]:
    """Updates an operational goal for the HCL.

    Args:
        request (OperationalGoalUpdate): The request body containing the goal name, value, and priority.

    Returns:
        Dict[str, Any]: A dictionary confirming the goal update.
    """
    print(
        f"[API] Updating operational goal '{request.goal_name}' to {request.value} with priority {request.priority}"
    )
    await homeostatic_regulator.update_operational_goal(
        request.goal_name, request.value, request.priority
    )
    return {
        "status": "success",
        "message": f"Operational goal '{request.goal_name}' updated.",
    }


@app.post("/trigger_red_line")
async def trigger_red_line_event(request: RedLineTriggerRequest) -> Dict[str, Any]:
    """Manually triggers a red-line event, forcing an emergency response.

    Args:
        request (RedLineTriggerRequest): The request body containing the trigger type and details.

    Returns:
        Dict[str, Any]: A dictionary confirming the red-line trigger.
    """
    print(f"[API] Manually triggering red-line event: {request.trigger_type}")
    response = await red_line_triggers.trigger_emergency_response(
        request.trigger_type, request.details
    )
    return {
        "status": "success",
        "message": f"Red-line event '{request.trigger_type}' triggered.",
        "response": response,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8020)
