#!/usr/bin/env python3
"""
Load test for Wargaming Service.

Simulates production-like load to validate performance targets:
- p50 latency <200ms
- p95 latency <1s
- p99 latency <3s
- Error rate <0.1%
- Throughput >100 req/s

Usage:
    python load_test_wargaming.py
    python load_test_wargaming.py --requests 2000 --concurrency 100
    
Author: MAXIMUS Team
Glory to YHWH - Validator of performance
"""

import asyncio
import aiohttp
import time
import argparse
import statistics
from datetime import datetime
from typing import List, Dict
import json


class LoadTestResult:
    """Container for load test results."""
    
    def __init__(self):
        self.successes: List[Dict] = []
        self.failures: List[Dict] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    @property
    def total(self) -> int:
        return len(self.successes) + len(self.failures)
    
    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return len(self.successes) / self.total
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def throughput(self) -> float:
        if self.duration == 0:
            return 0.0
        return self.total / self.duration


async def make_request(
    session: aiohttp.ClientSession,
    url: str,
    apv_id: str
) -> Dict:
    """
    Make single ML-first validation request.
    
    Args:
        session: aiohttp session
        url: Target URL
        apv_id: APV identifier
        
    Returns:
        Dict with success/failure and latency
    """
    start = time.time()
    
    try:
        payload = {
            "apv_id": apv_id,
            "cve_id": f"CVE-2024-{apv_id}",
            "patch_id": f"patch_{apv_id}",
            "patch_diff": "--- a/app.py\n+++ b/app.py\n@@ -10 +10 @@\n-query = f'SELECT * FROM users WHERE id={user_id}'\n+query = 'SELECT * FROM users WHERE id=?'",
            "confidence_threshold": 0.8,
            "target_url": "http://localhost:8080"
        }
        
        async with session.post(url, json=payload) as response:
            data = await response.json()
            elapsed = time.time() - start
            
            return {
                "success": response.status == 200,
                "latency": elapsed,
                "status_code": response.status,
                "apv_id": apv_id
            }
    
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        return {
            "success": False,
            "latency": elapsed,
            "error": "Timeout",
            "apv_id": apv_id
        }
    
    except Exception as e:
        elapsed = time.time() - start
        return {
            "success": False,
            "latency": elapsed,
            "error": str(e),
            "apv_id": apv_id
        }


async def load_test(
    url: str = "http://localhost:8026/wargaming/ml-first",
    num_requests: int = 1000,
    concurrency: int = 50,
    timeout: int = 30
) -> LoadTestResult:
    """
    Run load test.
    
    Args:
        url: Endpoint URL
        num_requests: Total requests to make
        concurrency: Max concurrent requests
        timeout: Timeout per request (seconds)
        
    Returns:
        LoadTestResult with statistics
    """
    print("🔥 Wargaming Service Load Test")
    print("="*60)
    print(f"Target: {url}")
    print(f"Requests: {num_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Timeout: {timeout}s")
    print("="*60)
    
    result = LoadTestResult()
    
    # Configure session with connection limits
    connector = aiohttp.TCPConnector(
        limit=concurrency,
        ttl_dns_cache=300
    )
    
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout_obj
    ) as session:
        
        print(f"\n⏱️  Starting {num_requests} requests...")
        result.start_time = time.time()
        
        # Create tasks in batches to control concurrency
        all_results = []
        
        for batch_start in range(0, num_requests, concurrency):
            batch_end = min(batch_start + concurrency, num_requests)
            batch_size = batch_end - batch_start
            
            tasks = [
                make_request(session, url, f"load_test_{i}")
                for i in range(batch_start, batch_end)
            ]
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend(batch_results)
            
            # Progress indicator
            completed = len(all_results)
            progress = (completed / num_requests) * 100
            print(f"  Progress: {completed}/{num_requests} ({progress:.1f}%)", end="\r")
        
        result.end_time = time.time()
        print()  # New line after progress
    
    # Categorize results
    for r in all_results:
        if isinstance(r, dict):
            if r.get("success"):
                result.successes.append(r)
            else:
                result.failures.append(r)
        else:
            # Exception occurred
            result.failures.append({
                "success": False,
                "error": str(r),
                "latency": 0
            })
    
    return result


def print_results(result: LoadTestResult):
    """Print formatted load test results."""
    print("\n" + "="*60)
    print("📊 LOAD TEST RESULTS")
    print("="*60)
    
    print(f"\n⏱️  Duration: {result.duration:.2f}s")
    print(f"📈 Throughput: {result.throughput:.2f} req/s")
    print(f"✅ Success: {len(result.successes)} ({result.success_rate*100:.1f}%)")
    print(f"❌ Failures: {len(result.failures)} ({(1-result.success_rate)*100:.1f}%)")
    
    # Latency statistics (from successful requests)
    if result.successes:
        latencies = [r["latency"] for r in result.successes]
        latencies.sort()
        
        p50 = latencies[len(latencies)//2]
        p95 = latencies[int(len(latencies)*0.95)]
        p99 = latencies[int(len(latencies)*0.99)]
        
        print(f"\n🎯 LATENCY PERCENTILES:")
        print(f"  p50: {p50*1000:.0f}ms")
        print(f"  p95: {p95*1000:.0f}ms")
        print(f"  p99: {p99*1000:.0f}ms")
        print(f"  min: {min(latencies)*1000:.0f}ms")
        print(f"  max: {max(latencies)*1000:.0f}ms")
        print(f"  avg: {statistics.mean(latencies)*1000:.0f}ms")
        
        # Check targets
        print(f"\n🎯 TARGET VALIDATION:")
        checks = {
            "p50 <200ms": (p50 < 0.2, p50*1000),
            "p95 <1s": (p95 < 1.0, p95*1000),
            "p99 <3s": (p99 < 3.0, p99*1000),
            "Error rate <0.1%": ((1-result.success_rate) < 0.001, (1-result.success_rate)*100),
            "Throughput >100 req/s": (result.throughput > 100, result.throughput)
        }
        
        all_passed = True
        for check, (passed, value) in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check} (actual: {value:.1f})")
            if not passed:
                all_passed = False
        
        return all_passed
    else:
        print("\n❌ No successful requests - cannot calculate latencies")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load test for Wargaming Service"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8026/wargaming/ml-first",
        help="Endpoint URL"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=1000,
        help="Total number of requests"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=50,
        help="Max concurrent requests"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout per request (seconds)"
    )
    
    args = parser.parse_args()
    
    # Run load test
    result = asyncio.run(load_test(
        url=args.url,
        num_requests=args.requests,
        concurrency=args.concurrency,
        timeout=args.timeout
    ))
    
    # Print results
    success = print_results(result)
    
    # Exit code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
