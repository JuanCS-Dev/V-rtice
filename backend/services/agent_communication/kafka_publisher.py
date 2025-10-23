"""
Kafka Publisher for Agent Communication Events

Publishes agent communication events to Kafka topic 'agent-communications'
for consumption by Narrative Filter service.

Air Gap Fix: AG-KAFKA-009
Priority: HIGH (Feature Enablement)
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from kafka import KafkaProducer
from kafka.errors import KafkaError

from .message import ACPMessage

logger = logging.getLogger(__name__)


class AgentCommunicationKafkaPublisher:
    """
    Publishes agent communication events to Kafka.

    Integrates with existing RabbitMQ-based agent communication
    to provide event stream for Narrative Filter semantic analysis.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "agent-communications"
    ):
        """
        Initialize Kafka publisher.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic for agent communication events
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer: Optional[KafkaProducer] = None
        self.connected = False

    def connect(self) -> bool:
        """
        Connect to Kafka broker.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to Kafka: {self.bootstrap_servers}")

            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                request_timeout_ms=10000,
                compression_type="gzip"
            )

            self.connected = True
            logger.info(f"✅ Kafka publisher connected: {self.topic}")
            return True

        except KafkaError as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Kafka: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from Kafka broker."""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                logger.info("Kafka publisher disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting from Kafka: {e}")

        self.connected = False

    def publish_agent_message(
        self,
        message: ACPMessage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish agent communication event to Kafka.

        Args:
            message: ACP message being sent
            metadata: Additional metadata for the event

        Returns:
            True if published successfully, False otherwise
        """
        if not self.connected or not self.producer:
            logger.warning("⚠️  Kafka publisher not connected - skipping publish")
            return False

        try:
            # Build Kafka event
            event = self._build_event(message, metadata)

            # Use agent types as key for partitioning
            key = f"{message.sender.value}-{message.recipient.value}"

            # Publish to Kafka (async fire-and-forget)
            future = self.producer.send(
                self.topic,
                value=event,
                key=key
            )

            # Optional: wait for confirmation (adds latency)
            # result = future.get(timeout=5)
            # logger.debug(f"Published to Kafka: partition={result.partition}, offset={result.offset}")

            logger.debug(
                f"📤 Published to Kafka: {message.message_type.value} | "
                f"{message.sender.value} → {message.recipient.value}"
            )

            return True

        except KafkaError as e:
            logger.error(f"Kafka publish failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing to Kafka: {e}")
            return False

    def _build_event(
        self,
        message: ACPMessage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build Kafka event from ACP message.

        Schema designed for Narrative Filter consumption.
        """
        return {
            # Event metadata
            "event_id": str(uuid4()),
            "event_type": "agent.message.sent",
            "timestamp": datetime.utcnow().isoformat() + "Z",

            # Agent communication details
            "agent_from": message.sender.value,
            "agent_to": message.recipient.value,
            "message_id": str(message.message_id),
            "message_type": message.message_type.value,
            "correlation_id": str(message.correlation_id) if message.correlation_id else None,

            # Message content
            "content": {
                "payload": message.payload,
                "priority": message.priority.value,
                "timestamp": message.timestamp.isoformat() + "Z",
                "correlation_id": str(message.correlation_id) if message.correlation_id else None
            },

            # Additional metadata
            "metadata": metadata or {},

            # Source tracking
            "source": {
                "service": "agent_communication",
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "production")
            }
        }

    def publish_coordination_event(
        self,
        event_type: str,
        agents_involved: list[str],
        description: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish agent coordination event.

        Args:
            event_type: Type of coordination event (e.g., "handoff", "collaboration")
            agents_involved: List of agent types involved
            description: Human-readable description
            data: Additional event data

        Returns:
            True if published successfully, False otherwise
        """
        if not self.connected or not self.producer:
            logger.warning("⚠️  Kafka publisher not connected - skipping publish")
            return False

        try:
            event = {
                "event_id": str(uuid4()),
                "event_type": f"agent.coordination.{event_type}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agents_involved": agents_involved,
                "description": description,
                "data": data or {},
                "source": {
                    "service": "agent_communication",
                    "version": "1.0.0"
                }
            }

            key = "-".join(sorted(agents_involved))

            future = self.producer.send(
                self.topic,
                value=event,
                key=key
            )

            logger.debug(f"📤 Published coordination event: {event_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish coordination event: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """
        Get health status of Kafka publisher.

        Returns:
            Health check result
        """
        return {
            "connected": self.connected,
            "bootstrap_servers": self.bootstrap_servers,
            "topic": self.topic,
            "status": "healthy" if self.connected else "unhealthy"
        }


# Global singleton instance
_kafka_publisher: Optional[AgentCommunicationKafkaPublisher] = None


def get_kafka_publisher() -> AgentCommunicationKafkaPublisher:
    """
    Get or create global Kafka publisher instance.

    Returns:
        Kafka publisher singleton
    """
    global _kafka_publisher

    if _kafka_publisher is None:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        topic = os.getenv("KAFKA_AGENT_COMMUNICATIONS_TOPIC", "agent-communications")

        _kafka_publisher = AgentCommunicationKafkaPublisher(
            bootstrap_servers=bootstrap_servers,
            topic=topic
        )

        # Auto-connect
        _kafka_publisher.connect()

    return _kafka_publisher


def shutdown_kafka_publisher():
    """Shutdown global Kafka publisher."""
    global _kafka_publisher

    if _kafka_publisher:
        _kafka_publisher.disconnect()
        _kafka_publisher = None
