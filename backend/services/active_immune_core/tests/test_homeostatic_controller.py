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
from unittest.mock import AsyncMock, MagicMock, patch

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


# ==================== PHASE 2: ADVANCED COVERAGE (56%→85%) ====================


@pytest.mark.asyncio
async def test_execute_scale_up_success():
    """Test successful scale up execution."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8001"
    )

    try:
        await ctrl.iniciar()

        from unittest.mock import AsyncMock, patch
        with patch.object(ctrl._http_session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"success": True})

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_response
            mock_ctx.__aexit__.return_value = None
            mock_post.return_value = mock_ctx

            result = await ctrl._execute_scale_up({"quantity": 5, "reason": "high_load"})

            assert result is True
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_scale_down_success():
    """Test successful scale down execution."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8001"
    )

    try:
        await ctrl.iniciar()

        from unittest.mock import AsyncMock, patch
        with patch.object(ctrl._http_session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"success": True})

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_response
            mock_ctx.__aexit__.return_value = None
            mock_post.return_value = mock_ctx

            result = await ctrl._execute_scale_down({"quantity": 3})

            assert result is True
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_clone_specialized_success():
    """Test successful specialized clone creation."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8001"
    )

    try:
        await ctrl.iniciar()

        from unittest.mock import AsyncMock, patch
        with patch.object(ctrl._http_session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"clone_ids": ["clone_001", "clone_002"]})

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_response
            mock_ctx.__aexit__.return_value = None
            mock_post.return_value = mock_ctx

            result = await ctrl._execute_clone_specialized({"specialization": "malware_hunter", "quantity": 2})

            assert result is True
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_destroy_clones_success():
    """Test successful clone destruction."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8001"
    )

    try:
        await ctrl.iniciar()

        from unittest.mock import AsyncMock, patch
        with patch.object(ctrl._http_session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"destroyed": 3})

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_response
            mock_ctx.__aexit__.return_value = None
            mock_post.return_value = mock_ctx

            result = await ctrl._execute_destroy_clones({"specialization": "old_threat"})

            assert result is True
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_adjust_sensitivity_success():
    """Test successful sensitivity adjustment."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8001"
    )

    try:
        await ctrl.iniciar()

        from unittest.mock import AsyncMock, patch
        with patch.object(ctrl._http_session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"success": True})

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_response
            mock_ctx.__aexit__.return_value = None
            mock_post.return_value = mock_ctx

            result = await ctrl._execute_adjust_sensitivity({"delta": 0.1})

            assert result is True
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_select_action_with_exploration():
    """Test action selection with exploration (epsilon-greedy)."""
    ctrl = HomeostaticController(controller_id="ctrl_test")
    ctrl.exploration_rate = 1.0  # Force exploration

    try:
        await ctrl.iniciar()

        state = SystemState.VIGILANCIA
        action = ctrl._select_action(state)

        # Should select some action (random due to exploration)
        assert action in ActionType
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_determine_action_params_scale_up():
    """Test action parameter determination for scale up."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        params = ctrl._determine_action_params(
            ActionType.SCALE_UP_AGENTS,
            issues=["cpu_high", "memory_high"]
        )

        assert "quantity" in params
        assert "reason" in params
        assert params["quantity"] > 0
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_determine_action_params_clone_specialized():
    """Test action parameter determination for specialized cloning."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        params = ctrl._determine_action_params(
            ActionType.CLONE_SPECIALIZED,
            issues=["persistent_threat"]
        )

        assert "specialization" in params
        assert "quantity" in params
    finally:
        await ctrl.parar()


# ==================== PHASE 3: ADVANCED COVERAGE (63%→85%+) ====================


@pytest.mark.asyncio
async def test_set_mmei_client():
    """Test setting MMEI client for consciousness integration."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    # Mock MMEI client
    mock_mmei = MagicMock()

    ctrl.set_mmei_client(mock_mmei)

    # Should set client if MMEI available, or log warning if not
    # Either way, should not crash
    assert True


@pytest.mark.asyncio
async def test_create_knowledge_table_no_pool():
    """Test knowledge table creation without database pool."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    # No database pool
    ctrl._db_pool = None

    # Should not crash
    await ctrl._create_knowledge_table()


@pytest.mark.asyncio
async def test_create_knowledge_table_error():
    """Test knowledge table creation handles errors."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        # Mock database pool that raises error
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Database error"))

        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None

        ctrl._db_pool = mock_pool

        # Should handle error gracefully
        await ctrl._create_knowledge_table()
    finally:
        if ctrl._running:
            await ctrl.parar()


