"""
Kafka Client for Cognitive Defense System.

Implements event-driven architecture with async Kafka producers/consumers
for scalable, decoupled processing pipeline.
"""

import logging
import json
import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
from aiokafka.structs import TopicPartition

from config import get_settings

logger = logging.getLogger(__name__)


class KafkaClient:
    """Manages Kafka producers and consumers for event streaming."""

    def __init__(self):
        """Initialize Kafka client."""
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.settings = get_settings()
        self._consumer_tasks: List[asyncio.Task] = []

    async def initialize_producer(self) -> None:
        """
        Initialize Kafka producer for sending events.

        Producer is configured for reliability with idempotent writes
        and compression for network efficiency.
        """
        if self.producer is not None:
            logger.warning("Producer already initialized, skipping")
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type='gzip',
                acks='all',  # Wait for all replicas
                enable_idempotence=True,  # Exactly-once semantics
                request_timeout_ms=30000,
            )

            await self.producer.start()

            logger.info(
                f"✅ Kafka producer initialized: {self.settings.KAFKA_BOOTSTRAP_SERVERS}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka producer: {e}")
            raise

    async def close_producer(self) -> None:
        """Close Kafka producer."""
        if self.producer is not None:
            await self.producer.stop()
            self.producer = None
            logger.info("✅ Kafka producer closed")

    async def send_event(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None,
        partition: Optional[int] = None
    ) -> bool:
        """
        Send event to Kafka topic.

        Args:
            topic: Kafka topic name
            message: Event payload (will be JSON serialized)
            key: Partition key (optional)
            partition: Specific partition (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if self.producer is None:
            logger.error("Producer not initialized")
            return False

        try:
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.utcnow().isoformat()

            # Send to Kafka
            await self.producer.send(
                topic=topic,
                value=message,
                key=key,
                partition=partition
            )

            logger.debug(f"Sent event to {topic}: {key or 'no-key'}")
            return True

        except KafkaError as e:
            logger.error(f"Kafka send error to {topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending to {topic}: {e}")
            return False

    async def create_consumer(
        self,
        topics: List[str],
        group_id: str,
        auto_offset_reset: str = 'earliest'
    ) -> AIOKafkaConsumer:
        """
        Create Kafka consumer for specified topics.

        Args:
            topics: List of topic names to subscribe
            group_id: Consumer group ID
            auto_offset_reset: 'earliest' or 'latest'

        Returns:
            Initialized consumer instance
        """
        try:
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                max_poll_records=100,
                session_timeout_ms=30000,
            )

            await consumer.start()
            self.consumers[group_id] = consumer

            logger.info(f"✅ Kafka consumer created: {group_id} -> {topics}")
            return consumer

        except Exception as e:
            logger.error(f"❌ Failed to create consumer {group_id}: {e}")
            raise

    async def close_consumer(self, group_id: str) -> None:
        """Close specific consumer by group ID."""
        if group_id in self.consumers:
            await self.consumers[group_id].stop()
            del self.consumers[group_id]
            logger.info(f"✅ Kafka consumer closed: {group_id}")

    async def close_all_consumers(self) -> None:
        """Close all active consumers."""
        for group_id in list(self.consumers.keys()):
            await self.close_consumer(group_id)

        # Cancel all consumer tasks
        for task in self._consumer_tasks:
            task.cancel()
        await asyncio.gather(*self._consumer_tasks, return_exceptions=True)
        self._consumer_tasks.clear()

    async def consume_messages(
        self,
        topics: List[str],
        group_id: str,
        message_handler: Callable,
        auto_offset_reset: str = 'earliest'
    ) -> None:
        """
        Consume messages from topics with handler function.

        Args:
            topics: List of topics to consume
            group_id: Consumer group ID
            message_handler: Async function to process each message
            auto_offset_reset: Offset reset strategy
        """
        consumer = await self.create_consumer(topics, group_id, auto_offset_reset)

        try:
            async for message in consumer:
                try:
                    await message_handler(
                        topic=message.topic,
                        key=message.key,
                        value=message.value,
                        partition=message.partition,
                        offset=message.offset
                    )
                except Exception as e:
                    logger.error(
                        f"Error in message handler for {message.topic}/{message.partition}/{message.offset}: {e}"
                    )
                    # Continue processing other messages

        except asyncio.CancelledError:
            logger.info(f"Consumer {group_id} cancelled")
        except Exception as e:
            logger.error(f"Consumer {group_id} error: {e}")
        finally:
            await self.close_consumer(group_id)

    def start_consumer_background(
        self,
        topics: List[str],
        group_id: str,
        message_handler: Callable,
        auto_offset_reset: str = 'earliest'
    ) -> asyncio.Task:
        """
        Start consumer in background task.

        Args:
            topics: List of topics
            group_id: Consumer group ID
            message_handler: Message processing function
            auto_offset_reset: Offset strategy

        Returns:
            Background task
        """
        task = asyncio.create_task(
            self.consume_messages(topics, group_id, message_handler, auto_offset_reset)
        )
        self._consumer_tasks.append(task)
        logger.info(f"Started background consumer: {group_id}")
        return task

    async def health_check(self) -> bool:
        """
        Check Kafka connectivity.

        Returns:
            True if healthy, False otherwise
        """
        if self.producer is None:
            return False

        try:
            # Try to send a test message to a health topic
            await self.producer.send(
                topic=self.settings.KAFKA_TOPIC_ERRORS,
                value={'type': 'health_check', 'timestamp': datetime.utcnow().isoformat()}
            )
            return True
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False


# ============================================================================
# TOPIC-SPECIFIC HELPER FUNCTIONS
# ============================================================================

async def send_raw_text_event(client: KafkaClient, text: str, analysis_id: str, metadata: Dict = None) -> bool:
    """Send raw text to processing pipeline."""
    return await client.send_event(
        topic=client.settings.KAFKA_TOPIC_RAW_TEXT,
        message={
            'analysis_id': analysis_id,
            'text': text,
            'metadata': metadata or {}
        },
        key=analysis_id
    )


async def send_processed_text_event(
    client: KafkaClient,
    analysis_id: str,
    entities: List[Dict],
    arguments: List[Dict],
    metadata: Dict = None
) -> bool:
    """Send processed text with extracted features."""
    return await client.send_event(
        topic=client.settings.KAFKA_TOPIC_PROCESSED_TEXT,
        message={
            'analysis_id': analysis_id,
            'entities': entities,
            'arguments': arguments,
            'metadata': metadata or {}
        },
        key=analysis_id
    )


async def send_claim_verification_request(
    client: KafkaClient,
    analysis_id: str,
    claims: List[str],
    priority: int = 5
) -> bool:
    """Send claims for Tier 2 verification."""
    return await client.send_event(
        topic=client.settings.KAFKA_TOPIC_CLAIMS_TO_VERIFY,
        message={
            'analysis_id': analysis_id,
            'claims': claims,
            'priority': priority,
            'request_timestamp': datetime.utcnow().isoformat()
        },
        key=analysis_id
    )


async def send_verification_result(
    client: KafkaClient,
    analysis_id: str,
    claim: str,
    verification_status: str,
    sources: List[Dict],
    confidence: float
) -> bool:
    """Send verification result back to pipeline."""
    return await client.send_event(
        topic=client.settings.KAFKA_TOPIC_VERIFICATION_RESULTS,
        message={
            'analysis_id': analysis_id,
            'claim': claim,
            'verification_status': verification_status,
            'sources': sources,
            'confidence': confidence,
            'verified_at': datetime.utcnow().isoformat()
        },
        key=analysis_id
    )


async def send_analysis_complete(
    client: KafkaClient,
    analysis_id: str,
    threat_score: float,
    severity: str,
    processing_time_ms: float
) -> bool:
    """Send final analysis result."""
    return await client.send_event(
        topic=client.settings.KAFKA_TOPIC_ANALYSIS_RESULTS,
        message={
            'analysis_id': analysis_id,
            'threat_score': threat_score,
            'severity': severity,
            'processing_time_ms': processing_time_ms,
            'completed_at': datetime.utcnow().isoformat()
        },
        key=analysis_id
    )


async def send_error_event(
    client: KafkaClient,
    error_type: str,
    error_message: str,
    context: Dict = None
) -> bool:
    """Send error event for monitoring."""
    return await client.send_event(
        topic=client.settings.KAFKA_TOPIC_ERRORS,
        message={
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'timestamp': datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

kafka_client = KafkaClient()


# ============================================================================
# LIFESPAN MANAGEMENT FOR FASTAPI
# ============================================================================

@asynccontextmanager
async def lifespan_kafka(app):
    """
    FastAPI lifespan context for Kafka initialization/cleanup.

    Usage:
        app = FastAPI(lifespan=lifespan_kafka)
    """
    # Startup
    logger.info("🚀 Initializing Kafka client...")
    await kafka_client.initialize_producer()

    # Optionally start background consumers here
    # Example:
    # kafka_client.start_consumer_background(
    #     topics=['claims_to_verify'],
    #     group_id='tier2_verifier',
    #     message_handler=tier2_verification_handler
    # )

    yield

    # Shutdown
    logger.info("🛑 Closing Kafka connections...")
    await kafka_client.close_all_consumers()
    await kafka_client.close_producer()
