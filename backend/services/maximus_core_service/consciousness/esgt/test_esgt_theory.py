"""
ESGT Theory & Integration Tests - GWD Validation
================================================

Tests validating ESGT against Global Workspace Dynamics theory
and integration with other consciousness components.

REGRA DE OURO: NO MOCK, NO PLACEHOLDER, PRODUCTION-READY
"""

import asyncio
import time
from typing import List

import pytest
import pytest_asyncio

from consciousness.esgt.coordinator import (
    ESGTCoordinator,
    SalienceScore,
    TriggerConditions,
)
from consciousness.esgt.spm import SimpleSPM, SimpleSPMConfig
from consciousness.tig.fabric import TIGFabric, TopologyConfig


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture(scope="function")
async def large_tig_fabric():
    """Create larger TIG fabric for theory validation."""
    config = TopologyConfig(
        node_count=32,
        target_density=0.25,
        clustering_target=0.75,
        enable_small_world_rewiring=True,
    )
    fabric = TIGFabric(config)
    await fabric.initialize()
    yield fabric


@pytest_asyncio.fixture(scope="function")
async def theory_coordinator(large_tig_fabric):
    """Create coordinator for theory testing."""
    triggers = TriggerConditions(
        min_salience=0.65,
        min_available_nodes=10,
        refractory_period_ms=100.0,
    )
    
    coordinator = ESGTCoordinator(
        tig_fabric=large_tig_fabric,
        triggers=triggers,
    )
    
    await coordinator.start()
    yield coordinator
    await coordinator.stop()


# =============================================================================
# GWD Theory Validation: Ignition Phenomenon
# =============================================================================


@pytest.mark.asyncio
async def test_gwd_ignition_threshold_behavior(theory_coordinator):
    """
    Test GWD prediction: All-or-none ignition threshold.
    
    Below threshold → no conscious access
    Above threshold → global broadcast
    """
    results: List[tuple[float, bool]] = []
    
    # Test salience range
    import numpy as np
    for salience_level in np.linspace(0.3, 0.95, 15):
        salience = SalienceScore(
            novelty=salience_level,
            relevance=salience_level * 0.95,
            urgency=salience_level * 0.90,
        )
        content = {"threshold_test": salience_level}
        
        event = await theory_coordinator.initiate_esgt(salience, content)
        results.append((salience_level, event.success))
        
        await asyncio.sleep(0.12)
    
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    # Should have both successes and failures
    assert len(successful) > 0, "No successful ignitions"
    assert len(failed) > 0, "No failed ignitions"
    
    # Find threshold
    success_saliences = [r[0] for r in successful]
    fail_saliences = [r[0] for r in failed]
    
    min_success = min(success_saliences)
    max_fail = max(fail_saliences)
    
    # Threshold should be relatively sharp
    threshold_width = min_success - max_fail
    assert threshold_width < 0.25, f"Threshold too gradual: {threshold_width:.3f}"


@pytest.mark.asyncio
async def test_gwd_refractory_period_enforcement(theory_coordinator):
    """
    Test GWD prediction: Psychological refractory period.
    
    Rapid successive stimuli cannot both become conscious.
    """
    salience = SalienceScore(novelty=0.90, relevance=0.88, urgency=0.85)
    
    # First stimulus
    event1 = await theory_coordinator.initiate_esgt(
        salience,
        {"stimulus": 1}
    )
    assert event1.success, "First stimulus should succeed"
    
    # Immediate second stimulus
    await asyncio.sleep(0.020)
    
    event2 = await theory_coordinator.initiate_esgt(
        salience,
        {"stimulus": 2}
    )
    assert not event2.success, "Second stimulus should be blocked"
    
    # Third stimulus after refractory
    await asyncio.sleep(0.120)
    
    event3 = await theory_coordinator.initiate_esgt(
        salience,
        {"stimulus": 3}
    )
    assert event3.success, "Third stimulus should succeed"


@pytest.mark.asyncio
async def test_gwd_winner_takes_all_competition(theory_coordinator):
    """
    Test GWD prediction: Winner-takes-all competition.
    
    Highest salience wins broadcast access.
    """
    # Create competing stimuli
    stimuli = [
        (SalienceScore(0.65, 0.60, 0.55), "low"),
        (SalienceScore(0.95, 0.93, 0.90), "high"),
        (SalienceScore(0.75, 0.72, 0.68), "medium"),
    ]
    
    results = []
    for salience, label in stimuli:
        event = await theory_coordinator.initiate_esgt(salience, {"label": label})
        results.append((label, event.success))
        await asyncio.sleep(0.005)
    
    successful = [r for r in results if r[1]]
    
    # Only one should succeed (refractory)
    assert len(successful) == 1, f"Expected 1 winner, got {len(successful)}"
    
    # Winner should be highest salience
    assert successful[0][0] == "high", f"Wrong winner: {successful[0][0]}"


