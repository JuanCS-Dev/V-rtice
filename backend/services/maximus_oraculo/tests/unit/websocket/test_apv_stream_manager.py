"""Unit tests for APVStreamManager."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

from websocket.apv_stream_manager import (
    APVStreamManager,
    StreamMessage,
    WebSocketConnection,
)


# ==================== FIXTURES ====================


@pytest.fixture
def mock_websocket() -> MagicMock:
    """Create a mock WebSocket."""
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    ws.client = ("127.0.0.1", 12345)
    return ws


@pytest.fixture
def stream_manager() -> APVStreamManager:
    """Create an APVStreamManager (not started)."""
    manager = APVStreamManager(
        kafka_bootstrap_servers="localhost:9092",
        kafka_topic="test-topic",
    )
    return manager


# ==================== CONNECTION TESTS ====================


@pytest.mark.asyncio
async def test_connection_lifecycle(
    stream_manager: APVStreamManager,
    mock_websocket: MagicMock,
) -> None:
    """Test WebSocket connection lifecycle."""
    # Connect
    connection_id = await stream_manager.connect(mock_websocket)
    
    assert connection_id is not None
    assert len(stream_manager._connections) == 1
    assert connection_id in stream_manager._connections
    
    # Verify welcome message sent
    mock_websocket.send_text.assert_called_once()
    call_args = mock_websocket.send_text.call_args[0][0]
    message = json.loads(call_args)
    assert message["type"] == "heartbeat"
    assert message["payload"]["status"] == "connected"
    
    # Disconnect
    await stream_manager.disconnect(connection_id)
    
    assert len(stream_manager._connections) == 0
    mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_connections(stream_manager: APVStreamManager) -> None:
    """Test multiple concurrent connections."""
    # Create 3 connections
    ws1 = AsyncMock(spec=WebSocket)
    ws2 = AsyncMock(spec=WebSocket)
    ws3 = AsyncMock(spec=WebSocket)
    
    id1 = await stream_manager.connect(ws1)
    id2 = await stream_manager.connect(ws2)
    id3 = await stream_manager.connect(ws3)
    
    assert len(stream_manager._connections) == 3
    assert id1 != id2 != id3
    
    # Disconnect one
    await stream_manager.disconnect(id2)
    
    assert len(stream_manager._connections) == 2
    assert id1 in stream_manager._connections
    assert id3 in stream_manager._connections
    assert id2 not in stream_manager._connections


@pytest.mark.asyncio
async def test_disconnect_nonexistent_connection(
    stream_manager: APVStreamManager,
) -> None:
    """Test disconnecting a nonexistent connection."""
    # Should not raise error
    await stream_manager.disconnect("nonexistent-id")


# ==================== METRICS TESTS ====================


def test_get_metrics_initial_state(stream_manager: APVStreamManager) -> None:
    """Test metrics in initial state."""
    metrics = stream_manager.get_metrics()
    
    assert metrics["active_connections"] == 0
    assert metrics["total_messages_broadcast"] == 0
    assert metrics["uptime_seconds"] == 0.0
    assert metrics["is_running"] is False
    assert metrics["kafka_topic"] == "test-topic"


@pytest.mark.asyncio
async def test_get_metrics_after_connections(
    stream_manager: APVStreamManager,
) -> None:
    """Test metrics after adding connections."""
    # Add connection
    ws = AsyncMock(spec=WebSocket)
    await stream_manager.connect(ws)
    
    metrics = stream_manager.get_metrics()
    
    assert metrics["active_connections"] == 1


# ==================== STREAM MESSAGE TESTS ====================


def test_stream_message_creation() -> None:
    """Test StreamMessage creation."""
    message = StreamMessage(
        type="apv",
        timestamp="2024-01-10T12:00:00",
        payload={"cve_id": "CVE-2024-TEST"},
    )
    
    assert message.type == "apv"
    assert message.timestamp == "2024-01-10T12:00:00"
    assert message.payload["cve_id"] == "CVE-2024-TEST"


def test_websocket_connection_creation(mock_websocket: MagicMock) -> None:
    """Test WebSocketConnection creation."""
    connection = WebSocketConnection(
        connection_id="test-id",
        websocket=mock_websocket,
    )
    
    assert connection.connection_id == "test-id"
    assert connection.websocket == mock_websocket
    assert connection.messages_sent == 0
    assert isinstance(connection.connected_at, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=websocket", "--cov-report=term-missing"])
