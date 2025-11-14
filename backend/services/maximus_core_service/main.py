"""Maximus Core Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Core Service.
It initializes and starts the Maximus AI system, including its autonomic core,
and exposes its capabilities via an API (e.g., FastAPI).

It handles the setup of the application, defines API endpoints for interaction,
and manages the lifecycle of the Maximus AI, ensuring it can receive requests,
process them, and return intelligent responses.
"""

import logging
import os
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from _demonstration.maximus_integrated import MaximusIntegrated
from pydantic import BaseModel

from consciousness.api import create_consciousness_api

# Consciousness System imports
from consciousness.system import ConsciousnessConfig, ConsciousnessSystem
from governance_sse import create_governance_api

# ADW (AI-Driven Workflows) router
from adw_router import router as adw_router

# HITL imports for Governance SSE
from hitl import DecisionQueue, HITLConfig, HITLDecisionFramework, OperatorInterface, SLAConfig

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck

# Import Service Registry client
try:
    from shared.vertice_registry_client import auto_register_service, RegistryClient
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False
    print("⚠️  Service Registry client not available - running standalone")

app = FastAPI(title="Maximus Core Service", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://localhost:8000",  # API Gateway
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
maximus_ai: MaximusIntegrated | None = None

# HITL components (initialized on startup)
decision_queue: DecisionQueue | None = None
operator_interface: OperatorInterface | None = None
decision_framework: HITLDecisionFramework | None = None

# Consciousness System (initialized on startup)
consciousness_system: ConsciousnessSystem | None = None

# Global heartbeat task for Service Registry
_heartbeat_task = None


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
            service_name="maximus_core_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )
        logger = logging.getLogger(__name__)

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="maximus_core_service",
            version=service_version
        )
        auto_update_sabbath_status("maximus_core_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="maximus_core_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="maximus_core_service")
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

    global maximus_ai, decision_queue, operator_interface, decision_framework, consciousness_system, _heartbeat_task

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

    # Register ADW (AI-Driven Workflows) API routes
    app.include_router(adw_router)
    print("✅ ADW API routes registered at /api/adw/*")

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

    # Auto-register with Service Registry
    if REGISTRY_AVAILABLE:
        try:
            _heartbeat_task = await auto_register_service(
                service_name="maximus_core_service",
                port=8150,  # Internal container port
                health_endpoint="/health",
                metadata={"category": "maximus_core", "version": "1.0.0"}
            )
            print("✅ Registered with Vértice Service Registry")
        except Exception as e:
            print(f"⚠️  Failed to register with service registry: {e}")

    print("✅ Maximus Core Service started successfully with full HITL Governance integration")


