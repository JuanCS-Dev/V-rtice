"""
FastAPI Service Layer for Motor de Integridade Processual (MIP).

Provides REST API endpoints for ethical evaluation of action plans.

Endpoints:
- POST /evaluate: Evaluate an action plan
- GET /health: Health check
- GET /frameworks: List available frameworks
- GET /metrics: Get evaluation metrics

Autor: Juan Carlos de Souza
Lei Governante: Constituição Vértice v2.6
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import logging

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from motor_integridade_processual.models.action_plan import ActionPlan
from motor_integridade_processual.models.verdict import EthicalVerdict, FrameworkName, DecisionLevel, FrameworkVerdict
from motor_integridade_processual.frameworks.kantian import KantianDeontology
from motor_integridade_processual.frameworks.utilitarian import UtilitarianCalculus
from motor_integridade_processual.frameworks.virtue import VirtueEthics
from motor_integridade_processual.frameworks.principialism import Principialism
from motor_integridade_processual.resolution.conflict_resolver import ConflictResolver

# CBR Engine Integration
from justice.cbr_engine import CBREngine, CBRResult
from justice.precedent_database import PrecedentDB, CasePrecedent
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Motor de Integridade Processual (MIP)",
    description="Ethical evaluation engine for MAXIMUS AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize frameworks
frameworks = {
    FrameworkName.KANTIAN: KantianDeontology(),
    FrameworkName.UTILITARIAN: UtilitarianCalculus(),
    FrameworkName.VIRTUE_ETHICS: VirtueEthics(),
    FrameworkName.PRINCIPIALISM: Principialism(),
}

# Initialize resolver
resolver = ConflictResolver()

# Initialize CBR Engine for precedent-based reasoning
db_url = os.getenv("DATABASE_URL", "postgresql://maximus:password@localhost/maximus")
try:
    precedent_db = PrecedentDB(db_url)
    cbr_engine = CBREngine(precedent_db)
    logger.info("CBR Engine initialized with precedent database")
except Exception as e:
    logger.warning(f"CBR Engine initialization failed: {e}. Continuing without precedents.")
    cbr_engine = None

# Metrics storage (in-memory for now)
evaluation_count = 0
evaluation_times: List[float] = []
decision_counts: Dict[str, int] = {}


# Request/Response Models
class EvaluationRequest(BaseModel):
    """Request body for /evaluate endpoint."""
    action_plan: ActionPlan = Field(..., description="Action plan to evaluate")


class EvaluationResponse(BaseModel):
    """Response body for /evaluate endpoint."""
    verdict: EthicalVerdict = Field(..., description="Ethical verdict")
    evaluation_time_ms: float = Field(..., description="Time taken for evaluation (ms)")


class HealthResponse(BaseModel):
    """Response body for /health endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    frameworks_loaded: int = Field(..., description="Number of frameworks loaded")
    timestamp: str = Field(..., description="Current timestamp")


class FrameworkInfo(BaseModel):
    """Information about an ethical framework."""
    name: str = Field(..., description="Framework name")
    description: str = Field(..., description="Framework description")
    weight: float = Field(..., description="Framework weight in aggregation")
    can_veto: bool = Field(..., description="Framework can veto decisions")


class MetricsResponse(BaseModel):
    """Response body for /metrics endpoint."""
    total_evaluations: int = Field(..., description="Total evaluations performed")
    avg_evaluation_time_ms: float = Field(..., description="Average evaluation time")
    decision_breakdown: Dict[str, int] = Field(..., description="Count by decision type")


# Endpoints

@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "service": "Motor de Integridade Processual (MIP)",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns service status and basic information.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        frameworks_loaded=len(frameworks),
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/frameworks", response_model=List[FrameworkInfo])
async def list_frameworks() -> List[FrameworkInfo]:
    """
    List available ethical frameworks.
    
    Returns information about each framework including weights and capabilities.
    """
    framework_infos = []
    
    for name, framework in frameworks.items():
        framework_infos.append(
            FrameworkInfo(
                name=name.value,
                description=framework.__class__.__doc__ or "Ethical framework",
                weight=resolver.weights.get(name.value, 0.25),
                can_veto=name == FrameworkName.KANTIAN
            )
        )
    
    return framework_infos


