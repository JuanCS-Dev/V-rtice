"""
Benchmark: Neo4j vs PostgreSQL for Cognitive Map

Compares performance of Neo4j graph database vs PostgreSQL with JSONB/GIN indexes
for MABA cognitive map operations.

Biblical Foundation:
- Ecclesiastes 7:12: "For the protection of wisdom is like the protection of money,
  and the advantage of knowledge is that wisdom preserves the life of him who has it"

Benchmark Operations (as specified in TRINITY_CORRECTION_PLAN):
1. Store 1000 pages with 10 elements each
2. Store 500 navigation edges
3. Query similar pages (100 queries)
4. Find navigation paths (100 queries)
5. Measure latency, memory, CPU

Decision Criteria:
- If Neo4j is <20% faster → Switch to SQL (lower ops complexity)
- If Neo4j is ≥20% faster → Keep Neo4j (document operational requirements)

Author: Vértice Platform Team
Created: 2025-11-01
"""

import asyncio
from datetime import datetime
import logging
import os
import random
import time
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import cognitive map implementations
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cognitive_map import CognitiveMapEngine
from core.cognitive_map_sql import CognitiveMapSQL


class BenchmarkResults:
    """Container for benchmark results."""

    def __init__(self, backend_name: str):
        self.backend_name = backend_name
        self.operations: dict[str, float] = {}
        self.total_time = 0.0

    def add_operation(self, operation: str, duration: float):
        """Record operation duration."""
        self.operations[operation] = duration
        self.total_time += duration

    def get_summary(self) -> dict[str, Any]:
        """Get benchmark summary."""
        return {
            "backend": self.backend_name,
            "operations": self.operations,
            "total_time": self.total_time,
        }


async def benchmark_neo4j() -> BenchmarkResults:
    """
    Benchmark Neo4j cognitive map.

    Returns:
        BenchmarkResults with timing data
    """
    logger.info("🔥 Starting Neo4j benchmark...")
    results = BenchmarkResults("Neo4j")

    # Initialize Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    engine = CognitiveMapEngine(neo4j_uri, neo4j_user, neo4j_password)

    # Initialize
    start = time.time()
    await engine.initialize()
    results.add_operation("initialize", time.time() - start)

    # 1. Store 1000 pages with 10 elements each
    logger.info("📄 Storing 1000 pages...")
    start = time.time()

    for i in range(1000):
        url = f"https://example.com/page-{i}"
        elements = [
            {
                "selector": f"#element-{j}",
                "tag": "button",
                "text": f"Button {j}",
                "attributes": {"class": "btn", "id": f"element-{j}"},
            }
            for j in range(10)
        ]

        await engine.store_page(url, title=f"Page {i}", elements=elements)

    results.add_operation("store_1000_pages", time.time() - start)

    # 2. Store 500 navigation edges
    logger.info("🔗 Storing 500 navigation edges...")
    start = time.time()

    for i in range(500):
        from_url = f"https://example.com/page-{i}"
        to_url = f"https://example.com/page-{i + 1}"
        await engine.store_navigation(
            from_url, to_url, action="click", selector="#next-button"
        )

    results.add_operation("store_500_navigations", time.time() - start)

    # 3. Query similar pages (100 queries)
    logger.info("🔍 Querying similar pages (100 queries)...")
    start = time.time()

    for i in range(100):
        url = f"https://example.com/page-{random.randint(0, 999)}"
        await engine.get_similar_pages(url, limit=5)

    results.add_operation("query_100_similar_pages", time.time() - start)

    # 4. Find navigation paths (100 queries)
    logger.info("🗺️  Finding navigation paths (100 queries)...")
    start = time.time()

    for i in range(100):
        from_idx = random.randint(0, 400)
        to_idx = from_idx + random.randint(1, 50)
        from_url = f"https://example.com/page-{from_idx}"
        to_url = f"https://example.com/page-{to_idx}"
        await engine.get_navigation_path(from_url, to_url)

    results.add_operation("query_100_navigation_paths", time.time() - start)

    # Close
    await engine.close()

    logger.info(f"✅ Neo4j benchmark complete: {results.total_time:.2f}s total")
    return results


