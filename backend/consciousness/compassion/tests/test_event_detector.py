"""
Tests for Event Detection Module

Comprehensive test coverage for SufferingEvent and EventDetector classes.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from compassion.event_detector import EventDetector, EventType, SufferingEvent


class TestSufferingEvent:
    """Tests for SufferingEvent dataclass."""

    def test_suffering_event_creation_success(self):
        """Test successful creation of SufferingEvent."""
        agent_id = uuid4()
        event = SufferingEvent(
            agent_id=agent_id,
            event_type=EventType.DISTRESS,
            severity=7,
            description="Test distress event"
        )

        assert event.agent_id == agent_id
        assert event.event_type == EventType.DISTRESS
        assert event.severity == 7
        assert event.description == "Test distress event"
        assert isinstance(event.timestamp, datetime)
        assert isinstance(event.event_id, UUID)
        assert event.context == {}

    def test_suffering_event_with_context(self):
        """Test SufferingEvent with custom context."""
        agent_id = uuid4()
        context = {"source": "api", "endpoint": "/status"}
        event = SufferingEvent(
            agent_id=agent_id,
            event_type=EventType.CONFUSION,
            severity=5,
            description="API confusion",
            context=context
        )

        assert event.context == context
        assert event.context["source"] == "api"

    def test_suffering_event_severity_validation_too_low(self):
        """Test severity validation rejects values below 1."""
        with pytest.raises(ValueError, match="Severity must be 1-10"):
            SufferingEvent(
                agent_id=uuid4(),
                event_type=EventType.DISTRESS,
                severity=0,
                description="Invalid severity"
            )

    def test_suffering_event_severity_validation_too_high(self):
        """Test severity validation rejects values above 10."""
        with pytest.raises(ValueError, match="Severity must be 1-10"):
            SufferingEvent(
                agent_id=uuid4(),
                event_type=EventType.DISTRESS,
                severity=11,
                description="Invalid severity"
            )

    def test_suffering_event_severity_must_be_int(self):
        """Test severity validation rejects non-integer values."""
        with pytest.raises(ValueError, match="Severity must be int"):
            SufferingEvent(
                agent_id=uuid4(),
                event_type=EventType.DISTRESS,
                severity=7.5,
                description="Float severity"
            )

    def test_suffering_event_type_must_be_enum(self):
        """Test event_type validation rejects strings."""
        with pytest.raises(TypeError, match="event_type must be EventType enum"):
            SufferingEvent(
                agent_id=uuid4(),
                event_type="distress",  # String instead of enum
                severity=5,
                description="Wrong type"
            )

    def test_suffering_event_all_severities_valid(self):
        """Test all valid severity levels 1-10."""
        agent_id = uuid4()
        for severity in range(1, 11):
            event = SufferingEvent(
                agent_id=agent_id,
                event_type=EventType.DISTRESS,
                severity=severity,
                description=f"Severity {severity}"
            )
            assert event.severity == severity


class TestEventDetectorInit:
    """Tests for EventDetector initialization."""

    def test_event_detector_initialization(self):
        """Test EventDetector initializes correctly."""
        detector = EventDetector()
        assert detector._detected_events == []
        assert len(detector._detected_events) == 0

    def test_event_detector_repr(self):
        """Test EventDetector string representation."""
        detector = EventDetector()
        assert repr(detector) == "EventDetector(detected=0)"

        # Add event and check repr updates
        agent_id = uuid4()
        detector.detect_from_text(agent_id, "System error occurred")
        assert repr(detector) == "EventDetector(detected=1)"


class TestDetectFromText:
    """Tests for text-based event detection."""

    def test_detect_distress_from_error_keyword(self):
        """Test distress detection from 'error' keyword."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "System error occurred")

        assert event is not None
        assert event.agent_id == agent_id
        assert event.event_type == EventType.DISTRESS
        assert event.severity >= 5
        assert "error" in event.description.lower()

    def test_detect_distress_from_multiple_keywords(self):
        """Test higher severity with multiple distress keywords."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(
            agent_id,
            "Critical error: system failed and crashed"
        )

        assert event is not None
        assert event.event_type == EventType.DISTRESS
        assert event.severity >= 7  # Multiple keywords = higher severity

    def test_detect_confusion_from_confused_keyword(self):
        """Test confusion detection from 'confused' keyword."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "I'm confused about the request")

        assert event is not None
        assert event.event_type == EventType.CONFUSION
        assert "confused" in event.description.lower()

    def test_detect_confusion_from_dont_understand(self):
        """Test confusion detection from 'don't understand' phrase."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "I don't understand what to do")

        assert event is not None
        assert event.event_type == EventType.CONFUSION

    def test_detect_isolation_from_alone_keyword(self):
        """Test isolation detection from 'alone' keyword."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "Agent is alone with no peers")

        assert event is not None
        assert event.event_type == EventType.ISOLATION
        assert "alone" in event.description.lower()

    def test_detect_isolation_from_no_response(self):
        """Test isolation detection from 'no response' phrase."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "No response from any service")

        assert event is not None
        assert event.event_type == EventType.ISOLATION

    def test_detect_no_event_from_normal_text(self):
        """Test no event detected from normal text."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "System is running smoothly")

        assert event is None

    def test_detect_empty_text_returns_none(self):
        """Test empty text returns None."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "")

        assert event is None

    def test_detect_case_insensitive(self):
        """Test detection is case-insensitive."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "SYSTEM ERROR OCCURRED")

        assert event is not None
        assert event.event_type == EventType.DISTRESS

    def test_detect_with_context(self):
        """Test detection preserves context."""
        detector = EventDetector()
        agent_id = uuid4()
        context = {"source": "monitor", "timestamp": "2025-10-14T12:00:00"}

        event = detector.detect_from_text(
            agent_id,
            "Error detected",
            context=context
        )

        assert event is not None
        assert event.context == context

    def test_detect_prioritizes_distress_over_confusion(self):
        """Test distress is detected first when multiple types present."""
        detector = EventDetector()
        agent_id = uuid4()

        # Text contains both distress and confusion keywords
        event = detector.detect_from_text(
            agent_id,
            "System error occurred and I'm confused"
        )

        # Should detect distress first
        assert event.event_type == EventType.DISTRESS

    def test_detect_all_distress_keywords(self):
        """Test all distress keywords are detected."""
        detector = EventDetector()
        agent_id = uuid4()

        keywords = ["error", "fail", "crash", "panic", "emergency", "critical"]

        for keyword in keywords:
            detector.clear_events()
            event = detector.detect_from_text(agent_id, f"System {keyword} detected")
            assert event is not None
            assert event.event_type == EventType.DISTRESS

    def test_detect_all_confusion_keywords(self):
        """Test all confusion keywords are detected."""
        detector = EventDetector()
        agent_id = uuid4()

        keywords = ["confused", "uncertain", "unclear", "don't understand"]

        for keyword in keywords:
            detector.clear_events()
            event = detector.detect_from_text(agent_id, f"I am {keyword}")
            assert event is not None
            assert event.event_type == EventType.CONFUSION

    def test_detect_all_isolation_keywords(self):
        """Test all isolation keywords are detected."""
        detector = EventDetector()
        agent_id = uuid4()

        keywords = ["alone", "isolated", "no response", "disconnected"]

        for keyword in keywords:
            detector.clear_events()
            event = detector.detect_from_text(agent_id, f"Agent is {keyword}")
            assert event is not None
            assert event.event_type == EventType.ISOLATION


