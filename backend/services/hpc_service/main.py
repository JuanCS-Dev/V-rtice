"""
hPC Service - Hierarchical Predictive Coding Network
=====================================================
Bayesian threat prediction and active inference.

Endpoints:
- POST /predict - Generate threat prediction
- POST /observe - Process observation and update beliefs
- POST /infer - Run active inference (autonomous threat hunting)
- POST /train - Train prior distribution
- GET /beliefs - Get current belief state
- GET /stats - Performance statistics
- GET /health - Health check
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import numpy as np

from bayesian_core import (
    BayesianCore, Observation, Prediction,
    PredictionError, BeliefState, ThreatLevel
)
from active_inference import (
    ActiveInferenceEngine, Action, ActionResult,
    InferenceState, ActionType
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
NUM_FEATURES = 30
HIERARCHY_LEVELS = 4
LEARNING_RATE = 0.1
EXPLORATION_BUDGET = 100.0

# ============================================================================
# Request/Response Models
# ============================================================================

class ObservationRequest(BaseModel):
    """Request to process observation"""
    timestamp: float = Field(..., description="Observation timestamp")
    features: List[float] = Field(..., description="Feature vector (30 features)")
    source_id: str = Field(..., description="Source identifier (IP, host, etc.)")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "timestamp": 1704067200.0,
                "features": [500.0] * 30,
                "source_id": "192.168.1.100",
                "metadata": {"protocol": "TCP", "port": 443}
            }
        }


class PredictionResponse(BaseModel):
    """Response from prediction"""
    predicted_features: List[float]
    predicted_variance: List[float]
    confidence: float
    threat_level: str
    threat_probabilities: Dict[str, float]
    reasoning: str


class ObservationResponse(BaseModel):
    """Response from observation processing"""
    prediction_error_magnitude: float
    surprise: float
    updated_threat_probabilities: Dict[str, float]
    updated_entropy: float
    belief_state: Dict


class InferenceRequest(BaseModel):
    """Request to run active inference"""
    initial_observation: Optional[ObservationRequest] = None
    exploration_budget: float = Field(default=50.0, description="Resource budget for exploration")
    information_threshold: float = Field(default=0.5, description="Stop when entropy below this")


class InferenceResponse(BaseModel):
    """Response from active inference"""
    iterations: int
    actions_executed: int
    total_information_gain: float
    final_entropy: float
    final_threat_probabilities: Dict[str, float]
    actions_summary: List[Dict]
    threats_discovered: int


class TrainingRequest(BaseModel):
    """Request to train prior"""
    observations: List[ObservationRequest] = Field(..., description="Normal traffic observations")


class StatsResponse(BaseModel):
    """Service statistics"""
    bayesian_core_stats: Dict
    active_inference_stats: Optional[Dict]
    uptime_seconds: float


# ============================================================================
# Global State
# ============================================================================

class HPCState:
    """Global hPC service state"""
    def __init__(self):
        self.bayesian_core: Optional[BayesianCore] = None
        self.active_inference: Optional[ActiveInferenceEngine] = None
        self.start_time = time.time()
        self.is_trained = False


hpc_state = HPCState()


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup hPC components"""
    logger.info("="*80)
    logger.info("hPC SERVICE STARTING - Hierarchical Predictive Coding")
    logger.info("="*80)

    try:
        # Initialize Bayesian core
        logger.info("Initializing Bayesian core...")
        hpc_state.bayesian_core = BayesianCore(
            num_features=NUM_FEATURES,
            hierarchy_levels=HIERARCHY_LEVELS,
            learning_rate=LEARNING_RATE
        )
        logger.info("✓ Bayesian core initialized")

        # Initialize active inference engine
        logger.info("Initializing active inference engine...")
        hpc_state.active_inference = ActiveInferenceEngine(
            bayesian_core=hpc_state.bayesian_core,
            exploration_budget=EXPLORATION_BUDGET
        )
        logger.info("✓ Active inference engine initialized")

        # Try to load pre-trained prior
        model_path = Path("/app/models/hpc_prior.npz")
        if model_path.exists():
            logger.info("Loading pre-trained prior...")
            data = np.load(str(model_path))
            hpc_state.bayesian_core.prior_mean = data['prior_mean']
            hpc_state.bayesian_core.prior_variance = data['prior_variance']
            hpc_state.is_trained = True
            logger.info("✓ Pre-trained prior loaded")
        else:
            logger.warning("No pre-trained prior found - send training data to /train")

        logger.info("="*80)
        logger.info("hPC SERVICE READY")
        logger.info("="*80)

        yield

        # Cleanup
        logger.info("hPC SERVICE SHUTTING DOWN")

    except Exception as e:
        logger.error(f"Failed to initialize hPC: {e}")
        raise


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="hPC Service - Hierarchical Predictive Coding",
    description="Bayesian threat prediction and active inference",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/predict", response_model=PredictionResponse)