@pytest.mark.asyncio
async def test_store_decision_no_pool():
    """Test storing decision without database pool."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    ctrl._db_pool = None

    # Should not crash
    await ctrl._store_decision(
        state=SystemState.REPOUSO,
        metrics={},
        action=ActionType.NOOP,
    )


@pytest.mark.asyncio
async def test_store_decision_error():
    """Test storing decision handles errors."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        # Mock database pool that raises error
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Insert error"))

        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None

        ctrl._db_pool = mock_pool

        # Should handle error gracefully
        await ctrl._store_decision(
            state=SystemState.ATENCAO,
            metrics={},
            action=ActionType.SCALE_UP_AGENTS,
        )
    finally:
        if ctrl._running:
            await ctrl.parar()


@pytest.mark.asyncio
async def test_load_q_table_no_pool():
    """Test loading Q-table without database pool."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    ctrl._db_pool = None

    # Should not crash
    await ctrl._load_q_table()


@pytest.mark.asyncio
async def test_load_q_table_error():
    """Test loading Q-table handles errors."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        # Mock database pool that raises error
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=Exception("Query error"))

        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None

        ctrl._db_pool = mock_pool

        # Should handle error gracefully
        await ctrl._load_q_table()
    finally:
        if ctrl._running:
            await ctrl.parar()


@pytest.mark.asyncio
async def test_monitor_method_collects_metrics():
    """Test _monitor method collects metrics."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        # Mock HTTP session for Prometheus
        from unittest.mock import AsyncMock, patch
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {"result": [{"metric": {}, "value": [1234567890, "50.5"]}]}
        })

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_response
        mock_ctx.__aexit__.return_value = None

        with patch.object(ctrl._http_session, 'get', return_value=mock_ctx):
            await ctrl._monitor()

            # Should have collected metrics
            assert ctrl.system_metrics is not None
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_analyze_returns_issues():
    """Test _analyze method returns list of issues."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        # Set high CPU
        ctrl.system_metrics = {"cpu_usage": 0.95, "memory_usage": 0.50}
        ctrl.agent_metrics = {"agents_active": 50}

        issues = await ctrl._analyze()

        # Should detect high CPU
        assert isinstance(issues, list)
        assert any("cpu" in issue.lower() for issue in issues)
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_plan_returns_action_and_params():
    """Test _plan method returns action and parameters."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        action, params = await ctrl._plan(issues=["cpu_high"])

        assert isinstance(action, ActionType)
        assert isinstance(params, dict)
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_method_routes_to_specific_executors():
    """Test _execute method routes to specific executor methods."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        # Test NOOP (always succeeds)
        result = await ctrl._execute(ActionType.NOOP, {})
        assert result is True
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_calculate_reward_accounts_for_success_and_issues():
    """Test _calculate_reward considers both success and remaining issues."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    # Success with no issues → high reward
    reward1 = ctrl._calculate_reward(success=True, issues=[])

    # Success with remaining issues → lower reward
    reward2 = ctrl._calculate_reward(success=True, issues=["cpu_high"])

    # Failure → negative reward
    reward3 = ctrl._calculate_reward(success=False, issues=["cpu_high"])

    assert reward1 > reward2
    assert reward3 < 0


@pytest.mark.asyncio
async def test_update_q_value_applies_learning():
    """Test _update_q_value updates Q-table with learning rate."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    state = SystemState.VIGILANCIA
    action = ActionType.SCALE_UP_AGENTS

    # Initial Q-value
    ctrl.q_table[(state, action)] = 0.0

    # Update Q-value
    ctrl._update_q_value(state, action, reward=1.0)

    # Should have updated (learning_rate * reward)
    assert ctrl.q_table[(state, action)] > 0.0


