"""Maximus HCL Executor Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Homeostatic Control
Loop (HCL) Executor Service. It initializes and configures the FastAPI
application, sets up event handlers for startup and shutdown, and defines the
API endpoints for receiving and executing resource alignment plans.

It orchestrates the execution of concrete actions based on plans from the HCL
Planner Service, interacting with underlying infrastructure (e.g., Kubernetes,
Docker) to adjust the AI's operational environment. This service is crucial
for translating HCL decisions into real-world system changes, maintaining
Maximus AI's stability and performance.
"""

from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from action_executor import ActionExecutor
from k8s_controller import KubernetesController

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


app = FastAPI(title="Maximus HCL Executor Service", version="1.0.0")

# Initialize executors
k8s_controller = KubernetesController()
action_executor = ActionExecutor(k8s_controller)


class ExecutePlanRequest(BaseModel):
    """Request model for executing a resource alignment plan.

    Attributes:
        plan_id (str): Unique identifier for the plan.
        actions (List[Dict[str, Any]]): A list of actions to be executed.
        priority (int): The priority of the plan execution (1-10, 10 being highest).
    """

    plan_id: str
    actions: List[Dict[str, Any]]
    priority: int = 5


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the HCL Executor Service."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="hcl_executor_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="hcl_executor_service",
            version=service_version
        )
        auto_update_sabbath_status("hcl_executor_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="hcl_executor_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="hcl_executor_service")
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

    print("⚙️ Starting Maximus HCL Executor Service...")
    print("✅ Maximus HCL Executor Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the HCL Executor Service."""
    print("👋 Shutting down Maximus HCL Executor Service...")
    print("🛑 Maximus HCL Executor Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the HCL Executor Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "HCL Executor Service is operational."}


@app.post("/execute_plan")
async def execute_resource_plan(request: ExecutePlanRequest) -> Dict[str, Any]:
    """Receives a resource alignment plan and executes its actions.

    Args:
        request (ExecutePlanRequest): The request body containing the plan details.

    Returns:
        Dict[str, Any]: A dictionary containing the execution results.
    """
    print(f"[API] Received plan {request.plan_id} for execution with {len(request.actions)} actions.")

    execution_results = await action_executor.execute_actions(request.plan_id, request.actions, request.priority)

    return {
        "timestamp": datetime.now().isoformat(),
        "plan_id": request.plan_id,
        "status": (
            "completed" if all(res.get("status") == "success" for res in execution_results) else "completed_with_errors"
        ),
        "action_results": execution_results,
    }


@app.get("/k8s_status")
async def get_kubernetes_status() -> Dict[str, Any]:
    """Retrieves the current status of the Kubernetes cluster (simulated).

    Returns:
        Dict[str, Any]: A dictionary with Kubernetes cluster status.
    """
    return await k8s_controller.get_cluster_status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8016)