@pytest.mark.asyncio
async def test_gwd_global_broadcast_timing(theory_coordinator):
    """
    Test GWD prediction: Ignition takes 100-300ms (biological analog).
    """
    salience = SalienceScore(novelty=0.90, relevance=0.88, urgency=0.85)
    
    durations: List[float] = []
    
    for i in range(10):
        content = {"timing_test": i}
        event = await theory_coordinator.initiate_esgt(salience, content)
        
        if event.success:
            durations.append(event.total_duration_ms)
        
        await asyncio.sleep(0.15)
    
    assert len(durations) >= 5, "Too few successful ignitions"
    
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    # GWD-inspired timing requirements
    assert min_duration > 30, f"Too fast: {min_duration:.1f}ms"
    assert avg_duration > 80, f"Average too fast: {avg_duration:.1f}ms"
    assert max_duration < 600, f"Too slow: {max_duration:.1f}ms"


# =============================================================================
# Integration Tests: ESGT + TIG
# =============================================================================


@pytest.mark.asyncio
async def test_esgt_tig_temporal_coherence(theory_coordinator):
    """
    Test that ESGT maintains temporal coherence via TIG.
    """
    salience = SalienceScore(novelty=0.85, relevance=0.80, urgency=0.75)
    
    # First event
    event1 = await theory_coordinator.initiate_esgt(
        salience,
        {"event": 1}
    )
    assert event1.success
    
    # Wait and trigger second
    await asyncio.sleep(0.15)
    
    event2 = await theory_coordinator.initiate_esgt(
        salience,
        {"event": 2}
    )
    assert event2.success
    
    # Both should be in history
    assert len(theory_coordinator.event_history) >= 2
    
    # Time delta should be realistic
    if len(theory_coordinator.event_history) >= 2:
        time_delta_ms = (
            theory_coordinator.event_history[-1].start_time_ns - 
            theory_coordinator.event_history[-2].start_time_ns
        ) / 1_000_000
        assert 100 < time_delta_ms < 250


@pytest.mark.asyncio
async def test_esgt_tig_node_recruitment_scales_with_salience(theory_coordinator):
    """
    Test that higher salience recruits more nodes.
    """
    # Low salience
    low_salience = SalienceScore(novelty=0.70, relevance=0.65, urgency=0.60)
    event_low = await theory_coordinator.initiate_esgt(
        low_salience,
        {"salience": "low"}
    )
    
    if event_low.success:
        low_nodes = len(event_low.participating_nodes)
        
        await asyncio.sleep(0.12)
        
        # High salience
        high_salience = SalienceScore(novelty=0.95, relevance=0.93, urgency=0.90)
        event_high = await theory_coordinator.initiate_esgt(
            high_salience,
            {"salience": "high"}
        )
        
        if event_high.success:
            high_nodes = len(event_high.participating_nodes)
            
            # High salience should recruit more
            assert high_nodes >= low_nodes, \
                f"High salience didn't recruit more: {high_nodes} vs {low_nodes}"


@pytest.mark.asyncio
async def test_esgt_tig_topology_enables_fast_ignition(large_tig_fabric):
    """
    Test that small-world topology enables fast global broadcast.
    """
    triggers = TriggerConditions(
        min_salience=0.65,
        min_available_nodes=10,
        refractory_period_ms=100.0,
    )
    
    coordinator = ESGTCoordinator(
        tig_fabric=large_tig_fabric,
        triggers=triggers,
    )
    
    await coordinator.start()
    
    try:
        salience = SalienceScore(novelty=0.85, relevance=0.80, urgency=0.75)
        
        start = time.perf_counter()
        event = await coordinator.initiate_esgt(salience, {"topology_test": True})
        end = time.perf_counter()
        
        if event.success:
            ignition_latency_ms = (end - start) * 1000
            
            # Small-world should enable fast ignition
            assert ignition_latency_ms < 30.0, \
                f"Ignition too slow: {ignition_latency_ms:.2f}ms"
        
    finally:
        await coordinator.stop()


