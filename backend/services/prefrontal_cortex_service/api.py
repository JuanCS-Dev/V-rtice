"""Maximus Prefrontal Cortex Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Prefrontal
Cortex Service. It exposes functionalities for higher-order cognitive functions
such as strategic planning, decision-making, working memory, and goal-directed
behavior.

Endpoints are provided for:
- Submitting complex problems for strategic planning.
- Requesting optimal decisions based on current context and goals.
- Querying the AI's current emotional state or impulse control levels.

This API allows other Maximus AI services or human operators to leverage the
Prefrontal Cortex Service's advanced cognitive capabilities, enabling Maximus
to formulate long-term goals, evaluate potential actions, and maintain coherent,
goal-oriented behavior across the entire AI system.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import asyncio
from datetime import datetime

from emotional_state_monitor import EmotionalStateMonitor
from impulse_inhibition import ImpulseInhibition
from rational_decision_validator import RationalDecisionValidator

app = FastAPI(title="Maximus Prefrontal Cortex Service", version="1.0.0")

# Initialize PFC components
emotional_state_monitor = EmotionalStateMonitor()
impulse_inhibition = ImpulseInhibition()
rational_decision_validator = RationalDecisionValidator()


class StrategicPlanRequest(BaseModel):
    """Request model for initiating strategic planning.

    Attributes:
        problem_description (str): A description of the problem to solve.
        current_context (Dict[str, Any]): The current operational context.
        long_term_goals (List[str]): The long-term goals to consider.
    """
    problem_description: str
    current_context: Dict[str, Any]
    long_term_goals: List[str]


class DecisionRequest(BaseModel):
    """Request model for requesting a decision.

    Attributes:
        options (List[Dict[str, Any]]): A list of decision options.
        criteria (Dict[str, Any]): Criteria for evaluating the options.
        context (Optional[Dict[str, Any]]): Additional context for the decision.
    """
    options: List[Dict[str, Any]]
    criteria: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Prefrontal Cortex Service."""
    print("🧠 Starting Maximus Prefrontal Cortex Service...")
    print("✅ Maximus Prefrontal Cortex Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Prefrontal Cortex Service."""
    print("👋 Shutting down Maximus Prefrontal Cortex Service...")
    print("🛑 Maximus Prefrontal Cortex Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Prefrontal Cortex Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Prefrontal Cortex Service is operational."}


@app.post("/strategic_plan")
async def generate_strategic_plan(request: StrategicPlanRequest) -> Dict[str, Any]:
    """Generates a strategic plan to address a complex problem.

    Args:
        request (StrategicPlanRequest): The request body containing problem description, context, and goals.

    Returns:
        Dict[str, Any]: A dictionary containing the generated strategic plan.
    """
    print(f"[API] Generating strategic plan for: {request.problem_description}")
    await asyncio.sleep(0.5) # Simulate complex planning

    # Simulate plan generation, considering emotional state and impulse control
    emotional_state = await emotional_state_monitor.get_current_state()
    impulse_level = impulse_inhibition.get_inhibition_level()

    plan_details = f"Strategic plan for '{request.problem_description}' considering emotional state ({emotional_state.get('mood')}) and impulse control ({impulse_level:.2f})."
    plan_steps = [
        {"step": 1, "action": "gather_more_information", "details": "Collect data relevant to the problem.", "priority": "high"},
        {"step": 2, "action": "evaluate_risks", "details": "Assess potential risks and opportunities.", "priority": "high"},
        {"step": 3, "action": "propose_solutions", "details": "Develop multiple solution pathways.", "priority": "medium"}
    ]

    return {"status": "success", "timestamp": datetime.now().isoformat(), "plan": {"description": plan_details, "steps": plan_steps}}


@app.post("/make_decision")
async def make_decision_endpoint(request: DecisionRequest) -> Dict[str, Any]:
    """Makes an optimal decision based on provided options and criteria.

    Args:
        request (DecisionRequest): The request body containing decision options, criteria, and context.

    Returns:
        Dict[str, Any]: A dictionary containing the chosen decision and rationale.
    """
    print(f"[API] Making decision based on {len(request.options)} options.")
    await asyncio.sleep(0.3) # Simulate decision making

    # Simulate decision making, validated by rational decision validator
    chosen_option = request.options[0] # Simple mock: always choose first
    validation_result = rational_decision_validator.validate_decision(chosen_option, request.criteria, request.context)

    return {"status": "success", "timestamp": datetime.now().isoformat(), "chosen_option": chosen_option, "rationale": validation_result}


@app.get("/emotional_state")
async def get_emotional_state() -> Dict[str, Any]:
    """Retrieves the AI's current emotional state (simulated).

    Returns:
        Dict[str, Any]: A dictionary summarizing the emotional state.
    """
    return await emotional_state_monitor.get_current_state()


@app.get("/impulse_inhibition_level")
async def get_impulse_inhibition_level() -> Dict[str, Any]:
    """Retrieves the current impulse inhibition level.

    Returns:
        Dict[str, Any]: A dictionary containing the impulse inhibition level.
    """
    return {"level": impulse_inhibition.get_inhibition_level()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8037)