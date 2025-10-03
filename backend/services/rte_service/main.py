"""
RTE Service - Reflex Triage Engine
===================================
Ultra-fast threat detection and autonomous response.

Architecture:
- Hyperscan pattern matching (<10ms)
- Fast ML models (Isolation Forest + VAE) (<10ms)
- Fusion engine (decision logic) (<5ms)
- Autonomous playbooks (<5ms execution)

Target latency: <50ms end-to-end (p99)

API Endpoints:
- POST /detect - Analyze event and execute response
- GET /health - Health check
- GET /stats - Performance statistics
- POST /reload-patterns - Hot-reload Hyperscan patterns
"""

import logging
import time
import asyncio
from typing import Dict, Optional, List
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from hyperscan_matcher import HyperscanMatcher
from fast_ml import FastMLEngine
from fusion_engine import FusionEngine, ThreatAction, FusionResult
from playbooks import PlaybookExecutor, PlaybookResult

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PATTERNS_FILE = Path("/app/patterns/threat_patterns.json")
ML_MODEL_DIR = Path("/app/models")
QUARANTINE_DIR = "/var/quarantine"
DRY_RUN = False  # Set to True for testing without actual execution
ENABLE_ROLLBACK = True


# ============================================================================
# Request/Response Models
# ============================================================================

class DetectionRequest(BaseModel):
    """Request for threat detection"""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: float = Field(..., description="Event timestamp (Unix epoch)")

    # Raw data for pattern matching
    payload: str = Field(..., description="Raw payload data (base64 or UTF-8)")

    # Event metadata for ML features
    metadata: Dict = Field(
        default_factory=dict,
        description="Event metadata (packet_size, protocol, etc.)"
    )

    # Optional context
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "event_id": "evt_123456",
                "timestamp": 1704067200.0,
                "payload": "SELECT * FROM users WHERE 1=1",
                "metadata": {
                    "packet_size": 512,
                    "packet_count": 10,
                    "bytes_sent": 5120,
                    "protocol": "TCP",
                    "payload_entropy": 4.5
                },
                "source_ip": "192.168.1.100",
                "destination_port": 3306,
                "protocol": "tcp"
            }
        }


class DetectionResponse(BaseModel):
    """Response from threat detection"""
    event_id: str
    action: str  # BLOCK, INVESTIGATE, ALLOW, QUARANTINE
    confidence: float
    threat_level: str
    reasoning: str

    # Detection details
    hyperscan_matches: int
    ml_anomaly_detected: bool
    ml_anomaly_score: Optional[float] = None

    # Playbook execution
    playbooks_executed: List[str] = []
    playbook_results: List[Dict] = []

    # Performance
    latency_ms: float
    latency_breakdown: Dict[str, float]


class StatsResponse(BaseModel):
    """Service statistics"""
    total_detections: int
    detections_by_action: Dict[str, int]
    avg_latency_ms: float
    p99_latency_ms: float

    hyperscan_stats: Dict
    playbook_stats: Dict

    uptime_seconds: float


# ============================================================================
# Global State
# ============================================================================

class RTEState:
    """Global RTE service state"""
    def __init__(self):
        self.hyperscan: Optional[HyperscanMatcher] = None
        self.ml_engine: Optional[FastMLEngine] = None
        self.fusion: Optional[FusionEngine] = None
        self.playbook_executor: Optional[PlaybookExecutor] = None

        self.start_time = time.time()
        self.detection_count = 0
        self.latencies: List[float] = []
        self.actions_count: Dict[str, int] = {
            "BLOCK": 0,
            "INVESTIGATE": 0,
            "ALLOW": 0,
            "QUARANTINE": 0
        }


