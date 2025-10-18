"""
Stress tests for resource limits validation.

Tests validate that the HITL API handles resource constraints gracefully:
1. CPU limits
2. Memory limits
3. Database connection pool exhaustion
4. Network latency

Usage:
    pytest tests/stress/test_resource_limits.py -v --tb=short

Requirements:
    - Docker with resource limits enabled
    - PostgreSQL running
    - HITL API accessible
"""

import pytest
import asyncio
import httpx
import time
from typing import List, Dict, Any
import subprocess
import json


# --- Fixtures ---

@pytest.fixture
def api_base_url() -> str:
    """Base URL for HITL API."""
    return "http://localhost:8003"


@pytest.fixture
async def async_client(api_base_url: str) -> httpx.AsyncClient:
    """Async HTTP client for testing."""
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def container_name() -> str:
    """Docker container name."""
    return "vertice-adaptive-immune"


# --- Helper Functions ---

def get_container_stats(container_name: str) -> Dict[str, Any]:
    """
    Get Docker container resource usage.

    Returns:
        Dict with cpu_percent, memory_usage_mb, memory_limit_mb
    """
    try:
        result = subprocess.run(
            ["docker", "stats", container_name, "--no-stream", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=True
        )
        stats = json.loads(result.stdout)

        # Parse CPU percentage (format: "12.34%")
        cpu_str = stats.get("CPUPerc", "0%").strip("%")
        cpu_percent = float(cpu_str) if cpu_str else 0.0

        # Parse memory usage (format: "123MiB / 1GiB")
        mem_usage_str = stats.get("MemUsage", "0B / 0B").split("/")[0].strip()
        mem_usage_mb = parse_memory_string(mem_usage_str)

        mem_limit_str = stats.get("MemUsage", "0B / 0B").split("/")[1].strip()
        mem_limit_mb = parse_memory_string(mem_limit_str)

        return {
            "cpu_percent": cpu_percent,
            "memory_usage_mb": mem_usage_mb,
            "memory_limit_mb": mem_limit_mb,
            "memory_percent": (mem_usage_mb / mem_limit_mb * 100) if mem_limit_mb > 0 else 0
        }
    except Exception as e:
        pytest.skip(f"Failed to get container stats: {e}")


def parse_memory_string(mem_str: str) -> float:
    """Parse memory string (e.g., '123MiB', '1.5GiB') to MB."""
    mem_str = mem_str.strip().upper()

    if "GIB" in mem_str or "GB" in mem_str:
        return float(mem_str.replace("GIB", "").replace("GB", "")) * 1024
    elif "MIB" in mem_str or "MB" in mem_str:
        return float(mem_str.replace("MIB", "").replace("MB", ""))
    elif "KIB" in mem_str or "KB" in mem_str:
        return float(mem_str.replace("KIB", "").replace("KB", "")) / 1024
    else:
        return 0.0


async def make_concurrent_requests(
    client: httpx.AsyncClient,
    endpoint: str,
    count: int,
    method: str = "GET",
    json_data: Dict[str, Any] = None
) -> List[httpx.Response]:
    """Make concurrent HTTP requests."""
    tasks = []
    for _ in range(count):
        if method == "GET":
            tasks.append(client.get(endpoint))
        elif method == "POST":
            tasks.append(client.post(endpoint, json=json_data))

    return await asyncio.gather(*tasks, return_exceptions=True)


# --- Test Cases ---

@pytest.mark.asyncio
@pytest.mark.stress
class TestCPULimits:
    """Test behavior under CPU constraints."""

    async def test_cpu_limit_graceful_degradation(
        self,
        async_client: httpx.AsyncClient,
        container_name: str
    ):
        """
        Test that API degrades gracefully under CPU limit.

        Expected behavior:
        - Response times increase but stay < 2s
        - No 500 errors
        - Eventually returns 503 if overloaded
        """
        # Get initial stats
        initial_stats = get_container_stats(container_name)
        print(f"\nInitial CPU: {initial_stats['cpu_percent']:.2f}%")

        # Send burst of CPU-intensive requests
        responses = await make_concurrent_requests(
            async_client,
            "/hitl/reviews",
            count=50  # 50 concurrent requests
        )

        # Analyze responses
        success_count = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        error_5xx_count = sum(1 for r in responses if isinstance(r, httpx.Response) and 500 <= r.status_code < 600)
        timeout_count = sum(1 for r in responses if isinstance(r, Exception))

        print(f"Success: {success_count}/{len(responses)}")
        print(f"5xx errors: {error_5xx_count}")
        print(f"Timeouts: {timeout_count}")

        # Get final stats
        final_stats = get_container_stats(container_name)
        print(f"Final CPU: {final_stats['cpu_percent']:.2f}%")

        # Assertions
        assert success_count >= len(responses) * 0.8, "At least 80% requests should succeed"
        assert error_5xx_count == 0, "No 500 errors should occur (503 is acceptable)"


@pytest.mark.asyncio
@pytest.mark.stress
class TestMemoryLimits:
    """Test behavior under memory constraints."""

    async def test_memory_limit_no_oom(
        self,
        async_client: httpx.AsyncClient,
        container_name: str
    ):
        """
        Test that API doesn't crash with OOM under memory pressure.

        Expected behavior:
        - Memory usage stays below limit
        - No container restart (OOM kill)
        - Graceful handling of memory pressure
        """
        # Get initial memory
        initial_stats = get_container_stats(container_name)
        print(f"\nInitial memory: {initial_stats['memory_usage_mb']:.2f}MB / {initial_stats['memory_limit_mb']:.2f}MB ({initial_stats['memory_percent']:.1f}%)")

        # Send requests that might cause memory growth
        responses = []
        for i in range(10):
            batch = await make_concurrent_requests(
                async_client,
                "/hitl/reviews?limit=100",  # Larger responses
                count=10
            )
            responses.extend(batch)

            # Check memory after each batch
            current_stats = get_container_stats(container_name)
            print(f"Batch {i+1}: {current_stats['memory_usage_mb']:.2f}MB ({current_stats['memory_percent']:.1f}%)")

            # Stop if approaching limit (90%)
            if current_stats['memory_percent'] > 90:
                print("Approaching memory limit, stopping test")
                break

            await asyncio.sleep(0.5)  # Brief pause between batches

        # Get final memory
        final_stats = get_container_stats(container_name)
        print(f"Final memory: {final_stats['memory_usage_mb']:.2f}MB ({final_stats['memory_percent']:.1f}%)")

        # Verify no OOM (container still running)
        result = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{.State.Running}}"],
            capture_output=True,
            text=True
        )
        container_running = result.stdout.strip() == "true"

        assert container_running, "Container should still be running (no OOM kill)"
        assert final_stats['memory_percent'] < 100, "Memory usage should not hit 100%"


