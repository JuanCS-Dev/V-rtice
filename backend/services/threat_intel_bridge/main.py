"""Threat Intelligence Bridge Service

Connects Reactive Fabric → Active Immune Core with:
- Circuit breaker for resilience
- Message validation and enrichment
- Prometheus metrics
- Structured logging

Authors: Juan & Claude
Version: 1.0.0
Doutrina: Constituição Vértice v2.7
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from pydantic import BaseModel, Field, ValidationError

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# Environment configuration
KAFKA_REACTIVE_FABRIC = os.getenv("KAFKA_REACTIVE_FABRIC", "reactive-fabric-core:9092")
KAFKA_IMMUNE_SYSTEM = os.getenv("KAFKA_IMMUNE_SYSTEM", "hcl-kafka:9092")
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "10"))
CIRCUIT_BREAKER_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Prometheus metrics
bridge_messages_total = Counter(
    "bridge_messages_total",
    "Total messages bridged",
    ["source_topic", "dest_topic", "status"],
)
bridge_latency_seconds = Histogram(
    "bridge_latency_seconds",
    "Message bridging latency",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
)
circuit_breaker_failures = Counter(
    "circuit_breaker_failures_total",
    "Total circuit breaker failures",
)
kafka_connection_errors = Counter(
    "kafka_connection_errors_total",
    "Total Kafka connection errors",
    ["kafka_target"],
)


# Pydantic models
class ThreatIntelMessage(BaseModel):
    """Threat intelligence message from Reactive Fabric."""

    event_id: str = Field(..., description="Unique event ID")
    source_ip: str = Field(..., description="Attacker IP")
    attack_type: str = Field(..., description="Attack type")
    severity: str = Field(..., description="Severity level (low/medium/high/critical)")
    honeypot_id: str = Field(..., description="Source honeypot ID")
    timestamp: str = Field(..., description="Event timestamp (ISO format)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    kafka_reactive_fabric: str
    kafka_immune_system: str
    circuit_breaker: str
    messages_bridged: int
    uptime_seconds: float


# Circuit breaker implementation
class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(self, threshold: int = 10, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def record_success(self) -> None:
        """Record successful operation."""
        self.failures = 0
        if self.state == "half_open":
            self.state = "closed"
            logger.info("circuit_breaker_closed")
        circuit_breaker_state.set(0 if self.state == "closed" else 1 if self.state == "open" else 2)

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        circuit_breaker_failures.inc()

        if self.failures >= self.threshold:
            self.state = "open"
            logger.warning(
                "circuit_breaker_opened",
                failures=self.failures,
                threshold=self.threshold,
            )
        circuit_breaker_state.set(0 if self.state == "closed" else 1 if self.state == "open" else 2)

    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.state == "closed":
            return False

        if self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    self.state = "half_open"
                    logger.info("circuit_breaker_half_open")
                    circuit_breaker_state.set(2)
                    return False
            return True

        # half_open: allow one request through
        return False


# Global instances
consumer: Optional[AIOKafkaConsumer] = None
producer: Optional[AIOKafkaProducer] = None
breaker: CircuitBreaker = CircuitBreaker(
    threshold=CIRCUIT_BREAKER_THRESHOLD,
    timeout=CIRCUIT_BREAKER_TIMEOUT,
)
bridge_task: Optional[asyncio.Task] = None
startup_time: datetime = datetime.utcnow()
messages_bridged_count: int = 0


async def enrich_threat_data(message: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich and validate threat data.

    Args:
        message: Raw message from Reactive Fabric

    Returns:
        Enriched message ready for Immune System

    Raises:
        ValidationError: If message doesn't match expected schema
    """
    # Validate schema
    threat = ThreatIntelMessage(**message)

    # Enrich with bridge metadata
    enriched = threat.model_dump()
    enriched["_bridge_timestamp"] = datetime.utcnow().isoformat()
    enriched["_bridge_version"] = "1.0.0"
    enriched["_source_service"] = "reactive_fabric_core"
    enriched["_dest_service"] = "active_immune_core"

    return enriched