rte_state = RTEState()


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup RTE components"""
    logger.info("="*80)
    logger.info("RTE SERVICE STARTING")
    logger.info("="*80)

    # Initialize components
    try:
        # 1. Hyperscan pattern matcher
        logger.info("Loading Hyperscan patterns...")
        if not PATTERNS_FILE.exists():
            logger.warning(f"Pattern file not found: {PATTERNS_FILE}")
            logger.info("Creating default patterns for testing...")
            _create_default_patterns(PATTERNS_FILE)

        rte_state.hyperscan = HyperscanMatcher(PATTERNS_FILE)
        logger.info(f"✓ Hyperscan loaded: {len(rte_state.hyperscan.patterns)} patterns")

        # 2. ML Engine
        logger.info("Initializing ML engine...")
        rte_state.ml_engine = FastMLEngine()

        # Try to load pre-trained models
        if_model_path = ML_MODEL_DIR / "isolation_forest.joblib"
        vae_model_path = ML_MODEL_DIR / "vae_model.pt"

        if if_model_path.exists() and vae_model_path.exists():
            rte_state.ml_engine.load_models(str(ML_MODEL_DIR))
            logger.info("✓ Pre-trained ML models loaded")
        else:
            logger.warning("No pre-trained models found - will use untrained models")
            logger.info("Train models by sending normal traffic samples")

        # 3. Fusion Engine
        logger.info("Initializing Fusion Engine...")
        rte_state.fusion = FusionEngine(
            hyperscan_matcher=rte_state.hyperscan,
            ml_engine=rte_state.ml_engine
        )
        logger.info("✓ Fusion Engine initialized")

        # 4. Playbook Executor
        logger.info("Initializing Playbook Executor...")
        rte_state.playbook_executor = PlaybookExecutor(
            dry_run=DRY_RUN,
            enable_rollback=ENABLE_ROLLBACK
        )
        logger.info(f"✓ Playbook Executor initialized (dry_run={DRY_RUN})")

        logger.info("="*80)
        logger.info("RTE SERVICE READY")
        logger.info("="*80)

        yield

        # Cleanup
        logger.info("RTE SERVICE SHUTTING DOWN")

    except Exception as e:
        logger.error(f"Failed to initialize RTE: {e}")
        raise


def _create_default_patterns(output_file: Path):
    """Create default threat patterns for testing"""
    import json

    default_patterns = [
        {
            "id": 1,
            "pattern": "malware.*\\.exe",
            "flags": ["CASELESS"],
            "metadata": {
                "severity": "critical",
                "category": "malware",
                "description": "Malware executable detection"
            }
        },
        {
            "id": 2,
            "pattern": "SELECT.*FROM.*WHERE",
            "flags": ["CASELESS"],
            "metadata": {
                "severity": "high",
                "category": "sqli",
                "description": "SQL injection attempt"
            }
        },
        {
            "id": 3,
            "pattern": "<script[^>]*>.*</script>",
            "flags": ["CASELESS", "DOTALL"],
            "metadata": {
                "severity": "high",
                "category": "xss",
                "description": "XSS attempt"
            }
        },
        {
            "id": 4,
            "pattern": "cmd\\.exe|powershell\\.exe|/bin/bash",
            "flags": ["CASELESS"],
            "metadata": {
                "severity": "critical",
                "category": "rce",
                "description": "Remote code execution attempt"
            }
        },
        {
            "id": 5,
            "pattern": "\\.\\./|\\.\\.\\\\",
            "flags": [],
            "metadata": {
                "severity": "medium",
                "category": "path_traversal",
                "description": "Path traversal attempt"
            }
        }
    ]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(default_patterns, f, indent=2)


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="RTE Service - Reflex Triage Engine",
    description="Ultra-fast threat detection and autonomous response (<50ms)",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/detect", response_model=DetectionResponse)
async def detect_threat(
    request: DetectionRequest,
    background_tasks: BackgroundTasks
) -> DetectionResponse:
    """
    Detect threats and execute autonomous response.

    Pipeline:
    1. Hyperscan pattern matching
    2. ML anomaly detection
    3. Fusion engine decision
    4. Autonomous playbook execution

    Target latency: <50ms (p99)
    """
    start_time = time.time()
    latency_breakdown = {}

    try:
        # Convert payload to bytes
        payload_bytes = request.payload.encode('utf-8')

        # Phase 1: Fusion Engine Analysis
        fusion_start = time.time()

        fusion_result: FusionResult = rte_state.fusion.analyze(
            data=payload_bytes,
            event_metadata=request.metadata
        )

        latency_breakdown["fusion_analysis_ms"] = (time.time() - fusion_start) * 1000

        # Phase 2: Autonomous Playbook Execution
        playbooks_executed = []
        playbook_results = []

        if fusion_result.action in [ThreatAction.BLOCK, ThreatAction.QUARANTINE]:
            playbook_start = time.time()

            # Execute appropriate playbooks based on action
            playbook_tasks = _determine_playbooks(fusion_result, request)

            for task in playbook_tasks:
                try:
                    result: PlaybookResult = await rte_state.playbook_executor.execute(
                        playbook_name=task["playbook"],
                        params=task["params"]
                    )

                    playbooks_executed.append(result.playbook_name)
                    playbook_results.append({
                        "playbook": result.playbook_name,
                        "status": result.status,
                        "actions": result.actions_taken,
                        "execution_time_ms": result.execution_time_ms
                    })

                except Exception as e:
                    logger.error(f"Playbook {task['playbook']} failed: {e}")
                    playbook_results.append({
                        "playbook": task["playbook"],
                        "status": "FAILED",
                        "error": str(e)
                    })

            latency_breakdown["playbook_execution_ms"] = (time.time() - playbook_start) * 1000

        # Calculate total latency
        total_latency_ms = (time.time() - start_time) * 1000

        # Update statistics
        rte_state.detection_count += 1
        rte_state.latencies.append(total_latency_ms)
        rte_state.actions_count[fusion_result.action] += 1

        # Keep only last 10000 latencies for stats
        if len(rte_state.latencies) > 10000:
            rte_state.latencies = rte_state.latencies[-10000:]

        # Build response
        response = DetectionResponse(
            event_id=request.event_id,
            action=fusion_result.action,
            confidence=fusion_result.confidence,
            threat_level=fusion_result.threat_level,
            reasoning=fusion_result.reasoning,
            hyperscan_matches=len(fusion_result.hyperscan_matches),
            ml_anomaly_detected=fusion_result.ml_score.is_anomaly if fusion_result.ml_score else False,
            ml_anomaly_score=fusion_result.ml_score.anomaly_score if fusion_result.ml_score else None,
            playbooks_executed=playbooks_executed,
            playbook_results=playbook_results,
            latency_ms=total_latency_ms,
            latency_breakdown=latency_breakdown
        )

        # Log detection
        logger.info(
            f"Detection {request.event_id}: {fusion_result.action} "
            f"(confidence={fusion_result.confidence:.2f}, latency={total_latency_ms:.2f}ms)"
        )

        return response

    except Exception as e:
        logger.error(f"Detection failed for {request.event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _determine_playbooks(
    fusion_result: FusionResult,
    request: DetectionRequest
) -> List[Dict]:
    """
    Determine which playbooks to execute based on detection result.

    Returns:
        List of playbook tasks: [{"playbook": str, "params": dict}, ...]
    """
    tasks = []

    # BLOCK action
    if fusion_result.action == ThreatAction.BLOCK:
        # Block source IP if available
        if request.source_ip:
            tasks.append({
                "playbook": "block_ip",
                "params": {
                    "ip_address": request.source_ip,
                    "protocol": request.protocol or "tcp",
                    "port": request.destination_port,
                    "duration_seconds": 3600  # 1 hour
                }
            })

        # Check if it's a malware pattern -> quarantine if file path in metadata
        if fusion_result.hyperscan_matches:
            for match in fusion_result.hyperscan_matches:
                if match.metadata.get("category") == "malware":
                    # If metadata has file_path, quarantine it
                    if "file_path" in request.metadata:
                        tasks.append({
                            "playbook": "quarantine_file",
                            "params": {
                                "file_path": request.metadata["file_path"],
                                "quarantine_dir": QUARANTINE_DIR
                            }
                        })

    # QUARANTINE action
    elif fusion_result.action == ThreatAction.QUARANTINE:
        # Isolate host if pod information available
        if "pod_name" in request.metadata and "namespace" in request.metadata:
            tasks.append({
                "playbook": "isolate_host",
                "params": {
                    "namespace": request.metadata["namespace"],
                    "pod_name": request.metadata["pod_name"],
                    "isolation_type": "full"
                }
            })

        # Redirect to honeypot
        if request.source_ip and "honeypot_ip" in request.metadata:
            tasks.append({
                "playbook": "redirect_honeypot",
                "params": {
                    "source_ip": request.source_ip,
                    "honeypot_ip": request.metadata["honeypot_ip"],
                    "honeypot_port": request.metadata.get("honeypot_port", 8080),
                    "protocol": request.protocol or "tcp"
                }
            })

    return tasks


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rte_service",
        "uptime_seconds": time.time() - rte_state.start_time,
        "detections_processed": rte_state.detection_count
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Get service statistics"""

    # Calculate p99 latency
    sorted_latencies = sorted(rte_state.latencies)
    p99_index = int(len(sorted_latencies) * 0.99)
    p99_latency = sorted_latencies[p99_index] if sorted_latencies else 0.0

    avg_latency = sum(rte_state.latencies) / len(rte_state.latencies) if rte_state.latencies else 0.0

    return StatsResponse(
        total_detections=rte_state.detection_count,
        detections_by_action=rte_state.actions_count,
        avg_latency_ms=avg_latency,
        p99_latency_ms=p99_latency,
        hyperscan_stats=rte_state.hyperscan.get_stats(),
        playbook_stats=rte_state.playbook_executor.get_stats(),
        uptime_seconds=time.time() - rte_state.start_time
    )


