"""
Kafka Metrics Streamer

Streams collected metrics to Kafka topic 'system.telemetry.raw' for real-time processing.
"""

import asyncio
import json
import logging
from typing import Any, Dict

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaError = Exception

logger = logging.getLogger(__name__)


class KafkaMetricsStreamer:
    """
    Streams metrics to Kafka for real-time processing.

    Enables downstream components to react to telemetry in real-time
    without querying the database.
    """

    def __init__(
        self, broker: str = "localhost:9092", topic: str = "system.telemetry.raw"
    ):
        """
        Initialize Kafka streamer.

        Args:
            broker: Kafka broker address
            topic: Topic name for telemetry data
        """
        self.broker = broker
        self.topic = topic
        self.producer = None
        self.messages_sent = 0
        self.errors = 0

        self._connect()

    def _connect(self):
        """Connect to Kafka broker."""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka client not available, metrics will not be streamed")
            self.producer = None
            return

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.broker,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,  # Maintain ordering
            )
            logger.info(f"Connected to Kafka broker: {self.broker}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.producer = None

    async def send(self, metrics: Dict[str, Any]) -> bool:
        """
        Send metrics to Kafka topic.

        Args:
            metrics: Dictionary of metric_name -> value pairs

        Returns:
            True if successful, False otherwise
        """
        if not self.producer:
            logger.warning("Kafka producer not initialized, attempting reconnect")
            self._connect()
            if not self.producer:
                return False

        try:
            # Send to Kafka
            future = self.producer.send(self.topic, value=metrics)

            # Wait for send to complete (with timeout)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, future.get, 5)  # 5s timeout

            self.messages_sent += 1

            if self.messages_sent % 100 == 0:
                logger.info(
                    f"Streamed {self.messages_sent} metric batches "
                    f"(errors: {self.errors})"
                )

            return True

        except KafkaError as e:
            self.errors += 1
            logger.error(f"Kafka send error: {e}")
            return False
        except Exception as e:
            self.errors += 1
            logger.error(f"Unexpected error sending to Kafka: {e}")
            return False

    async def close(self):
        """Close Kafka producer connection."""
        if self.producer:
            logger.info("Closing Kafka producer")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.producer.close)
            self.producer = None

    def get_stats(self) -> Dict[str, int]:
        """
        Get streaming statistics.

        Returns:
            Dictionary with messages_sent and errors
        """
        return {
            "messages_sent": self.messages_sent,
            "errors": self.errors,
            "success_rate": (
                (self.messages_sent / (self.messages_sent + self.errors) * 100)
                if (self.messages_sent + self.errors) > 0
                else 0
            ),
        }
