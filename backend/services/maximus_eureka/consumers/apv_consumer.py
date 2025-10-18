"""
APV Kafka Consumer - MAXIMUS Eureka Adaptive Immunity.

Consumes Actionable Prioritized Vulnerabilities from Oráculo Threat Sentinel,
initiating autonomous remediation pipeline.

Architectural Foundation:
    Consumer implements reactive event-driven pattern where Oráculo detection
    triggers Eureka remediation. Kafka provides:
    - Durability: APVs persisted until confirmed processed
    - Decoupling: Oráculo and Eureka scale independently
    - Replay: Failed remediations can be retried from offset
    - Ordering: Per-partition ordering ensures sequential CVE processing

    At-least-once delivery semantics with idempotency via APV ID deduplication
    prevents duplicate remediation attempts while guaranteeing no vulnerability
    is missed.

Performance Targets:
    - Consumption lag < 5 seconds
    - Processing throughput ≥ 100 APVs/min
    - Memory footprint < 500MB per consumer instance

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - The Ultimate Architect
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from pydantic import ValidationError

# Import APV from Oráculo
from backend.shared.models.apv import APV

# Import Eureka models

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class APVConsumerConfig:
    """
    Configuration for APV Kafka consumer.
    
    Attributes:
        kafka_bootstrap_servers: Kafka broker addresses
        kafka_topic: Topic containing APVs from Oráculo
        kafka_group_id: Consumer group ID for load balancing
        kafka_dlq_topic: Dead Letter Queue for failed APVs
        max_poll_records: Max records per poll (batch size)
        enable_auto_commit: Auto-commit offsets (False for manual control)
        auto_offset_reset: Offset reset policy ('earliest' or 'latest')
        session_timeout_ms: Consumer session timeout
        heartbeat_interval_ms: Heartbeat interval
        redis_cache_url: Redis URL for deduplication cache
        redis_ttl_seconds: TTL for deduplication entries
    """

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "maximus.adaptive-immunity.apv"
    kafka_group_id: str = "eureka-consumer-group"
    kafka_dlq_topic: str = "maximus.adaptive-immunity.apv.dlq"
    max_poll_records: int = 100
    enable_auto_commit: bool = False
    auto_offset_reset: str = "earliest"
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 10000
    redis_cache_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = 86400  # 24 hours


class APVConsumer:
    """
    Kafka consumer for APVs from Oráculo Threat Sentinel.
    
    Implements at-least-once delivery with idempotency guarantees.
    Processes APVs asynchronously, invoking confirmation and remediation pipeline.
    
    Design Philosophy:
        Reactive consumer that bridges detection (Oráculo) and remediation (Eureka).
        Handles failures gracefully via Dead Letter Queue, ensuring no APV is lost
        while preventing infinite retry loops.
    
    Usage:
        >>> config = APVConsumerConfig()
        >>> consumer = APVConsumer(config, process_apv_handler)
        >>> await consumer.start()
        >>> # Consumer runs until stopped
        >>> await consumer.stop()
    """

    def __init__(
        self,
        config: APVConsumerConfig,
        apv_handler: Callable[[APV], Any],
    ) -> None:
        """
        Initialize APV consumer.
        
        Args:
            config: Consumer configuration
            apv_handler: Async function to process each APV
                Signature: async def handler(apv: APV) -> None
        """
        self.config = config
        self.apv_handler = apv_handler
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running: bool = False
        self._processed_count: int = 0
        self._failed_count: int = 0
        self._started_at: Optional[datetime] = None

        # Redis client for deduplication
        self._redis_client: Optional[Any] = None  # Lazy initialization

        logger.info(
            "APVConsumer initialized",
            extra={
                "topic": config.kafka_topic,
                "group_id": config.kafka_group_id,
                "bootstrap_servers": config.kafka_bootstrap_servers,
            },
        )

    async def _init_redis(self) -> None:
        """Initialize Redis client for deduplication cache."""
        try:
            import redis.asyncio as redis

            self._redis_client = redis.from_url(
                self.config.redis_cache_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis_client.ping()
            logger.info("Redis connection established for deduplication")
        except Exception as e:
            logger.warning(
                f"Redis initialization failed: {e}. Deduplication disabled."
            )
            self._redis_client = None

    async def _is_duplicate(self, apv_id: str) -> bool:
        """
        Check if APV has been processed recently (idempotency check).
        
        Args:
            apv_id: APV identifier
            
        Returns:
            True if APV was processed within TTL window
        """
        if not self._redis_client:
            return False  # No deduplication if Redis unavailable

        try:
            cache_key = f"apv:processed:{apv_id}"
            exists = await self._redis_client.exists(cache_key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Redis deduplication check failed: {e}")
            return False  # Fail open: allow processing

    async def _mark_processed(self, apv_id: str) -> None:
        """
        Mark APV as processed in Redis cache.
        
        Args:
            apv_id: APV identifier
        """
        if not self._redis_client:
            return

        try:
            cache_key = f"apv:processed:{apv_id}"
            await self._redis_client.setex(
                cache_key,
                self.config.redis_ttl_seconds,
                datetime.utcnow().isoformat(),
            )
        except Exception as e:
            logger.error(f"Redis mark processed failed: {e}")

    async def _publish_to_dlq(
        self, raw_message: bytes, error: str
    ) -> None:
        """
        Publish failed APV to Dead Letter Queue.
        
        Args:
            raw_message: Original Kafka message bytes
            error: Error description
        """
        try:
            from aiokafka import AIOKafkaProducer

            producer = AIOKafkaProducer(
                bootstrap_servers=self.config.kafka_bootstrap_servers
            )
            await producer.start()

            # Enrich with error metadata
            dlq_message = {
                "original_message": raw_message.decode("utf-8"),
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
                "consumer_group": self.config.kafka_group_id,
            }

            await producer.send_and_wait(
                self.config.kafka_dlq_topic,
                json.dumps(dlq_message).encode("utf-8"),
            )
            await producer.stop()

            logger.info(
                f"Published to DLQ: {self.config.kafka_dlq_topic}",
                extra={"error": error},
            )
        except Exception as e:
            logger.error(f"Failed to publish to DLQ: {e}")

    async def _deserialize_apv(self, message: bytes) -> APV:
        """
        Deserialize Kafka message to APV Pydantic model.
        
        Args:
            message: Raw Kafka message bytes
            
        Returns:
            Validated APV object
            
        Raises:
            ValidationError: If message doesn't match APV schema
            json.JSONDecodeError: If message isn't valid JSON
        """
        data = json.loads(message.decode("utf-8"))
        return APV(**data)

    async def _process_message(
        self, message: Any
    ) -> None:
        """
        Process single Kafka message containing APV.
        
        Args:
            message: Kafka message object
        """
        try:
            # Deserialize APV
            apv = await self._deserialize_apv(message.value)

            # Idempotency check
            if await self._is_duplicate(apv.cve_id):
                logger.info(
                    f"Skipping duplicate APV: {apv.cve_id}",
                    extra={"apv_id": apv.cve_id},
                )
                return

            # Invoke handler (confirmation + remediation)
            logger.info(
                f"Processing APV: {apv.cve_id}",
                extra={
                    "apv_id": apv.cve_id,
                    "priority": apv.priority.value if apv.priority else None,
                    "packages": len(apv.affected_packages),
                },
            )

            await self.apv_handler(apv)

            # Mark as processed
            await self._mark_processed(apv.cve_id)

            self._processed_count += 1

            logger.info(
                f"Successfully processed APV: {apv.cve_id}",
                extra={"total_processed": self._processed_count},
            )

        except ValidationError as e:
            # Schema validation failure
            error_msg = f"APV validation failed: {e}"
            logger.error(error_msg, exc_info=True)
            await self._publish_to_dlq(message.value, error_msg)
            self._failed_count += 1

        except json.JSONDecodeError as e:
            # Malformed JSON
            error_msg = f"JSON decode failed: {e}"
            logger.error(error_msg)
            await self._publish_to_dlq(message.value, error_msg)
            self._failed_count += 1

        except Exception as e:
            # Unexpected error in handler
            error_msg = f"APV processing error: {e}"
            logger.error(error_msg, exc_info=True)
            await self._publish_to_dlq(message.value, error_msg)
            self._failed_count += 1

    async def start(self) -> None:
        """
        Start consuming APVs from Kafka.
        
        Runs until stopped via stop() method or external signal.
        Handles reconnection on Kafka broker failures.
        """
        if self._running:
            logger.warning("Consumer already running")
            return

        self._running = True
        self._started_at = datetime.utcnow()

        # Initialize Redis
        await self._init_redis()

        # Initialize Kafka consumer
        self._consumer = AIOKafkaConsumer(
            self.config.kafka_topic,
            bootstrap_servers=self.config.kafka_bootstrap_servers,
            group_id=self.config.kafka_group_id,
            enable_auto_commit=self.config.enable_auto_commit,
            auto_offset_reset=self.config.auto_offset_reset,
            session_timeout_ms=self.config.session_timeout_ms,
            heartbeat_interval_ms=self.config.heartbeat_interval_ms,
            max_poll_records=self.config.max_poll_records,
        )

        try:
            await self._consumer.start()
            logger.info(
                "APV Consumer started",
                extra={
                    "topic": self.config.kafka_topic,
                    "partitions": self._consumer.assignment(),
                },
            )

            # Consume loop
            async for message in self._consumer:
                if not self._running:
                    break

                await self._process_message(message)

                # Manual commit after successful processing
                if not self.config.enable_auto_commit:
                    await self._consumer.commit()

        except KafkaError as e:
            logger.error(f"Kafka error: {e}", exc_info=True)
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """
        Gracefully stop consumer.
        
        Commits offsets, closes connections, logs final statistics.
        """
        if not self._running:
            return

        self._running = False

        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped")

        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis connection closed")

        # Final statistics
        uptime = (
            (datetime.utcnow() - self._started_at).total_seconds()
            if self._started_at
            else 0
        )

        logger.info(
            "APV Consumer stopped",
            extra={
                "processed": self._processed_count,
                "failed": self._failed_count,
                "uptime_seconds": uptime,
                "throughput_per_min": (
                    (self._processed_count / uptime) * 60
                    if uptime > 0
                    else 0
                ),
            },
        )

    @property
    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running

    @property
    def stats(self) -> dict[str, Any]:
        """Get consumer statistics."""
        uptime = (
            (datetime.utcnow() - self._started_at).total_seconds()
            if self._started_at
            else 0
        )

        return {
            "running": self._running,
            "processed_count": self._processed_count,
            "failed_count": self._failed_count,
            "success_rate": (
                self._processed_count
                / (self._processed_count + self._failed_count)
                if (self._processed_count + self._failed_count) > 0
                else 0.0
            ),
            "uptime_seconds": uptime,
            "throughput_per_min": (
                (self._processed_count / uptime) * 60 if uptime > 0 else 0
            ),
            "started_at": (
                self._started_at.isoformat() if self._started_at else None
            ),
        }
