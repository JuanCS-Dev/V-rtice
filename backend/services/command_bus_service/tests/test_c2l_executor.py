"""Tests for C2L Command Executor."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from backend.services.command_bus_service.audit_repository import AuditLog, AuditRepository
from backend.services.command_bus_service.c2l_executor import C2LCommandExecutor
from backend.services.command_bus_service.kill_switch import KillSwitch
from backend.services.command_bus_service.models import C2LCommand, C2LCommandType, CommandReceipt
from backend.services.command_bus_service.nats_publisher import NATSPublisher


@pytest.mark.asyncio
async def test_execute_mute():
    """Test MUTE command execution."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.MUTE,
        target_agents=["agent-456"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    assert "Layers: 1" in result.message
    assert audit_repo.count() == 1


@pytest.mark.asyncio
async def test_execute_isolate():
    """Test ISOLATE command execution."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.ISOLATE,
        target_agents=["agent-789"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    assert "Layers: 2" in result.message
    assert audit_repo.count() == 2


@pytest.mark.asyncio
async def test_execute_terminate():
    """Test TERMINATE command execution."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.TERMINATE,
        target_agents=["agent-999"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    assert "Layers: 3" in result.message
    assert audit_repo.count() == 3


@pytest.mark.asyncio
async def test_execute_multiple_targets():
    """Test command execution with multiple targets."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.MUTE,
        target_agents=["agent-1", "agent-2", "agent-3"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    assert "Layers: 3" in result.message  # 1 layer x 3 agents
    assert audit_repo.count() == 3


@pytest.mark.asyncio
async def test_execute_layer_failure_continues():
    """Test that execution continues even if a layer fails."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = Mock(spec=KillSwitch)
    kill_switch.graceful_shutdown = AsyncMock(side_effect=Exception("Test error"))
    kill_switch.force_kill = AsyncMock()
    kill_switch.network_quarantine = AsyncMock()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.TERMINATE,
        target_agents=["agent-fail"],
    )

    result = await executor.execute(command)

    # Should still complete even with layer 1 failure
    assert result.status == "COMPLETED"
    # All 3 layers should be attempted
    assert audit_repo.count() == 3
    # First audit should be failure
    logs = await audit_repo.get_by_command(command.id)
    assert logs[0].success is False


@pytest.mark.asyncio
async def test_cascade_terminate():
    """Test cascade termination of sub-agents."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    # Mock _get_sub_agents to return empty (no infinite recursion)
    executor._get_sub_agents = AsyncMock(return_value=[])

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.TERMINATE,
        target_agents=["parent-agent"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    assert "Cascade: 0" in result.message


@pytest.mark.asyncio
async def test_execute_failure():
    """Test command execution failure - layer error logged but continues."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = Mock(spec=KillSwitch)
    kill_switch.graceful_shutdown = AsyncMock(side_effect=Exception("Fatal error"))
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.MUTE,
        target_agents=["agent-error"],
    )

    result = await executor.execute(command)

    # Executor continues even with layer failures
    assert result.status == "COMPLETED"
    # Audit log should record the failure
    logs = await audit_repo.get_by_command(command.id)
    assert len(logs) == 1
    assert logs[0].success is False


@pytest.mark.asyncio
async def test_execute_snapshot_state():
    """Test SNAPSHOT_STATE command (no layers)."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.SNAPSHOT_STATE,
        target_agents=["agent-snapshot"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    assert audit_repo.count() == 0  # No layers executed


@pytest.mark.asyncio
async def test_get_sub_agents():
    """Test _get_sub_agents returns empty list."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    sub_agents = await executor._get_sub_agents("parent-agent")
    assert sub_agents == []