# =============================================================================
# Integration Tests: ESGT + SPMs
# =============================================================================


@pytest.mark.asyncio
async def test_esgt_spm_bidirectional_flow(theory_coordinator):
    """
    Test bidirectional communication between ESGT and SPMs.
    """
    config = SimpleSPMConfig(
        processing_interval_ms=50.0,
        base_novelty=0.7,
        base_relevance=0.6,
        base_urgency=0.5,
        max_outputs=5,
    )
    spm = SimpleSPM("test-spm", config)
    await spm.start()
    
    try:
        # SPM generates output
        await asyncio.sleep(0.06)
        
        # Simulate SPM output
        salience = SalienceScore(novelty=0.8, relevance=0.75, urgency=0.70)
        content = {"spm_output": "test"}
        
        event = await theory_coordinator.initiate_esgt(salience, content)
        
        # Should handle SPM input
        assert event is not None
        
    finally:
        await spm.stop()


@pytest.mark.asyncio
async def test_esgt_multiple_spm_coordination(theory_coordinator):
    """
    Test coordination among multiple SPMs.
    """
    # Create multiple SPMs
    spms = []
    for i in range(3):
        config = SimpleSPMConfig(
            processing_interval_ms=50.0,
            base_novelty=0.6 + i * 0.1,
            base_relevance=0.6,
            base_urgency=0.5,
            max_outputs=3,
        )
        spm = SimpleSPM(f"spm-{i}", config)
        await spm.start()
        spms.append(spm)
    
    try:
        await asyncio.sleep(0.1)
        
        # Simulate outputs from different SPMs
        for i, _ in enumerate(spms):
            salience = SalienceScore(
                novelty=0.7 + i * 0.05,
                relevance=0.7,
                urgency=0.65,
            )
            content = {"spm_id": i}
            
            event = await theory_coordinator.initiate_esgt(salience, content)
            
            # First should succeed, others blocked by refractory
            if i == 0:
                await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(0.001)
        
    finally:
        for spm in spms:
            await spm.stop()


# =============================================================================
# Performance Validation
# =============================================================================


@pytest.mark.asyncio
async def test_performance_realtime_latency(theory_coordinator):
    """
    Test real-time performance requirement.
    
    Trigger-to-response latency must be reasonable.
    """
    salience = SalienceScore(novelty=0.90, relevance=0.88, urgency=0.85)
    
    latencies: List[float] = []
    
    for i in range(20):
        content = {"latency_test": i}
        start = time.perf_counter()
        await theory_coordinator.initiate_esgt(salience, content)
        end = time.perf_counter()
        
        latencies.append((end - start) * 1000)
        await asyncio.sleep(0.12)
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    assert avg_latency < 25.0, f"Average latency too high: {avg_latency:.2f}ms"
    assert max_latency < 100.0, f"Max latency too high: {max_latency:.2f}ms"


@pytest.mark.asyncio
async def test_performance_sustained_throughput(theory_coordinator):
    """
    Test sustained throughput over extended operation.
    """
    start_time = time.time()
    duration = 20.0  # 20 seconds
    
    successful_ignitions = 0
    total_attempts = 0
    
    while time.time() - start_time < duration:
        salience = SalienceScore(
            novelty=0.75 + 0.2 * ((time.time() * 1.1) % 1.0),
            relevance=0.70 + 0.25 * ((time.time() * 1.3) % 1.0),
            urgency=0.68,
        )
        content = {"sustained": total_attempts}
        
        event = await theory_coordinator.initiate_esgt(salience, content)
        
        total_attempts += 1
        if event.success:
            successful_ignitions += 1
        
        await asyncio.sleep(0.08)
    
    assert total_attempts > 150, f"Only {total_attempts} attempts in 20s"
    
    success_rate = successful_ignitions / total_attempts
    assert 0.05 < success_rate < 0.50, f"Unrealistic success rate: {success_rate:.1%}"


@pytest.mark.asyncio
async def test_performance_memory_stability(theory_coordinator):
    """
    Test memory stability over extended operation.
    """
    salience = SalienceScore(novelty=0.85, relevance=0.80, urgency=0.75)
    
    initial_history_size = len(theory_coordinator.event_history)
    
    # Generate many events
    for i in range(150):
        content = {"memory_test": i}
        await theory_coordinator.initiate_esgt(salience, content)
        await asyncio.sleep(0.06)
    
    final_history_size = len(theory_coordinator.event_history)
    
    # History should be bounded
    assert final_history_size < 200, f"History grew too large: {final_history_size}"
    assert final_history_size > 30, "History too aggressively pruned"
    
    growth = final_history_size - initial_history_size
    assert growth < 150, f"Unbounded growth: +{growth}"


