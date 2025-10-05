"""Maximus Strategic Planning Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Strategic
Planning Service. It exposes functionalities for formulating long-term goals,
developing complex strategies, and evaluating potential actions and their
consequences across the entire Maximus AI system.

Endpoints are provided for:
- Submitting high-level objectives for strategic planning.
- Requesting scenario analysis and risk assessments.
- Retrieving generated strategic plans and recommendations.

This API allows other Maximus AI services or human operators to leverage the
Strategic Planning Service's capabilities, enabling Maximus to make coherent,
goal-oriented decisions, and align its actions with overarching missions.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import asyncio
from datetime import datetime

from strategic_planning_core import StrategicPlanningCore

app = FastAPI(title="Maximus Strategic Planning Service", version="1.0.0")

# Initialize strategic planning core
strategic_planning_core = StrategicPlanningCore()


class StrategicObjective(BaseModel):
    """Request model for submitting a strategic objective.

    Attributes:
        objective_name (str): The name of the strategic objective.
        description (str): A detailed description of the objective.
        priority (int): The priority of this objective (1-10, 10 being highest).
        target_date (Optional[str]): ISO formatted target completion date.
    """
    objective_name: str
    description: str
    priority: int = 5
    target_date: Optional[str] = None


class ScenarioAnalysisRequest(BaseModel):
    """Request model for initiating a scenario analysis.

    Attributes:
        scenario_name (str): The name of the scenario to analyze.
        context (Dict[str, Any]): The context and parameters for the scenario.
        risk_factors (List[str]): Key risk factors to consider.
    """
    scenario_name: str
    context: Dict[str, Any]
    risk_factors: List[str]


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Strategic Planning Service."""
    print("🎯 Starting Maximus Strategic Planning Service...")
    print("✅ Maximus Strategic Planning Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Strategic Planning Service."""
    print("👋 Shutting down Maximus Strategic Planning Service...")
    print("🛑 Maximus Strategic Planning Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Strategic Planning Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Strategic Planning Service is operational."}


@app.post("/set_objective")
async def set_strategic_objective(objective: StrategicObjective) -> Dict[str, Any]:
    """Sets a new strategic objective for Maximus AI.

    Args:
        objective (StrategicObjective): The strategic objective details.

    Returns:
        Dict[str, Any]: A dictionary confirming the objective has been set.
    """
    print(f"[API] Setting strategic objective: {objective.objective_name}")
    await strategic_planning_core.set_objective(objective.objective_name, objective.description, objective.priority, objective.target_date)
    return {"status": "success", "message": f"Objective '{objective.objective_name}' set.", "timestamp": datetime.now().isoformat()}


@app.post("/analyze_scenario")
async def analyze_scenario_endpoint(request: ScenarioAnalysisRequest) -> Dict[str, Any]:
    """Initiates a scenario analysis to evaluate potential outcomes and risks.

    Args:
        request (ScenarioAnalysisRequest): The request body containing scenario details.

    Returns:
        Dict[str, Any]: A dictionary containing the scenario analysis results.
    """
    print(f"[API] Analyzing scenario: {request.scenario_name}")
    analysis_result = await strategic_planning_core.analyze_scenario(request.scenario_name, request.context, request.risk_factors)
    return {"status": "success", "timestamp": datetime.now().isoformat(), "analysis": analysis_result}


@app.get("/strategic_plan")
async def get_current_strategic_plan() -> Dict[str, Any]:
    """Retrieves the current strategic plan and its status.

    Returns:
        Dict[str, Any]: A dictionary summarizing the current strategic plan.
    """
    return await strategic_planning_core.get_strategic_plan()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8042)