async def bridge_messages() -> None:
    """Main bridge loop: consume from Reactive Fabric, publish to Immune System."""
    global consumer, producer, messages_bridged_count

    logger.info(
        "bridge_messages_started",
        reactive_fabric=KAFKA_REACTIVE_FABRIC,
        immune_system=KAFKA_IMMUNE_SYSTEM,
    )

    while True:
        try:
            if not consumer or not producer:
                logger.warning("kafka_clients_not_ready")
                await asyncio.sleep(5)
                continue

            async for msg in consumer:
                start_time = datetime.utcnow()

                # Check circuit breaker
                if breaker.is_open():
                    logger.warning("circuit_breaker_open_skipping_message")
                    bridge_messages_total.labels(
                        source_topic="reactive_fabric.threat_detected",
                        dest_topic="immunis.cytokines.threat_detected",
                        status="circuit_breaker_open",
                    ).inc()
                    continue

                try:
                    # Deserialize message
                    raw_message = msg.value

                    # Enrich and validate
                    enriched = await enrich_threat_data(raw_message)

                    # Publish to Immune System
                    await producer.send_and_wait(
                        "immunis.cytokines.threat_detected",
                        value=enriched,
                        key=enriched["event_id"].encode("utf-8"),
                    )

                    # Record success
                    breaker.record_success()
                    messages_bridged_count += 1

                    # Metrics
                    latency = (datetime.utcnow() - start_time).total_seconds()
                    bridge_latency_seconds.observe(latency)
                    bridge_messages_total.labels(
                        source_topic="reactive_fabric.threat_detected",
                        dest_topic="immunis.cytokines.threat_detected",
                        status="success",
                    ).inc()

                    logger.info(
                        "message_bridged",
                        event_id=enriched["event_id"],
                        latency_ms=latency * 1000,
                    )

                except ValidationError as e:
                    logger.error("message_validation_failed", error=str(e), raw_message=raw_message)
                    bridge_messages_total.labels(
                        source_topic="reactive_fabric.threat_detected",
                        dest_topic="immunis.cytokines.threat_detected",
                        status="validation_error",
                    ).inc()

                except KafkaError as e:
                    logger.error("kafka_publish_failed", error=str(e))
                    breaker.record_failure()
                    bridge_messages_total.labels(
                        source_topic="reactive_fabric.threat_detected",
                        dest_topic="immunis.cytokines.threat_detected",
                        status="kafka_error",
                    ).inc()

                except Exception as e:
                    logger.error("bridge_unexpected_error", error=str(e), error_type=type(e).__name__)
                    breaker.record_failure()
                    bridge_messages_total.labels(
                        source_topic="reactive_fabric.threat_detected",
                        dest_topic="immunis.cytokines.threat_detected",
                        status="error",
                    ).inc()

        except Exception as e:
            logger.error("bridge_loop_error", error=str(e))
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    global consumer, producer, bridge_task

    logger.info("threat_intel_bridge_starting")

    # Initialize Kafka consumer (Reactive Fabric)
    try:
        consumer = AIOKafkaConsumer(
            "reactive_fabric.threat_detected",
            bootstrap_servers=KAFKA_REACTIVE_FABRIC,
            group_id="threat_intel_bridge",
            value_deserializer=lambda m: __import__("json").loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        await consumer.start()
        logger.info("kafka_consumer_started", bootstrap_servers=KAFKA_REACTIVE_FABRIC)
    except Exception as e:
        logger.error("kafka_consumer_failed", error=str(e))
        kafka_connection_errors.labels(kafka_target="reactive_fabric").inc()
        raise

    # Initialize Kafka producer (Immune System)
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_IMMUNE_SYSTEM,
            value_serializer=lambda v: __import__("json").dumps(v, default=str).encode("utf-8"),
            compression_type="gzip",
            max_batch_size=16384,
            linger_ms=10,
            acks="all",
        )
        await producer.start()
        logger.info("kafka_producer_started", bootstrap_servers=KAFKA_IMMUNE_SYSTEM)
    except Exception as e:
        logger.error("kafka_producer_failed", error=str(e))
        kafka_connection_errors.labels(kafka_target="immune_system").inc()
        raise

    # Start bridge task
    bridge_task = asyncio.create_task(bridge_messages())
    logger.info("bridge_task_started")

    yield

    # Shutdown
    logger.info("threat_intel_bridge_stopping")

    if bridge_task:
        bridge_task.cancel()
        try:
            await bridge_task
        except asyncio.CancelledError:
            pass

    if consumer:
        await consumer.stop()
        logger.info("kafka_consumer_stopped")

    if producer:
        await producer.stop()
        logger.info("kafka_producer_stopped")


# FastAPI app
app = FastAPI(
    title="Threat Intel Bridge",
    description="Bridges Reactive Fabric → Active Immune Core",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    uptime = (datetime.utcnow() - startup_time).total_seconds()

    kafka_rf_status = "connected" if consumer else "disconnected"
    kafka_is_status = "connected" if producer else "disconnected"
    cb_status = breaker.state

    status = "healthy" if (consumer and producer and breaker.state == "closed") else "degraded"

    return HealthResponse(
        status=status,
        kafka_reactive_fabric=kafka_rf_status,
        kafka_immune_system=kafka_is_status,
        circuit_breaker=cb_status,
        messages_bridged=messages_bridged_count,
        uptime_seconds=uptime,
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=LOG_LEVEL.lower())
