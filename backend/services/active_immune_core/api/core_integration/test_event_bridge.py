"""Event Bridge Tests - PRODUCTION-READY

Tests for EventBridge using mock WebSocket connections.

NO MOCKS for Core - graceful degradation tested.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
from typing import Any, Dict, List

import pytest

from .event_bridge import EventBridge

# ==================== MOCK WEBSOCKET ====================


class MockWebSocket:
    """Mock WebSocket for testing"""

    def __init__(self):
        self.accepted = False
        self.closed = False
        self.messages: List[Dict[str, Any]] = []

    async def accept(self):
        self.accepted = True

    async def close(self):
        self.closed = True

    async def send_json(self, data: Dict[str, Any]):
        self.messages.append(data)


# ==================== TESTS ====================


@pytest.mark.asyncio
async def test_initialization():
    """Test EventBridge initialization"""
    bridge = EventBridge(
        kafka_bootstrap="localhost:9999",
        redis_url="redis://localhost:9999",
    )

    assert bridge is not None
    assert bridge._running is False
    assert len(bridge._connections) == 0
    assert bridge.total_events_streamed == 0
    assert "EventBridge" in repr(bridge)


@pytest.mark.asyncio
async def test_lifecycle():
    """Test EventBridge start/stop lifecycle"""
    bridge = EventBridge(
        kafka_bootstrap="localhost:9999",  # Not running
        redis_url="redis://localhost:9999",  # Not running
    )

    # Start
    await bridge.start()
    assert bridge._running is True
    assert len(bridge._tasks) == 2  # Kafka + Redis tasks

    # Stop
    await bridge.stop()
    assert bridge._running is False
    assert len(bridge._tasks) == 0


@pytest.mark.asyncio
async def test_double_start_idempotent():
    """Test double start is idempotent"""
    bridge = EventBridge()

    await bridge.start()
    tasks_after_first_start = len(bridge._tasks)

    await bridge.start()  # Second start
    tasks_after_second_start = len(bridge._tasks)

    # Should not create duplicate tasks
    assert tasks_after_first_start == tasks_after_second_start

    await bridge.stop()


@pytest.mark.asyncio
async def test_stop_not_running():
    """Test stop when not running doesn't error"""
    bridge = EventBridge()

    # Stop without start
    await bridge.stop()  # Should not raise


@pytest.mark.asyncio
async def test_connect_websocket():
    """Test WebSocket connection"""
    bridge = EventBridge()
    await bridge.start()

    ws = MockWebSocket()

    # Connect
    await bridge.connect(ws)

    assert ws.accepted is True
    assert ws in bridge._connections
    assert len(bridge._connections) == 1
    assert bridge.total_connections == 1
    assert bridge.peak_connections == 1

    # Should receive welcome message
    assert len(ws.messages) == 1
    welcome = ws.messages[0]
    assert welcome["event"] == "connected"
    assert "subscriptions" in welcome["data"]

    await bridge.stop()


@pytest.mark.asyncio
async def test_connect_with_subscriptions():
    """Test WebSocket connection with specific subscriptions"""
    bridge = EventBridge()
    await bridge.start()

    ws = MockWebSocket()

    # Connect with specific subscriptions
    await bridge.connect(ws, subscriptions={"cytokine", "hormone"})

    assert ws in bridge._connections
    assert bridge._connection_subscriptions[ws] == {"cytokine", "hormone"}

    # Welcome message should show subscriptions
    welcome = ws.messages[0]
    assert set(welcome["data"]["subscriptions"]) == {"cytokine", "hormone"}

    await bridge.stop()


@pytest.mark.asyncio
async def test_disconnect_websocket():
    """Test WebSocket disconnection"""
    bridge = EventBridge()
    await bridge.start()

    ws = MockWebSocket()
    await bridge.connect(ws)

    # Disconnect
    await bridge.disconnect(ws)

    assert ws.closed is True
    assert ws not in bridge._connections
    assert len(bridge._connections) == 0

    await bridge.stop()


@pytest.mark.asyncio
async def test_multiple_connections():
    """Test multiple WebSocket connections"""
    bridge = EventBridge()
    await bridge.start()

    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    ws3 = MockWebSocket()

    # Connect multiple
    await bridge.connect(ws1)
    await bridge.connect(ws2)
    await bridge.connect(ws3)

    assert len(bridge._connections) == 3
    assert bridge.total_connections == 3
    assert bridge.peak_connections == 3

    # Disconnect one
    await bridge.disconnect(ws2)

    assert len(bridge._connections) == 2
    assert ws2 not in bridge._connections

    await bridge.stop()


@pytest.mark.asyncio
async def test_update_subscriptions():
    """Test updating client subscriptions"""
    bridge = EventBridge()
    await bridge.start()

    ws = MockWebSocket()
    await bridge.connect(ws, subscriptions={"cytokine"})

    # Update subscriptions
    await bridge.update_subscriptions(ws, {"hormone", "threat_detection"})

    assert bridge._connection_subscriptions[ws] == {"hormone", "threat_detection"}

    await bridge.stop()


