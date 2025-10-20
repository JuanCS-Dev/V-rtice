"""
Kafka producer for Reactive Fabric Core Service
Publishes threat detections and status updates

Sprint 1: Real implementation
"""

import structlog
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from models import (
    ThreatDetectedMessage,
    HoneypotStatusMessage
)

logger = structlog.get_logger()


class KafkaProducer:
    """Kafka producer for publishing events."""
    
    # Topic names
    TOPIC_THREAT_DETECTED = "reactive_fabric.threat_detected"
    TOPIC_HONEYPOT_STATUS = "reactive_fabric.honeypot_status"
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                compression_type='gzip',
                max_batch_size=16384,
                linger_ms=10
            )
            await self.producer.start()
            self._connected = True
            logger.info("kafka_producer_started", bootstrap_servers=self.bootstrap_servers)
        except Exception as e:
            logger.error("kafka_producer_start_failed", error=str(e))
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self._connected = False
            logger.info("kafka_producer_stopped")
    
    async def health_check(self) -> bool:
        """Check Kafka connectivity."""
        return self._connected and self.producer is not None
    
    async def publish_threat_detected(self, message: ThreatDetectedMessage) -> bool:
        """
        Publish threat detection to Kafka.
        
        This message will be consumed by:
        - NK Cells (immune response)
        - Sentinel Agent (threat intel enrichment)
        - ESGT (stress level increase)
        
        Args:
            message: ThreatDetectedMessage with attack details
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.warning("kafka_producer_not_initialized")
            return False
        
        try:
            # Convert Pydantic model to dict
            payload = message.model_dump()
            
            # Add metadata
            payload['_source'] = 'reactive_fabric_core'
            payload['_published_at'] = datetime.utcnow().isoformat()
            
            # Publish to Kafka
            await self.producer.send_and_wait(
                self.TOPIC_THREAT_DETECTED,
                value=payload,
                key=message.event_id.encode('utf-8')
            )
            
            logger.info(
                "threat_detected_published",
                event_id=message.event_id,
                honeypot_id=message.honeypot_id,
                attack_type=message.attack_type,
                severity=message.severity.value,
                topic=self.TOPIC_THREAT_DETECTED
            )
            
            return True
            
        except KafkaError as e:
            logger.error(
                "kafka_publish_failed",
                error=str(e),
                topic=self.TOPIC_THREAT_DETECTED,
                event_id=message.event_id
            )
            return False
        except Exception as e:
            logger.error(
                "unexpected_publish_error",
                error=str(e),
                topic=self.TOPIC_THREAT_DETECTED
            )
            return False
    
    async def publish_honeypot_status(self, message: HoneypotStatusMessage) -> bool:
        """
        Publish honeypot status update to Kafka.
        
        Args:
            message: HoneypotStatusMessage with status details
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.warning("kafka_producer_not_initialized")
            return False
        
        try:
            # Convert Pydantic model to dict
            payload = message.model_dump()
            
            # Add metadata
            payload['_source'] = 'reactive_fabric_core'
            payload['_published_at'] = datetime.utcnow().isoformat()
            
            # Publish to Kafka
            await self.producer.send_and_wait(
                self.TOPIC_HONEYPOT_STATUS,
                value=payload,
                key=message.honeypot_id.encode('utf-8')
            )
            
            logger.debug(
                "honeypot_status_published",
                honeypot_id=message.honeypot_id,
                status=message.status.value,
                topic=self.TOPIC_HONEYPOT_STATUS
            )
            
            return True
            
        except KafkaError as e:
            logger.error(
                "kafka_publish_failed",
                error=str(e),
                topic=self.TOPIC_HONEYPOT_STATUS,
                honeypot_id=message.honeypot_id
            )
            return False
        except Exception as e:
            logger.error(
                "unexpected_publish_error",
                error=str(e),
                topic=self.TOPIC_HONEYPOT_STATUS
            )
            return False
    
    async def publish_raw(self, topic: str, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """
        Publish raw message to any topic.
        
        Args:
            topic: Kafka topic name
            message: Message payload (dict)
            key: Optional message key
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.warning("kafka_producer_not_initialized")
            return False
        
        try:
            key_bytes = key.encode('utf-8') if key else None
            
            await self.producer.send_and_wait(
                topic,
                value=message,
                key=key_bytes
            )
            
            logger.debug("raw_message_published", topic=topic, key=key)
            return True
            
        except Exception as e:
            logger.error("raw_publish_failed", error=str(e), topic=topic)
            return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_threat_detected_message(
    event_id: str,
    honeypot_id: str,
    attacker_ip: str,
    attack_type: str,
    severity: str,
    ttps: Optional[List[str]] = None,
    iocs: Optional[Dict[str, Any]] = None,
    confidence: float = 1.0,
    metadata: Optional[Dict[str, Any]] = None
) -> ThreatDetectedMessage:
    """
    Helper function to create ThreatDetectedMessage.
    
    Args:
        event_id: Unique event identifier
        honeypot_id: Honeypot identifier
        attacker_ip: Attacker IP address
        attack_type: Type of attack
        severity: Severity level (low, medium, high, critical)
        ttps: List of MITRE ATT&CK technique IDs
        iocs: Dict of IoCs {ips: [], domains: [], hashes: [], usernames: []}
        confidence: Confidence score (0.0-1.0)
        metadata: Additional metadata
    
    Returns:
        ThreatDetectedMessage instance
    """
    from models import AttackSeverity
    
    return ThreatDetectedMessage(
        event_id=event_id,
        timestamp=datetime.utcnow(),
        honeypot_id=honeypot_id,
        attacker_ip=attacker_ip,
        attack_type=attack_type,
        severity=AttackSeverity(severity),
        ttps=ttps or [],
        iocs=iocs or {},
        confidence=confidence,
        metadata=metadata or {}
    )


def create_honeypot_status_message(
    honeypot_id: str,
    status: str,
    uptime_seconds: Optional[int] = None,
    error_message: Optional[str] = None
) -> HoneypotStatusMessage:
    """
    Helper function to create HoneypotStatusMessage.
    
    Args:
        honeypot_id: Honeypot identifier
        status: Status (online, offline, degraded)
        uptime_seconds: Optional uptime in seconds
        error_message: Optional error message
    
    Returns:
        HoneypotStatusMessage instance
    """
    from .models import HoneypotStatus
    
    return HoneypotStatusMessage(
        honeypot_id=honeypot_id,
        status=HoneypotStatus(status),
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime_seconds,
        error_message=error_message
    )
