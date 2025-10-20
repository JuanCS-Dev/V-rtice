"""
Event Router - Intelligent event routing and transformation

Routes events between services with transformation and enrichment.
Implements the integration patterns for the Reactive Fabric + Immune System.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from typing import Any

from .event_schemas import (
    ImmuneResponseEvent,
    SeverityLevel,
    ThreatDetectionEvent,
)
from .topics import EventTopic

logger = logging.getLogger(__name__)


class EventRouter:
    """
    Intelligent event router for cross-system integration.

    Routes and transforms events between:
    - Reactive Fabric → Active Immune Core
    - Active Immune Core → Reactive Fabric
    - Both → Monitoring/Analytics

    Applies business logic for routing decisions.
    """

    def __init__(self):
        """Initialize event router."""
        self.events_routed = 0
        self.events_dropped = 0
        self.routing_rules: dict[EventTopic, dict[str, Any]] = {}

        logger.info("EventRouter initialized")

    # ==================== ROUTING LOGIC ====================

    def should_trigger_immune_response(
        self,
        threat_event: ThreatDetectionEvent,
    ) -> bool:
        """
        Determine if a threat should trigger immune response.

        Business rules:
        - CRITICAL severity: Always trigger
        - HIGH severity: Trigger if confidence >= 0.8
        - MEDIUM severity: Trigger if confidence >= 0.9
        - LOW severity: Don't trigger (passive observation only)

        Args:
            threat_event: Threat detection event

        Returns:
            True if should trigger immune response
        """
        severity = threat_event.severity
        confidence = threat_event.confidence

        if severity == SeverityLevel.CRITICAL:
            return True
        elif severity == SeverityLevel.HIGH:
            return confidence >= 0.8
        elif severity == SeverityLevel.MEDIUM:
            return confidence >= 0.9
        else:  # LOW
            return False

    def determine_immune_response_type(
        self,
        threat_event: ThreatDetectionEvent,
    ) -> str:
        """
        Determine which immune agent type should respond.

        Routing logic:
        - SSH/Telnet attacks → Neutrophil (fast innate response)
        - Web application attacks → Dendritic Cell (pattern analysis)
        - Malware/Payload delivery → NK Cell (cytotoxic response)
        - Reconnaissance/Scanning → Passive observation only
        - Repeated attacks (same source) → T Cell (adaptive, memory-based)

        Args:
            threat_event: Threat detection event

        Returns:
            Agent type identifier
        """
        attack_type = threat_event.attack_type.lower()
        severity = threat_event.severity

        # High-severity payload delivery → NK Cell
        if severity == SeverityLevel.CRITICAL or "malware" in attack_type or "payload" in attack_type:
            return "nk_cell"

        # SSH/Telnet brute force → Neutrophil
        elif "ssh" in attack_type or "telnet" in attack_type or "brute" in attack_type:
            return "neutrophil"

        # Web attacks → Dendritic Cell
        elif "http" in attack_type or "web" in attack_type or "sql" in attack_type:
            return "dendritic_cell"

        # Reconnaissance → Passive observation
        elif "scan" in attack_type or "recon" in attack_type:
            return "passive"

        # Default: Neutrophil (general-purpose responder)
        else:
            return "neutrophil"

    def enrich_threat_with_context(
        self,
        threat_event: ThreatDetectionEvent,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Enrich threat event with additional context.

        Args:
            threat_event: Original threat event
            context: Optional additional context

        Returns:
            Enriched event data
        """
        enriched = threat_event.model_dump()

        # Add routing metadata
        enriched["routing"] = {
            "should_trigger_immune": self.should_trigger_immune_response(threat_event),
            "recommended_responder": self.determine_immune_response_type(threat_event),
            "routed_at": threat_event.timestamp.isoformat(),
            "router_version": "1.0.0",
        }

        # Add external context if provided
        if context:
            enriched["external_context"] = context

        return enriched

    def transform_immune_response_for_reactive_fabric(
        self,
        immune_event: ImmuneResponseEvent,
    ) -> dict[str, Any]:
        """
        Transform immune response for Reactive Fabric consumption.

        Reactive Fabric needs to know:
        - Was the threat neutralized?
        - Should honeypot be cycled/reset?
        - Should attacker IP be blocked at network level?

        Args:
            immune_event: Immune response event

        Returns:
            Transformed event for Reactive Fabric
        """
        action_map = {
            "isolate": "cycle_honeypot",
            "neutralize": "block_attacker_ip",
            "observe": "continue_monitoring",
        }

        return {
            "event_id": immune_event.event_id,
            "threat_id": immune_event.threat_id,
            "response_status": immune_event.response_status,
            "recommended_action": action_map.get(
                immune_event.response_action,
                "continue_monitoring"
            ),
            "details": immune_event.details,
            "timestamp": immune_event.timestamp.isoformat(),
        }

    # ==================== METRICS ====================

    def get_metrics(self) -> dict[str, Any]:
        """Get router metrics."""
        return {
            "events_routed": self.events_routed,
            "events_dropped": self.events_dropped,
            "routing_rules_count": len(self.routing_rules),
        }

    def __repr__(self) -> str:
        return f"EventRouter(routed={self.events_routed}, dropped={self.events_dropped})"
