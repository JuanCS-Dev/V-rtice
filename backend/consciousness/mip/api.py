"""
MIP FastAPI Application

REST API para Motor de Integridade Processual.
Endpoints para avaliação ética, audit trail, e gestão de princípios.

Autor: Juan Carlos de Souza
Lei Governante: Constituição Vértice v2.6
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import get_settings
from .core import ProcessIntegrityEngine
from .models import (
    ActionPlan,
    ActionStep,
    EthicalVerdict,
    VerdictStatus,
    Stakeholder,
    ActionCategory,
    Effect,
    Precondition,
)
from .infrastructure.knowledge_base import (
    KnowledgeBaseRepository,
    PrincipleQueryService,
    AuditTrailService,
)
from .infrastructure.knowledge_models import (
    Principle,
    Decision,
    PrincipleLevel,
    DecisionStatus,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class EvaluateRequest(BaseModel):
    """Request para avaliar um ActionPlan."""
    plan: ActionPlan
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan": {
                    "name": "DDoS Protection",
                    "description": "Block malicious traffic",
                    "category": "defensive",
                    "steps": [{
                        "sequence_number": 1,
                        "description": "Block source IPs",
                        "action_type": "defensive",
                        "respects_autonomy": True,
                        "treats_as_means_only": False
                    }],
                    "stakeholders": [{
                        "id": "users",
                        "type": "human_group",
                        "description": "Protected users",
                        "impact_magnitude": 0.9,
                        "autonomy_respected": True,
                        "vulnerability_level": 0.5
                    }],
                    "urgency": 0.8,
                    "risk_level": 0.2
                }
            }
        }


class EvaluateResponse(BaseModel):
    """Response da avaliação ética."""
    verdict: EthicalVerdict
    evaluation_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "verdict": {
                    "status": "approved",
                    "aggregate_score": 0.85,
                    "confidence": 0.90,
                    "summary": "Plan approved"
                },
                "evaluation_time_ms": 0.5
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str
    version: str
    neo4j_connected: bool
    engine_initialized: bool


class PrincipleResponse(BaseModel):
    """Response com princípio ético."""
    id: str
    name: str
    level: str
    description: str
    severity: int
    philosophical_foundation: str


class DecisionResponse(BaseModel):
    """Response com decisão do audit trail."""
    id: str
    action_plan_name: str
    status: str
    aggregate_score: Optional[float]
    confidence: float
    summary: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Resposta de erro padronizada."""
    error: str
    detail: str
    status_code: int


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia lifecycle da aplicação.
    
    Startup: Inicializa engine e knowledge base.
    Shutdown: Fecha conexões.
    """
    logger.info(f"🚀 Starting {settings.service_name} v{settings.service_version}")
    
    # Initialize engine
    app.state.engine = ProcessIntegrityEngine()
    logger.info("✅ MIP Engine initialized")
    
    # Initialize knowledge base
    app.state.kb_repo = KnowledgeBaseRepository(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
    )
    
    try:
        await app.state.kb_repo.initialize()
        app.state.kb_connected = True
        logger.info("✅ Knowledge Base connected")
    except Exception as e:
        logger.warning(f"⚠️  Knowledge Base unavailable: {e}")
        logger.warning("⚠️  Operating in degraded mode (no persistence)")
        app.state.kb_connected = False
    
    # Initialize services
    if app.state.kb_connected:
        app.state.principle_service = PrincipleQueryService(app.state.kb_repo)
        app.state.audit_service = AuditTrailService(app.state.kb_repo)
        logger.info("✅ Services initialized")
    
    logger.info(f"🎯 MIP API ready at http://{settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down MIP API")
    if app.state.kb_connected:
        await app.state.kb_repo.close()
        logger.info("✅ Knowledge Base closed")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.service_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler para HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "detail": str(exc),
            "status_code": exc.status_code,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handler para exceções gerais."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500,
        }
    )


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Verifica status do serviço, engine e knowledge base.
    """
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.service_version,
        neo4j_connected=app.state.kb_connected,
        engine_initialized=app.state.engine is not None,
    )


