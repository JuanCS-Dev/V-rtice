"""Maximus Orchestrator Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Orchestrator Service.
It initializes and configures the FastAPI application, sets up event handlers
for startup and shutdown, and defines the API endpoints for managing and
coordinating the activities of all other Maximus AI services.

It acts as the central command and control hub, receiving high-level directives,
breaking them down into multi-service workflows, distributing tasks, and
monitoring their execution. This service is crucial for ensuring efficient,
coherent, and goal-oriented behavior across the entire Maximus AI ecosystem,
providing a unified interface for controlling and observing its operations.
"""

import asyncio
import logging
import os
import uuid
from typing import Any, Dict, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


app = FastAPI(title="Maximus Orchestrator Service", version="1.0.0")

# Configuration for Maximus sub-services (from environment or defaults)
MAXIMUS_CORE_SERVICE_URL = os.getenv("MAXIMUS_CORE_SERVICE_URL", "http://localhost:8000")
MAXIMUS_ATLAS_SERVICE_URL = os.getenv("MAXIMUS_ATLAS_SERVICE_URL", "http://localhost:8007")
MAXIMUS_ORACULO_SERVICE_URL = os.getenv("MAXIMUS_ORACULO_SERVICE_URL", "http://localhost:8026")
MAXIMUS_IMMUNIS_API_SERVICE_URL = os.getenv("MAXIMUS_IMMUNIS_API_SERVICE_URL", "http://localhost:8021")
MAXIMUS_ADR_CORE_SERVICE_URL = os.getenv("MAXIMUS_ADR_CORE_SERVICE_URL", "http://localhost:8005")


class OrchestrationRequest(BaseModel):
    """Request model for initiating a complex orchestration workflow.

    Attributes:
        workflow_name (str): The name of the workflow to execute (e.g., 'threat_hunting', 'system_optimization').
        parameters (Optional[Dict[str, Any]]): Parameters for the workflow.
        priority (int): The priority of the workflow (1-10, 10 being highest).
    """

    workflow_name: str
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 5


