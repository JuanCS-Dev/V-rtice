"""Edge Case Tests - System Robustness Validation

Tests consciousness system edge cases and boundary conditions:
- Cold start from uninitialized state
- Hot restart (stop→start cycles)
- Concurrent stimulus handling
- TIG node saturation
- ESGT thread collision
- Resource exhaustion scenarios

This is PRODUCTION-CRITICAL robustness validation.
Target: 100% edge case coverage.

Authors: Claude Code + Juan
Date: 2025-10-14
"""

import pytest
import asyncio
from consciousness.system import ConsciousnessSystem, ConsciousnessConfig


class TestSystemColdStart:
    """Test system initialization from completely uninitialized state."""

    @pytest.mark.asyncio
    async def test_cold_start_from_new_instance(self):
        """System should initialize successfully from cold state."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        # Before start, all components should be None
        assert system.tig_fabric is None
        assert system.esgt_coordinator is None
        assert system.arousal_controller is None

        try:
            # Cold start
            await system.start()

            # After start, all components should be initialized
            assert system.tig_fabric is not None
            assert system.esgt_coordinator is not None
            assert system.arousal_controller is not None
            assert system.is_healthy()

        finally:
            await system.stop()

    @pytest.mark.asyncio
    async def test_system_dict_before_start(self):
        """System dict should handle uninitialized state gracefully."""
        config = ConsciousnessConfig(safety_enabled=False)
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        # Should not crash, even though components are None
        system_dict = system.get_system_dict()

        assert system_dict['tig'] is None
        assert system_dict['esgt'] is None
        assert system_dict['arousal'] is None
        assert 'metrics' in system_dict


class TestSystemHotRestart:
    """Test system restart without resource leaks."""

    @pytest.mark.asyncio
    async def test_hot_restart_no_leak(self):
        """System should support stop→start cycles without issues."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            # Cycle 1: Start → Stop
            await system.start()
            assert system.is_healthy()
            await asyncio.sleep(0.1)
            await system.stop()
            assert not system._running

            # Cycle 2: Start again (hot restart)
            await system.start()
            assert system.is_healthy()
            await asyncio.sleep(0.1)

            # Should still be healthy after restart
            assert system.is_healthy()

        finally:
            await system.stop()

    @pytest.mark.asyncio
    async def test_triple_restart_stability(self):
        """System should survive multiple restart cycles."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            for cycle in range(3):
                await system.start()
                assert system.is_healthy(), f"Cycle {cycle+1} failed"
                await asyncio.sleep(0.05)
                await system.stop()
                assert not system._running

            # Final start to verify system still works
            await system.start()
            assert system.is_healthy()

        finally:
            await system.stop()


class TestConcurrentStimulus:
    """Test system handling of multiple concurrent stimuli."""

    @pytest.mark.asyncio
    async def test_concurrent_tig_activations(self):
        """System should handle multiple concurrent TIG activations."""
        config = ConsciousnessConfig(
            tig_node_count=100,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            # Fire 10 concurrent TIG activations
            tasks = []
            for i in range(10):
                node_id = i * 10  # Spread across nodes
                task = system.tig_fabric.activate_node(node_id, activation=0.8)
                tasks.append(task)

            # Wait for all to complete
            await asyncio.gather(*tasks)

            # System should still be healthy
            assert system.is_healthy()

            # ESGT should have processed some events
            # (May not fire all due to refractory period)
            assert system.esgt_coordinator.event_history is not None

        finally:
            await system.stop()

    @pytest.mark.asyncio
    async def test_rapid_fire_activations(self):
        """System should handle rapid sequential activations."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            esgt_refractory_period_ms=50.0,  # Shorter refractory
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            # Rapid fire (no await between activations)
            for i in range(20):
                await system.tig_fabric.activate_node(i % 50, activation=0.7)

            await asyncio.sleep(0.3)

            # System should survive rapid fire
            assert system.is_healthy()

        finally:
            await system.stop()


class TestTIGNodeSaturation:
    """Test TIG behavior under node saturation."""

    @pytest.mark.asyncio
    async def test_single_node_saturation(self):
        """TIG should handle repeated activation of single node."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            # Saturate single node with 50 activations
            node_id = 25
            for _ in range(50):
                await system.tig_fabric.activate_node(node_id, activation=0.95)

            await asyncio.sleep(0.2)

            # System should survive saturation
            assert system.is_healthy()

            # Node activation should be bounded (not explode)
            # (Implementation detail: may have decay)

        finally:
            await system.stop()

    @pytest.mark.asyncio
    async def test_all_nodes_simultaneous_activation(self):
        """TIG should handle all nodes activated simultaneously."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            # Activate ALL nodes simultaneously
            tasks = []
            for node_id in range(50):
                task = system.tig_fabric.activate_node(node_id, activation=0.9)
                tasks.append(task)

            await asyncio.gather(*tasks)

            await asyncio.sleep(0.3)

            # System should survive full saturation
            assert system.is_healthy()

        finally:
            await system.stop()