@app.post(
    "/evaluate",
    response_model=EvaluateResponse,
    status_code=status.HTTP_200_OK,
    tags=["Evaluation"],
    summary="Avaliar plano de ação",
    description="Avalia um ActionPlan contra frameworks éticos e retorna EthicalVerdict.",
)
async def evaluate_plan(request: EvaluateRequest):
    """
    Avalia um plano de ação.
    
    Executa validação ética multi-framework e retorna veredicto vinculante.
    Se Knowledge Base disponível, persiste decisão automaticamente.
    
    Args:
        request: EvaluateRequest com ActionPlan
        
    Returns:
        EvaluateResponse com verdict e timing
        
    Raises:
        HTTPException 400: Se plan inválido
        HTTPException 500: Se erro interno
    """
    try:
        start_time = time.time()
        
        # Validate plan
        plan = request.plan
        
        # Evaluate
        engine: ProcessIntegrityEngine = app.state.engine
        verdict = engine.evaluate(plan)
        
        # Persist if KB available
        if app.state.kb_connected:
            try:
                decision = Decision(
                    action_plan_id=plan.id,
                    action_plan_name=plan.name,
                    status=DecisionStatus(verdict.status.value),
                    aggregate_score=verdict.aggregate_score,
                    confidence=verdict.confidence,
                    kantian_score=verdict.kantian_score.score if verdict.kantian_score else None,
                    utilitarian_score=verdict.utilitarian_score.score if verdict.utilitarian_score else None,
                    virtue_score=verdict.virtue_score.score if verdict.virtue_score else None,
                    principialism_score=verdict.principialism_score.score if verdict.principialism_score else None,
                    summary=verdict.summary,
                    detailed_reasoning=verdict.detailed_reasoning,
                    conflicts_detected=verdict.conflicts_detected or [],
                    requires_human_review=verdict.requires_human_review,
                    urgency=plan.urgency,
                    risk_level=plan.risk_level,
                    evaluation_duration_ms=(time.time() - start_time) * 1000,
                )
                
                audit_service: AuditTrailService = app.state.audit_service
                await audit_service.log_decision(decision)
                logger.info(f"✅ Decision persisted: {plan.name}")
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to persist decision: {e}")
        
        evaluation_time = (time.time() - start_time) * 1000
        
        return EvaluateResponse(
            verdict=verdict,
            evaluation_time_ms=evaluation_time,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.get(
    "/principles",
    response_model=List[PrincipleResponse],
    tags=["Principles"],
    summary="Listar princípios éticos",
    description="Retorna todos os princípios da Constituição Vértice.",
)
async def list_principles(level: Optional[PrincipleLevel] = None):
    """
    Lista princípios éticos.
    
    Args:
        level: Filtrar por PrincipleLevel (opcional)
        
    Returns:
        Lista de princípios
        
    Raises:
        HTTPException 503: Se Knowledge Base indisponível
    """
    if not app.state.kb_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge Base unavailable"
        )
    
    try:
        repo: KnowledgeBaseRepository = app.state.kb_repo
        principles = await repo.list_principles(level)
        
        return [
            PrincipleResponse(
                id=str(p.id),
                name=p.name,
                level=p.level.value,
                description=p.description,
                severity=p.severity,
                philosophical_foundation=p.philosophical_foundation,
            )
            for p in principles
        ]
        
    except Exception as e:
        logger.error(f"Error listing principles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list principles: {str(e)}"
        )


@app.get(
    "/principles/{principle_id}",
    response_model=PrincipleResponse,
    tags=["Principles"],
    summary="Buscar princípio por ID",
)
async def get_principle(principle_id: UUID):
    """
    Busca princípio por ID.
    
    Args:
        principle_id: UUID do princípio
        
    Returns:
        Principle ou 404
    """
    if not app.state.kb_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge Base unavailable"
        )
    
    try:
        repo: KnowledgeBaseRepository = app.state.kb_repo
        principle = await repo.get_principle(principle_id)
        
        if not principle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Principle {principle_id} not found"
            )
        
        return PrincipleResponse(
            id=str(principle.id),
            name=principle.name,
            level=principle.level.value,
            description=principle.description,
            severity=principle.severity,
            philosophical_foundation=principle.philosophical_foundation,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting principle: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get principle: {str(e)}"
        )


@app.get(
    "/decisions/{decision_id}",
    response_model=DecisionResponse,
    tags=["Audit Trail"],
    summary="Buscar decisão por ID",
)
async def get_decision(decision_id: UUID):
    """
    Busca decisão do audit trail.
    
    Args:
        decision_id: UUID da decisão
        
    Returns:
        Decision ou 404
    """
    if not app.state.kb_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge Base unavailable"
        )
    
    try:
        repo: KnowledgeBaseRepository = app.state.kb_repo
        decision = await repo.get_decision(decision_id)
        
        if not decision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Decision {decision_id} not found"
            )
        
        return DecisionResponse(
            id=str(decision.id),
            action_plan_name=decision.action_plan_name,
            status=decision.status.value,
            aggregate_score=decision.aggregate_score,
            confidence=decision.confidence,
            summary=decision.summary,
            timestamp=decision.timestamp.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting decision: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get decision: {str(e)}"
        )


@app.get(
    "/audit-trail",
    response_model=List[DecisionResponse],
    tags=["Audit Trail"],
    summary="Listar audit trail",
    description="Retorna histórico de decisões éticas.",
)
async def get_audit_trail(
    limit: int = 100,
    offset: int = 0,
):
    """
    Lista audit trail.
    
    Args:
        limit: Máximo de resultados
        offset: Offset para paginação
        
    Returns:
        Lista de decisões
    """
    if not app.state.kb_connected:
        # Fallback para in-memory audit trail
        engine: ProcessIntegrityEngine = app.state.engine
        decisions = engine.get_audit_trail()
        
        # Convert in-memory entries to response
        return [
            DecisionResponse(
                id=str(entry.verdict.plan_id),
                action_plan_name=f"Plan {entry.verdict.plan_id}",
                status=entry.verdict.status.value,
                aggregate_score=entry.verdict.aggregate_score,
                confidence=entry.verdict.confidence,
                summary=entry.verdict.summary,
                timestamp=entry.timestamp.isoformat(),
            )
            for entry in decisions[offset:offset+limit]
        ]
    
    # TODO: Implement paginated query from Neo4j
    return []


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=True,
    )