class TestDetectFromBehavior:
    """Tests for behavior-based event detection."""

    def test_detect_distress_from_high_error_rate(self):
        """Test distress detection from high error rate."""
        detector = EventDetector()
        agent_id = uuid4()

        metrics = {"error_rate": 0.75}
        event = detector.detect_from_behavior(agent_id, metrics)

        assert event is not None
        assert event.event_type == EventType.DISTRESS
        assert "error rate" in event.description.lower()
        assert event.severity >= 5

    def test_detect_distress_from_slow_response_time(self):
        """Test distress detection from slow response time."""
        detector = EventDetector()
        agent_id = uuid4()

        metrics = {"response_time_ms": 8000}
        event = detector.detect_from_behavior(agent_id, metrics)

        assert event is not None
        assert event.event_type == EventType.DISTRESS
        assert "response time" in event.description.lower()

    def test_detect_isolation_from_no_connections(self):
        """Test isolation detection from no active connections."""
        detector = EventDetector()
        agent_id = uuid4()

        metrics = {"active_connections": 0, "expected_connections": 5}
        event = detector.detect_from_behavior(agent_id, metrics)

        assert event is not None
        assert event.event_type == EventType.ISOLATION
        assert "no active connections" in event.description.lower()

    def test_no_detection_from_normal_metrics(self):
        """Test no event from normal metrics."""
        detector = EventDetector()
        agent_id = uuid4()

        metrics = {
            "error_rate": 0.05,
            "response_time_ms": 200,
            "active_connections": 10
        }
        event = detector.detect_from_behavior(agent_id, metrics)

        assert event is None

    def test_empty_metrics_returns_none(self):
        """Test empty metrics returns None."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_behavior(agent_id, {})

        assert event is None

    def test_error_rate_severity_calculation(self):
        """Test severity scales with error rate."""
        detector = EventDetector()
        agent_id = uuid4()

        # High error rate = high severity
        metrics = {"error_rate": 0.9}
        event = detector.detect_from_behavior(agent_id, metrics)

        assert event is not None
        assert event.severity >= 8

    def test_response_time_severity_calculation(self):
        """Test severity scales with response time."""
        detector = EventDetector()
        agent_id = uuid4()

        # Very slow response = high severity
        metrics = {"response_time_ms": 10000}
        event = detector.detect_from_behavior(agent_id, metrics)

        assert event is not None
        assert event.severity >= 8

    def test_no_isolation_when_no_expected_connections(self):
        """Test no isolation detected when connections not expected."""
        detector = EventDetector()
        agent_id = uuid4()

        metrics = {"active_connections": 0, "expected_connections": 0}
        event = detector.detect_from_behavior(agent_id, metrics)

        assert event is None


class TestGetRecentEvents:
    """Tests for retrieving recent events."""

    def test_get_recent_events_empty(self):
        """Test get_recent_events returns empty list initially."""
        detector = EventDetector()

        events = detector.get_recent_events()

        assert events == []

    def test_get_recent_events_returns_detected_events(self):
        """Test get_recent_events returns detected events."""
        detector = EventDetector()
        agent_id = uuid4()

        detector.detect_from_text(agent_id, "Error occurred")
        detector.detect_from_text(agent_id, "Another error")

        events = detector.get_recent_events()

        assert len(events) == 2

    def test_get_recent_events_sorted_by_timestamp(self):
        """Test events are sorted by timestamp descending."""
        detector = EventDetector()
        agent_id = uuid4()

        event1 = detector.detect_from_text(agent_id, "First error")
        event2 = detector.detect_from_text(agent_id, "Second error")

        events = detector.get_recent_events()

        # Most recent first
        assert events[0].event_id == event2.event_id
        assert events[1].event_id == event1.event_id

    def test_get_recent_events_filter_by_agent_id(self):
        """Test filtering events by agent_id."""
        detector = EventDetector()
        agent1 = uuid4()
        agent2 = uuid4()

        detector.detect_from_text(agent1, "Agent 1 error")
        detector.detect_from_text(agent2, "Agent 2 error")

        events = detector.get_recent_events(agent_id=agent1)

        assert len(events) == 1
        assert events[0].agent_id == agent1

    def test_get_recent_events_filter_by_event_type(self):
        """Test filtering events by event_type."""
        detector = EventDetector()
        agent_id = uuid4()

        detector.detect_from_text(agent_id, "Error occurred")
        detector.detect_from_text(agent_id, "I'm confused")

        events = detector.get_recent_events(event_type=EventType.DISTRESS)

        assert len(events) == 1
        assert events[0].event_type == EventType.DISTRESS

    def test_get_recent_events_limit(self):
        """Test limiting number of returned events."""
        detector = EventDetector()
        agent_id = uuid4()

        for i in range(10):
            detector.detect_from_text(agent_id, f"Error {i}")

        events = detector.get_recent_events(limit=5)

        assert len(events) == 5

    def test_get_recent_events_combined_filters(self):
        """Test combining agent_id and event_type filters."""
        detector = EventDetector()
        agent1 = uuid4()
        agent2 = uuid4()

        detector.detect_from_text(agent1, "Agent 1 error")
        detector.detect_from_text(agent1, "Agent 1 confused")
        detector.detect_from_text(agent2, "Agent 2 error")

        events = detector.get_recent_events(
            agent_id=agent1,
            event_type=EventType.DISTRESS
        )

        assert len(events) == 1
        assert events[0].agent_id == agent1
        assert events[0].event_type == EventType.DISTRESS


class TestClearEvents:
    """Tests for clearing events."""

    def test_clear_events_empties_list(self):
        """Test clear_events removes all events."""
        detector = EventDetector()
        agent_id = uuid4()

        detector.detect_from_text(agent_id, "Error occurred")
        assert len(detector._detected_events) == 1

        detector.clear_events()

        assert len(detector._detected_events) == 0
        assert detector.get_recent_events() == []

    def test_clear_events_on_empty_detector(self):
        """Test clear_events on empty detector doesn't error."""
        detector = EventDetector()

        detector.clear_events()

        assert len(detector._detected_events) == 0


