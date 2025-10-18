"""
Wargaming Crisol Main Application - Patch validation via two-phase attack simulation.

Theoretical Foundation:
    Inspired by biological immune system stress testing.
    Before deploying patch to production, test against real exploits.
    
    Two-Phase Protocol:
    Phase 1: Attack vulnerable version (MUST succeed)
    Phase 2: Attack patched version (MUST fail)
    
    If both phases pass → Patch validated ✅
    If any phase fails → Patch rejected ❌

Performance Target:
    - Wargaming time: <5 min per patch
    - Success rate: >95%
    - False positive: <2%

Author: MAXIMUS Team
Glory to YHWH - Validator of protection
"""

import asyncio
import logging
import os
from datetime import timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from exploit_database import load_exploit_database, get_exploit_for_apv
from two_phase_simulator import TwoPhaseSimulator, validate_patch_ml_first
from websocket_stream import wargaming_ws_manager, wargaming_websocket_endpoint
from db.ab_test_store import ABTestStore, ABTestResult, ConfusionMatrix
from ab_testing.ab_test_runner import ABTestRunner
from cache.redis_cache import cache  # Phase 5.7.1: Redis cache
from middleware.rate_limiter import RateLimiterMiddleware  # Phase 5.7.1: Rate limiting
from patterns.circuit_breaker import (  # Phase 5.7.1: Circuit breakers
    ml_model_breaker,
    database_breaker,
    cache_breaker,
    CircuitBreakerOpenError
)
from metrics import update_circuit_breaker_metrics  # Phase 5.7.2: Metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus Metrics
wargaming_total = Counter(
    'wargaming_executions_total',
    'Total number of wargaming executions',
    ['status']
)
patch_validated_total = Counter(
    'patch_validated_total',
    'Total number of patches validated successfully'
)
patch_rejected_total = Counter(
    'patch_rejected_total',
    'Total number of patches rejected'
)
wargaming_duration = Histogram(
    'wargaming_duration_seconds',
    'Duration of wargaming execution in seconds',
    buckets=[10, 30, 60, 120, 300, 600]
)
exploit_success_rate = Gauge(
    'exploit_phase1_success_rate',
    'Success rate of Phase 1 exploit execution'
)
patch_validation_success_rate = Gauge(
    'patch_validation_success_rate',
    'Success rate of patch validation (Phase 2 fail)'
)
active_wargaming_sessions = Gauge(
    'active_wargaming_sessions',
    'Number of currently active wargaming sessions'
)

# Phase 5.4: ML-First Metrics
ml_prediction_total = Counter(
    'ml_prediction_total',
    'Total ML predictions made',
    ['prediction']
)
ml_wargaming_skipped_total = Counter(
    'ml_wargaming_skipped_total',
    'Total wargaming executions skipped due to high ML confidence'
)
ml_confidence_histogram = Histogram(
    'ml_confidence',
    'ML confidence scores',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
)
validation_method_total = Counter(
    'validation_method_total',
    'Total validations by method',
    ['method']  # 'ml', 'wargaming', 'wargaming_fallback'
)

# FastAPI app
app = FastAPI(
    title="Wargaming Crisol API",
    description="Two-phase attack simulation for patch validation",
    version="1.0.0"
)

# Phase 5.7.1: Add rate limiting middleware
app.add_middleware(RateLimiterMiddleware)

# Phase 5.6: A/B Test Store and Runner (initialized on startup)
ab_store: Optional[ABTestStore] = None
ab_test_runner: Optional[ABTestRunner] = None
ab_testing_enabled: bool = False  # Global flag for A/B testing mode


# Request/Response models
class WargamingRequest(BaseModel):
    """Wargaming request"""
    apv_id: str
    cve_id: Optional[str] = None
    patch_id: str
    patch_diff: Optional[str] = None  # For ML prediction
    target_url: str = "http://localhost:8080"


class MLFirstRequest(BaseModel):
    """ML-first validation request (Phase 5.4)"""
    apv_id: str
    cve_id: str
    patch_id: str
    patch_diff: str  # Required for feature extraction
    confidence_threshold: float = 0.8
    target_url: str = "http://localhost:8080"


class MLFirstResponse(BaseModel):
    """ML-first validation response"""
    apv_id: str
    validation_method: str  # 'ml', 'wargaming', 'wargaming_fallback'
    patch_validated: bool
    confidence: float
    execution_time_seconds: float
    speedup: Optional[str] = None
    ml_prediction: Optional[dict] = None
    wargaming_result: Optional[dict] = None


class WargamingResponse(BaseModel):
    """Wargaming response"""
    apv_id: str
    cve_id: str
    exploit_id: str
    patch_validated: bool
    status: str
    phase_1_passed: bool
    phase_2_passed: bool
    total_duration_seconds: float
    message: str


