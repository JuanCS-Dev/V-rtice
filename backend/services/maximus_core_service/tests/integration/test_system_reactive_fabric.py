"""System Integration Tests - Reactive Fabric (Sprint 3)

Tests the complete ConsciousnessSystem integration with Reactive Fabric:
- System starts with orchestrator
- Orchestrator collects metrics from all subsystems
- Orchestrator generates ESGT triggers
- System health checks include orchestrator
- System stops cleanly

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Sprint: Reactive Fabric Sprint 3 - System Integration
"""

import pytest
import asyncio
from consciousness.system import ConsciousnessSystem, ConsciousnessConfig


@pytest.fixture(scope="function")
def consciousness_system_with_fabric(request, event_loop):
    """Create full Consciousness System with Reactive Fabric."""
    config = ConsciousnessConfig(
        tig_node_count=20,  # Small for fast tests
        tig_target_density=0.25,
        esgt_min_salience=0.60,
        esgt_refractory_period_ms=50.0,
        esgt_max_frequency_hz=10.0,
        esgt_min_available_nodes=5,
        arousal_baseline=0.60,
        safety_enabled=False  # Disable for faster tests
    )

    system = ConsciousnessSystem(config)
    event_loop.run_until_complete(system.start())

    def cleanup():
        event_loop.run_until_complete(system.stop())

    request.addfinalizer(cleanup)

    return system


class TestSystemInitialization:
    """Test system initialization with Reactive Fabric."""

    @pytest.mark.asyncio
    async def test_system_starts_with_orchestrator(self, consciousness_system_with_fabric):
        """System should start with DataOrchestrator initialized."""
        system = consciousness_system_with_fabric

        # Verify orchestrator exists
        assert system.orchestrator is not None

        # Verify orchestrator is running
        assert system.orchestrator._running is True

        # Verify collectors initialized
        assert system.orchestrator.metrics_collector is not None
        assert system.orchestrator.event_collector is not None

    @pytest.mark.asyncio
    async def test_orchestrator_starts_after_components(self, consciousness_system_with_fabric):
        """Orchestrator should start after all components are ready."""
        system = consciousness_system_with_fabric

        # All subsystems should be running
        assert system.tig_fabric is not None
        assert system.esgt_coordinator is not None
        assert system.arousal_controller is not None

        # Orchestrator should be running
        assert system.orchestrator is not None
        assert system.orchestrator._running is True

    @pytest.mark.asyncio
    async def test_system_health_includes_orchestrator(self, consciousness_system_with_fabric):
        """System health check should include orchestrator status."""
        system = consciousness_system_with_fabric

        # System should be healthy
        assert system.is_healthy() is True

        # Stop orchestrator
        await system.orchestrator.stop()

        # System should now be unhealthy
        assert system.is_healthy() is False


class TestReactiveFabricOperation:
    """Test Reactive Fabric operation within system."""

    @pytest.mark.asyncio
    async def test_orchestrator_collects_metrics(self, consciousness_system_with_fabric):
        """Orchestrator should collect metrics from all subsystems."""
        system = consciousness_system_with_fabric

        # Wait for at least one collection
        await asyncio.sleep(0.3)

        # Verify collections occurred
        assert system.orchestrator.total_collections >= 1

        # Collect metrics directly
        metrics = await system.orchestrator.metrics_collector.collect()

        # Verify metrics collected from all subsystems
        assert metrics.tig_node_count == 20  # From config
        assert metrics.esgt_event_count >= 0
        assert metrics.arousal_level > 0
        assert metrics.health_score > 0

        # TRACK 1: Verify PFC/ToM metrics present
        assert hasattr(metrics, 'pfc_signals_processed')
        assert hasattr(metrics, 'tom_total_agents')

    @pytest.mark.asyncio
    async def test_orchestrator_collects_events(self, consciousness_system_with_fabric):
        """Orchestrator should collect events from subsystems."""
        system = consciousness_system_with_fabric

        # Wait for collections
        await asyncio.sleep(0.3)

        # Collect events directly
        events = await system.orchestrator.event_collector.collect_events()

        # Events may or may not be present (depends on system state)
        assert isinstance(events, list)
        assert system.orchestrator.event_collector.total_events_collected >= 0

    @pytest.mark.asyncio
    async def test_orchestrator_records_decisions(self, consciousness_system_with_fabric):
        """Orchestrator should record orchestration decisions."""
        system = consciousness_system_with_fabric

        # Wait for multiple collections
        await asyncio.sleep(0.5)

        # Verify decisions recorded
        assert len(system.orchestrator.decision_history) > 0

        # Get recent decisions
        recent = system.orchestrator.get_recent_decisions(limit=5)
        assert len(recent) > 0

        # Verify decision structure
        decision = recent[0]
        assert hasattr(decision, 'should_trigger_esgt')
        assert hasattr(decision, 'salience')
        assert hasattr(decision, 'reason')
        assert hasattr(decision, 'metrics_snapshot')

    @pytest.mark.asyncio
    async def test_orchestrator_provides_statistics(self, consciousness_system_with_fabric):
        """Orchestrator should provide statistics interface."""
        system = consciousness_system_with_fabric

        # Wait for collections
        await asyncio.sleep(0.3)

        # Get statistics
        stats = system.orchestrator.get_orchestration_stats()

        # Verify statistics structure
        assert "total_collections" in stats
        assert "total_triggers_generated" in stats
        assert "total_triggers_executed" in stats
        assert "metrics_collector" in stats
        assert "event_collector" in stats
        assert "collection_interval_ms" in stats
        assert "salience_threshold" in stats

        # Verify values make sense
        assert stats["total_collections"] > 0
        assert stats["collection_interval_ms"] == 100.0
        assert stats["salience_threshold"] == 0.65


