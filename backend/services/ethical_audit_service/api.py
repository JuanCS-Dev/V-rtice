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

        # Model loading: Using DummyModel for XAI demonstration
        # Real model loading tracked in GitHub Issue #TODO_CREATE_ISSUE
        # Expected implementation: model registry lookup by model_reference
        from xai.engine import DummyModel
        model = DummyModel()

        # Future: if model_reference:
        #     model = await model_registry.load(model_reference)

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
# DIFFERENTIAL PRIVACY ENDPOINTS
# ============================================================================

@app.post("/api/privacy/dp-query")
async def execute_dp_query(
    request: Dict[str, Any],
    current_user: TokenData = require_soc_or_admin,
) -> Dict[str, Any]:
    """Execute a differentially private query.

    Args:
        request: Query request containing:
            - query_type: 'count', 'sum', 'mean', 'histogram'
            - data: Query data (dict or list)
            - epsilon: Privacy parameter (optional, default: 1.0)
            - delta: Failure probability (optional, default: 1e-5)
            - Additional query-specific parameters
        current_user: Authenticated user

    Returns:
        DP query result with privacy guarantee
    """
    try:
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from privacy import DPAggregator
        import pandas as pd

        # Extract parameters
        query_type = request.get('query_type')
        data = request.get('data')
        epsilon = request.get('epsilon', 1.0)
        delta = request.get('delta', 1e-5)

        if not query_type:
            raise HTTPException(status_code=400, detail="query_type required")
        if not data:
            raise HTTPException(status_code=400, detail="data required")

        # Convert data to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise HTTPException(status_code=400, detail="Invalid data format")

        # Create aggregator
        aggregator = DPAggregator(epsilon=epsilon, delta=delta)

        # Execute query
        if query_type == 'count':
            result = aggregator.count(df)
        elif query_type == 'count_by_group':
            group_col = request.get('group_column')
            if not group_col:
                raise HTTPException(status_code=400, detail="group_column required for count_by_group")
            result = aggregator.count_by_group(df, group_column=group_col)
        elif query_type == 'sum':
            value_col = request.get('value_column')
            value_range = request.get('value_range', 1.0)
            if not value_col:
                raise HTTPException(status_code=400, detail="value_column required for sum")
            result = aggregator.sum(df, value_column=value_col, value_range=value_range)
        elif query_type == 'mean':
            value_col = request.get('value_column')
            value_range = request.get('value_range', 1.0)
            if not value_col:
                raise HTTPException(status_code=400, detail="value_column required for mean")
            result = aggregator.mean(df, value_column=value_col, value_range=value_range)
        elif query_type == 'histogram':
            value_col = request.get('value_column')
            bins = request.get('bins', 10)
            result = aggregator.histogram(df, value_column=value_col, bins=bins)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown query type: {query_type}")

        # Log query
        logger.info(
            f"DP query executed: type={query_type}, "
            f"epsilon={result.epsilon_used}, delta={result.delta_used:.6e}, "
            f"user={current_user.username}"
        )

        # Return result
        return {
            'query_type': query_type,
            'result': result.to_dict(),
            'privacy_guarantee': {
                'epsilon': result.epsilon_used,
                'delta': result.delta_used,
                'mechanism': result.mechanism
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DP query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/privacy/budget")
async def get_privacy_budget(
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get global privacy budget status.

    Args:
        current_user: Authenticated user

    Returns:
        Privacy budget statistics
    """
    try:
        if not hasattr(app.state, 'privacy_budget'):
            return {
                'status': 'not_configured',
                'message': 'No global privacy budget configured'
            }

        budget = app.state.privacy_budget
        stats = budget.get_statistics()

        return {
            'status': 'active',
            'budget': stats
        }

    except Exception as e:
        logger.error(f"Failed to get privacy budget: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get budget: {str(e)}")


@app.get("/api/privacy/stats")
async def get_privacy_stats(
    current_user: TokenData = require_auditor_or_admin,
) -> Dict[str, Any]:
    """Get differential privacy statistics.

    Args:
        current_user: Authenticated user

    Returns:
        Privacy statistics including query counts, privacy loss
    """
    try:
        stats = {
            'budget_configured': hasattr(app.state, 'privacy_budget'),
            'timestamp': datetime.utcnow().isoformat()
        }

        if hasattr(app.state, 'privacy_budget'):
            budget = app.state.privacy_budget
            budget_stats = budget.get_statistics()

            stats.update({
                'total_queries': budget_stats['queries_executed'],
                'epsilon_used': budget_stats['used_epsilon'],
                'delta_used': budget_stats['used_delta'],
                'epsilon_remaining': budget_stats['remaining_epsilon'],
                'delta_remaining': budget_stats['remaining_delta'],
                'privacy_level': budget_stats['privacy_level'],
                'budget_exhausted': budget_stats['budget_exhausted']
            })

        return stats

    except Exception as e:
        logger.error(f"Failed to get privacy stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/api/privacy/health")
async def privacy_health_check() -> Dict[str, Any]:
    """Differential privacy module health check.

    Returns:
        Health status of privacy components
    """
    try:
        import sys
        sys.path.append('/home/juan/vertice-dev/backend/services/maximus_core_service')

        from privacy import DPAggregator, LaplaceMechanism, GaussianMechanism
        from privacy.base import PrivacyBudget, PrivacyParameters

        # Test initialization
        aggregator = DPAggregator(epsilon=1.0, delta=1e-5)
        budget = PrivacyBudget(total_epsilon=10.0, total_delta=1e-4)
        params = PrivacyParameters(epsilon=1.0, delta=1e-5, sensitivity=1.0)

        budget_configured = hasattr(app.state, 'privacy_budget')

        return {
            'status': 'healthy',
            'components': {
                'dp_aggregator': 'ok',
                'laplace_mechanism': 'ok',
                'gaussian_mechanism': 'ok',
                'privacy_budget': 'ok',
                'global_budget': 'configured' if budget_configured else 'not_configured'
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Privacy health check failed: {e}", exc_info=True)
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


# ============================================================================
# FEDERATED LEARNING ENDPOINTS
# ============================================================================

@app.post("/api/fl/coordinator/start-round")
async def fl_start_round(
    request: Dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin)
):
    """
    Start a new federated learning training round.

    Body:
    {
        "model_type": "threat_classifier | malware_detector",
        "aggregation_strategy": "fedavg | secure | dp_fedavg",
        "min_clients": 2,
        "max_clients": 10,
        "local_epochs": 5,
        "local_batch_size": 32,
        "learning_rate": 0.001,
        "use_differential_privacy": false,
        "dp_epsilon": 8.0,
        "dp_delta": 1e-5
    }

    Returns:
    {
        "round_id": 1,
        "status": "waiting_for_clients",
        "selected_clients": ["client_1", "client_2"],
        "global_model_version": 5,
        "timestamp": "2025-10-06T12:00:00Z"
    }
    """
    try:
        from federated_learning import (
            FLCoordinator,
            CoordinatorConfig,
            FLConfig,
            ModelType,
            AggregationStrategy,
        )
        from federated_learning.model_adapters import create_model_adapter

        # Parse model type
        model_type_str = request.get("model_type", "threat_classifier")
        model_type = ModelType(model_type_str)

        # Parse aggregation strategy
        agg_strategy_str = request.get("aggregation_strategy", "fedavg")
        agg_strategy = AggregationStrategy(agg_strategy_str)

        # Create FL config
        fl_config = FLConfig(
            model_type=model_type,
            aggregation_strategy=agg_strategy,
            min_clients=request.get("min_clients", 2),
            max_clients=request.get("max_clients", 10),
            local_epochs=request.get("local_epochs", 5),
            local_batch_size=request.get("local_batch_size", 32),
            learning_rate=request.get("learning_rate", 0.001),
            use_differential_privacy=request.get("use_differential_privacy", False),
            dp_epsilon=request.get("dp_epsilon", 8.0),
            dp_delta=request.get("dp_delta", 1e-5),
        )

        # Initialize coordinator (in production, this would be persistent)
        coordinator_config = CoordinatorConfig(fl_config=fl_config)
        coordinator = FLCoordinator(coordinator_config)

        # Initialize global model
        model_adapter = create_model_adapter(model_type)
        coordinator.set_global_model(model_adapter.get_weights())

        # Store coordinator in app state (simplified; use Redis in production)
        if not hasattr(app.state, 'fl_coordinators'):
            app.state.fl_coordinators = {}
        app.state.fl_coordinators[model_type.value] = coordinator

        # Start round
        round_obj = coordinator.start_round()

        logger.info(
            f"FL round {round_obj.round_id} started by {current_user.user_id} "
            f"({model_type.value}, {agg_strategy.value})"
        )

        return {
            'round_id': round_obj.round_id,
            'status': round_obj.status.value,
            'selected_clients': round_obj.selected_clients,
            'global_model_version': round_obj.global_model_version,
            'model_type': model_type.value,
            'aggregation_strategy': agg_strategy.value,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"FL start round failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fl/coordinator/submit-update")
async def fl_submit_update(
    request: Dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin)
):
    """
    Submit a model update from FL client.

    Body:
    {
        "model_type": "threat_classifier",
        "client_id": "org_1",
        "round_id": 1,
        "weights": {...},  # Serialized weights
        "num_samples": 1000,
        "metrics": {"loss": 0.45, "accuracy": 0.88},
        "differential_privacy_applied": false,
        "epsilon_used": 0.0
    }

    Returns:
    {
        "success": true,
        "round_status": "training",
        "updates_received": 2,
        "updates_expected": 3
    }
    """
    try:
        from federated_learning import ModelUpdate
        from federated_learning.communication import FLCommunicationChannel
        import numpy as np

        # Get model type
        model_type_str = request.get("model_type", "threat_classifier")

        # Get coordinator
        if not hasattr(app.state, 'fl_coordinators'):
            raise HTTPException(status_code=404, detail="No FL coordinators active")

        coordinator = app.state.fl_coordinators.get(model_type_str)
        if not coordinator:
            raise HTTPException(
                status_code=404,
                detail=f"No coordinator for model type: {model_type_str}"
            )

        # Deserialize weights
        channel = FLCommunicationChannel()
        serialized_weights = request.get("weights", {})
        weights = channel.deserialize_weights(serialized_weights)

        # Create model update
        update = ModelUpdate(
            client_id=request.get("client_id"),
            round_id=request.get("round_id"),
            weights=weights,
            num_samples=request.get("num_samples", 0),
            metrics=request.get("metrics", {}),
            differential_privacy_applied=request.get("differential_privacy_applied", False),
            epsilon_used=request.get("epsilon_used", 0.0),
        )

        # Submit to coordinator
        coordinator.receive_update(update)

        # Get round status
        round_status = coordinator.get_round_status()

        logger.info(
            f"FL update received from {update.client_id} for round {update.round_id} "
            f"({update.num_samples} samples, {update.get_update_size_mb():.1f}MB)"
        )

        return {
            'success': True,
            'round_status': round_status['status'],
            'updates_received': round_status['received_updates'],
            'updates_expected': round_status['expected_updates'],
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"FL submit update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fl/coordinator/global-model")
async def fl_get_global_model(
    model_type: str = "threat_classifier",
    current_user: TokenData = Depends(require_soc_or_admin)
):
    """
    Download the current global model.

    Query Params:
        model_type: "threat_classifier" | "malware_detector"

    Returns:
    {
        "model_type": "threat_classifier",
        "model_version": 5,
        "weights": {...},  # Serialized weights
        "timestamp": "2025-10-06T12:00:00Z"
    }
    """
    try:
        from federated_learning.communication import FLCommunicationChannel

        # Get coordinator
        if not hasattr(app.state, 'fl_coordinators'):
            raise HTTPException(status_code=404, detail="No FL coordinators active")

        coordinator = app.state.fl_coordinators.get(model_type)
        if not coordinator:
            raise HTTPException(
                status_code=404,
                detail=f"No coordinator for model type: {model_type}"
            )

        # Get global model weights
        global_weights = coordinator.get_global_model()
        if global_weights is None:
            raise HTTPException(status_code=404, detail="Global model not initialized")

        # Serialize weights
        channel = FLCommunicationChannel()
        serialized_weights = channel.serialize_weights(global_weights)

        logger.info(
            f"Global model downloaded by {current_user.user_id} "
            f"(type={model_type}, version={coordinator.fl_config.model_version})"
        )

        return {
            'model_type': model_type,
            'model_version': coordinator.fl_config.model_version,
            'weights': serialized_weights,
            'total_parameters': sum(w.size for w in global_weights.values()),
            'timestamp': datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FL get global model failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fl/coordinator/round-status")
async def fl_round_status(
    model_type: str = "threat_classifier",
    current_user: TokenData = Depends(require_auditor_or_admin)
):
    """
    Get status of current FL round.

    Query Params:
        model_type: "threat_classifier" | "malware_detector"

    Returns:
    {
        "round_id": 1,
        "status": "training",
        "selected_clients": ["client_1", "client_2", "client_3"],
        "received_updates": 2,
        "expected_updates": 3,
        "progress": 0.67,
        "elapsed_time": 45.2
    }
    """
    try:
        # Get coordinator
        if not hasattr(app.state, 'fl_coordinators'):
            return {'status': 'no_active_rounds', 'timestamp': datetime.utcnow().isoformat()}

        coordinator = app.state.fl_coordinators.get(model_type)
        if not coordinator:
            return {'status': 'no_coordinator', 'timestamp': datetime.utcnow().isoformat()}

        # Get round status
        round_status = coordinator.get_round_status()

        if round_status is None:
            return {'status': 'no_active_round', 'timestamp': datetime.utcnow().isoformat()}

        return {
            **round_status,
            'model_type': model_type,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"FL round status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fl/metrics")
async def fl_get_metrics(
    model_type: str = "threat_classifier",
    current_user: TokenData = Depends(require_auditor_or_admin)
):
    """
    Get federated learning metrics and convergence data.

    Query Params:
        model_type: "threat_classifier" | "malware_detector"

    Returns:
    {
        "total_rounds": 10,
        "total_clients": 5,
        "active_clients": 5,
        "average_participation_rate": 0.95,
        "average_round_duration": 120.5,
        "total_samples_trained": 50000,
        "global_model_accuracy": 0.92,
        "convergence_status": false,
        "privacy_budget_used": 80.0,
        "last_updated": "2025-10-06T12:00:00Z"
    }
    """
    try:
        # Get coordinator
        if not hasattr(app.state, 'fl_coordinators'):
            return {
                'error': 'No FL coordinators active',
                'timestamp': datetime.utcnow().isoformat()
            }

        coordinator = app.state.fl_coordinators.get(model_type)
        if not coordinator:
            return {
                'error': f'No coordinator for model type: {model_type}',
                'timestamp': datetime.utcnow().isoformat()
            }

        # Get metrics
        metrics = coordinator.get_metrics()

        return {
            **metrics.to_dict(),
            'model_type': model_type,
        }

    except Exception as e:
        logger.error(f"FL metrics failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HITL/HOTL ENDPOINTS (Phase 5)
# ============================================================================

@app.post("/api/hitl/evaluate")
async def hitl_evaluate_decision(
    request: Dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin)
):
    """
    Submit AI decision for HITL evaluation.

    Request Body:
    {
        "action_type": "block_ip" | "isolate_host" | "quarantine_file" | ...,
        "action_params": {"ip_address": "10.0.0.1", ...},
        "ai_reasoning": "Detected port scanning activity",
        "confidence": 0.88,
        "threat_score": 0.75,
        "affected_assets": ["srv-001"],
        "asset_criticality": "high" | "medium" | "low",
        "business_impact": "Medium - potential service disruption",
        "metadata": {...}
    }

    Returns:
    {
        "decision_id": "uuid",
        "automation_level": "full" | "supervised" | "advisory" | "manual",
        "risk_level": "low" | "medium" | "high" | "critical",
        "status": "executed" | "queued" | "rejected",
        "executed": true/false,
        "queued": true/false,
        "sla_deadline": "2025-10-06T12:10:00Z",
        "result": {...} (if executed)
    }
    """
    try:
        # Initialize HITL framework if not exists
        if not hasattr(app.state, 'hitl_framework'):
            from maximus_core_service.hitl import (
                HITLDecisionFramework,
                HITLConfig,
                DecisionQueue,
                AuditTrail,
                OperatorInterface,
                EscalationManager,
                ActionType,
            )

            # Create components
            config = HITLConfig()
            framework = HITLDecisionFramework(config=config)
            queue = DecisionQueue()
            audit = AuditTrail()
            escalation = EscalationManager()
            operator_interface = OperatorInterface(
                decision_framework=framework,
                decision_queue=queue,
                escalation_manager=escalation,
                audit_trail=audit,
            )

            # Connect
            framework.set_decision_queue(queue)
            framework.set_audit_trail(audit)

            # Store in app state
            app.state.hitl_framework = framework
            app.state.hitl_queue = queue
            app.state.hitl_audit = audit
            app.state.hitl_operator_interface = operator_interface
            app.state.hitl_escalation = escalation

            logger.info("HITL framework initialized")

        # Get framework
        framework = app.state.hitl_framework

        # Parse action type
        action_type_str = request.get("action_type", "").upper()
        from maximus_core_service.hitl import ActionType
        try:
            action_type = ActionType[action_type_str]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action_type: {request.get('action_type')}"
            )

        # Evaluate decision
        result = framework.evaluate_action(
            action_type=action_type,
            action_params=request.get("action_params", {}),
            ai_reasoning=request.get("ai_reasoning", ""),
            confidence=float(request.get("confidence", 0.0)),
            threat_score=float(request.get("threat_score", 0.0)),
            affected_assets=request.get("affected_assets", []),
            asset_criticality=request.get("asset_criticality", "medium"),
            business_impact=request.get("business_impact", ""),
            **request.get("metadata", {}),
        )

        # Build response
        response = {
            "decision_id": result.decision.decision_id,
            "automation_level": result.decision.automation_level.value,
            "risk_level": result.decision.risk_level.value,
            "status": result.decision.status.value,
            "executed": result.executed,
            "queued": result.queued,
            "rejected": result.rejected,
            "sla_deadline": (
                result.decision.sla_deadline.isoformat()
                if result.decision.sla_deadline
                else None
            ),
            "processing_time": result.processing_time,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if result.executed:
            response["result"] = result.execution_output
        if result.execution_error:
            response["error"] = result.execution_error

        return response

    except Exception as e:
        logger.error(f"HITL evaluate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hitl/queue")
async def hitl_get_queue(
    risk_level: Optional[str] = None,
    limit: int = 20,
    current_user: TokenData = Depends(require_soc_or_admin)
):
    """
    Get pending decisions from HITL queue.

    Query Params:
        risk_level: Filter by risk level ("low", "medium", "high", "critical")
        limit: Maximum number of decisions to return (default: 20)

    Returns:
    {
        "pending_decisions": [
            {
                "decision_id": "uuid",
                "action_type": "block_ip",
                "action_params": {...},
                "ai_reasoning": "...",
                "confidence": 0.88,
                "threat_score": 0.75,
                "risk_level": "medium",
                "automation_level": "supervised",
                "created_at": "2025-10-06T12:00:00Z",
                "sla_deadline": "2025-10-06T12:15:00Z",
                "time_remaining": "14 minutes"
            },
            ...
        ],
        "total_in_queue": 15,
        "queue_size_by_risk": {
            "critical": 2,
            "high": 5,
            "medium": 6,
            "low": 2
        }
    }
    """
    try:
        if not hasattr(app.state, 'hitl_queue'):
            return {
                "pending_decisions": [],
                "total_in_queue": 0,
                "queue_size_by_risk": {},
                "error": "HITL not initialized"
            }

        queue = app.state.hitl_queue

        # Parse risk level filter
        risk_filter = None
        if risk_level:
            from maximus_core_service.hitl import RiskLevel
            try:
                risk_filter = RiskLevel[risk_level.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid risk_level: {risk_level}"
                )

        # Get pending decisions
        pending = queue.get_pending_decisions(risk_level=risk_filter)

        # Sort by priority and limit
        pending.sort(key=lambda d: (
            4 - list(RiskLevel).index(d.risk_level),
            d.sla_deadline or datetime.max,
        ))
        pending = pending[:limit]

        # Format response
        decisions_data = []
        for decision in pending:
            time_remaining = decision.get_time_remaining()
            decisions_data.append({
                "decision_id": decision.decision_id,
                "action_type": decision.context.action_type.value,
                "action_params": decision.context.action_params,
                "ai_reasoning": decision.context.ai_reasoning,
                "confidence": decision.context.confidence,
                "threat_score": decision.context.threat_score,
                "risk_level": decision.risk_level.value,
                "automation_level": decision.automation_level.value,
                "created_at": decision.created_at.isoformat(),
                "sla_deadline": (
                    decision.sla_deadline.isoformat() if decision.sla_deadline else None
                ),
                "time_remaining_seconds": (
                    int(time_remaining.total_seconds()) if time_remaining else None
                ),
            })

        # Get queue metrics
        queue_sizes = queue.get_size_by_risk()

        return {
            "pending_decisions": decisions_data,
            "total_in_queue": queue.get_total_size(),
            "queue_size_by_risk": {
                level.value: size for level, size in queue_sizes.items()
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"HITL queue failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hitl/approve")
async def hitl_approve_decision(
    request: Dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin)
):
    """
    Approve and execute HITL decision.

    Request Body:
    {
        "decision_id": "uuid",
        "operator_comment": "Verified malicious IP in threat intel",
        "modifications": {} (optional - modify action params before execution)
    }

    Returns:
    {
        "status": "approved",
        "executed": true,
        "decision_id": "uuid",
        "result": {...},
        "timestamp": "2025-10-06T12:00:00Z"
    }
    """
    try:
        if not hasattr(app.state, 'hitl_operator_interface'):
            raise HTTPException(status_code=503, detail="HITL not initialized")

        interface = app.state.hitl_operator_interface

        # Create/get operator session
        if not hasattr(app.state, 'hitl_operator_sessions'):
            app.state.hitl_operator_sessions = {}

        operator_id = current_user.username
        session_key = f"{operator_id}_{current_user.role}"

        if session_key not in app.state.hitl_operator_sessions:
            session = interface.create_session(
                operator_id=operator_id,
                operator_name=current_user.username,
                operator_role=current_user.role,
            )
            app.state.hitl_operator_sessions[session_key] = session
        else:
            session = app.state.hitl_operator_sessions[session_key]

        # Approve decision
        decision_id = request.get("decision_id")
        if not decision_id:
            raise HTTPException(status_code=400, detail="decision_id required")

        comment = request.get("operator_comment", "")
        modifications = request.get("modifications")

        if modifications:
            # Modify and approve
            result = interface.modify_and_approve(
                session_id=session.session_id,
                decision_id=decision_id,
                modifications=modifications,
                comment=comment,
            )
        else:
            # Simple approve
            result = interface.approve_decision(
                session_id=session.session_id,
                decision_id=decision_id,
                comment=comment,
            )

        return {
            **result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"HITL approve failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hitl/reject")
async def hitl_reject_decision(
    request: Dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin)
):
    """
    Reject HITL decision.

    Request Body:
    {
        "decision_id": "uuid",
        "reason": "False positive - legitimate system update",
        "operator_comment": "Verified with IT team"
    }

    Returns:
    {
        "status": "rejected",
        "decision_id": "uuid",
        "reason": "...",
        "timestamp": "2025-10-06T12:00:00Z"
    }
    """
    try:
        if not hasattr(app.state, 'hitl_operator_interface'):
            raise HTTPException(status_code=503, detail="HITL not initialized")

        interface = app.state.hitl_operator_interface

        # Get/create session
        if not hasattr(app.state, 'hitl_operator_sessions'):
            app.state.hitl_operator_sessions = {}

        operator_id = current_user.username
        session_key = f"{operator_id}_{current_user.role}"

        if session_key not in app.state.hitl_operator_sessions:
            session = interface.create_session(
                operator_id=operator_id,
                operator_name=current_user.username,
                operator_role=current_user.role,
            )
            app.state.hitl_operator_sessions[session_key] = session
        else:
            session = app.state.hitl_operator_sessions[session_key]

        # Reject decision
        decision_id = request.get("decision_id")
        reason = request.get("reason")

        if not decision_id or not reason:
            raise HTTPException(status_code=400, detail="decision_id and reason required")

        result = interface.reject_decision(
            session_id=session.session_id,
            decision_id=decision_id,
            reason=reason,
            comment=request.get("operator_comment", ""),
        )

        return {
            **result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"HITL reject failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hitl/escalate")
async def hitl_escalate_decision(
    request: Dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin)
):
    """
    Escalate HITL decision to higher authority.

    Request Body:
    {
        "decision_id": "uuid",
        "reason": "Requires senior review - production impact",
        "operator_comment": "Unable to make this decision at my level"
    }

    Returns:
    {
        "status": "escalated",
        "decision_id": "uuid",
        "escalated_to": "security_manager",
        "escalation_event_id": "uuid",
        "timestamp": "2025-10-06T12:00:00Z"
    }
    """
    try:
        if not hasattr(app.state, 'hitl_operator_interface'):
            raise HTTPException(status_code=503, detail="HITL not initialized")

        interface = app.state.hitl_operator_interface

        # Get/create session
        if not hasattr(app.state, 'hitl_operator_sessions'):
            app.state.hitl_operator_sessions = {}

        operator_id = current_user.username
        session_key = f"{operator_id}_{current_user.role}"

        if session_key not in app.state.hitl_operator_sessions:
            session = interface.create_session(
                operator_id=operator_id,
                operator_name=current_user.username,
                operator_role=current_user.role,
            )
            app.state.hitl_operator_sessions[session_key] = session
        else:
            session = app.state.hitl_operator_sessions[session_key]

        # Escalate decision
        decision_id = request.get("decision_id")
        reason = request.get("reason")

        if not decision_id or not reason:
            raise HTTPException(status_code=400, detail="decision_id and reason required")

        result = interface.escalate_decision(
            session_id=session.session_id,
            decision_id=decision_id,
            reason=reason,
            comment=request.get("operator_comment", ""),
        )

        return {
            **result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"HITL escalate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hitl/audit")
async def hitl_query_audit(
    decision_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    current_user: TokenData = Depends(require_auditor_or_admin)
):
    """
    Query HITL audit trail.

    Query Params:
        decision_id: Filter by decision ID
        start_time: Start time (ISO format)
        end_time: End time (ISO format)
        event_type: Event type filter ("decision_created", "decision_executed", etc.)
        limit: Maximum entries to return (default: 100)

    Returns:
    {
        "audit_entries": [
            {
                "entry_id": "uuid",
                "decision_id": "uuid",
                "event_type": "decision_created",
                "event_description": "AI decision created: block_ip",
                "actor_type": "ai" | "human",
                "actor_id": "maximus_ai" | "operator_123",
                "timestamp": "2025-10-06T12:00:00Z",
                "decision_snapshot": {...},
                "context_snapshot": {...}
            },
            ...
        ],
        "total_entries": 100,
        "timestamp": "2025-10-06T12:00:00Z"
    }
    """
    try:
        if not hasattr(app.state, 'hitl_audit'):
            return {
                "audit_entries": [],
                "total_entries": 0,
                "error": "HITL not initialized"
            }

        audit = app.state.hitl_audit

        # Build query
        from maximus_core_service.hitl import AuditQuery

        query_params = {
            "limit": limit,
        }

        if decision_id:
            query_params["decision_ids"] = [decision_id]

        if start_time:
            from datetime import datetime
            query_params["start_time"] = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

        if end_time:
            from datetime import datetime
            query_params["end_time"] = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        if event_type:
            query_params["event_types"] = [event_type]

        query = AuditQuery(**query_params)

        # Query audit trail
        entries = audit.query(query, redact_pii=True)

        # Format response
        entries_data = [
            {
                "entry_id": entry.entry_id,
                "decision_id": entry.decision_id,
                "event_type": entry.event_type,
                "event_description": entry.event_description,
                "actor_type": entry.actor_type,
                "actor_id": entry.actor_id,
                "timestamp": entry.timestamp.isoformat(),
                "decision_snapshot": entry.decision_snapshot,
                "context_snapshot": entry.context_snapshot,
                "compliance_tags": entry.compliance_tags,
            }
            for entry in entries
        ]

        return {
            "audit_entries": entries_data,
            "total_entries": len(entries),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"HITL audit query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMPLIANCE & CERTIFICATION ENDPOINTS
# ============================================================================

@app.post("/api/compliance/check")
@limiter.limit("10/minute")
async def check_compliance(
    request: Request,
    regulation_type: str,
    current_user: TokenData = Depends(require_auditor_or_admin),
):
    """Check compliance for specific regulation."""
    try:
        from maximus_core_service.compliance import (
            ComplianceEngine,
            ComplianceConfig,
            RegulationType,
        )

        # Parse regulation type
        reg_type = RegulationType(regulation_type)

        # Initialize engine
        config = ComplianceConfig(enabled_regulations=[reg_type])
        engine = ComplianceEngine(config)

        # Check compliance
        result = engine.check_compliance(reg_type)

        return {
            "regulation": regulation_type,
            "compliance_percentage": result.compliance_percentage,
            "score": result.score,
            "total_controls": result.total_controls,
            "compliant": result.compliant,
            "non_compliant": result.non_compliant,
            "violations": len(result.violations),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Compliance check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compliance/status")
@limiter.limit("30/minute")
async def get_compliance_status(
    request: Request,
    current_user: TokenData = Depends(require_auditor_or_admin),
):
    """Get overall compliance status for all regulations."""
    try:
        from maximus_core_service.compliance import ComplianceEngine, ComplianceConfig

        # Initialize engine with all regulations
        engine = ComplianceEngine()

        # Get status
        status = engine.get_compliance_status()

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Get compliance status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compliance/gaps")
@limiter.limit("10/minute")
async def analyze_gaps(
    request: Request,
    regulation_type: str,
    current_user: TokenData = Depends(require_auditor_or_admin),
):
    """Analyze compliance gaps for regulation."""
    try:
        from maximus_core_service.compliance import (
            ComplianceEngine,
            GapAnalyzer,
            RegulationType,
        )

        # Initialize components
        reg_type = RegulationType(regulation_type)
        engine = ComplianceEngine()
        analyzer = GapAnalyzer()

        # Check compliance
        compliance_result = engine.check_compliance(reg_type)

        # Analyze gaps
        gap_analysis = analyzer.analyze_compliance_gaps(compliance_result)

        return {
            "regulation": regulation_type,
            "total_gaps": len(gap_analysis.gaps),
            "compliance_percentage": gap_analysis.compliance_percentage,
            "estimated_hours": gap_analysis.estimated_remediation_hours,
            "gaps": [
                {
                    "control_id": g.control_id,
                    "title": g.title,
                    "severity": g.severity.value,
                    "priority": g.priority,
                    "effort_hours": g.estimated_effort_hours,
                }
                for g in gap_analysis.gaps[:20]  # Limit to top 20
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Gap analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compliance/remediation")
@limiter.limit("5/minute")
async def create_remediation_plan(
    request: Request,
    regulation_type: str,
    target_days: int = 180,
    current_user: TokenData = Depends(require_admin),
):
    """Create remediation plan for compliance gaps."""
    try:
        from maximus_core_service.compliance import (
            ComplianceEngine,
            GapAnalyzer,
            RegulationType,
        )

        # Initialize components
        reg_type = RegulationType(regulation_type)
        engine = ComplianceEngine()
        analyzer = GapAnalyzer()

        # Analyze gaps
        compliance_result = engine.check_compliance(reg_type)
        gap_analysis = analyzer.analyze_compliance_gaps(compliance_result)

        # Create plan
        plan = analyzer.create_remediation_plan(
            gap_analysis,
            target_completion_days=target_days,
            created_by=current_user.user_id,
        )

        return {
            "plan_id": plan.plan_id,
            "regulation": regulation_type,
            "total_actions": len(plan.actions),
            "target_completion": plan.target_completion_date.isoformat(),
            "status": plan.status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Remediation plan creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compliance/evidence")
@limiter.limit("20/minute")
async def list_evidence(
    request: Request,
    control_id: Optional[str] = None,
    current_user: TokenData = Depends(require_auditor_or_admin),
):
    """List collected compliance evidence."""
    try:
        from maximus_core_service.compliance import EvidenceCollector, ComplianceConfig

        # Initialize collector
        config = ComplianceConfig()
        collector = EvidenceCollector(config)

        # Get evidence
        if control_id:
            evidence = collector.get_evidence_for_control(control_id)
        else:
            all_evidence = collector.get_all_evidence()
            evidence = [e for items in all_evidence.values() for e in items]

        return {
            "total_evidence": len(evidence),
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "type": e.evidence_type.value,
                    "control_id": e.control_id,
                    "title": e.title,
                    "collected_at": e.collected_at.isoformat(),
                    "verified": e.verified,
                    "expired": e.is_expired(),
                }
                for e in evidence[:50]  # Limit to 50
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"List evidence failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compliance/evidence/collect")
@limiter.limit("10/minute")
async def collect_evidence(
    request: Request,
    control_id: str,
    evidence_type: str,
    title: str,
    description: str,
    file_path: str,
    current_user: TokenData = Depends(require_soc_or_admin),
):
    """Collect new compliance evidence."""
    try:
        from maximus_core_service.compliance import (
            EvidenceCollector,
            ComplianceConfig,
            EvidenceType,
        )
        from maximus_core_service.compliance.regulations import get_regulation, RegulationType

        # Initialize collector
        config = ComplianceConfig()
        collector = EvidenceCollector(config)

        # Parse evidence type
        ev_type = EvidenceType(evidence_type)

        # Find control (search all regulations)
        control = None
        for reg_type in config.enabled_regulations:
            regulation = get_regulation(reg_type)
            control = regulation.get_control(control_id)
            if control:
                break

        if not control:
            raise HTTPException(status_code=404, detail=f"Control {control_id} not found")

        # Collect evidence based on type
        if ev_type == EvidenceType.LOG:
            evidence_item = collector.collect_log_evidence(
                control, file_path, title, description
            )
        elif ev_type == EvidenceType.DOCUMENT:
            evidence_item = collector.collect_document_evidence(
                control, file_path, title, description
            )
        elif ev_type == EvidenceType.CONFIGURATION:
            evidence_item = collector.collect_configuration_evidence(
                control, file_path, title, description
            )
        elif ev_type == EvidenceType.POLICY:
            evidence_item = collector.collect_policy_evidence(
                control, file_path, title, description
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported evidence type: {evidence_type}")

        if not evidence_item:
            raise HTTPException(status_code=500, detail="Evidence collection failed")

        return {
            "evidence_id": evidence_item.evidence.evidence_id,
            "control_id": control_id,
            "type": evidence_type,
            "title": title,
            "file_size": evidence_item.file_size,
            "file_hash": evidence_item.evidence.file_hash,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evidence collection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compliance/certification")
@limiter.limit("5/minute")
async def check_certification_readiness(
    request: Request,
    regulation_type: str,
    current_user: TokenData = Depends(require_admin),
):
    """Check certification readiness for regulation."""
    try:
        from maximus_core_service.compliance import (
            ComplianceEngine,
            EvidenceCollector,
            ComplianceConfig,
            RegulationType,
        )
        from maximus_core_service.compliance.certifications import (
            ISO27001Checker,
            SOC2Checker,
            IEEE7000Checker,
        )

        # Initialize components
        reg_type = RegulationType(regulation_type)
        config = ComplianceConfig()
        engine = ComplianceEngine(config)
        collector = EvidenceCollector(config)

        # Select appropriate checker
        if reg_type == RegulationType.ISO_27001:
            checker = ISO27001Checker(engine, collector)
        elif reg_type == RegulationType.SOC2_TYPE_II:
            checker = SOC2Checker(engine, collector)
        elif reg_type == RegulationType.IEEE_7000:
            checker = IEEE7000Checker(engine, collector)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Certification checker not available for {regulation_type}",
            )

        # Check readiness
        cert_result = checker.check_certification_readiness()

        return {
            "regulation": regulation_type,
            "certification_ready": cert_result.certification_ready,
            "compliance_percentage": cert_result.compliance_percentage,
            "score": cert_result.score,
            "gaps_to_certification": cert_result.gaps_to_certification,
            "critical_gaps": cert_result.critical_gaps,
            "estimated_days": cert_result.estimated_days_to_certification,
            "recommendations": cert_result.recommendations[:10],  # Top 10
            "summary": cert_result.get_summary(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Certification readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compliance/dashboard")
@limiter.limit("20/minute")
async def get_compliance_dashboard(
    request: Request,
    current_user: TokenData = Depends(require_auditor_or_admin),
):
    """Get compliance dashboard data."""
    try:
        from maximus_core_service.compliance import (
            ComplianceEngine,
            EvidenceCollector,
            ComplianceMonitor,
            ComplianceConfig,
        )

        # Initialize components
        config = ComplianceConfig()
        engine = ComplianceEngine(config)
        collector = EvidenceCollector(config)
        monitor = ComplianceMonitor(engine, collector, config=config)

        # Run monitoring checks
        monitor._run_monitoring_checks()

        # Get dashboard data
        dashboard = monitor.generate_dashboard_data()

        return {
            "dashboard": dashboard,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Get compliance dashboard failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8612)
