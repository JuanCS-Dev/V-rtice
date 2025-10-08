"""
Standalone Governance SSE Server for E2E Testing

This is a minimal FastAPI server that includes only the governance routes,
avoiding dependencies on other MAXIMUS components. Use for manual E2E testing.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: Production-ready, REGRA DE OURO compliant
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Governance imports
from governance_sse.api_routes import create_governance_api

# HITL imports
from hitl import (
    DecisionQueue,
    HITLDecisionFramework,
    OperatorInterface,
    SLAConfig,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Application Lifespan Management
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Startup: Initialize HITL components (DecisionQueue, OperatorInterface)
    Shutdown: Gracefully shutdown queue and connections
    """
    logger.info("🚀 Starting Governance SSE Server (Standalone)")

    # Initialize HITL components
    sla_config = SLAConfig(
        low_risk_timeout=30,  # 30 minutes
        medium_risk_timeout=15,  # 15 minutes
        high_risk_timeout=10,  # 10 minutes
        critical_risk_timeout=5,  # 5 minutes
        warning_threshold=0.75,
        auto_escalate_on_timeout=True,
    )

    decision_queue = DecisionQueue(sla_config=sla_config, max_size=1000)
    decision_framework = HITLDecisionFramework()
    operator_interface = OperatorInterface(
        decision_queue=decision_queue,
        decision_framework=decision_framework,
    )

    # Create governance API router
    governance_router = create_governance_api(decision_queue, operator_interface)

    # Register router
    app.include_router(governance_router, prefix="/api/v1")

    # Store in app state
    app.state.decision_queue = decision_queue
    app.state.operator_interface = operator_interface

    logger.info("✅ Governance SSE Server initialized")
    logger.info("📡 Endpoints available at /api/v1/governance/*")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Governance SSE Server")
    decision_queue.sla_monitor.stop()
    logger.info("✅ Shutdown complete")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Governance SSE Server (Standalone)",
    description="Real-time HITL decision review via Server-Sent Events",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Governance SSE Server (Standalone)",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/governance/health",
            "pending": "/api/v1/governance/pending",
            "stream": "/api/v1/governance/stream/{operator_id}",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    """Global health check."""
    return {"status": "healthy", "service": "governance-sse-standalone"}


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Launching Governance SSE Server on http://localhost:8001")
    logger.info("📖 API docs available at http://localhost:8001/docs")

    uvicorn.run(
        "standalone_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
    )
