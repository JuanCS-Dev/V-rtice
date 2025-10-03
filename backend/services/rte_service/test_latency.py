"""
RTE Latency Benchmark
=====================
Test RTE end-to-end latency to validate <50ms p99 requirement.

Tests:
1. Pattern-only detection (Hyperscan fast path)
2. ML-only detection (no pattern match)
3. Combined detection (pattern + ML)
4. Clean traffic (no detection)

Metrics:
- Average latency
- p50, p95, p99 latencies
- Throughput (requests/sec)
"""

import asyncio
import time
import statistics
from typing import List, Dict
import json
import random

import httpx
import numpy as np

# Configuration
RTE_URL = "http://localhost:8005"
NUM_REQUESTS = 1000
CONCURRENT_REQUESTS = 10


class LatencyBenchmark:
    """Benchmark RTE latency"""

    def __init__(self, base_url: str = RTE_URL):
        self.base_url = base_url
        self.latencies: List[float] = []
        self.errors: List[str] = []

    async def run_benchmark(self, num_requests: int, concurrency: int):
        """
        Run latency benchmark.

        Args:
            num_requests: Total number of requests to send
            num_concurrent: Number of concurrent requests
        """
        print("\n" + "="*80)
        print("RTE LATENCY BENCHMARK")
        print("="*80)
        print(f"Target: {self.base_url}")
        print(f"Total requests: {num_requests}")
        print(f"Concurrency: {concurrency}")
        print("="*80 + "\n")

        # Test scenarios
        scenarios = [
            {
                "name": "Critical Pattern Match (Hyperscan fast path)",
                "payload": "Download malware.exe now!",
                "metadata": self._generate_normal_metadata(),
                "weight": 0.1  # 10% of traffic
            },
            {
                "name": "SQL Injection Pattern",
                "payload": "SELECT * FROM users WHERE 1=1",
                "metadata": self._generate_normal_metadata(),
                "weight": 0.2
            },
            {
                "name": "ML Anomaly Only (no pattern)",
                "payload": "Normal looking HTTP request",
                "metadata": self._generate_anomalous_metadata(),
                "weight": 0.2
            },
            {
                "name": "Clean Traffic (no detection)",
                "payload": "GET /api/health HTTP/1.1",
                "metadata": self._generate_normal_metadata(),
                "weight": 0.5  # 50% clean
            }
        ]

        # Health check first
        print("Checking service health...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=10)
                if response.status_code == 200:
                    print("✓ Service is healthy\n")
                else:
                    print(f"✗ Service unhealthy: {response.status_code}")
                    return
        except Exception as e:
            print(f"✗ Cannot connect to RTE service: {e}")
            return

        # Generate requests
        requests = []
        for i in range(num_requests):
            # Select scenario based on weight
            scenario = random.choices(
                scenarios,
                weights=[s["weight"] for s in scenarios]
            )[0]

            request = {
                "event_id": f"bench_{i}",
                "timestamp": time.time(),
                "payload": scenario["payload"],
                "metadata": scenario["metadata"],
                "source_ip": self._random_ip(),
                "destination_port": random.choice([80, 443, 3306, 5432, 8080]),
                "protocol": "tcp"
            }
            requests.append(request)

        # Run benchmark
        print(f"Sending {num_requests} requests with concurrency={concurrency}...\n")
        start_time = time.time()

        # Split into batches
        batches = [
            requests[i:i + concurrency]
            for i in range(0, len(requests), concurrency)
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for batch_idx, batch in enumerate(batches):
                tasks = [
                    self._send_request(client, req)
                    for req in batch
                ]
                await asyncio.gather(*tasks)

                # Progress indicator
                if (batch_idx + 1) % 10 == 0:
                    progress = ((batch_idx + 1) * concurrency / num_requests) * 100
                    print(f"Progress: {progress:.1f}% ({(batch_idx + 1) * concurrency}/{num_requests})")

        total_time = time.time() - start_time

        # Print results
        self._print_results(total_time, num_requests)

    async def _send_request(self, client: httpx.AsyncClient, request_data: Dict):
        """Send single request and measure latency"""
        start = time.time()

        try:
            response = await client.post(
                f"{self.base_url}/detect",
                json=request_data,
                timeout=30.0
            )

            latency_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                self.latencies.append(latency_ms)
            else:
                self.errors.append(f"HTTP {response.status_code}")

        except Exception as e:
            self.errors.append(str(e))

    def _generate_normal_metadata(self) -> Dict:
        """Generate normal traffic metadata"""
        return {
            "packet_size": np.random.normal(500, 100),
            "packet_count": np.random.randint(10, 100),
            "bytes_sent": np.random.normal(5000, 1000),
            "protocol": "TCP",
            "payload_entropy": np.random.uniform(3, 5),
            "connection_duration": np.random.uniform(0.1, 10),
            "packets_per_second": np.random.uniform(10, 100),
            "unique_ports": np.random.randint(1, 5),
            "syn_count": np.random.randint(1, 10),
            "fin_count": np.random.randint(1, 10),
            "rst_count": 0,
            "ack_ratio": np.random.uniform(0.8, 1.0),
            "dns_queries": np.random.randint(0, 5)
        }

    def _generate_anomalous_metadata(self) -> Dict:
        """Generate anomalous traffic metadata"""
        return {
            "packet_size": np.random.normal(50000, 5000),  # Very large
            "packet_count": np.random.randint(1000, 10000),  # Many packets
            "bytes_sent": np.random.normal(100000, 10000),  # High bandwidth
            "protocol": "ICMP",  # Unusual protocol
            "payload_entropy": np.random.uniform(7, 8),  # High entropy
            "connection_duration": np.random.uniform(0.001, 0.01),  # Very short
            "packets_per_second": np.random.uniform(1000, 5000),  # High PPS
            "unique_ports": np.random.randint(100, 500),  # Port scanning
            "syn_count": np.random.randint(100, 1000),  # SYN flood
            "fin_count": 0,
            "rst_count": np.random.randint(50, 100),
            "ack_ratio": np.random.uniform(0.1, 0.3),  # Low ACK ratio
            "dns_queries": np.random.randint(100, 1000)  # DNS tunneling
        }

    def _random_ip(self) -> str:
        """Generate random IP address"""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

    def _print_results(self, total_time: float, num_requests: int):
        """Print benchmark results"""
        print("\n" + "="*80)
        print("BENCHMARK RESULTS")
        print("="*80 + "\n")

        if not self.latencies:
            print("✗ No successful requests")
            return

        # Calculate statistics
        sorted_latencies = sorted(self.latencies)
        p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        avg = statistics.mean(self.latencies)
        min_lat = min(self.latencies)
        max_lat = max(self.latencies)
        stddev = statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0

        throughput = num_requests / total_time

        # Print latency stats
        print("LATENCY STATISTICS:")
        print(f"  Total requests:  {num_requests}")
        print(f"  Successful:      {len(self.latencies)} ({len(self.latencies)/num_requests*100:.1f}%)")
        print(f"  Failed:          {len(self.errors)} ({len(self.errors)/num_requests*100:.1f}%)")
        print()
        print(f"  Average:         {avg:.2f}ms")
        print(f"  Min:             {min_lat:.2f}ms")
        print(f"  Max:             {max_lat:.2f}ms")
        print(f"  Std Dev:         {stddev:.2f}ms")
        print()
        print(f"  p50 (median):    {p50:.2f}ms")
        print(f"  p95:             {p95:.2f}ms")
        print(f"  p99:             {p99:.2f}ms  {'✓ PASS' if p99 < 50 else '✗ FAIL'} (<50ms target)")
        print()
        print(f"THROUGHPUT:")
        print(f"  Total time:      {total_time:.2f}s")
        print(f"  Throughput:      {throughput:.2f} req/s")
        print()

        # Error breakdown
        if self.errors:
            print("ERRORS:")
            error_counts = {}
            for error in self.errors:
                error_counts[error] = error_counts.get(error, 0) + 1
            for error, count in error_counts.items():
                print(f"  {error}: {count}")
            print()

        # Latency distribution
        print("LATENCY DISTRIBUTION:")
        buckets = [
            ("0-10ms", 0, 10),
            ("10-20ms", 10, 20),
            ("20-30ms", 20, 30),
            ("30-50ms", 30, 50),
            ("50-100ms", 50, 100),
            ("100ms+", 100, float('inf'))
        ]

        for name, low, high in buckets:
            count = sum(1 for lat in self.latencies if low <= lat < high)
            pct = count / len(self.latencies) * 100
            bar = "█" * int(pct / 2)
            print(f"  {name:10s}: {bar:50s} {count:4d} ({pct:5.1f}%)")

        print("\n" + "="*80)

        # Pass/fail verdict
        if p99 < 50:
            print("✓ BENCHMARK PASSED - p99 latency under 50ms target")
        else:
            print(f"✗ BENCHMARK FAILED - p99 latency {p99:.2f}ms exceeds 50ms target")

        print("="*80 + "\n")


async def main():
    """Run benchmark"""
    benchmark = LatencyBenchmark(RTE_URL)
    await benchmark.run_benchmark(NUM_REQUESTS, CONCURRENT_REQUESTS)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                        RTE LATENCY BENCHMARK                              ║
║                                                                           ║
║  Target: p99 latency < 50ms                                               ║
║  Tests: Hyperscan + ML + Fusion Engine + Playbooks                        ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())
