"""Tests for NATS publisher."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from backend.services.command_bus_service.models import C2LCommand, C2LCommandType, CommandReceipt
from nats_publisher import NATSPublisher


@pytest.mark.asyncio
async def test_initialization():
    """Test publisher initialization."""
    publisher = NATSPublisher()
    assert publisher.nc is None
    assert publisher.js is None


@pytest.mark.asyncio
async def test_publish_command():
    """Test command publishing."""
    publisher = NATSPublisher()
    publisher.js = AsyncMock()

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.MUTE,
        target_agents=["agent-456"],
    )

    ack = Mock()
    ack.seq = 1
    publisher.js.publish = AsyncMock(return_value=ack)

    await publisher.publish_command(command)

    publisher.js.publish.assert_called_once()
    call_args = publisher.js.publish.call_args
    assert call_args[0][0] == "sovereign.commands.agent-456"


@pytest.mark.asyncio
async def test_publish_command_multiple_targets():
    """Test command publishing to multiple targets."""
    publisher = NATSPublisher()
    publisher.js = AsyncMock()

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.ISOLATE,
        target_agents=["agent-1", "agent-2", "agent-3"],
    )

    ack = Mock()
    ack.seq = 1
    publisher.js.publish = AsyncMock(return_value=ack)

    await publisher.publish_command(command)

    assert publisher.js.publish.call_count == 3


@pytest.mark.asyncio
async def test_publish_confirmation():
    """Test confirmation publishing."""
    publisher = NATSPublisher()
    publisher.js = AsyncMock()

    command_id = uuid4()
    receipt = CommandReceipt(
        command_id=command_id,
        status="COMPLETED",
        message="Test message",
    )

    ack = Mock()
    ack.seq = 2
    publisher.js.publish = AsyncMock(return_value=ack)

    await publisher.publish_confirmation(receipt)

    publisher.js.publish.assert_called_once()
    call_args = publisher.js.publish.call_args
    assert call_args[0][0] == f"sovereign.confirmations.{command_id}"


@pytest.mark.asyncio
async def test_publish_without_connection():
    """Test publishing without NATS connection raises error."""
    publisher = NATSPublisher()

    command = C2LCommand(
        id=uuid4(),
        operator_id="test-operator",
        command_type=C2LCommandType.MUTE,
        target_agents=["agent-456"],
    )

    with pytest.raises(RuntimeError, match="NATS not connected"):
        await publisher.publish_command(command)


@pytest.mark.asyncio
async def test_publish_confirmation_without_connection():
    """Test publishing confirmation without NATS connection raises error."""
    publisher = NATSPublisher()

    receipt = CommandReceipt(
        command_id=uuid4(),
        status="COMPLETED",
        message="Test message",
    )

    with pytest.raises(RuntimeError, match="NATS not connected"):
        await publisher.publish_confirmation(receipt)


@pytest.mark.asyncio
async def test_connect_disconnect():
    """Test connect and disconnect methods."""
    publisher = NATSPublisher()

    # Mock NATS client
    mock_nc = AsyncMock()
    mock_nc.jetstream = Mock(return_value="mock_js")
    publisher.nc = mock_nc

    await publisher.disconnect()
    mock_nc.close.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect_when_not_connected():
    """Test disconnect when nc is None."""
    publisher = NATSPublisher()
    # Should not raise error
    await publisher.disconnect()
    assert publisher.nc is None


@pytest.mark.asyncio
async def test_connect():
    """Test NATS connection with mocked client."""
    # Mock NATS client
    mock_nc = AsyncMock()
    mock_js = Mock()
    mock_nc.jetstream = Mock(return_value=mock_js)
    mock_nc.connect = AsyncMock()

    with patch("nats_publisher.NATSClient", return_value=mock_nc):
        publisher = NATSPublisher()
        await publisher.connect()

        assert publisher.nc is mock_nc
        assert publisher.js is mock_js
        mock_nc.connect.assert_called_once()

