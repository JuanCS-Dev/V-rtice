"""Global Workspace Broadcasting Module.

Implements Global Workspace Theory (Baars, 1988) with dual broadcasting:
1. Kafka: Durable event streaming for consciousness services (long-term)
2. Redis Streams: Hot path for ultra-low latency awareness (sub-ms)

This module allows the Digital Thalamus to broadcast salient sensory events
to the entire consciousness system, enabling global awareness and coordinated
cognitive processing.

Bio-inspiration: Mimics the broadcasting mechanism of the thalamus in
distributing sensory information to cortical areas for conscious awareness.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)


class GlobalWorkspace:
    """Global Workspace broadcaster for consciousness events.

    Implements dual-path broadcasting:
    - Kafka: Persistent, replay-capable, multi-consumer
    - Redis Streams: Ephemeral, ultra-low latency, time-windowed

    Attributes:
        kafka_bootstrap_servers (str): Kafka broker addresses
        redis_url (str): Redis connection string
        kafka_topic (str): Topic for consciousness events
        redis_stream (str): Stream key for hot path
        kafka_producer: AIOKafka producer instance
        redis_client: Redis async client
    """

    def __init__(
        self,
        kafka_bootstrap_servers: str = "kafka-immunity:9096",
        redis_url: str = "redis://redis:6379",
        kafka_topic: str = "consciousness-events",
        redis_stream: str = "consciousness:hot-path",
        redis_stream_maxlen: int = 10000,  # Keep last 10k events
    ):
        """Initialize Global Workspace broadcaster.

        Args:
            kafka_bootstrap_servers: Kafka broker addresses
            redis_url: Redis connection string
            kafka_topic: Kafka topic for consciousness events
            redis_stream: Redis stream key for hot path
            redis_stream_maxlen: Max events to keep in Redis stream
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.redis_url = redis_url
        self.kafka_topic = kafka_topic
        self.redis_stream = redis_stream
        self.redis_stream_maxlen = redis_stream_maxlen

        self.kafka_producer: Optional[AIOKafkaProducer] = None
        self.redis_client: Optional[aioredis.Redis] = None

        self._broadcasting_enabled = False
        self._events_broadcasted = 0
        self._kafka_errors = 0
        self._redis_errors = 0

        logger.info(f"🧠 Global Workspace initialized")
        logger.info(f"   Kafka: {kafka_bootstrap_servers} → {kafka_topic}")
        logger.info(f"   Redis: {redis_url} → {redis_stream}")

    async def start(self) -> None:
        """Start Global Workspace broadcasting infrastructure.

        Initializes Kafka producer and Redis client connections.
        """
        try:
            # Initialize Kafka producer
            self.kafka_producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                compression_type="gzip",
                acks="all",  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5,
            )
            await self.kafka_producer.start()
            logger.info("✅ Kafka producer started")

            # Initialize Redis client
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Redis client connected")

            self._broadcasting_enabled = True
            logger.info("🚀 Global Workspace broadcasting ACTIVE")

        except Exception as e:
            logger.error(f"❌ Failed to start Global Workspace: {e}")
            self._broadcasting_enabled = False
            raise

    async def stop(self) -> None:
        """Stop Global Workspace broadcasting infrastructure.

        Gracefully shuts down Kafka producer and Redis client.
        """
        logger.info("🛑 Stopping Global Workspace...")

        if self.kafka_producer:
            await self.kafka_producer.stop()
            logger.info("   Kafka producer stopped")

        if self.redis_client:
            await self.redis_client.close()
            logger.info("   Redis client closed")

        self._broadcasting_enabled = False
        logger.info("✅ Global Workspace stopped")

    async def broadcast_event(
        self,
        sensor_type: str,
        sensor_id: str,
        data: Dict[str, Any],
        salience: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Broadcast a salient sensory event to Global Workspace.

        Dual broadcast:
        1. Kafka: Persistent event for all consciousness services
        2. Redis Streams: Hot path for immediate awareness

        Args:
            sensor_type: Type of sensor (visual, auditory, etc.)
            sensor_id: Unique sensor identifier
            data: Processed sensory data payload
            salience: Salience score (0.0-1.0) indicating importance
            metadata: Additional event metadata

        Returns:
            Dict with broadcast status and event ID

        Raises:
            RuntimeError: If broadcasting is not enabled
        """
        if not self._broadcasting_enabled:
            raise RuntimeError("Global Workspace broadcasting not enabled")

        # Create consciousness event
        event = self._create_consciousness_event(
            sensor_type=sensor_type,
            sensor_id=sensor_id,
            data=data,
            salience=salience,
            metadata=metadata or {}
        )

        event_id = event["event_id"]

        # Broadcast to both channels concurrently
        kafka_task = self._broadcast_to_kafka(event)
        redis_task = self._broadcast_to_redis(event)

        kafka_result, redis_result = await asyncio.gather(
            kafka_task,
            redis_task,
            return_exceptions=True
        )

        # Track errors
        if isinstance(kafka_result, Exception):
            self._kafka_errors += 1
            logger.error(f"Kafka broadcast failed: {kafka_result}")

        if isinstance(redis_result, Exception):
            self._redis_errors += 1
            logger.error(f"Redis broadcast failed: {redis_result}")

        # Consider broadcast successful if at least one channel succeeded
        success = not (isinstance(kafka_result, Exception) and isinstance(redis_result, Exception))

        if success:
            self._events_broadcasted += 1

        return {
            "event_id": event_id,
            "broadcasted": success,
            "kafka_status": "success" if not isinstance(kafka_result, Exception) else "failed",
            "redis_status": "success" if not isinstance(redis_result, Exception) else "failed",
            "salience": salience,
            "timestamp": event["timestamp"]
        }

    def _create_consciousness_event(
        self,
        sensor_type: str,
        sensor_id: str,
        data: Dict[str, Any],
        salience: float,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a consciousness event with enriched metadata.

        Args:
            sensor_type: Type of sensor
            sensor_id: Sensor identifier
            data: Event data
            salience: Salience score
            metadata: Additional metadata

        Returns:
            Enriched consciousness event
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        return {
            "event_id": event_id,
            "event_type": "sensory_perception",
            "sensor_type": sensor_type,
            "sensor_id": sensor_id,
            "salience": salience,
            "timestamp": timestamp,
            "data": data,
            "metadata": {
                **metadata,
                "broadcast_source": "digital_thalamus",
                "global_workspace_version": "1.0.0"
            }
        }

    async def _broadcast_to_kafka(self, event: Dict[str, Any]) -> None:
        """Broadcast event to Kafka topic.

        Args:
            event: Consciousness event to broadcast
        """
        if not self.kafka_producer:
            raise RuntimeError("Kafka producer not initialized")

        # Use sensor_type as partition key for ordering
        key = event["sensor_type"].encode("utf-8")

        await self.kafka_producer.send_and_wait(
            self.kafka_topic,
            value=event,
            key=key
        )

        logger.debug(f"📤 Kafka: {event['event_id'][:8]}... (salience: {event['salience']:.2f})")

    async def _broadcast_to_redis(self, event: Dict[str, Any]) -> None:
        """Broadcast event to Redis stream (hot path).

        Args:
            event: Consciousness event to broadcast
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not initialized")

        # Add to stream with automatic trimming
        await self.redis_client.xadd(
            self.redis_stream,
            event,
            maxlen=self.redis_stream_maxlen,
            approximate=True  # Approximate trimming for performance
        )

        logger.debug(f"⚡ Redis: {event['event_id'][:8]}... (salience: {event['salience']:.2f})")

    async def get_status(self) -> Dict[str, Any]:
        """Get Global Workspace status and metrics.

        Returns:
            Status dictionary with metrics
        """
        return {
            "broadcasting_enabled": self._broadcasting_enabled,
            "events_broadcasted": self._events_broadcasted,
            "kafka_errors": self._kafka_errors,
            "redis_errors": self._redis_errors,
            "kafka_connected": self.kafka_producer is not None,
            "redis_connected": self.redis_client is not None,
            "kafka_topic": self.kafka_topic,
            "redis_stream": self.redis_stream
        }
