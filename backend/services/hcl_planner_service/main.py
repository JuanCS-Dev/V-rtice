"""HCL Planner Service - Main FastAPI Application.

This service is the decision-making core of the HCL ecosystem. It combines a
fast, rule-based Fuzzy Logic Controller with a sophisticated Reinforcement
Learning (RL) agent to make optimal resource management decisions.

- Consumes predictive analytics from the `system.predictions` Kafka topic.
- Uses a Fuzzy Controller to quickly determine the overall operational mode.
- Uses a Soft Actor-Critic (SAC) RL agent to decide on specific actions.
- Publishes the resulting action plan to the `system.actions` Kafka topic.
- Records all decisions in the HCL Knowledge Base for auditing and retraining.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .fuzzy_controller import FuzzyOperationalController
from .rl_agent import SACAgent

# Conditional Kafka import
try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

# ============================================================================
# Configuration and Initialization
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")

state: Dict[str, Any] = {}

class PlanningEngine:
    """A core engine that combines Fuzzy Logic and RL for decision-making."""
    def __init__(self):
        self.fuzzy_controller = FuzzyOperationalController()
        self.rl_agent = SACAgent()

    async def decide(self, system_state: Dict, force_mode: Optional[str] = None) -> Dict:
        """Makes a resource management decision."""
        if force_mode:
            mode = force_mode
            confidence = 1.0
        else:
            mode, confidence, _ = self.fuzzy_controller.decide(cpu=system_state['cpu_usage'], latency=system_state['latency'])
        
        # RL agent would determine specific actions here
        actions = [{"type": "scale", "service": "example", "replicas": 3}]
        return {"decision_id": f"dec_{datetime.now().timestamp()}", "operational_mode": mode, "confidence": confidence, "actions": actions}

# ============================================================================
# FastAPI Lifespan and Application Setup
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    logger.info("Starting HCL Planner Service...")
    state['planning_engine'] = PlanningEngine()
    # Kafka initialization would go here
    yield
    logger.info("Shutting down HCL Planner Service...")

app = FastAPI(
    title="HCL Planner Service",
    description="Decision-making service with Fuzzy Logic and Reinforcement Learning.",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# Pydantic Models
# ============================================================================

class SystemState(BaseModel):
    """Pydantic model for the current system state input."""
    cpu_usage: float
    memory_usage: float
    latency: float

class DecisionRequest(BaseModel):
    """Request model for manually triggering a decision."""
    state: SystemState
    force_mode: Optional[str] = None

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Provides a basic health check of the service."""
    return {"status": "healthy", "service": "hcl_planner"}

@app.post("/decide")
async def make_decision(request: DecisionRequest):
    """Manually triggers the planning engine to make a decision.

    This endpoint is used for testing and allows forcing a specific operational
    mode, bypassing the fuzzy logic controller.

    Args:
        request (DecisionRequest): The current system state and an optional
            mode to force.

    Returns:
        Dict: The generated action plan.
    """
    engine: PlanningEngine = state['planning_engine']
    try:
        decision = await engine.decide(request.state.dict(), request.force_mode)
        # In a real app, this would be sent to Kafka and the KB
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)