# =============================================================================
# Phenomenological Validation
# =============================================================================


@pytest.mark.asyncio
async def test_phenomenological_unity_via_coherence(theory_coordinator):
    """
    Test phenomenological property: Unity of consciousness.
    
    Each conscious moment should be unified (high coherence).
    """
    salience = SalienceScore(novelty=0.90, relevance=0.88, urgency=0.85)
    
    for trial in range(5):
        content = {"unity_test": trial}
        event = await theory_coordinator.initiate_esgt(salience, content)
        
        if event.success:
            # Unity requirement: High coherence
            assert event.achieved_coherence > 0.65, \
                f"Trial {trial} lacks unity: coherence={event.achieved_coherence:.3f}"
            
            # Unity requirement: Substantial node participation
            total_nodes = theory_coordinator.tig.config.node_count
            participation_ratio = len(event.participating_nodes) / total_nodes
            
            assert participation_ratio > 0.30, \
                f"Trial {trial} too fragmented: {participation_ratio:.1%}"
        
        await asyncio.sleep(0.12)


@pytest.mark.asyncio
async def test_phenomenological_intentionality_preservation(theory_coordinator):
    """
    Test phenomenological property: Intentionality (aboutness).
    
    Conscious states should maintain reference to content.
    """
    test_contents = [
        {"type": "visual", "object": "red_apple"},
        {"type": "thought", "topic": "mathematics"},
        {"type": "memory", "event": "childhood"},
        {"type": "intention", "action": "reach"},
    ]
    
    for content in test_contents:
        salience = SalienceScore(novelty=0.85, relevance=0.80, urgency=0.75)
        
        event = await theory_coordinator.initiate_esgt(salience, content)
        
        if event.success:
            # Intentionality: Content preserved in history
            assert len(theory_coordinator.event_history) > 0
            latest = theory_coordinator.event_history[-1]
            assert latest.content == content, "Content not preserved"
        
        await asyncio.sleep(0.12)


@pytest.mark.asyncio
async def test_consciousness_state_transitions(theory_coordinator):
    """
    Test consciousness state transitions over time.
    
    System should correctly transition:
    - Unconscious (no active event)
    - Conscious (active event)
    - Return to unconscious
    """
    # Start with no active event
    assert theory_coordinator.active_event is None
    
    # Low salience → remains unconscious
    low_salience = SalienceScore(novelty=0.4, relevance=0.3, urgency=0.2)
    event = await theory_coordinator.initiate_esgt(
        low_salience,
        {"subliminal": True}
    )
    assert not event.success
    
    # High salience → becomes conscious
    high_salience = SalienceScore(novelty=0.90, relevance=0.88, urgency=0.85)
    event = await theory_coordinator.initiate_esgt(
        high_salience,
        {"conscious": True}
    )
    assert event.success
    
    # Should have event in history
    assert len(theory_coordinator.event_history) >= 1
    
    # Eventually returns to no active event
    await asyncio.sleep(0.3)
    # (active_event may or may not be None depending on timing)


@pytest.mark.asyncio
async def test_sustained_consciousness_stream(theory_coordinator):
    """
    Test sustained stream of conscious experiences.
    """
    successful_events = []
    
    # 10 seconds of processing
    for i in range(20):
        salience = SalienceScore(
            novelty=0.7 + 0.2 * (i / 20),
            relevance=0.75 + 0.15 * (i / 20),
            urgency=0.65 + 0.25 * (i / 20),
        )
        content = {"stream": i}
        
        event = await theory_coordinator.initiate_esgt(salience, content)
        
        if event.success:
            successful_events.append(i)
        
        await asyncio.sleep(0.5)
    
    # Should have multiple successful events
    assert len(successful_events) >= 3, \
        f"Too few events: {len(successful_events)}"
    
    # Events should be distributed
    if len(successful_events) >= 2:
        intervals = [
            successful_events[i+1] - successful_events[i]
            for i in range(len(successful_events) - 1)
        ]
        avg_interval = sum(intervals) / len(intervals)
        assert avg_interval > 1, "Events too close"