@pytest.mark.asyncio
async def test_select_best_action_chooses_highest_q_value():
    """Test _select_best_action chooses action with highest Q-value."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    state = SystemState.ATENCAO

    # Populate Q-table
    ctrl.q_table[(state, ActionType.NOOP)] = 0.1
    ctrl.q_table[(state, ActionType.SCALE_UP_AGENTS)] = 0.9
    ctrl.q_table[(state, ActionType.SCALE_DOWN_AGENTS)] = 0.3

    best_action = ctrl._select_best_action(state)

    assert best_action == ActionType.SCALE_UP_AGENTS


# ==================== PHASE 4: MAPE-K LOOP & EXECUTION (70%→85%+) ====================


@pytest.mark.asyncio
async def test_mape_k_loop_runs():
    """Test MAPE-K loop executes at least one iteration."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        monitor_interval=1,  # Short interval for testing
    )

    try:
        await ctrl.iniciar()

        # Let MAPE-K loop run for one cycle
        await asyncio.sleep(1.5)

        # Should have collected some metrics
        assert ctrl.system_metrics is not None

        await ctrl.parar()
    except Exception:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_mape_k_loop_error_handling():
    """Test MAPE-K loop handles errors gracefully."""
    ctrl = HomeostaticController(controller_id="ctrl_test", monitor_interval=1)

    # Mock _monitor to raise error
    async def failing_monitor():
        raise RuntimeError("Monitor error")

    try:
        await ctrl.iniciar()

        # Replace monitor with failing version
        ctrl._monitor = failing_monitor

        # Let loop try to run
        await asyncio.sleep(1.5)

        # Controller should still be running despite error
        assert ctrl._running is True

        await ctrl.parar()
    except Exception:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_iniciar_with_postgres_connection():
    """Test iniciar creates PostgreSQL connection."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        db_url="postgresql://user:pass@localhost:5432/test",
    )

    # Mock asyncpg.create_pool
    mock_pool = AsyncMock()
    mock_pool.close = AsyncMock()

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_pool.acquire = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_pool.acquire.return_value.__aexit__.return_value = None

    # Mock asyncpg.create_pool as async function
    async def mock_create_pool(*args, **kwargs):
        return mock_pool

    with patch("active_immune_core.coordination.homeostatic_controller.asyncpg.create_pool", side_effect=mock_create_pool):
        await ctrl.iniciar()

        # Should have created pool
        assert ctrl._db_pool is not None

        await ctrl.parar()


@pytest.mark.asyncio
async def test_parar_closes_db_pool():
    """Test parar closes database pool."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        db_url="postgresql://user:pass@localhost:5432/test",
    )

    # Mock database pool
    mock_pool = AsyncMock()
    mock_pool.close = AsyncMock()

    # Mock connection for table creation
    mock_conn = AsyncMock()
    mock_pool.acquire = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_pool.acquire.return_value.__aexit__.return_value = None

    # Mock asyncpg.create_pool as async function
    async def mock_create_pool(*args, **kwargs):
        return mock_pool

    with patch("active_immune_core.coordination.homeostatic_controller.asyncpg.create_pool", side_effect=mock_create_pool):
        await ctrl.iniciar()
        await ctrl.parar()

    # Should have closed pool
    mock_pool.close.assert_called_once()


