"""Integration Tests - Reactive Fabric (Sprint 3)

Tests the complete data collection and orchestration pipeline:
- MetricsCollector integration
- EventCollector integration
- DataOrchestrator orchestration
- ESGT trigger generation

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Sprint: Reactive Fabric Sprint 3
"""

import pytest
from consciousness.system import ConsciousnessSystem, ConsciousnessConfig
from consciousness.reactive_fabric.collectors.metrics_collector import MetricsCollector
from consciousness.reactive_fabric.collectors.event_collector import EventCollector, EventType
from consciousness.reactive_fabric.orchestration.data_orchestrator import DataOrchestrator


@pytest.fixture(scope="function")
def consciousness_system_minimal(request, event_loop):
    """Create minimal Consciousness System for testing."""
    config = ConsciousnessConfig(
        tig_node_count=10,  # Small for fast tests
        tig_target_density=0.25,
        esgt_min_salience=0.60,
        esgt_refractory_period_ms=50.0,
        esgt_max_frequency_hz=10.0,
        esgt_min_available_nodes=3,
        arousal_baseline=0.60,
        safety_enabled=False  # Disable for faster tests
    )

    system = ConsciousnessSystem(config)
    event_loop.run_until_complete(system.start())

    def cleanup():
        event_loop.run_until_complete(system.stop())

    request.addfinalizer(cleanup)

    return system


class TestMetricsCollector:
    """Test MetricsCollector integration."""

    @pytest.mark.asyncio
    async def test_metrics_collector_initialization(self, consciousness_system_minimal):
        """MetricsCollector should initialize with system."""
        collector = MetricsCollector(consciousness_system_minimal)

        assert collector.system == consciousness_system_minimal
        assert collector.collection_count == 0

    @pytest.mark.asyncio
    async def test_metrics_collector_collects_data(self, consciousness_system_minimal):
        """MetricsCollector should collect system metrics."""
        collector = MetricsCollector(consciousness_system_minimal)

        metrics = await collector.collect()

        # Verify metrics collected
        assert metrics.timestamp > 0
        assert metrics.tig_node_count == 10  # From config
        assert metrics.arousal_level > 0
        assert metrics.health_score >= 0.0
        assert metrics.collection_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_metrics_collector_tracks_pfc_tom(self, consciousness_system_minimal):
        """MetricsCollector should track PFC and ToM metrics (Track 1)."""
        collector = MetricsCollector(consciousness_system_minimal)

        metrics = await collector.collect()

        # PFC metrics
        assert hasattr(metrics, 'pfc_signals_processed')
        assert hasattr(metrics, 'pfc_actions_generated')
        assert hasattr(metrics, 'pfc_approval_rate')

        # ToM metrics
        assert hasattr(metrics, 'tom_total_agents')
        assert hasattr(metrics, 'tom_total_beliefs')
        assert hasattr(metrics, 'tom_cache_hit_rate')


class TestEventCollector:
    """Test EventCollector integration."""

    @pytest.mark.asyncio
    async def test_event_collector_initialization(self, consciousness_system_minimal):
        """EventCollector should initialize with system."""
        collector = EventCollector(consciousness_system_minimal, max_events=100)

        assert collector.system == consciousness_system_minimal
        assert collector.max_events == 100
        assert len(collector.events) == 0

    @pytest.mark.asyncio
    async def test_event_collector_collects_events(self, consciousness_system_minimal):
        """EventCollector should collect system events."""
        collector = EventCollector(consciousness_system_minimal, max_events=100)

        events = await collector.collect_events()

        # Events may or may not be generated (depends on system state)
        assert isinstance(events, list)
        assert collector.total_events_collected >= 0

    @pytest.mark.asyncio
    async def test_event_collector_query_by_type(self, consciousness_system_minimal):
        """EventCollector should support querying by event type."""
        collector = EventCollector(consciousness_system_minimal, max_events=100)

        await collector.collect_events()

        # Query by type (may be empty)
        esgt_events = collector.get_events_by_type(EventType.ESGT_IGNITION)
        assert isinstance(esgt_events, list)

    @pytest.mark.asyncio
    async def test_event_collector_recent_events(self, consciousness_system_minimal):
        """EventCollector should return recent events."""
        collector = EventCollector(consciousness_system_minimal, max_events=100)

        await collector.collect_events()

        recent = collector.get_recent_events(limit=5)
        assert isinstance(recent, list)
        assert len(recent) <= 5


