"""Event Collector - Consciousness System Events

Collects discrete events from consciousness subsystems:
- Safety violations (threshold breaches, anomalies)
- PFC social signals (compassionate actions)
- ToM belief updates (mental state changes)
- ESGT ignition events (consciousness moments)

Events are timestamped and tagged with salience metadata
for orchestration and ESGT trigger evaluation.

Architecture:
    EventCollector → DataOrchestrator → ESGT

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Sprint: Reactive Fabric Sprint 3
"""

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of consciousness events."""

    SAFETY_VIOLATION = "safety_violation"
    PFC_SOCIAL_SIGNAL = "pfc_social_signal"
    TOM_BELIEF_UPDATE = "tom_belief_update"
    ESGT_IGNITION = "esgt_ignition"
    AROUSAL_CHANGE = "arousal_change"
    SYSTEM_HEALTH = "system_health"


class EventSeverity(Enum):
    """Event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ConsciousnessEvent:
    """A discrete consciousness system event."""

    event_id: str
    event_type: EventType
    severity: EventSeverity
    timestamp: float

    # Event data
    source: str  # Component that generated event
    data: Dict[str, Any] = field(default_factory=dict)

    # Salience factors (for ESGT orchestration)
    novelty: float = 0.5  # How unexpected is this?
    relevance: float = 0.5  # How important for current goals?
    urgency: float = 0.5  # How time-critical?

    # Metadata
    processed: bool = False
    esgt_triggered: bool = False


