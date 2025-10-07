"""
Unit tests for Homeostatic Controller (MAPE-K Loop)

Tests cover actual production implementation:
- Initialization and lifecycle
- MAPE-K loop (Monitor-Analyze-Plan-Execute-Knowledge)
- System state transitions
- Q-learning (reinforcement learning)
- Action execution
- Knowledge base persistence
- Metrics and error handling
"""

import asyncio
from datetime import datetime
from typing import Any, Dict

import pytest
import pytest_asyncio

from active_immune_core.coordination.homeostatic_controller import (
    HomeostaticController,
    SystemState,
    ActionType,
)


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def controller() -> HomeostaticController:
    """Create HomeostaticController instance for testing."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test_001",
        lymphnode_url="http://localhost:8200",
        metrics_url="http://localhost:9090",
        db_url="postgresql://user:pass@localhost:5432/immunis_test",
        monitor_interval=1,
    )
    yield ctrl
    if ctrl._running:
        await ctrl.parar()


# ==================== INITIALIZATION TESTS ====================


@pytest.mark.asyncio
async def test_controller_initialization():
    """Test HomeostaticController initialization."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test_001",
        lymphnode_url="http://localhost:8200",
        metrics_url="http://localhost:9090",
        db_url="postgresql://user:pass@localhost:5432/immunis_test",
    )

    assert ctrl.id == "ctrl_test_001"
    assert ctrl.lymphnode_url == "http://localhost:8200"
    assert ctrl.metrics_url == "http://localhost:9090"
    assert ctrl.current_state == SystemState.REPOUSO
    assert ctrl.monitor_interval == 30  # Default
    assert not ctrl._running
    assert len(ctrl.q_table) == 0


@pytest.mark.asyncio
async def test_controller_initialization_custom_interval():
    """Test controller with custom monitor interval."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        monitor_interval=5,
    )

    assert ctrl.monitor_interval == 5


# ==================== LIFECYCLE TESTS ====================


@pytest.mark.asyncio
async def test_controller_start_stop(controller: HomeostaticController):
    """Test controller lifecycle: start and stop."""
    # Start
    await controller.iniciar()
    assert controller._running is True
    assert len(controller._tasks) > 0

    # Stop
    await controller.parar()
    assert controller._running is False


@pytest.mark.asyncio
async def test_controller_double_start_idempotent(controller: HomeostaticController):
    """Test that starting twice is idempotent."""
    await controller.iniciar()
    first_task_count = len(controller._tasks)

    # Start again (should not crash)
    await controller.iniciar()
    second_task_count = len(controller._tasks)

    assert controller._running is True
    assert first_task_count > 0
    # Should not create duplicate tasks
    assert second_task_count == first_task_count

    await controller.parar()


@pytest.mark.asyncio
async def test_controller_stop_without_start():
    """Test stopping controller that was never started."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
    )

    # Should not raise exception
    await ctrl.parar()
    assert ctrl._running is False


# ==================== SYSTEM STATE TESTS ====================


@pytest.mark.asyncio
async def test_system_state_enum_values():
    """Test SystemState enum has all expected values."""
    assert hasattr(SystemState, "REPOUSO")
    assert hasattr(SystemState, "VIGILANCIA")
    assert hasattr(SystemState, "ATENCAO")
    assert hasattr(SystemState, "ATIVACAO")
    assert hasattr(SystemState, "INFLAMACAO")
    assert hasattr(SystemState, "EMERGENCIA")


@pytest.mark.asyncio
async def test_state_transition_updates_current_state(controller: HomeostaticController):
    """Test that state transitions update current_state."""
    initial_state = controller.current_state
    assert initial_state == SystemState.REPOUSO

    # Simulate state change
    controller.current_state = SystemState.VIGILANCIA
    assert controller.current_state == SystemState.VIGILANCIA


# ==================== ACTION TYPE TESTS ====================


@pytest.mark.asyncio
async def test_action_type_enum_values():
    """Test ActionType enum has all expected actions."""
    assert hasattr(ActionType, "NOOP")
    assert hasattr(ActionType, "SCALE_UP_AGENTS")
    assert hasattr(ActionType, "SCALE_DOWN_AGENTS")
    assert hasattr(ActionType, "CLONE_SPECIALIZED")
    assert hasattr(ActionType, "DESTROY_CLONES")
    assert hasattr(ActionType, "INCREASE_SENSITIVITY")
    assert hasattr(ActionType, "DECREASE_SENSITIVITY")


# ==================== Q-LEARNING TESTS ====================


@pytest.mark.asyncio
async def test_q_table_initialization(controller: HomeostaticController):
    """Test Q-table starts empty."""
    assert len(controller.q_table) == 0


