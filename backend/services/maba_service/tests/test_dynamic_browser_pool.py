"""Tests for Dynamic Browser Pool - Auto-scaling browser management."""

import pytest
from core.dynamic_browser_pool import DynamicBrowserPool


@pytest.fixture
async def pool():
    """Create dynamic browser pool."""
    p = DynamicBrowserPool(min_instances=2, max_instances=10, scale_check_interval=1)
    await p.initialize()
    yield p
    await p.shutdown()


class TestInitialization:
    @pytest.mark.asyncio
    async def test_initialize_creates_min_instances(self, pool):
        """GIVEN: Pool with min_instances=2.

        WHEN: initialize() called
        THEN: Creates 2 instances.
        """
        assert len(pool.instances) == 2
        assert pool._initialized is True


class TestInstanceSelection:
    @pytest.mark.asyncio
    async def test_get_instance_returns_least_loaded(self, pool):
        """GIVEN: Multiple instances with different loads.

        WHEN: get_instance() called
        THEN: Returns instance with lowest session count.
        """
        pool.instances[0].session_count = 5
        pool.instances[1].session_count = 2

        # Disable auto-scaling for this test
        pool.scale_up_threshold = 999

        instance = await pool.get_instance()
        assert instance.session_count in (0, 2)  # Could be 2 or newly scaled instance


class TestScaling:
    @pytest.mark.asyncio
    async def test_scale_up_adds_instances(self, pool):
        """GIVEN: Pool with 2 instances.

        WHEN: _scale_up(3) called
        THEN: Adds 3 instances.
        """
        initial_count = len(pool.instances)
        await pool._scale_up(3)
        assert len(pool.instances) == initial_count + 3

    @pytest.mark.asyncio
    async def test_scale_down_removes_idle_instances(self, pool):
        """GIVEN: Pool with idle instances.

        WHEN: _scale_down() called
        THEN: Removes instances with no sessions.
        """
        await pool._scale_up(2)  # Add 2 more
        initial_count = len(pool.instances)

        await pool._scale_down(1)
        assert len(pool.instances) == initial_count - 1


class TestMetrics:
    @pytest.mark.asyncio
    async def test_update_instance_metrics(self, pool):
        """GIVEN: Instance exists.

        WHEN: update_instance_metrics() called
        THEN: Updates CPU and memory.
        """
        instance_id = pool.instances[0].instance_id
        await pool.update_instance_metrics(instance_id, cpu=75.5, memory=512.0)

        assert pool.instances[0].cpu_usage == 75.5
        assert pool.instances[0].memory_usage == 512.0

    @pytest.mark.asyncio
    async def test_get_stats(self, pool):
        """GIVEN: Pool with instances.

        WHEN: get_stats() called
        THEN: Returns metrics dict.
        """
        stats = await pool.get_stats()

        assert "instances" in stats
        assert "total_sessions" in stats
        assert "avg_cpu" in stats
        assert stats["instances"] == 2


class TestSessionCounting:
    @pytest.mark.asyncio
    async def test_increment_session_count(self, pool):
        """GIVEN: Instance with 0 sessions.

        WHEN: increment_session_count() called
        THEN: Increments count.
        """
        instance_id = pool.instances[0].instance_id
        await pool.increment_session_count(instance_id)

        assert pool.instances[0].session_count == 1

    @pytest.mark.asyncio
    async def test_decrement_session_count(self, pool):
        """GIVEN: Instance with 1 session.

        WHEN: decrement_session_count() called
        THEN: Decrements count.
        """
        instance_id = pool.instances[0].instance_id
        pool.instances[0].session_count = 1

        await pool.decrement_session_count(instance_id)
        assert pool.instances[0].session_count == 0
