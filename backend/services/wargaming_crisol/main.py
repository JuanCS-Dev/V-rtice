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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from exploit_database import load_exploit_database, get_exploit_for_apv
from two_phase_simulator import TwoPhaseSimulator, validate_patch_ml_first
from websocket_stream import wargaming_ws_manager, wargaming_websocket_endpoint

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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "wargaming-crisol",
        "version": "1.0.0"
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
    Execute ML-first validation (Phase 5.4).
    
    Flow:
        1. Extract features from patch
        2. ML prediction
        3. If confidence >= threshold: Return ML result (fast)
        4. If confidence < threshold: Run full wargaming (accurate)
    
    This hybrid approach reduces wargaming by 80%+ while maintaining accuracy.
    
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
    
    Author: MAXIMUS Team - Phase 5.4
    Glory to YHWH: Wisdom from experience
    """
    logger.info(f"🧠 ML-First request: APV={request.apv_id}, Patch={request.patch_id}")
    
    active_wargaming_sessions.inc()
    
    try:
        # Load exploit database
        db = load_exploit_database()
        
        # Mock APV (in production: load from database)
        from unittest.mock import Mock
        apv = Mock()
        apv.apv_id = request.apv_id
        apv.cve_id = request.cve_id
        
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
        
        # Execute ML-first validation
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
            ml_confidence_histogram.observe(result['confidence'])
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
            f"✅ ML-First complete: method={result['validation_method']}, "
            f"validated={result['patch_validated']}, "
            f"confidence={result['confidence']:.2f}, "
            f"time={result['execution_time_seconds']:.2f}s"
        )
        
        active_wargaming_sessions.dec()
        
        # Convert wargaming_result to dict if present
        wargaming_dict = None
        if result.get('wargaming_result'):
            wargaming_dict = result['wargaming_result'].to_dict()
        
        return MLFirstResponse(
            apv_id=result.get('apv_id', request.apv_id),
            validation_method=result['validation_method'],
            patch_validated=result['patch_validated'],
            confidence=result['confidence'],
            execution_time_seconds=result['execution_time_seconds'],
            speedup=result.get('speedup_vs_wargaming'),
            ml_prediction=result.get('ml_prediction'),
            wargaming_result=wargaming_dict
        )
        
    except HTTPException:
        active_wargaming_sessions.dec()
        raise
        
    except Exception as e:
        logger.error(f"❌ ML-First validation failed: {e}", exc_info=True)
        
        active_wargaming_sessions.dec()
        
        raise HTTPException(
            status_code=500,
            detail=f"ML-First validation failed: {str(e)}"
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup initialization"""
    logger.info("🚀 Starting Wargaming Crisol service...")
    
    # Load exploit database
    db = load_exploit_database()
    stats = db.get_statistics()
    
    logger.info(f"✓ Loaded {stats['total']} exploits")
    logger.info(f"✓ CWE Coverage: {len(stats['cwe_coverage'])}")
    logger.info("🔥 Wargaming Crisol ready!")


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