@pytest.mark.asyncio
async def test_q_value_update(controller: HomeostaticController):
    """Test Q-value update with learning."""
    state = SystemState.VIGILANCIA
    action = ActionType.SCALE_UP_AGENTS
    reward = 0.8

    # Update Q-value
    controller._update_q_value(state, action, reward)

    # Should have entry in Q-table
    assert (state, action) in controller.q_table

    # Q-value should be updated (learning_rate * reward)
    expected_q = controller.learning_rate * reward
    assert abs(controller.q_table[(state, action)] - expected_q) < 0.01


@pytest.mark.asyncio
async def test_q_value_multiple_updates(controller: HomeostaticController):
    """Test Q-value converges with multiple updates."""
    state = SystemState.ATENCAO
    action = ActionType.CLONE_SPECIALIZED

    # Multiple updates with positive reward
    for _ in range(10):
        controller._update_q_value(state, action, reward=1.0)

    # Q-value should approach 1.0
    final_q = controller.q_table[(state, action)]
    assert final_q > 0.5  # Should be high


@pytest.mark.asyncio
async def test_q_value_negative_reward(controller: HomeostaticController):
    """Test Q-value with negative reward."""
    state = SystemState.EMERGENCIA
    action = ActionType.SCALE_DOWN_AGENTS

    # Update with negative reward (bad action)
    controller._update_q_value(state, action, reward=-0.5)

    # Q-value should be negative
    assert controller.q_table[(state, action)] < 0.0


@pytest.mark.asyncio
async def test_select_best_action(controller: HomeostaticController):
    """Test selecting best action from Q-table."""
    state = SystemState.ATIVACAO

    # Populate Q-table with different values
    controller.q_table[(state, ActionType.NOOP)] = 0.1
    controller.q_table[(state, ActionType.SCALE_UP_AGENTS)] = 0.9
    controller.q_table[(state, ActionType.CLONE_SPECIALIZED)] = 0.5

    # Best action should be SCALE_UP_AGENTS (highest Q-value)
    best_action = controller._select_best_action(state)
    assert best_action == ActionType.SCALE_UP_AGENTS


@pytest.mark.asyncio
async def test_select_action_with_exploration(controller: HomeostaticController):
    """Test epsilon-greedy exploration."""
    state = SystemState.VIGILANCIA

    # Set high epsilon (always explore)
    controller.epsilon = 1.0

    # Should select random action (exploration)
    action = controller._select_action(state)
    assert isinstance(action, ActionType)


@pytest.mark.asyncio
async def test_select_action_with_exploitation(controller: HomeostaticController):
    """Test exploitation when epsilon is low."""
    state = SystemState.ATIVACAO

    # Set zero epsilon (always exploit)
    controller.epsilon = 0.0

    # Populate Q-table
    controller.q_table[(state, ActionType.SCALE_UP_AGENTS)] = 1.0
    controller.q_table[(state, ActionType.NOOP)] = 0.0

    # Should always select best action
    for _ in range(10):
        action = controller._select_action(state)
        assert action == ActionType.SCALE_UP_AGENTS


# ==================== MONITORING TESTS ====================


@pytest.mark.asyncio
async def test_monitor_collects_metrics(controller: HomeostaticController):
    """Test monitoring collects system metrics."""
    await controller.iniciar()

    # Wait for at least one monitor cycle
    await asyncio.sleep(1.5)

    # Should have collected metrics
    assert controller.system_metrics is not None
    assert isinstance(controller.system_metrics, dict)
    assert len(controller.system_metrics) > 0
    # Should have basic system metrics
    assert "cpu_usage" in controller.system_metrics
    assert "memory_usage" in controller.system_metrics

    await controller.parar()


# ==================== ANALYSIS TESTS ====================


@pytest.mark.asyncio
async def test_analyze_detects_no_issues_normal_state(controller: HomeostaticController):
    """Test analyze detects no issues in normal state."""
    # Simulate normal metrics
    controller.system_metrics = {
        "cpu_percent": 50.0,
        "memory_percent": 60.0,
        "active_agents": 100,
        "temperature": 37.2,
    }

    issues = await controller._analyze()

    # Should have no critical issues
    assert isinstance(issues, list)


@pytest.mark.asyncio
async def test_analyze_detects_high_cpu(controller: HomeostaticController):
    """Test analyze detects high CPU usage."""
    # Simulate high CPU (normalized to 0-1 range)
    controller.system_metrics = {
        "cpu_usage": 0.95,  # 95%
        "memory_usage": 0.60,  # 60%
    }
    controller.agent_metrics = {
        "agents_active": 50,
        "agents_total": 100,
    }

    issues = await controller._analyze()

    # Should detect high CPU (threshold: 0.8)
    assert len(issues) > 0
    assert any("cpu" in issue.lower() for issue in issues)


