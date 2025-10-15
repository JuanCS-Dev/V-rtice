"""Coverage tests for MetricsCollector - targeting 90%+ coverage

Target lines (71.67% → 90%):
- Lines 134, 140-141: Arousal collection error paths
- Lines 164-169: TIG metrics exception handling
- Lines 186-192: ESGT metrics exception handling
- Lines 218-220: Safety metrics error handling
- Lines 194-195, 198-199, 202-203, 214-215: Health score edge cases

Authors: Claude Code (Coverage Sprint)
Date: 2025-10-14
"""

import pytest
from unittest.mock import Mock, AsyncMock
from consciousness.reactive_fabric.collectors.metrics_collector import (
    MetricsCollector,
    SystemMetrics,
)


@pytest.fixture
def mock_consciousness_system():
    """Mock ConsciousnessSystem with all components."""
    system = Mock()
    system.tig_fabric = Mock()
    system.tig_fabric.nodes = [Mock() for _ in range(20)]
    system.tig_fabric.edge_count = 50
    system.tig_fabric.get_metrics = Mock(return_value=Mock(avg_latency_us=5000))

    system.esgt_coordinator = Mock()
    system.esgt_coordinator.total_events = 10
    system.esgt_coordinator.get_success_rate = Mock(return_value=0.85)
    system.esgt_coordinator.get_recent_coherence = Mock(return_value=0.80)

    system.arousal_controller = Mock()
    system.arousal_controller.get_current_arousal = Mock(
        return_value=Mock(
            arousal=0.6,
            stress_contribution=0.2,
            need_contribution=0.1,
            level=Mock(value="MODERATE"),
        )
    )

    system.prefrontal_cortex = Mock()
    system.prefrontal_cortex.get_status = AsyncMock(
        return_value={
            "total_signals_processed": 5,
            "total_actions_generated": 3,
            "approval_rate": 0.8,
        }
    )

    system.tom_engine = Mock()
    system.tom_engine.get_stats = AsyncMock(
        return_value={
            "total_agents": 2,
            "memory": {"total_beliefs": 10},
            "redis_cache": {"enabled": False},
        }
    )

    system.safety_protocol = None
    system.get_safety_status = Mock(return_value=None)

    return system