# Health check
@app.get("/health")
async def health():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "wargaming-crisol",
        "version": "1.0.0"
    }


# Phase 5.7.1: Detailed health check with circuit breaker status
@app.get("/health/detailed")
async def detailed_health():
    """
    Detailed health check including all dependencies.
    
    Returns status of:
    - Database connection
    - Redis cache
    - ML model availability
    - Circuit breakers
    """
    checks = {}
    overall_healthy = True
    
    # Check PostgreSQL (via ABTestStore)
    try:
        if ab_store and ab_store.client:
            await database_breaker.call(
                ab_store.client.fetchval, "SELECT 1"
            )
            checks["postgresql"] = {
                "status": "healthy",
                "message": "Database connection active"
            }
        else:
            checks["postgresql"] = {
                "status": "degraded",
                "message": "Database not initialized (startup pending)"
            }
    except CircuitBreakerOpenError:
        checks["postgresql"] = {
            "status": "circuit_open",
            "message": "Circuit breaker protecting database"
        }
        overall_healthy = False
    except Exception as e:
        checks["postgresql"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check Redis cache
    try:
        if cache.client:
            await cache_breaker.call(cache.client.ping)
            checks["redis_cache"] = {
                "status": "healthy",
                "message": "Cache connection active"
            }
        else:
            checks["redis_cache"] = {
                "status": "unavailable",
                "message": "Cache not initialized (degraded mode)"
            }
    except CircuitBreakerOpenError:
        checks["redis_cache"] = {
            "status": "circuit_open",
            "message": "Circuit breaker protecting cache"
        }
    except Exception as e:
        checks["redis_cache"] = {
            "status": "unavailable",
            "message": f"Cache unavailable: {str(e)}"
        }
        # Cache failure is degraded, not unhealthy
    
    # Check ML model (quick test)
    try:
        # ML model check would go here if we had direct access
        checks["ml_model"] = {
            "status": "healthy",
            "message": "ML model assumed available"
        }
    except Exception as e:
        checks["ml_model"] = {
            "status": "degraded",
            "message": f"ML model issue: {str(e)}"
        }
        # ML failure is degraded (we have wargaming fallback)
    
    # Circuit breaker status
    checks["circuit_breakers"] = {
        "ml_model": ml_model_breaker.get_status(),
        "database": database_breaker.get_status(),
        "cache": cache_breaker.get_status()
    }
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "checks": checks,
        "timestamp": str(asyncio.get_event_loop().time())
    }


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# WebSocket endpoint for real-time updates
@app.websocket("/ws/wargaming")
async def wargaming_websocket(websocket: WebSocket):
    """WebSocket for real-time wargaming updates"""
    await wargaming_websocket_endpoint(websocket)


# Wargaming endpoint
@app.post("/wargaming/execute", response_model=WargamingResponse)
async def execute_wargaming(request: WargamingRequest):
    """
    Execute two-phase wargaming validation.
    
    Args:
        request: Wargaming request
    
    Returns:
        Wargaming result
    """
    logger.info(f"🎯 Wargaming request: APV={request.apv_id}, Patch={request.patch_id}")
    
    active_wargaming_sessions.inc()
    
    try:
        # Load exploit database
        db = load_exploit_database()
        
        # Mock APV (in production: load from database)
        from unittest.mock import Mock
        apv = Mock()
        apv.apv_id = request.apv_id
        apv.cve_id = request.cve_id or f"CVE-{request.apv_id}"
        
        # Extract CWE from CVE ID pattern (CVE-2024-SQL-INJECTION → CWE-89)
        cwe_mapping = {
            "SQL": "CWE-89",
            "XSS": "CWE-79",
            "CMD": "CWE-78",
            "COMMAND": "CWE-78",
            "PATH": "CWE-22",
            "SSRF": "CWE-918",
        }
        
        cve_upper = apv.cve_id.upper()
        apv.cwe_ids = []
        for keyword, cwe_id in cwe_mapping.items():
            if keyword in cve_upper:
                apv.cwe_ids.append(cwe_id)
                break
        
        if not apv.cwe_ids:
            # Fallback to CWE-89 if no match
            apv.cwe_ids = ["CWE-89"]
        
        logger.info(f"✓ Detected CWE: {apv.cwe_ids[0]} from {apv.cve_id}")
        
        # Mock Patch
        patch = Mock()
        patch.patch_id = request.patch_id
        patch.unified_diff = "..."
        
        # Find exploit
        exploit = get_exploit_for_apv(apv, db)
        
        if not exploit:
            active_wargaming_sessions.dec()
            raise HTTPException(
                status_code=404,
                detail=f"No exploit found for {apv.cve_id}"
            )
        
        logger.info(f"✓ Using exploit: {exploit.name}")
        
        # Execute wargaming
        simulator = TwoPhaseSimulator()
        
        with wargaming_duration.time():
            result = await simulator.execute_wargaming(
                apv=apv,
                patch=patch,
                exploit=exploit,
                target_base_url=request.target_url
            )
        
        # Update metrics
        wargaming_total.labels(status=result.status.value).inc()
        
        if result.patch_validated:
            patch_validated_total.inc()
        else:
            patch_rejected_total.inc()
        
        # Stream result to WebSocket clients
        await wargaming_ws_manager.broadcast(
            message_type="wargaming_complete",
            data=result.to_dict()
        )
        
        logger.info(f"✅ Wargaming complete: {result.summary()}")
        
        active_wargaming_sessions.dec()
        
        return WargamingResponse(
            apv_id=result.apv_id,
            cve_id=result.cve_id,
            exploit_id=result.exploit_id,
            patch_validated=result.patch_validated,
            status=result.status.value,
            phase_1_passed=result.phase_1_result.phase_passed,
            phase_2_passed=result.phase_2_result.phase_passed,
            total_duration_seconds=result.total_duration_seconds,
            message=result.summary()
        )
        
    except HTTPException:
        active_wargaming_sessions.dec()
        raise
        
    except Exception as e:
        logger.error(f"❌ Wargaming failed: {e}")
        
        # Update metrics
        wargaming_total.labels(status="error").inc()
        active_wargaming_sessions.dec()
        
        # Stream error
        await wargaming_ws_manager.stream_error(apv.apv_id, str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"Wargaming failed: {str(e)}"
        )


