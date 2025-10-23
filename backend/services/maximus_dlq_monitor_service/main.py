"""
MAXIMUS DLQ Monitor Service

Monitors Dead Letter Queue for failed APV messages and implements retry logic.

Air Gap Fix: AG-KAFKA-005
Priority: HIGH (Data Loss Prevention)
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from prometheus_client import Counter, Gauge, make_asgi_app
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
dlq_messages_total = Counter(
    "dlq_messages_total",
    "Total DLQ messages received",
    ["reason", "severity"]
)
dlq_retries_total = Counter(
    "dlq_retries_total",
    "Total DLQ retry attempts",
    ["success"]
)
dlq_queue_size = Gauge(
    "dlq_queue_size",
    "Current number of messages in DLQ"
)
dlq_alerts_sent = Counter(
    "dlq_alerts_sent_total",
    "Total alerts sent for DLQ issues"
)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
DLQ_TOPIC = "maximus.adaptive-immunity.dlq"
RETRY_TOPIC = "maximus.adaptive-immunity.apv"  # Retry to original topic
ALERT_TOPIC = "system.alerts"  # Central alerts topic
MAX_RETRIES = 3
DLQ_ALERT_THRESHOLD = 10

# Global state
consumer_task = None
dlq_message_count = 0


class DLQMonitor:
    """Dead Letter Queue Monitor with retry logic."""

    def __init__(self):
        self.consumer = None
        self.producer = None
        self.running = False

    async def start(self):
        """Start DLQ monitoring."""
        logger.info("Starting DLQ Monitor...")

        try:
            # Initialize Kafka consumer
            self.consumer = KafkaConsumer(
                DLQ_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id="dlq-monitor",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True
            )

            # Initialize Kafka producer for retries
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )

            logger.info(f"✅ DLQ Monitor connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
            logger.info(f"📊 Monitoring topic: {DLQ_TOPIC}")

            self.running = True
            await self._consume_loop()

        except KafkaError as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ DLQ Monitor failed to start: {e}")
            raise

    async def _consume_loop(self):
        """Main consumption loop."""
        global dlq_message_count

        while self.running:
            try:
                # Poll for messages (non-blocking)
                messages = self.consumer.poll(timeout_ms=1000)

                for topic_partition, records in messages.items():
                    for message in records:
                        dlq_message_count += 1
                        dlq_queue_size.set(dlq_message_count)

                        await self._process_dlq_message(message.value)

                # Allow other tasks to run
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in consume loop: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _process_dlq_message(self, message: Dict[str, Any]):
        """Process a single DLQ message."""
        global dlq_message_count
        try:
            # Extract metadata
            error_type = message.get("error", {}).get("type", "unknown")
            severity = message.get("severity", "medium")
            retry_count = message.get("retry_count", 0)
            apv_data = message.get("apv", {})

            logger.error(
                f"🚨 DLQ Message: {error_type} | "
                f"Severity: {severity} | "
                f"Retries: {retry_count} | "
                f"APV ID: {apv_data.get('id', 'unknown')}"
            )

            # Update metrics
            dlq_messages_total.labels(reason=error_type, severity=severity).inc()

            # Retry logic
            if retry_count < MAX_RETRIES:
                success = await self._retry_apv(apv_data, retry_count + 1)
                dlq_retries_total.labels(success=str(success)).inc()

                if success:
                    logger.info(f"✅ APV {apv_data.get('id')} retried successfully")
                    dlq_message_count = max(0, dlq_message_count - 1)
                    dlq_queue_size.set(dlq_message_count)
                else:
                    logger.warning(f"⚠️  APV {apv_data.get('id')} retry failed")
            else:
                # Max retries exceeded
                logger.error(
                    f"❌ APV {apv_data.get('id')} failed after {MAX_RETRIES} retries. "
                    "Manual intervention required."
                )
                await self._send_alert(message)

            # Check alert threshold
            if dlq_message_count >= DLQ_ALERT_THRESHOLD:
                logger.critical(
                    f"🚨 CRITICAL: DLQ size ({dlq_message_count}) exceeds threshold ({DLQ_ALERT_THRESHOLD})"
                )
                await self._send_alert({
                    "type": "dlq_threshold_exceeded",
                    "queue_size": dlq_message_count,
                    "threshold": DLQ_ALERT_THRESHOLD
                })

        except Exception as e:
            logger.error(f"Error processing DLQ message: {e}")

    async def _retry_apv(self, apv_data: Dict[str, Any], retry_count: int) -> bool:
        """Retry sending APV to original topic."""
        try:
            # Add retry metadata
            apv_data["_retry_metadata"] = {
                "retry_count": retry_count,
                "retry_timestamp": datetime.utcnow().isoformat(),
                "source": "dlq-monitor"
            }

            # Send to retry topic
            future = self.producer.send(RETRY_TOPIC, apv_data)
            result = future.get(timeout=10)

            logger.info(
                f"✅ APV retried (attempt {retry_count}/{MAX_RETRIES}): "
                f"Topic: {result.topic}, Partition: {result.partition}, Offset: {result.offset}"
            )
            return True

        except Exception as e:
            logger.error(f"Retry failed: {e}")
            return False

    async def _send_alert(self, data: Dict[str, Any]):
        """Send alert for DLQ issues to Kafka alerts topic."""
        try:
            dlq_alerts_sent.inc()

            # Build alert event
            alert_event = {
                "alert_id": str(uuid4()),
                "alert_type": "dlq_threshold_exceeded",
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "service": "maximus_dlq_monitor",
                "message": f"DLQ size exceeded threshold: {data.get('queue_size', 'unknown')} messages",
                "details": {
                    "dlq_size": data.get("queue_size", 0),
                    "threshold": DLQ_ALERT_THRESHOLD,
                    "sample_messages": data.get("sample_messages", []),
                    "timestamp": datetime.utcnow().isoformat()
                },
                "action_required": "Review DLQ messages and investigate root cause",
                "runbook_url": "https://docs.vertice.internal/runbooks/dlq-investigation"
            }

            # Publish alert to Kafka
            if self.producer:
                try:
                    self.producer.send(
                        ALERT_TOPIC,
                        key=b"dlq_alert",
                        value=alert_event
                    )
                    logger.info(f"✅ Alert published to Kafka topic: {ALERT_TOPIC}")
                except Exception as kafka_error:
                    logger.warning(f"Failed to publish alert to Kafka: {kafka_error}")

            # Also log critically for immediate visibility
            logger.critical(f"🚨 DLQ ALERT: {json.dumps(alert_event, indent=2)}")

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def stop(self):
        """Stop DLQ monitoring."""
        logger.info("Stopping DLQ Monitor...")
        self.running = False

        if self.consumer:
            self.consumer.close()

        if self.producer:
            self.producer.close()

        logger.info("✅ DLQ Monitor stopped")


# Global monitor instance
dlq_monitor = DLQMonitor()


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("🚀 Starting MAXIMUS DLQ Monitor Service")  # pragma: no cover

    # Start DLQ monitoring in background task
    global consumer_task  # pragma: no cover
    consumer_task = asyncio.create_task(dlq_monitor.start())  # pragma: no cover

    yield  # pragma: no cover

    # Shutdown
    logger.info("🛑 Shutting down MAXIMUS DLQ Monitor Service")  # pragma: no cover
    await dlq_monitor.stop()  # pragma: no cover

    if consumer_task:  # pragma: no cover
        consumer_task.cancel()  # pragma: no cover
        try:  # pragma: no cover
            await consumer_task  # pragma: no cover
        except asyncio.CancelledError:  # pragma: no cover
            pass  # pragma: no cover


# FastAPI app
app = FastAPI(
    title="MAXIMUS DLQ Monitor",
    description="Dead Letter Queue monitoring and retry service for APVs",
    version="1.0.0",
    lifespan=lifespan
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if dlq_monitor.running else "unhealthy",
        "service": "maximus-dlq-monitor",
        "kafka_connected": dlq_monitor.consumer is not None,
        "dlq_queue_size": dlq_message_count,
        "alert_threshold": DLQ_ALERT_THRESHOLD
    }


@app.get("/status")
async def get_status():
    """Get DLQ monitor status and metrics."""
    return {
        "service": "maximus-dlq-monitor",
        "running": dlq_monitor.running,
        "kafka_bootstrap": KAFKA_BOOTSTRAP_SERVERS,
        "dlq_topic": DLQ_TOPIC,
        "retry_topic": RETRY_TOPIC,
        "max_retries": MAX_RETRIES,
        "current_queue_size": dlq_message_count,
        "alert_threshold": DLQ_ALERT_THRESHOLD,
        "alert_status": "critical" if dlq_message_count >= DLQ_ALERT_THRESHOLD else "normal"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MAXIMUS DLQ Monitor",
        "version": "1.0.0",
        "description": "Monitoring Dead Letter Queue for failed APV messages",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "metrics": "/metrics"
        }
    }


if __name__ == "__main__":  # pragma: no cover
    # Run service
    port = int(os.getenv("PORT", 8085))  # pragma: no cover

    logger.info(f"🚀 Starting MAXIMUS DLQ Monitor on port {port}")  # pragma: no cover
    logger.info(f"📊 Kafka: {KAFKA_BOOTSTRAP_SERVERS}")  # pragma: no cover
    logger.info(f"📊 DLQ Topic: {DLQ_TOPIC}")  # pragma: no cover
    logger.info(f"📊 Retry Topic: {RETRY_TOPIC}")  # pragma: no cover
    logger.info(f"📊 Max Retries: {MAX_RETRIES}")  # pragma: no cover
    logger.info(f"📊 Alert Threshold: {ALERT_THRESHOLD}")  # pragma: no cover

    uvicorn.run(  # pragma: no cover
        app,  # pragma: no cover
        host="0.0.0.0",  # pragma: no cover
        port=port,  # pragma: no cover
        log_level="info"  # pragma: no cover
    )  # pragma: no cover