class TestDataOrchestrator:
    """Test DataOrchestrator integration."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, consciousness_system_minimal):
        """DataOrchestrator should initialize with system."""
        orchestrator = DataOrchestrator(
            consciousness_system_minimal,
            collection_interval_ms=200.0,  # Slower for tests
            salience_threshold=0.65
        )

        assert orchestrator.system == consciousness_system_minimal
        assert orchestrator.collection_interval_ms == 200.0
        assert orchestrator.salience_threshold == 0.65
        assert orchestrator._running is False

    @pytest.mark.asyncio
    async def test_orchestrator_has_collectors(self, consciousness_system_minimal):
        """DataOrchestrator should create collectors."""
        orchestrator = DataOrchestrator(consciousness_system_minimal)

        assert orchestrator.metrics_collector is not None
        assert orchestrator.event_collector is not None
        assert isinstance(orchestrator.metrics_collector, MetricsCollector)
        assert isinstance(orchestrator.event_collector, EventCollector)

    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self, consciousness_system_minimal):
        """DataOrchestrator should start and stop cleanly."""
        orchestrator = DataOrchestrator(
            consciousness_system_minimal,
            collection_interval_ms=500.0  # Slow to avoid rapid firing
        )

        # Start
        await orchestrator.start()
        assert orchestrator._running is True
        assert orchestrator._orchestration_task is not None

        # Stop
        await orchestrator.stop()
        assert orchestrator._running is False

    @pytest.mark.asyncio
    async def test_orchestrator_collects_data(self, consciousness_system_minimal):
        """DataOrchestrator should collect data in background."""
        orchestrator = DataOrchestrator(
            consciousness_system_minimal,
            collection_interval_ms=200.0
        )

        await orchestrator.start()

        # Wait for at least one collection
        import asyncio
        await asyncio.sleep(0.5)

        await orchestrator.stop()

        # Verify collections occurred
        assert orchestrator.total_collections >= 1

    @pytest.mark.asyncio
    async def test_orchestrator_get_stats(self, consciousness_system_minimal):
        """DataOrchestrator should provide statistics."""
        orchestrator = DataOrchestrator(consciousness_system_minimal)

        stats = orchestrator.get_orchestration_stats()

        assert "total_collections" in stats
        assert "total_triggers_generated" in stats
        assert "metrics_collector" in stats
        assert "event_collector" in stats


class TestReactiveFabricPipeline:
    """Test complete Reactive Fabric pipeline."""

    @pytest.mark.asyncio
    async def test_metrics_to_orchestrator_flow(self, consciousness_system_minimal):
        """Test metrics flow from collector to orchestrator."""
        orchestrator = DataOrchestrator(consciousness_system_minimal)

        # Collect metrics directly
        metrics = await orchestrator.metrics_collector.collect()

        # Verify metrics collected
        assert metrics is not None
        assert metrics.health_score > 0

    @pytest.mark.asyncio
    async def test_events_to_orchestrator_flow(self, consciousness_system_minimal):
        """Test events flow from collector to orchestrator."""
        orchestrator = DataOrchestrator(consciousness_system_minimal)

        # Collect events directly
        events = await orchestrator.event_collector.collect_events()

        # Events may be empty (depends on system state)
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_orchestrator_decision_history(self, consciousness_system_minimal):
        """Test orchestrator records decision history."""
        orchestrator = DataOrchestrator(
            consciousness_system_minimal,
            collection_interval_ms=200.0
        )

        await orchestrator.start()

        # Wait for some collections
        import asyncio
        await asyncio.sleep(0.5)

        await orchestrator.stop()

        # Check decision history
        assert len(orchestrator.decision_history) > 0

        # Get recent decisions
        recent = orchestrator.get_recent_decisions(limit=5)
        assert isinstance(recent, list)


# Run tests with:
# pytest tests/integration/test_reactive_fabric.py -v