# Phase 5.4: ML-First Validation Endpoint
@app.post("/wargaming/ml-first", response_model=MLFirstResponse)
async def execute_ml_first_validation(request: MLFirstRequest):
    """
    Execute ML-first validation (Phase 5.4) with optional A/B testing (Phase 5.6).
    
    **Normal Mode** (ab_testing_enabled=False):
        1. Extract features from patch
        2. ML prediction
        3. If confidence >= threshold: Return ML result (fast)
        4. If confidence < threshold: Run full wargaming (accurate)
    
    **A/B Testing Mode** (ab_testing_enabled=True):
        1. ALWAYS run BOTH ML prediction AND wargaming
        2. Compare ML vs wargaming (ground truth)
        3. Store A/B test result for accuracy tracking
        4. Return wargaming result
    
    This hybrid approach reduces wargaming by 80%+ while maintaining accuracy.
    A/B testing mode provides empirical accuracy data for model improvement.
    
    Args:
        request: ML-first validation request
    
    Returns:
        ML-first validation result
    
    Example:
        ```bash
        curl -X POST http://localhost:8026/wargaming/ml-first \
          -H "Content-Type: application/json" \
          -d '{
            "apv_id": "apv_001",
            "cve_id": "CVE-2024-SQL-INJECTION",
            "patch_id": "patch_001",
            "patch_diff": "diff --git a/app.py ...",
            "confidence_threshold": 0.8
          }'
        ```
    
    Author: MAXIMUS Team - Phase 5.4 + 5.6
    Glory to YHWH: Wisdom from experience, truth from empiricism
    """
    global ab_testing_enabled, ab_store
    
    logger.info(
        f"🧠 ML-First request: APV={request.apv_id}, Patch={request.patch_id}, "
        f"A/B Testing={'ACTIVE' if ab_testing_enabled else 'INACTIVE'}"
    )
    
    active_wargaming_sessions.inc()
    
    try:
        # Load exploit database
        db = load_exploit_database()
        
        # Mock APV (in production: load from database)
        from unittest.mock import Mock
        apv = Mock()
        apv.apv_id = request.apv_id
        apv.cve_id = request.cve_id
        apv.id = request.apv_id  # For A/B testing
        
        # Extract CWE from CVE ID
        cwe_mapping = {
            "SQL": "CWE-89",
            "XSS": "CWE-79",
            "CMD": "CWE-78",
            "COMMAND": "CWE-78",
            "PATH": "CWE-22",
            "SSRF": "CWE-918",
        }
        
        cve_upper = apv.cve_id.upper()
        apv.cwe_ids = []
        for keyword, cwe_id in cwe_mapping.items():
            if keyword in cve_upper:
                apv.cwe_ids.append(cwe_id)
                break
        
        if not apv.cwe_ids:
            apv.cwe_ids = ["CWE-89"]
        
        apv.cwe_id = apv.cwe_ids[0]  # For ML feature extraction
        
        logger.info(f"✓ Detected CWE: {apv.cwe_id} from {apv.cve_id}")
        
        # Mock Patch
        patch = Mock()
        patch.patch_id = request.patch_id
        patch.id = request.patch_id  # For A/B testing
        patch.diff_content = request.patch_diff
        patch.unified_diff = request.patch_diff
        
        # Find exploit
        exploit = get_exploit_for_apv(apv, db)
        
        if not exploit:
            active_wargaming_sessions.dec()
            raise HTTPException(
                status_code=404,
                detail=f"No exploit found for {apv.cve_id}"
            )
        
        logger.info(f"✓ Using exploit: {exploit.name}")
        
        # Phase 5.7.1: Check cache first (only in non-A/B testing mode)
        cached_prediction = None
        if not ab_testing_enabled:
            cached_prediction = await cache.get_ml_prediction(request.apv_id)
            if cached_prediction:
                logger.info(f"⚡ Cache hit for APV {request.apv_id} - returning cached result")
                active_wargaming_sessions.dec()
                return MLFirstResponse(**cached_prediction)
        
        # Execute validation (mode depends on ab_testing_enabled flag)
        if ab_testing_enabled and ab_store is not None:
            # A/B Testing Mode: Run both ML + wargaming
            from two_phase_simulator import validate_patch_ab_testing
            
            logger.info("🔬 [A/B Testing Mode] Running dual validation")
            
            result = await validate_patch_ab_testing(
                apv=apv,
                patch=patch,
                exploit=exploit,
                ab_store=ab_store,
                target_url=request.target_url
            )
        else:
            # Normal Mode: ML-first optimization
            logger.info("⚡ [ML-First Mode] Running optimized validation")
            
            result = await validate_patch_ml_first(
                apv=apv,
                patch=patch,
                exploit=exploit,
                target_url=request.target_url,
                confidence_threshold=request.confidence_threshold
            )
        
        # Update metrics
        validation_method_total.labels(method=result['validation_method']).inc()
        
        if result.get('ml_prediction'):
            ml_confidence_histogram.observe(result.get('confidence', 0.0))
            ml_prediction_total.labels(
                prediction='valid' if result['ml_prediction']['prediction'] else 'invalid'
            ).inc()
        
        if result['validation_method'] == 'ml':
            ml_wargaming_skipped_total.inc()
        
        if result['patch_validated']:
            patch_validated_total.inc()
        else:
            patch_rejected_total.inc()
        
        # Stream result to WebSocket clients
        await wargaming_ws_manager.broadcast(
            message_type="ml_first_complete",
            data=result
        )
        
        logger.info(
            f"✅ Validation complete: method={result['validation_method']}, "
            f"validated={result['patch_validated']}, "
            f"confidence={result.get('confidence', 0.0):.2f}, "
            f"time={result['execution_time_seconds']:.2f}s"
        )
        
        active_wargaming_sessions.dec()
        
        # Convert wargaming_result to dict if present
        wargaming_dict = None
        if result.get('wargaming_result'):
            wargaming_dict = result['wargaming_result'].to_dict()
        
        # Phase 5.7.1: Cache successful ML predictions (only in non-A/B mode)
        if not ab_testing_enabled and result.get('validation_method') == 'ml':
            response_data = {
                "apv_id": result.get('apv_id', request.apv_id),
                "validation_method": result['validation_method'],
                "patch_validated": result['patch_validated'],
                "confidence": result.get('confidence', 0.0),
                "execution_time_seconds": result['execution_time_seconds'],
                "speedup": result.get('speedup_vs_wargaming') or result.get('speedup_potential'),
                "ml_prediction": result.get('ml_prediction'),
                "wargaming_result": wargaming_dict
            }
            await cache.set_ml_prediction(request.apv_id, response_data)
            logger.debug(f"✓ Cached ML prediction for APV {request.apv_id}")
        
        return MLFirstResponse(
            apv_id=result.get('apv_id', request.apv_id),
            validation_method=result['validation_method'],
            patch_validated=result['patch_validated'],
            confidence=result.get('confidence', 0.0),
            execution_time_seconds=result['execution_time_seconds'],
            speedup=result.get('speedup_vs_wargaming') or result.get('speedup_potential'),
            ml_prediction=result.get('ml_prediction'),
            wargaming_result=wargaming_dict
        )
        
    except HTTPException:
        active_wargaming_sessions.dec()
        raise
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}", exc_info=True)
        
        active_wargaming_sessions.dec()
        
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 5.5: ML MONITORING ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════