class WorkflowStatus(BaseModel):
    """Response model for workflow status.

    Attributes:
        workflow_id (str): Unique identifier for the workflow.
        status (str): Current status of the workflow (e.g., 'running', 'completed', 'failed').
        current_step (Optional[str]): The current step being executed.
        progress (float): Progress percentage (0.0 to 1.0).
        results (Optional[Dict[str, Any]]): Final results if completed.
        error (Optional[str]): Error message if failed.
    """

    workflow_id: str
    status: str
    current_step: Optional[str] = None
    progress: float = 0.0
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# In-memory storage for active workflows (for demonstration)
active_workflows: Dict[str, WorkflowStatus] = {}


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Orchestrator Service."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    # Initialize as None to avoid NameError if exception occurs
    metrics_exporter = None
    constitutional_tracer = None
    health_checker = None

    try:
        # Logging
        configure_constitutional_logging(
            service_name="maximus_orchestrator_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )
        logger = logging.getLogger(__name__)

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="maximus_orchestrator_service",
            version=service_version
        )
        auto_update_sabbath_status("maximus_orchestrator_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="maximus_orchestrator_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="maximus_orchestrator_service")
        logger.info("✅ Constitutional Health Checker initialized")

        # Routes
        if metrics_exporter:
            app.include_router(metrics_exporter.create_router())
            logger.info("✅ Constitutional metrics routes added")

    except Exception as e:
        logger.error(f"❌ Constitutional initialization failed: {e}", exc_info=True)

    # Mark startup complete
    if health_checker:
        health_checker.mark_startup_complete()

    print(" orchestrator Starting Maximus Orchestrator Service...")
    print("✅ Maximus Orchestrator Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Orchestrator Service."""
    print("👋 Shutting down Maximus Orchestrator Service...")
    print("🛑 Maximus Orchestrator Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Orchestrator Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Orchestrator Service is operational."}


@app.post("/orchestrate", response_model=WorkflowStatus)
async def orchestrate_workflow(request: OrchestrationRequest) -> WorkflowStatus:
    """Initiates a complex workflow across multiple Maximus services.

    Args:
        request (OrchestrationRequest): The request body containing workflow details.

    Returns:
        WorkflowStatus: The initial status of the initiated workflow.
    """
    workflow_id = str(uuid.uuid4())
    print(f"[API] Initiating workflow '{request.workflow_name}' (ID: {workflow_id})")

    initial_status = WorkflowStatus(
        workflow_id=workflow_id,
        status="running",
        current_step="Initializing",
        progress=0.0,
    )
    active_workflows[workflow_id] = initial_status

    # Start the workflow in a background task
    asyncio.create_task(run_workflow(workflow_id, request.workflow_name, request.parameters))

    return initial_status


@app.get("/workflow/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str) -> WorkflowStatus:
    """Retrieves the current status of a specific workflow.

    Args:
        workflow_id (str): The ID of the workflow.

    Returns:
        WorkflowStatus: The current status and details of the workflow.

    Raises:
        HTTPException: If the workflow ID is not found.
    """
    workflow = active_workflows.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return workflow


async def run_workflow(workflow_id: str, workflow_name: str, parameters: Optional[Dict[str, Any]]):
    """Simulates the execution of a multi-step workflow.

    Args:
        workflow_id (str): The ID of the workflow.
        workflow_name (str): The name of the workflow.
        parameters (Optional[Dict[str, Any]]): Parameters for the workflow.
    """
    workflow_status = active_workflows[workflow_id]
    async with httpx.AsyncClient() as client:
        try:
            if workflow_name == "threat_hunting":
                await _threat_hunting_workflow(client, workflow_status, parameters)
            elif workflow_name == "system_optimization":
                await _system_optimization_workflow(client, workflow_status, parameters)
            else:
                raise ValueError(f"Unknown workflow: {workflow_name}")

            workflow_status.status = "completed"
            workflow_status.progress = 1.0
            workflow_status.current_step = "Finished"
            workflow_status.results = {"message": f"Workflow {workflow_name} completed successfully."}

        except Exception as e:
            workflow_status.status = "failed"
            workflow_status.error = str(e)
            workflow_status.current_step = "Error"
            print(f"[Orchestrator] Workflow {workflow_id} failed: {e}")


async def _threat_hunting_workflow(
    client: httpx.AsyncClient,
    status: WorkflowStatus,
    parameters: Optional[Dict[str, Any]],
):
    """Simulates a threat hunting workflow.

    Args:
        client (httpx.AsyncClient): HTTP client for inter-service communication.
        status (WorkflowStatus): The status object for the current workflow.
        parameters (Optional[Dict[str, Any]]): Parameters for the workflow.
    """
    status.current_step = "Starting Threat Hunting"
    status.progress = 0.1
    print(f"[Orchestrator] Workflow {status.workflow_id}: Starting Threat Hunting.")
    await asyncio.sleep(1)

    # Step 1: Query Atlas for environmental context
    status.current_step = "Querying Atlas Service"
    status.progress = 0.2
    atlas_response = await client.post(
        f"{MAXIMUS_ATLAS_SERVICE_URL}/query_environment",
        json={"query": "identify suspicious network segments", "context": parameters},
    )
    atlas_response.raise_for_status()
    print(f"[Orchestrator] Atlas response: {atlas_response.json()}")
    await asyncio.sleep(1)

    # Step 2: Use Oraculo for threat prediction
    status.current_step = "Consulting Oraculo for Prediction"
    status.progress = 0.5
    oraculo_response = await client.post(
        f"{MAXIMUS_ORACULO_SERVICE_URL}/predict",
        json={
            "data": atlas_response.json(),
            "prediction_type": "threat_level",
            "time_horizon": "24h",
        },
    )
    oraculo_response.raise_for_status()
    print(f"[Orchestrator] Oraculo prediction: {oraculo_response.json()}")
    await asyncio.sleep(1)

    # Step 3: Trigger Immunis response if threat predicted
    status.current_step = "Triggering Immunis Response"
    status.progress = 0.8
    if oraculo_response.json()["prediction"]["risk_assessment"] == "high":
        immunis_response = await client.post(
            f"{MAXIMUS_IMMUNIS_API_SERVICE_URL}/threat_alert",
            json={
                "threat_id": f"predicted_threat_{status.workflow_id}",
                "threat_type": "predicted_attack",
                "severity": "high",
                "details": oraculo_response.json(),
                "source": "MaximusOrchestrator",
            },
        )
        immunis_response.raise_for_status()
        print(f"[Orchestrator] Immunis response: {immunis_response.json()}")
    else:
        print("[Orchestrator] No high threat predicted, no Immunis response triggered.")
    await asyncio.sleep(1)


async def _system_optimization_workflow(
    client: httpx.AsyncClient,
    status: WorkflowStatus,
    parameters: Optional[Dict[str, Any]],
):
    """Simulates a system optimization workflow.

    Args:
        client (httpx.AsyncClient): HTTP client for inter-service communication.
        status (WorkflowStatus): The status object for the current workflow.
        parameters (Optional[Dict[str, Any]]): Parameters for the workflow.
    """
    status.current_step = "Starting System Optimization"
    status.progress = 0.1
    print(f"[Orchestrator] Workflow {status.workflow_id}: Starting System Optimization.")
    await asyncio.sleep(1)

    # Step 1: Get current system metrics from Maximus Core
    status.current_step = "Getting System Metrics"
    status.progress = 0.3
    core_metrics_response = await client.get(
        f"{MAXIMUS_CORE_SERVICE_URL}/health"
    )  # Using health as a proxy for metrics
    core_metrics_response.raise_for_status()
    print(f"[Orchestrator] Core metrics: {core_metrics_response.json()}")
    await asyncio.sleep(1)

    # Step 2: Consult Oraculo for optimization suggestions
    status.current_step = "Consulting Oraculo for Optimization"
    status.progress = 0.6
    oraculo_optimization_response = await client.post(
        f"{MAXIMUS_ORACULO_SERVICE_URL}/predict",
        json={
            "data": core_metrics_response.json(),
            "prediction_type": "resource_optimization",
            "time_horizon": "1h",
        },
    )
    oraculo_optimization_response.raise_for_status()
    print(f"[Orchestrator] Oraculo optimization suggestions: {oraculo_optimization_response.json()}")
    await asyncio.sleep(1)

    # Step 3: Apply suggestions via ADR Core Service (simulated)
    status.current_step = "Applying Optimization Actions"
    status.progress = 0.9
    suggestions = oraculo_optimization_response.json()["prediction"]["suggestions"]
    if suggestions:
        for suggestion in suggestions:
            if suggestion["type"] == "scale_up":
                print(f"[Orchestrator] Simulating scale up: {suggestion}")
                # In a real scenario, call HCL Executor or similar
                # adr_response = await client.post(f"{MAXIMUS_ADR_CORE_SERVICE_URL}/respond", json={...})
            elif suggestion["type"] == "optimize_database":
                print(f"[Orchestrator] Simulating database optimization: {suggestion}")
            await asyncio.sleep(0.5)
    print("[Orchestrator] Optimization actions simulated.")
    await asyncio.sleep(1)


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="0.0.0.0", port=8027)
