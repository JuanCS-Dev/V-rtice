"""
Unified Kafka Client - Production-ready event bus

Single client for all Kafka operations across the ecosystem.
Handles both producing and consuming with resilience patterns.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import contextlib
import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError

from .event_schemas import EventBase
from .topics import EventTopic

logger = logging.getLogger(__name__)


EventHandler = Callable[[EventBase], None]


class UnifiedKafkaClient:
    """
    Unified Kafka client for the Vértice ecosystem.

    Features:
    - Single client for producing and consuming
    - Type-safe event publishing with Pydantic schemas
    - Event handler registration with routing
    - Automatic retries with exponential backoff
    - Graceful degradation mode
    - Metrics and monitoring

    Usage:
        # Initialize
        client = UnifiedKafkaClient(
            bootstrap_servers="kafka:9092",
            service_name="my_service"
        )
        await client.start()

        # Publish event
        event = ThreatDetectionEvent(...)
        await client.publish(EventTopic.THREATS_DETECTED, event)

        # Subscribe to events
        await client.subscribe(
            EventTopic.IMMUNE_RESPONSES,
            handler=my_response_handler
        )

        # Cleanup
        await client.stop()
    """

    def __init__(
        self,
        bootstrap_servers: str,
        service_name: str,
        enable_producer: bool = True,
        enable_consumer: bool = True,
        enable_degraded_mode: bool = True,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
    ):
        """
        Initialize Unified Kafka Client.

        Args:
            bootstrap_servers: Kafka broker addresses
            service_name: Name of this service (for consumer group)
            enable_producer: Enable producer functionality
            enable_consumer: Enable consumer functionality
            enable_degraded_mode: Continue without Kafka if unavailable
            max_retries: Maximum retry attempts
            retry_backoff_base: Backoff multiplier for retries
        """
        self.bootstrap_servers = bootstrap_servers
        self.service_name = service_name
        self.enable_producer = enable_producer
        self.enable_consumer = enable_consumer
        self.enable_degraded_mode = enable_degraded_mode
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base

        # Producer
        self._producer: AIOKafkaProducer | None = None
        self._producer_available = False

        # Consumer
        self._consumer: AIOKafkaConsumer | None = None
        self._consumer_available = False
        self._consumer_task: asyncio.Task | None = None

        # Event handlers
        self._handlers: dict[EventTopic, list[EventHandler]] = {}
        self._subscribed_topics: list[EventTopic] = []

        # State
        self._running = False

        # Metrics
        self.events_published = 0
        self.events_consumed = 0
        self.events_failed = 0
        self.events_by_topic: dict[str, int] = {}

        logger.info(
            f"UnifiedKafkaClient initialized: service={service_name}, "
            f"producer={enable_producer}, consumer={enable_consumer}"
        )

    # ==================== LIFECYCLE ====================

    async def start(self) -> None:
        """Start Kafka client (producer and/or consumer)."""
        if self._running:
            logger.warning("UnifiedKafkaClient already running")
            return

        logger.info("Starting UnifiedKafkaClient...")

        # Start producer
        if self.enable_producer:
            await self._start_producer()

        # Start consumer
        if self.enable_consumer:
            await self._start_consumer()

        self._running = True
        logger.info("✓ UnifiedKafkaClient started")

    async def stop(self) -> None:
        """Stop Kafka client."""
        if not self._running:
            logger.warning("UnifiedKafkaClient not running")
            return

        logger.info("Stopping UnifiedKafkaClient...")

        # Stop consumer
        if self._consumer_task:
            self._consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._consumer_task

        if self._consumer:
            await self._consumer.stop()

        # Stop producer
        if self._producer:
            await self._producer.stop()

        self._running = False
        self._producer_available = False
        self._consumer_available = False

        logger.info("✓ UnifiedKafkaClient stopped")

    async def _start_producer(self) -> None:
        """Initialize Kafka producer."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode(),
                acks="all",
                compression_type="gzip",
                max_batch_size=16384,
                linger_ms=10,
            )
            await self._producer.start()
            self._producer_available = True
            logger.info("✓ Kafka producer started")
        except (KafkaConnectionError, KafkaError) as e:
            if self.enable_degraded_mode:
                self._producer_available = False
                logger.warning(f"Kafka producer unavailable - degraded mode: {e}")
            else:
                raise

    async def _start_consumer(self) -> None:
        """Initialize Kafka consumer."""
        if not self._subscribed_topics:
            logger.info("No topics subscribed - consumer not started")
            return

        try:
            topic_names = [topic.value for topic in self._subscribed_topics]

            self._consumer = AIOKafkaConsumer(
                *topic_names,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"{self.service_name}_consumer_group",
                value_deserializer=lambda v: json.loads(v.decode()),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            await self._consumer.start()
            self._consumer_available = True

            # Start background consumer task
            self._consumer_task = asyncio.create_task(self._consume_loop())

            logger.info(f"✓ Kafka consumer started (topics={topic_names})")
        except (KafkaConnectionError, KafkaError) as e:
            if self.enable_degraded_mode:
                self._consumer_available = False
                logger.warning(f"Kafka consumer unavailable - degraded mode: {e}")
            else:
                raise

    # ==================== PRODUCER METHODS ====================

    async def publish(
        self,
        topic: EventTopic,
        event: EventBase,
        key: str | None = None,
    ) -> bool:
        """
        Publish event to Kafka topic.

        Args:
            topic: Event topic
            event: Event object (must inherit from EventBase)
            key: Optional partition key (for ordering)

        Returns:
            True if published successfully, False otherwise
        """
        if not self._running:
            logger.error("UnifiedKafkaClient not running")
            return False

        if not isinstance(event, EventBase):
            raise TypeError(f"Event must inherit from EventBase, got {type(event)}")

        # Add metadata
        event_dict = event.model_dump()
        event_dict["_published_at"] = datetime.utcnow().isoformat()
        event_dict["_publisher"] = self.service_name

        # Try publishing to Kafka
        if self._producer_available:
            for attempt in range(self.max_retries + 1):
                try:
                    key_bytes = key.encode() if key else None

                    await self._producer.send_and_wait(
                        topic.value,
                        value=event_dict,
                        key=key_bytes,
                    )

                    # Update metrics
                    self.events_published += 1
                    self.events_by_topic[topic.value] = self.events_by_topic.get(topic.value, 0) + 1

                    logger.debug(f"Published event to {topic.value} (id={event.event_id})")
                    return True

                except Exception as e:
                    if attempt < self.max_retries:
                        backoff = self.retry_backoff_base ** attempt
                        logger.warning(f"Publish retry {attempt + 1}/{self.max_retries + 1}: {e}")
                        await asyncio.sleep(backoff)
                    else:
                        logger.error(f"Failed to publish after {self.max_retries + 1} attempts: {e}")
                        self._producer_available = False

        # Graceful degradation - log to file
        if self.enable_degraded_mode:
            self._log_event_to_file(topic, event_dict)
            self.events_failed += 1
            return False
        else:
            raise RuntimeError(f"Failed to publish event to {topic.value}")

    def _log_event_to_file(self, topic: EventTopic, event_data: dict[str, Any]) -> None:
        """Fallback: log event to file when Kafka unavailable."""
        try:
            with open(f"/tmp/{self.service_name}_events_fallback.jsonl", "a") as f:
                f.write(
                    json.dumps({
                        "topic": topic.value,
                        "event": event_data,
                        "logged_at": datetime.utcnow().isoformat(),
                    }) + "\n"
                )
            logger.warning(f"Event logged to fallback file: {topic.value}")
        except Exception as e:
            logger.error(f"Failed to log event to fallback file: {e}")

    # ==================== CONSUMER METHODS ====================

    async def subscribe(
        self,
        topic: EventTopic,
        handler: EventHandler,
    ) -> None:
        """
        Subscribe to topic and register event handler.

        Args:
            topic: Event topic to subscribe to
            handler: Async function to handle events
        """
        if topic not in self._handlers:
            self._handlers[topic] = []

        self._handlers[topic].append(handler)

        if topic not in self._subscribed_topics:
            self._subscribed_topics.append(topic)

        logger.info(f"Subscribed to {topic.value}")

        # Restart consumer if already running
        if self._running and self.enable_consumer:
            if self._consumer:
                await self._consumer.stop()
            await self._start_consumer()

    async def _consume_loop(self) -> None:
        """Background task for consuming events."""
        logger.info("Consumer loop started")

        try:
            async for message in self._consumer:
                try:
                    topic = EventTopic(message.topic)
                    event_data = message.value

                    # Route to handlers
                    if topic in self._handlers:
                        for handler in self._handlers[topic]:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(event_data)
                                else:
                                    handler(event_data)
                            except Exception as e:
                                logger.error(f"Handler error for {topic.value}: {e}")

                    # Update metrics
                    self.events_consumed += 1
                    self.events_by_topic[topic.value] = self.events_by_topic.get(topic.value, 0) + 1

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled")
        except Exception as e:
            logger.error(f"Consumer loop error: {e}")

    # ==================== STATUS & METRICS ====================

    def is_available(self) -> bool:
        """Check if Kafka is available."""
        producer_ok = not self.enable_producer or self._producer_available
        consumer_ok = not self.enable_consumer or self._consumer_available
        return self._running and producer_ok and consumer_ok

    def get_metrics(self) -> dict[str, Any]:
        """Get client metrics."""
        return {
            "running": self._running,
            "producer_available": self._producer_available,
            "consumer_available": self._consumer_available,
            "events_published": self.events_published,
            "events_consumed": self.events_consumed,
            "events_failed": self.events_failed,
            "events_by_topic": self.events_by_topic.copy(),
            "subscribed_topics": [t.value for t in self._subscribed_topics],
        }

    def __repr__(self) -> str:
        return (
            f"UnifiedKafkaClient(service={self.service_name}, "
            f"running={self._running}, "
            f"producer={self._producer_available}, "
            f"consumer={self._consumer_available})"
        )