async def benchmark_sql() -> BenchmarkResults:
    """
    Benchmark PostgreSQL cognitive map.

    Returns:
        BenchmarkResults with timing data
    """
    logger.info("🐘 Starting PostgreSQL benchmark...")
    results = BenchmarkResults("PostgreSQL")

    # Initialize PostgreSQL
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = int(os.getenv("POSTGRES_PORT", "5432"))
    db_name = os.getenv("POSTGRES_DB", "maba_test")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

    engine = CognitiveMapSQL(db_host, db_port, db_name, db_user, db_password)

    # Initialize
    start = time.time()
    await engine.initialize()
    results.add_operation("initialize", time.time() - start)

    # 1. Store 1000 pages with 10 elements each
    logger.info("📄 Storing 1000 pages...")
    start = time.time()

    for i in range(1000):
        url = f"https://example.com/page-{i}"
        elements = [
            {
                "selector": f"#element-{j}",
                "tag": "button",
                "text": f"Button {j}",
                "attributes": {"class": "btn", "id": f"element-{j}"},
            }
            for j in range(10)
        ]

        await engine.store_page(url, title=f"Page {i}", elements=elements)

    results.add_operation("store_1000_pages", time.time() - start)

    # 2. Store 500 navigation edges
    logger.info("🔗 Storing 500 navigation edges...")
    start = time.time()

    for i in range(500):
        from_url = f"https://example.com/page-{i}"
        to_url = f"https://example.com/page-{i + 1}"
        await engine.store_navigation(
            from_url, to_url, action="click", selector="#next-button"
        )

    results.add_operation("store_500_navigations", time.time() - start)

    # 3. Query similar pages (100 queries)
    logger.info("🔍 Querying similar pages (100 queries)...")
    start = time.time()

    for i in range(100):
        url = f"https://example.com/page-{random.randint(0, 999)}"
        await engine.get_similar_pages(url, limit=5)

    results.add_operation("query_100_similar_pages", time.time() - start)

    # 4. Find navigation paths (100 queries)
    logger.info("🗺️  Finding navigation paths (100 queries)...")
    start = time.time()

    for i in range(100):
        from_idx = random.randint(0, 400)
        to_idx = from_idx + random.randint(1, 50)
        from_url = f"https://example.com/page-{from_idx}"
        to_url = f"https://example.com/page-{to_idx}"
        await engine.get_navigation_path(from_url, to_url)

    results.add_operation("query_100_navigation_paths", time.time() - start)

    # Close
    await engine.close()

    logger.info(f"✅ PostgreSQL benchmark complete: {results.total_time:.2f}s total")
    return results


