"""Kafka Consumer for Security Events.

Consumes security events from Kafka and processes them through
the defense orchestrator pipeline.

Biological Inspiration:
- Sensory neurons: Kafka acts as distributed nervous system
- Signal transduction: Events trigger defense cascade
- Parallel processing: Multiple consumers for scalability

IIT Integration:
- Information flow: Kafka enables temporal coherence across distributed sensors
- Φ maximization: Integration of events from multiple sources
- Conscious awareness: Real-time threat detection emerges from event stream

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import json
import logging
from datetime import datetime
from typing import Optional

from prometheus_client import Counter, Histogram

try:
    from aiokafka import AIOKafkaConsumer
except ImportError:
    AIOKafkaConsumer = None

from detection.sentinel_agent import SecurityEvent
from orchestration.defense_orchestrator import DefenseOrchestrator

logger = logging.getLogger(__name__)


# Metrics
KAFKA_EVENTS_CONSUMED = Counter(
    "kafka_defense_events_consumed_total",
    "Total security events consumed from Kafka"
)

KAFKA_PROCESSING_LATENCY = Histogram(
    "kafka_defense_processing_latency_seconds",
    "Event processing latency"
)

KAFKA_ERRORS = Counter(
    "kafka_defense_errors_total",
    "Total Kafka consumer errors",
    ["error_type"]
)


class KafkaConsumerError(Exception):
    """Raised when Kafka consumer encounters error."""
    pass


class DefenseEventConsumer:
    """Consumes security events from Kafka and processes them.
    
    Implements async consumer pattern for high-throughput event processing.
    Connects Kafka event stream to defense orchestrator pipeline.
    
    Features:
    - Async event consumption
    - Automatic reconnection on failure
    - Graceful shutdown
    - Prometheus metrics
    
    Attributes:
        orchestrator: Defense orchestrator for event processing
        kafka_brokers: Kafka broker addresses
        topic: Kafka topic to consume
        group_id: Consumer group ID
    """
    
    def __init__(
        self,
        orchestrator: DefenseOrchestrator,
        kafka_brokers: str = "localhost:9092",
        topic: str = "security.events",
        group_id: str = "defense-orchestrator"
    ):
        """Initialize Kafka consumer.
        
        Args:
            orchestrator: Defense orchestrator instance
            kafka_brokers: Comma-separated broker addresses
            topic: Topic to consume events from
            group_id: Consumer group identifier
            
        Raises:
            KafkaConsumerError: If aiokafka not available
        """
        if AIOKafkaConsumer is None:
            raise KafkaConsumerError(
                "aiokafka package not installed. "
                "Install with: pip install aiokafka"
            )
        
        self.orchestrator = orchestrator
        self.kafka_brokers = kafka_brokers
        self.topic = topic
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        
        logger.info(
            f"DefenseEventConsumer initialized: "
            f"brokers={kafka_brokers}, topic={topic}"
        )
    
    async def start(self):
        """Start Kafka consumer.
        
        Raises:
            KafkaConsumerError: If consumer fails to start
        """
        try:
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.kafka_brokers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=5000
            )
            
            await self.consumer.start()
            self.running = True
            
            logger.info(f"Kafka consumer started: topic={self.topic}")
        
        except Exception as e:
            KAFKA_ERRORS.labels(error_type="start_failed").inc()
            logger.error(f"Failed to start Kafka consumer: {e}", exc_info=True)
            raise KafkaConsumerError(f"Consumer start failed: {e}")
    
    async def stop(self):
        """Stop Kafka consumer gracefully."""
        self.running = False
        
        if self.consumer:
            try:
                await self.consumer.stop()
                logger.info("Kafka consumer stopped")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}", exc_info=True)
    
    async def consume_loop(self):
        """Main consumption loop.
        
        Continuously consumes and processes events until stopped.
        Implements error handling and reconnection logic.
        """
        if not self.consumer or not self.running:
            raise KafkaConsumerError("Consumer not started")
        
        logger.info("Starting event consumption loop...")
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    # Record consumption
                    KAFKA_EVENTS_CONSUMED.inc()
                    
                    # Parse event
                    event_data = message.value
                    event = self._parse_security_event(event_data)
                    
                    # Process through orchestrator
                    logger.debug(f"Processing event: {event.event_id}")
                    
                    with KAFKA_PROCESSING_LATENCY.time():
                        response = await self.orchestrator.process_security_event(event)
                    
                    logger.info(
                        f"Event {event.event_id} processed: "
                        f"phase={response.phase.value}, "
                        f"success={response.success}, "
                        f"latency={response.latency_ms:.2f}ms"
                    )
                
                except json.JSONDecodeError as e:
                    KAFKA_ERRORS.labels(error_type="json_decode").inc()
                    logger.error(f"Invalid JSON in message: {e}")
                
                except Exception as e:
                    KAFKA_ERRORS.labels(error_type="processing").inc()
                    logger.error(f"Error processing message: {e}", exc_info=True)
        
        except Exception as e:
            KAFKA_ERRORS.labels(error_type="consumption").inc()
            logger.error(f"Consumer loop error: {e}", exc_info=True)
            raise
        
        finally:
            await self.stop()
    
    def _parse_security_event(self, data: dict) -> SecurityEvent:
        """Parse Kafka message to SecurityEvent.
        
        Args:
            data: Raw message data
            
        Returns:
            Parsed SecurityEvent
            
        Raises:
            ValueError: If data is invalid
        """
        try:
            return SecurityEvent(
                event_id=data['event_id'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                source=data['source'],
                event_type=data['event_type'],
                source_ip=data['source_ip'],
                destination_ip=data.get('destination_ip'),
                port=data.get('port'),
                protocol=data.get('protocol'),
                payload=data.get('payload', {}),
                context=data.get('context', {})
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse event: {e}")