class TestCalculateSeverity:
    """Tests for severity calculation logic."""

    def test_calculate_severity_single_keyword(self):
        """Test severity for single keyword match."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "System error")

        # Single keyword = medium severity
        assert event.severity == 5

    def test_calculate_severity_two_keywords(self):
        """Test severity for two keyword matches."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(agent_id, "Critical error occurred")

        # Two keywords = medium-high severity
        assert event.severity == 7

    def test_calculate_severity_three_plus_keywords(self):
        """Test severity for three or more keyword matches."""
        detector = EventDetector()
        agent_id = uuid4()

        event = detector.detect_from_text(
            agent_id,
            "Critical error: system failed and crashed"
        )

        # Three+ keywords = high severity
        assert event.severity == 9


class TestEventDetectorIntegration:
    """Integration tests for EventDetector."""

    def test_full_workflow_text_detection(self):
        """Test complete workflow: detect, store, retrieve."""
        detector = EventDetector()
        agent_id = uuid4()

        # Detect events
        event1 = detector.detect_from_text(agent_id, "System error")
        event2 = detector.detect_from_text(agent_id, "I'm confused")

        # Retrieve events
        all_events = detector.get_recent_events()
        distress_events = detector.get_recent_events(event_type=EventType.DISTRESS)

        assert len(all_events) == 2
        assert len(distress_events) == 1
        assert distress_events[0].event_id == event1.event_id

    def test_full_workflow_behavior_detection(self):
        """Test complete workflow with behavior metrics."""
        detector = EventDetector()
        agent_id = uuid4()

        # Detect from behavior
        metrics = {"error_rate": 0.8}
        event = detector.detect_from_behavior(agent_id, metrics)

        assert event is not None

        # Retrieve
        events = detector.get_recent_events(agent_id=agent_id)
        assert len(events) == 1
        assert "error rate" in events[0].description.lower()

    def test_mixed_detection_sources(self):
        """Test detecting from both text and behavior."""
        detector = EventDetector()
        agent_id = uuid4()

        # Text detection
        text_event = detector.detect_from_text(agent_id, "Error occurred")

        # Behavior detection
        metrics = {"response_time_ms": 6000}
        behavior_event = detector.detect_from_behavior(agent_id, metrics)

        # Both should be stored
        events = detector.get_recent_events()
        assert len(events) == 2
        assert text_event in events
        assert behavior_event in events
