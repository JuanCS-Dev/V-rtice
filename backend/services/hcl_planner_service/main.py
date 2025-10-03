"""
HCL Planner Service - Main Application
========================================
Decision-making service combining Fuzzy Logic and Reinforcement Learning.

Architecture:
1. Consumes predictions from Analyzer (Kafka: system.predictions)
2. Uses Fuzzy Logic for fast operational mode decisions
3. Uses RL Agent (SAC) for optimal resource allocation
4. Publishes actions to Executor (Kafka: system.actions)
5. Records decisions to Knowledge Base (HTTP)

Port: 8003
"""

import asyncio
import logging
import json
import os
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import httpx
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from fuzzy_controller import FuzzyOperationalController
from rl_agent import SACAgent

# Configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "hcl_planner")
KB_API_URL = os.getenv("KB_API_URL", "http://localhost:8000")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
MODEL_DIR = os.getenv("MODEL_DIR", "/app/models")

# Kafka topics
TOPIC_PREDICTIONS = "system.predictions"
TOPIC_ACTIONS = "system.actions"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class SystemState(BaseModel):
    """Current system state from monitoring"""
    timestamp: str
    cpu_usage: float = Field(..., ge=0, le=100)
    memory_usage: float = Field(..., ge=0, le=100)
    gpu_usage: float = Field(..., ge=0, le=100)
    queue_depth: int = Field(..., ge=0)
    error_rate: float = Field(..., ge=0)
    latency: float = Field(..., ge=0)
    replicas: Dict[str, int] = Field(default_factory=dict)


class PredictionData(BaseModel):
    """Prediction data from Analyzer"""
    type: str  # "forecast", "anomaly_detection", "failure_prediction"
    timestamp: str
    metric: Optional[str] = None
    forecast_values: Optional[List[float]] = None
    anomaly_score: Optional[float] = None
    is_anomaly: Optional[bool] = None
    failure_probability: Optional[float] = None
    details: Optional[Dict] = None


class ActionPlan(BaseModel):
    """Action plan to execute"""
    decision_id: str
    timestamp: str
    operational_mode: str  # ENERGY_EFFICIENT, BALANCED, HIGH_PERFORMANCE
    confidence: float = Field(..., ge=0, le=1)
    actions: List[Dict]
    reasoning: str
    expected_impact: Dict


class DecisionRequest(BaseModel):
    """Manual decision request"""
    state: SystemState
    force_mode: Optional[str] = None  # Override fuzzy decision


class DecisionResponse(BaseModel):
    """Decision response"""
    decision_id: str
    operational_mode: str
    confidence: float
    actions: List[Dict]
    method: str  # "fuzzy", "rl", "manual"
    details: Dict


# ============================================================================
# Planning Engine
# ============================================================================

