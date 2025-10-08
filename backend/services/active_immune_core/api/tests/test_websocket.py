"""WebSocket Tests - PRODUCTION-READY

Comprehensive tests for WebSocket real-time communication.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from fastapi.testclient import TestClient

# ==================== CONNECTION ====================


def test_websocket_connect_success(client: TestClient):
    """Test successful WebSocket connection"""
    with client.websocket_connect("/ws") as websocket:
        # Should receive welcome message
        data = websocket.receive_json()

        assert data["event_type"] == "connected"
        assert "connection_id" in data["data"]
        assert data["data"]["message"] == "Connected to Active Immune Core WebSocket"


def test_websocket_connect_with_client_id(client: TestClient):
    """Test WebSocket connection with custom client ID"""
    with client.websocket_connect("/ws?client_id=my_custom_id") as websocket:
        data = websocket.receive_json()

        assert data["event_type"] == "connected"
        assert "connection_id" in data["data"]


# ==================== PING/PONG ====================


def test_websocket_ping_pong(client: TestClient):
    """Test ping/pong health check"""
    with client.websocket_connect("/ws") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Send ping
        websocket.send_json({"action": "ping"})

        # Receive pong
        response = websocket.receive_json()

        assert response["success"] is True
        assert response["message"] == "pong"
        assert "timestamp" in response["data"]


# ==================== ROOM MANAGEMENT ====================


def test_websocket_join_room_success(client: TestClient):
    """Test joining a room"""
    with client.websocket_connect("/ws") as websocket:
        # Skip welcome message
        websocket.receive_json()

        # Join room
        websocket.send_json({"action": "join", "room": "agents"})

        response = websocket.receive_json()

        assert response["success"] is True
        assert "agents" in response["message"].lower()


def test_websocket_join_room_missing_room_name(client: TestClient):
    """Test joining room without room name"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"action": "join"})

        response = websocket.receive_json()

        assert response["success"] is False
        assert "required" in response["message"].lower()


def test_websocket_leave_room_success(client: TestClient):
    """Test leaving a room"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Join first
        websocket.send_json({"action": "join", "room": "agents"})
        websocket.receive_json()

        # Then leave
        websocket.send_json({"action": "leave", "room": "agents"})

        response = websocket.receive_json()

        assert response["success"] is True


# ==================== SUBSCRIPTION ====================


def test_websocket_subscribe_success(client: TestClient):
    """Test subscribing to event types"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"action": "subscribe", "data": {"event_types": ["agent_created", "agent_updated"]}})

        response = websocket.receive_json()

        assert response["success"] is True
        assert "subscribed" in response["message"].lower()


def test_websocket_subscribe_invalid_event_type(client: TestClient):
    """Test subscribing to invalid event type"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"action": "subscribe", "data": {"event_types": ["invalid_event_type"]}})

        response = websocket.receive_json()

        assert response["success"] is False
        assert "invalid" in response["message"].lower()


def test_websocket_unsubscribe_success(client: TestClient):
    """Test unsubscribing from event types"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Subscribe first
        websocket.send_json({"action": "subscribe", "data": {"event_types": ["agent_created"]}})
        websocket.receive_json()

        # Unsubscribe
        websocket.send_json({"action": "unsubscribe", "data": {"event_types": ["agent_created"]}})

        response = websocket.receive_json()

        assert response["success"] is True


# ==================== INFO ====================


def test_websocket_get_connection_info(client: TestClient):
    """Test getting connection information"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Join room and subscribe
        websocket.send_json({"action": "join", "room": "agents"})
        websocket.receive_json()

        websocket.send_json({"action": "subscribe", "data": {"event_types": ["agent_created"]}})
        websocket.receive_json()

        # Get info
        websocket.send_json({"action": "info"})

        response = websocket.receive_json()

        assert response["success"] is True
        assert "connection_id" in response["data"]
        assert "rooms" in response["data"]
        assert "subscriptions" in response["data"]
        assert "agents" in response["data"]["rooms"]


# ==================== INVALID ACTIONS ====================


def test_websocket_invalid_action(client: TestClient):
    """Test invalid action"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"action": "invalid_action"})

        response = websocket.receive_json()

        assert response["success"] is False
        assert "unknown action" in response["message"].lower()


