"""
FastAPI Service Layer for Motor de Integridade Processual (MIP).

Provides REST API endpoints for ethical evaluation of action plans.

Endpoints:
- POST /evaluate: Evaluate an action plan (with CBR precedent support)
- POST /evaluate/ab-test: A/B test CBR vs Frameworks
- GET /health: Health check
- GET /frameworks: List available frameworks
- GET /metrics: Get evaluation metrics
- POST /precedents/feedback: Update precedent with outcome feedback
- GET /precedents/{id}: Retrieve specific precedent
- GET /precedents/metrics: Get CBR precedent metrics
- GET /ab-test/metrics: Get A/B testing comparison metrics

Features:
- Case-Based Reasoning (CBR) with precedent database
- Constitutional validation (Lei I, Lei Zero, Lei II)
- Risk level validation
- Feedback loop for precedent improvement
- A/B testing framework for CBR vs traditional frameworks

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
from motor_integridade_processual.models.verdict import EthicalVerdict, FrameworkName, DecisionLevel
from motor_integridade_processual.frameworks.kantian import KantianDeontology
from motor_integridade_processual.frameworks.utilitarian import UtilitarianCalculus
from motor_integridade_processual.frameworks.virtue import VirtueEthics
from motor_integridade_processual.frameworks.principialism import Principialism
from motor_integridade_processual.resolution.conflict_resolver import ConflictResolver

# CBR Engine Integration
from justice.cbr_engine import CBREngine
from justice.precedent_database import PrecedentDB, CasePrecedent
from justice.validators import create_default_validators
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
    cbr_validators = create_default_validators()
    logger.info("CBR Engine initialized with precedent database + validators")
except Exception as e:
    logger.warning(f"CBR Engine initialization failed: {e}. Continuing without precedents.")
    cbr_engine = None
    cbr_validators = []

# Metrics storage (in-memory for now)
evaluation_count = 0
evaluation_times: List[float] = []
decision_counts: Dict[str, int] = {}

# CBR Metrics
cbr_precedents_used_count = 0
cbr_shortcut_count = 0

# A/B Testing Mode (set via environment variable)
AB_TESTING_ENABLED = os.getenv("MIP_AB_TESTING", "false").lower() == "true"
ab_test_results: List[Dict[str, Any]] = []  # Stores A/B test comparisons


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


class PrecedentFeedbackRequest(BaseModel):
    """Request body for /precedents/feedback endpoint."""
    precedent_id: int = Field(..., description="ID of the precedent to update")
    success_score: float = Field(..., ge=0.0, le=1.0, description="Success score (0.0-1.0)")
    outcome: Optional[Dict[str, Any]] = Field(None, description="Outcome details")


class PrecedentResponse(BaseModel):
    """Response body for precedent endpoints."""
    id: int = Field(..., description="Precedent ID")
    situation: Dict[str, Any] = Field(..., description="Situation that triggered decision")
    action_taken: str = Field(..., description="Action that was taken")
    rationale: str = Field(..., description="Rationale for the decision")
    success: Optional[float] = Field(None, description="Success score (0.0-1.0)")
    created_at: str = Field(..., description="Creation timestamp")


class PrecedentMetricsResponse(BaseModel):
    """Response body for /precedents/metrics endpoint."""
    total_precedents: int = Field(..., description="Total precedents stored")
    avg_success_score: float = Field(..., description="Average success score")
    high_confidence_count: int = Field(..., description="Count of high-confidence precedents (>0.8)")
    precedents_used_count: int = Field(..., description="Number of times precedents were used")
    shortcut_rate: float = Field(..., description="Percentage of evaluations using CBR shortcut")


class ABTestResult(BaseModel):
    """Single A/B test comparison result."""
    objective: str = Field(..., description="Action plan objective")
    cbr_decision: Optional[str] = Field(None, description="CBR decision")
    cbr_confidence: Optional[float] = Field(None, description="CBR confidence")
    framework_decision: str = Field(..., description="Framework decision")
    framework_confidence: float = Field(..., description="Framework confidence")
    decisions_match: bool = Field(..., description="Whether both methods agreed")
    timestamp: str = Field(..., description="Test timestamp")


class ABTestMetricsResponse(BaseModel):
    """Response body for A/B test metrics."""
    total_comparisons: int = Field(..., description="Total A/B tests performed")
    agreement_rate: float = Field(..., description="Percentage where CBR and frameworks agreed")
    cbr_avg_confidence: float = Field(..., description="Average CBR confidence when used")
    framework_avg_confidence: float = Field(..., description="Average framework confidence")
    cbr_faster_percentage: float = Field(..., description="Percentage where CBR was faster")
    recent_results: List[ABTestResult] = Field(..., description="Most recent A/B test results (last 10)")


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
    global evaluation_count, evaluation_times, decision_counts, cbr_precedents_used_count, cbr_shortcut_count

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

                # Execute full CBR cycle (retrieve → reuse → revise with validators)
                cbr_result = await cbr_engine.full_cycle(case_dict, validators=cbr_validators)

                if cbr_result and cbr_result.confidence > 0.8:
                    logger.info(f"High-confidence precedent found (conf={cbr_result.confidence:.2f}), using directly")

                    # Update CBR metrics
                    cbr_precedents_used_count += 1
                    cbr_shortcut_count += 1

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
                    cbr_precedents_used_count += 1  # Still used for reference
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


@app.post("/precedents/feedback", status_code=status.HTTP_200_OK)
async def update_precedent_feedback(request: PrecedentFeedbackRequest) -> Dict[str, str]:
    """
    Update precedent with outcome feedback.

    Allows humans/systems to provide feedback on how well a precedent-based
    decision worked out, improving future CBR recommendations.

    Args:
        request: PrecedentFeedbackRequest with precedent_id and success_score

    Returns:
        Success message

    Raises:
        HTTPException: If CBR disabled or precedent not found
    """
    if cbr_engine is None or precedent_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CBR Engine not available"
        )

    try:
        # Update success score
        updated = await precedent_db.update_success(
            request.precedent_id,
            request.success_score
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Precedent {request.precedent_id} not found"
            )

        # Update outcome if provided
        if request.outcome:
            precedent = await precedent_db.get_by_id(request.precedent_id)
            if precedent:
                precedent.outcome = request.outcome
                await precedent_db.store(precedent)

        logger.info(f"Updated precedent #{request.precedent_id} with success={request.success_score}")

        return {
            "status": "success",
            "message": f"Precedent #{request.precedent_id} updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update precedent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update precedent: {str(e)}"
        )


@app.get("/precedents/{precedent_id}", response_model=PrecedentResponse)
async def get_precedent(precedent_id: int) -> PrecedentResponse:
    """
    Retrieve a specific precedent by ID.

    Args:
        precedent_id: ID of the precedent to retrieve

    Returns:
        PrecedentResponse with precedent details

    Raises:
        HTTPException: If CBR disabled or precedent not found
    """
    if cbr_engine is None or precedent_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CBR Engine not available"
        )

    try:
        precedent = await precedent_db.get_by_id(precedent_id)

        if not precedent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Precedent {precedent_id} not found"
            )

        return PrecedentResponse(
            id=precedent.id,
            situation=precedent.situation,
            action_taken=precedent.action_taken,
            rationale=precedent.rationale,
            success=precedent.success,
            created_at=precedent.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve precedent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve precedent: {str(e)}"
        )


@app.post("/evaluate/ab-test", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def evaluate_ab_test(request: EvaluationRequest) -> Dict[str, Any]:
    """
    A/B test: Compare CBR vs Frameworks for same action plan.

    Evaluates the action plan using BOTH CBR (if available) and frameworks,
    then compares the results. Useful for validating CBR performance.

    Args:
        request: EvaluationRequest with action_plan

    Returns:
        Dict with both CBR and framework results + comparison

    Raises:
        HTTPException: If evaluation fails
    """
    global ab_test_results

    start_time = time.time()

    # === Run CBR evaluation ===
    cbr_decision = None
    cbr_confidence = None
    cbr_time_ms = 0.0

    if cbr_engine is not None:
        cbr_start = time.time()
        try:
            case_dict = {
                "objective": request.action_plan.objective,
                "action_type": getattr(request.action_plan, "action_type", "unknown"),
                "context": getattr(request.action_plan, "context", {}),
            }

            cbr_result = await cbr_engine.full_cycle(case_dict, validators=cbr_validators)

            if cbr_result:
                action_map = {
                    "approve": DecisionLevel.APPROVE,
                    "approve_with_monitoring": DecisionLevel.APPROVE_WITH_MONITORING,
                    "escalate": DecisionLevel.ESCALATE_TO_HUMAN,
                    "reject": DecisionLevel.REJECT,
                }
                cbr_decision = action_map.get(cbr_result.suggested_action, DecisionLevel.ESCALATE_TO_HUMAN).value
                cbr_confidence = cbr_result.confidence

        except Exception as e:
            logger.warning(f"CBR evaluation failed in A/B test: {e}")

        cbr_time_ms = (time.time() - cbr_start) * 1000

    # === Run Framework evaluation ===
    framework_start = time.time()

    framework_verdicts = []
    for name, framework in frameworks.items():
        try:
            verdict = framework.evaluate(request.action_plan)
            framework_verdicts.append(verdict)
        except Exception as e:
            logger.error(f"Framework {name.value} failed in A/B test: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Framework evaluation failed: {str(e)}"
            )

    framework_verdict = resolver.resolve(framework_verdicts, request.action_plan)
    framework_time_ms = (time.time() - framework_start) * 1000

    # === Compare results ===
    decisions_match = cbr_decision == framework_verdict.final_decision.value if cbr_decision else False

    ab_result = ABTestResult(
        objective=request.action_plan.objective,
        cbr_decision=cbr_decision,
        cbr_confidence=cbr_confidence,
        framework_decision=framework_verdict.final_decision.value,
        framework_confidence=framework_verdict.confidence_score,
        decisions_match=decisions_match,
        timestamp=datetime.utcnow().isoformat()
    )

    # Store result (keep last 100)
    ab_test_results.append(ab_result.dict())
    if len(ab_test_results) > 100:
        ab_test_results.pop(0)

    total_time_ms = (time.time() - start_time) * 1000

    return {
        "cbr": {
            "decision": cbr_decision,
            "confidence": cbr_confidence,
            "time_ms": cbr_time_ms,
            "used": cbr_decision is not None,
        },
        "frameworks": {
            "decision": framework_verdict.final_decision.value,
            "confidence": framework_verdict.confidence_score,
            "time_ms": framework_time_ms,
        },
        "comparison": {
            "decisions_match": decisions_match,
            "cbr_faster": cbr_time_ms < framework_time_ms if cbr_decision else False,
            "time_savings_ms": framework_time_ms - cbr_time_ms if cbr_decision else 0.0,
        },
        "total_time_ms": total_time_ms,
    }


@app.get("/ab-test/metrics", response_model=ABTestMetricsResponse)
async def get_ab_test_metrics() -> ABTestMetricsResponse:
    """
    Get A/B testing metrics.

    Returns statistics comparing CBR vs framework performance.

    Returns:
        ABTestMetricsResponse with comparison metrics
    """
    if len(ab_test_results) == 0:
        return ABTestMetricsResponse(
            total_comparisons=0,
            agreement_rate=0.0,
            cbr_avg_confidence=0.0,
            framework_avg_confidence=0.0,
            cbr_faster_percentage=0.0,
            recent_results=[],
        )

    # Calculate metrics
    total = len(ab_test_results)
    matches = sum(1 for r in ab_test_results if r["decisions_match"])
    agreement_rate = (matches / total * 100) if total > 0 else 0.0

    cbr_confidences = [r["cbr_confidence"] for r in ab_test_results if r["cbr_confidence"] is not None]
    cbr_avg = sum(cbr_confidences) / len(cbr_confidences) if cbr_confidences else 0.0

    framework_avg = sum(r["framework_confidence"] for r in ab_test_results) / total

    # Note: We don't track time in ab_test_results, so cbr_faster_percentage is 0
    # Would need to modify ABTestResult to include timing
    cbr_faster_percentage = 0.0

    # Get recent results
    recent = [ABTestResult(**r) for r in ab_test_results[-10:]]

    return ABTestMetricsResponse(
        total_comparisons=total,
        agreement_rate=agreement_rate,
        cbr_avg_confidence=cbr_avg,
        framework_avg_confidence=framework_avg,
        cbr_faster_percentage=cbr_faster_percentage,
        recent_results=recent,
    )


@app.get("/precedents/metrics", response_model=PrecedentMetricsResponse)
async def get_precedent_metrics() -> PrecedentMetricsResponse:
    """
    Get metrics about precedents and CBR usage.

    Returns statistics about precedent database and CBR performance.

    Raises:
        HTTPException: If CBR disabled
    """
    if cbr_engine is None or precedent_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CBR Engine not available"
        )

    try:
        # Get all precedents (limit to 1000 for performance)
        all_precedents = await precedent_db.find_similar([0.0] * 384, limit=1000)

        total_precedents = len(all_precedents)

        # Calculate average success score
        success_scores = [p.success for p in all_precedents if p.success is not None]
        avg_success = sum(success_scores) / len(success_scores) if success_scores else 0.0

        # Count high-confidence precedents (success > 0.8/0.9 = 0.89 confidence)
        high_confidence_count = sum(
            1 for p in all_precedents
            if p.success is not None and p.success * 0.9 > 0.8
        )

        # Calculate shortcut rate
        shortcut_rate = (cbr_shortcut_count / evaluation_count * 100) if evaluation_count > 0 else 0.0

        return PrecedentMetricsResponse(
            total_precedents=total_precedents,
            avg_success_score=avg_success,
            high_confidence_count=high_confidence_count,
            precedents_used_count=cbr_precedents_used_count,
            shortcut_rate=shortcut_rate
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get precedent metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get precedent metrics: {str(e)}"
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
