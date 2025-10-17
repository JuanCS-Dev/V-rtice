"""Tests for NATS subscriber."""

import asyncio
from typing import TYPE_CHECKING, AsyncIterator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from c2l_executor import C2LCommandExecutor
from models import C2LCommand, C2LCommandType, CommandReceipt
from nats_subscriber import NATSSubscriber

if TYPE_CHECKING:
    from nats.aio.msg import Msg
else:
    Msg = object  # Runtime fallback


@pytest.mark.asyncio
async def test_subscriber_initialization():
    """Test subscriber initialization."""
    executor = Mock(spec=C2LCommandExecutor)
    subscriber = NATSSubscriber(executor)

    assert subscriber.nc is None
    assert subscriber.js is None
    assert subscriber.executor is executor


@pytest.mark.asyncio
async def test_subscribe_without_connection():
    """Test subscribing without NATS connection raises error."""
    executor = Mock(spec=C2LCommandExecutor)
    subscriber = NATSSubscriber(executor)

    with pytest.raises(RuntimeError, match="NATS not connected"):
        await subscriber.subscribe()


@pytest.mark.asyncio
async def test_connect():
    """Test NATS connection with mocked client."""
    executor = Mock(spec=C2LCommandExecutor)

    # Mock NATS client
    mock_nc = AsyncMock()
    mock_js = Mock()
    mock_nc.jetstream = Mock(return_value=mock_js)
    mock_nc.connect = AsyncMock()

    with patch("nats_subscriber.NATSClient", return_value=mock_nc):
        subscriber = NATSSubscriber(executor)
        await subscriber.connect()

        assert subscriber.nc is mock_nc
        assert subscriber.js is mock_js
        mock_nc.connect.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect():
    """Test NATS disconnection."""
    executor = Mock(spec=C2LCommandExecutor)
    subscriber = NATSSubscriber(executor)

    # Mock NATS client
    mock_nc = AsyncMock()
    subscriber.nc = mock_nc

    await subscriber.disconnect()
    mock_nc.close.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect_when_not_connected():
    """Test disconnect when nc is None."""
    executor = Mock(spec=C2LCommandExecutor)
    subscriber = NATSSubscriber(executor)

    # Should not raise error
    await subscriber.disconnect()
    assert subscriber.nc is None


@pytest.mark.asyncio
async def test_subscribe_message_processing():
    """Test message processing in subscribe loop."""
    executor = AsyncMock(spec=C2LCommandExecutor)
    subscriber = NATSSubscriber(executor)

    # Mock JS
    mock_js = AsyncMock()
    subscriber.js = mock_js

    # Mock message
    command = C2LCommand(
        operator_id="test-op",
        command_type=C2LCommandType.MUTE,
        target_agents=["agent-1"],
    )

    receipt = CommandReceipt(
        command_id=command.id,
        status="COMPLETED",
        message="Success",
    )

    mock_msg = AsyncMock()
    mock_msg.data = command.model_dump_json().encode()
    mock_msg.ack = AsyncMock()

    # Create async iterator mock
    async def async_message_generator() -> AsyncIterator[object]:
        yield mock_msg

    # Mock subscription with async iterator
    mock_subscription = AsyncMock()
    mock_subscription.messages = async_message_generator()

    mock_js.subscribe = AsyncMock(return_value=mock_subscription)
    executor.execute = AsyncMock(return_value=receipt)
    executor.publisher = AsyncMock()
    executor.publisher.publish_confirmation = AsyncMock()

    # Run subscribe in background, cancel after processing
    task = asyncio.create_task(subscriber.subscribe())
    await asyncio.sleep(0.05)  # Let it process message
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass

    # Verify
    mock_js.subscribe.assert_called_once()
    executor.execute.assert_called_once()
    executor.publisher.publish_confirmation.assert_called_once()
    mock_msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_subscribe_message_processing_error():
    """Test error handling in message processing."""
    executor = AsyncMock(spec=C2LCommandExecutor)
    subscriber = NATSSubscriber(executor)

    # Mock JS
    mock_js = AsyncMock()
    subscriber.js = mock_js

    # Mock invalid message
    mock_msg = AsyncMock()
    mock_msg.data = b"invalid json"
    mock_msg.nak = AsyncMock()

    # Create async iterator mock
    async def async_message_generator() -> AsyncIterator[object]:
        yield mock_msg

    # Mock subscription
    mock_subscription = AsyncMock()
    mock_subscription.messages = async_message_generator()

    mock_js.subscribe = AsyncMock(return_value=mock_subscription)

    # Run subscribe in background, cancel after processing
    task = asyncio.create_task(subscriber.subscribe())
    await asyncio.sleep(0.05)  # Let it process message
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass

    # Verify error handling
    mock_js.subscribe.assert_called_once()
    mock_msg.nak.assert_called_once()