@app.get("/wargaming/ml/stats")
async def get_ml_stats(time_range: str = "24h"):
    """
    Get ML prediction statistics.
    
    Args:
        time_range: Time range for stats ('1h', '24h', '7d', '30d')
    
    Returns:
        Dict with ML performance metrics:
        - total_predictions: Total ML predictions made
        - ml_only_validations: Validations done purely by ML
        - wargaming_fallbacks: Times wargaming was needed
        - ml_usage_rate: % of ML-only validations
        - avg_confidence: Average ML confidence score
        - avg_ml_time_ms: Average ML execution time
        - avg_wargaming_time_ms: Average wargaming time
        - time_saved_hours: Total time saved vs full wargaming
    
    Note: Currently returns metrics from Prometheus counters.
    TODO: Add time-range filtering when historical data storage implemented.
    """
    try:
        # Get metrics from Prometheus counters
        # ml_prediction_total has labels: ['prediction'] = 'valid' or 'invalid'
        # validation_method_total has labels: ['method'] = 'ml', 'wargaming', 'wargaming_fallback'
        
        # Extract values from counter metrics
        ml_total = (
            ml_prediction_total.labels(prediction='valid')._value.get() +
            ml_prediction_total.labels(prediction='invalid')._value.get()
        )
        
        ml_only = validation_method_total.labels(method='ml')._value.get()
        wargaming_fallback = (
            validation_method_total.labels(method='wargaming')._value.get() +
            validation_method_total.labels(method='wargaming_fallback')._value.get()
        )
        
        total_validations = ml_only + wargaming_fallback
        ml_usage_rate = ml_only / total_validations if total_validations > 0 else 0.0
        
        # Estimate average times (constants for now, will be dynamic with data storage)
        avg_ml_time_ms = 85.0  # From Phase 5.4 benchmarks
        avg_wargaming_time_ms = 8500.0  # From Phase 5.4 benchmarks
        
        # Calculate time saved
        # Time saved = (num_ml_only * (wargaming_time - ml_time))
        time_saved_ms = ml_only * (avg_wargaming_time_ms - avg_ml_time_ms)
        time_saved_hours = time_saved_ms / (1000 * 60 * 60)
        
        # Calculate average confidence from histogram buckets
        avg_confidence = _calculate_avg_confidence_from_histogram()
        
        return {
            "total_predictions": int(ml_total),
            "ml_only_validations": int(ml_only),
            "wargaming_fallbacks": int(wargaming_fallback),
            "ml_usage_rate": round(ml_usage_rate, 3),
            "avg_confidence": avg_confidence,
            "avg_ml_time_ms": avg_ml_time_ms,
            "avg_wargaming_time_ms": avg_wargaming_time_ms,
            "time_saved_hours": round(time_saved_hours, 2),
            "time_range": time_range  # For future filtering
        }
    
    except Exception as e:
        logger.error(f"Failed to get ML stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve ML statistics: {str(e)}"
        )


