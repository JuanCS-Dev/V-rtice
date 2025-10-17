"""Tests for command bus service."""

import pytest
from command_bus_service.main import app
from command_bus_service.models import (
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
