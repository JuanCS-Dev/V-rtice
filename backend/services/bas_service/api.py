"""Maximus BAS Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Breach
and Attack Simulation (BAS) Service. It exposes functionalities for initiating
simulated attacks, managing attack campaigns, and retrieving simulation results.

Endpoints are provided for:
- Starting and stopping attack simulations.
- Querying the status of ongoing campaigns.
- Accessing detailed reports on attack effectiveness and identified vulnerabilities.

This API allows security teams and other Maximus AI services to continuously
validate the effectiveness of security controls and improve the overall resilience
of the Maximus AI system.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
from datetime import datetime
import uuid

from atomic_executor import AtomicExecutor
from attack_techniques import AttackTechniques
from metrics import MetricsCollector
from purple_team_engine import PurpleTeamEngine
from models import AttackSimulation, AttackResult, SimulationStatus

app = FastAPI(title="Maximus BAS Service", version="1.0.0")

# Initialize BAS components
atomic_executor = AtomicExecutor()
attack_techniques = AttackTechniques()
metrics_collector = MetricsCollector()
purple_team_engine = PurpleTeamEngine(atomic_executor, metrics_collector)


class StartSimulationRequest(BaseModel):
    """Request model for starting an attack simulation.

    Attributes:
        attack_scenario (str): The name of the attack scenario to simulate.
        target_service (str): The Maximus service or component to target.
        duration_seconds (int): The duration of the simulation in seconds.
        techniques (Optional[List[str]]): Specific attack techniques to use (e.g., 'T1059').
    """
    attack_scenario: str
    target_service: str
    duration_seconds: int = 60
    techniques: Optional[List[str]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the BAS Service."""
    print("💥 Starting Maximus BAS Service...")
    print("✅ Maximus BAS Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the BAS Service."""
    print("👋 Shutting down Maximus BAS Service...")
    print("🛑 Maximus BAS Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the BAS Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "BAS Service is operational."}


@app.post("/simulate", response_model=AttackSimulation)
async def start_simulation(request: StartSimulationRequest) -> AttackSimulation:
    """Starts a new breach and attack simulation.

    Args:
        request (StartSimulationRequest): The request body containing simulation parameters.

    Returns:
        AttackSimulation: The details of the started simulation.
    """
    print(f"[API] Starting simulation: {request.attack_scenario} against {request.target_service}")
    simulation_id = str(uuid.uuid4())
    simulation = AttackSimulation(
        id=simulation_id,
        attack_scenario=request.attack_scenario,
        target_service=request.target_service,
        start_time=datetime.now().isoformat(),
        status=SimulationStatus.RUNNING,
        techniques_used=request.techniques or []
    )
    # In a real scenario, this would trigger the PurpleTeamEngine to start the simulation
    asyncio.create_task(purple_team_engine.run_simulation(simulation))
    return simulation


@app.get("/simulation/{simulation_id}", response_model=AttackSimulation)
async def get_simulation_status(simulation_id: str) -> AttackSimulation:
    """Retrieves the current status of a specific attack simulation.

    Args:
        simulation_id (str): The ID of the simulation to retrieve.

    Returns:
        AttackSimulation: The current status and details of the simulation.

    Raises:
        HTTPException: If the simulation ID is not found.
    """
    simulation = purple_team_engine.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found.")
    return simulation


@app.get("/simulation/{simulation_id}/results", response_model=List[AttackResult])
async def get_simulation_results(simulation_id: str) -> List[AttackResult]:
    """Retrieves the results of a completed attack simulation.

    Args:
        simulation_id (str): The ID of the simulation to retrieve results for.

    Returns:
        List[AttackResult]: A list of attack results from the simulation.

    Raises:
        HTTPException: If the simulation ID is not found or results are not yet available.
    """
    simulation = purple_team_engine.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found.")
    if simulation.status != SimulationStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Simulation not yet completed.")
    return simulation.results


@app.get("/metrics")
async def get_bas_metrics() -> Dict[str, Any]:
    """Retrieves overall metrics for the BAS service.

    Returns:
        Dict[str, Any]: A dictionary containing various BAS operational metrics.
    """
    return metrics_collector.get_all_metrics()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