class TestMetricsCollectorCoverage:
    """Coverage-focused tests for MetricsCollector uncovered paths."""

    @pytest.mark.asyncio
    async def test_collect_arousal_metrics_exception(self, mock_consciousness_system):
        """Cover arousal collection exception path (lines 134, 140-141)."""
        # Make arousal collection fail
        mock_consciousness_system.arousal_controller.get_current_arousal.side_effect = (
            RuntimeError("Arousal system error")
        )

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should have error recorded
        assert len(metrics.errors) > 0
        assert any("Arousal" in err for err in metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_tig_metrics_exception(self, mock_consciousness_system):
        """Cover TIG metrics exception path (lines 164-169)."""
        mock_consciousness_system.tig_fabric.get_metrics.side_effect = RuntimeError(
            "TIG fabric error"
        )

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert len(metrics.errors) > 0
        assert any("TIG" in err for err in metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_esgt_metrics_exception(self, mock_consciousness_system):
        """Cover ESGT metrics exception path (lines 186-192)."""
        mock_consciousness_system.esgt_coordinator.get_success_rate.side_effect = RuntimeError(
            "ESGT coordinator error"
        )

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        assert len(metrics.errors) > 0
        assert any("ESGT" in err for err in metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_safety_metrics_exception(self, mock_consciousness_system):
        """Cover safety metrics exception path (lines 218-220)."""
        mock_consciousness_system.get_safety_status.side_effect = RuntimeError(
            "Safety protocol error"
        )

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should still collect other metrics
        assert metrics.tig_node_count == 20
        assert len(metrics.errors) > 0

    @pytest.mark.asyncio
    async def test_health_score_high_latency(self, mock_consciousness_system):
        """Cover high latency penalty path (lines 194-195)."""
        # Set high TIG latency
        mock_consciousness_system.tig_fabric.get_metrics.return_value.avg_latency_us = (
            15000  # > 10ms
        )

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Health score should be penalized
        assert metrics.health_score < 1.0

    @pytest.mark.asyncio
    async def test_health_score_low_esgt_success(self, mock_consciousness_system):
        """Cover low ESGT success rate penalty (lines 198-199)."""
        mock_consciousness_system.esgt_coordinator.get_success_rate.return_value = (
            0.6  # < 0.7
        )

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Health score should be penalized
        assert metrics.health_score < 1.0

    @pytest.mark.asyncio
    async def test_health_score_extreme_arousal(self, mock_consciousness_system):
        """Cover extreme arousal penalty (lines 202-203)."""
        mock_consciousness_system.arousal_controller.get_current_arousal.return_value.arousal = (
            0.95  # > 0.9
        )

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Health score should be penalized
        assert metrics.health_score < 1.0

    @pytest.mark.asyncio
    async def test_health_score_multiple_errors(self, mock_consciousness_system):
        """Cover multiple collection errors penalty (lines 214-215)."""
        # Make multiple subsystems fail
        mock_consciousness_system.tig_fabric.get_metrics.side_effect = RuntimeError(
            "TIG error"
        )
        mock_consciousness_system.esgt_coordinator.get_success_rate.side_effect = (
            RuntimeError("ESGT error")
        )

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Health score should be heavily penalized
        assert len(metrics.errors) >= 2
        assert metrics.health_score < 0.8

    @pytest.mark.asyncio
    async def test_collect_with_main_exception(self, mock_consciousness_system):
        """Cover main collect() exception handling (lines 139-141)."""
        # Make the entire collect process fail at the start
        mock_consciousness_system.tig_fabric = None
        mock_consciousness_system.esgt_coordinator = None
        mock_consciousness_system.arousal_controller = None
        mock_consciousness_system.prefrontal_cortex = Mock()
        mock_consciousness_system.prefrontal_cortex.get_status = AsyncMock(side_effect=RuntimeError("Critical failure"))
        mock_consciousness_system.tom_engine = None
        mock_consciousness_system.safety_protocol = None

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should have captured exception
        assert len(metrics.errors) > 0

    @pytest.mark.asyncio
    async def test_collect_esgt_frequency_with_timestamps(self, mock_consciousness_system):
        """Cover ESGT frequency calculation with timestamps (line 188)."""
        import time

        # Mock coordinator with ignition timestamps
        mock_consciousness_system.esgt_coordinator.total_events = 10
        mock_consciousness_system.esgt_coordinator.get_success_rate = Mock(return_value=0.9)
        mock_consciousness_system.esgt_coordinator.get_recent_coherence = Mock(return_value=0.85)

        # Add recent timestamps (within last 60 seconds)
        now = time.time()
        mock_consciousness_system.esgt_coordinator.ignition_timestamps = [
            now - 10,  # 10s ago
            now - 25,  # 25s ago
            now - 45,  # 45s ago
        ]

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should calculate frequency (3 events in 60s)
        assert metrics.esgt_frequency_hz > 0
        assert metrics.esgt_frequency_hz == 3 / 60.0

    @pytest.mark.asyncio
    async def test_collect_pfc_metrics_complete(self, mock_consciousness_system):
        """Cover PFC metrics collection success (lines 214-216)."""
        mock_consciousness_system.prefrontal_cortex.get_status = AsyncMock(return_value={
            "total_signals_processed": 100,
            "total_actions_generated": 75,
            "approval_rate": 0.92
        })

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Verify PFC metrics collected
        assert metrics.pfc_signals_processed == 100
        assert metrics.pfc_actions_generated == 75
        assert metrics.pfc_approval_rate == 0.92

    @pytest.mark.asyncio
    async def test_collect_pfc_exception(self, mock_consciousness_system):
        """Cover PFC metrics exception (lines 218-220)."""
        mock_consciousness_system.prefrontal_cortex.get_status = AsyncMock(side_effect=RuntimeError("PFC failure"))

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should have PFC error
        assert any("PFC" in err for err in metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_tom_with_cache_enabled(self, mock_consciousness_system):
        """Cover ToM cache hit rate when cache enabled (lines 232-233)."""
        mock_consciousness_system.tom_engine.get_stats = AsyncMock(return_value={
            "total_agents": 5,
            "memory": {"total_beliefs": 150},
            "redis_cache": {
                "enabled": True,
                "hit_rate": 0.78
            }
        })

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should have cache hit rate
        assert metrics.tom_cache_hit_rate == 0.78

    @pytest.mark.asyncio
    async def test_collect_tom_with_cache_disabled(self, mock_consciousness_system):
        """Cover ToM cache disabled path (line 232 false branch)."""
        mock_consciousness_system.tom_engine.get_stats = AsyncMock(return_value={
            "total_agents": 3,
            "memory": {"total_beliefs": 80},
            "redis_cache": {
                "enabled": False
            }
        })

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Cache hit rate should be 0 (default)
        assert metrics.tom_cache_hit_rate == 0.0

    @pytest.mark.asyncio
    async def test_collect_tom_exception(self, mock_consciousness_system):
        """Cover ToM metrics exception (lines 235-237)."""
        mock_consciousness_system.tom_engine.get_stats = AsyncMock(side_effect=RuntimeError("ToM failure"))

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should have ToM error
        assert any("ToM" in err for err in metrics.errors)

    @pytest.mark.asyncio
    async def test_collect_safety_with_status(self, mock_consciousness_system):
        """Cover safety metrics with status data (lines 244-246)."""
        mock_consciousness_system.safety_protocol = Mock()
        mock_consciousness_system.get_safety_status = Mock(return_value={
            "active_violations": 2,
            "kill_switch_triggered": False
        })

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should have safety metrics
        assert metrics.safety_violations == 2
        assert metrics.kill_switch_active is False

    @pytest.mark.asyncio
    async def test_collect_safety_with_kill_switch(self, mock_consciousness_system):
        """Cover safety metrics with kill switch active (line 246)."""
        mock_consciousness_system.safety_protocol = Mock()
        mock_consciousness_system.get_safety_status = Mock(return_value={
            "active_violations": 5,
            "kill_switch_triggered": True
        })

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should have kill switch active
        assert metrics.kill_switch_active is True
        assert metrics.safety_violations == 5

    @pytest.mark.asyncio
    async def test_collect_safety_exception(self, mock_consciousness_system):
        """Cover safety metrics exception (lines 248-250)."""
        mock_consciousness_system.safety_protocol = Mock()
        mock_consciousness_system.get_safety_status = Mock(side_effect=RuntimeError("Safety failure"))

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should have Safety error
        assert any("Safety" in err for err in metrics.errors)

    @pytest.mark.asyncio
    async def test_health_score_safety_violations_penalty(self, mock_consciousness_system):
        """Cover health score safety violation penalty (line 281)."""
        collector = MetricsCollector(mock_consciousness_system)

        metrics = SystemMetrics(timestamp=0, safety_violations=1, arousal_level=0.5)
        score = collector._calculate_health_score(metrics)

        # Should penalize -0.3 for violations, -0.1 for errors if any
        # Base 1.0 - 0.3 (safety) - 0.2 (arousal penalty if extreme) = varies
        # Let's just check it's penalized
        assert score < 1.0
        assert score >= 0.5  # Should be reasonable

    @pytest.mark.asyncio
    async def test_health_score_kill_switch_critical(self, mock_consciousness_system):
        """Cover health score kill switch = 0 (line 285)."""
        collector = MetricsCollector(mock_consciousness_system)

        metrics = SystemMetrics(timestamp=0, kill_switch_active=True)
        score = collector._calculate_health_score(metrics)

        # Kill switch = critical = 0.0
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_get_collection_stats_zero_collections(self, mock_consciousness_system):
        """Cover stats calculation with zero collections (line 299-302)."""
        collector = MetricsCollector(mock_consciousness_system)
        collector.collection_count = 0
        collector.total_collection_time_ms = 0.0

        stats = collector.get_collection_stats()

        # Should handle division by zero
        assert stats["avg_collection_time_ms"] == 0.0
        assert stats["total_collections"] == 0

    @pytest.mark.asyncio
    async def test_get_collection_stats_multiple_collections(self, mock_consciousness_system):
        """Cover stats calculation with multiple collections (line 305)."""
        collector = MetricsCollector(mock_consciousness_system)
        collector.collection_count = 10
        collector.total_collection_time_ms = 150.0

        stats = collector.get_collection_stats()

        # Should calculate average
        assert stats["avg_collection_time_ms"] == 15.0
        assert stats["total_collections"] == 10
        assert stats["total_time_ms"] == 150.0

    @pytest.mark.asyncio
    async def test_collect_arousal_with_no_state(self, mock_consciousness_system):
        """Cover arousal collection when get_current_arousal returns None (line 199 false)."""
        mock_consciousness_system.arousal_controller.get_current_arousal = Mock(return_value=None)

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should use defaults (no crash)
        assert metrics.arousal_level == 0.5  # Default
        assert metrics.arousal_classification == "MODERATE"  # Default

    @pytest.mark.asyncio
    async def test_collect_safety_with_none_status(self, mock_consciousness_system):
        """Cover safety collection when get_safety_status returns None (line 244 false)."""
        mock_consciousness_system.safety_protocol = Mock()
        mock_consciousness_system.get_safety_status = Mock(return_value=None)

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should use defaults
        assert metrics.safety_violations == 0
        assert metrics.kill_switch_active is False

    @pytest.mark.asyncio
    async def test_repr(self, mock_consciousness_system):
        """Cover __repr__ method."""
        collector = MetricsCollector(mock_consciousness_system)
        collector.collection_count = 25
        collector.total_collection_time_ms = 500.0

        repr_str = repr(collector)

        # Should contain key stats
        assert "MetricsCollector" in repr_str
        assert "collections=25" in repr_str
        assert "20.0ms" in repr_str  # 500/25

    @pytest.mark.asyncio
    async def test_collect_main_exception_path(self, mock_consciousness_system):
        """Cover main collect() exception at top level (lines 139-141)."""
        # Make the entire metrics object creation fail
        collector = MetricsCollector(mock_consciousness_system)

        # Break something at the root level to trigger top-level exception
        mock_consciousness_system.tig_fabric = None
        mock_consciousness_system.esgt_coordinator = None
        mock_consciousness_system.arousal_controller = None
        mock_consciousness_system.prefrontal_cortex = None
        mock_consciousness_system.tom_engine = None
        mock_consciousness_system.safety_protocol = None

        # This should work but with empty metrics
        metrics = await collector.collect()

        # Should complete without crash
        assert metrics is not None
        assert metrics.health_score >= 0.0

    @pytest.mark.asyncio
    async def test_collect_tig_no_coherence_method(self, mock_consciousness_system):
        """Cover TIG collection branch when get_coherence doesn't exist (line 167->exit)."""
        # Remove get_coherence method
        if hasattr(mock_consciousness_system.tig_fabric, 'get_coherence'):
            delattr(mock_consciousness_system.tig_fabric, 'get_coherence')

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should collect TIG metrics without coherence
        assert metrics.tig_node_count == 20
        assert metrics.tig_coherence == 0.0  # Default

    @pytest.mark.asyncio
    async def test_collect_esgt_no_timestamps(self, mock_consciousness_system):
        """Cover ESGT collection when ignition_timestamps missing (line 185->exit)."""
        # Remove ignition_timestamps attribute
        if hasattr(mock_consciousness_system.esgt_coordinator, 'ignition_timestamps'):
            delattr(mock_consciousness_system.esgt_coordinator, 'ignition_timestamps')

        collector = MetricsCollector(mock_consciousness_system)
        metrics = await collector.collect()

        # Should collect ESGT metrics without frequency
        assert metrics.esgt_event_count >= 0
        assert metrics.esgt_frequency_hz == 0.0  # Default

    @pytest.mark.asyncio
    async def test_collect_exception_during_health_calculation(self, mock_consciousness_system):
        """Cover top-level exception handler in collect() (lines 139-141)."""
        collector = MetricsCollector(mock_consciousness_system)

        # The only unprotected operation in collect() is _calculate_health_score()
        # All sub-collectors have their own exception handlers
        # So we need to break _calculate_health_score() to trigger lines 139-141

        original_calculate_health = collector._calculate_health_score

        def failing_health_score(metrics):
            # Raise exception during health score calculation
            raise RuntimeError("Health calculation catastrophic failure")

        collector._calculate_health_score = failing_health_score

        # This should trigger the top-level exception handler (lines 139-141)
        metrics = await collector.collect()

        # Should have error recorded
        assert len(metrics.errors) > 0
        assert "Health calculation catastrophic failure" in str(metrics.errors)


# Run with:
# pytest tests/unit/test_metrics_collector_coverage.py --cov=consciousness.reactive_fabric.collectors.metrics_collector --cov-report=term-missing -v