async def predict(context: Optional[Dict] = None) -> PredictionResponse:
    """
    Generate top-down prediction based on current beliefs.

    Uses Bayesian inference to predict expected features.
    """
    if not hpc_state.is_trained:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Send training data to /train first."
        )

    try:
        prediction: Prediction = hpc_state.bayesian_core.predict(context=context)

        # Get current threat probabilities
        threat_probs = {}
        if hpc_state.bayesian_core.belief_state:
            threat_probs = {
                level.value: prob
                for level, prob in hpc_state.bayesian_core.belief_state.threat_probability.items()
            }

        return PredictionResponse(
            predicted_features=prediction.mean.tolist(),
            predicted_variance=prediction.variance.tolist(),
            confidence=prediction.confidence,
            threat_level=prediction.threat_level.value,
            threat_probabilities=threat_probs,
            reasoning=prediction.reasoning
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/observe", response_model=ObservationResponse)
async def observe(request: ObservationRequest) -> ObservationResponse:
    """
    Process observation through predictive coding cycle.

    1. Generate prediction
    2. Compute prediction error
    3. Update beliefs

    Returns updated belief state.
    """
    if not hpc_state.is_trained:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Send training data to /train first."
        )

    try:
        # Create observation
        observation = Observation(
            timestamp=request.timestamp,
            features=np.array(request.features),
            source_id=request.source_id,
            metadata=request.metadata
        )

        # Generate prediction
        prediction: Prediction = hpc_state.bayesian_core.predict()

        # Compute prediction error
        pred_error: PredictionError = hpc_state.bayesian_core.compute_prediction_error(
            observation, prediction
        )

        # Update beliefs
        new_belief: BeliefState = hpc_state.bayesian_core.update_beliefs(
            observation, pred_error
        )

        return ObservationResponse(
            prediction_error_magnitude=float(pred_error.magnitude),
            surprise=float(pred_error.surprise),
            updated_threat_probabilities={
                level.value: prob
                for level, prob in new_belief.threat_probability.items()
            },
            updated_entropy=new_belief.entropy,
            belief_state={
                "feature_distribution": {
                    k: {"mean": v[0], "std": v[1]}
                    for k, v in list(new_belief.feature_distribution.items())[:5]  # First 5
                },
                "precision_matrix_shape": new_belief.precision_matrix.shape,
                "timestamp": new_belief.timestamp
            }
        )

    except Exception as e:
        logger.error(f"Observation processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/infer", response_model=InferenceResponse)
