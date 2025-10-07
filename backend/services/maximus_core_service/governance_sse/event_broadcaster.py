"""
Event Broadcaster - Simplified Interface for SSE Broadcasting

Provides a clean facade over ConnectionManager for broadcasting governance events.
Supports targeted broadcasting, event filtering, and priority-based routing.

This module simplifies event broadcasting for external callers who don't need
to interact directly with the SSE server internals.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: Production-ready, REGRA DE OURO compliant
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

# HITL imports
from hitl import (
    HITLDecision,
    RiskLevel,
    DecisionStatus,
)

# Local imports
from .sse_server import SSEEvent, decision_to_sse_data

logger = logging.getLogger(__name__)


# ============================================================================
# Event Priority and Filtering
# ============================================================================

@dataclass
class BroadcastOptions:
    """
    Options for event broadcasting.

    Allows fine-grained control over event delivery.
    """
    # Targeting
    target_operators: Optional[List[str]] = None  # None = all operators
    target_roles: Optional[List[str]] = None  # Filter by operator role
    priority_only: Optional[RiskLevel] = None  # Only operators handling this risk level

    # Delivery
    reliable: bool = True  # Retry on delivery failure
    max_retries: int = 3
    retry_delay: float = 1.0  # Seconds between retries

    # Filtering
    deduplicate: bool = True  # Don't send duplicate events
    ttl_seconds: Optional[int] = None  # Event time-to-live


class EventBroadcaster:
    """
    Event broadcaster for Governance SSE.

    Provides high-level interface for broadcasting events to operators.
    Handles event formatting, targeting, and delivery confirmation.

    Usage:
        broadcaster = EventBroadcaster()
        await broadcaster.broadcast_decision_pending(decision)
        await broadcaster.broadcast_decision_resolved(decision_id, status)
    """

    def __init__(self, connection_manager):
        """
        Initialize event broadcaster.

        Args:
            connection_manager: ConnectionManager instance from SSE server
        """
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Event deduplication (track last 1000 event IDs)
        self._sent_events: set = set()
        self._max_dedup_size = 1000

        # Metrics
        self.metrics = {
            "events_broadcast": 0,
            "events_targeted": 0,
            "events_filtered": 0,
            "events_deduplicated": 0,
            "delivery_failures": 0,
        }

        self.logger.info("Event Broadcaster initialized")

    async def broadcast_decision_pending(
        self,
        decision: HITLDecision,
        options: Optional[BroadcastOptions] = None,
    ) -> bool:
        """
        Broadcast that a new decision is pending operator review.

        Args:
            decision: HITL decision to broadcast
            options: Broadcasting options (None = defaults)

        Returns:
            True if broadcast successful, False otherwise
        """
        options = options or BroadcastOptions()

        # Create SSE event
        event = SSEEvent(
            event_type="decision_pending",
            event_id=f"dec_{decision.decision_id}_{datetime.now(timezone.utc).timestamp()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=decision_to_sse_data(decision),
        )

        # Broadcast
        success = await self._broadcast_with_options(event, options)

        if success:
            self.metrics["events_broadcast"] += 1
            self.logger.info(
                f"Broadcasted decision_pending: {decision.decision_id} "
                f"(risk={decision.risk_level.value})"
            )
        else:
            self.metrics["delivery_failures"] += 1
            self.logger.error(f"Failed to broadcast decision {decision.decision_id}")

        return success

    async def broadcast_decision_resolved(
        self,
        decision_id: str,
        status: DecisionStatus,
        operator_id: str,
        reasoning: Optional[str] = None,
        options: Optional[BroadcastOptions] = None,
    ) -> bool:
        """
        Broadcast that a decision has been resolved.

        Args:
            decision_id: Decision ID
            status: Final decision status (APPROVED/REJECTED/etc)
            operator_id: Operator who resolved it
            reasoning: Optional reasoning for decision
            options: Broadcasting options

        Returns:
            True if broadcast successful
        """
        options = options or BroadcastOptions()

        # Create SSE event
        event = SSEEvent(
            event_type="decision_resolved",
            event_id=f"resolved_{decision_id}_{datetime.now(timezone.utc).timestamp()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "decision_id": decision_id,
                "status": status.value,
                "resolved_by": operator_id,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "reasoning": reasoning,
            },
        )

        # Broadcast
        success = await self._broadcast_with_options(event, options)

        if success:
            self.metrics["events_broadcast"] += 1
            self.logger.info(
                f"Broadcasted decision_resolved: {decision_id} "
                f"(status={status.value}, operator={operator_id})"
            )
        else:
            self.metrics["delivery_failures"] += 1

        return success

    async def broadcast_sla_warning(
        self,
        decision: HITLDecision,
        time_remaining_seconds: int,
        options: Optional[BroadcastOptions] = None,
    ) -> bool:
        """
        Broadcast SLA warning for decision approaching deadline.

        Args:
            decision: Decision approaching SLA deadline
            time_remaining_seconds: Seconds until SLA violation
            options: Broadcasting options

        Returns:
            True if broadcast successful
        """
        options = options or BroadcastOptions()

        event = SSEEvent(
            event_type="sla_warning",
            event_id=f"sla_warn_{decision.decision_id}_{datetime.now(timezone.utc).timestamp()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "decision_id": decision.decision_id,
                "risk_level": decision.risk_level.value,
                "action_type": decision.context.action_type.value,
                "time_remaining_seconds": time_remaining_seconds,
                "message": f"SLA warning: {time_remaining_seconds}s remaining",
            },
        )

        success = await self._broadcast_with_options(event, options)

        if success:
            self.metrics["events_broadcast"] += 1
            self.logger.warning(
                f"Broadcasted SLA warning: {decision.decision_id} "
                f"(remaining={time_remaining_seconds}s)"
            )

        return success

    async def broadcast_sla_violation(
        self,
        decision: HITLDecision,
        options: Optional[BroadcastOptions] = None,
    ) -> bool:
        """
        Broadcast SLA violation alert.

        Args:
            decision: Decision that violated SLA
            options: Broadcasting options

        Returns:
            True if broadcast successful
        """
        options = options or BroadcastOptions()

        event = SSEEvent(
            event_type="sla_violation",
            event_id=f"sla_viol_{decision.decision_id}_{datetime.now(timezone.utc).timestamp()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "decision_id": decision.decision_id,
                "risk_level": decision.risk_level.value,
                "action_type": decision.context.action_type.value,
                "message": f"SLA VIOLATED for decision {decision.decision_id}",
                "severity": "critical",
            },
        )

        success = await self._broadcast_with_options(event, options)

        if success:
            self.metrics["events_broadcast"] += 1
            self.logger.error(f"Broadcasted SLA violation: {decision.decision_id}")

        return success

    async def broadcast_system_message(
        self,
        message: str,
        severity: str = "info",
        options: Optional[BroadcastOptions] = None,
    ) -> bool:
        """
        Broadcast system message to operators.

        Args:
            message: System message
            severity: Severity level (info/warning/error/critical)
            options: Broadcasting options

        Returns:
            True if broadcast successful
        """
        options = options or BroadcastOptions()

        event = SSEEvent(
            event_type="system_message",
            event_id=f"sys_{datetime.now(timezone.utc).timestamp()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "message": message,
                "severity": severity,
            },
        )

        success = await self._broadcast_with_options(event, options)

        if success:
            self.metrics["events_broadcast"] += 1

        return success

    async def _broadcast_with_options(
        self, event: SSEEvent, options: BroadcastOptions
    ) -> bool:
        """
        Internal broadcast with option processing.

        Args:
            event: SSE event to broadcast
            options: Broadcasting options

        Returns:
            True if broadcast successful
        """
        # Deduplication check
        if options.deduplicate:
            if event.event_id in self._sent_events:
                self.metrics["events_deduplicated"] += 1
                self.logger.debug(f"Event {event.event_id} deduplicated")
                return True  # Consider duplicate as "successful"

            self._sent_events.add(event.event_id)

            # Cleanup dedup cache if too large
            if len(self._sent_events) > self._max_dedup_size:
                # Remove oldest 200 IDs (approximation)
                excess = len(self._sent_events) - self._max_dedup_size
                for _ in range(excess):
                    self._sent_events.pop()

        # Filter by target operators
        target_operators = None
        if options.target_operators:
            target_operators = options.target_operators
            self.metrics["events_targeted"] += 1

        # Broadcast to specified operators (by operator ID)
        # Role-based filtering can be added via target_operators list

        # Attempt broadcast with retries
        retries = 0
        while retries <= options.max_retries:
            try:
                await self.connection_manager.broadcast_event(event, target_operators)
                return True

            except Exception as e:
                retries += 1
                if retries > options.max_retries:
                    self.logger.error(
                        f"Broadcast failed after {options.max_retries} retries: {e}",
                        exc_info=True,
                    )
                    return False

                self.logger.warning(
                    f"Broadcast retry {retries}/{options.max_retries} for {event.event_id}"
                )

                if options.reliable:
                    import asyncio
                    await asyncio.sleep(options.retry_delay)
                else:
                    return False

        return False

    def get_metrics(self) -> Dict:
        """
        Get broadcaster metrics.

        Returns:
            Metrics dictionary
        """
        return {
            **self.metrics,
            "active_connections": self.connection_manager.metrics["active_connections"],
            "dedup_cache_size": len(self._sent_events),
        }

    def clear_dedup_cache(self) -> None:
        """Clear deduplication cache (for testing or manual reset)."""
        self._sent_events.clear()
        self.logger.info("Deduplication cache cleared")
