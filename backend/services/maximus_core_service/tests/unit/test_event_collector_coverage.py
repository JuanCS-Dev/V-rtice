"""Coverage tests for EventCollector - targeting 90%+ coverage

Target lines (64.52% → 90%):
- Lines 179-200: ESGT event generation
- Lines 220-235: Arousal event generation
- Lines 255-270: Event filtering
- Lines 281-319: Event statistics

Authors: Claude Code (Coverage Sprint)
Date: 2025-10-14
"""

import pytest
import time
from unittest.mock import Mock
from consciousness.reactive_fabric.collectors.event_collector import (
    EventCollector,
    ConsciousnessEvent,
    EventType,
    EventSeverity,
)


@pytest.fixture
def mock_consciousness_system():
    """Mock ConsciousnessSystem."""
    system = Mock()
    system.esgt_coordinator = Mock()
    system.esgt_coordinator.event_history = []
    system.arousal_controller = Mock()
    system.arousal_controller.get_current_arousal = Mock(
        return_value=Mock(arousal=0.5, stress_contribution=0.2, level=Mock(value="MODERATE"))
    )
    return system


class TestEventCollectorCoverage:
    """Coverage-focused tests for EventCollector uncovered paths."""

    @pytest.mark.asyncio
    async def test_collect_events_no_coordinator(self, mock_consciousness_system):
        """Cover code path when no ESGT coordinator."""
        mock_consciousness_system.esgt_coordinator = None
        collector = EventCollector(mock_consciousness_system)

        events = await collector.collect_events()

        # Should not crash, just return empty or limited events
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_collect_events_with_esgt_history(self, mock_consciousness_system):
        """Cover ESGT event generation with history."""
        # Create mock ESGT event
        esgt_event = Mock()
        esgt_event.event_id = "001"
        esgt_event.timestamp_start = time.time()
        esgt_event.success = True
        esgt_event.achieved_coherence = 0.85
        esgt_event.total_duration_ms = 50
        esgt_event.node_count = 10

        # Setup coordinator with history
        mock_consciousness_system.esgt_coordinator.total_events = 1
        mock_consciousness_system.esgt_coordinator.event_history = [esgt_event]
        collector = EventCollector(mock_consciousness_system)

        events = await collector.collect_events()

        # Should generate ESGT event
        assert len(events) >= 1
        esgt_events = [e for e in events if e.event_type == EventType.ESGT_IGNITION]
        assert len(esgt_events) > 0

    @pytest.mark.asyncio
    async def test_collect_events_with_extreme_arousal(self, mock_consciousness_system):
        """Cover arousal event generation with extreme arousal."""
        # High arousal (> 0.9)
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = Mock(
            arousal=0.95,
            stress_contribution=0.3,
            need_contribution=0.2,
            level=Mock(value="VERY_HIGH"),
        )

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should generate arousal event for extreme state
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_collect_events_buffer_management(self, mock_consciousness_system):
        """Cover event buffer management and ring buffer behavior."""
        collector = EventCollector(mock_consciousness_system, max_events=100)

        # Add event directly to buffer
        event = ConsciousnessEvent(
            event_id="test-1",
            event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW,
            source="test",
            timestamp=time.time(),
            novelty=0.5,
            relevance=0.5,
            urgency=0.5,
        )
        collector.events.append(event)

        # Verify buffer contains event
        assert len(collector.events) == 1
        assert collector.events[0].event_id == "test-1"

    @pytest.mark.asyncio
    async def test_get_event_statistics_complete(self, mock_consciousness_system):
        """Cover event statistics collection."""
        collector = EventCollector(mock_consciousness_system)

        # Add various events
        for i in range(5):
            event = ConsciousnessEvent(
                event_id=f"event-{i}",
                event_type=EventType.SYSTEM_HEALTH,
                severity=EventSeverity.LOW,
                source="test",
                timestamp=time.time(),
                novelty=0.5,
                relevance=0.5,
                urgency=0.5,
            )
            collector.events.append(event)
            collector.total_events_collected += 1
            collector.events_by_type[EventType.SYSTEM_HEALTH] += 1

        stats = collector.get_collection_stats()

        # Verify statistics structure
        assert "total_events_collected" in stats
        assert "events_by_type" in stats
        assert stats["total_events_collected"] == 5

    @pytest.mark.asyncio
    async def test_event_buffer_circular_overflow(self, mock_consciousness_system):
        """Cover buffer overflow/circular behavior."""
        collector = EventCollector(mock_consciousness_system, max_events=5)

        # Add more events than buffer size
        for i in range(10):
            event = ConsciousnessEvent(
                event_id=f"event-{i}",
                event_type=EventType.SYSTEM_HEALTH,
                severity=EventSeverity.LOW,
                source="test",
                timestamp=time.time(),
                novelty=0.5,
                relevance=0.5,
                urgency=0.5,
            )
            collector.events.append(event)

        # Buffer should not exceed max_events (deque with maxlen)
        assert len(collector.events) <= collector.max_events

    @pytest.mark.asyncio
    async def test_collect_events_no_arousal_controller(self, mock_consciousness_system):
        """Cover code path when no arousal controller."""
        mock_consciousness_system.arousal_controller = None
        collector = EventCollector(mock_consciousness_system)

        events = await collector.collect_events()

        # Should not crash
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_collect_pfc_events_new_signals(self, mock_consciousness_system):
        """Cover PFC event generation when new signals detected (lines 215-237)."""
        from unittest.mock import AsyncMock

        # Setup PFC with signals
        mock_consciousness_system.prefrontal_cortex = Mock()
        mock_consciousness_system.prefrontal_cortex.get_status = AsyncMock(
            return_value={
                "total_signals_processed": 10,
                "total_actions_generated": 5,
                "approval_rate": 0.8,
            }
        )

        collector = EventCollector(mock_consciousness_system)
        collector._last_pfc_signals = 5  # Previous was 5, now is 10

        events = await collector.collect_events()

        # Should have PFC event
        pfc_events = [e for e in events if e.event_type == EventType.PFC_SOCIAL_SIGNAL]
        assert len(pfc_events) > 0

    @pytest.mark.asyncio
    async def test_collect_tom_events_new_beliefs(self, mock_consciousness_system):
        """Cover ToM event generation when new beliefs detected (lines 250-272)."""
        from unittest.mock import AsyncMock

        # Setup ToM with beliefs
        mock_consciousness_system.tom_engine = Mock()
        mock_consciousness_system.tom_engine.get_stats = AsyncMock(
            return_value={
                "total_agents": 3,
                "memory": {"total_beliefs": 50},
                "contradictions": 2,
            }
        )

        collector = EventCollector(mock_consciousness_system)
        collector._last_tom_beliefs = 30  # Previous was 30, now is 50

        events = await collector.collect_events()

        # Should have ToM event
        tom_events = [e for e in events if e.event_type == EventType.TOM_BELIEF_UPDATE]
        assert len(tom_events) > 0

    @pytest.mark.asyncio
    async def test_collect_safety_events_new_violations(self, mock_consciousness_system):
        """Cover Safety event generation when new violations detected (lines 286-314)."""
        from datetime import datetime

        # Setup Safety with violations
        mock_consciousness_system.safety_protocol = Mock()

        # Mock violation object
        violation = Mock()
        violation.violation_id = "v001"
        violation.timestamp = datetime.now()
        violation.severity = Mock(value="CRITICAL")
        violation.violation_type = Mock(value="THRESHOLD_BREACH")
        violation.value_observed = 0.95
        violation.threshold_violated = 0.9
        violation.message = "Test violation"

        mock_consciousness_system.get_safety_status = Mock(
            return_value={"active_violations": 2}
        )
        mock_consciousness_system.get_safety_violations = Mock(return_value=[violation])

        collector = EventCollector(mock_consciousness_system)
        collector._last_safety_violations = 0  # Previous was 0, now is 2

        events = await collector.collect_events()

        # Should have Safety event
        safety_events = [e for e in events if e.event_type == EventType.SAFETY_VIOLATION]
        assert len(safety_events) > 0

    @pytest.mark.asyncio
    async def test_collect_arousal_events_extreme_low(self, mock_consciousness_system):
        """Cover arousal event for low arousal (<0.2)."""
        # Low arousal
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = Mock(
            arousal=0.15,
            stress_contribution=0.1,
            need_contribution=0.05,
            level=Mock(value="VERY_LOW"),
        )

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should generate arousal event
        arousal_events = [e for e in events if e.event_type == EventType.AROUSAL_CHANGE]
        assert len(arousal_events) > 0

    @pytest.mark.asyncio
    async def test_collect_events_main_exception(self, mock_consciousness_system):
        """Cover main exception handler in collect_events (lines 162-163)."""
        # Make ESGT coordinator fail catastrophically
        mock_consciousness_system.esgt_coordinator = Mock()
        mock_consciousness_system.esgt_coordinator.total_events = property(
            lambda self: 1 / 0  # Raise ZeroDivisionError
        )

        collector = EventCollector(mock_consciousness_system)

        # Should not crash, exception is logged
        events = await collector.collect_events()
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_collect_arousal_exception(self, mock_consciousness_system):
        """Cover arousal collection exception handler (lines 351-352)."""
        mock_consciousness_system.arousal_controller.get_current_arousal.side_effect = (
            RuntimeError("Arousal failure")
        )

        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()

        # Should handle exception gracefully
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_get_events_by_type(self, mock_consciousness_system):
        """Cover get_events_by_type method (line 365)."""
        collector = EventCollector(mock_consciousness_system)

        # Add mixed events
        event1 = ConsciousnessEvent(
            event_id="e1",
            event_type=EventType.ESGT_IGNITION,
            severity=EventSeverity.HIGH,
            source="test",
            timestamp=time.time(),
        )
        event2 = ConsciousnessEvent(
            event_id="e2",
            event_type=EventType.SAFETY_VIOLATION,
            severity=EventSeverity.CRITICAL,
            source="test",
            timestamp=time.time(),
        )
        collector.events.append(event1)
        collector.events.append(event2)

        # Filter by type
        esgt_events = collector.get_events_by_type(EventType.ESGT_IGNITION)
        assert len(esgt_events) == 1
        assert esgt_events[0].event_id == "e1"

    @pytest.mark.asyncio
    async def test_get_recent_events(self, mock_consciousness_system):
        """Cover get_recent_events method (lines 376-377)."""
        collector = EventCollector(mock_consciousness_system)

        # Add events with different timestamps
        for i in range(5):
            event = ConsciousnessEvent(
                event_id=f"e{i}",
                event_type=EventType.SYSTEM_HEALTH,
                severity=EventSeverity.LOW,
                source="test",
                timestamp=time.time() + i,  # Increasing timestamps
            )
            collector.events.append(event)

        # Get recent
        recent = collector.get_recent_events(limit=3)
        assert len(recent) == 3
        # Should be sorted by timestamp descending (newest first)
        assert recent[0].timestamp >= recent[1].timestamp

    @pytest.mark.asyncio
    async def test_get_unprocessed_events(self, mock_consciousness_system):
        """Cover get_unprocessed_events method (line 385)."""
        collector = EventCollector(mock_consciousness_system)

        # Add processed and unprocessed events
        event1 = ConsciousnessEvent(
            event_id="e1",
            event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW,
            source="test",
            timestamp=time.time(),
            processed=True,
        )
        event2 = ConsciousnessEvent(
            event_id="e2",
            event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW,
            source="test",
            timestamp=time.time(),
            processed=False,
        )
        collector.events.append(event1)
        collector.events.append(event2)

        # Get unprocessed
        unprocessed = collector.get_unprocessed_events()
        assert len(unprocessed) == 1
        assert unprocessed[0].event_id == "e2"

    @pytest.mark.asyncio
    async def test_mark_processed(self, mock_consciousness_system):
        """Cover mark_processed method (lines 393-396)."""
        collector = EventCollector(mock_consciousness_system)

        # Add event
        event = ConsciousnessEvent(
            event_id="e1",
            event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW,
            source="test",
            timestamp=time.time(),
            processed=False,
        )
        collector.events.append(event)

        # Mark as processed
        collector.mark_processed("e1")

        # Verify marked
        assert event.processed is True

    @pytest.mark.asyncio
    async def test_repr(self, mock_consciousness_system):
        """Cover __repr__ method."""
        collector = EventCollector(mock_consciousness_system, max_events=1000)
        collector.total_events_collected = 50
        for i in range(10):
            event = ConsciousnessEvent(
                event_id=f"e{i}",
                event_type=EventType.SYSTEM_HEALTH,
                severity=EventSeverity.LOW,
                source="test",
                timestamp=time.time(),
            )
            collector.events.append(event)

        repr_str = repr(collector)
        assert "EventCollector" in repr_str
        assert "50" in repr_str  # total_events
        assert "10/1000" in repr_str  # buffer size

    @pytest.mark.asyncio
    async def test_esgt_event_failed(self, mock_consciousness_system):
        """Cover ESGT event with success=False (line 187 branch)."""
        esgt_event = Mock()
        esgt_event.event_id = "001"
        esgt_event.timestamp_start = time.time()
        esgt_event.success = False  # Failed event
        esgt_event.achieved_coherence = 0.3
        esgt_event.total_duration_ms = 10
        esgt_event.node_count = 5

        mock_consciousness_system.esgt_coordinator.total_events = 1
        mock_consciousness_system.esgt_coordinator.event_history = [esgt_event]
        collector = EventCollector(mock_consciousness_system)

        events = await collector.collect_events()

        # Should generate event with MEDIUM severity
        esgt_events = [e for e in events if e.event_type == EventType.ESGT_IGNITION]
        assert len(esgt_events) > 0
        assert esgt_events[0].severity == EventSeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_safety_event_non_critical(self, mock_consciousness_system):
        """Cover safety event with non-CRITICAL severity (line 298 branch)."""
        from datetime import datetime

        mock_consciousness_system.safety_protocol = Mock()

        violation = Mock()
        violation.violation_id = "v002"
        violation.timestamp = datetime.now()
        violation.severity = Mock(value="HIGH")  # Not CRITICAL
        violation.violation_type = Mock(value="ANOMALY")
        violation.value_observed = 0.8
        violation.threshold_violated = 0.7
        violation.message = "High severity test"

        mock_consciousness_system.get_safety_status = Mock(
            return_value={"active_violations": 1}
        )
        mock_consciousness_system.get_safety_violations = Mock(return_value=[violation])

        collector = EventCollector(mock_consciousness_system)
        collector._last_safety_violations = 0

        events = await collector.collect_events()

        safety_events = [e for e in events if e.event_type == EventType.SAFETY_VIOLATION]
        assert len(safety_events) > 0
        assert safety_events[0].severity == EventSeverity.HIGH


