"""Kafka consumer for strategic pattern detection."""

import json
from typing import Any

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from narrative_filter_service.config import settings
from narrative_filter_service.repository import SemanticRepository
from narrative_filter_service.strategic_detector import StrategicPatternDetector
from narrative_filter_service.strategic_repository import AllianceRepository, StrategicPatternRepository

logger = structlog.get_logger()


class StrategicConsumer:
    """Kafka consumer for strategic pattern detection."""

    def __init__(
        self,
        detector: StrategicPatternDetector,
        semantic_repo: SemanticRepository,
        pattern_repo: StrategicPatternRepository,
        alliance_repo: AllianceRepository,
    ) -> None:
        """Initialize consumer.

        Args:
            detector: StrategicPatternDetector instance
            semantic_repo: SemanticRepository instance
            pattern_repo: StrategicPatternRepository instance
            alliance_repo: AllianceRepository instance
        """
        self.detector = detector
        self.semantic_repo = semantic_repo
        self.pattern_repo = pattern_repo
        self.alliance_repo = alliance_repo
        self.consumer: AIOKafkaConsumer | None = None
        self.producer: AIOKafkaProducer | None = None
        self.running = False

    async def start(self) -> None:
        """Start Kafka consumer and producer."""
        self.consumer = AIOKafkaConsumer(
            settings.kafka_topic_semantic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="strategic-pattern-group",
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

        logger.info("strategic_consumer_started", topic=settings.kafka_topic_semantic)

    async def stop(self) -> None:
        """Stop Kafka consumer and producer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
        logger.info("strategic_consumer_stopped")

    async def process_batch(self, batch_size: int = 50, time_window_hours: int = 24) -> None:
        """Process a batch of semantic events to detect patterns.

        Args:
            batch_size: Number of events to process in batch
            time_window_hours: Time window for pattern detection
        """
        # Get recent semantic representations from DB
        # (In production, would maintain in-memory cache)
        logger.info("strategic_batch_processing", batch_size=batch_size, window_hours=time_window_hours)

    async def consume(self) -> None:
        """Consume and process messages."""
        if not self.consumer or not self.producer:
            raise RuntimeError("Consumer not started. Call start() first.")

        batch: list[dict[str, Any]] = []
        batch_size = 50

        async for msg in self.consumer:
            try:
                batch.append(msg.value)

                if len(batch) >= batch_size:
                    await self.process_batch(len(batch))
                    batch = []

            except Exception as e:
                logger.error("strategic_processing_error", error=str(e))

    async def run(self) -> None:
        """Run consumer loop."""
        await self.start()
        try:
            await self.consume()
        finally:
            await self.stop()
