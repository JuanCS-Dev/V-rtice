"""
Tests for Response Orchestrator.

Tests automated response planning and execution.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..response_orchestrator import (
    ResponseOrchestrator,
    ResponseConfig,
    ResponseAction,
    ResponsePlan,
    ResponseStatus,
    ResponsePriority,
    ActionType,
    SafetyCheck
)


@pytest.fixture
def config():
    """Create test configuration."""
    return ResponseConfig(
        auto_response_enabled=True,
        max_concurrent_actions=3,
        action_timeout_seconds=60,
        require_dual_approval=False,
        rollback_on_failure=True,
        safety_checks_enabled=True,
        critical_threshold=0.8,
        high_threshold=0.6,
        medium_threshold=0.4
    )


@pytest.fixture
def orchestrator(config):
    """Create test orchestrator."""
    return ResponseOrchestrator(config)


class TestResponseOrchestrator:
    """Test suite for ResponseOrchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.config is not None
        assert len(orchestrator.response_plans) == 0
        assert len(orchestrator.active_responses) == 0
        assert orchestrator.total_plans == 0
        assert orchestrator.total_actions == 0
        assert orchestrator._running is False

    @pytest.mark.asyncio
    async def test_create_response_plan_critical(self, orchestrator):
        """Test creating response plan for critical threat."""
        plan = await orchestrator.create_response_plan(
            threat_id="THREAT001",
            threat_score=0.9,
            threat_category="EXFILTRATION",
            entities={"ip": "10.0.0.100", "hostname": "infected-host"},
            mitre_tactics=["TA0010"]
        )

        assert plan.plan_id in orchestrator.response_plans
        assert plan.priority == ResponsePriority.CRITICAL
        assert plan.threat_score == 0.9
        assert len(plan.actions) > 0
        assert plan.auto_execute is True  # Critical threats auto-execute
        assert orchestrator.total_plans == 1

        # Should have critical actions
        action_types = [a.action_type for a in plan.actions]
        assert ActionType.BLOCK_IP in action_types
        assert ActionType.ISOLATE_HOST in action_types

    @pytest.mark.asyncio
    async def test_create_response_plan_high(self, orchestrator):
        """Test creating response plan for high threat."""
        plan = await orchestrator.create_response_plan(
            threat_id="THREAT002",
            threat_score=0.7,
            threat_category="CREDENTIAL_ACCESS",
            entities={"user": "admin", "ip": "192.168.1.50"}
        )

        assert plan.priority == ResponsePriority.HIGH
        assert len(plan.actions) > 0

        # Should have credential rotation
        action_types = [a.action_type for a in plan.actions]
        assert ActionType.ROTATE_CREDENTIALS in action_types

    @pytest.mark.asyncio
    async def test_create_response_plan_medium(self, orchestrator):
        """Test creating response plan for medium threat."""
        plan = await orchestrator.create_response_plan(
            threat_id="THREAT003",
            threat_score=0.5,
            threat_category="RECONNAISSANCE",
            entities={"ip": "10.0.0.200", "port": 22}
        )

        assert plan.priority == ResponsePriority.MEDIUM
        assert len(plan.actions) > 0

        # Should have defensive actions
        action_types = [a.action_type for a in plan.actions]
        assert ActionType.DEPLOY_HONEYPOT in action_types

    @pytest.mark.asyncio
    async def test_plan_execution_order(self, orchestrator):
        """Test execution order planning."""
        actions = [
            ResponseAction(
                action_type=ActionType.BLOCK_IP,
                target={"ip": "10.0.0.1"},
                priority=ResponsePriority.CRITICAL
            ),
            ResponseAction(
                action_type=ActionType.ISOLATE_HOST,
                target={"hostname": "host1"},
                priority=ResponsePriority.HIGH
            ),
            ResponseAction(
                action_type=ActionType.DEPLOY_HONEYPOT,
                target={"type": "ssh"},
                priority=ResponsePriority.MEDIUM
            )
        ]

        execution_order, parallel_groups = orchestrator._plan_execution_order(actions)

        # Critical should be first
        assert execution_order[0] == actions[0].action_id

        # Should have 3 parallel groups (one per priority)
        assert len(parallel_groups) == 3

    @pytest.mark.asyncio
    async def test_safety_checks_pass(self, orchestrator):
        """Test safety checks passing."""
        plan = ResponsePlan(
            name="Test Plan",
            description="Test",
            threat_id="TEST001",
            threat_score=0.5,
            actions=[],
            execution_order=[],
            priority=ResponsePriority.MEDIUM
        )

        checks_passed = await orchestrator._perform_safety_checks(plan)

        assert checks_passed is True
        assert len(orchestrator.safety_checks) > 0

    @pytest.mark.asyncio
    async def test_safety_checks_conflict(self, orchestrator):
        """Test safety checks with conflicts."""
        orchestrator.executing_actions.add("action1")

        plan = ResponsePlan(
            name="Test Plan",
            description="Test",
            threat_id="TEST001",
            threat_score=0.5,
            actions=[],
            execution_order=[],
            priority=ResponsePriority.MEDIUM
        )

        checks_passed = await orchestrator._perform_safety_checks(plan)

        # Should fail due to conflicting actions
        assert checks_passed is False

    @pytest.mark.asyncio
    async def test_execute_plan_success(self, orchestrator):
        """Test successful plan execution."""
        plan = await orchestrator.create_response_plan(
            threat_id="THREAT004",
            threat_score=0.6,
            threat_category="LATERAL_MOVEMENT",
            entities={"ip": "10.0.0.50"}
        )

        success = await orchestrator.execute_plan(plan.plan_id, approver="admin")

        assert success is True
        assert plan.status == ResponseStatus.COMPLETED
        assert plan.plan_id in orchestrator.completed_responses
        assert orchestrator.successful_actions > 0

    @pytest.mark.asyncio
    async def test_execute_plan_not_found(self, orchestrator):
        """Test executing non-existent plan."""
        success = await orchestrator.execute_plan("nonexistent")

        assert success is False

    @pytest.mark.asyncio
    async def test_execute_single_action(self, orchestrator):
        """Test executing a single action."""
        action = ResponseAction(
            action_type=ActionType.BLOCK_IP,
            target={"ip": "10.0.0.1"},
            priority=ResponsePriority.HIGH
        )

        result = await orchestrator._execute_single_action(action)

        assert result is True
        assert action.status == ResponseStatus.COMPLETED
        assert action.executed_at is not None
        assert orchestrator.successful_actions == 1

    @pytest.mark.asyncio
    async def test_execute_action_with_error(self, orchestrator):
        """Test action execution with error."""
        action = ResponseAction(
            action_type=ActionType.BLOCK_IP,
            target={"ip": "10.0.0.1"},
            priority=ResponsePriority.HIGH
        )

        # Mock route_action to raise error
        orchestrator._route_action = AsyncMock(side_effect=Exception("Test error"))

        result = await orchestrator._execute_single_action(action)

        assert result is False
        assert action.status == ResponseStatus.FAILED
        assert action.error_message == "Test error"
        assert orchestrator.failed_actions == 1

    @pytest.mark.asyncio
    async def test_route_action_block_ip(self, orchestrator):
        """Test routing block IP action."""
        action = ResponseAction(
            action_type=ActionType.BLOCK_IP,
            target={"ip": "10.0.0.1"},
            parameters={"duration_minutes": 30},
            priority=ResponsePriority.HIGH
        )

        result = await orchestrator._route_action(action)

        assert result is not None
        assert result["action"] == "block_ip"
        assert result["ip"] == "10.0.0.1"
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_route_action_isolate_host(self, orchestrator):
        """Test routing isolate host action."""
        action = ResponseAction(
            action_type=ActionType.ISOLATE_HOST,
            target={"hostname": "infected-host"},
            priority=ResponsePriority.CRITICAL
        )

        result = await orchestrator._route_action(action)

        assert result is not None
        assert result["action"] == "isolate_host"
        assert result["hostname"] == "infected-host"

    @pytest.mark.asyncio
    async def test_route_action_kill_process(self, orchestrator):
        """Test routing kill process action."""
        action = ResponseAction(
            action_type=ActionType.KILL_PROCESS,
            target={"pid": 1234, "process": "malware.exe"},
            priority=ResponsePriority.HIGH
        )

        result = await orchestrator._route_action(action)

        assert result is not None
        assert result["action"] == "kill_process"

    @pytest.mark.asyncio
    async def test_route_action_quarantine_file(self, orchestrator):
        """Test routing quarantine file action."""
        action = ResponseAction(
            action_type=ActionType.QUARANTINE_FILE,
            target={"file_path": "/tmp/malware.bin"},
            priority=ResponsePriority.HIGH
        )

        result = await orchestrator._route_action(action)

        assert result is not None
        assert result["action"] == "quarantine_file"

    @pytest.mark.asyncio
    async def test_route_action_disable_user(self, orchestrator):
        """Test routing disable user action."""
        action = ResponseAction(
            action_type=ActionType.DISABLE_USER,
            target={"user": "compromised_user"},
            priority=ResponsePriority.CRITICAL
        )

        result = await orchestrator._route_action(action)

        assert result is not None
        assert result["action"] == "disable_user"

    @pytest.mark.asyncio
    async def test_route_action_activate_kill_switch(self, orchestrator):
        """Test routing kill switch activation."""
        action = ResponseAction(
            action_type=ActionType.ACTIVATE_KILL_SWITCH,
            target={"system": "all"},
            parameters={"severity": "high"},
            priority=ResponsePriority.CRITICAL
        )

        result = await orchestrator._route_action(action)

        assert result is not None
        assert result["action"] == "activate_kill_switch"

    @pytest.mark.asyncio
    async def test_route_action_deploy_honeypot(self, orchestrator):
        """Test routing honeypot deployment."""
        action = ResponseAction(
            action_type=ActionType.DEPLOY_HONEYPOT,
            target={"type": "ssh_decoy"},
            parameters={"port": 2222},
            priority=ResponsePriority.MEDIUM
        )

        result = await orchestrator._route_action(action)

        assert result is not None
        assert result["action"] == "deploy_honeypot"

    @pytest.mark.asyncio
    async def test_concurrent_action_execution(self, orchestrator):
        """Test concurrent action execution."""
        orchestrator.config.max_concurrent_actions = 2

        actions = [
            ResponseAction(
                action_type=ActionType.BLOCK_IP,
                target={"ip": f"10.0.0.{i}"},
                priority=ResponsePriority.HIGH
            )
            for i in range(5)
        ]

        # Execute all actions
        tasks = [orchestrator._execute_single_action(a) for a in actions]
        results = await asyncio.gather(*tasks)

        assert all(results)
        assert orchestrator.successful_actions == 5

    @pytest.mark.asyncio
    async def test_rollback_on_failure(self, orchestrator):
        """Test rollback on plan failure."""
        plan = ResponsePlan(
            name="Test Plan",
            description="Test",
            threat_id="TEST001",
            threat_score=0.7,
            actions=[
                ResponseAction(
                    action_id="act1",
                    action_type=ActionType.BLOCK_IP,
                    target={"ip": "10.0.0.1"},
                    priority=ResponsePriority.HIGH,
                    reversible=True
                )
            ],
            execution_order=["act1"],
            priority=ResponsePriority.HIGH
        )

        plan.executed_actions = ["act1"]
        plan.status = ResponseStatus.FAILED

        await orchestrator._rollback_plan(plan)

        assert plan.status == ResponseStatus.ROLLBACK
        assert orchestrator.rollback_count == 1

    @pytest.mark.asyncio
    async def test_get_response_status(self, orchestrator):
        """Test getting response status."""
        # Create and execute a plan
        plan = await orchestrator.create_response_plan(
            threat_id="THREAT005",
            threat_score=0.7,
            threat_category="LATERAL_MOVEMENT",
            entities={"ip": "10.0.0.100"}
        )

        await orchestrator.execute_plan(plan.plan_id)

        status = await orchestrator.get_response_status()

        assert "active_plans" in status
        assert "completed_plans" in status
        assert "total_plans" in status
        assert status["total_plans"] == 1
        assert status["completed_plans"] == 1

    @pytest.mark.asyncio
    async def test_start_stop(self, orchestrator):
        """Test starting and stopping orchestrator."""
        await orchestrator.start()
        assert orchestrator._running is True

        await orchestrator.stop()
        assert orchestrator._running is False

    @pytest.mark.asyncio
    async def test_get_metrics(self, orchestrator):
        """Test getting orchestrator metrics."""
        # Create some activity
        await orchestrator.create_response_plan(
            threat_id="THREAT006",
            threat_score=0.8,
            threat_category="EXFILTRATION",
            entities={"ip": "10.0.0.200"}
        )

        metrics = orchestrator.get_metrics()

        assert metrics["running"] is False
        assert metrics["total_plans"] == 1
        assert "success_rate" in metrics
        assert "safety_checks" in metrics

    @pytest.mark.asyncio
    async def test_parallel_group_execution(self, orchestrator):
        """Test parallel group execution."""
        plan = ResponsePlan(
            name="Test Plan",
            description="Test",
            threat_id="TEST002",
            threat_score=0.7,
            actions=[
                ResponseAction(
                    action_id="act1",
                    action_type=ActionType.BLOCK_IP,
                    target={"ip": "10.0.0.1"},
                    priority=ResponsePriority.HIGH
                ),
                ResponseAction(
                    action_id="act2",
                    action_type=ActionType.BLOCK_IP,
                    target={"ip": "10.0.0.2"},
                    priority=ResponsePriority.HIGH
                )
            ],
            execution_order=["act1", "act2"],
            parallel_groups=[["act1", "act2"]],
            priority=ResponsePriority.HIGH
        )

        success = await orchestrator._execute_actions(plan)

        assert success is True
        assert len(plan.executed_actions) == 2

    @pytest.mark.asyncio
    async def test_integration_with_firewall(self, orchestrator):
        """Test integration with firewall component."""
        # Mock firewall integration
        mock_firewall = AsyncMock()
        mock_firewall.block_ip = AsyncMock(return_value=True)
        orchestrator.firewall = mock_firewall

        action = ResponseAction(
            action_type=ActionType.BLOCK_IP,
            target={"ip": "10.0.0.1"},
            parameters={"duration_minutes": 60},
            priority=ResponsePriority.HIGH
        )

        result = await orchestrator._block_ip(action)

        assert result["success"] is True
        mock_firewall.block_ip.assert_called_once_with("10.0.0.1", 60)

    @pytest.mark.asyncio
    async def test_integration_with_kill_switch(self, orchestrator):
        """Test integration with kill switch component."""
        # Mock kill switch integration
        mock_kill_switch = AsyncMock()
        mock_kill_switch.activate = AsyncMock(return_value=True)
        orchestrator.kill_switch = mock_kill_switch

        action = ResponseAction(
            action_type=ActionType.ACTIVATE_KILL_SWITCH,
            target={"system": "all"},
            parameters={"severity": "critical"},
            priority=ResponsePriority.CRITICAL
        )

        result = await orchestrator._activate_kill_switch(action)

        assert result["success"] is True
        mock_kill_switch.activate.assert_called_once_with("critical")

    def test_repr(self, orchestrator):
        """Test string representation."""
        repr_str = repr(orchestrator)
        assert "ResponseOrchestrator" in repr_str
        assert "running=" in repr_str
        assert "plans=" in repr_str
        assert "success_rate=" in repr_str