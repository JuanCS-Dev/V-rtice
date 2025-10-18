"""
Breaking point test - find system limits.

Gradually increases load until system breaks or degrades significantly.

Usage:
    pytest tests/stress/test_breaking_point.py -v -s

This test will:
1. Start with 10 users
2. Ramp up to 500 users in 10-minute increments
3. Monitor response times and error rates
4. Identify breaking point

Output:
    - Capacity report (max users, max RPS)
    - Performance degradation curve
    - Resource usage at breaking point
"""

import pytest
import asyncio
import httpx
import time
from typing import List
from dataclasses import dataclass
import subprocess
import json


@dataclass
class LoadTestResult:
    """Results from a single load level."""
    users: int
    duration_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_second: float
    error_rate_percent: float
    cpu_percent: float
    memory_mb: float


# --- Helper Functions ---

async def run_load_level(
    base_url: str,
    num_users: int,
    duration_seconds: int = 60
) -> LoadTestResult:
    """
    Run load test at specific concurrency level.

    Args:
        base_url: API base URL
        num_users: Number of concurrent users
        duration_seconds: Test duration

    Returns:
        LoadTestResult with metrics
    """
    print(f"\n→ Testing {num_users} users for {duration_seconds}s...")

    start_time = time.time()
    end_time = start_time + duration_seconds

    latencies: List[float] = []
    successful = 0
    failed = 0

    # Create clients
    clients = [
        httpx.AsyncClient(base_url=base_url, timeout=10.0)
        for _ in range(num_users)
    ]

    async def make_request(client: httpx.AsyncClient):
        """Make single request and record latency."""
        nonlocal successful, failed
        request_start = time.time()
        try:
            response = await client.get("/hitl/reviews")
            request_duration = (time.time() - request_start) * 1000  # ms

            if response.status_code == 200:
                successful += 1
                latencies.append(request_duration)
            else:
                failed += 1

        except Exception:
            failed += 1

    # Run load for specified duration
    tasks = []
    while time.time() < end_time:
        # Each user makes a request
        for client in clients:
            tasks.append(make_request(client))

        # Wait for batch to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        tasks.clear()

        # Small delay between batches
        await asyncio.sleep(0.1)

    # Close clients
    for client in clients:
        await client.aclose()

    # Calculate metrics
    actual_duration = time.time() - start_time
    total_requests = successful + failed
    rps = total_requests / actual_duration if actual_duration > 0 else 0
    error_rate = (failed / total_requests * 100) if total_requests > 0 else 0

    latencies.sort()
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
    p99_latency = latencies[int(len(latencies) * 0.99)] if latencies else 0

    # Get resource usage
    try:
        stats_result = subprocess.run(
            ["docker", "stats", "vertice-adaptive-immune", "--no-stream", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        stats = json.loads(stats_result.stdout)
        cpu_percent = float(stats.get("CPUPerc", "0%").strip("%"))

        mem_usage_str = stats.get("MemUsage", "0MiB / 0MiB").split("/")[0].strip()
        memory_mb = float(mem_usage_str.replace("MiB", "").replace("GiB", "").replace("MB", "").replace("GB", ""))
    except Exception:
        cpu_percent = 0.0
        memory_mb = 0.0

    return LoadTestResult(
        users=num_users,
        duration_seconds=int(actual_duration),
        total_requests=total_requests,
        successful_requests=successful,
        failed_requests=failed,
        average_latency_ms=avg_latency,
        p95_latency_ms=p95_latency,
        p99_latency_ms=p99_latency,
        requests_per_second=rps,
        error_rate_percent=error_rate,
        cpu_percent=cpu_percent,
        memory_mb=memory_mb
    )


def print_result(result: LoadTestResult):
    """Print result in readable format."""
    print(f"  Users: {result.users}")
    print(f"  Requests: {result.total_requests} ({result.successful_requests} ok, {result.failed_requests} fail)")
    print(f"  RPS: {result.requests_per_second:.2f}")
    print(f"  Error rate: {result.error_rate_percent:.2f}%")
    print(f"  Avg latency: {result.average_latency_ms:.0f}ms")
    print(f"  P95 latency: {result.p95_latency_ms:.0f}ms")
    print(f"  P99 latency: {result.p99_latency_ms:.0f}ms")
    print(f"  CPU: {result.cpu_percent:.1f}%")
    print(f"  Memory: {result.memory_mb:.0f}MB")


def is_degraded(result: LoadTestResult, baseline: LoadTestResult = None) -> bool:
    """
    Check if system is degraded compared to baseline.

    Degradation criteria:
    - Error rate > 1%
    - P95 latency > 2x baseline
    - RPS < 50% baseline
    """
    if result.error_rate_percent > 1.0:
        print(f"  ⚠️ High error rate: {result.error_rate_percent:.2f}%")
        return True

    if result.p95_latency_ms > 2000:  # > 2 seconds
        print(f"  ⚠️ High latency: {result.p95_latency_ms:.0f}ms")
        return True

    if baseline:
        latency_ratio = result.p95_latency_ms / baseline.p95_latency_ms if baseline.p95_latency_ms > 0 else 1
        if latency_ratio > 2:
            print(f"  ⚠️ Latency degraded 2x: {result.p95_latency_ms:.0f}ms vs {baseline.p95_latency_ms:.0f}ms")
            return True

        rps_ratio = result.requests_per_second / baseline.requests_per_second if baseline.requests_per_second > 0 else 1
        if rps_ratio < 0.5:
            print(f"  ⚠️ Throughput dropped 50%: {result.requests_per_second:.2f} vs {baseline.requests_per_second:.2f}")
            return True

    return False


# --- Test Cases ---

@pytest.mark.asyncio
@pytest.mark.stress
@pytest.mark.slow
async def test_find_breaking_point():
    """
    Find system breaking point through gradual ramp-up.

    Test progression:
    - 10 users (baseline)
    - 25 users
    - 50 users
    - 100 users
    - 150 users
    - 200 users
    - 300 users
    - 400 users
    - 500 users

    Stops when system degrades significantly.
    """
    base_url = "http://localhost:8003"
    test_levels = [10, 25, 50, 100, 150, 200, 300, 400, 500]
    duration_per_level = 60  # seconds

    print("=" * 60)
    print("BREAKING POINT TEST")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Test levels: {test_levels}")
    print(f"Duration per level: {duration_per_level}s")
    print("=" * 60)

    results: List[LoadTestResult] = []
    baseline: LoadTestResult = None
    breaking_point: LoadTestResult = None

    for num_users in test_levels:
        result = await run_load_level(base_url, num_users, duration_per_level)
        results.append(result)
        print_result(result)

        # First level is baseline
        if baseline is None:
            baseline = result
            print("  ✓ Baseline established")
            continue

        # Check for degradation
        if is_degraded(result, baseline):
            breaking_point = result
            print(f"\n⚠️ BREAKING POINT REACHED at {num_users} users")
            break

        print("  ✓ System healthy")

    # Print final report
    print("\n" + "=" * 60)
    print("CAPACITY REPORT")
    print("=" * 60)

    if breaking_point:
        # Find last good level (before breaking point)
        last_good = results[-2] if len(results) > 1 else baseline

        print("\n✅ Maximum Capacity:")
        print(f"  Users: {last_good.users}")
        print(f"  RPS: {last_good.requests_per_second:.2f}")
        print(f"  P95 latency: {last_good.p95_latency_ms:.0f}ms")
        print(f"  Error rate: {last_good.error_rate_percent:.2f}%")

        print("\n❌ Breaking Point:")
        print(f"  Users: {breaking_point.users}")
        print(f"  RPS: {breaking_point.requests_per_second:.2f}")
        print(f"  P95 latency: {breaking_point.p95_latency_ms:.0f}ms")
        print(f"  Error rate: {breaking_point.error_rate_percent:.2f}%")

        print("\n📊 Degradation:")
        print(f"  Latency increase: {breaking_point.p95_latency_ms / last_good.p95_latency_ms:.1f}x")
        print(f"  Throughput decrease: {breaking_point.requests_per_second / last_good.requests_per_second:.1f}x")
        print(f"  Error rate increase: {breaking_point.error_rate_percent - last_good.error_rate_percent:.2f}%")

    else:
        # Completed all levels without breaking
        max_result = results[-1]
        print("\n✅ System handled maximum tested load:")
        print(f"  Users: {max_result.users}")
        print(f"  RPS: {max_result.requests_per_second:.2f}")
        print(f"  P95 latency: {max_result.p95_latency_ms:.0f}ms")
        print(f"  Error rate: {max_result.error_rate_percent:.2f}%")
        print("\n💡 Consider testing higher loads")

    # Performance curve
    print("\n📈 Performance Curve:")
    print("  Users | RPS    | P95 (ms) | Error % | CPU % | Memory (MB)")
    print("  " + "-" * 65)
    for r in results:
        print(f"  {r.users:5d} | {r.requests_per_second:6.1f} | {r.p95_latency_ms:8.0f} | {r.error_rate_percent:7.2f} | {r.cpu_percent:5.1f} | {r.memory_mb:11.0f}")

    print("\n" + "=" * 60)

    # Recommendations
    print("\n💡 Recommendations:")
    if breaking_point:
        last_good = results[-2] if len(results) > 1 else baseline
        print(f"  - Production capacity: {int(last_good.users * 0.7)} users (70% of max)")
        print(f"  - Set autoscaling trigger at: {int(last_good.users * 0.5)} users")
        print(f"  - Configure rate limiting at: {int(last_good.requests_per_second * 0.8)} req/s")
    else:
        max_result = results[-1]
        print(f"  - System can handle > {max_result.users} users")
        print("  - Run extended load test to validate sustained performance")

    print("=" * 60)

    # Test assertions
    assert len(results) > 0, "At least one load level should complete"
    assert baseline is not None, "Baseline should be established"

    # Verify baseline is healthy
    assert baseline.error_rate_percent < 1.0, f"Baseline error rate too high: {baseline.error_rate_percent:.2f}%"
    assert baseline.p95_latency_ms < 1000, f"Baseline latency too high: {baseline.p95_latency_ms:.0f}ms"


@pytest.mark.asyncio
@pytest.mark.stress
async def test_quick_stress_check():
    """
    Quick stress check for CI/CD pipelines.

    Tests only 3 levels:
    - 10 users (baseline)
    - 50 users (moderate load)
    - 100 users (high load)

    Duration: ~3 minutes
    """
    base_url = "http://localhost:8003"
    test_levels = [10, 50, 100]
    duration_per_level = 30  # seconds

    print("\n" + "=" * 60)
    print("QUICK STRESS CHECK")
    print("=" * 60)

    results: List[LoadTestResult] = []

    for num_users in test_levels:
        result = await run_load_level(base_url, num_users, duration_per_level)
        results.append(result)
        print_result(result)

        # Check health
        if result.error_rate_percent > 1.0:
            print(f"  ❌ High error rate at {num_users} users")
        elif result.p95_latency_ms > 1000:
            print(f"  ⚠️ High latency at {num_users} users")
        else:
            print(f"  ✅ Healthy at {num_users} users")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    max_healthy_users = 0
    for r in results:
        if r.error_rate_percent < 1.0 and r.p95_latency_ms < 1000:
            max_healthy_users = r.users

    print(f"✅ System healthy up to: {max_healthy_users} users")
    print(f"📊 Max tested RPS: {results[-1].requests_per_second:.2f}")
    print(f"📊 Max tested P95: {results[-1].p95_latency_ms:.0f}ms")

    # Assertions for CI/CD
    assert max_healthy_users >= 50, "System should handle at least 50 users"
    assert results[-1].error_rate_percent < 5.0, "Error rate should be < 5% even under stress"


# --- Pytest Configuration ---

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (> 5 minutes)"
    )
