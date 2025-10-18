"""
Base collector abstract class for all intelligence collectors.

This module defines the interface that all collectors must implement,
ensuring consistent behavior across different intelligence sources.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncIterator
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
import os

logger = logging.getLogger(__name__)


class CollectorHealth(str, Enum):
    """Health status of a collector."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class CollectorMetrics(BaseModel):
    """Metrics for monitoring collector performance."""

    collector_id: UUID = Field(default_factory=uuid4)
    collector_type: str
    health: CollectorHealth = CollectorHealth.HEALTHY
    events_collected: int = 0
    errors_count: int = 0
    last_collection_time: Optional[datetime] = None
    average_latency_ms: float = 0.0
    throughput_per_second: float = 0.0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CollectorConfig(BaseModel):
    """Base configuration for collectors."""

    enabled: bool = True
    collection_interval_seconds: int = 60
    batch_size: int = 100
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    timeout_seconds: int = 30
    rate_limit_per_minute: Optional[int] = None


class CollectedEvent(BaseModel):
    """Base model for all collected events."""

    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    collector_type: str
    source: str
    severity: str = "info"  # info, low, medium, high, critical
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    raw_data: Optional[Dict[str, Any]] = None
    parsed_data: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseCollector(ABC):
    """
    Abstract base class for all intelligence collectors.

    All collectors must implement passive collection only (Phase 1 compliance).
    No automated responses are allowed, only observation and reporting.
    """

    def __init__(self, config: CollectorConfig):
        """
        Initialize the base collector.

        Args:
            config: Collector configuration
        """
        self.config = config
        self.metrics = CollectorMetrics(
            collector_type=self.__class__.__name__
        )
        self._running = False
        self._start_time = datetime.utcnow()
        self._collection_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize collector resources.

        This method should establish connections, validate credentials,
        and prepare the collector for operation.
        """
        pass

    @abstractmethod
    async def collect(self) -> AsyncIterator[CollectedEvent]:
        """
        Collect events from the source.

        Yields:
            CollectedEvent: Events collected from the source
        """
        pass

    @abstractmethod
    async def validate_source(self) -> bool:
        """
        Validate that the collection source is accessible.

        Returns:
            bool: True if source is valid and accessible
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up collector resources.

        This method should close connections and release resources.
        """
        pass

    async def start(self) -> None:
        """Start the collector."""
        if self._running:
            logger.warning(f"{self.__class__.__name__} is already running")
            return

        try:
            logger.info(f"Starting {self.__class__.__name__}")
            await self.initialize()

            if not await self.validate_source():
                raise RuntimeError(f"Source validation failed for {self.__class__.__name__}")

            self._running = True
            self._start_time = datetime.utcnow()
            self._collection_task = asyncio.create_task(self._collection_loop())

            self.metrics.health = CollectorHealth.HEALTHY
            logger.info(f"{self.__class__.__name__} started successfully")

        except Exception as e:
            logger.error(f"Failed to start {self.__class__.__name__}: {e}")
            self.metrics.health = CollectorHealth.UNHEALTHY
            self.metrics.errors_count += 1
            raise

    async def stop(self) -> None:
        """Stop the collector."""
        if not self._running:
            logger.warning(f"{self.__class__.__name__} is not running")
            return

        logger.info(f"Stopping {self.__class__.__name__}")
        self._running = False
        self._shutdown_event.set()

        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        await self.cleanup()
        self.metrics.health = CollectorHealth.OFFLINE
        logger.info(f"{self.__class__.__name__} stopped")

    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while self._running:
            try:
                collection_start = datetime.utcnow()
                event_count = 0

                async for event in self.collect():
                    event_count += 1
                    await self._process_event(event)

                    if self.config.batch_size and event_count >= self.config.batch_size:
                        break

                # Update metrics
                collection_time = (datetime.utcnow() - collection_start).total_seconds()
                self.metrics.events_collected += event_count
                self.metrics.last_collection_time = datetime.utcnow()
                self.metrics.average_latency_ms = (collection_time * 1000) / max(event_count, 1)
                self.metrics.throughput_per_second = event_count / max(collection_time, 0.001)
                self.metrics.uptime_seconds = (
                    datetime.utcnow() - self._start_time
                ).total_seconds()

                # Wait for next collection interval
                await asyncio.sleep(self.config.collection_interval_seconds)

            except Exception as e:
                logger.error(f"Collection error in {self.__class__.__name__}: {e}")
                self.metrics.errors_count += 1
                self.metrics.health = CollectorHealth.DEGRADED

                # Retry with exponential backoff
                await asyncio.sleep(self.config.retry_delay_seconds)

    async def _process_event(self, event: CollectedEvent) -> None:
        """
        Process a collected event.

        Phase 1 compliance: This method only logs and stores events.
        No automated responses are triggered.

        Args:
            event: The collected event to process
        """
        # Add collector metadata
        event.metadata["collector_id"] = str(self.metrics.collector_id)
        event.metadata["collection_time"] = datetime.utcnow().isoformat()

        # Log high-severity events
        if event.severity in ["high", "critical"]:
            logger.warning(
                f"High severity event collected by {self.__class__.__name__}: "
                f"{event.event_id} - {event.severity}"
            )

        # Send to event processing pipeline (Kafka/Redis)
        await self._send_to_pipeline(event)
    
    async def _send_to_pipeline(self, event: SecurityEvent) -> None:
        """Send event to processing pipeline (Kafka or Redis)."""
        try:
            # Try Kafka first
            from kafka import KafkaProducer
            import json
            
            kafka_broker = os.getenv("KAFKA_BROKER", "localhost:9092")
            producer = KafkaProducer(
                bootstrap_servers=[kafka_broker],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            )
            
            # Publish to Kafka topic
            producer.send('security_events', {
                "event_id": event.event_id,
                "severity": event.severity.value,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
            })
            producer.flush()
            
            logger.debug(f"Event {event.event_id} sent to Kafka")
            
        except Exception as kafka_error:
            logger.debug(f"Kafka unavailable: {kafka_error}")
            
            # Fallback to Redis
            try:
                from vertice_db.redis_client import get_redis_client
                import json
                
                redis = await get_redis_client()
                await redis.lpush('security_events', json.dumps({
                    "event_id": event.event_id,
                    "severity": event.severity.value,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                }))
                
                logger.debug(f"Event {event.event_id} sent to Redis")
                
            except Exception as redis_error:
                logger.warning(f"Event pipeline unavailable: {redis_error}")

    def get_metrics(self) -> CollectorMetrics:
        """
        Get current collector metrics.

        Returns:
            CollectorMetrics: Current metrics
        """
        return self.metrics

    def is_healthy(self) -> bool:
        """
        Check if collector is healthy.

        Returns:
            bool: True if collector is healthy
        """
        return self.metrics.health == CollectorHealth.HEALTHY

    def __repr__(self) -> str:
        """String representation of the collector."""
        return (
            f"{self.__class__.__name__}("
            f"health={self.metrics.health.value}, "
            f"events={self.metrics.events_collected}, "
            f"errors={self.metrics.errors_count})"
        )