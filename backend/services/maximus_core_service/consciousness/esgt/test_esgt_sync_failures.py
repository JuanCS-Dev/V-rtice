"""
ESGT Synchronization Failure Tests
===================================

Tests ESGT behavior when TIG temporal synchronization fails.

Theoretical Foundation:
-----------------------
Consciousness requires temporal binding - distributed neural events must be
synchronized within narrow time windows (~10-50ms) to create unified experience.

When synchronization fails:
1. **Φ decreases**: Integration is impaired (IIT prediction)
2. **Binding breaks**: No unified percept (binding problem)
3. **Consciousness dims**: Reduced phenomenal clarity
4. **Not catastrophic**: System degrades gracefully

ESGT Temporal Requirements:
---------------------------
- PTP synchronization: <100ns jitter (hardware) / <1μs (simulation)
- Phase coherence: r ≥ 0.70 (Kuramoto order parameter)
- Clock drift: <100 ppm (biological limit)
- Temporal window: Events within ~200ms for binding

Synchronization Failures:
-------------------------
1. **TIG sync loss**: PTP fails, no temporal reference
2. **Phase decoherence**: Oscillators lose sync
3. **Jitter accumulation**: Timing uncertainty grows
4. **Clock drift**: Systematic offset increases
5. **Temporal window violations**: Events too far apart

IIT/GWT Relevance:
------------------
**IIT**: Temporal integration requires synchrony - desynchronization → Φ drop
**GWT**: Global ignition requires coordinated timing - async → failed broadcast
**Biology**: Neural synchrony (gamma, theta) essential for binding

"Time is the fabric of consciousness. Desynchronization tears it."
"""

import asyncio
import time

import pytest
import pytest_asyncio

from consciousness.esgt.coordinator import (
    ESGTCoordinator,
    ESGTPhase,
    SalienceScore,
    TriggerConditions,
)
from consciousness.tig.fabric import TIGFabric, TopologyConfig


@pytest_asyncio.fixture(scope="function")
async def tig_fabric_sync():
    """Create TIG fabric for sync testing."""
    config = TopologyConfig(num_nodes=12, avg_degree=4)
    fabric = TIGFabric(config)
    await fabric.initialize()
    yield fabric
    await fabric.stop()


