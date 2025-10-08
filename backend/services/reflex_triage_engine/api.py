"""Reflex Triage Engine - FastAPI Service

Ultra-fast threat triage <50ms with autonomous response.

Endpoints:
- POST /rte/scan - Scan event for threats
- POST /rte/scan-file - Scan file for malware
- POST /rte/reload-signatures - Hot-reload signatures
- GET /rte/stats - Get engine statistics
"""

import logging
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from autonomous_response import AutonomousResponseEngine, PlaybookAction
from fast_anomaly_detector import FastAnomalyDetector
from hyperscan_engine import HyperscanEngine
from reflex_fusion import ReflexFusionEngine, ThreatDecision

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Reflex Triage Engine",
    description="Ultra-fast threat detection and autonomous response <50ms",
    version="1.0.0",
)

# Initialize engines (global state)
hyperscan_engine: Optional[HyperscanEngine] = None
anomaly_detector: Optional[FastAnomalyDetector] = None
fusion_engine: Optional[ReflexFusionEngine] = None
response_engine: Optional[AutonomousResponseEngine] = None


# Pydantic models
class ScanRequest(BaseModel):
    """Scan request model."""

    event_data: str  # Base64 encoded or hex string
    event_metadata: Dict
    auto_respond: bool = False


class ScanResponse(BaseModel):
    """Scan response model."""

    decision: str
    confidence: float
    threat_score: float
    detections: Dict
    reasoning: List[str]
    latency_ms: float
    action_taken: Optional[Dict] = None


class ReloadRequest(BaseModel):
    """Reload signatures request."""

    signatures_path: str


@app.on_event("startup")
async def startup_event():
    """Initialize engines on startup."""
    global hyperscan_engine, anomaly_detector, fusion_engine, response_engine

    logger.info("Starting Reflex Triage Engine...")

    # Initialize Hyperscan
    hyperscan_engine = HyperscanEngine()

    # Load default signatures if available
    try:
        hyperscan_engine.load_signatures("/app/signatures/default_signatures.json")
        hyperscan_engine.compile_database()
    except Exception as e:
        logger.warning(f"Could not load default signatures: {e}")

    # Initialize Anomaly Detector
    anomaly_detector = FastAnomalyDetector()

    # Try to load pre-trained model
    try:
        anomaly_detector.load_model("/app/models/anomaly_detector.pkl")
    except Exception as e:
        logger.warning(f"Could not load anomaly model: {e}")

    # Initialize Fusion Engine
    fusion_engine = ReflexFusionEngine(
        hyperscan_engine=hyperscan_engine,
        anomaly_detector=anomaly_detector,
        vae_layer=None,  # Can integrate L1 VAE later
    )

    # Initialize Response Engine (dry-run by default)
    response_engine = AutonomousResponseEngine(dry_run_mode=True)

    logger.info("Reflex Triage Engine ready!")


@app.post("/rte/scan", response_model=ScanResponse)
async def scan_event(request: ScanRequest):
    """Scan event for threats.

    Args:
        request: Scan request with event data and metadata

    Returns:
        ScanResponse with triage decision
    """
    if not fusion_engine:
        raise HTTPException(status_code=503, detail="Engines not initialized")

    try:
        # Decode event data (assuming hex string)
        event_data = bytes.fromhex(request.event_data)

        # Perform triage
        result = fusion_engine.triage(event_data=event_data, event_metadata=request.event_metadata)

        # Autonomous response if requested and BLOCK decision
        action_result = None
        if request.auto_respond and result.decision == ThreatDecision.BLOCK:
            # Determine action based on threat type
            if "ip" in request.event_metadata:
                action_result = await response_engine.execute_playbook(
                    action=PlaybookAction.BLOCK_IP, target=request.event_metadata["ip"]
                )
            elif "process_id" in request.event_metadata:
                action_result = await response_engine.execute_playbook(
                    action=PlaybookAction.KILL_PROCESS,
                    target=str(request.event_metadata["process_id"]),
                    context=request.event_metadata,
                )

        return ScanResponse(
            decision=result.decision.value,
            confidence=result.confidence,
            threat_score=result.threat_score,
            detections=result.detections,
            reasoning=result.reasoning,
            latency_ms=result.latency_ms,
            action_taken=(
                {
                    "action": action_result.action.value,
                    "success": action_result.success,
                    "dry_run": action_result.dry_run,
                    "message": action_result.message,
                }
                if action_result
                else None
            ),
        )

    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rte/scan-file")
async def scan_file(file: UploadFile = File(...)):
    """Scan uploaded file for malware.

    Args:
        file: Uploaded file

    Returns:
        Scan results
    """
    if not fusion_engine:
        raise HTTPException(status_code=503, detail="Engines not initialized")

    try:
        # Read file content
        content = await file.read()

        # Create metadata
        metadata = {
            "filename": file.filename,
            "file_size": len(content),
            "content_type": file.content_type,
        }

        # Scan
        result = fusion_engine.triage(event_data=content, event_metadata=metadata)

        return {
            "filename": file.filename,
            "decision": result.decision.value,
            "confidence": result.confidence,
            "threat_score": result.threat_score,
            "detections": result.detections,
            "reasoning": result.reasoning,
            "latency_ms": result.latency_ms,
        }

    except Exception as e:
        logger.error(f"File scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rte/reload-signatures")
async def reload_signatures(request: ReloadRequest):
    """Hot-reload signatures from file.

    Args:
        request: Reload request with signatures path

    Returns:
        Success message
    """
    if not hyperscan_engine:
        raise HTTPException(status_code=503, detail="Hyperscan not initialized")

    try:
        hyperscan_engine.reload_signatures(request.signatures_path)

        return {
            "status": "success",
            "message": f"Signatures reloaded from {request.signatures_path}",
            "signatures_count": len(hyperscan_engine.signatures),
        }

    except Exception as e:
        logger.error(f"Reload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rte/stats")
async def get_statistics():
    """Get engine statistics.

    Returns:
        Statistics from all engines
    """
    if not all([hyperscan_engine, anomaly_detector, fusion_engine, response_engine]):
        raise HTTPException(status_code=503, detail="Engines not initialized")

    return {
        "hyperscan": hyperscan_engine.get_statistics(),
        "anomaly_detector": anomaly_detector.get_statistics(),
        "fusion_engine": fusion_engine.get_statistics(),
        "autonomous_response": response_engine.get_statistics(),
    }


@app.post("/rte/response/enable-production")
async def enable_production_mode():
    """Enable production mode (disable dry-run).

    ⚠️ WARNING: This enables real autonomous actions!

    Returns:
        Confirmation message
    """
    if not response_engine:
        raise HTTPException(status_code=503, detail="Response engine not initialized")

    response_engine.enable_production_mode()

    return {
        "status": "warning",
        "message": "⚠️ PRODUCTION MODE ENABLED - Real autonomous actions will be executed!",
        "dry_run_mode": response_engine.dry_run_mode,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "reflex_triage_engine",
        "engines_initialized": all([hyperscan_engine, anomaly_detector, fusion_engine, response_engine]),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, log_level="info", reload=False)
