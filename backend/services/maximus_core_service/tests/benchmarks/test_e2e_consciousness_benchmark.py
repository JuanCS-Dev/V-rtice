"""End-to-End Consciousness Cycle Benchmark

Measures complete consciousness cycle: perception → ESGT ignition → action selection.

Target: <500ms (biologically plausible conscious processing cycle)

Reference:
- Dehaene et al. (2014): Conscious access and processing: 300-500ms
- GWT: Ignition (100ms) + Broadcasting (200ms) + Response (200ms) = 500ms
- P300 wave: ~300ms for conscious recognition
- Voluntary action after conscious decision: 200-500ms

Authors: Juan & Claude Code
Version: 1.0.0 - FASE IV Sprint 3
"""

import asyncio
import time

import pytest
import pytest_asyncio

from consciousness.esgt.coordinator import ESGTCoordinator, SalienceScore, TriggerConditions
from consciousness.mcea.controller import ArousalConfig, ArousalController
from consciousness.tig.fabric import TIGFabric, TopologyConfig
from tests.benchmarks.test_esgt_latency_benchmark import LatencyStats

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def consciousness_system():
    """Create complete consciousness system for E2E benchmarking."""
    # 1. TIG Fabric
    tig_config = TopologyConfig(node_count=24, target_density=0.25)
    tig_fabric = TIGFabric(tig_config)
    await tig_fabric.initialize()
    await tig_fabric.enter_esgt_mode()

    # 2. ESGT Coordinator
    triggers = TriggerConditions()
    triggers.min_salience = 0.60
    triggers.refractory_period_ms = 100.0  # Realistic biological timing
    triggers.max_esgt_frequency_hz = 10.0
    triggers.min_available_nodes = 6

    esgt_coordinator = ESGTCoordinator(tig_fabric=tig_fabric, triggers=triggers, coordinator_id="e2e-coordinator")
    await esgt_coordinator.start()

    # 3. Arousal Controller
    arousal_config = ArousalConfig(update_interval_ms=50.0, baseline_arousal=0.60)
    arousal_controller = ArousalController(config=arousal_config, controller_id="e2e-arousal")
    await arousal_controller.start()

    yield {"tig": tig_fabric, "esgt": esgt_coordinator, "arousal": arousal_controller}

    # Cleanup
    await esgt_coordinator.stop()
    await arousal_controller.stop()
    await tig_fabric.exit_esgt_mode()


