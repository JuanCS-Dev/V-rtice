"""Tests for TemperatureController - Homeostatic Temperature Regulation

FASE 3 SPRINT 4: Test suite for temperature controller including temperature
adjustment, decay, state computation, and activation level management.

Test Structure:
- TestTemperatureControllerLifecycle (4 tests)
- TestTemperatureAdjustment (5 tests)
- TestHomeostaticStates (7 tests)
- TestActivationLevels (4 tests)
- TestStatistics (2 tests)

Total: 22 tests

NO MOCK, NO PLACEHOLDER, NO TODO - Production ready.
DOUTRINA VERTICE compliant: Quality-first, production-ready code.

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

import pytest

from coordination.temperature_controller import (
    TemperatureController,
    HomeostaticState,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def controller():
    """Create a TemperatureController with default settings."""
    return TemperatureController(
        lymphnode_id="lymph-test-1",
        initial_temp=37.0,
        min_temp=36.0,
        max_temp=42.0,
        decay_rate=0.98,
        decay_interval_sec=30.0,
    )


@pytest.fixture
def hot_controller():
    """Create a TemperatureController with high temperature (inflammation)."""
    return TemperatureController(
        lymphnode_id="lymph-hot",
        initial_temp=39.5,
    )


@pytest.fixture
def cold_controller():
    """Create a TemperatureController with low temperature (repouso)."""
    return TemperatureController(
        lymphnode_id="lymph-cold",
        initial_temp=36.8,
    )


# =============================================================================
# TEST LIFECYCLE
# =============================================================================


class TestTemperatureControllerLifecycle:
    """Test TemperatureController initialization and configuration."""

    def test_initialization_default(self):
        """Test default initialization."""
        controller = TemperatureController(lymphnode_id="lymph-1")
        assert controller.lymphnode_id == "lymph-1"
        assert controller.decay_rate == 0.98
        assert controller.decay_interval_sec == 30.0

    @pytest.mark.asyncio
    async def test_initialization_custom(self):
        """Test custom initialization."""
        controller = TemperatureController(
            lymphnode_id="lymph-2",
            initial_temp=38.0,
            min_temp=35.0,
            max_temp=43.0,
            decay_rate=0.95,
            decay_interval_sec=60.0,
        )
        assert controller.lymphnode_id == "lymph-2"
        assert controller.decay_rate == 0.95
        assert controller.decay_interval_sec == 60.0

        temp = await controller.get_current_temperature()
        assert temp == 38.0

    @pytest.mark.asyncio
    async def test_initial_temperature(self, controller):
        """Test initial temperature is correct."""
        temp = await controller.get_current_temperature()
        assert temp == 37.0

    def test_repr(self, controller):
        """Test string representation."""
        repr_str = repr(controller)
        assert "TemperatureController" in repr_str
        assert "lymph-test-1" in repr_str


# =============================================================================
# TEST TEMPERATURE ADJUSTMENT
# =============================================================================


class TestTemperatureAdjustment:
    """Test temperature adjustment and decay."""

    @pytest.mark.asyncio
    async def test_adjust_temperature_increase(self, controller):
        """Test increasing temperature."""
        initial = await controller.get_current_temperature()
        assert initial == 37.0

        new_temp = await controller.adjust_temperature(delta=+1.0)
        assert new_temp == 38.0

    @pytest.mark.asyncio
    async def test_adjust_temperature_decrease(self, controller):
        """Test decreasing temperature."""
        await controller.set_temperature(38.0)

        new_temp = await controller.adjust_temperature(delta=-0.5)
        assert new_temp == 37.5

    @pytest.mark.asyncio
    async def test_adjust_temperature_clamping_max(self, controller):
        """Test temperature clamping at maximum."""
        await controller.set_temperature(41.5)

        # Try to exceed max (42.0)
        new_temp = await controller.adjust_temperature(delta=+2.0)
        assert new_temp == 42.0  # Clamped at max

    @pytest.mark.asyncio
    async def test_adjust_temperature_clamping_min(self, controller):
        """Test temperature clamping at minimum."""
        await controller.set_temperature(36.2)

        # Try to go below min (36.0)
        new_temp = await controller.adjust_temperature(delta=-1.0)
        assert new_temp == 36.0  # Clamped at min

    @pytest.mark.asyncio
    async def test_apply_decay(self, controller):
        """Test temperature decay."""
        await controller.set_temperature(38.0)

        # Apply decay (0.98 multiplier)
        new_temp = await controller.apply_decay()
        expected = 38.0 * 0.98
        assert abs(new_temp - expected) < 0.01


# =============================================================================
# TEST HOMEOSTATIC STATES
# =============================================================================


class TestHomeostaticStates:
    """Test homeostatic state computation."""

    @pytest.mark.asyncio
    async def test_state_repouso(self, cold_controller):
        """Test REPOUSO state (< 37.0°C)."""
        await cold_controller.set_temperature(36.8)
        state = await cold_controller.get_homeostatic_state()
        assert state == HomeostaticState.REPOUSO

    @pytest.mark.asyncio
    async def test_state_vigilancia(self, controller):
        """Test VIGILANCIA state (37.0-37.5°C)."""
        await controller.set_temperature(37.2)
        state = await controller.get_homeostatic_state()
        assert state == HomeostaticState.VIGILANCIA

    @pytest.mark.asyncio
    async def test_state_atencao(self, controller):
        """Test ATENÇÃO state (37.5-38.0°C)."""
        await controller.set_temperature(37.7)
        state = await controller.get_homeostatic_state()
        assert state == HomeostaticState.ATENCAO

    @pytest.mark.asyncio
    async def test_state_ativacao(self, controller):
        """Test ATIVAÇÃO state (38.0-39.0°C)."""
        await controller.set_temperature(38.5)
        state = await controller.get_homeostatic_state()
        assert state == HomeostaticState.ATIVACAO

    @pytest.mark.asyncio
    async def test_state_inflamacao(self, hot_controller):
        """Test INFLAMAÇÃO state (>= 39.0°C)."""
        state = await hot_controller.get_homeostatic_state()
        assert state == HomeostaticState.INFLAMACAO

    @pytest.mark.asyncio
    async def test_state_boundary_vigilancia(self, controller):
        """Test boundary at 37.0°C (VIGILANCIA)."""
        await controller.set_temperature(37.0)
        state = await controller.get_homeostatic_state()
        assert state == HomeostaticState.VIGILANCIA

    @pytest.mark.asyncio
    async def test_state_boundary_inflamacao(self, controller):
        """Test boundary at 39.0°C (INFLAMAÇÃO)."""
        await controller.set_temperature(39.0)
        state = await controller.get_homeostatic_state()
        assert state == HomeostaticState.INFLAMACAO


# =============================================================================
# TEST ACTIVATION LEVELS
# =============================================================================


class TestActivationLevels:
    """Test activation level calculation."""

    @pytest.mark.asyncio
    async def test_activation_percentage_repouso(self, cold_controller):
        """Test activation percentage for REPOUSO (5%)."""
        await cold_controller.set_temperature(36.8)
        pct = await cold_controller.get_target_activation_percentage()
        assert pct == 0.05

    @pytest.mark.asyncio
    async def test_activation_percentage_vigilancia(self, controller):
        """Test activation percentage for VIGILANCIA (15%)."""
        await controller.set_temperature(37.2)
        pct = await controller.get_target_activation_percentage()
        assert pct == 0.15

    @pytest.mark.asyncio
    async def test_activation_percentage_inflamacao(self, hot_controller):
        """Test activation percentage for INFLAMAÇÃO (80%)."""
        pct = await hot_controller.get_target_activation_percentage()
        assert pct == 0.8

    @pytest.mark.asyncio
    async def test_calculate_target_active_agents(self, controller):
        """Test calculating target active agents."""
        await controller.set_temperature(38.0)  # ATIVAÇÃO = 50%

        # With 100 agents, expect 50 active
        target = await controller.calculate_target_active_agents(total_agents=100)
        assert target == 50

        # With 20 agents, expect 10 active
        target = await controller.calculate_target_active_agents(total_agents=20)
        assert target == 10


# =============================================================================
# TEST STATISTICS
# =============================================================================


class TestStatistics:
    """Test statistics collection and reporting."""

    @pytest.mark.asyncio
    async def test_get_stats(self, controller):
        """Test get_stats returns all fields."""
        await controller.set_temperature(37.5)

        stats = await controller.get_stats()

        assert "lymphnode_id" in stats
        assert "current_temperature" in stats
        assert "homeostatic_state" in stats
        assert "target_activation_percentage" in stats
        assert "decay_rate" in stats
        assert "decay_interval_sec" in stats
        assert "temperature_config" in stats

        assert stats["lymphnode_id"] == "lymph-test-1"
        assert stats["current_temperature"] == 37.5
        assert stats["homeostatic_state"] == "atencao"
        assert stats["target_activation_percentage"] == 0.3
        assert stats["decay_rate"] == 0.98

    @pytest.mark.asyncio
    async def test_stats_reflect_changes(self, controller):
        """Test stats reflect temperature changes."""
        # Initial state
        stats1 = await controller.get_stats()
        assert stats1["current_temperature"] == 37.0
        assert stats1["homeostatic_state"] == "vigilancia"

        # After temperature increase
        await controller.adjust_temperature(delta=+2.0)

        stats2 = await controller.get_stats()
        assert stats2["current_temperature"] == 39.0
        assert stats2["homeostatic_state"] == "inflamacao"
        assert stats2["target_activation_percentage"] == 0.8