@pytest.mark.asyncio
@pytest.mark.stress
class TestDatabaseConnectionPool:
    """Test database connection pool exhaustion."""

    async def test_connection_pool_exhaustion_graceful(
        self,
        async_client: httpx.AsyncClient
    ):
        """
        Test that API handles DB connection pool exhaustion gracefully.

        Expected behavior:
        - Requests wait for available connection (queue)
        - No crashes
        - Clear error messages if pool exhausted
        """
        # Default pool size is 20 connections
        # Try to exhaust pool with 50 concurrent requests
        responses = await make_concurrent_requests(
            async_client,
            "/hitl/reviews",
            count=50
        )

        # Analyze responses
        success_count = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        error_503_count = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 503)
        timeout_count = sum(1 for r in responses if isinstance(r, Exception))

        print(f"\nSuccess: {success_count}/{len(responses)}")
        print(f"503 errors: {error_503_count}")
        print(f"Timeouts: {timeout_count}")

        # All requests should either succeed or return 503 (service unavailable)
        # None should crash (500) or hang indefinitely
        total_handled = success_count + error_503_count + timeout_count
        assert total_handled == len(responses), "All requests should be handled"

        # At least some should succeed (queue mechanism working)
        assert success_count > 0, "At least some requests should succeed"


@pytest.mark.asyncio
@pytest.mark.stress
class TestNetworkLatency:
    """Test behavior under network latency."""

    async def test_high_latency_timeouts(
        self,
        async_client: httpx.AsyncClient
    ):
        """
        Test that API respects timeouts under high latency.

        This test validates client-side timeout handling.
        For actual network latency testing, use iptables/tc commands.
        """
        # Create client with very short timeout
        short_timeout_client = httpx.AsyncClient(
            base_url=async_client.base_url,
            timeout=0.1  # 100ms timeout
        )

        try:
            # Try to make request with short timeout
            # Should timeout on slow operations
            start_time = time.time()
            try:
                response = await short_timeout_client.get("/hitl/reviews")
                elapsed = time.time() - start_time
                print(f"\nRequest completed in {elapsed:.3f}s")

                # If it succeeds, it should be fast
                assert elapsed < 0.5, "Request should complete quickly or timeout"

            except httpx.TimeoutException:
                elapsed = time.time() - start_time
                print(f"\nRequest timed out after {elapsed:.3f}s (expected)")
                # Timeout should happen close to configured timeout
                assert 0.05 < elapsed < 0.5, f"Timeout should occur around 0.1s, got {elapsed:.3f}s"

        finally:
            await short_timeout_client.aclose()


