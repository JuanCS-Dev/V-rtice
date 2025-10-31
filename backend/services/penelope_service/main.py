"""PENELOPE (Christian Autonomous Healing Service) - Main Application Entry Point.

Este serviço provê capacidades de auto-cura autônoma governadas por princípios
cristãos estabelecidos nos 7 Artigos Bíblicos de Governança.

Key Features:
- Autonomous anomaly detection and diagnosis
- Code patch generation with 7 Biblical Articles governance
- Digital twin validation before production deployment
- Wisdom Base for historical precedent learning
- Sabbath observance (no patches on Sundays)

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import uvicorn
from core.observability_client import ObservabilityClient
from core.praotes_validator import PraotesValidator

# Import PENELOPE core components
from core.sophia_engine import SophiaEngine
from core.tapeinophrosyne_monitor import TapeinophrosyneMonitor
from core.wisdom_base_client import WisdomBaseClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import start_http_server

# Shared library imports (work when in ~/vertice-dev/backend/services/)
from shared.vertice_registry_client import RegistryClient, auto_register_service

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global service components
wisdom_base: WisdomBaseClient | None = None
observability_client: ObservabilityClient | None = None
sophia_engine: SophiaEngine | None = None
praotes_validator: PraotesValidator | None = None
tapeinophrosyne_monitor: TapeinophrosyneMonitor | None = None
_heartbeat_task: asyncio.Task | None = None


def is_sabbath() -> bool:
    """
    Verifica se é Sabbath (domingo, UTC).

    Returns:
        True se é domingo
    """
    now = datetime.now(timezone.utc)
    return now.weekday() == 6  # Sunday = 6


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown of PENELOPE service, including:
    - Service initialization
    - 7 Biblical Articles governance engines
    - Wisdom Base and observability clients
    - Service registry registration
    - Sabbath protocol activation
    - Graceful shutdown with prayer
    """
    global wisdom_base, observability_client, sophia_engine, praotes_validator
    global tapeinophrosyne_monitor, _heartbeat_task

    # ORAÇÃO DE INICIALIZAÇÃO
    logger.info("✝" * 50)
    logger.info("PENELOPE - Christian Autonomous Healing Service")
    logger.info("✝" * 50)
    logger.info("")
    logger.info("🙏 ORAÇÃO OPERACIONAL:")
    logger.info("")
    logger.info("Senhor, concede-me sabedoria para discernir quando agir,")
    logger.info("mansidão para intervir apenas o necessário,")
    logger.info("e humildade para reconhecer meus limites.")
    logger.info("")
    logger.info("Que eu seja mordoma fiel do código confiado a mim,")
    logger.info("servindo com amor aos desenvolvedores que criaram este sistema.")
    logger.info("")
    logger.info("Que eu observe o Sabbath como dia de reflexão,")
    logger.info("e que a verdade governe cada uma de minhas decisões.")
    logger.info("")
    logger.info("Não em minha força, mas sob Vossa orientação.")
    logger.info("Amém.")
    logger.info("")
    logger.info("✝" * 50)

    logger.info("🚀 Starting PENELOPE Service...")

    try:
        # Initialize Wisdom Base
        wisdom_base = WisdomBaseClient()
        logger.info("✅ Wisdom Base initialized")

        # Initialize Observability Client
        observability_client = ObservabilityClient(
            prometheus_url=os.getenv("PROMETHEUS_URL", "http://prometheus:9090"),
            loki_url=os.getenv("LOKI_URL", "http://loki:3100"),
        )
        logger.info("✅ Observability Client initialized")

        # Initialize 7 Biblical Articles Engines
        sophia_engine = SophiaEngine(wisdom_base, observability_client)
        logger.info("✅ Sophia Engine (Sabedoria) initialized")

        praotes_validator = PraotesValidator()
        logger.info("✅ Praotes Validator (Mansidão) initialized")

        tapeinophrosyne_monitor = TapeinophrosyneMonitor(wisdom_base)
        logger.info("✅ Tapeinophrosyne Monitor (Humildade) initialized")

        # Check Sabbath mode
        if is_sabbath():
            logger.info("🕊️ SABBATH MODE ACTIVE - No patches will be applied today")
            logger.info("   (Only observing and learning, respecting the day of rest)")
        else:
            logger.info("✅ Regular operation mode (weekday)")

        # Register with Service Registry
        try:
            _heartbeat_task = await auto_register_service(
                service_name="penelope",
                port=int(os.getenv("SERVICE_PORT", 8154)),
                health_endpoint="/health",
                metadata={
                    "category": "maximus_subordinate",
                    "type": "autonomous_healing",
                    "version": os.getenv("SERVICE_VERSION", "1.0.0"),
                    "governance": "7_biblical_articles",
                    "sabbath_mode": is_sabbath(),
                },
            )
            logger.info("✅ Registered with Vértice Service Registry")
        except Exception as e:
            logger.warning(f"⚠️ Failed to register with service registry: {e}")
            logger.warning("   Continuing without registry (standalone mode)")

        logger.info("✅ PENELOPE Service started successfully")
        logger.info("   Governed by: 7 Biblical Articles of Christian Governance")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start PENELOPE Service: {e}", exc_info=True)
        raise

    finally:
        # Shutdown sequence
        logger.info("👋 Shutting down PENELOPE Service...")

        # Cancel heartbeat task
        if _heartbeat_task:
            _heartbeat_task.cancel()
            try:
                await _heartbeat_task
            except asyncio.CancelledError:
                pass

        # Deregister from Service Registry
        try:
            await RegistryClient.deregister("penelope")
            logger.info("✅ Deregistered from Service Registry")
        except Exception as e:
            logger.warning(f"⚠️ Failed to deregister: {e}")

        logger.info("🙏 Thank you for allowing me to serve.")
        logger.info("🛑 PENELOPE Service shut down successfully")
        logger.info("✝ Soli Deo Gloria ✝")