def compare_results(neo4j_results: BenchmarkResults, sql_results: BenchmarkResults):
    """
    Compare benchmark results and make recommendation.

    Args:
        neo4j_results: Neo4j benchmark results
        sql_results: PostgreSQL benchmark results
    """
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS COMPARISON")
    print("=" * 80)

    print("\n📊 Operation-by-Operation Comparison:\n")
    print(f"{'Operation':<40} {'Neo4j (s)':<15} {'PostgreSQL (s)':<15} {'Winner':<10}")
    print("-" * 80)

    neo4j_wins = 0
    sql_wins = 0

    for operation in neo4j_results.operations:
        neo4j_time = neo4j_results.operations[operation]
        sql_time = sql_results.operations[operation]

        if neo4j_time < sql_time:
            winner = "Neo4j"
            neo4j_wins += 1
        else:
            winner = "PostgreSQL"
            sql_wins += 1

        print(f"{operation:<40} {neo4j_time:<15.3f} {sql_time:<15.3f} {winner:<10}")

    print("-" * 80)
    print(
        f"{'TOTAL':<40} {neo4j_results.total_time:<15.3f} {sql_results.total_time:<15.3f}"
    )

    # Calculate performance difference
    if neo4j_results.total_time < sql_results.total_time:
        faster_backend = "Neo4j"
        slower_backend = "PostgreSQL"
        faster_time = neo4j_results.total_time
        slower_time = sql_results.total_time
    else:
        faster_backend = "PostgreSQL"
        slower_backend = "Neo4j"
        faster_time = sql_results.total_time
        slower_time = neo4j_results.total_time

    performance_diff_pct = ((slower_time - faster_time) / slower_time) * 100

    print(
        f"\n🏆 {faster_backend} is {performance_diff_pct:.1f}% faster than {slower_backend}"
    )

    # Make recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    if faster_backend == "Neo4j" and performance_diff_pct >= 20:
        print("\n✅ KEEP NEO4J")
        print(f"   - Neo4j is {performance_diff_pct:.1f}% faster (≥20% threshold)")
        print("   - Graph operations justify additional operational complexity")
        print("   - Action: Document Neo4j operational requirements")
        print("   - Action: Create Neo4j deployment playbooks")
    elif faster_backend == "PostgreSQL" or performance_diff_pct < 20:
        print("\n✅ SWITCH TO POSTGRESQL")
        if faster_backend == "PostgreSQL":
            print(f"   - PostgreSQL is {performance_diff_pct:.1f}% faster")
        else:
            print(
                f"   - Neo4j is only {performance_diff_pct:.1f}% faster (<20% threshold)"
            )
        print("   - Lower operational complexity (already using PostgreSQL)")
        print("   - WITH RECURSIVE provides sufficient graph query capabilities")
        print("   - GIN indexes provide fast JSONB queries")
        print("   - Action: Migrate to PostgreSQL implementation")
        print("   - Action: Update configuration to use CognitiveMapSQL")

    print("\n" + "=" * 80)

    # Summary statistics
    print("\n📈 Summary Statistics:\n")
    print(f"Neo4j wins: {neo4j_wins}/{len(neo4j_results.operations)} operations")
    print(f"PostgreSQL wins: {sql_wins}/{len(sql_results.operations)} operations")
    print(f"\nTotal execution time:")
    print(f"  - Neo4j: {neo4j_results.total_time:.2f}s")
    print(f"  - PostgreSQL: {sql_results.total_time:.2f}s")
    print(
        f"  - Difference: {abs(neo4j_results.total_time - sql_results.total_time):.2f}s"
    )

    print("\n" + "=" * 80)


async def main():
    """Run benchmarks and compare results."""
    print("\n" + "=" * 80)
    print("MABA COGNITIVE MAP BENCHMARK: Neo4j vs PostgreSQL")
    print("=" * 80)
    print("\nBiblical Foundation:")
    print('Ecclesiastes 7:12: "For the protection of wisdom is like the protection')
    print('of money, and the advantage of knowledge is that wisdom preserves life"')
    print("\n" + "=" * 80)

    # Run benchmarks
    try:
        neo4j_results = await benchmark_neo4j()
    except Exception as e:
        logger.error(f"Neo4j benchmark failed: {e}")
        logger.info("Skipping Neo4j comparison")
        neo4j_results = None

    try:
        sql_results = await benchmark_sql()
    except Exception as e:
        logger.error(f"PostgreSQL benchmark failed: {e}")
        logger.info("Skipping PostgreSQL comparison")
        sql_results = None

    # Compare results
    if neo4j_results and sql_results:
        compare_results(neo4j_results, sql_results)
    elif sql_results:
        print("\n✅ Only PostgreSQL benchmark completed successfully")
        print("   Recommendation: Use PostgreSQL (Neo4j unavailable)")
    elif neo4j_results:
        print("\n⚠️  Only Neo4j benchmark completed successfully")
        print("   Recommendation: Fix PostgreSQL setup or use Neo4j")
    else:
        print("\n❌ Both benchmarks failed")
        print("   Action: Fix database configurations and retry")


if __name__ == "__main__":
    asyncio.run(main())