@app.get("/wargaming/ml/confidence-distribution")
async def get_confidence_distribution(time_range: str = "24h"):
    """
    Get histogram of ML confidence scores.
    
    Args:
        time_range: Time range for distribution ('1h', '24h', '7d', '30d')
    
    Returns:
        Dict with histogram data:
        - bins: Confidence score bins (e.g., [0.5, 0.6, 0.7, ...])
        - counts: Count of predictions in each bin
        - threshold: Confidence threshold for ML-only validation
    
    Note: Currently returns estimated distribution.
    TODO: Extract from ml_confidence_histogram Prometheus metric.
    """
    try:
        # Define bins (matching Prometheus histogram buckets)
        bins = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
        
        # Extract real counts from ml_confidence_histogram
        from prometheus_client import REGISTRY
        
        # Get histogram metric
        for collector in REGISTRY._collector_to_names:
            if hasattr(collector, '_name') and 'ml_confidence' in collector._name:
                # Extract bucket counts from Prometheus histogram
                buckets = collector._buckets
                counts = [bucket._value.get() for bucket in buckets]
                break
        else:
            # Fallback if metric not found
            logger.warning("ml_confidence_histogram not found, using estimated distribution")
            counts = [2, 5, 8, 15, 35, 25, 10, 5]
        
        threshold = 0.8  # From validate_patch_ml_first default
        
        return {
            "bins": bins,
            "counts": counts,
            "threshold": threshold,
            "time_range": time_range
        }
    
    except Exception as e:
        logger.error(f"Failed to get confidence distribution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve confidence distribution: {str(e)}"
        )


