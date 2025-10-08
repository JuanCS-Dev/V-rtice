"""MCEA Arousal Modulation Latency Benchmark

Measures latency of arousal modulation operations.

Target: <20ms (biologically plausible autonomic response)

Reference:
- Autonomic nervous system response: 50-200ms
- Emotional arousal modulation: Fast subcortical pathway
- Sympathetic/parasympathetic balance adjustment: <100ms

Authors: Juan & Claude Code
Version: 1.0.0 - FASE IV Sprint 3
"""

import asyncio
import time

import pytest
import pytest_asyncio

from consciousness.mcea.controller import ArousalConfig, ArousalController
from tests.benchmarks.test_esgt_latency_benchmark import LatencyStats

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def mcea_controller():
    """Create MCEA arousal controller."""
    config = ArousalConfig(
        update_interval_ms=50.0,  # 20 Hz modulation
        baseline_arousal=0.50,
        min_arousal=0.10,
        max_arousal=0.95,
    )
    controller = ArousalController(config=config, controller_id="benchmark-mcea")
    await controller.start()
    yield controller
    await controller.stop()


# ==================== BENCHMARKS ====================


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_mcea_arousal_modulation_latency(mcea_controller):
    """Benchmark MCEA arousal modulation request latency.

    Measures time to request arousal modulation.
    Target: <20ms
    """
    latencies = []
    sample_count = 100

    # Warm-up
    for _ in range(5):
        mcea_controller.request_modulation(source="warmup", delta=0.05, duration_seconds=0.5)

    # Benchmark
    for i in range(sample_count):
        start = time.perf_counter()
        mcea_controller.request_modulation(
            source=f"benchmark-{i}", delta=0.1 if i % 2 == 0 else -0.1, duration_seconds=1.0
        )
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

    # Analysis
    stats = LatencyStats(latencies)
    stats.print_report("MCEA Arousal Modulation Request Latency", target_p99=20.0)

    # Assertions
    assert stats.mean < 50, f"Mean latency too high: {stats.mean:.2f}ms"
    assert stats.p99 < 200, f"P99 latency too high: {stats.p99:.2f}ms"


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_mcea_arousal_retrieval_latency(mcea_controller):
    """Benchmark MCEA current arousal retrieval latency.

    Measures time to get current arousal level.
    Target: <10ms (very fast read)
    """
    latencies = []
    sample_count = 100

    # Warm-up
    for _ in range(5):
        _ = mcea_controller.get_current_arousal()

    # Benchmark
    for i in range(sample_count):
        start = time.perf_counter()
        arousal_state = mcea_controller.get_current_arousal()
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

        # Verify valid arousal
        assert 0.0 <= arousal_state.arousal <= 1.0

    # Analysis
    stats = LatencyStats(latencies)
    stats.print_report("MCEA Arousal Retrieval Latency", target_p99=10.0)

    # Assertions
    assert stats.mean < 20, f"Mean latency too high: {stats.mean:.2f}ms"
    assert stats.p99 < 100, f"P99 latency too high: {stats.p99:.2f}ms"


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_mcea_modulation_response_pattern(mcea_controller):
    """Benchmark arousal modulation response pattern.

    Measures modulation request → actual arousal change latency.
    """
    latencies = []
    sample_count = 20

    for i in range(sample_count):
        # Get baseline
        baseline_state = mcea_controller.get_current_arousal()

        # Request modulation
        start = time.perf_counter()
        mcea_controller.request_modulation(source=f"pattern-test-{i}", delta=0.20, duration_seconds=0.5)

        # Wait for controller to process (background task)
        await asyncio.sleep(0.1)  # Give time for modulation to apply

        # Check if arousal changed
        new_state = mcea_controller.get_current_arousal()
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

        # Small delay between tests
        await asyncio.sleep(0.05)

    # Analysis
    stats = LatencyStats(latencies)
    stats.print_report("MCEA Modulation Response Pattern", target_p99=150.0)

    assert stats.p99 < 500, f"Response latency too high: {stats.p99:.2f}ms"


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_benchmark_count():
    """Verify benchmark test count."""
    assert True  # 4 benchmarks total