@app.on_event("shutdown")
async def shutdown_event():
    """Shuts down the Maximus AI system and its autonomic core on application shutdown."""
    global maximus_ai, decision_queue, consciousness_system, _heartbeat_task
    print("👋 Shutting down Maximus Core Service...")

    # Deregister from Service Registry
    if _heartbeat_task:
        _heartbeat_task.cancel()
    if REGISTRY_AVAILABLE:
        try:
            await RegistryClient.deregister("maximus_core_service")
        except:
            pass

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
async def health_check() -> dict[str, Any]:
    """Performs a comprehensive health check of the Maximus Core Service.

    Checks:
    - MAXIMUS AI status
    - Consciousness System health (TIG, ESGT, Arousal, Safety)
    - PrefrontalCortex status (social cognition)
    - ToM Engine status (with Redis cache if configured)
    - Decision Queue status (HITL Governance)

    Returns:
        Dict[str, Any]: Comprehensive health status with component breakdown
    """
    health_status = {
        "status": "healthy",
        "message": "Maximus Core Service is operational.",
        "timestamp": __import__("time").time(),
        "components": {}
    }

    # Check MAXIMUS AI
    if not maximus_ai:
        health_status["status"] = "degraded"
        health_status["components"]["maximus_ai"] = {"status": "not_initialized"}
    else:
        health_status["components"]["maximus_ai"] = {"status": "healthy"}

    # Check Consciousness System
    if consciousness_system:
        is_healthy = consciousness_system.is_healthy()
        health_status["components"]["consciousness"] = {
            "status": "healthy" if is_healthy else "unhealthy",
            "running": consciousness_system._running,
            "safety_enabled": consciousness_system.config.safety_enabled
        }

        # Add TIG Fabric status
        if consciousness_system.tig_fabric:
            tig_metrics = consciousness_system.tig_fabric.get_metrics()
            health_status["components"]["tig_fabric"] = {
                "status": "healthy",
                "node_count": len(consciousness_system.tig_fabric.nodes),
                "edge_count": tig_metrics.edge_count,
                "avg_latency_us": tig_metrics.avg_latency_us
            }

        # Add ESGT Coordinator status
        if consciousness_system.esgt_coordinator:
            health_status["components"]["esgt_coordinator"] = {
                "status": "healthy" if consciousness_system.esgt_coordinator._running else "stopped",
                "total_events": consciousness_system.esgt_coordinator.total_events,
                "success_rate": consciousness_system.esgt_coordinator.get_success_rate()
            }

        # TRACK 1: Add PrefrontalCortex status
        if consciousness_system.prefrontal_cortex:
            pfc_status = await consciousness_system.prefrontal_cortex.get_status()
            health_status["components"]["prefrontal_cortex"] = {
                "status": "healthy",
                "signals_processed": pfc_status["total_signals_processed"],
                "actions_generated": pfc_status["total_actions_generated"],
                "approval_rate": pfc_status["approval_rate"],
                "metacognition": pfc_status["metacognition"]
            }

        # TRACK 1: Add ToM Engine status (including Redis cache)
        if consciousness_system.tom_engine:
            tom_stats = await consciousness_system.tom_engine.get_stats()
            health_status["components"]["tom_engine"] = {
                "status": "initialized" if consciousness_system.tom_engine._initialized else "not_initialized",
                "total_agents": tom_stats["total_agents"],
                "memory_cache_size": tom_stats["memory"]["cache_size"],
                "contradictions": tom_stats["contradictions"]["total"],
                "redis_cache": {
                    "enabled": tom_stats["redis_cache"]["enabled"],
                    "hit_rate": tom_stats["redis_cache"].get("hit_rate", 0.0) if tom_stats["redis_cache"]["enabled"] else None
                }
            }

        # Add Safety Protocol status (if enabled)
        if consciousness_system.config.safety_enabled and consciousness_system.safety_protocol:
            safety_status = consciousness_system.get_safety_status()
            health_status["components"]["safety_protocol"] = {
                "status": "monitoring" if safety_status["monitoring_active"] else "inactive",
                "kill_switch_triggered": safety_status["kill_switch_triggered"],
                "active_violations": safety_status["active_violations"]
            }
    else:
        health_status["components"]["consciousness"] = {"status": "not_initialized"}

    # Check HITL Decision Queue
    if decision_queue:
        pending_decisions = decision_queue.get_pending_decisions()
        
        # Track SLA violations from decision queue
        sla_violations = sum(
            1 for decision in pending_decisions
            if hasattr(decision, 'created_at') and 
            (datetime.utcnow() - decision.created_at).total_seconds() > 300  # 5min SLA
        )
        
        health_status["components"]["decision_queue"] = {
            "status": "healthy" if sla_violations == 0 else "degraded",
            "pending_decisions": len(pending_decisions),
            "sla_violations": sla_violations,
        }
    else:
        health_status["components"]["decision_queue"] = {"status": "not_initialized"}

    # Determine overall status
    component_statuses = [c.get("status") for c in health_status["components"].values() if "status" in c]
    if any(s in ["unhealthy", "not_initialized"] for s in component_statuses):
        health_status["status"] = "degraded"
    if not maximus_ai:
        raise HTTPException(status_code=503, detail="Service degraded: MAXIMUS AI not initialized")

    return health_status


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
        # Ensure context is a dict, not None
        context = request.context if request.context is not None else {}
        response = await maximus_ai.process_query(request.query, context)
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

    # Core service runs on 8100, API Gateway proxies on 8000
    uvicorn.run(app, host="0.0.0.0", port=8100)
