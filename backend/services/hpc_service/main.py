"""hPC Service - Hierarchical Predictive Coding Network (Main API).

This module provides the main FastAPI application for the hPC service. It exposes
endpoints for the core functionalities of the Bayesian network:

-   **/predict**: Generate a top-down prediction based on the current belief state.
-   **/observe**: Process a new observation, compute the prediction error, and
    update the model's beliefs.
-   **/infer**: Trigger the active inference loop for autonomous threat hunting.
-   **/train**: Train the model's prior beliefs on a dataset of normal traffic.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from active_inference import ActiveInferenceEngine
from bayesian_core import BayesianCore, Observation

# ============================================================================
# Configuration and Initialization
# ============================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

NUM_FEATURES = 30

state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application's lifespan for startup and shutdown events."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="hpc_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="hpc_service",
            version=service_version
        )
        auto_update_sabbath_status("hpc_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="hpc_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="hpc_service")
        logger.info("✅ Constitutional Health Checker initialized")

        # Routes
        if metrics_exporter:
            app.include_router(metrics_exporter.create_router())
            logger.info("✅ Constitutional metrics routes added")

    except Exception as e:
        logger.error(f"❌ Constitutional initialization failed: {e}", exc_info=True)

    # Mark startup complete
    if health_checker:
        health_checker.mark_startup_complete()

    logger.info("Starting hPC Service...")
    state["bayesian_core"] = BayesianCore(num_features=NUM_FEATURES)
    state["active_inference"] = ActiveInferenceEngine(state["bayesian_core"])
    logger.info("hPC components initialized.")
    yield
    logger.info("hPC Service shut down.")


app = FastAPI(
    title="hPC Service - Hierarchical Predictive Coding",
    description="A Bayesian threat prediction and active inference engine.",
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================================
# Pydantic Models
# ============================================================================


class ObservationRequest(BaseModel):
    """Request model for submitting a new observation."""

    features: List[float] = Field(..., min_items=NUM_FEATURES, max_items=NUM_FEATURES)
    source_id: str


class TrainingRequest(BaseModel):
    """Request model for training the model's prior beliefs."""

    observations: List[ObservationRequest]


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/health")
async def health_check():
    """Provides a basic health check of the service."""
    return {"status": "healthy", "service": "hpc_service"}


@app.post("/train")
async def train(request: TrainingRequest):
    """Trains the Bayesian core's prior beliefs on a dataset of normal observations."""
    core: BayesianCore = state["bayesian_core"]
    try:
        observations = [
            Observation(timestamp=0, features=np.array(obs.features), source_id=obs.source_id)
            for obs in request.observations
        ]
        core.learn_prior(observations)
        return {
            "status": "success",
            "message": f"Prior trained on {len(observations)} observations.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/observe")
async def observe(request: ObservationRequest):
    """Processes a single observation, updating the model's beliefs.

    This endpoint simulates one cycle of the predictive coding loop: predict,
    calculate error, and update.
    """
    core: BayesianCore = state["bayesian_core"]
    if not core.belief_state:
        raise HTTPException(
            status_code=400,
            detail="Model prior not trained. Please train first via /train.",
        )

    try:
        obs = Observation(
            timestamp=0,
            features=np.array(request.features),
            source_id=request.source_id,
        )
        prediction = core.predict()
        error = core.compute_prediction_error(obs, prediction)
        new_belief = core.update_beliefs(obs, error)
        return {
            "updated_entropy": new_belief.entropy,
            "prediction_error": error.magnitude,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/infer")
async def infer():
    """Triggers the active inference engine to autonomously hunt for threats."""
    inference_engine: ActiveInferenceEngine = state["active_inference"]
    try:
        result = await inference_engine.infer()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


    uvicorn.run(app, host="0.0.0.0", port=8006)
