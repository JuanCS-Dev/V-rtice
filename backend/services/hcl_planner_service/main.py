"""Maximus HCL Planner Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Homeostatic Control
Loop (HCL) Planner Service. It initializes and configures the FastAPI
application, sets up event handlers for startup and shutdown, and defines the
API endpoints for receiving analysis results and generating resource alignment plans.

It orchestrates the application of planning algorithms, such as fuzzy logic
controllers or reinforcement learning agents, to develop optimal strategies for
resource allocation, scaling, and configuration changes. This service is crucial
for translating HCL analysis into actionable plans for the HCL Executor Service,
ensuring Maximus AI's adaptive self-management.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import asyncio
from datetime import datetime

from fuzzy_controller import FuzzyController
from rl_agent import RLAgent

app = FastAPI(title="Maximus HCL Planner Service", version="1.0.0")

# Initialize planning components
fuzzy_controller = FuzzyController()
rl_agent = RLAgent()


class PlanRequest(BaseModel):
    """Request model for generating a resource alignment plan.

    Attributes:
        analysis_result (Dict[str, Any]): The analysis result from the HCL Analyzer Service.
        current_state (Dict[str, Any]): The current system state.
        operational_goals (Dict[str, Any]): Current operational goals (e.g., 'high_performance', 'cost_efficiency').
    """
    analysis_result: Dict[str, Any]
    current_state: Dict[str, Any]
    operational_goals: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the HCL Planner Service."""
    print("📝 Starting Maximus HCL Planner Service...")
    print("✅ Maximus HCL Planner Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the HCL Planner Service."""
    print("👋 Shutting down Maximus HCL Planner Service...")
    print("🛑 Maximus HCL Planner Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the HCL Planner Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "HCL Planner Service is operational."}


@app.post("/generate_plan")
async def generate_resource_plan(request: PlanRequest) -> Dict[str, Any]:
    """Generates a resource alignment plan based on analysis results and operational goals.

    Args:
        request (PlanRequest): The request body containing analysis results, current state, and goals.

    Returns:
        Dict[str, Any]: A dictionary containing the generated resource plan.
    """
    print(f"[API] Generating plan based on analysis: {request.analysis_result.get('overall_health_score')}")
    
    plan_id = f"plan-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    actions: List[Dict[str, Any]] = []
    plan_details: str = ""

    # Example: Use fuzzy controller for initial actions
    fuzzy_actions = fuzzy_controller.generate_actions(
        request.analysis_result.get("overall_health_score", 1.0),
        request.current_state.get("cpu_usage", 0.0),
        request.operational_goals.get("performance_priority", 0.5)
    )
    actions.extend(fuzzy_actions)
    plan_details += "Fuzzy controller suggested actions. "

    # Example: RL agent for more complex, adaptive decisions
    if request.analysis_result.get("requires_intervention", False):
        rl_recommendations = await rl_agent.recommend_actions(
            request.current_state,
            request.analysis_result,
            request.operational_goals
        )
        actions.extend(rl_recommendations)
        plan_details += "RL agent recommended further actions due to intervention requirement."

    return {
        "timestamp": datetime.now().isoformat(),
        "plan_id": plan_id,
        "status": "generated",
        "plan_details": plan_details.strip(),
        "actions": actions,
        "estimated_impact": {"performance_boost": 0.1, "cost_reduction": 0.05} # Placeholder
    }


@app.get("/planner_status")
async def get_planner_status() -> Dict[str, Any]:
    """Retrieves the current status of the HCL Planner Service.

    Returns:
        Dict[str, Any]: A dictionary with the current status of planning components.
    """
    return {
        "status": "active",
        "fuzzy_controller_status": fuzzy_controller.get_status(),
        "rl_agent_status": await rl_agent.get_status()
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8019)