@app.post("/reload-patterns")
async def reload_patterns():
    """Hot-reload Hyperscan patterns"""
    try:
        if not PATTERNS_FILE.exists():
            raise HTTPException(status_code=404, detail="Pattern file not found")

        logger.info("Hot-reloading Hyperscan patterns...")
        rte_state.hyperscan.reload_patterns(PATTERNS_FILE)

        return {
            "status": "success",
            "message": f"Reloaded {len(rte_state.hyperscan.patterns)} patterns"
        }
    except Exception as e:
        logger.error(f"Failed to reload patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train-ml")
async def train_ml_models(normal_events: List[Dict]):
    """
    Train ML models on normal traffic samples.

    Send 500-1000 samples of normal traffic to establish baseline.
    """
    try:
        logger.info(f"Training ML models on {len(normal_events)} samples...")

        rte_state.ml_engine.train(normal_events)

        # Save models
        ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        rte_state.ml_engine.save_models(str(ML_MODEL_DIR))

        return {
            "status": "success",
            "message": f"Trained on {len(normal_events)} samples",
            "models_saved": str(ML_MODEL_DIR)
        }
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os

    # Configuration from environment
    HOST = os.getenv("RTE_HOST", "0.0.0.0")
    PORT = int(os.getenv("RTE_PORT", "8005"))

    logger.info(f"Starting RTE service on {HOST}:{PORT}")

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True
    )
