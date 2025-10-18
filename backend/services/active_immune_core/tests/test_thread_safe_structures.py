"""Tests for coordination/thread_safe_structures.py

100% deterministic tests - no flakiness allowed.

Authors: Juan + Claude
Date: 2025-10-07
"""

import asyncio

import pytest

from coordination.thread_safe_structures import (
    AtomicCounter,
    ThreadSafeBuffer,
    ThreadSafeCounter,
    ThreadSafeTemperature,
)

# ==================== THREAD-SAFE BUFFER TESTS ====================


class TestThreadSafeBuffer:
    """Test thread-safe circular buffer"""

    @pytest.mark.asyncio
    async def test_append_single_item(self):
        """Test appending a single item"""
        buffer = ThreadSafeBuffer[int](maxsize=10)

        await buffer.append(42)

        items = await buffer.get_all()
        assert items == [42]

    @pytest.mark.asyncio
    async def test_append_multiple_items(self):
        """Test appending multiple items"""
        buffer = ThreadSafeBuffer[str](maxsize=10)

        await buffer.append("a")
        await buffer.append("b")
        await buffer.append("c")

        items = await buffer.get_all()
        assert items == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_maxsize_drops_oldest(self):
        """Test that buffer drops oldest items when full"""
        buffer = ThreadSafeBuffer[int](maxsize=3)

        # Fill buffer
        await buffer.append(1)
        await buffer.append(2)
        await buffer.append(3)

        # Add one more (should drop 1)
        await buffer.append(4)

        items = await buffer.get_all()
        assert items == [2, 3, 4]  # 1 was dropped

    @pytest.mark.asyncio
    async def test_get_recent_n_items(self):
        """Test getting last N items"""
        buffer = ThreadSafeBuffer[int](maxsize=10)

        for i in range(5):
            await buffer.append(i)

        recent = await buffer.get_recent(3)
        assert recent == [2, 3, 4]  # Last 3 items

    @pytest.mark.asyncio
    async def test_get_recent_more_than_size(self):
        """Test get_recent when N > buffer size"""
        buffer = ThreadSafeBuffer[int](maxsize=10)

        await buffer.append(1)
        await buffer.append(2)

        recent = await buffer.get_recent(5)
        assert recent == [1, 2]  # Only returns what's available

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing buffer"""
        buffer = ThreadSafeBuffer[int](maxsize=10)

        await buffer.append(1)
        await buffer.append(2)
        await buffer.append(3)

        cleared_count = await buffer.clear()

        assert cleared_count == 3
        items = await buffer.get_all()
        assert items == []

    @pytest.mark.asyncio
    async def test_size(self):
        """Test getting current buffer size"""
        buffer = ThreadSafeBuffer[int](maxsize=10)

        assert await buffer.size() == 0

        await buffer.append(1)
        assert await buffer.size() == 1

        await buffer.append(2)
        assert await buffer.size() == 2

    @pytest.mark.asyncio
    async def test_maxsize_property(self):
        """Test maxsize property"""
        buffer = ThreadSafeBuffer[int](maxsize=100)

        assert buffer.maxsize() == 100

    @pytest.mark.asyncio
    async def test_stats(self):
        """Test statistics tracking"""
        buffer = ThreadSafeBuffer[int](maxsize=3)

        # Append 5 items (2 will be dropped)
        for i in range(5):
            await buffer.append(i)

        stats = await buffer.stats()

        assert stats["current_size"] == 3
        assert stats["maxsize"] == 3
        assert stats["total_appended"] == 5
        assert stats["total_dropped"] == 2

    @pytest.mark.asyncio
    async def test_concurrent_appends(self):
        """Test concurrent appends are safe"""
        buffer = ThreadSafeBuffer[int](maxsize=100)

        # Run 50 concurrent appends
        tasks = [buffer.append(i) for i in range(50)]
        await asyncio.gather(*tasks)

        size = await buffer.size()
        assert size == 50

    @pytest.mark.asyncio
    async def test_generic_type_dict(self):
        """Test buffer with dict type"""
        buffer = ThreadSafeBuffer[dict](maxsize=10)

        await buffer.append({"key": "value1"})
        await buffer.append({"key": "value2"})

        items = await buffer.get_all()
        assert len(items) == 2
        assert items[0]["key"] == "value1"


# ==================== ATOMIC COUNTER TESTS ====================


class TestAtomicCounter:
    """Test atomic counter"""

    @pytest.mark.asyncio
    async def test_initial_value(self):
        """Test counter initializes with given value"""
        counter = AtomicCounter(initial=10)

        value = await counter.get()
        assert value == 10

    @pytest.mark.asyncio
    async def test_increment_default(self):
        """Test increment by 1 (default)"""
        counter = AtomicCounter(initial=0)

        new_value = await counter.increment()

        assert new_value == 1
        assert await counter.get() == 1

    @pytest.mark.asyncio
    async def test_increment_by_delta(self):
        """Test increment by specific delta"""
        counter = AtomicCounter(initial=0)

        new_value = await counter.increment(delta=5)

        assert new_value == 5

    @pytest.mark.asyncio
    async def test_decrement_default(self):
        """Test decrement by 1 (default)"""
        counter = AtomicCounter(initial=10)

        new_value = await counter.decrement()

        assert new_value == 9

    @pytest.mark.asyncio
    async def test_decrement_by_delta(self):
        """Test decrement by specific delta"""
        counter = AtomicCounter(initial=10)

        new_value = await counter.decrement(delta=3)

        assert new_value == 7

    @pytest.mark.asyncio
    async def test_set(self):
        """Test setting counter to specific value"""
        counter = AtomicCounter(initial=0)

        old_value = await counter.set(100)

        assert old_value == 0
        assert await counter.get() == 100

    @pytest.mark.asyncio
    async def test_compare_and_set_success(self):
        """Test CAS operation succeeds when value matches"""
        counter = AtomicCounter(initial=10)

        success = await counter.compare_and_set(expected=10, new=20)

        assert success is True
        assert await counter.get() == 20

    @pytest.mark.asyncio
    async def test_compare_and_set_failure(self):
        """Test CAS operation fails when value doesn't match"""
        counter = AtomicCounter(initial=10)

        success = await counter.compare_and_set(expected=5, new=20)

        assert success is False
        assert await counter.get() == 10  # Unchanged

    @pytest.mark.asyncio
    async def test_concurrent_increments(self):
        """Test concurrent increments are atomic"""
        counter = AtomicCounter(initial=0)

        # Run 100 concurrent increments
        tasks = [counter.increment() for _ in range(100)]
        await asyncio.gather(*tasks)

        final_value = await counter.get()
        assert final_value == 100  # All increments counted