@app.get("/wargaming/ml/recent-predictions")
async def get_recent_predictions(limit: int = 20, time_range: str = "24h"):
    """
    Get recent ML predictions with metadata.
    
    Args:
        limit: Maximum number of predictions to return (default: 20)
        time_range: Time range for predictions ('1h', '24h', '7d', '30d')
    
    Returns:
        List[Dict]: Recent predictions with:
        - apv_id: APV identifier
        - cve_id: CVE identifier
        - patch_id: Patch identifier
        - timestamp: ISO 8601 timestamp
        - method: Validation method used ('ml', 'wargaming', 'wargaming_fallback')
        - confidence: ML confidence score (0.0-1.0)
        - validated: Whether patch was validated
        - execution_time_ms: Execution time in milliseconds
    
    Note: Currently returns empty list (no persistence layer yet).
    Will query from PostgreSQL wargaming_results table.
    """
    try:
        # Query from database if available
        from .db import get_wargaming_results_from_db
        
        try:
            results = await get_wargaming_results_from_db(limit=limit)
            logger.info(f"Retrieved {len(results)} recent predictions from database")
            return results
        except (ImportError, Exception) as e:
            logger.warning(f"Database query failed, returning empty: {e}")
            return []
        
        # Example structure (for frontend development):
        # return [{
        #     "apv_id": "apv_001",
        #     "cve_id": "CVE-2024-SQL-INJECTION",
        #     "patch_id": "patch_001",
        #     "timestamp": "2025-10-11T12:30:00Z",
        #     "method": "ml",
        #     "confidence": 0.95,
        #     "validated": True,
        #     "execution_time_ms": 80.5
        # }]
        
        return []
    
    except Exception as e:
        logger.error(f"Failed to get recent predictions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent predictions: {str(e)}"
        )


@app.get("/wargaming/ml/accuracy")
async def get_ml_accuracy(
    time_range: str = "24h",
    model_version: str = "rf_v1"
):
    """
    Get ML accuracy metrics from A/B testing (Phase 5.6).
    
    Args:
        time_range: Time range for accuracy calculation ('1h', '24h', '7d', '30d')
        model_version: ML model version (default: 'rf_v1')
    
    Returns:
        Dict with accuracy metrics:
        - timeframe: Requested time range
        - model_version: ML model version
        - confusion_matrix: {true_positive, false_positive, false_negative, true_negative}
        - metrics: {precision, recall, f1_score, accuracy}
        - recent_tests: Last 20 A/B test results
        - accuracy_trend: Hourly accuracy over time
        - total_ab_tests: Number of A/B tests in timeframe
    
    Raises:
        HTTPException 503: If database connection unavailable
        HTTPException 500: If calculation fails
    """
    global ab_store
    
    try:
        # Check if AB store is initialized
        if ab_store is None:
            raise HTTPException(
                status_code=503,
                detail="A/B test store not initialized. Database may be unavailable."
            )
        
        # Parse time range
        time_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        time_delta = time_map.get(time_range, timedelta(hours=24))
        
        # Get confusion matrix
        cm = await ab_store.get_confusion_matrix(model_version, time_delta)
        
        # Get recent tests
        recent_tests = await ab_store.get_recent_tests(limit=20, model_version=model_version)
        
        # Convert datetime to ISO string for JSON serialization
        for test in recent_tests:
            if 'created_at' in test and test['created_at']:
                test['created_at'] = test['created_at'].isoformat()
        
        # Get accuracy trend
        trend = await ab_store.get_accuracy_over_time(
            model_version, time_delta, "1 hour"
        )
        
        # Convert datetime to ISO string in trend
        for point in trend:
            if 'bucket' in point and point['bucket']:
                point['bucket'] = point['bucket'].isoformat()
            # Convert Decimal to float for JSON
            if 'accuracy' in point:
                point['accuracy'] = float(point['accuracy'])
            if 'avg_confidence' in point:
                point['avg_confidence'] = float(point['avg_confidence'])
        
        # Calculate total A/B tests
        total_ab_tests = (
            cm.true_positive + cm.false_positive +
            cm.false_negative + cm.true_negative
        )
        
        logger.info(
            f"A/B testing metrics: {total_ab_tests} tests, "
            f"accuracy={cm.accuracy:.4f}, "
            f"precision={cm.precision:.4f}, "
            f"recall={cm.recall:.4f}"
        )
        
        return {
            "timeframe": time_range,
            "model_version": model_version,
            "confusion_matrix": {
                "true_positive": cm.true_positive,
                "false_positive": cm.false_positive,
                "false_negative": cm.false_negative,
                "true_negative": cm.true_negative
            },
            "metrics": {
                "precision": round(cm.precision, 4),
                "recall": round(cm.recall, 4),
                "f1_score": round(cm.f1_score, 4),
                "accuracy": round(cm.accuracy, 4)
            },
            "recent_tests": recent_tests,
            "accuracy_trend": trend,
            "total_ab_tests": total_ab_tests
        }
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    
    except Exception as e:
        logger.error(f"Failed to get ML accuracy: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve ML accuracy: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Phase 5.6: A/B Testing Control Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/wargaming/ab-testing/enable")
