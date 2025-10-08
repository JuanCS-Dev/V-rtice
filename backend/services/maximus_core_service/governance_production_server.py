#!/usr/bin/env python
"""
Governance Production Server

Production-ready FastAPI server dedicated to Governance Workspace.
Lightweight server without full MAXIMUS dependencies.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO compliant - NO MOCK, NO PLACEHOLDER, NO TODO
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from governance_sse import create_governance_api
from hitl import (
    DecisionQueue,
    EscalationManager,
    HITLConfig,
    HITLDecisionFramework,
    OperatorInterface,
    SLAConfig,
)

# Create FastAPI app
app = FastAPI(
    title="Governance Workspace - Production Server",
    version="1.0.0",
    description="HITL Governance Workspace with SSE streaming for ethical AI decision review",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
decision_queue = None
operator_interface = None
decision_framework = None


@app.on_event("startup")
async def startup_event():
    """Initialize Governance components on startup."""
    global decision_queue, operator_interface, decision_framework

    print("=" * 80)
    print("🏛️  Starting Governance Workspace Production Server")
    print("=" * 80)
    print()

    # Create SLA configuration
    print("🔧 Initializing HITL Governance Framework...")
    sla_config = SLAConfig(
        low_risk_timeout=30,  # 30 minutes
        medium_risk_timeout=15,  # 15 minutes
        high_risk_timeout=10,  # 10 minutes
        critical_risk_timeout=5,  # 5 minutes
        warning_threshold=0.75,  # Warn at 75% of SLA
        auto_escalate_on_timeout=True,
    )
    print("✅ SLA Config created")

    # Create HITL configuration
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
    print("✅ HITL Config created")

    # Create DecisionQueue
    decision_queue = DecisionQueue(sla_config=sla_config, max_size=1000)
    print("✅ Decision Queue initialized")

    # Create HITLDecisionFramework
    decision_framework = HITLDecisionFramework(config=hitl_config)
    decision_framework.set_decision_queue(decision_queue)
    print("✅ HITL Decision Framework initialized and connected")

    # Create EscalationManager
    escalation_manager = EscalationManager()
    print("✅ Escalation Manager initialized")

    # Create OperatorInterface
    operator_interface = OperatorInterface(
        decision_queue=decision_queue,
        decision_framework=decision_framework,
        escalation_manager=escalation_manager,
    )
    print("✅ Operator Interface initialized")

    # Register Governance API routes
    governance_router = create_governance_api(
        decision_queue=decision_queue,
        operator_interface=operator_interface,
    )
    app.include_router(governance_router, prefix="/api/v1")
    print("✅ Governance API routes registered at /api/v1/governance/*")

    print()
    print("=" * 80)
    print("✅ Governance Workspace Production Server started successfully")
    print("=" * 80)
    print()
    print("📡 Endpoints available:")
    print("   - http://0.0.0.0:8000/api/v1/governance/health")
    print("   - http://0.0.0.0:8000/api/v1/governance/stream/{operator_id}")
    print("   - http://0.0.0.0:8000/api/v1/governance/pending")
    print("   - http://0.0.0.0:8000/api/v1/governance/session/create")
    print("   - http://0.0.0.0:8000/docs (API documentation)")
    print()


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown of Governance components."""
    global decision_queue

    print()
    print("=" * 80)
    print("🛑 Shutting down Governance Workspace Production Server")
    print("=" * 80)
    print()

    # Stop DecisionQueue SLA monitor
    if decision_queue:
        decision_queue.sla_monitor.stop()
        print("✅ Decision Queue shut down")

    print("✅ Governance Workspace shutdown complete")
    print()


@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Governance server.

    Returns:
        Health status and component status
    """
    return {
        "status": "healthy",
        "service": "Governance Workspace Production Server",
        "version": "1.0.0",
        "components": {
            "decision_queue": decision_queue is not None,
            "operator_interface": operator_interface is not None,
            "decision_framework": decision_framework is not None,
        },
    }


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "Governance Workspace Production Server",
        "version": "1.0.0",
        "description": "HITL Governance Workspace for ethical AI decision review",
        "docs": "/docs",
        "health": "/health",
        "governance_api": "/api/v1/governance",
    }


if __name__ == "__main__":
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
