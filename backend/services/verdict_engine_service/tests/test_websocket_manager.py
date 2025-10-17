"""Tests for WebSocket manager."""


import pytest
from models import WebSocketMessage
from websocket_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connection_manager_init():
    """Test ConnectionManager initialization."""
    manager = ConnectionManager()

    assert manager.active_connections == {}
    assert manager.get_connection_count() == 0


@pytest.mark.asyncio
async def test_connect_websocket(mocker):
    """Test WebSocket connection."""
    manager = ConnectionManager()
    websocket = mocker.AsyncMock()
    websocket.send_json = mocker.AsyncMock()
    client_id = "test-client-1"

    await manager.connect(websocket, client_id)

    assert client_id in manager.active_connections
    assert manager.get_connection_count() == 1
    websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect_websocket(mocker):
    """Test WebSocket disconnection."""
    manager = ConnectionManager()
    websocket = mocker.AsyncMock()
    websocket.send_json = mocker.AsyncMock()
    client_id = "test-client-1"

    await manager.connect(websocket, client_id)
    assert manager.get_connection_count() == 1

    await manager.disconnect(client_id)
    assert manager.get_connection_count() == 0
    assert client_id not in manager.active_connections


@pytest.mark.asyncio
async def test_send_personal(mocker, sample_verdict):
    """Test sending message to specific client."""
    manager = ConnectionManager()
    websocket = mocker.AsyncMock()  # Remove spec=WebSocket que causa bool() == False
    client_id = "test-client-1"

    await manager.connect(websocket, client_id)

    message = WebSocketMessage(type="verdict", data=sample_verdict)
    await manager.send_personal(message, client_id)

    websocket.send_json.assert_called_once_with(message.model_dump(mode="json"))


@pytest.mark.asyncio
async def test_send_personal_failure(mocker):
    """Test send_personal with WebSocket error."""
    manager = ConnectionManager()
    websocket = mocker.AsyncMock()  # Remove spec=WebSocket
    websocket.send_json.side_effect = Exception("Connection lost")
    client_id = "test-client-1"

    await manager.connect(websocket, client_id)

    message = WebSocketMessage(type="ping", data={})
    await manager.send_personal(message, client_id)

    # Client should be disconnected after error
    assert client_id not in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast_verdict(mocker, sample_verdict):
    """Test broadcasting verdict to all clients."""
    manager = ConnectionManager()
    ws1 = mocker.AsyncMock()
    ws2 = mocker.AsyncMock()

    await manager.connect(ws1, "client-1")
    await manager.connect(ws2, "client-2")

    await manager.broadcast_verdict(sample_verdict)

    ws1.send_json.assert_called_once()
    ws2.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_stats(mocker, sample_stats):
    """Test broadcasting stats to all clients."""
    manager = ConnectionManager()
    websocket = mocker.AsyncMock()
    websocket.send_json = mocker.AsyncMock()

    await manager.connect(websocket, "client-1")

    await manager.broadcast_stats(sample_stats)

    websocket.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_with_failures(mocker, sample_verdict):
    """Test broadcast handling client failures."""
    manager = ConnectionManager()
    ws1 = mocker.AsyncMock()
    ws2 = mocker.AsyncMock()
    ws2.send_json.side_effect = Exception("Failed")

    await manager.connect(ws1, "client-1")
    await manager.connect(ws2, "client-2")

    await manager.broadcast_verdict(sample_verdict)

    # ws1 should succeed
    assert "client-1" in manager.active_connections
    # ws2 should be disconnected after failure
    assert "client-2" not in manager.active_connections


@pytest.mark.asyncio
async def test_ping_all(mocker):
    """Test ping all connections."""
    manager = ConnectionManager()
    ws1 = mocker.AsyncMock()
    ws2 = mocker.AsyncMock()

    await manager.connect(ws1, "client-1")
    await manager.connect(ws2, "client-2")

    await manager.ping_all()

    assert ws1.send_json.call_count == 1
    assert ws2.send_json.call_count == 1