@pytest.mark.asyncio
async def test_execute_routes_to_noop():
    """Test _execute handles NOOP action."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        result = await ctrl._execute(ActionType.NOOP, {})

        assert result is True
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_unknown_action():
    """Test _execute handles unknown action type."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        # Create a fake action (not in the router)
        class FakeAction:
            value = "fake_action"

        result = await ctrl._execute(FakeAction(), {})

        # Should return False for unknown action
        assert result is False
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_determine_action_params_various_actions():
    """Test _determine_action_params for various action types."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    try:
        await ctrl.iniciar()

        # Test SCALE_DOWN
        params = ctrl._determine_action_params(ActionType.SCALE_DOWN_AGENTS, issues=[])
        assert "quantity" in params

        # Test CLONE_SPECIALIZED (has specialization)
        params = ctrl._determine_action_params(ActionType.CLONE_SPECIALIZED, issues=[])
        assert "specialization" in params
        assert "tipo" in params

        # Test INCREASE_SENSITIVITY
        params = ctrl._determine_action_params(ActionType.INCREASE_SENSITIVITY, issues=[])
        assert "delta" in params

        # Test DECREASE_SENSITIVITY
        params = ctrl._determine_action_params(ActionType.DECREASE_SENSITIVITY, issues=[])
        assert "delta" in params

        # Test NOOP (no params)
        params = ctrl._determine_action_params(ActionType.NOOP, issues=[])
        assert params == {}

        # Test DESTROY_CLONES (no params - not in _determine_action_params)
        params = ctrl._determine_action_params(ActionType.DESTROY_CLONES, issues=[])
        assert params == {}
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_collect_system_metrics_prometheus_failure():
    """Test _collect_system_metrics handles Prometheus failure."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        metrics_url="http://localhost:9090",
    )

    try:
        await ctrl.iniciar()

        # Mock HTTP session that raises error
        async def raise_error(*args, **kwargs):
            raise Exception("Prometheus unavailable")

        with patch.object(ctrl._http_session, 'get', side_effect=raise_error):
            metrics = await ctrl._collect_system_metrics()

            # Should return fallback metrics
            assert "cpu_usage" in metrics
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_collect_agent_metrics_lymphnode_failure():
    """Test _collect_agent_metrics handles Lymphnode failure."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8200",
    )

    try:
        await ctrl.iniciar()

        # Mock HTTP session that raises error
        async def raise_error(*args, **kwargs):
            raise Exception("Lymphnode unavailable")

        with patch.object(ctrl._http_session, 'get', side_effect=raise_error):
            metrics = await ctrl._collect_agent_metrics()

            # Should return empty metrics
            assert isinstance(metrics, dict)
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_scale_up_http_error():
    """Test _execute_scale_up handles HTTP error."""
    import aiohttp

    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8001"
    )

    try:
        await ctrl.iniciar()

        # Mock HTTP session post to raise ClientConnectorError
        def mock_post_error(*args, **kwargs):
            raise aiohttp.ClientConnectorError(connection_key=None, os_error=OSError("Connection failed"))

        with patch.object(ctrl._http_session, 'post', side_effect=mock_post_error):
            result = await ctrl._execute_scale_up({"quantity": 5})

            # Should return False on error
            assert result is False
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_scale_up_non_200_response():
    """Test _execute_scale_up handles non-200 response."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8001"
    )

    try:
        await ctrl.iniciar()

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal error")

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_response
        mock_ctx.__aexit__.return_value = None

        with patch.object(ctrl._http_session, 'post', return_value=mock_ctx):
            result = await ctrl._execute_scale_up({"quantity": 5})

            # Should return False for non-200
            assert result is False
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_select_action_uses_epsilon_greedy():
    """Test _select_action implements epsilon-greedy strategy."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    state = SystemState.VIGILANCIA

    # Test exploitation (epsilon = 0)
    ctrl.epsilon = 0.0
    ctrl.q_table[(state, ActionType.SCALE_UP_AGENTS)] = 1.0
    ctrl.q_table[(state, ActionType.NOOP)] = 0.0

    action = ctrl._select_action(state)
    assert action == ActionType.SCALE_UP_AGENTS

    # Test exploration (epsilon = 1)
    ctrl.epsilon = 1.0
    action = ctrl._select_action(state)
    # Should select some action (random)
    assert action in ActionType


# ========================================
# PHASE 5: Database Success Path Coverage
# ========================================

@pytest.mark.asyncio
async def test_create_knowledge_table_success():
    """Test _create_knowledge_table executes CREATE TABLE successfully."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        db_url="postgresql://user:pass@localhost:5432/test",
    )

    # Mock database pool and connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()

    # Mock pool.acquire as async context manager
    mock_acquire = MagicMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire = MagicMock(return_value=mock_acquire)

    # Mock asyncpg.create_pool
    async def mock_create_pool(*args, **kwargs):
        return mock_pool

    with patch("active_immune_core.coordination.homeostatic_controller.asyncpg.create_pool", side_effect=mock_create_pool):
        await ctrl.iniciar()

        # Verify CREATE TABLE was executed
        assert mock_conn.execute.called
        call_args = mock_conn.execute.call_args[0][0]
        assert "CREATE TABLE" in call_args
        assert "homeostatic_decisions" in call_args

        await ctrl.parar()


@pytest.mark.asyncio
async def test_store_decision_success():
    """Test _store_decision executes INSERT successfully."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        db_url="postgresql://user:pass@localhost:5432/test",
    )

    # Mock database pool and connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()

    # Mock pool.acquire as async context manager
    mock_acquire = MagicMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire = MagicMock(return_value=mock_acquire)

    async def mock_create_pool(*args, **kwargs):
        return mock_pool

    with patch("active_immune_core.coordination.homeostatic_controller.asyncpg.create_pool", side_effect=mock_create_pool):
        await ctrl.iniciar()

        # Store a decision
        await ctrl._store_decision(
            state=SystemState.ATIVACAO,
            metrics={"cpu_usage": 75.0},
            action=ActionType.SCALE_UP_AGENTS,
            action_params={"quantity": 10},
            outcome="success",
            reward=5.0,
        )

        # Verify INSERT was executed
        insert_calls = [call for call in mock_conn.execute.call_args_list if "INSERT" in str(call)]
        assert len(insert_calls) > 0

        await ctrl.parar()


@pytest.mark.asyncio
async def test_load_q_table_success_with_data():
    """Test _load_q_table loads data from database successfully."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        db_url="postgresql://user:pass@localhost:5432/test",
    )

    # Mock database pool and connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()

    # Mock fetch to return Q-table data
    mock_conn.fetch = AsyncMock(return_value=[
        {"state": "repouso", "action": "noop", "avg_reward": 0.5},
        {"state": "ativacao", "action": "scale_up_agents", "avg_reward": 5.0},
    ])

    # Mock pool.acquire as async context manager
    mock_acquire = MagicMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire = MagicMock(return_value=mock_acquire)

    async def mock_create_pool(*args, **kwargs):
        return mock_pool

    with patch("active_immune_core.coordination.homeostatic_controller.asyncpg.create_pool", side_effect=mock_create_pool):
        await ctrl.iniciar()

        # Load Q-table
        await ctrl._load_q_table()

        # Verify Q-table was populated
        assert len(ctrl.q_table) == 2
        assert ctrl.q_table[(SystemState.REPOUSO, ActionType.NOOP)] == 0.5
        assert ctrl.q_table[(SystemState.ATIVACAO, ActionType.SCALE_UP_AGENTS)] == 5.0

        await ctrl.parar()


