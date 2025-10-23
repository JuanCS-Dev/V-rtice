"""
Honeypot Status Consumer for Active Immune Core

Consumes honeypot interaction status from Reactive Fabric to enhance
threat intelligence and pattern learning.

Air Gap Fix: AG-KAFKA-004
Priority: MEDIUM (Intel Enhancement)
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from communication.cytokines import CytokineMessenger, CytokineType

logger = logging.getLogger(__name__)


class HoneypotStatusConsumer:
    """
    Consumes honeypot status updates from Reactive Fabric.

    Processes honeypot interactions to:
    1. Extract Indicators of Compromise (IOCs)
    2. Update threat pattern database
    3. Trigger cytokine broadcasts for learned patterns
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "reactive_fabric.honeypot_status",
        group_id: str = "active-immune-core-honeypot"
    ):
        """
        Initialize honeypot consumer.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic for honeypot status
            group_id: Consumer group ID
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False

        # Threat pattern storage (in-memory for now)
        self.learned_patterns: Dict[str, Dict[str, Any]] = {}
        self.interaction_count = 0

        # Cytokine messenger for threat broadcasts
        self.cytokine_messenger = CytokineMessenger(
            bootstrap_servers=bootstrap_servers,
            topic_prefix="immunis.cytokines",
            consumer_group_prefix="honeypot_intel"
        )

    async def start(self):
        """Start consuming honeypot status updates."""
        try:
            logger.info(f"Starting Honeypot Status Consumer: {self.topic}")

            # Initialize cytokine messenger
            await self.cytokine_messenger.start()
            logger.info("✅ Cytokine messenger initialized")

            # Initialize Kafka consumer
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True
            )

            logger.info(f"✅ Honeypot consumer connected: {self.topic}")
            self.running = True

            # Start consumption loop
            await self._consume_loop()

        except KafkaError as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Honeypot consumer failed to start: {e}")
            raise

    async def _consume_loop(self):
        """Main consumption loop."""
        while self.running:
            try:
                # Poll for messages (non-blocking with timeout)
                messages = self.consumer.poll(timeout_ms=1000)

                for topic_partition, records in messages.items():
                    for message in records:
                        await self._process_honeypot_status(message.value)

                # Allow other tasks to run
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in honeypot consume loop: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _process_honeypot_status(self, status: Dict[str, Any]):
        """
        Process honeypot status update.

        Args:
            status: Honeypot status event from Reactive Fabric
        """
        try:
            honeypot_id = status.get("honeypot_id", "unknown")
            event_type = status.get("status", "unknown")
            timestamp = status.get("timestamp", datetime.utcnow().isoformat())

            logger.info(
                f"🍯 Honeypot Status: {honeypot_id} | "
                f"Event: {event_type} | "
                f"Time: {timestamp}"
            )

            self.interaction_count += 1

            # Process interaction events
            if event_type == "interaction_detected":
                await self._handle_interaction(status)
            elif event_type == "attack_detected":
                await self._handle_attack(status)
            elif event_type == "probe_detected":
                await self._handle_probe(status)
            else:
                logger.debug(f"Honeypot status: {event_type}")

        except Exception as e:
            logger.error(f"Error processing honeypot status: {e}")

    async def _handle_interaction(self, status: Dict[str, Any]):
        """Handle honeypot interaction event."""
        try:
            # Extract IOCs
            iocs = self._extract_iocs(status)

            logger.info(f"🔍 IOCs extracted from honeypot interaction: {iocs}")

            # Add to threat pattern database
            pattern_id = f"honeypot-{status.get('honeypot_id')}-{self.interaction_count}"
            self.learned_patterns[pattern_id] = {
                "type": "honeypot_interaction",
                "iocs": iocs,
                "timestamp": status.get("timestamp"),
                "severity": "medium",
                "source": "reactive_fabric_honeypot"
            }

            # Trigger cytokine: threat pattern learned
            await self._broadcast_threat_pattern_learned(pattern_id, iocs)

        except Exception as e:
            logger.error(f"Error handling honeypot interaction: {e}")

    async def _handle_attack(self, status: Dict[str, Any]):
        """Handle honeypot attack event (high severity)."""
        try:
            iocs = self._extract_iocs(status)

            logger.warning(f"⚠️  Attack detected on honeypot: {iocs}")

            # Add as high-severity pattern
            pattern_id = f"honeypot-attack-{self.interaction_count}"
            self.learned_patterns[pattern_id] = {
                "type": "honeypot_attack",
                "iocs": iocs,
                "timestamp": status.get("timestamp"),
                "severity": "high",
                "attack_type": status.get("attack_type", "unknown"),
                "source": "reactive_fabric_honeypot"
            }

            # Broadcast high-priority threat
            await self._broadcast_threat_pattern_learned(pattern_id, iocs, severity="high")

        except Exception as e:
            logger.error(f"Error handling honeypot attack: {e}")

    async def _handle_probe(self, status: Dict[str, Any]):
        """Handle honeypot probe event (reconnaissance)."""
        try:
            iocs = self._extract_iocs(status)

            logger.info(f"🔎 Probe detected on honeypot: {iocs}")

            # Add as reconnaissance pattern
            pattern_id = f"honeypot-probe-{self.interaction_count}"
            self.learned_patterns[pattern_id] = {
                "type": "honeypot_probe",
                "iocs": iocs,
                "timestamp": status.get("timestamp"),
                "severity": "low",
                "source": "reactive_fabric_honeypot"
            }

            # Broadcast reconnaissance pattern
            await self._broadcast_threat_pattern_learned(pattern_id, iocs, severity="low")

        except Exception as e:
            logger.error(f"Error handling honeypot probe: {e}")

    def _extract_iocs(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract Indicators of Compromise from honeypot status.

        Returns:
            Dictionary of IOCs (IP, port, protocol, payload, etc.)
        """
        return {
            "source_ip": status.get("source_ip", "unknown"),
            "source_port": status.get("source_port"),
            "target_ip": status.get("target_ip"),
            "target_port": status.get("target_port"),
            "protocol": status.get("protocol", "unknown"),
            "payload": status.get("payload", ""),
            "user_agent": status.get("user_agent"),
            "request_method": status.get("request_method"),
            "request_path": status.get("request_path"),
            "timestamp": status.get("timestamp")
        }

    async def _broadcast_threat_pattern_learned(
        self,
        pattern_id: str,
        iocs: Dict[str, Any],
        severity: str = "medium"
    ):
        """
        Broadcast cytokine: threat pattern learned.

        Sends IL1 (pro-inflammatory) cytokine to alert immune system
        about newly learned threat patterns from honeypot interactions.

        Args:
            pattern_id: Unique pattern identifier
            iocs: Indicators of Compromise
            severity: Threat severity level
        """
        try:
            logger.info(
                f"📡 Broadcasting threat pattern learned: {pattern_id} | "
                f"Severity: {severity} | "
                f"IOCs: {iocs.get('source_ip', 'N/A')}"
            )

            # Map severity to cytokine type and priority
            cytokine_map = {
                "low": (CytokineType.IL8, 4),      # IL8: Reconnaissance alert
                "medium": (CytokineType.IL1, 6),   # IL1: Standard threat
                "high": (CytokineType.TNF, 9)      # TNF: Critical threat (apoptosis trigger)
            }

            cytokine_type, priority = cytokine_map.get(severity, (CytokineType.IL1, 5))

            # Send cytokine broadcast
            success = await self.cytokine_messenger.send_cytokine(
                tipo=cytokine_type,
                payload={
                    "event": "threat_pattern_learned",
                    "pattern_id": pattern_id,
                    "iocs": iocs,
                    "severity": severity,
                    "source": "honeypot_consumer",
                    "threat_type": "honeypot_interaction",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                emissor_id="honeypot_consumer",
                prioridade=priority,
                area_alvo=None,  # Broadcast to all immune agents
                ttl_segundos=600  # 10 minutes TTL
            )

            if success:
                logger.info(f"✅ Cytokine {cytokine_type} broadcasted for pattern {pattern_id}")
            else:
                logger.warning(f"⚠️  Cytokine broadcast failed (degraded mode) for {pattern_id}")

        except Exception as e:
            logger.error(f"Failed to broadcast threat pattern: {e}")

    async def stop(self):
        """Stop honeypot consumer and cytokine messenger."""
        logger.info("Stopping Honeypot Status Consumer")
        self.running = False

        if self.consumer:
            self.consumer.close()

        # Stop cytokine messenger
        await self.cytokine_messenger.stop()

        logger.info("✅ Honeypot consumer stopped")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get honeypot consumer statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_interactions": self.interaction_count,
            "learned_patterns_count": len(self.learned_patterns),
            "running": self.running,
            "topic": self.topic,
            "group_id": self.group_id
        }


# Global singleton instance
_honeypot_consumer: Optional[HoneypotStatusConsumer] = None


def get_honeypot_consumer() -> HoneypotStatusConsumer:
    """
    Get or create global honeypot consumer instance.

    Returns:
        Honeypot consumer singleton
    """
    global _honeypot_consumer

    if _honeypot_consumer is None:
        import os
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        topic = os.getenv("HONEYPOT_STATUS_TOPIC", "reactive_fabric.honeypot_status")

        _honeypot_consumer = HoneypotStatusConsumer(
            bootstrap_servers=bootstrap_servers,
            topic=topic
        )

    return _honeypot_consumer


async def start_honeypot_consumer():
    """Start global honeypot consumer (async)."""
    consumer = get_honeypot_consumer()
    await consumer.start()


async def stop_honeypot_consumer():
    """Stop global honeypot consumer (async)."""
    global _honeypot_consumer

    if _honeypot_consumer:
        await _honeypot_consumer.stop()
        _honeypot_consumer = None