@pytest.mark.asyncio
async def test_execute_fatal_error():
    """Test command execution with fatal error."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = Mock(spec=AuditRepository)
    audit_repo.save = AsyncMock(side_effect=RuntimeError("Database down"))

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.MUTE,
        target_agents=["agent-db-error"],
    )

    result = await executor.execute(command)

    assert result.status == "FAILED"
    assert "Database down" in result.message


@pytest.mark.asyncio
async def test_execute_network_layer():
    """Test NETWORK layer execution (branch coverage)."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.ISOLATE,
        target_agents=["agent-network"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    # ISOLATE = SOFTWARE + NETWORK layers
    assert audit_repo.count() == 2
    logs = await audit_repo.get_by_command(command.id)
    assert any(log.layer == "NETWORK" for log in logs)


@pytest.mark.asyncio
async def test_cascade_with_sub_agents():
    """Test cascade termination WITH sub-agents."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    # Mock retorna 2 sub-agents (mas eles tb retornam empty para evitar loop infinito)
    async def mock_get_sub_agents(agent_id: str) -> list[str]:
        if agent_id == "parent-agent":
            return ["child-1", "child-2"]
        return []

    executor._get_sub_agents = mock_get_sub_agents

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.TERMINATE,
        target_agents=["parent-agent"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    assert "Cascade: 2" in result.message
    # Parent: 3 layers + Child1: 3 layers + Child2: 3 layers = 9
    assert audit_repo.count() == 9


@pytest.mark.asyncio
async def test_audit_get_all():
    """Test audit repository get_all method."""
    audit_repo = AuditRepository()

    # Add 3 logs
    for i in range(3):
        await audit_repo.save(AuditLog(
            command_id=uuid4(),
            layer="SOFTWARE",
            action="MUTE",
            success=True,
        ))

    all_logs = await audit_repo.get_all()
    assert len(all_logs) == 3


@pytest.mark.asyncio
async def test_execute_container_layer_failure():
    """Test CONTAINER layer failure (branch 155->158)."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = Mock(spec=KillSwitch)
    kill_switch.graceful_shutdown = AsyncMock()
    kill_switch.force_kill = AsyncMock(side_effect=Exception("Container kill failed"))
    kill_switch.network_quarantine = AsyncMock()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.TERMINATE,
        target_agents=["agent-container-fail"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    # All 3 layers attempted
    assert audit_repo.count() == 3
    logs = await audit_repo.get_by_command(command.id)
    # Layer 2 (CONTAINER) should be failure
    container_log = [log for log in logs if log.layer == "CONTAINER"][0]
    assert container_log.success is False
    assert "Container kill failed" in container_log.details["error"]


@pytest.mark.asyncio
async def test_execute_network_layer_failure():
    """Test NETWORK layer failure (complete branch 155->158)."""
    publisher = Mock(spec=NATSPublisher)
    kill_switch = Mock(spec=KillSwitch)
    kill_switch.graceful_shutdown = AsyncMock()
    kill_switch.force_kill = AsyncMock()
    kill_switch.network_quarantine = AsyncMock(side_effect=Exception("Network quarantine failed"))
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.TERMINATE,
        target_agents=["agent-network-fail"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    # All 3 layers attempted
    assert audit_repo.count() == 3
    logs = await audit_repo.get_by_command(command.id)
    # Layer 3 (NETWORK) should be failure
    network_log = [log for log in logs if log.layer == "NETWORK"][0]
    assert network_log.success is False
    assert "Network quarantine failed" in network_log.details["error"]


@pytest.mark.asyncio
async def test_cascade_terminate_with_failures():
    """Test cascade termination when sub-agent fails (branch 213->203)."""
    from datetime import datetime

    publisher = Mock(spec=NATSPublisher)
    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(publisher, kill_switch, audit_repo)

    # Mock _get_sub_agents to return 3 sub-agents
    async def mock_get_sub_agents(agent_id: str) -> list[str]:
        if agent_id == "parent-agent":
            return ["child-1", "child-2", "child-3"]
        return []

    executor._get_sub_agents = mock_get_sub_agents

    # Mock execute to fail for child-2
    original_execute = executor.execute

    call_count = {"count": 0}

    async def mock_execute(command: C2LCommand) -> CommandReceipt:
        call_count["count"] += 1
        # First call = parent (success)
        # Second call = child-1 (success)
        # Third call = child-2 (FAIL)
        # Fourth call = child-3 (success)
        if call_count["count"] == 3 and command.target_agents[0] == "child-2":
            return CommandReceipt(
                command_id=command.id,
                status="FAILED",
                message="Simulated failure",
                timestamp=datetime.utcnow(),
            )
        return await original_execute(command)

    executor.execute = mock_execute

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.TERMINATE,
        target_agents=["parent-agent"],
    )

    result = await executor.execute(command)

    assert result.status == "COMPLETED"
    # Only 2 out of 3 cascade terminated (child-2 failed)
    assert "Cascade: 2" in result.message