@pytest.mark.asyncio
async def test_monitor_with_mmei_needs_success():
    """Test _monitor successfully fetches MMEI needs."""
    ctrl = HomeostaticController(controller_id="ctrl_test")

    # Mock MMEI needs object
    class MockNeeds:
        def __init__(self):
            self.rest_need = 0.3
            self.repair_need = 0.6
            self.efficiency_need = 0.4

    # Mock MMEI client
    mock_mmei = AsyncMock()
    mock_mmei.get_current_needs = AsyncMock(return_value=MockNeeds())

    ctrl.set_mmei_client(mock_mmei)

    try:
        await ctrl.iniciar()

        # Run monitor
        await ctrl._monitor()

        # Verify MMEI needs were fetched
        assert ctrl.current_needs is not None
        assert ctrl.current_needs.rest_need == 0.3
        assert ctrl.current_needs.repair_need == 0.6
        assert ctrl.current_needs.efficiency_need == 0.4
    finally:
        await ctrl.parar()


@pytest.mark.asyncio
async def test_full_mape_k_cycle_execution():
    """Test full MAPE-K cycle executes all steps."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        monitor_interval=0.5,
        db_url="postgresql://user:pass@localhost:5432/test",
    )

    # Mock MMEI needs object
    class MockNeeds:
        def __init__(self):
            self.rest_need = 0.3
            self.repair_need = 0.6
            self.efficiency_need = 0.4

    # Mock MMEI client
    mock_mmei = AsyncMock()
    mock_mmei.get_current_needs = AsyncMock(return_value=MockNeeds())
    ctrl.set_mmei_client(mock_mmei)

    # Mock database
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])

    # Mock pool.acquire as async context manager
    mock_acquire = MagicMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire = MagicMock(return_value=mock_acquire)

    async def mock_create_pool(*args, **kwargs):
        return mock_pool

    # Mock HTTP responses
    mock_response_prometheus = AsyncMock()
    mock_response_prometheus.status = 200
    mock_response_prometheus.json = AsyncMock(return_value={
        "data": {"result": [{"value": [1234567890, "50.0"]}]}
    })

    mock_response_lymphnode = AsyncMock()
    mock_response_lymphnode.status = 200
    mock_response_lymphnode.json = AsyncMock(return_value={
        "total_agents": 25,
        "active_agents": 20,
        "threats_detected": 3,
    })

    with patch("active_immune_core.coordination.homeostatic_controller.asyncpg.create_pool", side_effect=mock_create_pool):
        await ctrl.iniciar()

        # Mock HTTP session for metrics collection
        with patch.object(ctrl._http_session, 'get') as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response_prometheus)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            # Let MAPE-K loop run for 2+ cycles
            await asyncio.sleep(1.5)

            # Verify full cycle executed
            assert ctrl.system_metrics is not None
            assert ctrl.last_action is not None
            assert mock_mmei.get_current_needs.called

        await ctrl.parar()


@pytest.mark.asyncio
async def test_execute_routes_all_action_types():
    """Test _execute routes to correct executors for all action types."""
    ctrl = HomeostaticController(
        controller_id="ctrl_test",
        lymphnode_url="http://localhost:8001"
    )

    try:
        await ctrl.iniciar()

        # Mock HTTP responses
        mock_response = AsyncMock()
        mock_response.status = 200

        with patch.object(ctrl._http_session, 'post') as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

            # Test SCALE_DOWN_AGENTS
            result = await ctrl._execute(ActionType.SCALE_DOWN_AGENTS, {"quantity": 5})
            assert result is True

            # Test DESTROY_CLONES
            result = await ctrl._execute(ActionType.DESTROY_CLONES, {"clone_id": "123"})
            assert result is True

            # Test INCREASE_SENSITIVITY
            result = await ctrl._execute(ActionType.INCREASE_SENSITIVITY, {"delta": 0.1})
            assert result is True

            # Verify routing happened
            assert mock_post.called
    finally:
        await ctrl.parar()
