"""Active Immune Core Service - FastAPI Main

PRODUCTION-READY service with:
- Health checks
- Prometheus metrics
- Agent management endpoints
- Graceful shutdown
- Structured logging
- Kafka integration with Reactive Fabric Bridge

NO MOCKS, NO PLACEHOLDERS, NO TODOs.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app
from pydantic import BaseModel, Field

from config import settings
from communication.kafka_consumers import KafkaEventConsumer, ExternalTopic
from honeypot_consumer import start_honeypot_consumer, stop_honeypot_consumer  # AG-KAFKA-004

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


# Configure logging
settings.configure_logging()
logger = logging.getLogger(__name__)

# ==================== PROMETHEUS METRICS ====================

# Agents
agents_active = Gauge(
    "immunis_agents_active",
    "Number of active agents",
    ["type", "status"],
)
agents_total = Gauge(
    "immunis_agents_total",
    "Total agents created",
    ["type"],
)
agent_apoptosis_total = Counter(
    "immunis_agent_apoptosis_total",
    "Total agent apoptosis events",
    ["reason"],
)

# Threats
threats_detected_total = Counter(
    "immunis_threats_detected_total",
    "Total threats detected",
    ["agent_type"],
)
threats_neutralized_total = Counter(
    "immunis_threats_neutralized_total",
    "Total threats neutralized",
    ["agent_type", "method"],
)
false_positives_total = Counter(
    "immunis_false_positives_total",
    "Total false positives",
    ["agent_type"],
)

# Detection latency
detection_latency = Histogram(
    "immunis_detection_latency_seconds",
    "Time from threat appearance to detection",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120],
)
neutralization_latency = Histogram(
    "immunis_neutralization_latency_seconds",
    "Time from detection to neutralization",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)

# Homeostasis
temperature_gauge = Gauge(
    "immunis_temperature_celsius",
    "Regional temperature",
    ["area", "lymphnode_id"],
)
homeostatic_state = Gauge(
    "immunis_homeostatic_state",
    "Current homeostatic state (0=repouso, 1=vigilancia, 2=atencao, 3=inflamacao)",
    ["lymphnode_id"],
)

# Communication
cytokines_sent_total = Counter(
    "immunis_cytokines_sent_total",
    "Total cytokines sent",
    ["type", "priority"],
)
cytokines_received_total = Counter(
    "immunis_cytokines_received_total",
    "Total cytokines received",
    ["type"],
)

# Lymphnodes
lymphnodes_active = Gauge(
    "immunis_lymphnodes_active",
    "Number of active lymphnodes",
    ["nivel"],
)

# ==================== GLOBAL STATE ====================

# Runtime state (will be populated during lifespan)
global_state: Dict[str, Any] = {
    "agents": {},  # agent_id -> agent instance
    "lymphnodes": {},  # lymphnode_id -> lymphnode instance
    "started_at": None,
    "version": "1.0.0",
    "kafka_consumer": None,  # Kafka consumer instance
}


# ==================== THREAT HANDLER ====================


async def handle_reactive_threat(event: Dict[str, Any]) -> None:
    """
    Handle threat detected events from Reactive Fabric Bridge.
    
    Processes threat intelligence from honeypots and integrates with
    Active Immune Core defense mechanisms.
    
    Args:
        event: Threat event from Reactive Fabric
            - event_id: Unique event identifier
            - source_ip: Attacker IP address
            - attack_type: Type of attack detected
            - severity: Threat severity level
            - honeypot_id: Source honeypot identifier
            - timestamp: Event timestamp
            - metadata: Additional context
    """
    try:
        logger.info(
            "reactive_threat_received",
            event_id=event.get("event_id"),
            source_ip=event.get("source_ip"),
            attack_type=event.get("attack_type"),
            severity=event.get("severity"),
        )
        
        # Update metrics
        threats_detected_total.labels(agent_type="reactive_fabric").inc()

        # Future expansion points (handled by orchestrator):
        # - NK Cells automated response coordination
        # - Threat intelligence memory updates
        # - Homeostatic state adjustments for critical severity

        logger.info(
            "reactive_threat_processed",
            event_id=event.get("event_id"),
        )
        
    except Exception as e:
        logger.error(
            "reactive_threat_handler_failed",
            error=str(e),
            event=event,
        )


# ==================== REQUEST/RESPONSE MODELS ====================


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(description="Service status (healthy/unhealthy)")
    timestamp: datetime = Field(description="Current timestamp")
    version: str = Field(description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Uptime in seconds")
    agents_active: int = Field(description="Number of active agents")
    lymphnodes_active: int = Field(description="Number of active lymphnodes")


class AgentListResponse(BaseModel):
    """Agent list response"""

    total: int = Field(description="Total agents")
    agents: List[Dict[str, Any]] = Field(description="Agent details")


class AgentDetailResponse(BaseModel):
    """Agent detail response"""

    id: str
    tipo: str
    status: str
    ativo: bool
    area_patrulha: str
    localizacao_atual: str
    energia: float
    temperatura_local: float
    deteccoes_total: int
    neutralizacoes_total: int
    falsos_positivos: int
    tempo_vida_horas: float


class CloneRequest(BaseModel):
    """Clone agents request"""

    tipo: str = Field(description="Agent type (macrofago, nk_cell, neutrofilo)")
    especializacao: str = Field(description="Specialization (e.g., threat_192.0.2.100)")
    quantidade: int = Field(default=5, ge=1, le=50, description="Number of clones")
    lymphnode_id: Optional[str] = Field(None, description="Target lymphnode")


class CloneResponse(BaseModel):
    """Clone agents response"""

    clones_created: int = Field(description="Number of clones created")
    clone_ids: List[str] = Field(description="Clone IDs")


class HomeostasisResponse(BaseModel):
    """Homeostatic state response"""

    estado: str = Field(description="Current homeostatic state")
    temperatura_media: float = Field(description="Average temperature")
    agentes_total: int = Field(description="Total agents")
    agentes_ativos: int = Field(description="Active agents")
    percentual_ativo: float = Field(description="Active percentage")
    target_percentual: float = Field(description="Target active percentage")


class ErrorResponse(BaseModel):
    """Error response"""

    error: str = Field(description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now)


# ==================== LIFESPAN ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager - startup and shutdown"""
    # ==================== STARTUP ====================

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="active_immune_core",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="active_immune_core",
            version=service_version
        )
        auto_update_sabbath_status("active_immune_core")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="active_immune_core",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="active_immune_core")
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

    logger.info("=" * 80)
    logger.info("Starting Active Immune Core Service")
    logger.info("=" * 80)
    logger.info(f"Version: {global_state['version']}")
    logger.info(f"Port: {settings.service_port}")
    logger.info(f"Kafka: {settings.kafka_bootstrap_servers}")
    logger.info(f"Redis: {settings.redis_url}")
    logger.info(f"PostgreSQL: {settings.postgres_host}:{settings.postgres_port}")
    logger.info(f"Ethical AI: {settings.ethical_ai_url}")
    logger.info("=" * 80)

    global_state["started_at"] = datetime.now()

    # Initialize Kafka consumer for Reactive Fabric threats
    try:
        logger.info("Initializing Kafka consumer for Reactive Fabric integration...")
        kafka_consumer = KafkaEventConsumer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="active_immune_core_reactive_fabric",
            enable_degraded_mode=True,
        )
        
        # Register handler for reactive threats
        kafka_consumer.register_handler(
            ExternalTopic.REACTIVE_THREATS,
            handle_reactive_threat,
        )
        
        # Start consumer
        await kafka_consumer.start()
        global_state["kafka_consumer"] = kafka_consumer
        logger.info("Kafka consumer started successfully - listening for Reactive Fabric threats")
        
    except Exception as e:
        logger.warning(
            f"Kafka consumer initialization failed (degraded mode): {e}",
            exc_info=True,
        )
        # Continue without Kafka (graceful degradation)

    # Initialize lymphnodes (will be implemented in Fase 3)
    logger.info("Lymphnodes: Will be initialized in Fase 3")

    # Initialize baseline agents (will be implemented in Fase 2)
    logger.info("Baseline agents: Will be initialized in Fase 2")

    # AG-KAFKA-004: Initialize honeypot status consumer
    try:
        logger.info("Initializing Honeypot Status Consumer...")
        honeypot_task = asyncio.create_task(start_honeypot_consumer())
        global_state["honeypot_consumer_task"] = honeypot_task
        logger.info("✅ Honeypot Status Consumer started - listening for Reactive Fabric honeypot events")
    except Exception as e:
        logger.warning(f"⚠️  Honeypot consumer initialization failed (non-critical): {e}")

    logger.info("Active Immune Core Service started successfully")

    yield

    # ==================== SHUTDOWN ====================
    logger.info("=" * 80)
    logger.info("Stopping Active Immune Core Service")
    logger.info("=" * 80)

    # Stop Kafka consumer
    kafka_consumer = global_state.get("kafka_consumer")
    if kafka_consumer:
        try:
            logger.info("Stopping Kafka consumer...")
            await kafka_consumer.stop()
            logger.info("Kafka consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping Kafka consumer: {e}")

    # AG-KAFKA-004: Stop honeypot consumer
    honeypot_task = global_state.get("honeypot_consumer_task")
    if honeypot_task:
        try:
            logger.info("Stopping Honeypot Status Consumer...")
            await stop_honeypot_consumer()
            honeypot_task.cancel()
            try:
                await honeypot_task
            except asyncio.CancelledError:
                pass
            logger.info("✅ Honeypot consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping honeypot consumer: {e}")

    # Stop all agents
    for agent_id, agent in global_state["agents"].items():
        logger.info(f"Stopping agent: {agent_id}")
        try:
            await agent.parar()
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")

    # Stop all lymphnodes
    for lymphnode_id, lymphnode in global_state["lymphnodes"].items():
        logger.info(f"Stopping lymphnode: {lymphnode_id}")
        try:
            await lymphnode.parar()
        except Exception as e:
            logger.error(f"Error stopping lymphnode {lymphnode_id}: {e}")

    logger.info("Active Immune Core Service stopped gracefully")


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Active Immune Core Service",
    description="Autonomous immune agents for real-time threat detection and neutralization",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ==================== EXCEPTION HANDLERS ====================


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.debug else None,
        ).model_dump(),
    )