# ==================== THREAD-SAFE TEMPERATURE TESTS ====================


class TestThreadSafeTemperature:
    """Test thread-safe temperature management"""

    @pytest.mark.asyncio
    async def test_initial_value(self):
        """Test temperature initializes with given value"""
        temp = ThreadSafeTemperature(initial=37.0)

        value = await temp.get()
        assert value == 37.0

    @pytest.mark.asyncio
    async def test_adjust_positive(self):
        """Test adjusting temperature upward"""
        temp = ThreadSafeTemperature(initial=37.0)

        new_value = await temp.adjust(+0.5)

        assert new_value == 37.5

    @pytest.mark.asyncio
    async def test_adjust_negative(self):
        """Test adjusting temperature downward"""
        temp = ThreadSafeTemperature(initial=37.0)

        new_value = await temp.adjust(-0.5)

        assert new_value == 36.5

    @pytest.mark.asyncio
    async def test_adjust_clamped_to_max(self):
        """Test temperature clamped to max boundary"""
        temp = ThreadSafeTemperature(initial=41.0, min_temp=36.0, max_temp=42.0)

        new_value = await temp.adjust(+2.0)  # Would be 43.0

        assert new_value == 42.0  # Clamped to max

    @pytest.mark.asyncio
    async def test_adjust_clamped_to_min(self):
        """Test temperature clamped to min boundary"""
        temp = ThreadSafeTemperature(initial=37.0, min_temp=36.0, max_temp=42.0)

        new_value = await temp.adjust(-2.0)  # Would be 35.0

        assert new_value == 36.0  # Clamped to min

    @pytest.mark.asyncio
    async def test_set(self):
        """Test setting temperature directly"""
        temp = ThreadSafeTemperature(initial=37.0)

        new_value = await temp.set(38.5)

        assert new_value == 38.5

    @pytest.mark.asyncio
    async def test_set_clamped(self):
        """Test set also enforces bounds"""
        temp = ThreadSafeTemperature(initial=37.0, min_temp=36.0, max_temp=42.0)

        new_value = await temp.set(50.0)  # Above max

        assert new_value == 42.0  # Clamped

    @pytest.mark.asyncio
    async def test_multiply(self):
        """Test multiplying temperature"""
        temp = ThreadSafeTemperature(initial=37.0)

        new_value = await temp.multiply(1.1)  # 37.0 * 1.1 = 40.7

        assert new_value == pytest.approx(40.7)

    @pytest.mark.asyncio
    async def test_multiply_clamped(self):
        """Test multiply also enforces bounds"""
        temp = ThreadSafeTemperature(initial=40.0, min_temp=36.0, max_temp=42.0)

        new_value = await temp.multiply(1.5)  # Would be 60.0

        assert new_value == 42.0  # Clamped to max

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test temperature statistics"""
        temp = ThreadSafeTemperature(initial=37.0, min_temp=36.0, max_temp=42.0)

        # Make some adjustments
        await temp.adjust(+1.0)  # 38.0
        await temp.adjust(+1.0)  # 39.0
        await temp.adjust(-0.5)  # 38.5

        stats = await temp.get_stats()

        assert stats["current"] == 38.5
        assert stats["min"] == 36.0
        assert stats["max"] == 42.0
        assert stats["history_size"] == 4  # initial + 3 adjustments
        assert "avg" in stats
        assert "variance" in stats

    @pytest.mark.asyncio
    async def test_history_tracking(self):
        """Test that history is tracked"""
        temp = ThreadSafeTemperature(initial=37.0)

        await temp.adjust(+0.1)
        await temp.adjust(+0.1)
        await temp.adjust(+0.1)

        stats = await temp.get_stats()
        assert stats["history_size"] == 4  # initial + 3 adjustments

    @pytest.mark.asyncio
    async def test_history_max_size(self):
        """Test that history is limited to max size"""
        temp = ThreadSafeTemperature(initial=37.0)

        # Make 150 adjustments (max history is 100)
        for i in range(150):
            await temp.adjust(+0.01)

        stats = await temp.get_stats()
        assert stats["history_size"] <= 100  # Should be capped

    @pytest.mark.asyncio
    async def test_concurrent_adjustments(self):
        """Test concurrent adjustments are safe"""
        temp = ThreadSafeTemperature(initial=37.0, min_temp=36.0, max_temp=42.0)

        # Run 50 concurrent small adjustments
        tasks = [temp.adjust(+0.01) for _ in range(50)]
        await asyncio.gather(*tasks)

        final_value = await temp.get()
        # Should be 37.0 + (0.01 * 50) = 37.5
        assert final_value == pytest.approx(37.5)


# ==================== THREAD-SAFE COUNTER TESTS ====================


class TestThreadSafeCounter:
    """Test thread-safe counter (defaultdict-style)"""

    @pytest.mark.asyncio
    async def test_increment_new_key(self):
        """Test incrementing a new key (starts at 0)"""
        counter = ThreadSafeCounter[str]()

        new_count = await counter.increment("threat_1")

        assert new_count == 1

    @pytest.mark.asyncio
    async def test_increment_existing_key(self):
        """Test incrementing an existing key"""
        counter = ThreadSafeCounter[str]()

        await counter.increment("threat_1")
        await counter.increment("threat_1")
        new_count = await counter.increment("threat_1")

        assert new_count == 3

    @pytest.mark.asyncio
    async def test_increment_by_delta(self):
        """Test incrementing by specific delta"""
        counter = ThreadSafeCounter[str]()

        new_count = await counter.increment("threat_1", delta=5)

        assert new_count == 5

    @pytest.mark.asyncio
    async def test_get_existing_key(self):
        """Test getting count for existing key"""
        counter = ThreadSafeCounter[str]()

        await counter.increment("threat_1", delta=10)

        count = await counter.get("threat_1")
        assert count == 10

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test getting count for nonexistent key returns 0"""
        counter = ThreadSafeCounter[str]()

        count = await counter.get("nonexistent")

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_all(self):
        """Test getting all counts"""
        counter = ThreadSafeCounter[str]()

        await counter.increment("threat_1", delta=5)
        await counter.increment("threat_2", delta=3)

        all_counts = await counter.get_all()

        assert all_counts == {"threat_1": 5, "threat_2": 3}

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing all counts"""
        counter = ThreadSafeCounter[str]()

        await counter.increment("threat_1")
        await counter.increment("threat_2")

        await counter.clear()

        all_counts = await counter.get_all()
        assert all_counts == {}

    @pytest.mark.asyncio
    async def test_items(self):
        """Test getting all items as list of tuples"""
        counter = ThreadSafeCounter[str]()

        await counter.increment("threat_1", delta=10)
        await counter.increment("threat_2", delta=20)

        items = await counter.items()

        assert set(items) == {("threat_1", 10), ("threat_2", 20)}

    @pytest.mark.asyncio
    async def test_size(self):
        """Test getting number of unique keys"""
        counter = ThreadSafeCounter[str]()

        await counter.increment("threat_1")
        await counter.increment("threat_2")
        await counter.increment("threat_1")  # Same key again

        size = await counter.size()
        assert size == 2  # Only 2 unique keys

    @pytest.mark.asyncio
    async def test_concurrent_increments_same_key(self):
        """Test concurrent increments on same key are atomic"""
        counter = ThreadSafeCounter[str]()

        # Run 100 concurrent increments on same key
        tasks = [counter.increment("threat_1") for _ in range(100)]
        await asyncio.gather(*tasks)

        final_count = await counter.get("threat_1")
        assert final_count == 100

    @pytest.mark.asyncio
    async def test_concurrent_increments_different_keys(self):
        """Test concurrent increments on different keys"""
        counter = ThreadSafeCounter[str]()

        # Increment 50 different keys concurrently
        tasks = [counter.increment(f"threat_{i}") for i in range(50)]
        await asyncio.gather(*tasks)

        size = await counter.size()
        assert size == 50

    @pytest.mark.asyncio
    async def test_generic_type_int(self):
        """Test counter with int keys"""
        counter = ThreadSafeCounter[int]()

        await counter.increment(1, delta=10)
        await counter.increment(2, delta=20)

        count1 = await counter.get(1)
        count2 = await counter.get(2)

        assert count1 == 10
        assert count2 == 20


# ==================== INTEGRATION TESTS ====================


class TestThreadSafeStructuresIntegration:
    """Test integration scenarios"""

    @pytest.mark.asyncio
    async def test_buffer_and_counter_together(self):
        """Test using buffer and counter together (realistic scenario)"""
        buffer = ThreadSafeBuffer[dict](maxsize=100)
        counter = ThreadSafeCounter[str]()

        # Simulate cytokine processing
        for i in range(10):
            cytokine = {"threat_id": f"threat_{i % 3}", "severity": 0.8}
            await buffer.append(cytokine)
            await counter.increment(cytokine["threat_id"])

        # Verify
        buffer_size = await buffer.size()
        assert buffer_size == 10

        counts = await counter.get_all()
        # threat_0, threat_1, threat_2 should each have ~3-4 detections
        assert sum(counts.values()) == 10

    @pytest.mark.asyncio
    async def test_temperature_and_counter_homeostasis(self):
        """Test temperature and counter for homeostatic regulation"""
        temp = ThreadSafeTemperature(initial=37.0, min_temp=36.0, max_temp=42.0)
        threat_counter = ThreadSafeCounter[str]()

        # Simulate threat detection increasing temperature
        for _ in range(5):
            await threat_counter.increment("active_threats")
            await temp.adjust(+0.2)  # Each threat increases temp

        current_temp = await temp.get()
        assert current_temp == pytest.approx(38.0)  # 37.0 + (0.2 * 5)

        active_threats = await threat_counter.get("active_threats")
        assert active_threats == 5

    @pytest.mark.asyncio
    async def test_all_structures_concurrent(self):
        """Test all structures under concurrent load"""
        buffer = ThreadSafeBuffer[int](maxsize=50)
        counter = AtomicCounter()
        temp = ThreadSafeTemperature(initial=37.0)
        threat_counter = ThreadSafeCounter[str]()

        async def simulate_agent_activity(agent_id: int):
            await buffer.append(agent_id)
            await counter.increment()
            await temp.adjust(+0.01)
            await threat_counter.increment(f"agent_{agent_id}")

        # Run 30 agents concurrently
        tasks = [simulate_agent_activity(i) for i in range(30)]
        await asyncio.gather(*tasks)

        # Verify all structures maintained consistency
        assert await buffer.size() == 30
        assert await counter.get() == 30
        assert await temp.get() == pytest.approx(37.3)  # 37.0 + (0.01 * 30)
        assert await threat_counter.size() == 30
