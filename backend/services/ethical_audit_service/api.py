"""Ethical Audit Service - FastAPI Application.

This service provides comprehensive audit logging and analytics for all ethical
decisions made by the VÉRTICE AI platform. It supports the 4-framework ethical
architecture (Kantian, Consequentialist, Virtue Ethics, Principialism).
"""

from datetime import datetime
import logging
import os
import time
from typing import Any, Dict, List, Optional
import uuid

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler, Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

from auth import (
    get_current_user,
    require_admin,
    require_any_role,
    require_auditor_or_admin,
    require_soc_or_admin,
    TokenData,
    UserRole,
)
from database import EthicalAuditDatabase
from models import (
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    ConsequentialistResult,
    DecisionHistoryQuery,
    DecisionHistoryResponse,
    DecisionType,
    EthicalDecisionLog,
    EthicalDecisionRequest,
    EthicalDecisionResponse,
    EthicalMetrics,
    FinalDecision,
    FrameworkPerformance,
    HumanOverrideRequest,
    HumanOverrideResponse,
    KantianResult,
    PrinciplismResult,
    RiskLevel,
    VirtueEthicsResult,
)

# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="VÉRTICE Ethical Audit Service",
    version="1.0.0",
    description="Comprehensive audit logging and analytics for AI ethical decisions",
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# FIXED: CORS middleware with environment-based origins (not wildcard)
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8080,http://localhost:4200",
).split(",")

logger.info(f"CORS allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # FIXED: No more wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
    allow_headers=["Content-Type", "Authorization"],  # Only needed headers
)

# Add trusted host middleware for additional security
TRUSTED_HOSTS = os.getenv(
    "TRUSTED_HOSTS", "localhost,127.0.0.1,ethical-audit,ethical_audit_service"
).split(",")

app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

# Database client (initialized on startup)
db: Optional[EthicalAuditDatabase] = None


# ============================================================================
# LIFECYCLE EVENTS
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize database connection and schema on startup."""
    global db
    print("🚀 Starting Ethical Audit Service...")

    db = EthicalAuditDatabase()
    await db.connect()
    await db.initialize_schema()

    print("✅ Ethical Audit Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of database connections."""
    global db
    print("👋 Shutting down Ethical Audit Service...")

    if db:
        await db.disconnect()

    print("🛑 Ethical Audit Service stopped")


