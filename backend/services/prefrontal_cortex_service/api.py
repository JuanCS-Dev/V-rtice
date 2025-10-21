"""Maximus Prefrontal Cortex Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Prefrontal
Cortex Service. It exposes functionalities for higher-order cognitive functions
such as strategic planning, decision-making, working memory, and goal-directed
behavior.

Endpoints are provided for:
- Submitting complex problems for strategic planning.
- Requesting optimal decisions based on current context and goals.
- Querying the AI's current emotional state or impulse control levels.

FASE 3 Enhancement: Consumes Global Workspace consciousness events from Kafka
for higher-order cognitive processing and decision-making.

This API allows other Maximus AI services or human operators to leverage the
Prefrontal Cortex Service's advanced cognitive capabilities, enabling Maximus
to formulate long-term goals, evaluate potential actions, and maintain coherent,
goal-oriented behavior across the entire AI system.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI
from pydantic import BaseModel

from emotional_state_monitor import EmotionalStateMonitor
from impulse_inhibition import ImpulseInhibition
from rational_decision_validator import RationalDecisionValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maximus Prefrontal Cortex Service", version="2.0.0")

# Global variables for Kafka consumer
kafka_consumer: Optional[AIOKafkaConsumer] = None
consumer_task: Optional[asyncio.Task] = None
consciousness_events_buffer: List[Dict[str, Any]] = []

# Initialize PFC components
emotional_state_monitor = EmotionalStateMonitor()
impulse_inhibition = ImpulseInhibition()
rational_decision_validator = RationalDecisionValidator()


class StrategicPlanRequest(BaseModel):
    """Request model for initiating strategic planning.

    Attributes:
        problem_description (str): A description of the problem to solve.
        current_context (Dict[str, Any]): The current operational context.
        long_term_goals (List[str]): The long-term goals to consider.
    """

    problem_description: str
    current_context: Dict[str, Any]
    long_term_goals: List[str]


class DecisionRequest(BaseModel):
    """Request model for requesting a decision.

    Attributes:
        options (List[Dict[str, Any]]): A list of decision options.
        criteria (Dict[str, Any]): Criteria for evaluating the options.
        context (Optional[Dict[str, Any]]): Additional context for the decision.
    """

    options: List[Dict[str, Any]]
    criteria: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


async def consume_consciousness_events():
    """Background task to consume Global Workspace consciousness events from Kafka.

    Processes events for higher-order decision making and strategic planning.
    """
    global kafka_consumer, consciousness_events_buffer

    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-immunity:9096")
    kafka_topic = os.getenv("KAFKA_CONSCIOUSNESS_TOPIC", "consciousness-events")

    kafka_consumer = AIOKafkaConsumer(
        kafka_topic,
        bootstrap_servers=kafka_servers,
        group_id="prefrontal-processors",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest"
    )

    logger.info(f"🧠 Connecting to Kafka: {kafka_servers}, topic: {kafka_topic}")

    await kafka_consumer.start()
    logger.info("✅ Kafka consumer started for Global Workspace events")

    try:
        async for msg in kafka_consumer:
            event = msg.value
            logger.info(f"   🔔 Consciousness event received: {event.get('sensor_type')} (salience: {event.get('salience', 0.0):.2f})")

            # Process event for strategic planning
            consciousness_events_buffer.append(event)

            # Keep buffer size manageable (last 100 events)
            if len(consciousness_events_buffer) > 100:
                consciousness_events_buffer.pop(0)

    except asyncio.CancelledError:
        logger.info("Kafka consumer task cancelled")
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}")
    finally:
        await kafka_consumer.stop()
        logger.info("Kafka consumer stopped")


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Prefrontal Cortex Service."""
    global consumer_task

    print("🧠 Starting Maximus Prefrontal Cortex Service v2.0...")  # pragma: no cover

    # Start Kafka consumer in background
    consumer_task = asyncio.create_task(consume_consciousness_events())

    print("✅ Maximus Prefrontal Cortex Service started successfully.")  # pragma: no cover


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Prefrontal Cortex Service."""
    global consumer_task

    print("👋 Shutting down Maximus Prefrontal Cortex Service...")  # pragma: no cover

    # Stop Kafka consumer
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    print("🛑 Maximus Prefrontal Cortex Service shut down.")  # pragma: no cover


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Prefrontal Cortex Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Prefrontal Cortex Service is operational."}


@app.get("/consciousness_events")
async def get_consciousness_events() -> Dict[str, Any]:
    """Retrieves recent consciousness events from Global Workspace.

    Returns:
        Dict[str, Any]: Recent consciousness events processed by Prefrontal Cortex.
    """
    return {
        "total_events": len(consciousness_events_buffer),
        "recent_events": consciousness_events_buffer[-10:] if consciousness_events_buffer else [],
        "kafka_consumer_active": kafka_consumer is not None
    }


@app.post("/strategic_plan")
async def generate_strategic_plan(request: StrategicPlanRequest) -> Dict[str, Any]:
    """Generates a strategic plan to address a complex problem.

    Args:
        request (StrategicPlanRequest): The request body containing problem description, context, and goals.

    Returns:
        Dict[str, Any]: A dictionary containing the generated strategic plan.
    """
    print(f"[API] Generating strategic plan for: {request.problem_description}")
    await asyncio.sleep(0.5)  # Simulate complex planning

    # Simulate plan generation, considering emotional state and impulse control
    emotional_state = await emotional_state_monitor.get_current_state()
    impulse_level = impulse_inhibition.get_inhibition_level()

    plan_details = f"Strategic plan for '{request.problem_description}' considering emotional state ({emotional_state.get('mood')}) and impulse control ({impulse_level:.2f})."
    plan_steps = [
        {
            "step": 1,
            "action": "gather_more_information",
            "details": "Collect data relevant to the problem.",
            "priority": "high",
        },
        {
            "step": 2,
            "action": "evaluate_risks",
            "details": "Assess potential risks and opportunities.",
            "priority": "high",
        },
        {
            "step": 3,
            "action": "propose_solutions",
            "details": "Develop multiple solution pathways.",
            "priority": "medium",
        },
    ]

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "plan": {"description": plan_details, "steps": plan_steps},
    }


@app.post("/make_decision")
async def make_decision_endpoint(request: DecisionRequest) -> Dict[str, Any]:
    """Makes an optimal decision based on provided options and criteria.

    Args:
        request (DecisionRequest): The request body containing decision options, criteria, and context.

    Returns:
        Dict[str, Any]: A dictionary containing the chosen decision and rationale.
    """
    print(f"[API] Making decision based on {len(request.options)} options.")
    await asyncio.sleep(0.3)  # Simulate decision making

    # Simulate decision making, validated by rational decision validator
    chosen_option = request.options[0]  # Simple mock: always choose first
    validation_result = rational_decision_validator.validate_decision(chosen_option, request.criteria, request.context)

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "chosen_option": chosen_option,
        "rationale": validation_result,
    }


@app.get("/emotional_state")
async def get_emotional_state() -> Dict[str, Any]:
    """Retrieves the AI's current emotional state (simulated).

    Returns:
        Dict[str, Any]: A dictionary summarizing the emotional state.
    """
    return await emotional_state_monitor.get_current_state()


@app.get("/impulse_inhibition_level")
async def get_impulse_inhibition_level() -> Dict[str, Any]:
    """Retrieves the current impulse inhibition level.

    Returns:
        Dict[str, Any]: A dictionary containing the impulse inhibition level.
    """
    return {"level": impulse_inhibition.get_inhibition_level()}


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="0.0.0.0", port=8037)
