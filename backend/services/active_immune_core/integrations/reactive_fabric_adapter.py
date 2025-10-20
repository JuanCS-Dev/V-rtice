"""
Reactive Fabric Adapter - Active Immune Core → Reactive Fabric Integration

Bidirectional integration layer:
1. Receives threat detections from Reactive Fabric
2. Sends immune responses back
3. Routes threats to appropriate immune agents

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Callable, Dict, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backend.shared.messaging import (  # noqa: E402
    EventRouter,
    EventTopic,
    ImmuneResponseEvent,
    ThreatDetectionEvent,
    UnifiedKafkaClient,
)

logger = logging.getLogger(__name__)


ThreatHandler = Callable[[Dict[str, Any]], None]


class ReactiveFabricAdapter:
    """
    Adapter between Active Immune Core and Reactive Fabric.

    Responsibilities:
    1. Subscribe to threat detections from Reactive Fabric
    2. Route threats to appropriate immune agents
    3. Publish immune responses back to Reactive Fabric
    4. Track response metrics

    Usage:
        adapter = ReactiveFabricAdapter()

        # Register threat handler
        adapter.register_threat_handler(my_threat_processor)

        await adapter.start()
        # Adapter runs in background, routing threats to handlers

        # Send response
        await adapter.send_response(
            threat_id="...",
            responder_agent_id="...",
            action="neutralize",
            ...
        )

        await adapter.stop()
    """

    def __init__(
        self,
        kafka_bootstrap_servers: Optional[str] = None,
        enable_degraded_mode: bool = True,
    ):
        """
        Initialize Reactive Fabric Adapter.

        Args:
            kafka_bootstrap_servers: Kafka broker addresses
            enable_degraded_mode: Continue without Kafka if unavailable
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers or os.getenv(
            "KAFKA_BROKERS",
            "kafka:9092"
        )

        # Initialize unified Kafka client
        self.kafka_client = UnifiedKafkaClient(
            bootstrap_servers=self.kafka_bootstrap_servers,
            service_name="active_immune_core",
            enable_producer=True,
            enable_consumer=True,
            enable_degraded_mode=enable_degraded_mode,
        )

        # Initialize event router
        self.event_router = EventRouter()

        # Threat handlers
        self._threat_handlers: list[ThreatHandler] = []

        # State
        self._running = False

        # Metrics
        self.threats_received = 0
        self.threats_routed = 0
        self.responses_sent = 0
        self.routing_latency_ms: list[float] = []

        logger.info("ReactiveFabricAdapter initialized")

    # ==================== LIFECYCLE ====================

    async def start(self) -> None:
        """Start the adapter."""
        if self._running:
            logger.warning("ReactiveFabricAdapter already running")
            return

        logger.info("Starting ReactiveFabricAdapter...")

        # Start Kafka client
        await self.kafka_client.start()

        # Subscribe to threat detections
        await self.kafka_client.subscribe(
            EventTopic.THREATS_DETECTED,
            handler=self._handle_threat_detection,
        )

        self._running = True
        logger.info("✓ ReactiveFabricAdapter started")

    async def stop(self) -> None:
        """Stop the adapter."""
        if not self._running:
            logger.warning("ReactiveFabricAdapter not running")
            return

        logger.info("Stopping ReactiveFabricAdapter...")

        await self.kafka_client.stop()

        self._running = False
        logger.info("✓ ReactiveFabricAdapter stopped")

    # ==================== THREAT HANDLING ====================

    def register_threat_handler(self, handler: ThreatHandler) -> None:
        """
        Register threat handler.

        Handler will be called for each threat detection with:
        {
            "threat_id": "...",
            "attack_type": "...",
            "severity": "...",
            "recommended_responder": "nk_cell|neutrophil|dendritic_cell",
            ...
        }

        Args:
            handler: Threat handler function
        """
        self._threat_handlers.append(handler)
        logger.info(f"Registered threat handler: {handler.__name__}")

    async def _handle_threat_detection(self, event_data: Dict[str, Any]) -> None:
        """
        Handle threat detection event from Reactive Fabric.

        Routes threat to appropriate immune agents based on:
        - Attack type
        - Severity
        - Confidence
        - Historical patterns

        Args:
            event_data: Threat detection event data
        """
        try:
            start_time = datetime.utcnow()

            # Parse threat
            threat_id = event_data.get("event_id")
            attack_type = event_data.get("attack_type")
            severity = event_data.get("severity")
            attacker_ip = event_data.get("attacker_ip")

            logger.info(
                f"Received threat detection: id={threat_id}, "
                f"type={attack_type}, severity={severity}, "
                f"attacker={attacker_ip}"
            )

            self.threats_received += 1

            # Create threat event for routing
            threat_event = ThreatDetectionEvent(**event_data)

            # Determine recommended responder
            recommended_responder = self.event_router.determine_immune_response_type(
                threat_event
            )

            # Enrich with routing context
            enriched_data = {
                **event_data,
                "recommended_responder": recommended_responder,
                "routed_at": datetime.utcnow().isoformat(),
            }

            # Call threat handlers
            for handler in self._threat_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(enriched_data)
                    else:
                        handler(enriched_data)
                except Exception as e:
                    logger.error(f"Threat handler error: {e}")

            # Track latency
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.routing_latency_ms.append(latency_ms)

            # Keep only last 100 measurements
            if len(self.routing_latency_ms) > 100:
                self.routing_latency_ms = self.routing_latency_ms[-100:]

            self.threats_routed += 1

            logger.debug(f"Threat routed: {threat_id} → {recommended_responder} ({latency_ms:.2f}ms)")

        except Exception as e:
            logger.error(f"Error handling threat detection: {e}")

    # ==================== RESPONSE SENDING ====================

    async def send_response(
        self,
        threat_id: str,
        responder_agent_id: str,
        responder_agent_type: str,
        response_action: str,
        response_status: str,
        target: str,
        response_time_ms: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send immune response to Reactive Fabric.

        Args:
            threat_id: Original threat event ID
            responder_agent_id: Agent that responded
            responder_agent_type: Type of agent (nk_cell, neutrophil, etc)
            response_action: Action taken (isolate, neutralize, observe)
            response_status: Status (success, failed, partial)
            target: What was targeted
            response_time_ms: Response latency in ms
            details: Additional details

        Returns:
            True if successfully sent
        """
        if not self._running:
            logger.error("ReactiveFabricAdapter not running")
            return False

        try:
            response_event = ImmuneResponseEvent(
                threat_id=threat_id,
                responder_agent_id=responder_agent_id,
                responder_agent_type=responder_agent_type,
                response_action=response_action,
                response_status=response_status,
                response_time_ms=response_time_ms,
                target=target,
                details=details or {},
            )

            success = await self.kafka_client.publish(
                EventTopic.IMMUNE_RESPONSES,
                response_event,
                key=threat_id,  # Partition by threat for ordering
            )

            if success:
                self.responses_sent += 1
                logger.info(
                    f"Immune response sent: threat={threat_id}, "
                    f"action={response_action}, status={response_status}"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to send immune response: {e}")
            return False

    # ==================== STATUS & METRICS ====================

    def is_available(self) -> bool:
        """Check if adapter is available."""
        return self._running and self.kafka_client.is_available()

    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        avg_latency = (
            sum(self.routing_latency_ms) / len(self.routing_latency_ms)
            if self.routing_latency_ms
            else 0.0
        )

        return {
            "running": self._running,
            "kafka_available": self.kafka_client.is_available(),
            "threats_received": self.threats_received,
            "threats_routed": self.threats_routed,
            "responses_sent": self.responses_sent,
            "avg_routing_latency_ms": round(avg_latency, 2),
            "handlers_registered": len(self._threat_handlers),
            "kafka_metrics": self.kafka_client.get_metrics(),
            "router_metrics": self.event_router.get_metrics(),
        }

    def __repr__(self) -> str:
        return (
            f"ReactiveFabricAdapter(running={self._running}, "
            f"threats_received={self.threats_received}, "
            f"responses_sent={self.responses_sent})"
        )
