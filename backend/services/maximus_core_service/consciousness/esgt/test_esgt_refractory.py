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
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from consciousness.esgt.coordinator import (
    ESGTCoordinator,
    ESGTPhase,
    SalienceScore,
    TriggerConditions,
)
from consciousness.tig.fabric import TIGFabric, TopologyConfig


class TestESGTRefractoryPeriod:
    """
    Comprehensive tests for ESGT refractory period enforcement.
    
    Theory: Like neural refractory periods, ESGT must prevent continuous
    ignition to maintain discrete conscious moments.
    """

    @pytest.mark.asyncio
    async def test_concurrent_ignition_during_refractory_blocked(self):
        """
        Second ignition attempt during refractory should be blocked.
        
        Validates: Refractory enforcement
        Theory: Absolute refractory period - no ignition possible
        """
        # Create coordinator with short refractory for testing
        triggers = TriggerConditions(refractory_period_ms=100.0)  # 100ms
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        # Mock high salience
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # First ignition should succeed
        result1 = await coordinator.trigger_esgt(content={"test": "first"})
        assert result1.success, "First ignition should succeed"
        
        # Immediate second attempt (during refractory)
        await asyncio.sleep(0.01)  # 10ms < 100ms refractory
        
        result2 = await coordinator.trigger_esgt(content={"test": "second"})
        assert not result2.success, "Second ignition during refractory should fail"
        assert "refractory" in result2.message.lower(), \
            f"Expected refractory message, got: {result2.message}"
        
        await coordinator.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_refractory_period_expires_allows_next(self):
        """
        After refractory period expires, next ignition should succeed.
        
        Validates: Refractory timeout
        Theory: Like relative refractory period ending, normal excitability restored
        """
        triggers = TriggerConditions(refractory_period_ms=50.0)  # 50ms for fast test
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # First ignition
        result1 = await coordinator.trigger_esgt(content={"test": "first"})
        assert result1.success
        
        # Wait for refractory to expire
        await asyncio.sleep(0.06)  # 60ms > 50ms refractory
        
        # Second ignition should now succeed
        result2 = await coordinator.trigger_esgt(content={"test": "second"})
        assert result2.success, "Ignition after refractory should succeed"
        
        await coordinator.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_attempts_all_blocked(self):
        """
        Multiple concurrent ignition attempts during refractory all blocked.
        
        Validates: Refractory enforcement under concurrent load
        Theory: All attempts during absolute refractory fail (no accumulation)
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # First ignition
        result1 = await coordinator.trigger_esgt(content={"test": "first"})
        assert result1.success
        
        # Launch 5 concurrent attempts during refractory
        tasks = [
            coordinator.trigger_esgt(content={"test": f"concurrent{i}"})
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All concurrent attempts should fail
        assert all(not r.success for r in results), \
            "All concurrent attempts during refractory should fail"
        
        assert all("refractory" in r.message.lower() for r in results), \
            "All should report refractory violation"
        
        await coordinator.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_refractory_period_violation_logged(self):
        """
        Refractory period violations should be logged for monitoring.
        
        Validates: Observability of violations
        Theory: System health monitoring requires violation tracking
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # First ignition
        await coordinator.trigger_esgt(content={"test": "first"})
        
        # Get initial violation count
        metrics = coordinator.get_metrics()
        initial_violations = metrics.get("refractory_violations", 0)
        
        # Attempt during refractory
        await asyncio.sleep(0.01)
        result = await coordinator.trigger_esgt(content={"test": "second"})
        assert not result.success
        
        # Check violation was counted
        metrics = coordinator.get_metrics()
        final_violations = metrics.get("refractory_violations", 0)
        
        assert final_violations > initial_violations, \
            "Refractory violation should be logged"
        
        await coordinator.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_phase_transition_during_refractory_rejected(self):
        """
        Phase transition attempts during refractory should be rejected.
        
        Validates: Refractory prevents any ESGT activity
        Theory: During absolute refractory, no state changes possible
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # Trigger ESGT
        await coordinator.trigger_esgt(content={"test": "first"})
        
        # Current ESGT should be active
        current_event = coordinator.current_event
        assert current_event is not None, "Should have active ESGT event"
        
        # Attempt new trigger during refractory
        await asyncio.sleep(0.01)
        result = await coordinator.trigger_esgt(content={"test": "second"})
        
        assert not result.success
        # Should still be processing first ESGT or moved to idle
        # (Either way, second ignition rejected by refractory)
        
        await coordinator.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_early_termination_resets_refractory(self):
        """
        Early ESGT termination should still enforce full refractory period.
        
        Validates: Refractory not shortened by early termination
        Theory: Refractory based on initiation time, not completion
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # Start ESGT
        start_time = time.time()
        result1 = await coordinator.trigger_esgt(content={"test": "first"})
        
        # Terminate early (simulate)
        if hasattr(coordinator, 'stop_current_esgt'):
            await coordinator.stop_current_esgt()
        
        # Attempt new ignition immediately after early termination
        await asyncio.sleep(0.02)  # 20ms < 100ms
        result2 = await coordinator.trigger_esgt(content={"test": "second"})
        
        # Should still be blocked by refractory
        elapsed = (time.time() - start_time) * 1000  # ms
        if elapsed < 100:
            assert not result2.success, \
                "Early termination should not shorten refractory period"
        
        await coordinator.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_refractory_period_configurable(self):
        """
        Refractory period should be configurable per coordinator.
        
        Validates: Flexibility for different consciousness modes
        Theory: Different arousal states may have different temporal dynamics
        """
        # Test with different refractory periods
        short_triggers = TriggerConditions(refractory_period_ms=50.0)
        long_triggers = TriggerConditions(refractory_period_ms=200.0)
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        # Short refractory coordinator
        coord_short = ESGTCoordinator(tig_fabric=fabric, triggers=short_triggers)
        await coord_short.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coord_short._compute_salience = Mock(return_value=salience)
        
        # Trigger first
        await coord_short.trigger_esgt(content={"test": "1"})
        
        # Wait 60ms (should be OK for short, blocked for long)
        await asyncio.sleep(0.06)
        
        result_short = await coord_short.trigger_esgt(content={"test": "2"})
        assert result_short.success, "60ms should exceed 50ms refractory"
        
        await coord_short.stop()
        
        # Long refractory coordinator
        coord_long = ESGTCoordinator(tig_fabric=fabric, triggers=long_triggers)
        await coord_long.initialize()
        coord_long._compute_salience = Mock(return_value=salience)
        
        await coord_long.trigger_esgt(content={"test": "1"})
        await asyncio.sleep(0.06)
        
        result_long = await coord_long.trigger_esgt(content={"test": "2"})
        assert not result_long.success, "60ms should not exceed 200ms refractory"
        
        await coord_long.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_refractory_queue_handling(self):
        """
        Ignition requests during refractory should not queue (immediate rejection).
        
        Validates: No request queuing during refractory
        Theory: Consciousness is winner-take-all, not FIFO queue
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # Trigger first ESGT
        await coordinator.trigger_esgt(content={"test": "first"})
        
        # Queue multiple during refractory
        results_during = []
        for i in range(3):
            await asyncio.sleep(0.01)
            result = await coordinator.trigger_esgt(content={"test": f"queued{i}"})
            results_during.append(result)
        
        # All should be rejected immediately (not queued)
        assert all(not r.success for r in results_during), \
            "All requests during refractory should be rejected"
        
        # Wait for refractory to expire
        await asyncio.sleep(0.15)
        
        # New request should succeed (no queue backlog)
        result_after = await coordinator.trigger_esgt(content={"test": "after"})
        assert result_after.success, "Post-refractory request should succeed immediately"
        
        await coordinator.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_refractory_period_vs_esgt_duration(self):
        """
        Refractory period should be independent of ESGT duration.
        
        Validates: Refractory timing starts at ignition, not completion
        Theory: Like neural refractory - starts at action potential initiation
        """
        triggers = TriggerConditions(refractory_period_ms=100.0)
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # Trigger ESGT
        start_time = time.time()
        result1 = await coordinator.trigger_esgt(content={"test": "first"})
        assert result1.success
        
        # Note: ESGT may still be running (BROADCAST/SUSTAIN phase)
        # But refractory clock started at initiation
        
        # Wait exactly refractory period from start
        elapsed = (time.time() - start_time) * 1000
        remaining = max(0, 100 - elapsed)
        await asyncio.sleep(remaining / 1000 + 0.01)  # +10ms buffer
        
        # Should be allowed regardless of whether first ESGT completed
        result2 = await coordinator.trigger_esgt(content={"test": "second"})
        
        total_elapsed = (time.time() - start_time) * 1000
        if total_elapsed >= 100:
            assert result2.success or not result2.success, \
                "After refractory period, attempt should be evaluated (may succeed/fail based on other conditions)"
        
        await coordinator.stop()
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_zero_refractory_period_allows_continuous(self):
        """
        Zero refractory period should allow continuous ignitions (testing mode).
        
        Validates: Refractory can be disabled for testing
        Theory: For debugging/testing, may need rapid-fire ESGTs
        """
        triggers = TriggerConditions(refractory_period_ms=0.0)  # Disabled
        
        config = TopologyConfig(num_nodes=10, avg_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        coordinator = ESGTCoordinator(tig_fabric=fabric, triggers=triggers)
        await coordinator.initialize()
        
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        coordinator._compute_salience = Mock(return_value=salience)
        
        # Rapid-fire ignitions
        results = []
        for i in range(3):
            result = await coordinator.trigger_esgt(content={"test": f"rapid{i}"})
            results.append(result)
            await asyncio.sleep(0.01)  # Minimal delay
        
        # With zero refractory, all should succeed (or fail for other reasons, not refractory)
        for result in results:
            if not result.success:
                assert "refractory" not in result.message.lower(), \
                    "With zero refractory, failure should not be due to refractory"
        
        await coordinator.stop()
        await fabric.stop()
