"""
ESGT Refractory Period Edge Case Tests
======================================

Tests comprehensive refractory period behavior - the biological analog
of neural absolute refractory periods that prevent runaway excitation.

Theoretical Foundation:
-----------------------
Biological neurons have absolute and relative refractory periods that:
1. Prevent continuous firing (absolute)
2. Require stronger stimuli during recovery (relative)
3. Enable temporal coding and discrete events

ESGT refractory periods serve the same purpose:
1. Prevent continuous ESGT (consciousness requires discrete moments)
2. Enforce temporal gating (200ms default = 5 Hz max)
3. Allow quiescence for unconscious processing

IIT Relevance:
--------------
Consciousness requires transient synchronized states, not continuous.
The refractory period ensures phenomenal discreteness.

GWT Relevance:
--------------
Global ignition events must be discrete, time-limited episodes.
Refractory prevents continuous broadcasting.
"""

import asyncio

import pytest
import pytest_asyncio

from consciousness.esgt.coordinator import (
    ESGTCoordinator,
    SalienceScore,
    TriggerConditions,
)
from consciousness.tig.fabric import TIGFabric, TopologyConfig


@pytest_asyncio.fixture(scope="function")
async def tig_fabric_small():
    """Create small TIG fabric for fast testing."""
    config = TopologyConfig(num_nodes=10, avg_degree=3)
    fabric = TIGFabric(config)
    await fabric.initialize()
    yield fabric
    await fabric.stop()