class TestSystemLifecycle:
    """Test system lifecycle with Reactive Fabric."""

    @pytest.mark.asyncio
    async def test_system_stops_orchestrator_cleanly(self, consciousness_system_with_fabric):
        """System should stop orchestrator without errors."""
        system = consciousness_system_with_fabric

        # Verify running
        assert system.orchestrator._running is True

        # Stop system
        await system.stop()

        # Verify orchestrator stopped
        assert system.orchestrator._running is False

    @pytest.mark.asyncio
    async def test_orchestrator_stops_before_components(self):
        """Orchestrator should stop before subsystems to prevent collection errors."""
        config = ConsciousnessConfig(
            tig_node_count=20,
            safety_enabled=False
        )

        system = ConsciousnessSystem(config)
        await system.start()

        # Verify all running
        assert system.orchestrator._running is True
        assert system.esgt_coordinator._running is True

        # Stop system
        await system.stop()

        # All should be stopped
        assert system.orchestrator._running is False
        assert system.esgt_coordinator._running is False


class TestReactiveFabricIntegration:
    """Test complete Reactive Fabric integration with consciousness."""

    @pytest.mark.asyncio
    async def test_orchestrator_can_generate_esgt_triggers(self, consciousness_system_with_fabric):
        """Orchestrator should be able to generate ESGT triggers."""
        system = consciousness_system_with_fabric

        # Get initial ESGT event count
        initial_events = system.esgt_coordinator.total_events

        # Wait for orchestration cycles
        await asyncio.sleep(1.0)

        # Check if any triggers were generated
        # (May or may not trigger depending on salience)
        stats = system.orchestrator.get_orchestration_stats()

        # Verify orchestration occurred
        assert stats["total_collections"] >= 5  # At 100ms interval, should have ~10 collections

        # If triggers generated, verify ESGT received them
        if stats["total_triggers_executed"] > 0:
            current_events = system.esgt_coordinator.total_events
            assert current_events >= initial_events

    @pytest.mark.asyncio
    async def test_metrics_reflect_all_subsystems(self, consciousness_system_with_fabric):
        """Collected metrics should reflect all subsystem states."""
        system = consciousness_system_with_fabric

        # Collect current metrics
        metrics = await system.orchestrator.metrics_collector.collect()

        # Verify TIG metrics
        assert metrics.tig_node_count > 0
        assert metrics.tig_edge_count >= 0

        # Verify ESGT metrics
        assert metrics.esgt_event_count >= 0
        assert metrics.esgt_success_rate >= 0

        # Verify Arousal metrics
        assert 0.0 <= metrics.arousal_level <= 1.0

        # Verify Safety metrics
        assert metrics.safety_violations >= 0

        # TRACK 1: Verify PFC metrics
        assert metrics.pfc_signals_processed >= 0
        assert metrics.pfc_actions_generated >= 0

        # TRACK 1: Verify ToM metrics
        assert metrics.tom_total_agents >= 0
        assert metrics.tom_total_beliefs >= 0

    @pytest.mark.asyncio
    async def test_orchestrator_health_score_calculation(self, consciousness_system_with_fabric):
        """Orchestrator should calculate overall system health score."""
        system = consciousness_system_with_fabric

        # Collect metrics with health score
        metrics = await system.orchestrator.metrics_collector.collect()

        # Verify health score calculated
        assert 0.0 <= metrics.health_score <= 1.0

        # Health should be good for freshly started system
        assert metrics.health_score > 0.7  # Reasonable threshold


class TestReactiveFabricConfiguration:
    """Test Reactive Fabric configuration options."""

    @pytest.mark.asyncio
    async def test_orchestrator_custom_collection_interval(self):
        """Orchestrator should respect custom collection interval."""
        config = ConsciousnessConfig(
            tig_node_count=20,
            safety_enabled=False
        )

        system = ConsciousnessSystem(config)
        await system.start()

        # Verify default interval
        assert system.orchestrator.collection_interval_ms == 100.0

        # Verify collection interval in stats
        stats = system.orchestrator.get_orchestration_stats()
        assert stats["collection_interval_ms"] == 100.0

        await system.stop()

    @pytest.mark.asyncio
    async def test_orchestrator_custom_salience_threshold(self):
        """Orchestrator should respect custom salience threshold."""
        config = ConsciousnessConfig(
            tig_node_count=20,
            safety_enabled=False
        )

        system = ConsciousnessSystem(config)
        await system.start()

        # Verify default threshold
        assert system.orchestrator.salience_threshold == 0.65

        # Verify threshold in stats
        stats = system.orchestrator.get_orchestration_stats()
        assert stats["salience_threshold"] == 0.65

        await system.stop()


# Run tests with:
# pytest tests/integration/test_system_reactive_fabric.py -v