# ============================================================================
# HEALTH & STATUS
# ============================================================================


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Dict with service status and timestamp
    """
    return {
        "status": "healthy",
        "service": "ethical_audit_service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db and db.pool else "disconnected",
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Detailed service status with database stats.

    Returns:
        Dict with detailed status information
    """
    if not db or not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    async with db.pool.acquire() as conn:
        # Get table counts
        decisions_count = await conn.fetchval("SELECT COUNT(*) FROM ethical_decisions")
        overrides_count = await conn.fetchval("SELECT COUNT(*) FROM human_overrides")
        compliance_count = await conn.fetchval("SELECT COUNT(*) FROM compliance_logs")

        # Get latest decision timestamp
        latest_decision = await conn.fetchval(
            "SELECT MAX(timestamp) FROM ethical_decisions"
        )

    return {
        "service": "ethical_audit_service",
        "status": "operational",
        "database": {
            "connected": True,
            "pool_size": db.pool.get_size(),
            "decisions_logged": decisions_count,
            "overrides_logged": overrides_count,
            "compliance_checks": compliance_count,
            "latest_decision": latest_decision.isoformat() if latest_decision else None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# ETHICAL DECISION LOGGING
# ============================================================================


@app.post("/audit/decision", response_model=Dict[str, Any])
@limiter.limit("100/minute")  # Rate limit: 100 requests per minute
async def log_decision(
    request: Request,
    decision_log: EthicalDecisionLog,
    current_user: TokenData = require_soc_or_admin,
) -> Dict[str, Any]:
    """Log an ethical decision to the audit database.

    This endpoint receives a complete ethical decision from the ethical engine
    and stores it in the time-series database for audit and analytics.

    Args:
        decision_log: Complete ethical decision log with all framework results

    Returns:
        Dict with logged decision ID and confirmation
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        decision_id = await db.log_decision(decision_log)

        return {
            "status": "success",
            "decision_id": str(decision_id),
            "timestamp": decision_log.timestamp.isoformat(),
            "message": "Ethical decision logged successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log decision: {str(e)}")


@app.get("/audit/decision/{decision_id}", response_model=Dict[str, Any])
async def get_decision(
    decision_id: uuid.UUID, current_user: TokenData = require_auditor_or_admin
) -> Dict[str, Any]:
    """Retrieve a specific ethical decision by ID.

    Args:
        decision_id: UUID of the decision

    Returns:
        Complete decision record with all framework results
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    decision = await db.get_decision(decision_id)

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decision


@app.post("/audit/decisions/query", response_model=DecisionHistoryResponse)
@limiter.limit("30/minute")  # Rate limit: 30 queries per minute
async def query_decisions(
    request: Request,
    query: DecisionHistoryQuery,
    current_user: TokenData = require_auditor_or_admin,
) -> DecisionHistoryResponse:
    """Query ethical decisions with advanced filtering.

    Supports filtering by:
    - Time range (start_time, end_time)
    - Decision type (offensive_action, auto_response, etc.)
    - System component
    - Final decision (APPROVED, REJECTED, ESCALATED_HITL)
    - Risk level (low, medium, high, critical)
    - Confidence range
    - Automated vs. HITL decisions

    Args:
        query: DecisionHistoryQuery with filter parameters

    Returns:
        Paginated list of decisions matching the query
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    start_time = time.time()

    try:
        decisions, total_count = await db.query_decisions(query)

        query_time_ms = int((time.time() - start_time) * 1000)

        # Convert to response models
        decision_responses = []
        for dec in decisions:
            # Parse framework results from JSON
            kantian = (
                KantianResult(**dec["kantian_result"])
                if dec.get("kantian_result")
                else None
            )
            consequentialist = (
                ConsequentialistResult(**dec["consequentialist_result"])
                if dec.get("consequentialist_result")
                else None
            )
            virtue = (
                VirtueEthicsResult(**dec["virtue_ethics_result"])
                if dec.get("virtue_ethics_result")
                else None
            )
            principi = (
                PrinciplismResult(**dec["principialism_result"])
                if dec.get("principialism_result")
                else None
            )

            decision_responses.append(
                EthicalDecisionResponse(
                    decision_id=dec["id"],
                    timestamp=dec["timestamp"],
                    decision_type=DecisionType(dec["decision_type"]),
                    action_description=dec["action_description"],
                    system_component=dec["system_component"],
                    kantian_result=kantian,
                    consequentialist_result=consequentialist,
                    virtue_ethics_result=virtue,
                    principialism_result=principi,
                    final_decision=FinalDecision(dec["final_decision"]),
                    final_confidence=dec["final_confidence"],
                    decision_explanation=dec["decision_explanation"],
                    total_latency_ms=dec["total_latency_ms"],
                    risk_level=RiskLevel(dec["risk_level"]),
                    automated=dec["automated"],
                )
            )

        return DecisionHistoryResponse(
            total_count=total_count,
            decisions=decision_responses,
            query_time_ms=query_time_ms,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# ============================================================================
# HUMAN OVERRIDE LOGGING
# ============================================================================


@app.post("/audit/override", response_model=HumanOverrideResponse)
async def log_override(
    override: HumanOverrideRequest, current_user: TokenData = require_soc_or_admin
) -> HumanOverrideResponse:
    """Log a human override of an AI ethical decision.

    This is critical for audit trails when human operators override AI decisions.
    Requires detailed justification for compliance and learning purposes.

    Args:
        override: HumanOverrideRequest with operator details and justification

    Returns:
        Confirmation with override ID
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    # Verify decision exists
    decision = await db.get_decision(override.decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    try:
        override_id = await db.log_override(override)

        return HumanOverrideResponse(
            override_id=override_id,
            decision_id=override.decision_id,
            timestamp=datetime.utcnow(),
            operator_id=override.operator_id,
            operator_role=override.operator_role,
            override_decision=override.override_decision,
            justification=override.justification,
            override_reason=override.override_reason,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log override: {str(e)}")


@app.get("/audit/overrides/{decision_id}", response_model=List[Dict[str, Any]])
async def get_overrides(decision_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get all human overrides for a specific decision.

    Args:
        decision_id: UUID of the decision

    Returns:
        List of all overrides for this decision
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    overrides = await db.get_overrides_by_decision(decision_id)
    return overrides


# ============================================================================
# COMPLIANCE LOGGING
# ============================================================================


@app.post("/audit/compliance", response_model=ComplianceCheckResponse)
async def log_compliance_check(
    check: ComplianceCheckRequest,
) -> ComplianceCheckResponse:
    """Log a regulatory compliance check.

    Supports multiple regulations:
    - EU AI Act
    - GDPR Article 22
    - NIST AI RMF
    - Tallinn Manual 2.0
    - Executive Order 14110
    - Brazil LGPD

    Args:
        check: ComplianceCheckRequest with regulation details and results

    Returns:
        Confirmation with compliance check ID
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        compliance_id = await db.log_compliance_check(check)

        return ComplianceCheckResponse(
            compliance_id=compliance_id,
            timestamp=datetime.utcnow(),
            regulation=check.regulation,
            requirement_id=check.requirement_id,
            check_result=check.check_result,
            remediation_required=check.remediation_required,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to log compliance check: {str(e)}"
        )


# ============================================================================
# METRICS & ANALYTICS
# ============================================================================


@app.get("/audit/metrics", response_model=EthicalMetrics)
async def get_metrics() -> EthicalMetrics:
    """Get real-time ethical KPIs and metrics.

    Provides comprehensive metrics including:
    - Decision quality (approval rate, rejection rate, HITL escalation)
    - Performance (latency p95/p99)
    - Framework agreement rates
    - Human override metrics
    - Compliance status
    - Risk distribution

    Returns:
        EthicalMetrics with current system-wide ethical KPIs
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        metrics = await db.get_metrics()
        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@app.get("/audit/metrics/frameworks", response_model=List[FrameworkPerformance])
async def get_framework_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back")
) -> List[FrameworkPerformance]:
    """Get performance metrics for each ethical framework.

    Tracks performance of all 4 frameworks:
    - Kantian Deontology
    - Consequentialism (Utilitarianism)
    - Virtue Ethics
    - Principialism

    Args:
        hours: Number of hours to look back (1-168)

    Returns:
        List of FrameworkPerformance objects with latency and accuracy metrics
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        performance = await db.get_framework_performance(hours=hours)
        return performance

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get framework metrics: {str(e)}"
        )


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================


@app.get("/audit/analytics/timeline")
async def get_decision_timeline(
    hours: int = Query(default=24, ge=1, le=720, description="Hours to analyze"),
    bucket_minutes: int = Query(
        default=60, ge=5, le=1440, description="Time bucket size in minutes"
    ),
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get time-series analytics of ethical decisions.

    Args:
        hours: Number of hours to analyze
        bucket_minutes: Time bucket size for aggregation
        current_user: Authenticated user (for RBAC)

    Returns:
        Time-series data with decision counts and metrics per bucket
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db.pool.acquire() as conn:
        # FIXED: Use parametrized queries instead of f-strings
        rows = await conn.fetch(
            """
            SELECT
                time_bucket($1::text || ' minutes', timestamp) AS bucket,
                COUNT(*) as total_decisions,
                AVG(final_confidence) as avg_confidence,
                AVG(total_latency_ms) as avg_latency,
                SUM(CASE WHEN final_decision = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN final_decision = 'REJECTED' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN final_decision = 'ESCALATED_HITL' THEN 1 ELSE 0 END) as escalated
            FROM ethical_decisions
            WHERE timestamp >= NOW() - ($2::text || ' hours')::INTERVAL
            GROUP BY bucket
            ORDER BY bucket ASC
        """,
            str(bucket_minutes),
            str(hours),
        )

    timeline = [
        {
            "timestamp": row["bucket"].isoformat(),
            "total_decisions": row["total_decisions"],
            "avg_confidence": float(row["avg_confidence"] or 0.0),
            "avg_latency_ms": float(row["avg_latency"] or 0.0),
            "approved": row["approved"],
            "rejected": row["rejected"],
            "escalated": row["escalated"],
        }
        for row in rows
    ]

    return {
        "hours_analyzed": hours,
        "bucket_minutes": bucket_minutes,
        "data_points": len(timeline),
        "timeline": timeline,
    }


@app.get("/audit/analytics/risk-heatmap")
async def get_risk_heatmap(
    hours: int = Query(default=24, ge=1, le=720, description="Hours to analyze"),
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get risk heatmap showing decision type vs risk level distribution.

    Args:
        hours: Number of hours to analyze
        current_user: Authenticated user (for RBAC)

    Returns:
        Heatmap data with counts for each (decision_type, risk_level) combination
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db.pool.acquire() as conn:
        # FIXED: Parametrized query
        rows = await conn.fetch(
            """
            SELECT
                decision_type,
                risk_level,
                COUNT(*) as count,
                AVG(final_confidence) as avg_confidence
            FROM ethical_decisions
            WHERE timestamp >= NOW() - ($1::text || ' hours')::INTERVAL
            GROUP BY decision_type, risk_level
            ORDER BY decision_type, risk_level
        """,
            str(hours),
        )

    heatmap = [
        {
            "decision_type": row["decision_type"],
            "risk_level": row["risk_level"],
            "count": row["count"],
            "avg_confidence": float(row["avg_confidence"] or 0.0),
        }
        for row in rows
    ]

    return {"hours_analyzed": hours, "heatmap": heatmap}


# ============================================================================
# XAI (EXPLAINABILITY) ENDPOINTS
# ============================================================================


@app.post("/api/explain")
@limiter.limit("30/minute")  # Rate limit for XAI (computationally expensive)
async def explain_decision(
    request: Request,
    explanation_request: Dict[str, Any],
    current_user: TokenData = require_soc_or_admin,
) -> Dict[str, Any]:
    """Generate explanation for a model's prediction or decision.

    This endpoint provides XAI (Explainable AI) capabilities using LIME, SHAP,
    or counterfactual explanations for cybersecurity models.

    Args:
        request: FastAPI request (for rate limiting)
        explanation_request: Explanation request with keys:
            - decision_id: ID of decision to explain
            - explanation_type: 'lime', 'shap', or 'counterfactual'
            - detail_level: 'summary', 'detailed', or 'technical'
            - instance: Input instance (dict of features)
            - prediction: Model's prediction
        current_user: Authenticated user

    Returns:
        Explanation result with feature importances and summary
    """
    try:
        # Import XAI engine (lazy import to avoid loading if not needed)
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from xai.engine import get_global_engine
        from xai.base import ExplanationType, DetailLevel

        # Get parameters
        decision_id = explanation_request.get('decision_id')
        explanation_type = explanation_request.get('explanation_type', 'lime')
        detail_level = explanation_request.get('detail_level', 'detailed')
        instance = explanation_request.get('instance', {})
        prediction = explanation_request.get('prediction')
        model_reference = explanation_request.get('model_reference', None)

        # Validate required fields
        if not instance:
            raise HTTPException(status_code=400, detail="instance is required")
        if prediction is None:
            raise HTTPException(status_code=400, detail="prediction is required")

        # Convert string types to enums
        try:
            exp_type = ExplanationType(explanation_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid explanation_type. Must be one of: lime, shap, counterfactual"
            )

        try:
            det_level = DetailLevel(detail_level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid detail_level. Must be one of: summary, detailed, technical"
            )

        # Get XAI engine
        engine = get_global_engine()

        # For now, use a dummy model (in production, load actual model)
        # This is a placeholder that will be replaced with actual model loading
        from xai.engine import DummyModel
        model = DummyModel()

        # TODO: Load actual model based on model_reference
        # if model_reference:
        #     model = load_model(model_reference)

        # Add decision_id to instance for tracking
        if decision_id:
            instance['decision_id'] = decision_id

        # Generate explanation
        start_time = time.time()

        explanation = await engine.explain(
            model=model,
            instance=instance,
            prediction=prediction,
            explanation_type=exp_type,
            detail_level=det_level
        )

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"XAI explanation generated: {explanation_type}, "
            f"latency={latency_ms}ms, confidence={explanation.confidence:.2f}"
        )

        # Convert to dict for JSON response
        response = {
            "success": True,
            "explanation_id": explanation.explanation_id,
            "decision_id": explanation.decision_id,
            "explanation_type": explanation.explanation_type.value,
            "detail_level": explanation.detail_level.value,
            "summary": explanation.summary,
            "top_features": [
                {
                    "feature_name": f.feature_name,
                    "importance": f.importance,
                    "value": str(f.value),
                    "description": f.description,
                    "contribution": f.contribution
                }
                for f in explanation.top_features
            ],
            "confidence": explanation.confidence,
            "counterfactual": explanation.counterfactual,
            "visualization_data": explanation.visualization_data,
            "model_type": explanation.model_type,
            "latency_ms": explanation.latency_ms,
            "metadata": explanation.metadata
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XAI explanation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@app.get("/api/xai/stats")
async def get_xai_stats(
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get XAI engine statistics.

    Args:
        current_user: Authenticated user

    Returns:
        XAI statistics including cache hits, top features, drift detection
    """
    try:
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from xai.engine import get_global_engine

        engine = get_global_engine()
        stats = engine.get_statistics()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get XAI stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get XAI statistics: {str(e)}"
        )


@app.get("/api/xai/top-features")
async def get_xai_top_features(
    n: int = Query(default=10, ge=1, le=100, description="Number of top features"),
    hours: Optional[int] = Query(default=None, ge=1, le=720, description="Time window in hours"),
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get top N most important features across all explanations.

    Args:
        n: Number of top features
        hours: Optional time window in hours
        current_user: Authenticated user

    Returns:
        Top features with statistics
    """
    try:
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from xai.engine import get_global_engine

        engine = get_global_engine()
        top_features = engine.get_top_features(n=n, time_window_hours=hours)

        return {
            "success": True,
            "top_features": top_features,
            "time_window_hours": hours
        }

    except Exception as e:
        logger.error(f"Failed to get top features: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get top features: {str(e)}"
        )


@app.get("/api/xai/drift")
async def get_xai_drift(
    feature_name: Optional[str] = Query(default=None, description="Specific feature to check"),
    window_size: int = Query(default=100, ge=10, le=1000, description="Window size for drift detection"),
    threshold: float = Query(default=0.2, ge=0.0, le=1.0, description="Drift threshold"),
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Detect feature importance drift.

    Args:
        feature_name: Specific feature (None = global drift)
        window_size: Window size for comparison
        threshold: Drift threshold
        current_user: Authenticated user

    Returns:
        Drift detection results
    """
    try:
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from xai.engine import get_global_engine

        engine = get_global_engine()
        drift_result = engine.detect_drift(
            feature_name=feature_name,
            window_size=window_size,
            threshold=threshold
        )

        return {
            "success": True,
            "drift_result": drift_result
        }

    except Exception as e:
        logger.error(f"Failed to detect drift: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect drift: {str(e)}"
        )


@app.get("/api/xai/health")
async def xai_health_check() -> Dict[str, Any]:
    """XAI engine health check.

    Returns:
        Health status of XAI components
    """
    try:
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from xai.engine import get_global_engine

        engine = get_global_engine()
        health = await engine.health_check()

        return health

    except Exception as e:
        logger.error(f"XAI health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================================
# FAIRNESS & BIAS MITIGATION ENDPOINTS (PHASE 3)
# ============================================================================


@app.post("/api/fairness/evaluate")
@limiter.limit("50/minute")
async def evaluate_fairness(
    request: Request,
    fairness_request: Dict[str, Any],
    current_user: TokenData = require_soc_or_admin,
) -> Dict[str, Any]:
    """Evaluate fairness of model predictions across protected groups.

    Args:
        request: FastAPI request (for rate limiting)
        fairness_request: Fairness evaluation request with keys:
            - model_id: Model identifier
            - predictions: Array of predictions
            - true_labels: Array of true labels (optional)
            - protected_attribute: Array of protected attribute values
            - protected_value: Value indicating protected group (default 1)
            - protected_attr_type: Type of protected attribute
        current_user: Authenticated user

    Returns:
        Fairness evaluation results with metrics and bias detection
    """
    try:
        # Import fairness module
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from fairness.monitor import FairnessMonitor
        from fairness.base import ProtectedAttribute
        import numpy as np

        # Get parameters
        model_id = fairness_request.get('model_id', 'unknown')
        predictions = np.array(fairness_request.get('predictions', []))
        true_labels_list = fairness_request.get('true_labels')
        true_labels = np.array(true_labels_list) if true_labels_list else None
        protected_attribute = np.array(fairness_request.get('protected_attribute', []))
        protected_value = fairness_request.get('protected_value', 1)
        protected_attr_type = fairness_request.get('protected_attr_type', 'geographic_location')

        # Validate required fields
        if len(predictions) == 0:
            raise HTTPException(status_code=400, detail="predictions array is required")
        if len(protected_attribute) == 0:
            raise HTTPException(status_code=400, detail="protected_attribute array is required")
        if len(predictions) != len(protected_attribute):
            raise HTTPException(
                status_code=400,
                detail="predictions and protected_attribute must have same length"
            )

        # Convert protected attribute type
        try:
            prot_attr = ProtectedAttribute(protected_attr_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid protected_attr_type. Must be one of: {[e.value for e in ProtectedAttribute]}"
            )

        # Get or create fairness monitor
        if not hasattr(app.state, 'fairness_monitor'):
            app.state.fairness_monitor = FairnessMonitor({
                'history_max_size': 1000,
                'alert_threshold': 'medium'
            })

        monitor = app.state.fairness_monitor

        # Evaluate fairness
        start_time = time.time()

        snapshot = monitor.evaluate_fairness(
            predictions=predictions,
            true_labels=true_labels,
            protected_attribute=protected_attribute,
            protected_value=protected_value,
            model_id=model_id,
            protected_attr_type=prot_attr
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Convert to response
        fairness_metrics = {}
        for metric, result in snapshot.fairness_results.items():
            fairness_metrics[metric.value] = {
                'is_fair': result.is_fair,
                'difference': result.difference,
                'ratio': result.ratio,
                'threshold': result.threshold,
                'group_0_value': result.group_0_value,
                'group_1_value': result.group_1_value,
                'sample_size_0': result.sample_size_0,
                'sample_size_1': result.sample_size_1
            }

        bias_results = {}
        for method, result in snapshot.bias_results.items():
            bias_results[method] = {
                'bias_detected': result.bias_detected,
                'severity': result.severity,
                'confidence': result.confidence,
                'p_value': result.p_value,
                'effect_size': result.effect_size,
                'affected_groups': result.affected_groups,
                'metadata': result.metadata
            }

        logger.info(
            f"Fairness evaluation complete: model={model_id}, "
            f"latency={latency_ms}ms, {len(fairness_metrics)} metrics"
        )

        return {
            'success': True,
            'model_id': model_id,
            'protected_attribute': prot_attr.value,
            'sample_size': snapshot.sample_size,
            'timestamp': snapshot.timestamp.isoformat(),
            'fairness_metrics': fairness_metrics,
            'bias_detection': bias_results,
            'latency_ms': latency_ms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fairness evaluation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate fairness: {str(e)}"
        )


@app.post("/api/fairness/mitigate")
@limiter.limit("20/minute")
async def mitigate_bias(
    request: Request,
    mitigation_request: Dict[str, Any],
    current_user: TokenData = require_soc_or_admin,
) -> Dict[str, Any]:
    """Apply bias mitigation strategy to model predictions.

    Args:
        request: FastAPI request (for rate limiting)
        mitigation_request: Mitigation request with keys:
            - strategy: 'threshold_optimization', 'calibration_adjustment', or 'auto'
            - predictions: Array of predictions
            - true_labels: Array of true labels
            - protected_attribute: Array of protected attribute values
            - protected_value: Value indicating protected group
        current_user: Authenticated user

    Returns:
        Mitigation results with fairness improvement
    """
    try:
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from fairness.mitigation import MitigationEngine
        import numpy as np

        # Get parameters
        strategy = mitigation_request.get('strategy', 'auto')
        predictions = np.array(mitigation_request.get('predictions', []))
        true_labels = np.array(mitigation_request.get('true_labels', []))
        protected_attribute = np.array(mitigation_request.get('protected_attribute', []))
        protected_value = mitigation_request.get('protected_value', 1)

        # Validate
        if len(predictions) == 0 or len(true_labels) == 0:
            raise HTTPException(status_code=400, detail="predictions and true_labels are required")

        # Get or create mitigation engine
        if not hasattr(app.state, 'mitigation_engine'):
            app.state.mitigation_engine = MitigationEngine({
                'performance_threshold': 0.75,
                'max_performance_loss': 0.05
            })

        engine = app.state.mitigation_engine

        # Apply mitigation
        start_time = time.time()

        if strategy == 'auto':
            result = engine.mitigate_auto(
                predictions, true_labels, protected_attribute, protected_value
            )
        elif strategy == 'threshold_optimization':
            result = engine.mitigate_threshold_optimization(
                predictions, true_labels, protected_attribute, protected_value
            )
        elif strategy == 'calibration_adjustment':
            result = engine.mitigate_calibration_adjustment(
                predictions, true_labels, protected_attribute, protected_value
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy. Must be: auto, threshold_optimization, or calibration_adjustment"
            )

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Bias mitigation complete: strategy={result.mitigation_method}, "
            f"success={result.success}, latency={latency_ms}ms"
        )

        return {
            'success': result.success,
            'mitigation_method': result.mitigation_method,
            'protected_attribute': result.protected_attribute.value,
            'fairness_before': result.fairness_before,
            'fairness_after': result.fairness_after,
            'performance_impact': result.performance_impact,
            'timestamp': result.timestamp.isoformat(),
            'metadata': result.metadata,
            'latency_ms': latency_ms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bias mitigation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mitigate bias: {str(e)}"
        )


@app.get("/api/fairness/trends")
async def get_fairness_trends(
    model_id: Optional[str] = None,
    metric: Optional[str] = None,
    lookback_hours: int = Query(24, ge=1, le=168),
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get fairness trends over time.

    Args:
        model_id: Filter by model ID (optional)
        metric: Filter by metric (optional)
        lookback_hours: Hours to look back (1-168)
        current_user: Authenticated user

    Returns:
        Fairness trends analysis
    """
    try:
        if not hasattr(app.state, 'fairness_monitor'):
            return {
                'trends': {},
                'num_snapshots': 0,
                'message': 'No fairness data available yet'
            }

        monitor = app.state.fairness_monitor

        # Convert metric string to enum if provided
        fairness_metric = None
        if metric:
            import sys
            sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')
            from fairness.base import FairnessMetric

            try:
                fairness_metric = FairnessMetric(metric)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric. Must be one of: {[e.value for e in FairnessMetric]}"
                )

        trends = monitor.get_fairness_trends(
            model_id=model_id,
            metric=fairness_metric,
            lookback_hours=lookback_hours
        )

        return trends

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get fairness trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trends: {str(e)}"
        )


@app.get("/api/fairness/drift")
async def detect_fairness_drift(
    model_id: Optional[str] = None,
    metric: Optional[str] = None,
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Detect drift in fairness metrics.

    Args:
        model_id: Filter by model ID (optional)
        metric: Filter by metric (optional)
        current_user: Authenticated user

    Returns:
        Drift detection results
    """
    try:
        if not hasattr(app.state, 'fairness_monitor'):
            return {
                'drift_detected': False,
                'message': 'No fairness data available yet'
            }

        monitor = app.state.fairness_monitor

        # Convert metric if provided
        fairness_metric = None
        if metric:
            import sys
            sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')
            from fairness.base import FairnessMetric

            try:
                fairness_metric = FairnessMetric(metric)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric. Must be one of: {[e.value for e in FairnessMetric]}"
                )

        drift_result = monitor.detect_drift(
            model_id=model_id,
            metric=fairness_metric
        )

        return drift_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to detect fairness drift: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect drift: {str(e)}"
        )


@app.get("/api/fairness/alerts")
async def get_fairness_alerts(
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    since_hours: Optional[int] = Query(None, ge=1, le=720),
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get fairness violation alerts.

    Args:
        severity: Filter by severity (low, medium, high, critical)
        limit: Maximum alerts to return (1-500)
        since_hours: Only return alerts from last N hours (optional)
        current_user: Authenticated user

    Returns:
        List of fairness alerts
    """
    try:
        if not hasattr(app.state, 'fairness_monitor'):
            return {
                'alerts': [],
                'total': 0,
                'message': 'No fairness monitoring active'
            }

        monitor = app.state.fairness_monitor

        alerts = monitor.get_alerts(
            severity=severity,
            limit=limit,
            since_hours=since_hours
        )

        # Convert to dict
        alerts_dict = []
        for alert in alerts:
            alerts_dict.append({
                'alert_id': alert.alert_id,
                'timestamp': alert.timestamp.isoformat(),
                'severity': alert.severity,
                'metric': alert.metric.value,
                'protected_attribute': alert.protected_attribute.value,
                'violation_details': alert.violation_details,
                'recommended_action': alert.recommended_action,
                'auto_mitigated': alert.auto_mitigated,
                'metadata': alert.metadata
            })

        return {
            'alerts': alerts_dict,
            'total': len(alerts_dict),
            'severity_filter': severity,
            'limit': limit
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get fairness alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts: {str(e)}"
        )


@app.get("/api/fairness/stats")
async def get_fairness_stats(
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get fairness monitoring statistics.

    Args:
        current_user: Authenticated user

    Returns:
        Fairness statistics including violation rate
    """
    try:
        if not hasattr(app.state, 'fairness_monitor'):
            return {
                'total_evaluations': 0,
                'total_violations': 0,
                'violation_rate': 0.0,
                'message': 'No fairness monitoring active'
            }

        monitor = app.state.fairness_monitor
        stats = monitor.get_statistics()

        return stats

    except Exception as e:
        logger.error(f"Failed to get fairness stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@app.get("/api/fairness/health")
async def fairness_health_check() -> Dict[str, Any]:
    """Fairness module health check.

    Returns:
        Health status of fairness components
    """
    try:
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from fairness.constraints import FairnessConstraints
        from fairness.bias_detector import BiasDetector
        from fairness.mitigation import MitigationEngine

        # Test initialization
        constraints = FairnessConstraints()
        detector = BiasDetector()
        engine = MitigationEngine()

        monitor_active = hasattr(app.state, 'fairness_monitor')
        monitor_snapshots = len(app.state.fairness_monitor.history) if monitor_active else 0

        return {
            'status': 'healthy',
            'components': {
                'fairness_constraints': 'ok',
                'bias_detector': 'ok',
                'mitigation_engine': 'ok',
                'monitor': 'active' if monitor_active else 'inactive'
            },
            'monitor_snapshots': monitor_snapshots,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Fairness health check failed: {e}", exc_info=True)
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8612)