class EventCollector:
    """
    Collects events from consciousness subsystems.

    Events are stored in a ring buffer (recent events only)
    and can be queried for orchestration and dashboards.

    Usage:
        collector = EventCollector(consciousness_system, max_events=1000)

        # Collect recent events
        events = await collector.collect_events()

        # Query events
        safety_events = collector.get_events_by_type(EventType.SAFETY_VIOLATION)
        recent = collector.get_recent_events(limit=10)
    """

    def __init__(self, consciousness_system: Any, max_events: int = 1000):
        """Initialize event collector.

        Args:
            consciousness_system: ConsciousnessSystem instance
            max_events: Maximum events to keep in buffer
        """
        self.system = consciousness_system
        self.max_events = max_events

        # Event buffer (ring buffer)
        self.events: deque[ConsciousnessEvent] = deque(maxlen=max_events)

        # Event counters
        self.total_events_collected = 0
        self.events_by_type: Dict[EventType, int] = {t: 0 for t in EventType}

        # Last collection state (for delta detection)
        self._last_collection_time = time.time()
        self._last_esgt_event_count = 0
        self._last_pfc_signals = 0
        self._last_tom_beliefs = 0
        self._last_safety_violations = 0

        logger.info(f"EventCollector initialized (max_events={max_events})")

    async def collect_events(self) -> List[ConsciousnessEvent]:
        """Collect new events since last collection.

        Detects changes in subsystem state and generates events.

        Returns:
            List of new ConsciousnessEvent objects
        """
        new_events: List[ConsciousnessEvent] = []
        now = time.time()

        try:
            # Collect ESGT events
            if self.system.esgt_coordinator:
                esgt_events = await self._collect_esgt_events()
                new_events.extend(esgt_events)

            # Collect PFC events (Track 1)
            if self.system.prefrontal_cortex:
                pfc_events = await self._collect_pfc_events()
                new_events.extend(pfc_events)

            # Collect ToM events (Track 1)
            if self.system.tom_engine:
                tom_events = await self._collect_tom_events()
                new_events.extend(tom_events)

            # Collect Safety events
            if self.system.safety_protocol:
                safety_events = await self._collect_safety_events()
                new_events.extend(safety_events)

            # Collect Arousal events
            if self.system.arousal_controller:
                arousal_events = await self._collect_arousal_events()
                new_events.extend(arousal_events)

            # Add events to buffer
            for event in new_events:
                self.events.append(event)
                self.total_events_collected += 1
                self.events_by_type[event.event_type] += 1

            logger.debug(f"Collected {len(new_events)} events")

        except Exception as e:
            logger.error(f"Error collecting events: {e}")

        self._last_collection_time = now
        return new_events

    async def _collect_esgt_events(self) -> List[ConsciousnessEvent]:
        """Collect ESGT ignition events."""
        events = []

        try:
            coordinator = self.system.esgt_coordinator
            current_count = coordinator.total_events

            # Detect new ESGT events
            if current_count > self._last_esgt_event_count:
                # Get recent events from history
                new_count = current_count - self._last_esgt_event_count
                recent_esgt_events = coordinator.event_history[-new_count:]

                for esgt_event in recent_esgt_events:
                    # Create ConsciousnessEvent
                    event = ConsciousnessEvent(
                        event_id=f"esgt-{esgt_event.event_id}",
                        event_type=EventType.ESGT_IGNITION,
                        severity=EventSeverity.HIGH if esgt_event.success else EventSeverity.MEDIUM,
                        timestamp=esgt_event.timestamp_start,
                        source="ESGT Coordinator",
                        data={
                            "success": esgt_event.success,
                            "coherence": esgt_event.achieved_coherence,
                            "duration_ms": esgt_event.total_duration_ms,
                            "nodes": esgt_event.node_count,
                        },
                        novelty=0.8,  # ESGT events are always novel
                        relevance=0.9,  # Consciousness moments are highly relevant
                        urgency=0.7,  # Moderate urgency
                    )
                    events.append(event)

            self._last_esgt_event_count = current_count

        except Exception as e:
            logger.warning(f"Error collecting ESGT events: {e}")

        return events

    async def _collect_pfc_events(self) -> List[ConsciousnessEvent]:
        """Collect PFC social signal events (Track 1)."""
        events = []

        try:
            pfc_status = await self.system.prefrontal_cortex.get_status()
            current_signals = pfc_status.get("total_signals_processed", 0)

            # Detect new PFC signals
            if current_signals > self._last_pfc_signals:
                # Create event for new signals
                event = ConsciousnessEvent(
                    event_id=f"pfc-{int(time.time() * 1000)}",
                    event_type=EventType.PFC_SOCIAL_SIGNAL,
                    severity=EventSeverity.MEDIUM,
                    timestamp=time.time(),
                    source="PrefrontalCortex",
                    data={
                        "signals_processed": current_signals,
                        "actions_generated": pfc_status.get("total_actions_generated", 0),
                        "approval_rate": pfc_status.get("approval_rate", 0.0),
                    },
                    novelty=0.6,  # Social signals are moderately novel
                    relevance=0.8,  # Highly relevant for social cognition
                    urgency=0.5,  # Moderate urgency
                )
                events.append(event)

            self._last_pfc_signals = current_signals

        except Exception as e:
            logger.warning(f"Error collecting PFC events: {e}")

        return events

    async def _collect_tom_events(self) -> List[ConsciousnessEvent]:
        """Collect ToM belief update events (Track 1)."""
        events = []

        try:
            tom_stats = await self.system.tom_engine.get_stats()
            current_beliefs = tom_stats.get("memory", {}).get("total_beliefs", 0)

            # Detect new beliefs
            if current_beliefs > self._last_tom_beliefs:
                # Create event for new beliefs
                event = ConsciousnessEvent(
                    event_id=f"tom-{int(time.time() * 1000)}",
                    event_type=EventType.TOM_BELIEF_UPDATE,
                    severity=EventSeverity.LOW,
                    timestamp=time.time(),
                    source="ToM Engine",
                    data={
                        "total_beliefs": current_beliefs,
                        "total_agents": tom_stats.get("total_agents", 0),
                        "contradictions": tom_stats.get("contradictions", 0),
                    },
                    novelty=0.5,  # Belief updates are moderately novel
                    relevance=0.7,  # Relevant for mental model tracking
                    urgency=0.3,  # Low urgency
                )
                events.append(event)

            self._last_tom_beliefs = current_beliefs

        except Exception as e:
            logger.warning(f"Error collecting ToM events: {e}")

        return events

    async def _collect_safety_events(self) -> List[ConsciousnessEvent]:
        """Collect Safety protocol events."""
        events = []

        try:
            safety_status = self.system.get_safety_status()

            if safety_status:
                current_violations = safety_status.get("active_violations", 0)

                # Detect new violations
                if current_violations > self._last_safety_violations:
                    # Get recent violations
                    violations = self.system.get_safety_violations(limit=10)

                    for violation in violations:
                        event = ConsciousnessEvent(
                            event_id=f"safety-{violation.violation_id}",
                            event_type=EventType.SAFETY_VIOLATION,
                            severity=EventSeverity.CRITICAL if violation.severity.value == "CRITICAL" else EventSeverity.HIGH,
                            timestamp=violation.timestamp.timestamp(),
                            source="Safety Protocol",
                            data={
                                "violation_type": violation.violation_type.value,
                                "severity": violation.severity.value,
                                "value_observed": violation.value_observed,
                                "threshold": violation.threshold_violated,
                                "message": violation.message,
                            },
                            novelty=0.9,  # Safety violations are highly novel
                            relevance=1.0,  # Critical relevance
                            urgency=1.0,  # Maximum urgency
                        )
                        events.append(event)

                self._last_safety_violations = current_violations

        except Exception as e:
            logger.warning(f"Error collecting Safety events: {e}")

        return events

    async def _collect_arousal_events(self) -> List[ConsciousnessEvent]:
        """Collect Arousal change events."""
        events = []

        try:
            arousal_state = self.system.arousal_controller.get_current_arousal()

            if arousal_state:
                # Detect significant arousal changes (>0.2 delta)
                # (This requires tracking previous arousal state)
                # For now, we'll generate events for extreme arousal
                if arousal_state.arousal < 0.2 or arousal_state.arousal > 0.9:
                    event = ConsciousnessEvent(
                        event_id=f"arousal-{int(time.time() * 1000)}",
                        event_type=EventType.AROUSAL_CHANGE,
                        severity=EventSeverity.MEDIUM,
                        timestamp=time.time(),
                        source="Arousal Controller",
                        data={
                            "arousal_level": arousal_state.arousal,
                            "classification": arousal_state.level.value if hasattr(arousal_state.level, 'value') else str(arousal_state.level),
                            "stress": arousal_state.stress_contribution,
                            "need": arousal_state.need_contribution,
                        },
                        novelty=0.7,  # Extreme arousal is novel
                        relevance=0.8,  # Highly relevant for system state
                        urgency=0.6,  # Moderate urgency
                    )
                    events.append(event)

        except Exception as e:
            logger.warning(f"Error collecting Arousal events: {e}")

        return events

    def get_events_by_type(self, event_type: EventType) -> List[ConsciousnessEvent]:
        """Get events filtered by type.

        Args:
            event_type: Event type to filter

        Returns:
            List of matching events
        """
        return [e for e in self.events if e.event_type == event_type]

    def get_recent_events(self, limit: int = 10) -> List[ConsciousnessEvent]:
        """Get most recent events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events (newest first)
        """
        recent = list(self.events)[-limit:]
        return sorted(recent, key=lambda e: e.timestamp, reverse=True)

    def get_unprocessed_events(self) -> List[ConsciousnessEvent]:
        """Get events that haven't been processed yet.

        Returns:
            List of unprocessed events
        """
        return [e for e in self.events if not e.processed]

    def mark_processed(self, event_id: str) -> None:
        """Mark event as processed.

        Args:
            event_id: Event ID to mark
        """
        for event in self.events:
            if event.event_id == event_id:
                event.processed = True
                break

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collector statistics.

        Returns:
            Dict with event counts and statistics
        """
        return {
            "total_events_collected": self.total_events_collected,
            "events_in_buffer": len(self.events),
            "events_by_type": {k.value: v for k, v in self.events_by_type.items()},
            "buffer_capacity": self.max_events,
            "buffer_utilization": len(self.events) / self.max_events,
        }

    def __repr__(self) -> str:
        return (
            f"EventCollector("
            f"total_events={self.total_events_collected}, "
            f"buffer_size={len(self.events)}/{self.max_events})"
        )
