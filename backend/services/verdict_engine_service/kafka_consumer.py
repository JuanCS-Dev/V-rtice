"""Kafka consumer for verdicts stream.

Consumes verdicts from verdicts-stream topic (produced by narrative_filter),
broadcasts to WebSocket clients, updates cache.
"""

import asyncio
import json
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from aiokafka import AIOKafkaConsumer

from services.verdict_engine_service.cache import VerdictCache
from services.verdict_engine_service.config import settings
from services.verdict_engine_service.models import Verdict
from services.verdict_engine_service.websocket_manager import ConnectionManager

logger = structlog.get_logger()


class VerdictConsumer:
    """Kafka consumer for verdict streaming."""

    def __init__(
        self,
        cache: VerdictCache,
        ws_manager: ConnectionManager,
    ) -> None:
        """Initialize consumer."""
        self.cache = cache
        self.ws_manager = ws_manager
        self.consumer: AIOKafkaConsumer | None = None
        self.running = False

    async def start(self) -> None:
        """Start Kafka consumer."""
        self.consumer = AIOKafkaConsumer(
            settings.kafka_verdicts_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            auto_offset_reset=settings.kafka_auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        await self.consumer.start()
        self.running = True
        logger.info(
            "kafka_consumer_started",
            topic=settings.kafka_verdicts_topic,
            group=settings.kafka_consumer_group,
        )

    async def stop(self) -> None:
        """Stop Kafka consumer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("kafka_consumer_stopped")

    async def consume(self) -> None:
        """Consume messages from Kafka and broadcast."""
        if not self.consumer:
            raise RuntimeError("Consumer not started")

        async for message in self.consumer:
            try:
                # Parse verdict from Kafka message
                verdict_data = message.value
                verdict = self._parse_verdict(verdict_data)

                # Cache verdict
                await self.cache.cache_verdict(verdict)

                # Broadcast to WebSocket clients
                await self.ws_manager.broadcast_verdict(verdict)

                # Invalidate stats cache (new verdict affects stats)
                await self.cache.invalidate_stats()

                logger.info(
                    "verdict_processed",
                    verdict_id=str(verdict.id),
                    severity=verdict.severity,
                    category=verdict.category,
                    connections=self.ws_manager.get_connection_count(),
                )

            except Exception as e:
                logger.error(
                    "verdict_processing_failed",
                    error=str(e),
                    message_value=message.value,
                )

    def _parse_verdict(self, data: dict[str, Any]) -> Verdict:
        """Parse verdict from Kafka message."""
        # Handle UUID conversion
        if isinstance(data.get("id"), str):
            data["id"] = UUID(data["id"])
        if data.get("mitigation_command_id") and isinstance(data["mitigation_command_id"], str):
            data["mitigation_command_id"] = UUID(data["mitigation_command_id"])

        # Handle Decimal conversion
        if isinstance(data.get("confidence"), float | str):
            data["confidence"] = Decimal(str(data["confidence"]))

        return Verdict(**data)


async def start_consumer_task(
    cache: VerdictCache,
    ws_manager: ConnectionManager,
) -> VerdictConsumer:
    """Start verdict consumer as background task."""
    consumer = VerdictConsumer(cache, ws_manager)
    await consumer.start()

    # Run consume loop in background
    asyncio.create_task(consumer.consume())

    return consumer