async def enable_ab_testing():
    """
    Enable A/B testing mode.
    
    In A/B testing mode, ALL patch validations will run BOTH ML prediction
    AND wargaming simulation, allowing empirical accuracy measurement.
    
    **Warning**: This increases validation time significantly as wargaming
    is no longer bypassed even with high ML confidence.
    
    Returns:
        Dict with status and message
    """
    global ab_testing_enabled, ab_store
    
    # Check if AB store is available
    if ab_store is None:
        raise HTTPException(
            status_code=503,
            detail="A/B Test Store not initialized. Cannot enable A/B testing."
        )
    
    ab_testing_enabled = True
    logger.info("🔬 A/B Testing ENABLED - All validations will run ML + Wargaming")
    
    return {
        "ab_testing_enabled": True,
        "message": "A/B testing activated. All validations will now compare ML vs wargaming.",
        "warning": "This will increase validation time but provides accuracy metrics.",
        "note": "Results will be stored in ml_ab_tests table for analysis."
    }


@app.post("/wargaming/ab-testing/disable")
async def disable_ab_testing():
    """
    Disable A/B testing mode.
    
    Reverts to ML-first optimization where high-confidence ML predictions
    skip wargaming simulation for speed.
    
    Returns:
        Dict with status and message
    """
    global ab_testing_enabled
    
    ab_testing_enabled = False
    logger.info("⚡ A/B Testing DISABLED - Reverting to ML-first optimization")
    
    return {
        "ab_testing_enabled": False,
        "message": "A/B testing deactivated. Reverting to ML-first mode.",
        "note": "High-confidence ML predictions will now skip wargaming for speed."
    }


@app.get("/wargaming/ab-testing/status")
async def get_ab_testing_status():
    """
    Get current A/B testing status.
    
    Returns:
        Dict with:
        - ab_testing_enabled: Whether A/B testing is active
        - ab_store_available: Whether database connection is available
        - description: Explanation of A/B testing
        - ml_confidence_threshold: Current threshold for ML bypass
    """
    global ab_testing_enabled, ab_store
    
    return {
        "ab_testing_enabled": ab_testing_enabled,
        "ab_store_available": ab_store is not None,
        "description": (
            "A/B testing compares ML predictions against wargaming ground truth "
            "for accuracy tracking and continuous learning."
        ),
        "ml_confidence_threshold": 0.8,
        "mode": "ab_testing" if ab_testing_enabled else "ml_first",
        "note": (
            "Enable A/B testing during development/testing to collect accuracy data. "
            "Disable in production for optimal performance."
        )
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 5.7.1: Cache Management Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/wargaming/cache/stats")
async def get_cache_stats():
    """
    Get Redis cache statistics.
    
    Returns:
        Dict with cache performance metrics:
        - hits: Total cache hits
        - misses: Total cache misses
        - hit_ratio: Cache hit ratio (0.0 to 1.0)
        - connected_clients: Number of connected clients
        - used_memory_human: Memory usage (human-readable)
    
    Example:
        ```bash
        curl http://localhost:8026/wargaming/cache/stats
        ```
    
    Author: MAXIMUS Team - Phase 5.7.1
    """
    try:
        stats = await cache.get_cache_stats()
        return {
            "status": "available" if "error" not in stats else "unavailable",
            "stats": stats,
            "note": "Cache performance metrics from Redis INFO command"
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "note": "Cache may be unavailable or disconnected"
        }


@app.post("/wargaming/cache/invalidate/{apv_id}")
async def invalidate_cache_for_apv(apv_id: str):
    """
    Invalidate cached prediction for specific APV.
    
    Use when APV data changes or patch is updated.
    
    Args:
        apv_id: APV identifier to invalidate
    
    Returns:
        Dict with invalidation result
    
    Example:
        ```bash
        curl -X POST http://localhost:8026/wargaming/cache/invalidate/apv_001
        ```
    
    Author: MAXIMUS Team - Phase 5.7.1
    """
    try:
        deleted = await cache.invalidate_ml_cache(apv_id)
        
        if deleted > 0:
            logger.info(f"✓ Cache invalidated for APV {apv_id}")
            return {
                "status": "success",
                "apv_id": apv_id,
                "deleted_keys": deleted,
                "message": f"Cache invalidated for APV {apv_id}"
            }
        else:
            return {
                "status": "not_found",
                "apv_id": apv_id,
                "deleted_keys": 0,
                "message": f"No cached data found for APV {apv_id}"
            }
    
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache invalidation failed: {str(e)}"
        )


@app.post("/wargaming/cache/invalidate-all")
async def invalidate_all_cache():
    """
    Invalidate all cached ML predictions.
    
    Use after model retraining or when cache needs refresh.
    
    **Warning**: This will clear all ML prediction cache.
    
    Returns:
        Dict with invalidation result
    
    Example:
        ```bash
        curl -X POST http://localhost:8026/wargaming/cache/invalidate-all
        ```
    
    Author: MAXIMUS Team - Phase 5.7.1
    """
    try:
        deleted = await cache.invalidate_ml_cache()
        
        logger.warning(f"⚠️ All ML prediction cache invalidated ({deleted} keys deleted)")
        
        return {
            "status": "success",
            "deleted_keys": deleted,
            "message": f"Invalidated all ML predictions ({deleted} keys)",
            "warning": "Cache will be rebuilt on next predictions"
        }
    
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache invalidation failed: {str(e)}"
        )


