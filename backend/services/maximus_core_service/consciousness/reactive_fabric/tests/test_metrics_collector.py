"""Tests for MetricsCollector - Reactive Fabric Sprint 3.

Target: 100% statement + branch coverage.

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
from unittest.mock import MagicMock

from consciousness.reactive_fabric.collectors.metrics_collector import (
    MetricsCollector,
    SystemMetrics,
)


class TestSystemMetrics:
    """Test SystemMetrics dataclass."""

    def test_system_metrics_creation(self):
        """Test creating SystemMetrics with all fields."""
        metrics = SystemMetrics(
            timestamp=1234567890.0,
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        assert metrics.tig_node_count == 10
        assert metrics.tig_edge_count == 25
        assert metrics.health_score == 0.85
        assert metrics.errors == []


class TestMetricsCollectorInit:
    """Test MetricsCollector initialization."""

    def test_init_with_default_params(self, mock_consciousness_system):
        """Test MetricsCollector initialization with default params."""
        collector = MetricsCollector(mock_consciousness_system)

        assert collector.system == mock_consciousness_system
        assert collector.collection_count == 0
        assert collector.total_collection_time_ms == 0.0


class TestMetricsCollectorCollect:
    """Test MetricsCollector.collect() method."""

    @pytest.mark.asyncio
    async def test_collect_success(self, mock_consciousness_system):
        """Test successful metrics collection."""
        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert isinstance(metrics, SystemMetrics)
        assert collector.collection_count == 1
        assert metrics.timestamp > 0
        assert metrics.tig_node_count == 10
        assert metrics.tig_edge_count == 25

    @pytest.mark.asyncio
    async def test_collect_multiple_times(self, mock_consciousness_system):
        """Test collecting metrics multiple times."""
        collector = MetricsCollector(mock_consciousness_system)

        metrics1 = await collector.collect()
        metrics2 = await collector.collect()

        assert collector.collection_count == 2
        assert metrics1.timestamp < metrics2.timestamp

    @pytest.mark.asyncio
    async def test_collect_with_tig_exception(self, mock_consciousness_system):
        """Test collection when TIG raises exception."""
        mock_consciousness_system.tig_fabric.get_metrics.side_effect = Exception("TIG error")

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should still complete but record errors
        assert isinstance(metrics, SystemMetrics)
        assert "TIG" in "".join(metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_with_esgt_exception(self, mock_consciousness_system):
        """Test collection when ESGT raises exception."""
        mock_consciousness_system.esgt_coordinator.get_success_rate.side_effect = Exception("ESGT error")

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert "ESGT" in "".join(metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_with_arousal_exception(self, mock_consciousness_system):
        """Test collection when Arousal raises exception."""
        mock_consciousness_system.arousal_controller.get_current_arousal.side_effect = Exception("Arousal error")

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert "Arousal" in "".join(metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_with_pfc_exception(self, mock_consciousness_system):
        """Test collection when PFC raises exception."""
        mock_consciousness_system.prefrontal_cortex.get_status.side_effect = Exception("PFC error")

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert "PFC" in "".join(metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_with_tom_exception(self, mock_consciousness_system):
        """Test collection when ToM raises exception."""
        mock_consciousness_system.tom_engine.get_stats.side_effect = Exception("ToM error")

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert "ToM" in "".join(metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_with_safety_exception(self, mock_consciousness_system):
        """Test collection when Safety raises exception."""
        mock_consciousness_system.get_safety_status.side_effect = Exception("Safety error")

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert "Safety" in "".join(metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_with_top_level_exception(self, mock_consciousness_system):
        """Test collection when top-level exception occurs."""
        # Force error at collection level
        mock_consciousness_system.tig_fabric = None

        collector = MetricsCollector(mock_consciousness_system)
        # Manually inject error
        collector.system.tig_fabric = MagicMock()
        collector.system.tig_fabric.__bool__ = lambda x: (_ for _ in ()).throw(Exception("Critical"))

        metrics = await collector.collect()
        # Should handle gracefully
        assert isinstance(metrics, SystemMetrics)


class TestHealthScoreCalculation:
    """Test _calculate_health_score() method."""

    @pytest.mark.asyncio
    async def test_health_score_healthy_system(self, mock_consciousness_system):
        """Test health score calculation for healthy system."""
        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Healthy system should have high health score
        assert metrics.health_score > 0.7

    @pytest.mark.asyncio
    async def test_health_score_high_latency_penalty(self, mock_consciousness_system):
        """Test that high latency reduces health score."""
        mock_metrics = MagicMock()
        mock_metrics.avg_latency_us = 15000.0  # > 10000 triggers penalty
        mock_consciousness_system.tig_fabric.get_metrics.return_value = mock_metrics

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Health should be penalized
        assert metrics.health_score < 0.9

    @pytest.mark.asyncio
    async def test_health_score_low_esgt_success_penalty(self, mock_consciousness_system):
        """Test that low ESGT success rate reduces health score."""
        mock_consciousness_system.esgt_coordinator.get_success_rate.return_value = 0.60

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert metrics.health_score < 0.9

    @pytest.mark.asyncio
    async def test_health_score_low_arousal_penalty(self, mock_consciousness_system):
        """Test that low arousal reduces health score."""
        arousal_state = MagicMock()
        arousal_state.arousal = 0.1  # < 0.2 triggers penalty
        arousal_state.level = MagicMock()
        arousal_state.level.value = "LOW"
        arousal_state.stress_contribution = 0.1
        arousal_state.need_contribution = 0.1
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = arousal_state

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert metrics.health_score < 1.0

    @pytest.mark.asyncio
    async def test_health_score_high_arousal_penalty(self, mock_consciousness_system):
        """Test that high arousal reduces health score."""
        arousal_state = MagicMock()
        arousal_state.arousal = 0.95  # > 0.9 triggers penalty
        arousal_state.level = MagicMock()
        arousal_state.level.value = "EXTREME"
        arousal_state.stress_contribution = 0.9
        arousal_state.need_contribution = 0.1
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = arousal_state

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert metrics.health_score < 1.0

    @pytest.mark.asyncio
    async def test_health_score_safety_violations_penalty(self, mock_consciousness_system):
        """Test that safety violations reduce health score."""
        mock_consciousness_system.get_safety_status.return_value = {
            "active_violations": 2,
            "kill_switch_triggered": False,
        }

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert metrics.health_score < 0.8

    @pytest.mark.asyncio
    async def test_health_score_kill_switch_critical(self, mock_consciousness_system):
        """Test that kill switch sets health to 0."""
        mock_consciousness_system.get_safety_status.return_value = {
            "active_violations": 5,
            "kill_switch_triggered": True,
        }

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Kill switch should cause zero health
        assert metrics.health_score == 0.0

    @pytest.mark.asyncio
    async def test_health_score_collection_errors_penalty(self, mock_consciousness_system):
        """Test that collection errors reduce health score."""
        # Force multiple subsystem errors
        mock_consciousness_system.tig_fabric.get_metrics.side_effect = Exception("TIG error")
        mock_consciousness_system.esgt_coordinator.get_success_rate.side_effect = Exception("ESGT error")

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Multiple errors should reduce health
        assert len(metrics.errors) >= 2
        assert metrics.health_score < 0.9


class TestCollectionStats:
    """Test get_collection_stats() method."""

    @pytest.mark.asyncio
    async def test_get_collection_stats_initial(self, mock_consciousness_system):
        """Test stats retrieval before any collections."""
        collector = MetricsCollector(mock_consciousness_system)
        stats = collector.get_collection_stats()

        assert stats["total_collections"] == 0
        assert stats["avg_collection_time_ms"] == 0.0

    @pytest.mark.asyncio
    async def test_get_collection_stats_after_collections(self, mock_consciousness_system):
        """Test stats retrieval after collections."""
        collector = MetricsCollector(mock_consciousness_system)

        await collector.collect()
        await collector.collect()

        stats = collector.get_collection_stats()

        assert stats["total_collections"] == 2
        assert stats["avg_collection_time_ms"] > 0


class TestRepr:
    """Test __repr__() method."""

    def test_repr(self, mock_consciousness_system):
        """Test string representation."""
        collector = MetricsCollector(mock_consciousness_system)

        repr_str = repr(collector)

        assert "MetricsCollector" in repr_str
        assert "collections=0" in repr_str


class TestBranchCoverage:
    """Tests to cover remaining branches."""

    @pytest.mark.asyncio
    async def test_tig_no_get_coherence(self, mock_consciousness_system):
        """Test TIG metrics when get_coherence doesn't exist."""
        del mock_consciousness_system.tig_fabric.get_coherence

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should handle missing get_coherence gracefully
        assert isinstance(metrics, SystemMetrics)

    @pytest.mark.asyncio
    async def test_tig_get_coherence_returns_none(self, mock_consciousness_system):
        """Test TIG metrics when get_coherence returns None."""
        mock_consciousness_system.tig_fabric.get_coherence.return_value = None

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert metrics.tig_coherence == 0.0

    @pytest.mark.asyncio
    async def test_esgt_no_ignition_timestamps(self, mock_consciousness_system):
        """Test ESGT metrics when no ignition_timestamps attribute."""
        del mock_consciousness_system.esgt_coordinator.ignition_timestamps

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should handle missing attribute
        assert isinstance(metrics, SystemMetrics)

    @pytest.mark.asyncio
    async def test_esgt_empty_ignition_timestamps(self, mock_consciousness_system):
        """Test ESGT metrics when ignition_timestamps is empty."""
        mock_consciousness_system.esgt_coordinator.ignition_timestamps = []

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert metrics.esgt_frequency_hz == 0.0

    @pytest.mark.asyncio
    async def test_arousal_returns_none(self, mock_consciousness_system):
        """Test arousal metrics when get_current_arousal returns None."""
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value = None

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should use default arousal values
        assert isinstance(metrics, SystemMetrics)

    @pytest.mark.asyncio
    async def test_safety_status_returns_none(self, mock_consciousness_system):
        """Test safety metrics when get_safety_status returns None."""
        mock_consciousness_system.get_safety_status.return_value = None

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should handle None safety status
        assert isinstance(metrics, SystemMetrics)

    @pytest.mark.asyncio
    async def test_tom_redis_disabled(self, mock_consciousness_system):
        """Test ToM metrics when Redis cache is disabled."""
        mock_consciousness_system.tom_engine.get_stats.return_value = {
            "total_agents": 5,
            "memory": {"total_beliefs": 25},
            "redis_cache": {"enabled": False},
        }

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should not set cache hit rate when disabled
        assert metrics.tom_cache_hit_rate == 0.0

    @pytest.mark.asyncio
    async def test_subsystem_is_none(self, mock_consciousness_system):
        """Test collection when some subsystems are None."""
        mock_consciousness_system.prefrontal_cortex = None
        mock_consciousness_system.tom_engine = None

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should skip None subsystems
        assert isinstance(metrics, SystemMetrics)
        assert metrics.pfc_signals_processed == 0
        assert metrics.tom_total_agents == 0

    @pytest.mark.asyncio
    async def test_all_subsystems_none(self, mock_consciousness_system):
        """Test collection when all optional subsystems are None."""
        mock_consciousness_system.tig_fabric = None
        mock_consciousness_system.esgt_coordinator = None
        mock_consciousness_system.arousal_controller = None
        mock_consciousness_system.prefrontal_cortex = None
        mock_consciousness_system.tom_engine = None
        mock_consciousness_system.safety_protocol = None

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should handle all None subsystems - may have errors penalty
        assert isinstance(metrics, SystemMetrics)
        assert 0 <= metrics.health_score <= 1.0