class PlanningEngine:
    """
    Core planning engine combining fuzzy logic and reinforcement learning.

    Decision flow:
    1. Fuzzy Controller determines operational mode (fast, ~1ms)
    2. RL Agent computes optimal actions (slower, ~50ms)
    3. Actions are validated and sent to Executor
    4. Decision is recorded to Knowledge Base
    """

    def __init__(self):
        self.fuzzy_controller = FuzzyOperationalController()
        self.rl_agent = None  # Lazy loaded
        self.rl_model_path = os.path.join(MODEL_DIR, "sac_agent.zip")
        self.decision_history: List[Dict] = []
        self.current_mode = "BALANCED"

        logger.info("Planning engine initialized")

    def _ensure_rl_agent(self):
        """Lazy load RL agent"""
        if self.rl_agent is None:
            if os.path.exists(self.rl_model_path):
                logger.info(f"Loading RL agent from {self.rl_model_path}")
                self.rl_agent = SACAgent(model_path=self.rl_model_path)
            else:
                logger.warning("No trained RL model found, creating new agent")
                self.rl_agent = SACAgent()

    async def decide(
        self,
        state: SystemState,
        predictions: Optional[Dict] = None,
        force_mode: Optional[str] = None
    ) -> DecisionResponse:
        """
        Make decision based on current state and predictions.

        Args:
            state: Current system state
            predictions: Optional predictions from Analyzer
            force_mode: Optional forced operational mode

        Returns:
            DecisionResponse with actions
        """
        decision_id = f"decision_{datetime.now(timezone.utc).timestamp()}"

        # Phase 1: Determine operational mode (Fuzzy Logic)
        if force_mode:
            mode = force_mode
            confidence = 1.0
            fuzzy_details = {"forced": True}
            logger.info(f"Forced mode: {mode}")
        else:
            mode, confidence, fuzzy_details = self.fuzzy_controller.decide(
                cpu=state.cpu_usage,
                memory=state.memory_usage,
                error_rate=state.error_rate,
                latency=state.latency
            )
            logger.info(f"Fuzzy decision: {mode} (confidence={confidence:.2f})")

        self.current_mode = mode

        # Phase 2: Compute actions (RL Agent)
        self._ensure_rl_agent()

        # Prepare state for RL agent
        rl_state = np.array([
            state.cpu_usage,
            state.memory_usage,
            state.gpu_usage,
            state.queue_depth,
            state.error_rate,
            state.latency,
            state.replicas.get("maximus_core", 3),
            state.replicas.get("threat_intel", 2),
            state.replicas.get("malware", 2)
        ], dtype=np.float32)

        # Get action from RL agent
        action, _ = self.rl_agent.predict(rl_state, deterministic=True)

        # Parse action
        maximus_delta = int(np.round(action[0]))
        threat_intel_delta = int(np.round(action[1]))
        malware_delta = int(np.round(action[2]))
        resource_mult = float(action[3])

        # Apply mode-specific adjustments
        if mode == "HIGH_PERFORMANCE":
            # Aggressive scaling
            maximus_delta = max(maximus_delta, 0)
            threat_intel_delta = max(threat_intel_delta, 0)
            malware_delta = max(malware_delta, 0)
            resource_mult = max(resource_mult, 1.0)
        elif mode == "ENERGY_EFFICIENT":
            # Conservative scaling
            maximus_delta = min(maximus_delta, 0)
            threat_intel_delta = min(threat_intel_delta, 0)
            malware_delta = min(malware_delta, 0)
            resource_mult = min(resource_mult, 1.0)
        # BALANCED mode uses raw RL output

        # Build action plan
        actions = []

        if maximus_delta != 0:
            actions.append({
                "type": "scale_service",
                "service": "maximus_core",
                "current_replicas": state.replicas.get("maximus_core", 3),
                "target_replicas": np.clip(
                    state.replicas.get("maximus_core", 3) + maximus_delta, 1, 20
                ),
                "delta": maximus_delta
            })

        if threat_intel_delta != 0:
            actions.append({
                "type": "scale_service",
                "service": "threat_intel",
                "current_replicas": state.replicas.get("threat_intel", 2),
                "target_replicas": np.clip(
                    state.replicas.get("threat_intel", 2) + threat_intel_delta, 1, 20
                ),
                "delta": threat_intel_delta
            })

        if malware_delta != 0:
            actions.append({
                "type": "scale_service",
                "service": "malware_analysis",
                "current_replicas": state.replicas.get("malware", 2),
                "target_replicas": np.clip(
                    state.replicas.get("malware", 2) + malware_delta, 1, 20
                ),
                "delta": malware_delta
            })

        if abs(resource_mult - 1.0) > 0.1:
            actions.append({
                "type": "adjust_resources",
                "multiplier": resource_mult,
                "cpu_limit": f"{int(1000 * resource_mult)}m",
                "memory_limit": f"{int(2048 * resource_mult)}Mi"
            })

        # If no actions, it means system is stable
        if not actions:
            actions.append({
                "type": "no_action",
                "reason": "System stable, no changes needed"
            })

        # Build reasoning
        reasoning_parts = [
            f"Operational mode: {mode} (confidence: {confidence:.2f})",
            f"CPU: {state.cpu_usage:.1f}%, Memory: {state.memory_usage:.1f}%",
            f"Error rate: {state.error_rate:.1f}, Latency: {state.latency:.1f}ms"
        ]

        if predictions:
            reasoning_parts.append(f"Predictions: {predictions.get('type', 'unknown')}")

        reasoning = "; ".join(reasoning_parts)

        # Expected impact
        expected_impact = {
            "operational_mode": mode,
            "estimated_cost_change": self._estimate_cost_change(actions),
            "estimated_latency_change": self._estimate_latency_change(state, actions),
            "confidence": confidence
        }

        response = DecisionResponse(
            decision_id=decision_id,
            operational_mode=mode,
            confidence=confidence,
            actions=actions,
            method="fuzzy+rl" if not force_mode else "manual",
            details={
                "fuzzy": fuzzy_details,
                "rl_action": action.tolist(),
                "predictions": predictions,
                "expected_impact": expected_impact
            }
        )

        # Store in history
        self.decision_history.append({
            "decision_id": decision_id,
            "timestamp": state.timestamp,
            "state": state.dict(),
            "response": response.dict()
        })

        # Keep last 1000 decisions
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]

        return response

    def _estimate_cost_change(self, actions: List[Dict]) -> float:
        """Estimate cost change from actions"""
        cost_per_replica = {"maximus_core": 2.0, "threat_intel": 1.5, "malware_analysis": 3.0}
        total_change = 0.0

        for action in actions:
            if action["type"] == "scale_service":
                service = action["service"]
                delta = action["delta"]
                total_change += delta * cost_per_replica.get(service, 2.0)

        return total_change

    def _estimate_latency_change(self, state: SystemState, actions: List[Dict]) -> float:
        """Estimate latency change from actions"""
        scale_actions = [a for a in actions if a["type"] == "scale_service"]

        if not scale_actions:
            return 0.0

        total_delta = sum(a["delta"] for a in scale_actions)

        # Simple heuristic: more replicas = lower latency (if overloaded)
        if state.cpu_usage > 70:
            return -10 * total_delta  # -10ms per replica if overloaded
        else:
            return -2 * total_delta  # -2ms per replica if normal

    async def train_rl_agent(self, timesteps: int = 50000) -> Dict:
        """Train RL agent"""
        logger.info(f"Training RL agent for {timesteps} timesteps")

        self._ensure_rl_agent()
        self.rl_agent.train(total_timesteps=timesteps)
        self.rl_agent.save(self.rl_model_path)

        return {
            "status": "completed",
            "timesteps": timesteps,
            "model_path": self.rl_model_path
        }


