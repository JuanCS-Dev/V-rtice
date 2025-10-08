"""Kafka Event Producer - Event-Driven Integration - PRODUCTION-READY

Kafka producer for publishing Active Immune Core events to external systems.

Event Topics:
- immunis.threats.detected - Threat detection events
- immunis.cloning.expanded - Clonal expansion events
- immunis.homeostasis.alerts - Homeostatic state changes
- immunis.system.health - System health metrics

External consumers: SIEM, ADR Core, Monitoring, Analytics

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError

logger = logging.getLogger(__name__)


class EventTopic(str, Enum):
    """Kafka event topics for Active Immune Core"""

    THREATS_DETECTED = "immunis.threats.detected"
    CLONING_EXPANDED = "immunis.cloning.expanded"
    HOMEOSTASIS_ALERTS = "immunis.homeostasis.alerts"
    SYSTEM_HEALTH = "immunis.system.health"


class KafkaEventProducer:
    """
    Kafka Event Producer for Active Immune Core.

    Publishes system events to Kafka for consumption by external services.

    Features:
    - Async event publishing
    - Automatic retries with exponential backoff
    - Graceful degradation (logs to file when Kafka unavailable)
    - Event batching and compression
    - Event ordering guarantees (by key)

    Usage:
        producer = KafkaEventProducer()
        await producer.start()

        await producer.publish_threat_detection(
            threat_id="threat_001",
            threat_type="malware",
            severity="high",
            ...
        )

        await producer.stop()
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        enable_degraded_mode: bool = True,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
    ):
        """
        Initialize Kafka Event Producer.

        Args:
            bootstrap_servers: Kafka broker addresses
            enable_degraded_mode: Enable graceful degradation
            max_retries: Maximum retry attempts
            retry_backoff_base: Backoff multiplier for retries
        """
        self.bootstrap_servers = bootstrap_servers
        self.enable_degraded_mode = enable_degraded_mode
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base

        self._producer: Optional[AIOKafkaProducer] = None
        self._running = False
        self._kafka_available = False

        # Metrics
        self.total_events_published = 0
        self.total_events_failed = 0
        self.events_by_topic: Dict[str, int] = {topic.value: 0 for topic in EventTopic}

        logger.info(f"KafkaEventProducer initialized (bootstrap={bootstrap_servers})")

    # ==================== LIFECYCLE ====================

    async def start(self) -> None:
        """
        Start Kafka producer.

        Attempts to connect to Kafka. If unavailable and degraded mode
        is enabled, continues without Kafka (logs to file).
        """
        if self._running:
            logger.warning("KafkaEventProducer already running")
            return

        logger.info("Starting KafkaEventProducer...")

        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode(),
                acks="all",  # Wait for all replicas
                compression_type="gzip",
                max_batch_size=16384,
                linger_ms=10,  # Batch events for 10ms
            )

            await self._producer.start()
            self._kafka_available = True
            self._running = True

            logger.info("✓ KafkaEventProducer started (Kafka connected)")

        except (KafkaConnectionError, KafkaError) as e:
            if self.enable_degraded_mode:
                self._running = True
                self._kafka_available = False
                logger.warning(f"Kafka unavailable - running in degraded mode: {e}")
            else:
                raise

    async def stop(self) -> None:
        """Stop Kafka producer."""
        if not self._running:
            logger.warning("KafkaEventProducer not running")
            return

        logger.info("Stopping KafkaEventProducer...")

        if self._producer:
            await self._producer.stop()

        self._running = False
        self._kafka_available = False

        logger.info("✓ KafkaEventProducer stopped")

    def is_available(self) -> bool:
        """Check if Kafka is available."""
        return self._running and self._kafka_available

    # ==================== EVENT PUBLISHING ====================

    async def publish_event(
        self,
        topic: EventTopic,
        event_data: Dict[str, Any],
        key: Optional[str] = None,
    ) -> bool:
        """
        Publish event to Kafka topic.

        Args:
            topic: Event topic
            event_data: Event payload
            key: Optional partition key (for ordering)

        Returns:
            True if published successfully, False otherwise
        """
        if not self._running:
            logger.error("KafkaEventProducer not running")
            return False

        # Add metadata
        enriched_event = {
            **event_data,
            "source_service": "active_immune_core",
            "published_at": datetime.utcnow().isoformat(),
        }

        # Try publishing to Kafka
        if self._kafka_available:
            for attempt in range(self.max_retries + 1):
                try:
                    # Encode key if provided
                    key_bytes = key.encode() if key else None

                    # Send to Kafka
                    await self._producer.send_and_wait(
                        topic.value,
                        value=enriched_event,
                        key=key_bytes,
                    )

                    # Update metrics
                    self.total_events_published += 1
                    self.events_by_topic[topic.value] += 1

                    logger.debug(f"Published event to {topic.value} (key={key})")
                    return True

                except Exception as e:
                    if attempt < self.max_retries:
                        backoff = self.retry_backoff_base**attempt
                        logger.warning(
                            f"Failed to publish to {topic.value} (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                        )
                        await asyncio.sleep(backoff)
                    else:
                        logger.error(f"Failed to publish to {topic.value} after {self.max_retries + 1} attempts: {e}")
                        self._kafka_available = False

        # Graceful degradation - log to file
        if self.enable_degraded_mode:
            self._log_event_to_file(topic, enriched_event)
            self.total_events_failed += 1
            return False
        else:
            raise RuntimeError(f"Failed to publish event to {topic.value}")

    def _log_event_to_file(
        self,
        topic: EventTopic,
        event_data: Dict[str, Any],
    ) -> None:
        """
        Fallback: log event to file when Kafka unavailable.

        Args:
            topic: Event topic
            event_data: Event payload
        """
        try:
            with open("/tmp/immunis_events_fallback.jsonl", "a") as f:
                f.write(
                    json.dumps(
                        {
                            "topic": topic.value,
                            "event": event_data,
                            "logged_at": datetime.utcnow().isoformat(),
                        }
                    )
                    + "\n"
                )
            logger.warning(f"Event logged to fallback file: {topic.value} (Kafka unavailable)")
        except Exception as e:
            logger.error(f"Failed to log event to fallback file: {e}")

    # ==================== DOMAIN-SPECIFIC PUBLISHERS ====================

    async def publish_threat_detection(
        self,
        threat_id: str,
        threat_type: str,
        severity: str,
        detector_agent: str,
        target: str,
        confidence: float,
        details: Dict[str, Any],
    ) -> bool:
        """
        Publish threat detection event.

        Args:
            threat_id: Threat identifier
            threat_type: Threat type (malware, intrusion, etc.)
            severity: Severity (low/medium/high/critical)
            detector_agent: Agent that detected threat
            target: Threat target (IP, file, etc.)
            confidence: Detection confidence (0.0-1.0)
            details: Additional threat details

        Returns:
            True if published successfully
        """
        event_data = {
            "event_type": "threat_detection",
            "threat_id": threat_id,
            "threat_type": threat_type,
            "severity": severity,
            "detector_agent": detector_agent,
            "target": target,
            "confidence": confidence,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Use threat_id as key for ordering
        return await self.publish_event(
            EventTopic.THREATS_DETECTED,
            event_data,
            key=threat_id,
        )

    async def publish_clonal_expansion(
        self,
        parent_id: str,
        clone_ids: List[str],
        num_clones: int,
        especializacao: str,
        lymphnode_id: str,
        trigger: str,
    ) -> bool:
        """
        Publish clonal expansion event.

        Args:
            parent_id: Parent agent ID
            clone_ids: List of created clone IDs
            num_clones: Number of clones created
            especializacao: Specialization (threat signature)
            lymphnode_id: Lymphnode that created clones
            trigger: What triggered cloning

        Returns:
            True if published successfully
        """
        event_data = {
            "event_type": "clonal_expansion",
            "parent_id": parent_id,
            "clone_ids": clone_ids,
            "num_clones": num_clones,
            "especializacao": especializacao,
            "lymphnode_id": lymphnode_id,
            "trigger": trigger,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Use parent_id as key
        return await self.publish_event(
            EventTopic.CLONING_EXPANDED,
            event_data,
            key=parent_id,
        )

    async def publish_homeostatic_alert(
        self,
        lymphnode_id: str,
        old_state: Optional[str],
        new_state: str,
        temperatura_regional: float,
        recommended_action: str,
        metrics: Dict[str, Any],
    ) -> bool:
        """
        Publish homeostatic state change event.

        Args:
            lymphnode_id: Lymphnode identifier
            old_state: Previous state
            new_state: New homeostatic state
            temperatura_regional: Regional temperature
            recommended_action: Recommended action
            metrics: Additional metrics

        Returns:
            True if published successfully
        """
        event_data = {
            "event_type": "homeostatic_alert",
            "lymphnode_id": lymphnode_id,
            "old_state": old_state,
            "new_state": new_state,
            "temperatura_regional": temperatura_regional,
            "recommended_action": recommended_action,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Use lymphnode_id as key
        return await self.publish_event(
            EventTopic.HOMEOSTASIS_ALERTS,
            event_data,
            key=lymphnode_id,
        )

    async def publish_system_health(
        self,
        health_status: str,
        total_agents: int,
        active_agents: int,
        threats_detected: int,
        threats_neutralized: int,
        average_temperature: float,
        lymphnodes: List[Dict[str, Any]],
    ) -> bool:
        """
        Publish system health event.

        Args:
            health_status: Health status (healthy/degraded/critical)
            total_agents: Total agents
            active_agents: Active agents
            threats_detected: Total threats detected
            threats_neutralized: Total threats neutralized
            average_temperature: Average system temperature
            lymphnodes: Lymphnode metrics

        Returns:
            True if published successfully
        """
        event_data = {
            "event_type": "system_health",
            "health_status": health_status,
            "total_agents": total_agents,
            "active_agents": active_agents,
            "threats_detected": threats_detected,
            "threats_neutralized": threats_neutralized,
            "average_temperature": average_temperature,
            "lymphnodes": lymphnodes,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # No key - use round-robin partitioning
        return await self.publish_event(
            EventTopic.SYSTEM_HEALTH,
            event_data,
        )

    # ==================== METRICS ====================

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get producer metrics.

        Returns:
            Dict with metrics
        """
        return {
            "running": self._running,
            "kafka_available": self._kafka_available,
            "total_events_published": self.total_events_published,
            "total_events_failed": self.total_events_failed,
            "events_by_topic": self.events_by_topic.copy(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"KafkaEventProducer(running={self._running}, "
            f"kafka_available={self._kafka_available}, "
            f"published={self.total_events_published})"
        )