# Create FastAPI application
app = FastAPI(
    title="PENELOPE - Christian Autonomous Healing Service",
    version=os.getenv("SERVICE_VERSION", "1.0.0"),
    description="Autonomous code healing service governed by 7 Biblical Articles",
    lifespan=lifespan,
)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include PENELOPE API routes
from api.routes import router as penelope_router

app.include_router(penelope_router)

# Include WebSocket routes
from websocket_routes import router as websocket_router

app.include_router(websocket_router)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Comprehensive health check endpoint.

    Checks:
    - PENELOPE core engines status
    - Wisdom Base connectivity
    - Observability clients connectivity
    - Sabbath mode status

    Returns:
        Dict with health status and component details
    """
    components_status = {}

    # Check Sophia Engine
    components_status["sophia_engine"] = "ok" if sophia_engine else "not_initialized"

    # Check Praotes Validator
    components_status["praotes_validator"] = (
        "ok" if praotes_validator else "not_initialized"
    )

    # Check Tapeinophrosyne Monitor
    components_status["tapeinophrosyne_monitor"] = (
        "ok" if tapeinophrosyne_monitor else "not_initialized"
    )

    # Check Wisdom Base
    components_status["wisdom_base"] = "ok" if wisdom_base else "not_initialized"

    # Check Observability
    components_status["observability_client"] = (
        "ok" if observability_client else "not_initialized"
    )

    # Overall status
    all_ok = all(status == "ok" for status in components_status.values())
    overall_status = "healthy" if all_ok else "degraded"

    return {
        "status": overall_status,
        "components": components_status,
        "virtues_status": {
            "sophia": components_status["sophia_engine"],
            "praotes": components_status["praotes_validator"],
            "tapeinophrosyne": components_status["tapeinophrosyne_monitor"],
        },
        "sabbath_mode": is_sabbath(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "PENELOPE - Christian Autonomous Healing Service",
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "status": "operational",
        "governance": "7_biblical_articles",
        "sabbath_mode": is_sabbath(),
        "description": "Autonomous code healing governed by Christian principles",
        "virtues": [
            "sophia (wisdom)",
            "praotes (meekness)",
            "tapeinophrosyne (humility)",
            "stewardship",
            "agape (love)",
            "sabbath (rest)",
            "aletheia (truth)",
        ],
        "endpoints": {"health": "/health", "api": "/api/v1", "docs": "/docs"},
    }


def main():
    """Main entry point for running PENELOPE service."""
    # Start Prometheus metrics server on separate port
    metrics_port = int(os.getenv("METRICS_PORT", 9090))
    try:
        start_http_server(metrics_port)
        logger.info(f"📈 Prometheus metrics server started on port {metrics_port}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start metrics server: {e}")

    # Run FastAPI application
    service_host = os.getenv("SERVICE_HOST", "0.0.0.0")
    service_port = int(os.getenv("SERVICE_PORT", 8154))
    workers = int(os.getenv("WORKER_PROCESSES", 1))

    uvicorn.run(
        app,
        host=service_host,
        port=service_port,
        workers=workers,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        timeout_keep_alive=75,
    )


if __name__ == "__main__":
    main()