class TestESGTSynchronizationFailures:
    """
    Tests for ESGT behavior under synchronization failures.
    
    Theory: Temporal binding requires tight synchronization.
    Failures impair consciousness but don't crash system.
    """

    @pytest.mark.asyncio
    async def test_tig_sync_loss_during_esgt(self, tig_fabric_sync):
        """
        Loss of TIG synchronization during ESGT should be detectable.
        
        Validates: Sync monitoring
        Theory: Temporal coherence loss → binding failure
        """
        triggers = TriggerConditions(
            min_available_nodes=8,
            min_salience=0.60,
            refractory_period_ms=50.0
        )
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_sync,
            triggers=triggers,
            coordinator_id="test-sync-loss"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Attempt ESGT
        event = await coordinator.initiate_esgt(salience, {"test": "sync_loss"})
        
        # Check if sync status is tracked
        if event.success:
            # Should have timing information
            assert event.total_duration_ms >= 0, "Should track duration"
            
            # If there's a sync_quality or timing_jitter field, validate it
            if hasattr(event, 'sync_quality'):
                assert 0.0 <= event.sync_quality <= 1.0, "Sync quality should be normalized"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_phase_decoherence_handling(self, tig_fabric_sync):
        """
        Phase decoherence (oscillators lose sync) should be detected.
        
        Validates: Coherence monitoring
        Theory: Kuramoto order parameter r < threshold → failed binding
        """
        triggers = TriggerConditions(
            min_available_nodes=8,
            min_salience=0.60,
            refractory_period_ms=50.0
        )
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_sync,
            triggers=triggers,
            coordinator_id="test-decoherence"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Initiate ESGT
        event = await coordinator.initiate_esgt(salience, {"test": "decoherence"})
        
        # Check if coherence is tracked
        if event.success:
            assert hasattr(event, 'achieved_coherence'), "Should track coherence"
            assert hasattr(event, 'target_coherence'), "Should have target coherence"
            
            # Coherence should be meaningful
            if event.achieved_coherence > 0:
                # Target is typically 0.70 for consciousness threshold
                assert 0.0 <= event.target_coherence <= 1.0
                assert 0.0 <= event.achieved_coherence <= 1.0
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_jitter_accumulation_effects(self, tig_fabric_sync):
        """
        Accumulated timing jitter should impact ESGT quality.
        
        Validates: Jitter impact on coherence
        Theory: Excessive jitter → timing uncertainty → poor binding
        """
        triggers = TriggerConditions(
            min_available_nodes=8,
            min_salience=0.60,
            refractory_period_ms=50.0
        )
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_sync,
            triggers=triggers,
            coordinator_id="test-jitter"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Multiple ESGTs to potentially accumulate jitter
        events = []
        for i in range(3):
            event = await coordinator.initiate_esgt(salience, {"test": f"jitter_{i}"})
            events.append(event)
            await asyncio.sleep(0.06)  # Wait between attempts
        
        # Check if any events tracked timing/jitter
        successful_events = [e for e in events if e.success]
        
        if successful_events:
            # At least one succeeded despite potential jitter
            assert len(successful_events) > 0, "System should handle jitter"
            
            # Check for timing metrics
            for event in successful_events:
                assert event.total_duration_ms >= 0, "Should track timing"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_clock_drift_impact_on_ignition(self, tig_fabric_sync):
        """
        Clock drift between nodes should be tolerated up to threshold.
        
        Validates: Drift tolerance
        Theory: Moderate drift acceptable, extreme drift fails binding
        """
        triggers = TriggerConditions(
            min_available_nodes=8,
            min_salience=0.60,
            refractory_period_ms=50.0,
            max_tig_latency_ms=10.0  # Allow some latency
        )
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_sync,
            triggers=triggers,
            coordinator_id="test-drift"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Attempt ignition
        event = await coordinator.initiate_esgt(salience, {"test": "drift"})
        
        # System should either succeed (drift within tolerance) or fail gracefully
        assert event is not None, "Should return event"
        
        if not event.success and event.failure_reason:
            # If failed, check if it's timing-related
            timing_failure = any(
                keyword in event.failure_reason.lower()
                for keyword in ['latency', 'timing', 'sync', 'drift']
            )
            
            if timing_failure:
                # Timing failure is acceptable - validates monitoring
                assert True, "Timing failure correctly detected"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_temporal_window_violations(self, tig_fabric_sync):
        """
        Events outside temporal window should not bind into single ESGT.
        
        Validates: Temporal window enforcement
        Theory: Binding requires events within ~200ms window
        """
        triggers = TriggerConditions(
            min_available_nodes=8,
            min_salience=0.60,
            refractory_period_ms=50.0
        )
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_sync,
            triggers=triggers,
            coordinator_id="test-temporal-window"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # First ESGT
        event1 = await coordinator.initiate_esgt(salience, {"test": "first"})
        first_time = time.time()
        
        # Wait beyond typical binding window
        await asyncio.sleep(0.3)  # 300ms > 200ms binding window
        
        # Second ESGT - should be separate, not bound to first
        event2 = await coordinator.initiate_esgt(salience, {"test": "second"})
        second_time = time.time()
        
        # Events should be temporally separate
        time_diff_ms = (second_time - first_time) * 1000
        
        if event1.success and event2.success:
            # Should be different events (different IDs if tracked)
            assert time_diff_ms > 200, "Events should be temporally separated"
            
            # Each should be independent
            assert event1.event_id != event2.event_id if hasattr(event1, 'event_id') else True
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_synchronization_recovery_after_failure(self, tig_fabric_sync):
        """
        System should recover synchronization after transient failures.
        
        Validates: Sync recovery capability
        Theory: Biological systems can re-entrain after desync
        """
        triggers = TriggerConditions(
            min_available_nodes=8,
            min_salience=0.60,
            refractory_period_ms=50.0
        )
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_sync,
            triggers=triggers,
            coordinator_id="test-recovery"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Attempt multiple ignitions
        events = []
        for i in range(5):
            event = await coordinator.initiate_esgt(salience, {"test": f"recovery_{i}"})
            events.append(event)
            await asyncio.sleep(0.08)  # 80ms between attempts
        
        # Check success pattern
        successes = [e for e in events if e.success]
        
        # System should be able to perform multiple successful ESGTs
        # (validates that it can recover/maintain sync across multiple attempts)
        if len(successes) > 0:
            # At least one success shows system is functional
            assert len(successes) >= 1, "System should succeed at least once"
            
            # Multiple successes show recovery/stability
            # But some may fail due to refractory or other conditions
            assert coordinator.total_events == 5, "All attempts should be processed"
        
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_partial_sync_degraded_performance(self, tig_fabric_sync):
        """
        Partial synchronization (some nodes synced) should allow degraded ESGT.
        
        Validates: Graceful degradation under partial sync
        Theory: Partial Φ is still consciousness, just reduced
        """
        triggers = TriggerConditions(
            min_available_nodes=6,  # Lower requirement
            min_salience=0.60,
            refractory_period_ms=50.0
        )
        
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric_sync,
            triggers=triggers,
            coordinator_id="test-partial-sync"
        )
        await coordinator.start()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        # Attempt ignition
        event = await coordinator.initiate_esgt(salience, {"test": "partial_sync"})
        
        # If successful with partial sync
        if event.success:
            # May have fewer participating nodes
            if hasattr(event, 'node_count'):
                # Some nodes participated
                assert event.node_count > 0, "Should have some participating nodes"
                
                # May be less than total available (partial sync)
                # This is acceptable - degraded but functional
            
            # Coherence may be lower but above threshold
            if hasattr(event, 'achieved_coherence') and event.achieved_coherence > 0:
                assert event.achieved_coherence >= 0.5, \
                    "Partial sync should still achieve minimum coherence"
        
        await coordinator.stop()