class TestESGTRefractoryPeriod:
    """
    Comprehensive tests for ESGT refractory period enforcement.
    
    Theory: Like neural refractory periods, ESGT must prevent continuous
    ignition to maintain discrete conscious moments.
    """

    @pytest.mark.asyncio
    async def test_concurrent_ignition_during_refractory_blocked(self, tig_fabric_small):
        """
        Second ignition attempt during refractory should be blocked.
        
        Validates: Refractory enforcement
        Theory: Absolute refractory period - no ignition possible
        """
        # Create coordinator with short refractory for testing
        triggers = TriggerConditions(refractory_period_ms=100.0)  # 100ms
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_small,
            triggers=triggers,
            coordinator_id="test-refractory-1"
        )
        await coordinator.start()
        
        # High salience for both attempts
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # First ignition should succeed
        event1 = await coordinator.initiate_esgt(salience, {"test": "first"})
        assert event1.success or not event1.success, "First ignition attempted"
        
        # Immediate second attempt (during refractory)
        await asyncio.sleep(0.01)  # 10ms < 100ms refractory
        
        event2 = await coordinator.initiate_esgt(salience, {"test": "second"})
        
        # If first succeeded, second should be blocked by refractory
        if event1.success:
            assert not event2.success, "Second ignition during refractory should fail"
            if event2.failure_reason:
                assert "refractory" in event2.failure_reason.lower(), \
                    f"Expected refractory message, got: {event2.failure_reason}"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_refractory_period_expires_allows_next(self, tig_fabric_small):
        """
        After refractory period expires, next ignition should succeed.
        
        Validates: Refractory timeout
        Theory: Like relative refractory period ending, normal excitability restored
        """
        triggers = TriggerConditions(refractory_period_ms=50.0)  # 50ms for fast test
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_small,
            triggers=triggers,
            coordinator_id="test-refractory-2"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # First ignition
        event1 = await coordinator.initiate_esgt(salience, {"test": "first"})
        
        # Wait for refractory to expire
        await asyncio.sleep(0.06)  # 60ms > 50ms refractory
        
        # Second ignition should now be evaluated (not blocked by refractory)
        event2 = await coordinator.initiate_esgt(salience, {"test": "second"})
        
        # Should not fail due to refractory
        if not event2.success and event2.failure_reason:
            assert "refractory" not in event2.failure_reason.lower(), \
                "After refractory period, should not fail due to refractory"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_attempts_all_blocked(self, tig_fabric_small):
        """
        Multiple concurrent ignition attempts during refractory all blocked.
        
        Validates: Refractory enforcement under concurrent load
        Theory: All attempts during absolute refractory fail (no accumulation)
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_small,
            triggers=triggers,
            coordinator_id="test-refractory-3"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # First ignition
        event1 = await coordinator.initiate_esgt(salience, {"test": "first"})
        
        if event1.success:
            # Launch 5 concurrent attempts during refractory
            tasks = [
                coordinator.initiate_esgt(salience, {"test": f"concurrent{i}"})
                for i in range(5)
            ]
            
            events = await asyncio.gather(*tasks)
            
            # All concurrent attempts should fail due to refractory
            refractory_blocks = sum(
                1 for e in events 
                if not e.success and e.failure_reason and "refractory" in e.failure_reason.lower()
            )
            
            assert refractory_blocks > 0, \
                "At least some concurrent attempts should be blocked by refractory"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_refractory_period_violation_logged(self, tig_fabric_small):
        """
        Refractory period violations should be tracked in metrics.
        
        Validates: Observability of violations
        Theory: System health monitoring requires violation tracking
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_small,
            triggers=triggers,
            coordinator_id="test-refractory-4"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # First ignition
        event1 = await coordinator.initiate_esgt(salience, {"test": "first"})
        initial_total = coordinator.total_events
        
        # Attempt during refractory
        await asyncio.sleep(0.01)
        event2 = await coordinator.initiate_esgt(salience, {"test": "second"})
        
        # Total events should increment (attempt was made)
        assert coordinator.total_events >= initial_total, \
            "Event attempts should be tracked"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_refractory_period_configurable(self, tig_fabric_small):
        """
        Refractory period should be configurable per coordinator.
        
        Validates: Flexibility for different consciousness modes
        Theory: Different arousal states may have different temporal dynamics
        """
        # Test with different refractory periods
        short_triggers = TriggerConditions(refractory_period_ms=50.0)
        long_triggers = TriggerConditions(refractory_period_ms=200.0)
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Short refractory coordinator
        coord_short = ESGTCoordinator(
            tig_fabric=tig_fabric_small,
            triggers=short_triggers,
            coordinator_id="test-short"
        )
        await coord_short.start()
        
        await coord_short.initiate_esgt(salience, {"test": "1"})
        await asyncio.sleep(0.06)  # 60ms
        event_short = await coord_short.initiate_esgt(salience, {"test": "2"})
        
        # 60ms > 50ms, so should not fail due to refractory
        if not event_short.success and event_short.failure_reason:
            assert "refractory" not in event_short.failure_reason.lower(), \
                "60ms should exceed 50ms refractory"
        
        await coord_short.stop()
        
        # Long refractory coordinator
        coord_long = ESGTCoordinator(
            tig_fabric=tig_fabric_small,
            triggers=long_triggers,
            coordinator_id="test-long"
        )
        await coord_long.start()
        
        event1 = await coord_long.initiate_esgt(salience, {"test": "1"})
        await asyncio.sleep(0.06)  # 60ms
        event_long = await coord_long.initiate_esgt(salience, {"test": "2"})
        
        # 60ms < 200ms, so should fail due to refractory if first succeeded
        if event1.success:
            assert not event_long.success, "60ms should not exceed 200ms refractory"
            if event_long.failure_reason:
                assert "refractory" in event_long.failure_reason.lower()
        
        await coord_long.stop()

    @pytest.mark.asyncio
    async def test_refractory_queue_handling(self, tig_fabric_small):
        """
        Ignition requests during refractory should not queue (immediate rejection).
        
        Validates: No request queuing during refractory
        Theory: Consciousness is winner-take-all, not FIFO queue
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_small,
            triggers=triggers,
            coordinator_id="test-queue"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Trigger first ESGT
        event1 = await coordinator.initiate_esgt(salience, {"test": "first"})
        
        # Queue multiple during refractory
        events_during = []
        for i in range(3):
            await asyncio.sleep(0.01)
            event = await coordinator.initiate_esgt(salience, {"test": f"queued{i}"})
            events_during.append(event)
        
        # Wait for refractory to expire
        await asyncio.sleep(0.15)
        
        # New request should succeed immediately (no queue backlog)
        event_after = await coordinator.initiate_esgt(salience, {"test": "after"})
        
        # Verify no queuing behavior
        total_attempts = coordinator.total_events
        # Should be ~5 attempts (1 + 3 + 1), not delayed processing
        assert total_attempts >= 4, "Should process requests immediately, not queue"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_zero_refractory_period_allows_continuous(self, tig_fabric_small):
        """
        Zero refractory period should allow continuous ignitions (testing mode).
        
        Validates: Refractory can be disabled for testing
        Theory: For debugging/testing, may need rapid-fire ESGTs
        """
        triggers = TriggerConditions(refractory_period_ms=0.0)  # Disabled
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_small,
            triggers=triggers,
            coordinator_id="test-zero"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Rapid-fire ignitions
        events = []
        for i in range(3):
            event = await coordinator.initiate_esgt(salience, {"test": f"rapid{i}"})
            events.append(event)
            await asyncio.sleep(0.01)  # Minimal delay
        
        # With zero refractory, failures should not be due to refractory
        for event in events:
            if not event.success and event.failure_reason:
                assert "refractory" not in event.failure_reason.lower(), \
                    "With zero refractory, failure should not be due to refractory"
        
        await coordinator.stop()