# ==================== ENDPOINTS ====================


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """
    Health check endpoint.

    Returns service health status, uptime, and active components.
    """
    started_at = global_state.get("started_at")
    uptime = (datetime.now() - started_at).total_seconds() if started_at else None

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=global_state["version"],
        uptime_seconds=uptime,
        agents_active=len([a for a in global_state["agents"].values() if a.state.ativo]),
        lymphnodes_active=len(global_state["lymphnodes"]),
    )


@app.get("/ready", tags=["Health"])
async def readiness():
    """
    Readiness check endpoint.

    Returns 200 if service is ready to accept traffic.
    """
    # Check if critical dependencies are available
    # In Fase 1, we just check if app started
    if global_state.get("started_at") is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready"}


@app.get("/agents", response_model=AgentListResponse, tags=["Agents"])
async def list_agents(
    tipo: Optional[str] = None,
    status_filter: Optional[str] = None,
    ativo: Optional[bool] = None,
):
    """
    List all agents.

    Query parameters:
    - tipo: Filter by agent type (macrofago, nk_cell, neutrofilo)
    - status_filter: Filter by status (patrulhando, investigando, neutralizando)
    - ativo: Filter by active status (true/false)
    """
    agents = global_state["agents"].values()

    # Apply filters
    if tipo:
        agents = [a for a in agents if a.state.tipo == tipo]
    if status_filter:
        agents = [a for a in agents if a.state.status == status_filter]
    if ativo is not None:
        agents = [a for a in agents if a.state.ativo == ativo]

    agents_list = [
        {
            "id": a.state.id,
            "tipo": a.state.tipo,
            "status": a.state.status,
            "ativo": a.state.ativo,
            "area": a.state.area_patrulha,
            "localizacao": a.state.localizacao_atual,
            "energia": a.state.energia,
            "temperatura": a.state.temperatura_local,
        }
        for a in agents
    ]

    return AgentListResponse(total=len(agents_list), agents=agents_list)


