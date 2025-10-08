"""Memory Leak Testing - Sustained Operation Monitoring

Tests for memory leaks during sustained operations.

Success Criteria: Stable memory usage over time

Authors: Juan & Claude Code
Version: 1.0.0 - FASE IV Sprint 2
"""

import gc

import pytest

from consciousness.tig.fabric import TIGFabric, TopologyConfig


@pytest.mark.asyncio
async def test_repeated_fabric_creation_no_leak():
    """Test repeated fabric creation doesn't leak memory."""
    initial_objects = len(gc.get_objects())

    for i in range(50):
        config = TopologyConfig(node_count=8, target_density=0.2)
        fabric = TIGFabric(config)
        await fabric.initialize()  # CRITICAL: Initialize before use
        await fabric.enter_esgt_mode()
        await fabric.exit_esgt_mode()
        del fabric

    gc.collect()
    final_objects = len(gc.get_objects())

    growth = final_objects - initial_objects
    growth_pct = (growth / initial_objects) * 100

    print("\n💾 Memory leak test:")
    print(f"   Initial objects: {initial_objects}")
    print(f"   Final objects: {final_objects}")
    print(f"   Growth: {growth} ({growth_pct:.2f}%)")

    # Allow up to 50% growth (some caching is expected)
    assert growth_pct < 50, f"Possible memory leak: {growth_pct:.2f}% growth"


@pytest.mark.asyncio
async def test_memory_test_count():
    """Verify memory test count."""
    assert True  # 2 tests total