# ============================================================================
# Kafka Integration
# ============================================================================

class KafkaHandler:
    """Handle Kafka consumer/producer for predictions and actions"""

    def __init__(self, planning_engine: PlanningEngine):
        self.planning_engine = planning_engine
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[AIOKafkaProducer] = None
        self.running = False

    async def start(self):
        """Start Kafka consumer and producer"""
        try:
            self.consumer = AIOKafkaConsumer(
                TOPIC_PREDICTIONS,
                bootstrap_servers=KAFKA_BROKERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id=f"{SERVICE_NAME}_group",
                auto_offset_reset='latest'
            )

            self.producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BROKERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )

            await self.consumer.start()
            await self.producer.start()

            logger.info(f"Kafka connected: {KAFKA_BROKERS}")
            logger.info(f"Consuming from: {TOPIC_PREDICTIONS}")
            logger.info(f"Publishing to: {TOPIC_ACTIONS}")

            self.running = True
            asyncio.create_task(self._consume_loop())

        except Exception as e:
            logger.error(f"Failed to start Kafka: {e}")
            raise

    async def stop(self):
        """Stop Kafka consumer and producer"""
        self.running = False

        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()

        logger.info("Kafka disconnected")

    async def _consume_loop(self):
        """Main consumption loop"""
        logger.info("Starting prediction consumption loop")

        try:
            async for msg in self.consumer:
                try:
                    prediction = msg.value
                    await self._handle_prediction(prediction)
                except Exception as e:
                    logger.error(f"Error handling prediction: {e}")
        except Exception as e:
            logger.error(f"Consumer loop error: {e}")

    async def _handle_prediction(self, prediction: Dict):
        """Handle incoming prediction"""
        logger.info(f"Received prediction: {prediction.get('type')}")

        # TODO: Fetch current state from Monitor or KB
        # For now, extract from prediction if available
        state_data = prediction.get("current_state")

        if not state_data:
            logger.warning("No state data in prediction, skipping decision")
            return

        try:
            state = SystemState(**state_data)

            # Make decision
            decision = await self.planning_engine.decide(state, predictions=prediction)

            # Publish action plan
            action_plan = ActionPlan(
                decision_id=decision.decision_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                operational_mode=decision.operational_mode,
                confidence=decision.confidence,
                actions=decision.actions,
                reasoning=f"Prediction-triggered decision: {prediction.get('type')}",
                expected_impact=decision.details.get("expected_impact", {})
            )

            await self.publish_action(action_plan)

            # Record to Knowledge Base
            await self._record_decision(state, decision, prediction)

        except Exception as e:
            logger.error(f"Error processing prediction: {e}")

    async def publish_action(self, action_plan: ActionPlan):
        """Publish action plan to Kafka"""
        try:
            await self.producer.send(
                TOPIC_ACTIONS,
                value=action_plan.dict()
            )
            logger.info(f"Published action plan: {action_plan.decision_id}")
        except Exception as e:
            logger.error(f"Failed to publish action: {e}")

    async def _record_decision(self, state: SystemState, decision: DecisionResponse, prediction: Dict):
        """Record decision to Knowledge Base"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "timestamp": state.timestamp,
                    "trigger_type": f"prediction_{prediction.get('type')}",
                    "operational_mode": decision.operational_mode,
                    "actions_taken": decision.actions,
                    "state_before": state.dict(),
                    "confidence": decision.confidence,
                    "prediction_data": prediction
                }

                response = await client.post(
                    f"{KB_API_URL}/decisions",
                    json=payload,
                    timeout=5.0
                )
                response.raise_for_status()
                logger.info(f"Recorded decision to KB: {decision.decision_id}")

        except Exception as e:
            logger.error(f"Failed to record decision to KB: {e}")


# ============================================================================
# FastAPI Application
# ============================================================================

planning_engine = PlanningEngine()
kafka_handler = KafkaHandler(planning_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    logger.info("Starting HCL Planner Service")

    # Create model directory
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Start Kafka
    try:
        await kafka_handler.start()
    except Exception as e:
        logger.warning(f"Kafka not available: {e}")

    yield

    # Cleanup
    await kafka_handler.stop()
    logger.info("HCL Planner Service stopped")


app = FastAPI(
    title="HCL Planner Service",
    description="Decision-making service with Fuzzy Logic and Reinforcement Learning",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "current_mode": planning_engine.current_mode,
        "rl_agent_loaded": planning_engine.rl_agent is not None,
        "kafka_connected": kafka_handler.running,
        "decisions_count": len(planning_engine.decision_history)
    }


@app.post("/decide", response_model=DecisionResponse)
async def make_decision(request: DecisionRequest):
    """
    Make decision based on current state.

    Manual decision endpoint for testing or emergency override.
    """
    try:
        decision = await planning_engine.decide(
            state=request.state,
            force_mode=request.force_mode
        )
        return decision
    except Exception as e:
        logger.error(f"Decision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train/rl")
async def train_rl_agent(
    background_tasks: BackgroundTasks,
    timesteps: int = 50000
):
    """
    Train RL agent in background.

    Training happens asynchronously to avoid blocking.
    """
    background_tasks.add_task(planning_engine.train_rl_agent, timesteps)

    return {
        "status": "training_started",
        "timesteps": timesteps,
        "message": "RL agent training in background"
    }


@app.get("/history")
async def get_decision_history(limit: int = 100):
    """Get recent decision history"""
    return {
        "count": len(planning_engine.decision_history),
        "decisions": planning_engine.decision_history[-limit:]
    }


@app.get("/fuzzy/test")
async def test_fuzzy(
    cpu: float,
    memory: float,
    error_rate: float,
    latency: float
):
    """
    Test fuzzy controller with specific inputs.

    Useful for debugging and visualization.
    """
    mode, confidence, details = planning_engine.fuzzy_controller.decide(
        cpu=cpu,
        memory=memory,
        error_rate=error_rate,
        latency=latency
    )

    return {
        "mode": mode,
        "confidence": confidence,
        "details": details
    }


@app.post("/mode/set")
async def set_operational_mode(mode: str):
    """
    Manually set operational mode.

    Modes: ENERGY_EFFICIENT, BALANCED, HIGH_PERFORMANCE
    """
    valid_modes = ["ENERGY_EFFICIENT", "BALANCED", "HIGH_PERFORMANCE"]

    if mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Must be one of: {valid_modes}"
        )

    planning_engine.current_mode = mode
    logger.info(f"Manual mode change: {mode}")

    return {
        "status": "success",
        "mode": mode,
        "message": f"Operational mode set to {mode}"
    }


@app.get("/status")
async def get_status():
    """Get detailed service status"""
    return {
        "service": SERVICE_NAME,
        "operational_mode": planning_engine.current_mode,
        "fuzzy_controller": {
            "loaded": planning_engine.fuzzy_controller is not None,
            "rules_count": len(planning_engine.fuzzy_controller.rules)
        },
        "rl_agent": {
            "loaded": planning_engine.rl_agent is not None,
            "model_path": planning_engine.rl_model_path,
            "model_exists": os.path.exists(planning_engine.rl_model_path)
        },
        "kafka": {
            "connected": kafka_handler.running,
            "consuming_from": TOPIC_PREDICTIONS,
            "publishing_to": TOPIC_ACTIONS
        },
        "decisions": {
            "total": len(planning_engine.decision_history),
            "recent": planning_engine.decision_history[-5:] if planning_engine.decision_history else []
        }
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
