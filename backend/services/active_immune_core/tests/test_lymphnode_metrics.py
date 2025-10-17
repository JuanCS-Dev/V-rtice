"""Tests for LymphnodeMetrics - Metrics Collection and Reporting

FASE 3 SPRINT 5: Test suite for lymphnode metrics including threat counting,
neutralization tracking, clonal expansion statistics, and reporting.

Test Structure:
- TestLymphnodeMetricsLifecycle (3 tests)
- TestThreatAndNeutralizationMetrics (5 tests)
- TestClonalExpansionMetrics (5 tests)
- TestMetricsCalculations (3 tests)
- TestStatistics (2 tests)

Total: 18 tests

NO MOCK, NO PLACEHOLDER, NO TODO - Production ready.
DOUTRINA VERTICE compliant: Quality-first, production-ready code.

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

import pytest

from active_immune_core.coordination.lymphnode_metrics import LymphnodeMetrics

# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def metrics():
    """Create a LymphnodeMetrics instance."""
    return LymphnodeMetrics(lymphnode_id="lymph-test-1")


# =============================================================================
# TEST LIFECYCLE
# =============================================================================


class TestLymphnodeMetricsLifecycle:
    """Test LymphnodeMetrics initialization and configuration."""

    def test_initialization(self):
        """Test initialization."""
        metrics = LymphnodeMetrics(lymphnode_id="lymph-1")
        assert metrics.lymphnode_id == "lymph-1"

    @pytest.mark.asyncio
    async def test_initial_counters_zero(self, metrics):
        """Test all counters start at zero."""
        assert await metrics.get_threats_detected() == 0
        assert await metrics.get_neutralizations() == 0
        assert await metrics.get_clones_created() == 0
        assert await metrics.get_clones_destroyed() == 0

    def test_repr(self, metrics):
        """Test string representation."""
        repr_str = repr(metrics)
        assert "LymphnodeMetrics" in repr_str
        assert "lymph-test-1" in repr_str


# =============================================================================
# TEST THREAT AND NEUTRALIZATION METRICS
# =============================================================================


class TestThreatAndNeutralizationMetrics:
    """Test threat detection and neutralization counting."""

    @pytest.mark.asyncio
    async def test_increment_threats_detected(self, metrics):
        """Test incrementing threats detected."""
        count = await metrics.increment_threats_detected()
        assert count == 1

        count = await metrics.increment_threats_detected()
        assert count == 2

    @pytest.mark.asyncio
    async def test_increment_threats_detected_multiple(self, metrics):
        """Test incrementing threats by multiple."""
        count = await metrics.increment_threats_detected(count=5)
        assert count == 5

    @pytest.mark.asyncio
    async def test_increment_neutralizations(self, metrics):
        """Test incrementing neutralizations."""
        count = await metrics.increment_neutralizations()
        assert count == 1

        count = await metrics.increment_neutralizations()
        assert count == 2

    @pytest.mark.asyncio
    async def test_increment_neutralizations_multiple(self, metrics):
        """Test incrementing neutralizations by multiple."""
        count = await metrics.increment_neutralizations(count=3)
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_threats_and_neutralizations(self, metrics):
        """Test getting threat and neutralization counts."""
        await metrics.increment_threats_detected(count=10)
        await metrics.increment_neutralizations(count=7)

        threats = await metrics.get_threats_detected()
        neutralizations = await metrics.get_neutralizations()

        assert threats == 10
        assert neutralizations == 7


# =============================================================================
# TEST CLONAL EXPANSION METRICS
# =============================================================================


class TestClonalExpansionMetrics:
    """Test clonal expansion metrics."""

    @pytest.mark.asyncio
    async def test_increment_clones_created(self, metrics):
        """Test incrementing clones created."""
        count = await metrics.increment_clones_created()
        assert count == 1

        count = await metrics.increment_clones_created(count=4)
        assert count == 5

    @pytest.mark.asyncio
    async def test_increment_clones_destroyed(self, metrics):
        """Test incrementing clones destroyed."""
        count = await metrics.increment_clones_destroyed()
        assert count == 1

        count = await metrics.increment_clones_destroyed(count=2)
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_clones_created_and_destroyed(self, metrics):
        """Test getting clone creation and destruction counts."""
        await metrics.increment_clones_created(count=15)
        await metrics.increment_clones_destroyed(count=5)

        created = await metrics.get_clones_created()
        destroyed = await metrics.get_clones_destroyed()

        assert created == 15
        assert destroyed == 5

    @pytest.mark.asyncio
    async def test_get_net_clones_positive(self, metrics):
        """Test net clones (positive)."""
        await metrics.increment_clones_created(count=20)
        await metrics.increment_clones_destroyed(count=8)

        net = await metrics.get_net_clones()
        assert net == 12

    @pytest.mark.asyncio
    async def test_get_net_clones_negative(self, metrics):
        """Test net clones (negative, more destroyed than created)."""
        await metrics.increment_clones_created(count=5)
        await metrics.increment_clones_destroyed(count=10)

        net = await metrics.get_net_clones()
        assert net == -5


# =============================================================================
# TEST METRICS CALCULATIONS
# =============================================================================


class TestMetricsCalculations:
    """Test derived metrics calculations."""

    @pytest.mark.asyncio
    async def test_neutralization_rate_perfect(self, metrics):
        """Test neutralization rate (100%)."""
        await metrics.increment_threats_detected(count=10)
        await metrics.increment_neutralizations(count=10)

        rate = await metrics.get_neutralization_rate()
        assert rate == 1.0

    @pytest.mark.asyncio
    async def test_neutralization_rate_partial(self, metrics):
        """Test neutralization rate (partial)."""
        await metrics.increment_threats_detected(count=10)
        await metrics.increment_neutralizations(count=7)

        rate = await metrics.get_neutralization_rate()
        assert rate == 0.7

    @pytest.mark.asyncio
    async def test_neutralization_rate_zero_threats(self, metrics):
        """Test neutralization rate with zero threats."""
        rate = await metrics.get_neutralization_rate()
        assert rate == 0.0


# =============================================================================
# TEST STATISTICS
# =============================================================================


class TestStatistics:
    """Test statistics collection and reporting."""

    @pytest.mark.asyncio
    async def test_get_stats_all_fields(self, metrics):
        """Test get_stats returns all fields."""
        await metrics.increment_threats_detected(count=20)
        await metrics.increment_neutralizations(count=15)
        await metrics.increment_clones_created(count=30)
        await metrics.increment_clones_destroyed(count=10)

        stats = await metrics.get_stats()

        assert "lymphnode_id" in stats
        assert "total_threats_detected" in stats
        assert "total_neutralizations" in stats
        assert "total_clones_created" in stats
        assert "total_clones_destroyed" in stats
        assert "net_clones" in stats
        assert "neutralization_rate" in stats

        assert stats["lymphnode_id"] == "lymph-test-1"
        assert stats["total_threats_detected"] == 20
        assert stats["total_neutralizations"] == 15
        assert stats["total_clones_created"] == 30
        assert stats["total_clones_destroyed"] == 10
        assert stats["net_clones"] == 20
        assert stats["neutralization_rate"] == 0.75

    @pytest.mark.asyncio
    async def test_reset_all(self, metrics):
        """Test resetting all counters."""
        # Set some values
        await metrics.increment_threats_detected(count=10)
        await metrics.increment_neutralizations(count=5)
        await metrics.increment_clones_created(count=15)
        await metrics.increment_clones_destroyed(count=3)

        # Reset
        await metrics.reset_all()

        # Verify all zeroed
        assert await metrics.get_threats_detected() == 0
        assert await metrics.get_neutralizations() == 0
        assert await metrics.get_clones_created() == 0
        assert await metrics.get_clones_destroyed() == 0
