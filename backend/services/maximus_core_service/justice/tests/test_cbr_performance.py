"""Performance tests for CBR Engine - Production validation.

Tests cover:
- Retrieval latency under load
- Retain throughput
- Memory usage stability

Performance targets:
- Retrieval: <500ms for 1000 cases (relaxed for SQLite)
- Throughput: 100 retains in <10s
- Memory: <100MB increase over 1000 operations
"""

import pytest
import asyncio
import time
import gc
from services.maximus_core_service.justice.cbr_engine import CBREngine
from services.maximus_core_service.justice.precedent_database import PrecedentDB, CasePrecedent


@pytest.mark.asyncio
async def test_cbr_retrieval_latency():
    """Retrieval should complete in reasonable time for 1000 cases.

    Note: SQLite is slower than PostgreSQL+pgvector.
    Target: <500ms for 1000 cases (vs <100ms production target).
    """
    db = PrecedentDB("sqlite:///:memory:")
    cbr = CBREngine(db)

    # Populate 1000 cases
    print("\nPopulating 1000 test cases...")
    for i in range(1000):
        emb = [0.0] * 384
        emb[i % 384] = float(i) / 1000.0  # Unique embeddings

        await db.store(CasePrecedent(
            situation={"id": i, "type": f"scenario_{i % 10}"},
            action_taken=f"action_{i % 5}",
            rationale=f"Rationale {i}",
            success=0.5 + (i % 50) / 100.0,
            embedding=emb
        ))

    # Measure retrieval time
    query_emb = [0.5] * 384

    start = time.time()
    results = await db.find_similar(query_emb, limit=10)
    elapsed = time.time() - start

    print(f"Retrieval time: {elapsed*1000:.1f}ms for 1000 cases")

    # Relaxed target for SQLite (production with pgvector is faster)
    assert elapsed < 0.5, f"Retrieval too slow: {elapsed*1000:.1f}ms"
    assert len(results) == 10


@pytest.mark.asyncio
async def test_cbr_retain_throughput():
    """Should handle 100 retains in reasonable time.

    Target: <10s for 100 cases (10 cases/second).
    """
    db = PrecedentDB("sqlite:///:memory:")

    print("\nTesting retain throughput...")
    start = time.time()

    for i in range(100):
        emb = [0.0] * 384
        emb[i % 384] = 1.0

        await db.store(CasePrecedent(
            situation={"id": i, "type": f"test_{i}"},
            action_taken=f"action_{i}",
            rationale=f"Rationale {i}",
            success=0.5,
            embedding=emb
        ))

    elapsed = time.time() - start

    throughput = 100 / elapsed
    print(f"Retain throughput: {throughput:.1f} cases/sec ({elapsed:.1f}s total)")

    assert elapsed < 10.0, f"Retain too slow: {elapsed:.1f}s for 100 cases"


@pytest.mark.asyncio
async def test_cbr_memory_stability():
    """Should not leak memory over 1000 operations.

    Target: <100MB increase over 1000 retrieve operations.
    """
    try:
        import psutil
        import os
    except ImportError:
        pytest.skip("psutil not available")

    db = PrecedentDB("sqlite:///:memory:")
    cbr = CBREngine(db)

    # Populate 100 cases
    for i in range(100):
        emb = [0.0] * 384
        emb[i % 384] = 1.0

        await db.store(CasePrecedent(
            situation={"id": i, "type": f"test_{i}"},
            action_taken=f"action_{i}",
            rationale=f"Rationale {i}",
            success=0.5,
            embedding=emb
        ))

    # Force garbage collection before measurement
    gc.collect()

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    print(f"\nInitial memory: {initial_memory:.1f} MB")

    # Perform 1000 retrieve operations
    for i in range(1000):
        query = {"id": i % 100, "type": f"test_{i % 100}"}
        await cbr.retrieve(query)

    # Force garbage collection after operations
    gc.collect()

    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory

    print(f"Final memory: {final_memory:.1f} MB")
    print(f"Memory increase: {memory_increase:.1f} MB")

    # Should not increase by >100MB
    assert memory_increase < 100, f"Potential memory leak: +{memory_increase:.1f}MB"


@pytest.mark.asyncio
async def test_cbr_concurrent_retrieval():
    """Should handle concurrent retrieval requests without degradation.

    Tests 20 parallel retrieve operations.
    """
    db = PrecedentDB("sqlite:///:memory:")
    cbr = CBREngine(db)

    # Populate 100 cases
    for i in range(100):
        emb = [0.0] * 384
        emb[i % 384] = 1.0

        await db.store(CasePrecedent(
            situation={"id": i, "type": f"test_{i}"},
            action_taken=f"action_{i}",
            rationale=f"Rationale {i}",
            success=0.5,
            embedding=emb
        ))

    # 20 concurrent retrievals
    async def retrieve_case(i):
        query = {"id": i % 100, "type": f"test_{i % 100}"}
        return await cbr.retrieve(query)

    start = time.time()
    results = await asyncio.gather(*[retrieve_case(i) for i in range(20)])
    elapsed = time.time() - start

    print(f"\n20 concurrent retrievals: {elapsed*1000:.1f}ms")

    # All should succeed
    assert len(results) == 20
    assert all(isinstance(r, list) for r in results)

    # Should not be significantly slower than sequential
    # (SQLite doesn't parallelize well, but shouldn't deadlock)
    assert elapsed < 5.0, f"Concurrent retrieval too slow: {elapsed:.1f}s"


@pytest.mark.asyncio
async def test_cbr_large_case_base_performance():
    """Should maintain reasonable performance with 5000+ cases.

    This tests scalability beyond typical workload.
    """
    db = PrecedentDB("sqlite:///:memory:")

    print("\nPopulating 5000 cases (this may take a while)...")
    start = time.time()

    # Populate 5000 cases
    for i in range(5000):
        emb = [0.0] * 384
        emb[i % 384] = float(i) / 5000.0

        await db.store(CasePrecedent(
            situation={"id": i, "type": f"scenario_{i % 50}"},
            action_taken=f"action_{i % 10}",
            rationale=f"Rationale {i}",
            success=0.5 + (i % 100) / 200.0,
            embedding=emb
        ))

    populate_time = time.time() - start
    print(f"Population time: {populate_time:.1f}s")

    # Test retrieval with large case base
    query_emb = [0.5] * 384

    start = time.time()
    results = await db.find_similar(query_emb, limit=10)
    retrieval_time = time.time() - start

    print(f"Retrieval time with 5000 cases: {retrieval_time*1000:.1f}ms")

    # Should still complete in reasonable time
    # SQLite fallback may be slower, but should not be prohibitive
    assert retrieval_time < 2.0, f"Retrieval too slow with large case base: {retrieval_time:.1f}s"
    assert len(results) == 10
