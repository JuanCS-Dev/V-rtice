"""Tests for command bus service."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from backend.services.command_bus_service.main import app, lifespan
from backend.services.command_bus_service.models import (
    C2LCommand,
    C2LCommandType,
    CommandStatus,
    KillSwitchLayer,
    KillSwitchResult,
)
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture
def test_client():
    """Create test client with lifespan context."""
    with TestClient(app) as client:
        yield client


def test_health_check(test_client: TestClient) -> None:
    """Test health check endpoint."""
    response = test_client.get("/health/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "command-bus-service"
    assert data["version"] == "1.0.0"


def test_c2l_command_creation() -> None:
    """Test C2L Command model creation."""
    command = C2LCommand(
        operator_id="operator_001",
        command_type=C2LCommandType.ISOLATE,
        target_agents=["agent_a"],
        parameters={"reason": "suspicious_behavior"},
    )

    assert command.operator_id == "operator_001"
    assert command.command_type == C2LCommandType.ISOLATE
    assert command.status == CommandStatus.PENDING
    assert len(command.target_agents) == 1


def test_kill_switch_result() -> None:
    """Test KillSwitchResult model."""
    result = KillSwitchResult(
        agent_id="agent_malicious",
        layers_executed=[KillSwitchLayer.SOFTWARE, KillSwitchLayer.CONTAINER, KillSwitchLayer.NETWORK],
        success=True,
        details={"layer1_response": "shutdown_ok", "layer2_response": "container_destroyed", "layer3_response": "network_blocked"},
    )

    assert result.agent_id == "agent_malicious"
    assert len(result.layers_executed) == 3
    assert result.success is True
    assert KillSwitchLayer.NETWORK in result.layers_executed


def test_command_types_enum() -> None:
    """Test all C2L command types."""
    command_types = [
        C2LCommandType.MUTE,
        C2LCommandType.ISOLATE,
        C2LCommandType.TERMINATE,
        C2LCommandType.SNAPSHOT_STATE,
        C2LCommandType.REVOKE_ACCESS,
        C2LCommandType.INJECT_CONSTRAINT,
    ]

    for cmd_type in command_types:
        command = C2LCommand(operator_id="test_op", command_type=cmd_type, target_agents=["agent_x"])
        assert command.command_type == cmd_type


@pytest.mark.asyncio
async def test_lifespan_startup_shutdown():
    """Test application lifespan (startup and shutdown)."""
    # Mock all external dependencies
    mock_publisher = AsyncMock()
    mock_publisher.connect = AsyncMock()
    mock_publisher.disconnect = AsyncMock()

    mock_subscriber = AsyncMock()
    mock_subscriber.connect = AsyncMock()
    mock_subscriber.subscribe = AsyncMock(side_effect=asyncio.CancelledError())
    mock_subscriber.disconnect = AsyncMock()

    mock_executor = Mock()
    mock_audit_repo = Mock()
    mock_kill_switch = Mock()

    with (
        patch("backend.services.command_bus_service.main.NATSPublisher", return_value=mock_publisher),
        patch("backend.services.command_bus_service.main.NATSSubscriber", return_value=mock_subscriber),
        patch("backend.services.command_bus_service.main.C2LCommandExecutor", return_value=mock_executor),
        patch("backend.services.command_bus_service.main.AuditRepository", return_value=mock_audit_repo),
        patch("backend.services.command_bus_service.main.KillSwitch", return_value=mock_kill_switch),
    ):
        # Create mock FastAPI instance
        mock_app = Mock()

        # Run lifespan
        async with lifespan(mock_app):
            # Verify startup
            mock_publisher.connect.assert_called_once()
            mock_subscriber.connect.assert_called_once()

        # Verify shutdown
        mock_subscriber.disconnect.assert_called_once()
        mock_publisher.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_subscriber_task_cancellation():
    """Test that subscriber task is properly cancelled on shutdown."""
    mock_publisher = AsyncMock()
    mock_subscriber = AsyncMock()

    # Simulate long-running subscriber
    async def long_subscribe():
        try:
            await asyncio.sleep(1000)
        except asyncio.CancelledError:
            raise

    mock_subscriber.subscribe = long_subscribe

    with (
        patch("backend.services.command_bus_service.main.NATSPublisher", return_value=mock_publisher),
        patch("backend.services.command_bus_service.main.NATSSubscriber", return_value=mock_subscriber),
        patch("backend.services.command_bus_service.main.C2LCommandExecutor"),
        patch("backend.services.command_bus_service.main.AuditRepository"),
        patch("backend.services.command_bus_service.main.KillSwitch"),
    ):
        mock_app = Mock()

        async with lifespan(mock_app):
            # Startup completed
            await asyncio.sleep(0.1)

        # Shutdown should cancel task gracefully
        # No assertion needed - if CancelledError propagates, test fails