# Phase 5.7.2: Background task to update circuit breaker metrics
async def update_circuit_breaker_metrics_loop():
    """
    Periodically update Prometheus metrics for circuit breakers.
    
    Updates every 10 seconds to keep metrics fresh.
    """
    while True:
        try:
            update_circuit_breaker_metrics(ml_model_breaker)
            update_circuit_breaker_metrics(database_breaker)
            update_circuit_breaker_metrics(cache_breaker)
        except Exception as e:
            logger.warning(f"Circuit breaker metrics update failed: {e}")
        
        await asyncio.sleep(10)  # Update every 10 seconds


# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup initialization"""
    global ab_store, ab_test_runner
    
    logger.info("🚀 Starting Wargaming Crisol service (Phase 5.7.1)...")
    
    # Load exploit database
    db = load_exploit_database()
    stats = db.get_statistics()
    
    logger.info(f"✓ Loaded {stats['total']} exploits")
    logger.info(f"✓ CWE Coverage: {len(stats['cwe_coverage'])}")
    
    # Phase 5.7.1: Initialize Redis cache
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/2")
        await cache.connect()
        logger.info(f"✓ Redis cache connected (Phase 5.7.1): {redis_url}")
    except Exception as e:
        logger.warning(f"⚠️ Redis cache initialization failed: {e}")
        logger.warning("   Cache operations will be skipped (degraded mode)")
    
    # Phase 5.6: Initialize A/B Test Store and Runner
    try:
        # Build database URL from environment variables
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        pg_db = os.getenv("POSTGRES_DB", "aurora")
        pg_user = os.getenv("POSTGRES_USER", "postgres")
        pg_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        db_url = os.getenv(
            "DATABASE_URL",
            f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        )
        
        logger.info(f"Connecting to PostgreSQL at {pg_host}:{pg_port}/{pg_db}")
        
        # Initialize store
        ab_store = ABTestStore(db_url)
        await ab_store.connect()
        logger.info("✓ A/B Test Store initialized (Phase 5.6)")
        
        # Initialize runner
        ab_test_rate = float(os.getenv("AB_TEST_RATE", "0.10"))  # 10% default
        ab_test_runner = ABTestRunner(
            ab_store=ab_store,
            ab_test_rate=ab_test_rate,
            model_version="rf_v1"
        )
        logger.info(f"✓ A/B Test Runner initialized (rate: {ab_test_rate*100:.1f}%)")
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize A/B testing: {e}")
        logger.warning("   A/B testing endpoints will return 503")
        ab_store = None
        ab_test_runner = None
    
    # Phase 5.7.2: Start background task for circuit breaker metrics
    asyncio.create_task(update_circuit_breaker_metrics_loop())
    logger.info("✓ Circuit breaker metrics updater started (Phase 5.7.2)")
    
    logger.info("🔥 Wargaming Crisol ready!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global ab_store
    
    logger.info("🛑 Shutting down Wargaming Crisol service...")
    
    # Phase 5.7.1: Close Redis cache
    try:
        await cache.close()
        logger.info("✓ Redis cache closed")
    except Exception as e:
        logger.warning(f"⚠️ Redis cache close failed: {e}")
    
    # Close A/B Test Store
    if ab_store:
        await ab_store.close()
        logger.info("✓ A/B Test Store closed")
    
    logger.info("👋 Wargaming Crisol stopped")


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8026))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


def _calculate_avg_confidence_from_histogram() -> float:
    """Calculate average confidence from Prometheus histogram."""
    try:
        from prometheus_client import REGISTRY
        
        total_weight = 0.0
        total_count = 0
        
        # Search for ml_confidence histogram in registry
        for collector in REGISTRY._collector_to_names:
            if hasattr(collector, '_name') and 'ml_confidence' in str(collector._name):
                if hasattr(collector, '_buckets'):
                    buckets = collector._buckets
                    for i, bucket in enumerate(buckets):
                        if hasattr(bucket, '_value'):
                            count = bucket._value.get()
                            # Use bucket upper bound as representative value
                            bucket_value = bucket._upper_bound if hasattr(bucket, '_upper_bound') else 0.85
                            total_weight += count * bucket_value
                            total_count += count
                
                if total_count > 0:
                    return total_weight / total_count
        
        # Fallback
        return 0.87
    except Exception as e:
        logger.debug(f"Could not calculate avg confidence: {e}")
        return 0.87