def test_websocket_invalid_json(client: TestClient):
    """Test sending invalid JSON"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_text("invalid json{")

        response = websocket.receive_json()

        assert response["success"] is False
        assert "json" in response["message"].lower()


# ==================== BROADCASTING ====================


def test_websocket_receives_agent_created_event(client: TestClient):
    """Test receiving agent created event"""
    with client.websocket_connect("/ws") as websocket:
        # Skip welcome
        websocket.receive_json()

        # Join agents room
        websocket.send_json({"action": "join", "room": "agents"})
        websocket.receive_json()

        # Create agent via REST API
        client.post("/agents/", json={"agent_type": "neutrophil"})

        # Should receive WebSocket event
        event = websocket.receive_json()

        assert event["event_type"] == "agent_created"
        assert "agent_id" in event["data"]
        assert event["room"] == "agents"


def test_websocket_receives_agent_updated_event(client: TestClient):
    """Test receiving agent updated event"""
    # Create agent first
    agent_response = client.post("/agents/", json={"agent_type": "neutrophil"})
    agent_id = agent_response.json()["agent_id"]

    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Join room
        websocket.send_json({"action": "join", "room": "agents"})
        websocket.receive_json()

        # Update agent
        client.patch(f"/agents/{agent_id}", json={"status": "active"})

        # Receive updated event
        event = websocket.receive_json()

        assert event["event_type"] == "agent_updated"
        assert event["data"]["agent_id"] == agent_id


def test_websocket_receives_agent_deleted_event(client: TestClient):
    """Test receiving agent deleted event"""
    # Create agent first
    agent_response = client.post("/agents/", json={"agent_type": "neutrophil"})
    agent_id = agent_response.json()["agent_id"]

    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Join room
        websocket.send_json({"action": "join", "room": "agents"})
        websocket.receive_json()

        # Delete agent
        client.delete(f"/agents/{agent_id}")

        # Receive deleted event
        event = websocket.receive_json()

        assert event["event_type"] == "agent_deleted"
        assert event["data"]["agent_id"] == agent_id


def test_websocket_receives_task_created_event(client: TestClient):
    """Test receiving task created event"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Join tasks room
        websocket.send_json({"action": "join", "room": "tasks"})
        websocket.receive_json()

        # Create task
        client.post("/coordination/tasks", json={"task_type": "detection", "priority": 5})

        # Receive event
        event = websocket.receive_json()

        assert event["event_type"] == "task_created"
        assert "task_id" in event["data"]
        assert event["room"] == "tasks"


def test_websocket_receives_election_triggered_event(client: TestClient):
    """Test receiving election triggered event"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Join coordination room
        websocket.send_json({"action": "join", "room": "coordination"})
        websocket.receive_json()

        # Trigger election
        client.post("/coordination/election/trigger")

        # Receive election triggered event
        event = websocket.receive_json()

        assert event["event_type"] == "election_triggered"
        assert event["room"] == "coordination"


# ==================== SUBSCRIPTION FILTERING ====================


def test_websocket_subscription_filters_events(client: TestClient):
    """Test that subscription filters work"""
    # Create agent first
    agent_response = client.post("/agents/", json={"agent_type": "neutrophil"})
    agent_id = agent_response.json()["agent_id"]

    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Join room
        websocket.send_json({"action": "join", "room": "agents"})
        websocket.receive_json()

        # Subscribe ONLY to agent_deleted
        websocket.send_json({"action": "subscribe", "data": {"event_types": ["agent_deleted"]}})
        websocket.receive_json()

        # Update agent (should NOT receive this)
        client.patch(f"/agents/{agent_id}", json={"status": "active"})

        # Delete agent (should receive this)
        client.delete(f"/agents/{agent_id}")

        # Should only receive delete event
        event = websocket.receive_json()

        assert event["event_type"] == "agent_deleted"


# ==================== REST ENDPOINTS ====================


def test_get_websocket_stats(client: TestClient):
    """Test getting WebSocket statistics"""
    response = client.get("/ws/stats")

    assert response.status_code == 200
    data = response.json()

    assert "active_connections" in data
    assert "total_connections" in data
    assert "total_disconnections" in data
    assert "messages_sent" in data
    assert "messages_received" in data


def test_broadcast_event_via_rest(client: TestClient):
    """Test broadcasting event via REST endpoint"""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        # Join system room
        websocket.send_json({"action": "join", "room": "system"})
        websocket.receive_json()

        # Broadcast via REST
        response = client.post(
            "/ws/broadcast",
            params={"event_type": "alert_triggered", "room": "system"},
            json={
                "level": "warning",
                "message": "Test alert",
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Receive event
        event = websocket.receive_json()

        assert event["event_type"] == "alert_triggered"
        assert event["data"]["level"] == "warning"


def test_broadcast_event_invalid_type(client: TestClient):
    """Test broadcasting with invalid event type"""
    response = client.post("/ws/broadcast", params={"event_type": "invalid_event_type"}, json={"test": "data"})

    assert response.status_code == 400
    assert "invalid" in response.json()["message"].lower()