@app.post("/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_200_OK)
async def evaluate_action_plan(request: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate an action plan against ethical frameworks with precedent-based reasoning.

    Process:
    1. Check CBR precedents (retrieve → reuse → revise)
       - If high confidence (>0.8), use precedent directly
       - Otherwise, fallback to frameworks
    2. Evaluate plan with each framework (if no precedent)
    3. Resolve conflicts between frameworks
    4. Generate unified verdict
    5. Store decision as new precedent (retain)
    6. Update metrics

    Args:
        request: EvaluationRequest with action_plan

    Returns:
        EvaluationResponse with verdict and timing

    Raises:
        HTTPException: If evaluation fails
    """
    global evaluation_count, evaluation_times, decision_counts
    
    start_time = time.time()
    
    try:
        logger.info(f"Evaluating action plan: {request.action_plan.objective}")

        # === PHASE 1: Try CBR (Precedent-Based Reasoning) ===
        cbr_result = None
        if cbr_engine is not None:
            try:
                # Convert action_plan to case dictionary
                case_dict = {
                    "objective": request.action_plan.objective,
                    "action_type": getattr(request.action_plan, "action_type", "unknown"),
                    "context": getattr(request.action_plan, "context", {}),
                    "target": getattr(request.action_plan, "target", None),
                }

                # Execute full CBR cycle (retrieve → reuse → revise)
                cbr_result = await cbr_engine.full_cycle(case_dict, validators=[])

                if cbr_result and cbr_result.confidence > 0.8:
                    logger.info(f"High-confidence precedent found (conf={cbr_result.confidence:.2f}), using directly")

                    # Create verdict from precedent
                    decision_map = {
                        "approve": DecisionLevel.APPROVE,
                        "approve_with_monitoring": DecisionLevel.APPROVE_WITH_MONITORING,
                        "escalate": DecisionLevel.ESCALATE_TO_HUMAN,
                        "reject": DecisionLevel.REJECT,
                    }
                    decision = decision_map.get(cbr_result.suggested_action, DecisionLevel.ESCALATE_TO_HUMAN)

                    # Build precedent-based verdict
                    final_verdict = EthicalVerdict(
                        final_decision=decision,
                        confidence_score=cbr_result.confidence,
                        reasoning=cbr_result.rationale,
                        framework_verdicts=[],
                        minority_opinions=[],
                        recommendations=[f"Based on precedent #{cbr_result.precedent_id}"],
                        processing_time_ms=0.0,
                    )

                elif cbr_result:
                    logger.info(f"Low-confidence precedent found (conf={cbr_result.confidence:.2f}), falling back to frameworks")
                else:
                    logger.info("No applicable precedent found, using frameworks")

            except Exception as e:
                logger.warning(f"CBR cycle failed: {e}, falling back to frameworks")
                cbr_result = None

        # === PHASE 2: Framework Evaluation (if no high-confidence precedent) ===
        if cbr_result is None or cbr_result.confidence <= 0.8:
            # Evaluate with each framework
            framework_verdicts = []
            for name, framework in frameworks.items():
                try:
                    verdict = framework.evaluate(request.action_plan)
                    framework_verdicts.append(verdict)
                    logger.debug(f"{name.value}: {verdict.decision.value} (score: {verdict.score})")
                except Exception as e:
                    logger.error(f"Framework {name.value} evaluation failed: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Framework evaluation failed: {str(e)}"
                    )

            # Resolve conflicts
            try:
                final_verdict = resolver.resolve(framework_verdicts, request.action_plan)
                logger.info(f"Final decision: {final_verdict.final_decision.value}")
            except Exception as e:
                logger.error(f"Conflict resolution failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Conflict resolution failed: {str(e)}"
                )
        
        # Calculate evaluation time
        elapsed_time = (time.time() - start_time) * 1000  # ms

        # Update metrics
        evaluation_count += 1
        evaluation_times.append(elapsed_time)
        decision_type = final_verdict.final_decision.value
        decision_counts[decision_type] = decision_counts.get(decision_type, 0) + 1

        # Update verdict processing time
        final_verdict.processing_time_ms = elapsed_time

        # === PHASE 3: Retain (Store as new precedent) ===
        if cbr_engine is not None:
            try:
                # Map DecisionLevel back to action string
                action_map = {
                    DecisionLevel.APPROVE: "approve",
                    DecisionLevel.APPROVE_WITH_MONITORING: "approve_with_monitoring",
                    DecisionLevel.ESCALATE_TO_HUMAN: "escalate",
                    DecisionLevel.REJECT: "reject",
                }
                action_taken = action_map.get(final_verdict.final_decision, "unknown")

                # Create precedent case
                new_precedent = CasePrecedent(
                    situation=case_dict if cbr_result else {
                        "objective": request.action_plan.objective,
                        "action_type": getattr(request.action_plan, "action_type", "unknown"),
                        "context": getattr(request.action_plan, "context", {}),
                    },
                    action_taken=action_taken,
                    rationale=final_verdict.reasoning,
                    outcome=None,  # Will be updated later with feedback
                    success=None,  # Will be updated with feedback (0.5 default)
                    ethical_frameworks=[fv.framework_name for fv in final_verdict.framework_verdicts],
                    constitutional_compliance={},  # Will be enhanced later
                    embedding=None,  # Will be generated by PrecedentDB
                )

                # Store precedent
                await cbr_engine.retain(new_precedent)
                logger.info(f"Decision stored as precedent (action={action_taken})")

            except Exception as e:
                logger.warning(f"Failed to store precedent: {e}")
                # Don't fail the request if precedent storage fails

        return EvaluationResponse(
            verdict=final_verdict,
            evaluation_time_ms=elapsed_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Get evaluation metrics.
    
    Returns statistics about evaluations performed.
    """
    avg_time = sum(evaluation_times) / len(evaluation_times) if evaluation_times else 0.0
    
    return MetricsResponse(
        total_evaluations=evaluation_count,
        avg_evaluation_time_ms=avg_time,
        decision_breakdown=decision_counts
    )


# Exception handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Startup/Shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info("=== MIP Service Starting ===")
    logger.info(f"Frameworks loaded: {len(frameworks)}")
    logger.info(f"Frameworks: {[f.value for f in frameworks.keys()]}")
    logger.info(f"CBR Engine: {'✓ Active' if cbr_engine else '✗ Disabled'}")
    logger.info("=== MIP Service Ready ===")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("=== MIP Service Shutting Down ===")
    logger.info(f"Total evaluations performed: {evaluation_count}")
    logger.info("=== MIP Service Stopped ===")