# --- Integration Test ---

@pytest.mark.asyncio
@pytest.mark.stress
class TestStressIntegration:
    """Integration test combining multiple stressors."""

    async def test_combined_stress_resilience(
        self,
        async_client: httpx.AsyncClient,
        container_name: str
    ):
        """
        Test resilience under combined CPU, memory, and connection stress.

        This simulates a realistic high-load scenario.
        """
        print("\n=== Combined Stress Test ===")

        # Get initial stats
        initial_stats = get_container_stats(container_name)
        print(f"Initial state:")
        print(f"  CPU: {initial_stats['cpu_percent']:.2f}%")
        print(f"  Memory: {initial_stats['memory_usage_mb']:.2f}MB ({initial_stats['memory_percent']:.1f}%)")

        # Send sustained load for 30 seconds
        start_time = time.time()
        all_responses = []

        while time.time() - start_time < 30:  # 30 seconds
            batch = await make_concurrent_requests(
                async_client,
                "/hitl/reviews",
                count=20
            )
            all_responses.extend(batch)

            # Log stats every 5 batches
            if len(all_responses) % 100 == 0:
                current_stats = get_container_stats(container_name)
                print(f"After {len(all_responses)} requests:")
                print(f"  CPU: {current_stats['cpu_percent']:.2f}%")
                print(f"  Memory: {current_stats['memory_usage_mb']:.2f}MB ({current_stats['memory_percent']:.1f}%)")

            await asyncio.sleep(0.1)  # Small delay between batches

        # Get final stats
        final_stats = get_container_stats(container_name)
        print(f"\nFinal state:")
        print(f"  CPU: {final_stats['cpu_percent']:.2f}%")
        print(f"  Memory: {final_stats['memory_usage_mb']:.2f}MB ({final_stats['memory_percent']:.1f}%)")

        # Analyze all responses
        success_count = sum(1 for r in all_responses if isinstance(r, httpx.Response) and r.status_code == 200)
        error_count = sum(1 for r in all_responses if isinstance(r, httpx.Response) and r.status_code >= 400)
        exception_count = sum(1 for r in all_responses if isinstance(r, Exception))

        print(f"\nResults:")
        print(f"  Total requests: {len(all_responses)}")
        print(f"  Successful: {success_count} ({success_count/len(all_responses)*100:.1f}%)")
        print(f"  Errors: {error_count}")
        print(f"  Exceptions: {exception_count}")

        # Verify container still running
        result = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{.State.Running}}"],
            capture_output=True,
            text=True
        )
        container_running = result.stdout.strip() == "true"

        # Assertions
        assert container_running, "Container should still be running after stress test"
        assert success_count >= len(all_responses) * 0.7, "At least 70% requests should succeed under stress"
        assert final_stats['memory_percent'] < 100, "Memory should not be exhausted"


# --- Conftest for Docker Setup ---

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "stress: mark test as stress test (may modify system resources)"
    )