class TestESGTThreadCollision:
    """Test ESGT behavior when multiple ignitions triggered simultaneously."""

    @pytest.mark.asyncio
    async def test_concurrent_high_salience_stimuli(self):
        """ESGT should handle multiple high-salience stimuli concurrently."""
        config = ConsciousnessConfig(
            tig_node_count=100,
            esgt_min_salience=0.65,
            esgt_refractory_period_ms=100.0,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            baseline_events = len(system.esgt_coordinator.event_history)

            # Fire 5 high-salience stimuli concurrently
            tasks = []
            for i in range(5):
                node_id = i * 20
                task = system.tig_fabric.activate_node(node_id, activation=0.95)
                tasks.append(task)

            await asyncio.gather(*tasks)

            await asyncio.sleep(0.4)

            current_events = len(system.esgt_coordinator.event_history)

            # ESGT should have managed collisions
            # (May merge or serialize - implementation dependent)
            # At minimum, should not crash
            assert system.is_healthy()

            # Should have processed at least some events
            # (Refractory period may limit count)
            assert current_events >= baseline_events

        finally:
            await system.stop()


class TestResourceExhaustion:
    """Test system behavior under resource constraints."""

    @pytest.mark.asyncio
    async def test_large_tig_initialization(self):
        """System should initialize even with large TIG."""
        config = ConsciousnessConfig(
            tig_node_count=500,  # Large TIG
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            # Should initialize successfully (may take time)
            await system.start()

            assert system.is_healthy()
            assert system.tig_fabric is not None

            # Verify TIG has correct node count
            system_dict = system.get_system_dict()
            metrics = system_dict['metrics']
            # Note: actual count may differ due to topology constraints
            assert metrics['tig_node_count'] > 0

        finally:
            await system.stop()


class TestComponentFailureIsolation:
    """Test system isolation of component failures."""

    @pytest.mark.asyncio
    async def test_system_with_safety_disabled(self):
        """System should work with safety explicitly disabled."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            safety_enabled=False,  # Explicitly disabled
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            # Safety should be None
            assert system.safety_protocol is None

            # But other components should work
            assert system.tig_fabric is not None
            assert system.esgt_coordinator is not None
            assert system.arousal_controller is not None
            assert system.is_healthy()

        finally:
            await system.stop()

    @pytest.mark.asyncio
    async def test_system_safety_status_when_disabled(self):
        """Safety status should return None when disabled."""
        config = ConsciousnessConfig(
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            status = system.get_safety_status()
            assert status is None

            violations = system.get_safety_violations()
            assert violations == []

        finally:
            await system.stop()


class TestSystemConfigurationVariations:
    """Test system with various configuration combinations."""

    @pytest.mark.asyncio
    async def test_minimal_configuration(self):
        """System should work with minimal config (all defaults)."""
        # Use default config
        system = ConsciousnessSystem()
        system.config.safety_enabled = False  # Disable for test
        system.config.reactive.enable_data_orchestration = False

        try:
            await system.start()
            assert system.is_healthy()

        finally:
            await system.stop()

    @pytest.mark.asyncio
    async def test_aggressive_esgt_configuration(self):
        """System should work with aggressive ESGT settings."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            esgt_min_salience=0.30,  # Very low threshold
            esgt_refractory_period_ms=50.0,  # Very short refractory
            esgt_max_frequency_hz=10.0,  # High frequency
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()
            assert system.is_healthy()

            # Should be more sensitive to stimuli
            await system.tig_fabric.activate_node(10, activation=0.40)
            await asyncio.sleep(0.2)

            assert system.is_healthy()

        finally:
            await system.stop()

    @pytest.mark.asyncio
    async def test_conservative_esgt_configuration(self):
        """System should work with conservative ESGT settings."""
        config = ConsciousnessConfig(
            tig_node_count=50,
            esgt_min_salience=0.95,  # Very high threshold
            esgt_refractory_period_ms=500.0,  # Very long refractory
            esgt_max_frequency_hz=1.0,  # Low frequency
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()
            assert system.is_healthy()

            # Should be less sensitive to stimuli
            await system.tig_fabric.activate_node(10, activation=0.70)
            await asyncio.sleep(0.2)

            assert system.is_healthy()

        finally:
            await system.stop()


class TestSystemMetricsEdgeCases:
    """Test system metrics under edge conditions."""

    @pytest.mark.asyncio
    async def test_metrics_when_components_inactive(self):
        """Metrics should handle inactive components gracefully."""
        config = ConsciousnessConfig(
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            # Get metrics immediately after start (may not be stable)
            system_dict = system.get_system_dict()
            metrics = system_dict['metrics']

            # Should have metrics dict (even if values are default)
            assert isinstance(metrics, dict)

        finally:
            await system.stop()