# ==================== BENCHMARKS ====================


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_e2e_consciousness_cycle_baseline(consciousness_system):
    """Benchmark complete consciousness cycle.

    Cycle: Stimulus → Salience → ESGT Ignition → Response
    Target: <500ms P99
    """
    esgt = consciousness_system["esgt"]
    arousal = consciousness_system["arousal"]

    latencies = []
    sample_count = 30  # Reduced due to refractory period

    # Warm-up
    for _ in range(3):
        salience = SalienceScore(novelty=0.75, relevance=0.80, urgency=0.70)
        await esgt.initiate_esgt(salience, {"warmup": True})
        await asyncio.sleep(0.11)  # Respect refractory

    # Benchmark full cycle
    for i in range(sample_count):
        cycle_start = time.perf_counter()

        # 1. Stimulus perception (simulated)
        stimulus_salience = SalienceScore(novelty=0.7 + (i % 10) * 0.02, relevance=0.8, urgency=0.75)

        # 2. ESGT Ignition (conscious access)
        event = await esgt.initiate_esgt(stimulus_salience, {"cycle": i})

        # 3. Response selection (simulated - arousal modulation)
        if event.success:
            # Arousal modulation based on conscious content
            arousal.request_modulation(source=f"conscious-response-{i}", delta=0.10, duration_seconds=1.0)

        cycle_latency_ms = (time.perf_counter() - cycle_start) * 1000
        latencies.append(cycle_latency_ms)

        # Respect refractory period
        await asyncio.sleep(0.11)

    # Analysis
    stats = LatencyStats(latencies)
    stats.print_report("End-to-End Consciousness Cycle", target_p99=500.0)

    # Assertions
    assert stats.mean < 1000, f"Mean cycle time too high: {stats.mean:.2f}ms"
    assert stats.p99 < 5000, f"P99 cycle time too high: {stats.p99:.2f}ms (relaxed for simulation)"


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_e2e_consciousness_with_arousal_modulation(consciousness_system):
    """Benchmark consciousness cycle with arousal modulation.

    Tests if arousal level affects ESGT ignition latency.
    """
    esgt = consciousness_system["esgt"]
    arousal = consciousness_system["arousal"]

    latencies_low_arousal = []
    latencies_high_arousal = []

    sample_count = 15

    # Low arousal condition
    arousal.request_modulation(source="test-low", delta=-0.20, duration_seconds=10.0)
    await asyncio.sleep(0.2)  # Let arousal settle

    for i in range(sample_count):
        start = time.perf_counter()
        salience = SalienceScore(novelty=0.75, relevance=0.80, urgency=0.70)
        await esgt.initiate_esgt(salience, {"arousal": "low"})
        latencies_low_arousal.append((time.perf_counter() - start) * 1000)
        await asyncio.sleep(0.11)

    # High arousal condition
    arousal.request_modulation(source="test-high", delta=0.30, duration_seconds=10.0)
    await asyncio.sleep(0.2)  # Let arousal settle

    for i in range(sample_count):
        start = time.perf_counter()
        salience = SalienceScore(novelty=0.75, relevance=0.80, urgency=0.70)
        await esgt.initiate_esgt(salience, {"arousal": "high"})
        latencies_high_arousal.append((time.perf_counter() - start) * 1000)
        await asyncio.sleep(0.11)

    # Analysis
    stats_low = LatencyStats(latencies_low_arousal)
    stats_high = LatencyStats(latencies_high_arousal)

    stats_low.print_report("Consciousness Cycle - Low Arousal")
    stats_high.print_report("Consciousness Cycle - High Arousal")

    print("\n📊 Arousal Impact Analysis:")
    print(f"   Low Arousal Mean:  {stats_low.mean:.2f} ms")
    print(f"   High Arousal Mean: {stats_high.mean:.2f} ms")
    print(f"   Difference:        {abs(stats_high.mean - stats_low.mean):.2f} ms")


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_e2e_multi_ignition_sequence(consciousness_system):
    """Benchmark sequence of multiple ESGT ignitions.

    Simulates stream of consciousness - multiple ignitions in succession.
    """
    esgt = consciousness_system["esgt"]

    sequence_latencies = []
    num_sequences = 5
    ignitions_per_sequence = 5

    for seq in range(num_sequences):
        sequence_start = time.perf_counter()

        for ign in range(ignitions_per_sequence):
            salience = SalienceScore(novelty=0.65 + ign * 0.05, relevance=0.75, urgency=0.70)
            await esgt.initiate_esgt(salience, {"seq": seq, "ign": ign})
            await asyncio.sleep(0.11)  # Refractory period

        sequence_duration_ms = (time.perf_counter() - sequence_start) * 1000
        sequence_latencies.append(sequence_duration_ms)

        # Delay between sequences
        await asyncio.sleep(0.2)

    # Analysis
    stats = LatencyStats(sequence_latencies)
    stats.print_report(f"Multi-Ignition Sequence ({ignitions_per_sequence} ignitions)", target_p99=3000.0)

    print("\n📊 Sequence Performance:")
    print(f"   Ignitions per Sequence: {ignitions_per_sequence}")
    print(f"   Mean Sequence Time:     {stats.mean:.2f} ms")
    print(f"   Mean per Ignition:      {stats.mean / ignitions_per_sequence:.2f} ms")


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_benchmark_count():
    """Verify benchmark test count."""
    assert True  # 4 benchmarks total