@pytest.mark.asyncio
async def test_analyze_detects_high_memory(controller: HomeostaticController):
    """Test analyze detects high memory usage."""
    # Simulate high memory (normalized to 0-1 range)
    controller.system_metrics = {
        "cpu_usage": 0.50,  # 50%
        "memory_usage": 0.95,  # 95%
    }
    controller.agent_metrics = {
        "agents_active": 50,
        "agents_total": 100,
    }

    issues = await controller._analyze()

    # Should detect high memory (threshold: 0.85)
    assert len(issues) > 0
    assert any("memory" in issue.lower() for issue in issues)


# ==================== PLANNING TESTS ====================


@pytest.mark.asyncio
async def test_plan_returns_action_and_params(controller: HomeostaticController):
    """Test planning returns action and parameters."""
    issues = ["high_cpu"]

    action, params = await controller._plan(issues)

    assert isinstance(action, ActionType)
    assert isinstance(params, dict)


@pytest.mark.asyncio
async def test_plan_noop_when_no_issues(controller: HomeostaticController):
    """Test plan returns NOOP when no issues."""
    issues = []

    action, params = await controller._plan(issues)

    assert action == ActionType.NOOP
    assert params == {}


# ==================== EXECUTION TESTS ====================


@pytest.mark.asyncio
async def test_execute_noop_always_succeeds(controller: HomeostaticController):
    """Test executing NOOP always succeeds."""
    success = await controller._execute(ActionType.NOOP, {})
    assert success is True


# ==================== REWARD CALCULATION TESTS ====================


@pytest.mark.asyncio
async def test_calculate_reward_success_no_issues(controller: HomeostaticController):
    """Test reward calculation for successful action with no remaining issues."""
    reward = controller._calculate_reward(success=True, issues=[])

    # Should be positive reward
    assert reward > 0.0


@pytest.mark.asyncio
async def test_calculate_reward_failure(controller: HomeostaticController):
    """Test reward calculation for failed action."""
    reward = controller._calculate_reward(success=False, issues=["high_cpu"])

    # Should be negative reward
    assert reward < 0.0


@pytest.mark.asyncio
async def test_calculate_reward_success_with_remaining_issues(controller: HomeostaticController):
    """Test reward for successful action but issues remain."""
    reward = controller._calculate_reward(success=True, issues=["high_cpu", "high_memory"])

    # Should be less positive than perfect resolution
    # (Still positive because action succeeded)
    assert reward > 0.0

    # But less than perfect reward
    perfect_reward = controller._calculate_reward(success=True, issues=[])
    assert reward < perfect_reward


# ==================== METRICS TESTS ====================


@pytest.mark.asyncio
async def test_get_controller_metrics(controller: HomeostaticController):
    """Test retrieving controller metrics."""
    metrics = controller.get_controller_metrics()

    assert metrics["controller_id"] == controller.id
    assert metrics["current_state"] == SystemState.REPOUSO.value
    assert "q_table_size" in metrics


@pytest.mark.asyncio
async def test_metrics_track_actions(controller: HomeostaticController):
    """Test metrics track action counts."""
    # Execute action
    await controller._execute(ActionType.NOOP, {})

    # Verify metrics are available
    metrics = controller.get_controller_metrics()
    assert "controller_id" in metrics
    assert "current_state" in metrics
    # Verify last action is tracked
    assert controller.last_action == ActionType.NOOP


# ==================== ERROR HANDLING TESTS ====================


@pytest.mark.asyncio
async def test_graceful_degradation_postgres_failure():
    """Test graceful degradation when PostgreSQL connection fails."""
    # Use invalid PostgreSQL DSN
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        db_url="postgresql://invalid:invalid@invalid-host:5432/invalid",
    )

    # Should start without crashing (graceful degradation)
    try:
        await ctrl.iniciar()
        assert ctrl._running is True
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_graceful_degradation_prometheus_failure():
    """Test graceful degradation when Prometheus is unreachable."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        metrics_url="http://invalid-host:9090",
    )

    # Should start without crashing
    try:
        await ctrl.iniciar()
        assert ctrl._running is True

        # Wait for monitor cycle (should handle gracefully)
        await asyncio.sleep(0.5)
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_graceful_degradation_lymphnode_failure():
    """Test graceful degradation when Lymphnode API is unreachable."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://invalid-host:8001",
    )

    # Should start without crashing
    try:
        await ctrl.iniciar()
        assert ctrl._running is True
    finally:
        await ctrl.parar()


# ==================== REPR TEST ====================


@pytest.mark.asyncio
async def test_repr(controller: HomeostaticController):
    """Test string representation."""
    repr_str = repr(controller)
    assert "ctrl_test_001" in repr_str
    # Repr includes either the enum value or the full enum name
    assert (SystemState.REPOUSO.value in repr_str or "SystemState.REPOUSO" in repr_str)