@pytest.mark.asyncio
async def test_broadcast_event():
    """Test event broadcasting"""
    bridge = EventBridge()
    await bridge.start()

    # Connect multiple clients with different subscriptions
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    ws3 = MockWebSocket()

    await bridge.connect(ws1, subscriptions={"cytokine"})
    await bridge.connect(ws2, subscriptions={"hormone"})
    await bridge.connect(ws3, subscriptions={"cytokine", "hormone"})

    # Clear welcome messages
    ws1.messages.clear()
    ws2.messages.clear()
    ws3.messages.clear()

    # Broadcast cytokine event
    await bridge._broadcast_event(
        {
            "event": "cytokine",
            "data": {"test": "data"},
        }
    )

    # ws1 and ws3 should receive (subscribed to cytokine)
    # ws2 should NOT receive (not subscribed)
    assert len(ws1.messages) == 1
    assert len(ws2.messages) == 0
    assert len(ws3.messages) == 1

    # Broadcast hormone event
    await bridge._broadcast_event(
        {
            "event": "hormone",
            "data": {"test": "data"},
        }
    )

    # ws2 and ws3 should receive (subscribed to hormone)
    # ws1 should NOT receive new message
    assert len(ws1.messages) == 1  # Still 1
    assert len(ws2.messages) == 1  # Got hormone
    assert len(ws3.messages) == 2  # Got both

    await bridge.stop()


@pytest.mark.asyncio
async def test_emit_agent_state_event():
    """Test manual agent state event emission"""
    bridge = EventBridge()
    await bridge.start()

    ws = MockWebSocket()
    await bridge.connect(ws, subscriptions={"agent_state"})
    ws.messages.clear()

    # Emit agent state event
    await bridge.emit_agent_state_event(
        agent_id="test_agent",
        agent_type="MACROFAGO",
        old_status="patrulhando",
        new_status="fagocitando",
        area_patrulha="test_area",
        message={"reason": "threat_detected"},
    )

    # Should receive event
    assert len(ws.messages) == 1
    event = ws.messages[0]
    assert event["event"] == "agent_state"
    assert event["data"]["agent_id"] == "test_agent"
    assert event["data"]["new_status"] == "fagocitando"

    await bridge.stop()


@pytest.mark.asyncio
async def test_emit_threat_detection():
    """Test manual threat detection event emission"""
    bridge = EventBridge()
    await bridge.start()

    ws = MockWebSocket()
    await bridge.connect(ws, subscriptions={"threat_detection"})
    ws.messages.clear()

    # Emit threat detection event
    await bridge.emit_threat_detection(
        threat_id="threat_001",
        threat_type="malware",
        severity="high",
        detector_agent="macrofago_001",
        target="192.168.1.50",
        confidence=0.92,
        details={"hash": "a1b2c3"},
    )

    # Should receive event
    assert len(ws.messages) == 1
    event = ws.messages[0]
    assert event["event"] == "threat_detection"
    assert event["data"]["threat_id"] == "threat_001"
    assert event["data"]["confidence"] == 0.92

    await bridge.stop()


@pytest.mark.asyncio
async def test_event_filtering():
    """Test event filtering by subscription"""
    bridge = EventBridge()
    await bridge.start()

    # Client subscribed only to cytokines
    ws = MockWebSocket()
    await bridge.connect(ws, subscriptions={"cytokine"})
    ws.messages.clear()

    # Emit hormone event (not subscribed)
    await bridge._broadcast_event(
        {
            "event": "hormone",
            "data": {"test": "data"},
        }
    )

    # Should NOT receive
    assert len(ws.messages) == 0

    # Emit cytokine event (subscribed)
    await bridge._broadcast_event(
        {
            "event": "cytokine",
            "data": {"test": "data"},
        }
    )

    # Should receive
    assert len(ws.messages) == 1

    await bridge.stop()


@pytest.mark.asyncio
async def test_metrics():
    """Test EventBridge metrics"""
    bridge = EventBridge()

    # Initial metrics
    metrics = bridge.get_metrics()
    assert metrics["running"] is False
    assert metrics["active_connections"] == 0
    assert metrics["total_connections"] == 0

    await bridge.start()

    # After start
    metrics = bridge.get_metrics()
    assert metrics["running"] is True

    # Connect clients
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    await bridge.connect(ws1)
    await bridge.connect(ws2)

    metrics = bridge.get_metrics()
    assert metrics["active_connections"] == 2
    assert metrics["total_connections"] == 2
    assert metrics["peak_connections"] == 2

    # Disconnect one
    await bridge.disconnect(ws1)

    metrics = bridge.get_metrics()
    assert metrics["active_connections"] == 1
    assert metrics["peak_connections"] == 2  # Peak remains

    await bridge.stop()


@pytest.mark.asyncio
async def test_concurrent_broadcasting():
    """Test concurrent event broadcasting"""

    bridge = EventBridge()
    await bridge.start()

    # Connect multiple clients
    clients = []
    for i in range(10):
        ws = MockWebSocket()
        await bridge.connect(ws)
        ws.messages.clear()
        clients.append(ws)

    # Broadcast multiple events concurrently
    events = [{"event": "cytokine", "data": {"id": i}} for i in range(20)]

    broadcast_tasks = [bridge._broadcast_event(event) for event in events]

    await asyncio.gather(*broadcast_tasks)

    # All clients should receive all events
    for ws in clients:
        assert len(ws.messages) == 20

    await bridge.stop()


@pytest.mark.asyncio
async def test_repr():
    """Test EventBridge string representation"""
    bridge = EventBridge()

    repr_str = repr(bridge)

    assert "EventBridge" in repr_str
    assert "running=False" in repr_str
    assert "connections=0" in repr_str
