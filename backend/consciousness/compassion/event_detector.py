"""
Event Detection Module

Detects suffering events from agent behavior and context.
Implements keyword-based pattern matching for distress, confusion, and isolation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class EventType(str, Enum):
    """Types of suffering events that can be detected."""

    DISTRESS = "distress"
    CONFUSION = "confusion"
    ISOLATION = "isolation"
    UNKNOWN = "unknown"


@dataclass
class SufferingEvent:
    """
    Represents a detected suffering event.

    Attributes:
        agent_id: UUID of the agent experiencing suffering
        event_type: Type of suffering (distress, confusion, isolation)
        severity: Severity level from 1 (low) to 10 (critical)
        description: Human-readable description of the event
        timestamp: When the event was detected
        context: Additional context data
        event_id: Unique identifier for this event
    """

    agent_id: UUID
    event_type: EventType
    severity: int
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        """Validate severity range."""
        if not isinstance(self.severity, int):
            raise ValueError(f"Severity must be int, got {type(self.severity)}")
        if not 1 <= self.severity <= 10:
            raise ValueError(f"Severity must be 1-10, got {self.severity}")
        if not isinstance(self.event_type, EventType):
            raise TypeError(f"event_type must be EventType enum, got {type(self.event_type)}")


class EventDetector:
    """
    Detects suffering events from text analysis and behavioral patterns.

    Uses keyword-based pattern matching to identify:
    - Distress: error, fail, crash, panic, emergency
    - Confusion: confused, uncertain, don't understand, unclear
    - Isolation: alone, isolated, no response, disconnected
    """

    # Keyword patterns for each event type
    DISTRESS_KEYWORDS = {
        "error", "fail", "failed", "failure", "crash", "crashed",
        "panic", "emergency", "critical", "severe", "crisis"
    }

    CONFUSION_KEYWORDS = {
        "confused", "confusing", "uncertain", "unsure", "unclear",
        "don't understand", "do not understand", "don't know",
        "ambiguous", "puzzled", "perplexed"
    }

    ISOLATION_KEYWORDS = {
        "alone", "isolated", "isolation", "no response", "unresponsive",
        "disconnected", "abandoned", "ignored", "silent", "unreachable"
    }

    def __init__(self):
        """Initialize the event detector."""
        self._detected_events: List[SufferingEvent] = []

    def detect_from_text(
        self,
        agent_id: UUID,
        text: str,
        context: Optional[Dict[str, any]] = None
    ) -> Optional[SufferingEvent]:
        """
        Detect suffering event from text content.

        Args:
            agent_id: UUID of the agent
            text: Text to analyze
            context: Optional additional context

        Returns:
            SufferingEvent if detected, None otherwise
        """
        if not text:
            return None

        text_lower = text.lower()
        context = context or {}

        # Check for distress
        for keyword in self.DISTRESS_KEYWORDS:
            if keyword in text_lower:
                severity = self._calculate_severity(text_lower, self.DISTRESS_KEYWORDS)
                event = SufferingEvent(
                    agent_id=agent_id,
                    event_type=EventType.DISTRESS,
                    severity=severity,
                    description=f"Distress detected: keyword '{keyword}' in text",
                    context=context
                )
                self._detected_events.append(event)
                return event

        # Check for confusion
        for keyword in self.CONFUSION_KEYWORDS:
            if keyword in text_lower:
                severity = self._calculate_severity(text_lower, self.CONFUSION_KEYWORDS)
                event = SufferingEvent(
                    agent_id=agent_id,
                    event_type=EventType.CONFUSION,
                    severity=severity,
                    description=f"Confusion detected: keyword '{keyword}' in text",
                    context=context
                )
                self._detected_events.append(event)
                return event

        # Check for isolation
        for keyword in self.ISOLATION_KEYWORDS:
            if keyword in text_lower:
                severity = self._calculate_severity(text_lower, self.ISOLATION_KEYWORDS)
                event = SufferingEvent(
                    agent_id=agent_id,
                    event_type=EventType.ISOLATION,
                    severity=severity,
                    description=f"Isolation detected: keyword '{keyword}' in text",
                    context=context
                )
                self._detected_events.append(event)
                return event

        return None

    def detect_from_behavior(
        self,
        agent_id: UUID,
        metrics: Dict[str, any]
    ) -> Optional[SufferingEvent]:
        """
        Detect suffering event from behavioral metrics.

        Args:
            agent_id: UUID of the agent
            metrics: Behavioral metrics (error_rate, response_time, etc.)

        Returns:
            SufferingEvent if detected, None otherwise
        """
        if not metrics:
            return None

        # High error rate indicates distress
        error_rate = metrics.get("error_rate", 0.0)
        if error_rate > 0.5:  # More than 50% errors
            severity = min(10, int(error_rate * 10) + 5)
            event = SufferingEvent(
                agent_id=agent_id,
                event_type=EventType.DISTRESS,
                severity=severity,
                description=f"High error rate detected: {error_rate:.2%}",
                context={"metrics": metrics}
            )
            self._detected_events.append(event)
            return event

        # High response time indicates possible issues
        response_time = metrics.get("response_time_ms", 0)
        if response_time > 5000:  # More than 5 seconds
            severity = min(10, int(response_time / 1000))
            event = SufferingEvent(
                agent_id=agent_id,
                event_type=EventType.DISTRESS,
                severity=severity,
                description=f"Slow response time: {response_time}ms",
                context={"metrics": metrics}
            )
            self._detected_events.append(event)
            return event

        # No connections indicates isolation
        connection_count = metrics.get("active_connections", 0)
        if connection_count == 0 and metrics.get("expected_connections", 0) > 0:
            event = SufferingEvent(
                agent_id=agent_id,
                event_type=EventType.ISOLATION,
                severity=7,
                description="No active connections detected",
                context={"metrics": metrics}
            )
            self._detected_events.append(event)
            return event

        return None

    def _calculate_severity(self, text: str, keyword_set: set) -> int:
        """
        Calculate severity based on keyword matches.

        Args:
            text: Text to analyze
            keyword_set: Set of keywords to match

        Returns:
            Severity level from 1-10
        """
        match_count = sum(1 for keyword in keyword_set if keyword in text)

        # Base severity on number of matches
        if match_count >= 3:
            return 9  # Multiple indicators = high severity
        elif match_count == 2:
            return 7  # Two indicators = medium-high
        else:
            return 5  # Single indicator = medium

    def get_recent_events(
        self,
        agent_id: Optional[UUID] = None,
        event_type: Optional[EventType] = None,
        limit: int = 10
    ) -> List[SufferingEvent]:
        """
        Get recent detected events with optional filtering.

        Args:
            agent_id: Filter by agent ID
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        events = self._detected_events

        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Sort by timestamp descending and limit
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    def clear_events(self):
        """Clear all detected events."""
        self._detected_events.clear()

    def __repr__(self) -> str:
        """String representation."""
        return f"EventDetector(detected={len(self._detected_events)})"