async def infer(request: InferenceRequest) -> InferenceResponse:
    """
    Run active inference for autonomous threat hunting.

    The agent will:
    1. Identify high-uncertainty areas
    2. Plan actions to reduce uncertainty
    3. Execute actions and gather observations
    4. Update beliefs
    5. Repeat until budget exhausted or uncertainty minimized

    This can take several seconds depending on budget.
    """
    if not hpc_state.is_trained:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Send training data to /train first."
        )

    try:
        # Update engine parameters
        hpc_state.active_inference.exploration_budget = request.exploration_budget
        hpc_state.active_inference.information_threshold = request.information_threshold

        # Convert initial observation if provided
        initial_obs = None
        if request.initial_observation:
            initial_obs = Observation(
                timestamp=request.initial_observation.timestamp,
                features=np.array(request.initial_observation.features),
                source_id=request.initial_observation.source_id,
                metadata=request.initial_observation.metadata
            )

        # Run active inference
        logger.info("Starting active inference...")
        final_state: InferenceState = await hpc_state.active_inference.infer(
            initial_observation=initial_obs
        )

        # Build actions summary
        actions_summary = []
        for result in final_state.executed_actions:
            actions_summary.append({
                "action_type": result.action.action_type.value,
                "parameters": result.action.parameters,
                "success": result.success,
                "information_gained": result.information_gained,
                "execution_time_ms": result.execution_time_ms
            })

        return InferenceResponse(
            iterations=len(final_state.executed_actions),
            actions_executed=len(final_state.executed_actions),
            total_information_gain=final_state.total_information_gain,
            final_entropy=final_state.current_belief.entropy,
            final_threat_probabilities={
                level.value: prob
                for level, prob in final_state.current_belief.threat_probability.items()
            },
            actions_summary=actions_summary,
            threats_discovered=hpc_state.active_inference.stats["threats_discovered"]
        )

    except Exception as e:
        logger.error(f"Active inference failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train")
async def train(request: TrainingRequest):
    """
    Train prior distribution from normal traffic.

    Send 500-1000 observations of normal (benign) traffic.
    This establishes the baseline for prediction.
    """
    try:
        logger.info(f"Training prior on {len(request.observations)} observations...")

        # Convert to Observation objects
        observations = []
        for obs_req in request.observations:
            obs = Observation(
                timestamp=obs_req.timestamp,
                features=np.array(obs_req.features),
                source_id=obs_req.source_id,
                metadata=obs_req.metadata
            )
            observations.append(obs)

        # Learn prior
        hpc_state.bayesian_core.learn_prior(observations)
        hpc_state.is_trained = True

        # Save prior to disk
        model_path = Path("/app/models/hpc_prior.npz")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            str(model_path),
            prior_mean=hpc_state.bayesian_core.prior_mean,
            prior_variance=hpc_state.bayesian_core.prior_variance
        )

        logger.info(f"Prior trained and saved to {model_path}")

        return {
            "status": "success",
            "message": f"Trained on {len(observations)} observations",
            "prior_mean_sample": hpc_state.bayesian_core.prior_mean[:5].tolist(),
            "prior_variance_sample": hpc_state.bayesian_core.prior_variance[:5].tolist()
        }

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/beliefs")
async def get_beliefs():
    """Get current belief state"""
    if not hpc_state.is_trained or not hpc_state.bayesian_core.belief_state:
        raise HTTPException(status_code=400, detail="No belief state available")

    belief = hpc_state.bayesian_core.belief_state

    return {
        "threat_probabilities": {
            level.value: prob
            for level, prob in belief.threat_probability.items()
        },
        "entropy": belief.entropy,
        "feature_distribution_sample": {
            k: {"mean": v[0], "std": v[1]}
            for k, v in list(belief.feature_distribution.items())[:10]
        },
        "timestamp": belief.timestamp,
        "observation_history_size": len(hpc_state.bayesian_core.observation_history)
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Get service statistics"""
    bayesian_stats = hpc_state.bayesian_core.get_stats()

    active_inference_stats = None
    if hpc_state.active_inference and hpc_state.active_inference.state:
        active_inference_stats = hpc_state.active_inference.get_stats()

    return StatsResponse(
        bayesian_core_stats=bayesian_stats,
        active_inference_stats=active_inference_stats,
        uptime_seconds=time.time() - hpc_state.start_time
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "hpc_service",
        "is_trained": hpc_state.is_trained,
        "uptime_seconds": time.time() - hpc_state.start_time
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os

    HOST = os.getenv("HPC_HOST", "0.0.0.0")
    PORT = int(os.getenv("HPC_PORT", "8006"))

    logger.info(f"Starting hPC service on {HOST}:{PORT}")

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True
    )
