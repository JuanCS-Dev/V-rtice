"""Maximus Core Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Core Service.
It initializes and starts the Maximus AI system, including its autonomic core,
and exposes its capabilities via an API (e.g., FastAPI).

It handles the setup of the application, defines API endpoints for interaction,
and manages the lifecycle of the Maximus AI, ensuring it can receive requests,
process them, and return intelligent responses.
"""

from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from _demonstration.maximus_integrated import MaximusIntegrated
from pydantic import BaseModel

from consciousness.api import create_consciousness_api

# Consciousness System imports
from consciousness.system import ConsciousnessConfig, ConsciousnessSystem
from governance_sse import create_governance_api

# HITL imports for Governance SSE
from hitl import DecisionQueue, HITLConfig, HITLDecisionFramework, OperatorInterface, SLAConfig

app = FastAPI(title="Maximus Core Service", version="1.0.0")
maximus_ai: MaximusIntegrated | None = None

# HITL components (initialized on startup)
decision_queue: DecisionQueue | None = None
operator_interface: OperatorInterface | None = None
decision_framework: HITLDecisionFramework | None = None

# Consciousness System (initialized on startup)
consciousness_system: ConsciousnessSystem | None = None


class QueryRequest(BaseModel):
    """Request model for processing a query.

    Attributes:
        query (str): The natural language query to be processed by Maximus AI.
        context (Optional[Dict[str, Any]]): Additional contextual information for the query.
    """

    query: str
    context: dict[str, Any] | None = None


@app.on_event("startup")
async def startup_event():
    """Initializes the Maximus AI system and starts its autonomic core on application startup."""
    global maximus_ai, decision_queue, operator_interface, decision_framework, consciousness_system

    print("🚀 Starting Maximus Core Service...")

    # Initialize MAXIMUS AI
    maximus_ai = MaximusIntegrated()
    await maximus_ai.start_autonomic_core()
    print("✅ MAXIMUS AI initialized")

    # Initialize HITL components for Governance Workspace
    print("🔧 Initializing HITL Governance Framework...")

    # Create SLA configuration for decision queue
    sla_config = SLAConfig(
        low_risk_timeout=30,  # 30 minutes
        medium_risk_timeout=15,  # 15 minutes
        high_risk_timeout=10,  # 10 minutes
        critical_risk_timeout=5,  # 5 minutes
        warning_threshold=0.75,  # Warn at 75% of SLA
        auto_escalate_on_timeout=True,
    )

    # Create HITL configuration for decision framework
    hitl_config = HITLConfig(
        full_automation_threshold=0.99,  # Very high threshold for full automation
        supervised_threshold=0.80,  # Medium threshold for supervised execution
        advisory_threshold=0.60,  # Low threshold for advisory
        high_risk_requires_approval=True,  # HIGH risk always requires approval
        critical_risk_requires_approval=True,  # CRITICAL risk always requires approval
        max_queue_size=1000,
        audit_all_decisions=True,
        redact_pii_in_audit=True,
        audit_retention_days=365 * 7,  # 7 years for compliance
    )

    # Create DecisionQueue with SLA config
    decision_queue = DecisionQueue(sla_config=sla_config, max_size=1000)
    print("✅ Decision Queue initialized")

    # Create HITLDecisionFramework
    decision_framework = HITLDecisionFramework(config=hitl_config)
    decision_framework.set_decision_queue(decision_queue)
    print("✅ HITL Decision Framework initialized and connected to DecisionQueue")

    # Create OperatorInterface with full HITL integration
    operator_interface = OperatorInterface(
        decision_queue=decision_queue,
        decision_framework=decision_framework,
        # escalation_manager, audit_trail can be added later
    )
    print("✅ Operator Interface initialized")

    # Register Governance API routes
    governance_router = create_governance_api(
        decision_queue=decision_queue,
        operator_interface=operator_interface,
    )
    app.include_router(governance_router, prefix="/api/v1")
    print("✅ Governance API routes registered at /api/v1/governance/*")

    # Initialize Consciousness System
    print("🧠 Initializing Consciousness System...")
    try:
        # Create consciousness system with production config
        consciousness_config = ConsciousnessConfig(
            tig_node_count=100,
            tig_target_density=0.25,
            esgt_min_salience=0.65,
            esgt_refractory_period_ms=200.0,
            esgt_max_frequency_hz=5.0,
            esgt_min_available_nodes=25,
            arousal_update_interval_ms=50.0,
            arousal_baseline=0.60,
        )
        consciousness_system = ConsciousnessSystem(consciousness_config)
        await consciousness_system.start()

        # Register Consciousness API routes
        consciousness_router = create_consciousness_api(consciousness_system.get_system_dict())
        app.include_router(consciousness_router)
        print("✅ Consciousness API routes registered at /api/consciousness/*")
    except Exception as e:
        print(f"⚠️  Consciousness System initialization failed: {e}")
        print("   Continuing without consciousness monitoring...")
        consciousness_system = None

    print("✅ Maximus Core Service started successfully with full HITL Governance integration")


@app.on_event("shutdown")
async def shutdown_event():
    """Shuts down the Maximus AI system and its autonomic core on application shutdown."""
    global maximus_ai, decision_queue, consciousness_system
    print("👋 Shutting down Maximus Core Service...")

    # Stop Consciousness System
    if consciousness_system:
        await consciousness_system.stop()
        print("✅ Consciousness System shut down")

    # Stop DecisionQueue SLA monitor
    if decision_queue:
        decision_queue.sla_monitor.stop()
        print("✅ Decision Queue shut down")

    # Stop MAXIMUS AI
    if maximus_ai:
        await maximus_ai.stop_autonomic_core()
        print("✅ MAXIMUS AI shut down")

    print("🛑 Maximus Core Service shut down.")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Performs a health check of the Maximus Core Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    if maximus_ai:
        return {"status": "healthy", "message": "Maximus Core Service is operational."}
    raise HTTPException(status_code=503, detail="Maximus AI not initialized.")


@app.post("/query")
async def process_query_endpoint(request: QueryRequest) -> dict[str, Any]:
    """Processes a natural language query using the Maximus AI.

    Args:
        request (QueryRequest): The request body containing the query and optional context.

    Returns:
        Dict[str, Any]: The response from the Maximus AI, including the final answer, confidence score, and other metadata.

    Raises:
        HTTPException: If the Maximus AI is not initialized.
    """
    if not maximus_ai:
        raise HTTPException(status_code=503, detail="Maximus AI not initialized.")
    try:
        response = await maximus_ai.process_query(request.query, request.context)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    # This block is for local development and running the FastAPI app directly.
    # In a production Docker environment, uvicorn is typically run via command line.

    # Start Prometheus metrics server
    from prometheus_client import start_http_server
    start_http_server(8001)
    print("📈 Prometheus metrics server started on port 8001")

    uvicorn.run(app, host="0.0.0.0", port=8000)