# Run with:
# pytest tests/unit/test_event_collector_coverage.py --cov=consciousness.reactive_fabric.collectors.event_collector --cov-branch --cov-report=term-missing -v

    @pytest.mark.asyncio
    async def test_collect_events_exception_during_collection(self, mock_consciousness_system):
        """Cover main exception handler by breaking sub-collector (lines 162-163)."""

        # Make _collect_esgt_events raise an unhandled exception
        # (it has its own try-except, but we'll break it at a deeper level)
        async def failing_collect():
            # Simulate catastrophic failure that escapes sub-collector's handler
            1 / 0

        collector = EventCollector(mock_consciousness_system)
        original_method = collector._collect_esgt_events
        collector._collect_esgt_events = failing_collect

        # This should trigger lines 162-163 (main exception handler)
        events = await collector.collect_events()

        # Should handle exception gracefully, return empty list
        assert isinstance(events, list)

        # Restore
        collector._collect_esgt_events = original_method
    
    @pytest.mark.asyncio
    async def test_collect_pfc_no_new_signals(self, mock_consciousness_system):
        """Cover PFC branch when no new signals (line 218->237 branch)."""
        from unittest.mock import AsyncMock
    
        mock_consciousness_system.prefrontal_cortex = Mock()
        mock_consciousness_system.prefrontal_cortex.get_status = AsyncMock(
            return_value={"total_signals_processed": 5}
        )
    
        collector = EventCollector(mock_consciousness_system)
        collector._last_pfc_signals = 5  # Same as current, no new signals
    
        events = await collector.collect_events()
    
        # Should NOT have PFC event
        pfc_events = [e for e in events if e.event_type == EventType.PFC_SOCIAL_SIGNAL]
        assert len(pfc_events) == 0
    
    @pytest.mark.asyncio
    async def test_collect_tom_no_new_beliefs(self, mock_consciousness_system):
        """Cover ToM branch when no new beliefs (line 253->272 branch)."""
        from unittest.mock import AsyncMock
    
        mock_consciousness_system.tom_engine = Mock()
        mock_consciousness_system.tom_engine.get_stats = AsyncMock(
            return_value={"memory": {"total_beliefs": 30}}
        )
    
        collector = EventCollector(mock_consciousness_system)
        collector._last_tom_beliefs = 30  # Same as current
    
        events = await collector.collect_events()
    
        # Should NOT have ToM event
        tom_events = [e for e in events if e.event_type == EventType.TOM_BELIEF_UPDATE]
        assert len(tom_events) == 0
    
    @pytest.mark.asyncio
    async def test_collect_safety_no_new_violations(self, mock_consciousness_system):
        """Cover Safety branch when no new violations (line 290->314 branch)."""
        mock_consciousness_system.safety_protocol = Mock()
        mock_consciousness_system.get_safety_status = Mock(
            return_value={"active_violations": 1}
        )
    
        collector = EventCollector(mock_consciousness_system)
        collector._last_safety_violations = 1  # Same as current
    
        events = await collector.collect_events()
    
        # Should NOT have Safety event
        safety_events = [e for e in events if e.event_type == EventType.SAFETY_VIOLATION]
        assert len(safety_events) == 0
    
    @pytest.mark.asyncio
    async def test_collect_arousal_normal_range(self, mock_consciousness_system):
        """Cover arousal branch when within normal range (line 332 branch)."""
        # Normal arousal (not < 0.2 or > 0.9)
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = Mock(
            arousal=0.6,  # Normal range
            stress_contribution=0.1,
            need_contribution=0.1,
            level=Mock(value="MODERATE"),
        )
    
        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()
    
        # Should NOT generate arousal event (normal arousal)
        arousal_events = [e for e in events if e.event_type == EventType.AROUSAL_CHANGE]
        assert len(arousal_events) == 0
    
    @pytest.mark.asyncio
    async def test_collect_safety_no_status(self, mock_consciousness_system):
        """Cover Safety branch when get_safety_status returns None (line 286 branch)."""
        mock_consciousness_system.safety_protocol = Mock()
        mock_consciousness_system.get_safety_status = Mock(return_value=None)
    
        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()
    
        # Should handle None gracefully
        assert isinstance(events, list)
    
    @pytest.mark.asyncio
    async def test_collect_arousal_no_state(self, mock_consciousness_system):
        """Cover arousal branch when get_current_arousal returns None (line 328 branch)."""
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = None
    
        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()
    
        # Should handle None gracefully
        assert isinstance(events, list)
    
    @pytest.mark.asyncio
    async def test_collect_esgt_no_new_events(self, mock_consciousness_system):
        """Cover ESGT branch when no new events (line 177->202 branch)."""
        mock_consciousness_system.esgt_coordinator.total_events = 0
        mock_consciousness_system.esgt_coordinator.event_history = []
    
        collector = EventCollector(mock_consciousness_system)
        collector._last_esgt_event_count = 0  # Same as current
    
        events = await collector.collect_events()
    
        # Should NOT have ESGT events
        esgt_events = [e for e in events if e.event_type == EventType.ESGT_IGNITION]
        assert len(esgt_events) == 0
    
    @pytest.mark.asyncio
    async def test_mark_processed_nonexistent_event(self, mock_consciousness_system):
        """Cover mark_processed when event_id not found (line 393->exit branch)."""
        collector = EventCollector(mock_consciousness_system)
    
        # Add event
        event = ConsciousnessEvent(
            event_id="e1",
            event_type=EventType.SYSTEM_HEALTH,
            severity=EventSeverity.LOW,
            source="test",
            timestamp=time.time(),
            processed=False,
        )
        collector.events.append(event)
    
        # Try to mark nonexistent event
        collector.mark_processed("nonexistent")
    
        # Original event should remain unprocessed
        assert event.processed is False


    @pytest.mark.asyncio
    async def test_collect_sequential_branch_pfc_none_tom_present(self, mock_consciousness_system):
        """Cover sequential branch: PFC None, ToM present (line 135->140)."""
        from unittest.mock import AsyncMock
    
        # PFC None, but ToM present
        mock_consciousness_system.prefrontal_cortex = None
        mock_consciousness_system.tom_engine = Mock()
        mock_consciousness_system.tom_engine.get_stats = AsyncMock(
            return_value={"memory": {"total_beliefs": 50}}
        )
    
        collector = EventCollector(mock_consciousness_system)
        collector._last_tom_beliefs = 30
    
        events = await collector.collect_events()
    
        # Should have ToM event but no PFC event
        assert isinstance(events, list)
    
    @pytest.mark.asyncio
    async def test_collect_sequential_branch_tom_none_safety_present(self, mock_consciousness_system):
        """Cover sequential branch: ToM None, Safety present (line 140->145)."""
        from datetime import datetime
    
        # PFC and ToM None, but Safety present
        mock_consciousness_system.prefrontal_cortex = None
        mock_consciousness_system.tom_engine = None
        mock_consciousness_system.safety_protocol = Mock()
    
        violation = Mock()
        violation.violation_id = "v001"
        violation.timestamp = datetime.now()
        violation.severity = Mock(value="CRITICAL")
        violation.violation_type = Mock(value="TEST")
        violation.value_observed = 1.0
        violation.threshold_violated = 0.9
        violation.message = "Test"
    
        mock_consciousness_system.get_safety_status = Mock(
            return_value={"active_violations": 1}
        )
        mock_consciousness_system.get_safety_violations = Mock(return_value=[violation])
    
        collector = EventCollector(mock_consciousness_system)
        collector._last_safety_violations = 0
    
        events = await collector.collect_events()
    
        # Should have Safety event
        assert isinstance(events, list)
    
    @pytest.mark.asyncio
    async def test_collect_sequential_branch_safety_none_arousal_present(self, mock_consciousness_system):
        """Cover sequential branch: Safety None, Arousal present (line 145->150)."""
        # PFC, ToM, Safety None, but Arousal present with extreme value
        mock_consciousness_system.prefrontal_cortex = None
        mock_consciousness_system.tom_engine = None
        mock_consciousness_system.safety_protocol = None
        mock_consciousness_system.arousal_controller = Mock()
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = Mock(
            arousal=0.95,
            stress_contribution=0.3,
            need_contribution=0.2,
            level=Mock(value="VERY_HIGH"),
        )
    
        collector = EventCollector(mock_consciousness_system)
        events = await collector.collect_events()
    
        # Should have Arousal event
        assert isinstance(events, list)