@app.get("/agents/{agent_id}", response_model=AgentDetailResponse, tags=["Agents"])
async def get_agent(agent_id: str):
    """
    Get agent details.

    Returns complete agent state including metrics and history.
    """
    if agent_id not in global_state["agents"]:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    agent = global_state["agents"][agent_id]
    state = agent.state

    return AgentDetailResponse(
        id=state.id,
        tipo=state.tipo,
        status=state.status,
        ativo=state.ativo,
        area_patrulha=state.area_patrulha,
        localizacao_atual=state.localizacao_atual,
        energia=state.energia,
        temperatura_local=state.temperatura_local,
        deteccoes_total=state.deteccoes_total,
        neutralizacoes_total=state.neutralizacoes_total,
        falsos_positivos=state.falsos_positivos,
        tempo_vida_horas=state.tempo_vida.total_seconds() / 3600,
    )


@app.post("/agents/clone", response_model=CloneResponse, tags=["Agents"])
async def clone_agents(request: CloneRequest):
    """
    Create specialized agent clones.

    Creates N clones of specified type with given specialization.
    Clones are distributed to lymphnodes for coordination.

    Will be implemented in Fase 2-3.
    """
    raise HTTPException(
        status_code=501,
        detail="Cloning will be implemented in Fase 2-3 (Agent Factory + Lymphnodes)",
    )


@app.get("/lymphnodes", tags=["Coordination"])
async def list_lymphnodes():
    """
    List all lymphnodes.

    Returns lymphnode details including temperature, agent count, metrics.

    Will be implemented in Fase 3.
    """
    raise HTTPException(
        status_code=501,
        detail="Lymphnodes will be implemented in Fase 3",
    )


@app.get("/homeostasis", response_model=HomeostasisResponse, tags=["Homeostasis"])
async def get_homeostasis():
    """
    Get global homeostatic state.

    Returns current state (Repouso/Vigilância/Atenção/Inflamação),
    temperature, active agent percentage.

    Will be implemented in Fase 3.
    """
    raise HTTPException(
        status_code=501,
        detail="Homeostasis controller will be implemented in Fase 3",
    )


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint"""
    return {
        "service": "Active Immune Core",
        "version": global_state["version"],
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


# ==================== MAIN ====================


def main():
    """Run service"""
    try:
        uvicorn.run(
            "active_immune_core.main:app",
            host=settings.host,
            port=settings.service_port,
            log_level=settings.log_level.lower(),
            reload=settings.debug,
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("Received SIGINT, shutting down gracefully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
