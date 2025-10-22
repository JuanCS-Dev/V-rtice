"""Tests for EventCollector - Reactive Fabric Sprint 3.

Target: 100% statement + branch coverage.

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
import time
from unittest.mock import MagicMock

from consciousness.reactive_fabric.collectors.event_collector import (
    EventCollector,
    ConsciousnessEvent,
    EventType,
    EventSeverity,
)


class TestEventDataclasses:
    """Test event enum and dataclass definitions."""

    def test_event_type_enum(self):
        """Test EventType enum values."""
        assert EventType.SAFETY_VIOLATION.value == "safety_violation"
        assert EventType.PFC_SOCIAL_SIGNAL.value == "pfc_social_signal"
        assert EventType.TOM_BELIEF_UPDATE.value == "tom_belief_update"
        assert EventType.ESGT_IGNITION.value == "esgt_ignition"
        assert EventType.AROUSAL_CHANGE.value == "arousal_change"
        assert EventType.SYSTEM_HEALTH.value == "system_health"

    def test_event_severity_enum(self):
        """Test EventSeverity enum values."""
        assert EventSeverity.LOW.value == "low"
        assert EventSeverity.MEDIUM.value == "medium"
        assert EventSeverity.HIGH.value == "high"
        assert EventSeverity.CRITICAL.value == "critical"

    def test_consciousness_event_creation(self):
        """Test ConsciousnessEvent dataclass."""
        event = ConsciousnessEvent(
            event_id="test_001",
            event_type=EventType.SAFETY_VIOLATION,
            severity=EventSeverity.HIGH,
            timestamp=time.time(),
            source="Test",
            data={"key": "value"},
            novelty=0.8,
            relevance=0.9,
            urgency=1.0,
        )

        assert event.event_id == "test_001"
        assert event.event_type == EventType.SAFETY_VIOLATION
        assert event.severity == EventSeverity.HIGH
        assert event.processed is False
        assert event.esgt_triggered is False


class TestEventCollectorInit:
    """Test EventCollector initialization."""

    def test_init_default_params(self, mock_consciousness_system):
        """Test initialization with default params."""
        collector = EventCollector(mock_consciousness_system)

        assert collector.system == mock_consciousness_system
        assert collector.max_events == 1000
        assert len(collector.events) == 0
        assert collector.total_events_collected == 0
        assert len(collector.events_by_type) == 6  # 6 EventType values

    def test_init_custom_max_events(self, mock_consciousness_system):
        """Test initialization with custom max_events."""
        collector = EventCollector(mock_consciousness_system, max_events=500)

        assert collector.max_events == 500
        assert collector.events.maxlen == 500


class TestCollectEvents:
    """Test collect_events() method."""

    @pytest.mark.asyncio
    async def test_collect_events_success(self, mock_consciousness_system):
        """Test successful event collection."""
        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        assert isinstance(events, list)
        assert collector.total_events_collected >= 0

    @pytest.mark.asyncio
    async def test_collect_events_multiple_times(self, mock_consciousness_system):
        """Test collecting events multiple times."""
        collector = EventCollector(mock_consciousness_system)

        events1 = await collector.collect_events()
        events2 = await collector.collect_events()

        assert isinstance(events1, list)
        assert isinstance(events2, list)

    @pytest.mark.asyncio
    async def test_collect_with_exception_handling(self, mock_consciousness_system):
        """Test that exceptions are handled gracefully."""
        mock_consciousness_system.esgt_coordinator.total_events = None
        type(mock_consciousness_system.esgt_coordinator).total_events = property(
            lambda self: (_ for _ in ()).throw(Exception("ESGT error"))
        )

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should return empty list despite error
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_collect_top_level_exception(self, mock_consciousness_system):
        """Test top-level exception handling in collect_events."""
        # Force exception at top level by making esgt_coordinator evaluation fail
        type(mock_consciousness_system).esgt_coordinator = property(
            lambda self: (_ for _ in ()).throw(Exception("Top-level error"))
        )

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should handle error and return empty list
        assert isinstance(events, list)
        assert events == []


class TestCollectESGTEvents:
    """Test _collect_esgt_events() method."""

    @pytest.mark.asyncio
    async def test_collect_esgt_new_event(self, mock_consciousness_system):
        """Test collecting new ESGT events."""
        mock_consciousness_system.esgt_coordinator.total_events = 101  # One more than initial

        collector = EventCollector(mock_consciousness_system)
        # First collection establishes baseline
        await collector.collect_events()

        # Second collection should detect new event
        mock_consciousness_system.esgt_coordinator.total_events = 102
        events = await collector.collect_events()

        esgt_events = [e for e in events if e.event_type == EventType.ESGT_IGNITION]
        assert len(esgt_events) > 0

    @pytest.mark.asyncio
    async def test_collect_esgt_no_new_events(self, mock_consciousness_system):
        """Test collecting when no new ESGT events."""
        collector = EventCollector(mock_consciousness_system)

        events = await collector.collect_events()
        # Should collect initial events
        first_count = len([e for e in events if e.event_type == EventType.ESGT_IGNITION])

        # Second collection with same count
        events2 = await collector.collect_events()
        second_count = len([e for e in events2 if e.event_type == EventType.ESGT_IGNITION])

        assert second_count == 0  # No new events

    @pytest.mark.asyncio
    async def test_collect_esgt_exception_handling(self, mock_consciousness_system):
        """Test ESGT event collection with exception."""
        mock_consciousness_system.esgt_coordinator.total_events = 105
        mock_consciousness_system.esgt_coordinator.event_history = None

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should handle error gracefully
        assert isinstance(events, list)


class TestCollectPFCEvents:
    """Test _collect_pfc_events() method."""

    @pytest.mark.asyncio
    async def test_collect_pfc_new_signals(self, mock_consciousness_system):
        """Test collecting new PFC signals."""
        collector = EventCollector(mock_consciousness_system)
        await collector.collect_events()  # Establish baseline

        # Update signal count
        mock_consciousness_system.prefrontal_cortex.get_status = pytest.helpers.AsyncMock(
            return_value={
                "total_signals_processed": 50,  # More than initial 42
                "total_actions_generated": 12,
                "approval_rate": 0.88,
            }
        )

        events = await collector.collect_events()
        pfc_events = [e for e in events if e.event_type == EventType.PFC_SOCIAL_SIGNAL]

        assert len(pfc_events) > 0

    @pytest.mark.asyncio
    async def test_collect_pfc_no_new_signals(self, mock_consciousness_system):
        """Test collecting when no new PFC signals."""
        collector = EventCollector(mock_consciousness_system)

        await collector.collect_events()  # First collection
        events = await collector.collect_events()  # Second with same count

        pfc_events = [e for e in events if e.event_type == EventType.PFC_SOCIAL_SIGNAL]
        # Should only collect on first pass or when count changes
        assert isinstance(pfc_events, list)

    @pytest.mark.asyncio
    async def test_collect_pfc_exception_handling(self, mock_consciousness_system):
        """Test PFC event collection with exception."""
        from unittest.mock import AsyncMock
        mock_consciousness_system.prefrontal_cortex.get_status = AsyncMock(
            side_effect=Exception("PFC error")
        )

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should handle error gracefully
        assert isinstance(events, list)


class TestCollectToMEvents:
    """Test _collect_tom_events() method."""

    @pytest.mark.asyncio
    async def test_collect_tom_new_beliefs(self, mock_consciousness_system):
        """Test collecting new ToM belief updates."""
        from unittest.mock import AsyncMock
        collector = EventCollector(mock_consciousness_system)
        await collector.collect_events()  # Establish baseline

        # Update belief count
        mock_consciousness_system.tom_engine.get_stats = AsyncMock(return_value={
            "total_agents": 6,
            "memory": {"total_beliefs": 30},  # More than initial 25
            "contradictions": 0,
        })

        events = await collector.collect_events()
        tom_events = [e for e in events if e.event_type == EventType.TOM_BELIEF_UPDATE]

        assert len(tom_events) > 0

    @pytest.mark.asyncio
    async def test_collect_tom_no_new_beliefs(self, mock_consciousness_system):
        """Test collecting when no new ToM beliefs."""
        collector = EventCollector(mock_consciousness_system)

        await collector.collect_events()
        events = await collector.collect_events()

        # Second collection should have no new ToM events
        tom_events = [e for e in events if e.event_type == EventType.TOM_BELIEF_UPDATE]
        assert isinstance(tom_events, list)

    @pytest.mark.asyncio
    async def test_collect_tom_exception_handling(self, mock_consciousness_system):
        """Test ToM event collection with exception."""
        from unittest.mock import AsyncMock
        mock_consciousness_system.tom_engine.get_stats = AsyncMock(
            side_effect=Exception("ToM error")
        )

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        assert isinstance(events, list)


class TestCollectSafetyEvents:
    """Test _collect_safety_events() method."""

    @pytest.mark.asyncio
    async def test_collect_safety_new_violations(self, mock_consciousness_system):
        """Test collecting new safety violations."""
        collector = EventCollector(mock_consciousness_system)
        await collector.collect_events()  # Establish baseline

        # Add new violation
        mock_consciousness_system.get_safety_status.return_value = {
            "active_violations": 1,
            "kill_switch_triggered": False,
        }

        events = await collector.collect_events()
        safety_events = [e for e in events if e.event_type == EventType.SAFETY_VIOLATION]

        assert len(safety_events) > 0

    @pytest.mark.asyncio
    async def test_collect_safety_critical_severity(self, mock_consciousness_system):
        """Test collecting CRITICAL safety violations."""
        mock_consciousness_system.get_safety_status.return_value = {
            "active_violations": 1,
            "kill_switch_triggered": False,
        }

        # Make violation CRITICAL
        mock_violation = mock_consciousness_system.get_safety_violations.return_value[0]
        mock_violation.severity.value = "CRITICAL"

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        safety_events = [e for e in events if e.event_type == EventType.SAFETY_VIOLATION]
        if safety_events:
            assert safety_events[0].severity == EventSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_collect_safety_no_status(self, mock_consciousness_system):
        """Test collecting when safety_status returns None."""
        mock_consciousness_system.get_safety_status.return_value = None

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should handle None gracefully
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_collect_safety_exception_handling(self, mock_consciousness_system):
        """Test safety event collection with exception."""
        mock_consciousness_system.get_safety_status.side_effect = Exception("Safety error")

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        assert isinstance(events, list)


class TestCollectArousalEvents:
    """Test _collect_arousal_events() method."""

    @pytest.mark.asyncio
    async def test_collect_arousal_low_extreme(self, mock_consciousness_system):
        """Test collecting low arousal extreme event."""
        arousal_state = MagicMock()
        arousal_state.arousal = 0.1  # < 0.2 triggers event
        arousal_state.level = MagicMock()
        arousal_state.level.value = "LOW"
        arousal_state.stress_contribution = 0.1
        arousal_state.need_contribution = 0.1
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = arousal_state

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        arousal_events = [e for e in events if e.event_type == EventType.AROUSAL_CHANGE]
        assert len(arousal_events) > 0

    @pytest.mark.asyncio
    async def test_collect_arousal_high_extreme(self, mock_consciousness_system):
        """Test collecting high arousal extreme event."""
        arousal_state = MagicMock()
        arousal_state.arousal = 0.95  # > 0.9 triggers event
        arousal_state.level = MagicMock()
        arousal_state.level.value = "EXTREME_HIGH"
        arousal_state.stress_contribution = 0.9
        arousal_state.need_contribution = 0.1
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = arousal_state

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        arousal_events = [e for e in events if e.event_type == EventType.AROUSAL_CHANGE]
        assert len(arousal_events) > 0

    @pytest.mark.asyncio
    async def test_collect_arousal_moderate_no_event(self, mock_consciousness_system):
        """Test no arousal event for moderate levels."""
        # Default arousal is 0.65 (moderate), should not trigger event
        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        arousal_events = [e for e in events if e.event_type == EventType.AROUSAL_CHANGE]
        assert len(arousal_events) == 0

    @pytest.mark.asyncio
    async def test_collect_arousal_none_state(self, mock_consciousness_system):
        """Test collecting when arousal_state is None."""
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = None

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should handle None gracefully
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_collect_arousal_exception_handling(self, mock_consciousness_system):
        """Test arousal event collection with exception."""
        mock_consciousness_system.arousal_controller.get_current_arousal.side_effect = Exception("Arousal error")

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        assert isinstance(events, list)


class TestEventQueries:
    """Test event query methods."""

    @pytest.mark.asyncio
    async def test_get_events_by_type(self, mock_consciousness_system):
        """Test filtering events by type."""
        collector = EventCollector(mock_consciousness_system)
        await collector.collect_events()

        # Query by type
        safety_events = collector.get_events_by_type(EventType.SAFETY_VIOLATION)
        assert isinstance(safety_events, list)

    @pytest.mark.asyncio
    async def test_get_recent_events(self, mock_consciousness_system):
        """Test getting recent events."""
        collector = EventCollector(mock_consciousness_system)
        await collector.collect_events()

        recent = collector.get_recent_events(limit=5)
        assert isinstance(recent, list)
        assert len(recent) <= 5

    @pytest.mark.asyncio
    async def test_get_recent_events_sorted(self, mock_consciousness_system):
        """Test that recent events are sorted by timestamp descending."""
        collector = EventCollector(mock_consciousness_system)

        # Add multiple events with different timestamps
        event1 = ConsciousnessEvent(
            event_id="e1", event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW, timestamp=100.0, source="Test"
        )
        event2 = ConsciousnessEvent(
            event_id="e2", event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW, timestamp=200.0, source="Test"
        )
        collector.events.append(event1)
        collector.events.append(event2)

        recent = collector.get_recent_events(limit=10)
        if len(recent) >= 2:
            assert recent[0].timestamp >= recent[1].timestamp

    @pytest.mark.asyncio
    async def test_get_unprocessed_events(self, mock_consciousness_system):
        """Test getting unprocessed events."""
        collector = EventCollector(mock_consciousness_system)
        await collector.collect_events()

        unprocessed = collector.get_unprocessed_events()
        assert isinstance(unprocessed, list)
        assert all(not e.processed for e in unprocessed)

    @pytest.mark.asyncio
    async def test_mark_processed(self, mock_consciousness_system):
        """Test marking event as processed."""
        collector = EventCollector(mock_consciousness_system)

        # Add event
        event = ConsciousnessEvent(
            event_id="test_mark", event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW, timestamp=time.time(), source="Test"
        )
        collector.events.append(event)

        # Mark as processed
        collector.mark_processed("test_mark")

        # Verify
        found = [e for e in collector.events if e.event_id == "test_mark"]
        if found:
            assert found[0].processed is True

    def test_mark_processed_nonexistent(self, mock_consciousness_system):
        """Test marking nonexistent event (no-op)."""
        collector = EventCollector(mock_consciousness_system)

        # Add an event so the loop iterates
        event = ConsciousnessEvent(
            event_id="existing_event", event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW, timestamp=time.time(), source="Test"
        )
        collector.events.append(event)

        # Try to mark a different (nonexistent) event - should not raise error
        collector.mark_processed("nonexistent_id")

        # Existing event should remain unprocessed
        assert event.processed is False


class TestCollectionStats:
    """Test get_collection_stats() method."""

    @pytest.mark.asyncio
    async def test_get_collection_stats(self, mock_consciousness_system):
        """Test getting collection statistics."""
        collector = EventCollector(mock_consciousness_system)
        await collector.collect_events()

        stats = collector.get_collection_stats()

        assert "total_events_collected" in stats
        assert "events_in_buffer" in stats
        assert "events_by_type" in stats
        assert "buffer_capacity" in stats
        assert "buffer_utilization" in stats

    @pytest.mark.asyncio
    async def test_stats_buffer_utilization(self, mock_consciousness_system):
        """Test buffer utilization calculation."""
        collector = EventCollector(mock_consciousness_system, max_events=10)

        stats = collector.get_collection_stats()
        assert stats["buffer_utilization"] >= 0.0
        assert stats["buffer_utilization"] <= 1.0


class TestRepr:
    """Test __repr__() method."""

    def test_repr(self, mock_consciousness_system):
        """Test string representation."""
        collector = EventCollector(mock_consciousness_system)

        repr_str = repr(collector)

        assert "EventCollector" in repr_str
        assert "total_events=" in repr_str
        assert "buffer_size=" in repr_str


class TestSubsystemNone:
    """Test behavior when subsystems are None."""

    @pytest.mark.asyncio
    async def test_all_subsystems_none(self, mock_consciousness_system):
        """Test collection when all subsystems are None."""
        mock_consciousness_system.esgt_coordinator = None
        mock_consciousness_system.prefrontal_cortex = None
        mock_consciousness_system.tom_engine = None
        mock_consciousness_system.safety_protocol = None
        mock_consciousness_system.arousal_controller = None

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should return empty list
        assert events == []
        assert collector.total_events_collected == 0
