"""Kafka Producer for Defense Outputs.

Publishes defense detections, enriched threats, and response actions
to Kafka topics for downstream consumption.

Biological Inspiration:
- Efferent neurons: Output pathway from defense system
- Signaling cascade: Events trigger downstream responses
- Broadcast communication: One event notifies multiple subscribers

IIT Integration:
- Information broadcast: Detection results shared across system
- Φ propagation: Integrated insights disseminated
- Temporal ordering: Events published in causal sequence

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from prometheus_client import Counter, Histogram

try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None

from detection.sentinel_agent import DetectionResult
from intelligence.fusion_engine import EnrichedThreat
from response.automated_response import PlaybookResult

logger = logging.getLogger(__name__)


# Metrics
KAFKA_MESSAGES_PRODUCED = Counter(
    "kafka_defense_messages_produced_total",
    "Total messages produced to Kafka",
    ["topic"]
)

KAFKA_PRODUCE_LATENCY = Histogram(
    "kafka_defense_produce_latency_seconds",
    "Message production latency"
)

KAFKA_PRODUCE_ERRORS = Counter(
    "kafka_defense_produce_errors_total",
    "Total Kafka producer errors",
    ["error_type"]
)


class KafkaProducerError(Exception):
    """Raised when Kafka producer encounters error."""
    pass


class DefenseEventProducer:
    """Publishes defense outputs to Kafka topics.
    
    Provides high-throughput async publishing of defense events
    to multiple Kafka topics.
    
    Features:
    - Async message production
    - Automatic serialization
    - Error handling and retries
    - Prometheus metrics
    
    Topics:
    - defense.detections: Sentinel detection results
    - threat.enriched: Enriched threat intelligence
    - defense.responses: Response execution results
    
    Attributes:
        kafka_brokers: Kafka broker addresses
        producer: AIOKafkaProducer instance
    """
    
    def __init__(self, kafka_brokers: str = "localhost:9092"):
        """Initialize Kafka producer.
        
        Args:
            kafka_brokers: Comma-separated broker addresses
            
        Raises:
            KafkaProducerError: If aiokafka not available
        """
        if AIOKafkaProducer is None:
            raise KafkaProducerError(
                "aiokafka package not installed. "
                "Install with: pip install aiokafka"
            )
        
        self.kafka_brokers = kafka_brokers
        self.producer: Optional[AIOKafkaProducer] = None
        
        logger.info(f"DefenseEventProducer initialized: brokers={kafka_brokers}")
    
    async def start(self):
        """Start Kafka producer.
        
        Raises:
            KafkaProducerError: If producer fails to start
        """
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_brokers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='gzip',
                acks='all',  # Wait for all replicas
                retries=3
            )
            
            await self.producer.start()
            logger.info("Kafka producer started")
        
        except Exception as e:
            KAFKA_PRODUCE_ERRORS.labels(error_type="start_failed").inc()
            logger.error(f"Failed to start Kafka producer: {e}", exc_info=True)
            raise KafkaProducerError(f"Producer start failed: {e}")
    
    async def stop(self):
        """Stop Kafka producer gracefully."""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping producer: {e}", exc_info=True)
    
    async def publish_detection(
        self,
        detection: DetectionResult,
        topic: str = "defense.detections"
    ):
        """Publish detection result to Kafka.
        
        Args:
            detection: Detection result from Sentinel
            topic: Kafka topic to publish to
            
        Raises:
            KafkaProducerError: If publish fails
        """
        if not self.producer:
            raise KafkaProducerError("Producer not started")
        
        try:
            message = {
                "detection_id": detection.detection_id,
                "event_id": detection.event.event_id,
                "is_threat": detection.is_threat,
                "confidence": detection.confidence,
                "severity": detection.severity.value if detection.severity else None,
                "mitre_techniques": [
                    {
                        "technique_id": t.technique_id,
                        "name": t.name,
                        "tactic": t.tactic
                    }
                    for t in detection.mitre_techniques
                ],
                "narrative": detection.narrative,
                "timestamp": detection.timestamp.isoformat()
            }
            
            with KAFKA_PRODUCE_LATENCY.time():
                await self.producer.send_and_wait(topic, value=message)
            
            KAFKA_MESSAGES_PRODUCED.labels(topic=topic).inc()
            logger.debug(f"Published detection: {detection.detection_id} to {topic}")
        
        except Exception as e:
            KAFKA_PRODUCE_ERRORS.labels(error_type="detection").inc()
            logger.error(f"Failed to publish detection: {e}", exc_info=True)
            raise KafkaProducerError(f"Detection publish failed: {e}")
    
    async def publish_enriched_threat(
        self,
        threat: EnrichedThreat,
        topic: str = "threat.enriched"
    ):
        """Publish enriched threat intelligence to Kafka.
        
        Args:
            threat: Enriched threat from Fusion Engine
            topic: Kafka topic to publish to
            
        Raises:
            KafkaProducerError: If publish fails
        """
        if not self.producer:
            raise KafkaProducerError("Producer not started")
        
        try:
            message = {
                "threat_id": threat.threat_id,
                "primary_ioc": {
                    "value": threat.primary_ioc.value,
                    "type": threat.primary_ioc.ioc_type.value
                },
                "severity": threat.severity,
                "confidence": threat.confidence,
                "threat_actor": (
                    threat.threat_actor.actor_id if threat.threat_actor else None
                ),
                "ttps": threat.ttps,
                "campaigns": threat.campaigns,
                "attack_chain_stage": threat.attack_chain_stage,
                "narrative": threat.narrative,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            with KAFKA_PRODUCE_LATENCY.time():
                await self.producer.send_and_wait(topic, value=message)
            
            KAFKA_MESSAGES_PRODUCED.labels(topic=topic).inc()
            logger.debug(f"Published enriched threat: {threat.threat_id} to {topic}")
        
        except Exception as e:
            KAFKA_PRODUCE_ERRORS.labels(error_type="enrichment").inc()
            logger.error(f"Failed to publish enriched threat: {e}", exc_info=True)
            raise KafkaProducerError(f"Enriched threat publish failed: {e}")
    
    async def publish_response(
        self,
        playbook_result: PlaybookResult,
        topic: str = "defense.responses"
    ):
        """Publish response execution result to Kafka.
        
        Args:
            playbook_result: Result of playbook execution
            topic: Kafka topic to publish to
            
        Raises:
            KafkaProducerError: If publish fails
        """
        if not self.producer:
            raise KafkaProducerError("Producer not started")
        
        try:
            message = {
                "playbook_id": playbook_result.playbook.playbook_id,
                "playbook_name": playbook_result.playbook.name,
                "threat_id": playbook_result.context.threat_id,
                "event_id": playbook_result.context.event_id,
                "success": playbook_result.success,
                "actions_executed": len(playbook_result.executed_actions),
                "actions_failed": len(playbook_result.failed_actions),
                "execution_time_seconds": playbook_result.execution_time.total_seconds(),
                "timestamp": playbook_result.completed_at.isoformat()
            }
            
            with KAFKA_PRODUCE_LATENCY.time():
                await self.producer.send_and_wait(topic, value=message)
            
            KAFKA_MESSAGES_PRODUCED.labels(topic=topic).inc()
            logger.debug(
                f"Published response: {playbook_result.playbook.playbook_id} to {topic}"
            )
        
        except Exception as e:
            KAFKA_PRODUCE_ERRORS.labels(error_type="response").inc()
            logger.error(f"Failed to publish response: {e}", exc_info=True)
            raise KafkaProducerError(f"Response publish failed: {e}")
    
    async def publish_raw(self, topic: str, message: Dict[str, Any]):
        """Publish raw message to Kafka.
        
        Generic method for publishing any message.
        
        Args:
            topic: Kafka topic
            message: Message dict to publish
            
        Raises:
            KafkaProducerError: If publish fails
        """
        if not self.producer:
            raise KafkaProducerError("Producer not started")
        
        try:
            with KAFKA_PRODUCE_LATENCY.time():
                await self.producer.send_and_wait(topic, value=message)
            
            KAFKA_MESSAGES_PRODUCED.labels(topic=topic).inc()
            logger.debug(f"Published raw message to {topic}")
        
        except Exception as e:
            KAFKA_PRODUCE_ERRORS.labels(error_type="raw").inc()
            logger.error(f"Failed to publish raw message: {e}", exc_info=True)
            raise KafkaProducerError(f"Raw message publish failed: {e}")
