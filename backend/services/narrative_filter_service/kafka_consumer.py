"""Kafka consumer for agent communications."""

import json
from typing import Any

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from narrative_filter_service.config import settings
from narrative_filter_service.models import SemanticRepresentation
from narrative_filter_service.repository import SemanticRepository
from narrative_filter_service.semantic_processor import SemanticProcessor

logger = structlog.get_logger()


class TelemetryConsumer:
    """Kafka consumer for agent communication telemetry."""

    def __init__(self, processor: SemanticProcessor, repository: SemanticRepository) -> None:
        """Initialize consumer.

        Args:
            processor: SemanticProcessor instance
            repository: SemanticRepository instance
        """
        self.processor = processor
        self.repository = repository
        self.consumer: AIOKafkaConsumer | None = None
        self.producer: AIOKafkaProducer | None = None
        self.running = False

    async def start(self) -> None:
        """Start Kafka consumer and producer."""
        self.consumer = AIOKafkaConsumer(
            settings.kafka_topic_input,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )

        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        await self.consumer.start()
        await self.producer.start()
        self.running = True

        logger.info("telemetry_consumer_started", topic=settings.kafka_topic_input)

    async def stop(self) -> None:
        """Stop Kafka consumer and producer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
        logger.info("telemetry_consumer_stopped")

    async def consume(self) -> None:
        """Consume and process messages."""
        if not self.consumer or not self.producer:
            raise RuntimeError("Consumer not started. Call start() first.")

        async for msg in self.consumer:
            try:
                await self.process_message(msg.value)
            except Exception as e:
                logger.error("message_processing_error", error=str(e), message_id=msg.value.get("message_id"))

    async def process_message(self, message: dict[str, Any]) -> None:
        """Process a single message.

        Args:
            message: Message dict from Kafka
        """
        # Extract fields
        message_id = message.get("message_id")
        source_agent_id = message.get("source_agent_id")
        content = message.get("content")

        if not all([message_id, source_agent_id, content]):
            logger.warning("incomplete_message", message=message)
            return

        # Process semantically
        representation = await self.processor.process_message(
            message_id=message_id,
            source_agent_id=source_agent_id,
            content=content,
            timestamp=message.get("timestamp"),
            provenance_chain=message.get("provenance_chain"),
        )

        # Persist to database
        await self.repository.create(representation)

        # Publish to semantic-events topic
        await self.publish_semantic_event(representation)

        logger.info(
            "message_processed",
            message_id=message_id,
            agent_id=source_agent_id,
            intent=representation.intent_classification.value,
            confidence=representation.intent_confidence,
        )

    async def publish_semantic_event(self, representation: SemanticRepresentation) -> None:
        """Publish semantic event to Kafka.

        Args:
            representation: SemanticRepresentation to publish
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")

        event = {
            "message_id": representation.message_id,
            "source_agent_id": representation.source_agent_id,
            "timestamp": representation.timestamp.isoformat(),
            "intent_classification": representation.intent_classification.value,
            "intent_confidence": representation.intent_confidence,
            "embedding_sample": representation.content_embedding[:10],  # First 10 dims for debug
            "raw_content": representation.raw_content,
        }

        await self.producer.send(settings.kafka_topic_semantic, value=event)

    async def run(self) -> None:
        """Run consumer loop."""
        await self.start()
        try:
            await self.consume()
        finally:
            await self.stop()
