"""
Test Suite: websocket_gateway.py - 100% ABSOLUTE Coverage
==========================================================

Target: backend/shared/websocket_gateway.py
Estratégia: Testes exhaustivos de WebSocket manager, pub/sub e broadcasting
Meta: 100% statements + 100% branches
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import WebSocket, WebSocketDisconnect

from backend.shared.websocket_gateway import (
    Channel,
    ConnectionManager,
    MessageType,
    WebSocketMessage,
    create_websocket_app,
)


# ============================================================================
# ENUMS TESTS
# ============================================================================


class TestMessageType:
    """Test MessageType enum"""

    def test_message_type_values(self):
        """Test all MessageType values"""
        assert MessageType.PING == "ping"
        assert MessageType.PONG == "pong"
        assert MessageType.SUBSCRIBE == "subscribe"
        assert MessageType.UNSUBSCRIBE == "unsubscribe"
        assert MessageType.SUBSCRIBED == "subscribed"
        assert MessageType.UNSUBSCRIBED == "unsubscribed"
        assert MessageType.CONTAINER_STATUS == "container_status"
        assert MessageType.OSINT_PROGRESS == "osint_progress"
        assert MessageType.MAXIMUS_STREAM == "maximus_stream"
        assert MessageType.TASK_UPDATE == "task_update"
        assert MessageType.THREAT_ALERT == "threat_alert"
        assert MessageType.CONSCIOUSNESS_METRIC == "consciousness_metric"
        assert MessageType.ERROR == "error"
        assert MessageType.INFO == "info"


class TestChannel:
    """Test Channel enum"""

    def test_channel_values(self):
        """Test all Channel values"""
        assert Channel.CONTAINERS == "maximus:containers"
        assert Channel.OSINT == "maximus:osint"
        assert Channel.MAXIMUS_AI == "maximus:ai"
        assert Channel.TASKS == "maximus:tasks"
        assert Channel.THREATS == "maximus:threats"
        assert Channel.CONSCIOUSNESS == "maximus:consciousness"
        assert Channel.SYSTEM == "maximus:system"


# ============================================================================
# WEBSOCKET MESSAGE TESTS
# ============================================================================


class TestWebSocketMessage:
    """Test WebSocketMessage model"""

    def test_message_basic(self):
        """Test basic message creation"""
        msg = WebSocketMessage(type=MessageType.PING)
        assert msg.type == MessageType.PING
        assert msg.channel is None
        assert msg.data is None
        assert isinstance(msg.timestamp, datetime)
        assert msg.client_id is None

    def test_message_with_channel(self):
        """Test message with channel"""
        msg = WebSocketMessage(
            type=MessageType.CONTAINER_STATUS, channel=Channel.CONTAINERS
        )
        assert msg.type == MessageType.CONTAINER_STATUS
        assert msg.channel == Channel.CONTAINERS

    def test_message_with_data(self):
        """Test message with data"""
        data = {"status": "running", "container_id": "abc123"}
        msg = WebSocketMessage(
            type=MessageType.CONTAINER_STATUS,
            channel=Channel.CONTAINERS,
            data=data,
        )
        assert msg.data == data

    def test_message_with_client_id(self):
        """Test message with client ID"""
        msg = WebSocketMessage(type=MessageType.PING, client_id="client-123")
        assert msg.client_id == "client-123"

    def test_message_serialization(self):
        """Test message can be serialized to JSON"""
        msg = WebSocketMessage(
            type=MessageType.TASK_UPDATE,
            channel=Channel.TASKS,
            data={"task_id": "task-1", "progress": 50},
            client_id="client-1",
        )
        msg_dict = msg.model_dump()
        assert msg_dict["type"] == "task_update"
        assert msg_dict["channel"] == "maximus:tasks"
        assert msg_dict["data"]["progress"] == 50
        assert msg_dict["client_id"] == "client-1"


# ============================================================================
# CONNECTION MANAGER TESTS
# ============================================================================


class TestConnectionManagerInit:
    """Test ConnectionManager initialization"""

    @patch("backend.shared.websocket_gateway.aioredis")
    def test_init_without_redis(self, mock_aioredis):
        """Test initialization without Redis URL"""
        manager = ConnectionManager()
        assert manager.active_connections == {}
        assert manager.subscriptions == {}
        assert manager.redis_client is None
        assert manager.pubsub is None
        mock_aioredis.from_url.assert_not_called()

    def test_init_with_redis(self):
        """Test initialization with Redis URL"""
        manager = ConnectionManager(redis_url="redis://localhost:6379")
        
        # At __init__, redis_client is None (only set in start())
        assert manager.redis_url == "redis://localhost:6379"
        assert manager.redis_client is None
        assert manager.pubsub is None


class TestConnectionManagerConnect:
    """Test client connection"""

    @pytest.mark.asyncio
    async def test_connect_new_client(self):
        """Test connecting a new client"""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket)

        assert "client-1" in manager.active_connections
        assert manager.active_connections["client-1"] == websocket
        assert manager.subscriptions["client-1"] == set()
        websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_duplicate_client(self):
        """Test connecting duplicate client (should replace)"""
        manager = ConnectionManager()
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket1)
        await manager.connect("client-1", websocket2)

        assert manager.active_connections["client-1"] == websocket2
        assert websocket1.accept.call_count == 1
        assert websocket2.accept.call_count == 1


class TestConnectionManagerDisconnect:
    """Test client disconnection"""

    @pytest.mark.asyncio
    async def test_disconnect_existing_client(self):
        """Test disconnecting existing client"""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket)
        manager.disconnect("client-1")

        assert "client-1" not in manager.active_connections
        assert "client-1" not in manager.subscriptions

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_client(self):
        """Test disconnecting non-existent client (no-op)"""
        manager = ConnectionManager()
        # Should not raise error
        manager.disconnect("nonexistent-client")


class TestConnectionManagerSubscribe:
    """Test channel subscription"""

    @pytest.mark.asyncio
    async def test_subscribe_to_channel(self):
        """Test subscribing to a channel"""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket)
        await manager.subscribe("client-1", Channel.CONTAINERS)

        assert Channel.CONTAINERS in manager.subscriptions["client-1"]

    @pytest.mark.asyncio
    async def test_subscribe_multiple_channels(self):
        """Test subscribing to multiple channels"""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket)
        await manager.subscribe("client-1", Channel.CONTAINERS)
        await manager.subscribe("client-1", Channel.THREATS)

        assert Channel.CONTAINERS in manager.subscriptions["client-1"]
        assert Channel.THREATS in manager.subscriptions["client-1"]
        assert len(manager.subscriptions["client-1"]) == 2

    @pytest.mark.asyncio
    async def test_subscribe_duplicate_channel(self):
        """Test subscribing to same channel twice (idempotent)"""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket)
        await manager.subscribe("client-1", Channel.CONTAINERS)
        await manager.subscribe("client-1", Channel.CONTAINERS)

        assert len(manager.subscriptions["client-1"]) == 1


class TestConnectionManagerUnsubscribe:
    """Test channel unsubscription"""

    @pytest.mark.asyncio
    async def test_unsubscribe_from_channel(self):
        """Test unsubscribing from a channel"""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket)
        await manager.subscribe("client-1", Channel.CONTAINERS)
        await manager.unsubscribe("client-1", Channel.CONTAINERS)

        assert Channel.CONTAINERS not in manager.subscriptions["client-1"]

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_channel(self):
        """Test unsubscribing from non-subscribed channel (no-op)"""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket)
        # Should not raise error
        await manager.unsubscribe("client-1", Channel.CONTAINERS)


class TestConnectionManagerSendPersonal:
    """Test sending personal messages"""

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending message to specific client"""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", websocket)
        message = WebSocketMessage(type=MessageType.PONG)

        await manager.send_personal_message(message, "client-1")

        # Manager sends welcome message on connect + actual message
        assert websocket.send_json.call_count == 2
        # Last call should be our PONG
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "pong"

    @pytest.mark.asyncio
    async def test_send_personal_message_nonexistent_client(self):
        """Test sending message to non-existent client (no-op)"""
        manager = ConnectionManager()
        message = WebSocketMessage(type=MessageType.PONG)

        # Should not raise error
        await manager.send_personal_message(message, "nonexistent")


class TestConnectionManagerBroadcast:
    """Test broadcasting messages"""

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self):
        """Test broadcasting to channel subscribers"""
        manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws3 = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", ws1)
        await manager.connect("client-2", ws2)
        await manager.connect("client-3", ws3)

        await manager.subscribe("client-1", Channel.CONTAINERS)
        await manager.subscribe("client-2", Channel.CONTAINERS)
        # client-3 NOT subscribed

        message = WebSocketMessage(
            type=MessageType.CONTAINER_STATUS,
            channel=Channel.CONTAINERS,
            data={"status": "running"},
        )

        await manager.broadcast_to_channel(message, Channel.CONTAINERS)

        # Each subscribed client gets: welcome + subscribe confirmation + broadcast
        assert ws1.send_json.call_count == 3  # welcome + subscribed + container_status
        assert ws2.send_json.call_count == 3
        # ws3 only gets welcome (not subscribed)
        assert ws3.send_json.call_count == 1

    @pytest.mark.asyncio
    async def test_broadcast_empty_channel(self):
        """Test broadcasting to channel with no subscribers"""
        manager = ConnectionManager()
        message = WebSocketMessage(
            type=MessageType.CONTAINER_STATUS, channel=Channel.CONTAINERS
        )

        # Should not raise error
        await manager.broadcast_to_channel(message, Channel.CONTAINERS)


class TestConnectionManagerPublish:
    """Test Redis publish"""

    @pytest.mark.asyncio
    async def test_publish_without_redis(self):
        """Test publish when Redis not configured (no-op)"""
        manager = ConnectionManager()
        message = WebSocketMessage(
            type=MessageType.CONTAINER_STATUS, channel=Channel.CONTAINERS
        )

        # Should not raise error
        await manager.publish(message, Channel.CONTAINERS)

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.aioredis")
    async def test_publish_with_redis(self, mock_aioredis):
        """Test publish with Redis configured"""
        mock_redis = AsyncMock()
        # aioredis.from_url() is awaited, so return coroutine
        async def mock_from_url(*args, **kwargs):
            return mock_redis
        mock_aioredis.from_url = mock_from_url

        manager = ConnectionManager(redis_url="redis://localhost:6379")
        await manager.start()  # Initialize redis_client
        
        message = WebSocketMessage(
            type=MessageType.CONTAINER_STATUS,
            channel=Channel.CONTAINERS,
            data={"status": "running"},
        )

        await manager.publish(message, Channel.CONTAINERS)

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args[0]
        assert call_args[0] == "maximus:containers"
        # Verify JSON can be parsed
        assert json.loads(call_args[1])["type"] == "container_status"


class TestConnectionManagerRedisListener:
    """Test Redis listener (_redis_listener is internal, tested via start())"""

    @pytest.mark.asyncio
    async def test_start_without_redis(self):
        """Test start() when Redis not configured"""
        manager = ConnectionManager()
        await manager.start()  # Should not raise
        assert manager.redis_client is None
        assert manager.pubsub is None

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.aioredis")
    @patch("backend.shared.websocket_gateway.asyncio.create_task")  # Prevent background listener
    async def test_start_with_redis(self, mock_create_task, mock_aioredis):
        """Test start() with Redis configured"""
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_redis.pubsub = lambda: mock_pubsub
        
        async def mock_from_url(*args, **kwargs):
            return mock_redis
        mock_aioredis.from_url = mock_from_url

        manager = ConnectionManager(redis_url="redis://localhost:6379")
        await manager.start()
        
        assert manager.redis_client is not None
        assert manager.pubsub is not None
        mock_pubsub.subscribe.assert_called_once()
        # Verify background task was created
        mock_create_task.assert_called_once()


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================


class TestCreateWebSocketApp:
    """Test factory function"""

    def test_create_app_returns_fastapi_app(self):
        """Test factory returns FastAPI app"""
        app = create_websocket_app()
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)
        assert app.title == "MAXIMUS WebSocket Gateway"

    def test_health_endpoint(self):
        """Test /health endpoint"""
        from fastapi.testclient import TestClient
        app = create_websocket_app()
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "active_connections" in data
        assert "redis_connected" in data


# ============================================================================
# EDGE CASES AND INTEGRATION
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_multiple_clients_different_subscriptions(self):
        """Test multiple clients with different subscription sets"""
        manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", ws1)
        await manager.connect("client-2", ws2)

        await manager.subscribe("client-1", Channel.CONTAINERS)
        await manager.subscribe("client-1", Channel.THREATS)
        await manager.subscribe("client-2", Channel.OSINT)

        # Broadcast to CONTAINERS
        msg1 = WebSocketMessage(type=MessageType.CONTAINER_STATUS, channel=Channel.CONTAINERS)
        await manager.broadcast_to_channel(msg1, Channel.CONTAINERS)

        # ws1: welcome + subscribe(CONTAINERS) + subscribe(THREATS) + broadcast(CONTAINERS) = 4
        # ws2: welcome + subscribe(OSINT) = 2
        assert ws1.send_json.call_count == 4
        # Last call to ws1 should be CONTAINER_STATUS
        assert ws1.send_json.call_args[0][0]["type"] == "container_status"
        
        ws1.reset_mock()
        ws2.reset_mock()

        # Broadcast to OSINT
        msg2 = WebSocketMessage(type=MessageType.OSINT_PROGRESS, channel=Channel.OSINT)
        await manager.broadcast_to_channel(msg2, Channel.OSINT)

        # ws1 not subscribed to OSINT
        assert ws1.send_json.call_count == 0
        # ws2 subscribed to OSINT
        assert ws2.send_json.call_count == 1
        assert ws2.send_json.call_args[0][0]["type"] == "osint_progress"

    @pytest.mark.asyncio
    async def test_disconnect_removes_all_subscriptions(self):
        """Test disconnect cleans up all subscriptions"""
        manager = ConnectionManager()
        ws = AsyncMock(spec=WebSocket)

        await manager.connect("client-1", ws)
        await manager.subscribe("client-1", Channel.CONTAINERS)
        await manager.subscribe("client-1", Channel.THREATS)
        await manager.subscribe("client-1", Channel.OSINT)

        assert len(manager.subscriptions["client-1"]) == 3

        manager.disconnect("client-1")

        assert "client-1" not in manager.subscriptions

    @pytest.mark.asyncio
    async def test_message_timestamp_auto_generated(self):
        """Test message timestamp is auto-generated"""
        msg1 = WebSocketMessage(type=MessageType.PING)
        await asyncio.sleep(0.001)
        msg2 = WebSocketMessage(type=MessageType.PONG)

        assert msg1.timestamp != msg2.timestamp
        assert msg1.timestamp < msg2.timestamp


# ============================================================================
# COVERAGE COMPLETION - GAPS
# ============================================================================


class TestConnectionManagerStop:
    """Test stop() method"""

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.aioredis")
    @patch("backend.shared.websocket_gateway.asyncio.create_task")
    async def test_stop_with_redis(self, mock_create_task, mock_aioredis):
        """Test stop() closes Redis connections"""
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        mock_redis.pubsub = lambda: mock_pubsub
        mock_redis.close = AsyncMock()
        
        async def mock_from_url(*args, **kwargs):
            return mock_redis
        mock_aioredis.from_url = mock_from_url

        manager = ConnectionManager(redis_url="redis://localhost:6379")
        await manager.start()
        await manager.stop()
        
        assert manager._running is False
        mock_pubsub.unsubscribe.assert_called_once()
        mock_pubsub.close.assert_called_once()
        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_without_redis(self):
        """Test stop() without Redis (no-op)"""
        manager = ConnectionManager()
        await manager.stop()  # Should not raise
        assert manager._running is False


class TestConnectionManagerDisconnectCleanup:
    """Test disconnect edge cases"""

    @pytest.mark.asyncio
    async def test_disconnect_removes_subscriptions(self):
        """Test disconnect removes from subscription channels"""
        manager = ConnectionManager()
        ws = AsyncMock(spec=WebSocket)
        
        await manager.connect("client-1", ws)
        await manager.subscribe("client-1", Channel.CONTAINERS)
        await manager.subscribe("client-1", Channel.THREATS)
        
        # Verify in subscriptions
        assert "client-1" in manager.subscriptions
        assert len(manager.subscriptions["client-1"]) == 2
        
        manager.disconnect("client-1")
        
        # Verify cleanup
        assert "client-1" not in manager.active_connections
        assert "client-1" not in manager.subscriptions


class TestPublishHelpers:
    """Test standalone publish helper functions"""

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.manager")
    async def test_publish_container_status(self, mock_manager):
        """Test publish_container_status helper"""
        from backend.shared.websocket_gateway import publish_container_status
        mock_manager.publish = AsyncMock()
        
        data = {"status": "running", "container_id": "abc123"}
        await publish_container_status(data)
        
        mock_manager.publish.assert_called_once()
        call_args = mock_manager.publish.call_args[0]
        assert call_args[0].type == MessageType.CONTAINER_STATUS
        assert call_args[0].data == data
        assert call_args[1] == Channel.CONTAINERS

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.manager")
    async def test_publish_osint_progress(self, mock_manager):
        """Test publish_osint_progress helper"""
        from backend.shared.websocket_gateway import publish_osint_progress
        mock_manager.publish = AsyncMock()
        
        data = {"progress": 50, "target": "domain.com"}
        await publish_osint_progress(data)
        
        mock_manager.publish.assert_called_once()
        call_args = mock_manager.publish.call_args[0]
        assert call_args[0].type == MessageType.OSINT_PROGRESS
        assert call_args[1] == Channel.OSINT

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.manager")
    async def test_publish_maximus_stream(self, mock_manager):
        """Test publish_maximus_stream helper"""
        from backend.shared.websocket_gateway import publish_maximus_stream
        mock_manager.publish = AsyncMock()
        
        data = {"message": "Analyzing threat..."}
        await publish_maximus_stream(data)
        
        mock_manager.publish.assert_called_once()
        call_args = mock_manager.publish.call_args[0]
        assert call_args[0].type == MessageType.MAXIMUS_STREAM
        assert call_args[1] == Channel.MAXIMUS_AI

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.manager")
    async def test_publish_task_update(self, mock_manager):
        """Test publish_task_update helper"""
        from backend.shared.websocket_gateway import publish_task_update
        mock_manager.publish = AsyncMock()
        
        data = {"task_id": "task-123", "status": "completed"}
        await publish_task_update(data)
        
        mock_manager.publish.assert_called_once()
        call_args = mock_manager.publish.call_args[0]
        assert call_args[0].type == MessageType.TASK_UPDATE
        assert call_args[1] == Channel.TASKS

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.manager")
    async def test_publish_threat_alert(self, mock_manager):
        """Test publish_threat_alert helper"""
        from backend.shared.websocket_gateway import publish_threat_alert
        mock_manager.publish = AsyncMock()
        
        data = {"severity": "critical", "ip": "1.2.3.4"}
        await publish_threat_alert(data)
        
        mock_manager.publish.assert_called_once()
        call_args = mock_manager.publish.call_args[0]
        assert call_args[0].type == MessageType.THREAT_ALERT
        assert call_args[1] == Channel.THREATS


class TestPublishRedisError:
    """Test publish() Redis error handling"""

    @pytest.mark.asyncio
    @patch("backend.shared.websocket_gateway.aioredis")
    @patch("backend.shared.websocket_gateway.asyncio.create_task")
    async def test_publish_redis_error_still_broadcasts_locally(self, mock_create_task, mock_aioredis):
        """Test publish() broadcasts locally even if Redis fails"""
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_redis.pubsub = lambda: mock_pubsub
        # Make Redis publish raise error
        mock_redis.publish = AsyncMock(side_effect=Exception("Redis connection lost"))
        
        async def mock_from_url(*args, **kwargs):
            return mock_redis
        mock_aioredis.from_url = mock_from_url

        manager = ConnectionManager(redis_url="redis://localhost:6379")
        await manager.start()
        
        # Connect client
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("client-1", ws)
        await manager.subscribe("client-1", Channel.CONTAINERS)
        
        message = WebSocketMessage(
            type=MessageType.CONTAINER_STATUS,
            channel=Channel.CONTAINERS,
            data={"status": "running"},
        )
        
        # Should not raise despite Redis error
        await manager.publish(message, Channel.CONTAINERS)
        
        # Verify local broadcast still happened
        # welcome + subscribe + broadcast = 3
        assert ws.send_json.call_count == 3


# ============================================================================
# MOCK VALIDATION
# ============================================================================


def test_no_mocks_in_source():
    """Verify source file has no mock code"""
    with open("backend/shared/websocket_gateway.py") as f:
        content = f.read()
        assert "TODO" not in content
        assert "FIXME" not in content
        assert "mock" not in content.lower() or "mock_" in content.lower()  # Only test mocks allowed


def test_module_exports():
    """Test module exports expected symbols"""
    from backend.shared import websocket_gateway

    assert hasattr(websocket_gateway, "ConnectionManager")
    assert hasattr(websocket_gateway, "MessageType")
    assert hasattr(websocket_gateway, "Channel")
    assert hasattr(websocket_gateway, "WebSocketMessage")
    assert hasattr(websocket_gateway, "create_websocket_app")


# ============================================================================
# MISSING COVERAGE - 100% ABSOLUTO
# ============================================================================


class TestUnsubscribeEdgeCases:
    """Test unsubscribe with client_id not in subscriptions"""

    @pytest.mark.asyncio
    async def test_unsubscribe_client_not_in_subscriptions(self):
        """Test unsubscribe when client_id not in subscriptions dict"""
        manager = ConnectionManager()
        
        # Call unsubscribe on non-existent client - should not raise
        await manager.unsubscribe("ghost-client", Channel.CONTAINERS)
        
        # Verify no error and subscriptions still empty
        assert "ghost-client" not in manager.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_client_not_in_subscriptions(self):
        """Test subscribe when client_id not yet in subscriptions dict (tests L149->exit branch)"""
        manager = ConnectionManager()
        
        # Manually add client to active_connections but NOT subscriptions
        # This simulates edge case where client connected but subscriptions dict corrupted
        ws = AsyncMock(spec=WebSocket)
        manager.active_connections["ghost-client"] = ws
        # Deliberately NOT adding to subscriptions to test the else branch
        
        # Call subscribe - should return silently without error (branch 149->exit)
        await manager.subscribe("ghost-client", Channel.CONTAINERS)
        
        # Should still not be in subscriptions (method returned early)
        assert "ghost-client" not in manager.subscriptions


class TestBroadcastExceptionHandling:
    """Test broadcast exception handling and cleanup"""

    @pytest.mark.asyncio
    async def test_broadcast_exception_triggers_cleanup(self):
        """Test that broadcast exceptions trigger disconnection cleanup"""
        manager = ConnectionManager()
        
        # Connect 3 clients
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws3 = AsyncMock(spec=WebSocket)
        
        await manager.connect("client-1", ws1)
        await manager.connect("client-2", ws2)
        await manager.connect("client-3", ws3)
        
        # Subscribe all to same channel
        await manager.subscribe("client-1", Channel.THREATS)
        await manager.subscribe("client-2", Channel.THREATS)
        await manager.subscribe("client-3", Channel.THREATS)
        
        # Make client-2 fail on send
        ws2.send_json.side_effect = Exception("Connection lost")
        
        message = WebSocketMessage(
            type=MessageType.THREAT_ALERT,
            channel=Channel.THREATS,
            data={"threat": "critical"}
        )
        
        # Broadcast should handle exception and cleanup
        await manager.broadcast_to_channel(message, Channel.THREATS)
        
        # Verify client-2 was disconnected
        assert "client-2" not in manager.active_connections
        assert "client-2" not in manager.subscriptions
        
        # Verify other clients still connected
        assert "client-1" in manager.active_connections
        assert "client-3" in manager.active_connections


class TestRedisListenerLoop:
    """Test _redis_listener background task"""

    @pytest.mark.asyncio
    async def test_redis_listener_processes_valid_message(self):
        """Test _redis_listener processes valid Redis messages"""
        manager = ConnectionManager()
        
        # Mock pubsub to return one valid message
        mock_pubsub = AsyncMock()
        ws_msg = WebSocketMessage(
            type=MessageType.CONTAINER_STATUS,
            channel=Channel.CONTAINERS,
            data={"status": "running"}
        )
        
        messages = [
            {
                "type": "message",
                "channel": "maximus:containers",
                "data": ws_msg.model_dump_json()
            },
            None  # Timeout to allow loop to check _running
        ]
        
        call_idx = [0]
        async def get_msg(ignore_subscribe_messages=True, timeout=1.0):
            idx = call_idx[0]
            call_idx[0] += 1
            if idx < len(messages):
                msg = messages[idx]
                if msg:
                    return msg
            # After messages, return None and check if stopped
            await asyncio.sleep(0.01)
            return None
        
        mock_pubsub.get_message = get_msg
        manager.pubsub = mock_pubsub
        manager._running = True
        
        # Connect a client
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("client-1", ws)
        await manager.subscribe("client-1", Channel.CONTAINERS)
        
        # Run listener in background
        task = asyncio.create_task(manager._redis_listener())
        await asyncio.sleep(0.15)
        
        # Stop
        manager._running = False
        await asyncio.sleep(0.05)
        
        # Cleanup task
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Verify broadcast happened (welcome + subscribe + redis message = 3)
        assert ws.send_json.call_count >= 3

    @pytest.mark.asyncio
    async def test_redis_listener_handles_invalid_json(self):
        """Test _redis_listener handles invalid JSON"""
        manager = ConnectionManager()
        
        mock_pubsub = AsyncMock()
        messages = [
            {
                "type": "message",
                "channel": "maximus:containers",
                "data": "invalid {json"
            },
            None
        ]
        
        call_idx = [0]
        async def get_msg(ignore_subscribe_messages=True, timeout=1.0):
            idx = call_idx[0]
            call_idx[0] += 1
            if idx < len(messages):
                return messages[idx]
            await asyncio.sleep(0.01)
            return None
        
        mock_pubsub.get_message = get_msg
        manager.pubsub = mock_pubsub
        manager._running = True
        
        # Run listener
        task = asyncio.create_task(manager._redis_listener())
        await asyncio.sleep(0.1)
        
        manager._running = False
        await asyncio.sleep(0.05)
        
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Should not crash

    @pytest.mark.asyncio
    async def test_redis_listener_handles_get_message_exception(self):
        """Test _redis_listener handles get_message exceptions"""
        manager = ConnectionManager()
        
        mock_pubsub = AsyncMock()
        mock_pubsub.get_message = AsyncMock(side_effect=Exception("Redis down"))
        
        manager.pubsub = mock_pubsub
        manager._running = True
        
        # Should handle exception in try/except block and exit gracefully
        await manager._redis_listener()
        
        # Should complete without crash


class TestWebSocketAppLifecycle:
    """Test create_websocket_app lifecycle hooks"""

    @pytest.mark.asyncio
    async def test_startup_hook_calls_manager_start(self):
        """Test startup event calls manager.start()"""
        with patch("backend.shared.websocket_gateway.manager") as mock_manager:
            mock_manager.start = AsyncMock()
            
            app = create_websocket_app()
            
            # Trigger startup manually
            for handler in app.router.on_startup:
                await handler()
            
            mock_manager.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_hook_calls_manager_stop(self):
        """Test shutdown event calls manager.stop()"""
        with patch("backend.shared.websocket_gateway.manager") as mock_manager:
            mock_manager.stop = AsyncMock()
            
            app = create_websocket_app()
            
            # Trigger shutdown manually
            for handler in app.router.on_shutdown:
                await handler()
            
            mock_manager.stop.assert_called_once()


class TestWebSocketEndpoint:
    """Test websocket_endpoint handler"""

    @pytest.mark.asyncio
    async def test_websocket_endpoint_ping_pong(self):
        """Test websocket endpoint handles PING/PONG"""
        with patch("backend.shared.websocket_gateway.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = MagicMock()
            mock_manager.send_personal_message = AsyncMock()
            
            app = create_websocket_app()
            
            # Simulate websocket connection
            ws = AsyncMock(spec=WebSocket)
            
            # Simulate PING then disconnect
            call_count = 0
            async def mock_receive_json():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {"type": "ping"}
                else:
                    raise WebSocketDisconnect()
            
            ws.receive_json = mock_receive_json
            
            # Get endpoint handler
            endpoint = None
            for route in app.routes:
                if hasattr(route, 'path') and route.path == "/ws/{client_id}":
                    endpoint = route.endpoint
                    break
            
            assert endpoint is not None
            
            # Call endpoint
            await endpoint(ws, "test-client")
            
            # Verify PONG was sent
            mock_manager.send_personal_message.assert_called()
            args = mock_manager.send_personal_message.call_args
            assert args[0][0].type == MessageType.PONG

    @pytest.mark.asyncio
    async def test_websocket_endpoint_subscribe(self):
        """Test websocket endpoint handles SUBSCRIBE"""
        with patch("backend.shared.websocket_gateway.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = MagicMock()
            mock_manager.subscribe = AsyncMock()
            
            app = create_websocket_app()
            
            ws = AsyncMock(spec=WebSocket)
            
            call_count = 0
            async def mock_receive_json():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {
                        "type": "subscribe",
                        "channel": "maximus:containers"
                    }
                else:
                    raise WebSocketDisconnect()
            
            ws.receive_json = mock_receive_json
            
            endpoint = None
            for route in app.routes:
                if hasattr(route, 'path') and route.path == "/ws/{client_id}":
                    endpoint = route.endpoint
                    break
            
            await endpoint(ws, "test-client")
            
            # Verify subscribe was called
            mock_manager.subscribe.assert_called_with("test-client", Channel.CONTAINERS)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_unsubscribe(self):
        """Test websocket endpoint handles UNSUBSCRIBE"""
        with patch("backend.shared.websocket_gateway.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = MagicMock()
            mock_manager.unsubscribe = AsyncMock()
            
            app = create_websocket_app()
            
            ws = AsyncMock(spec=WebSocket)
            
            call_count = 0
            async def mock_receive_json():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {
                        "type": "unsubscribe",
                        "channel": "maximus:threats"
                    }
                else:
                    raise WebSocketDisconnect()
            
            ws.receive_json = mock_receive_json
            
            endpoint = None
            for route in app.routes:
                if hasattr(route, 'path') and route.path == "/ws/{client_id}":
                    endpoint = route.endpoint
                    break
            
            await endpoint(ws, "test-client")
            
            # Verify unsubscribe was called
            mock_manager.unsubscribe.assert_called_with("test-client", Channel.THREATS)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_unknown_message_type(self):
        """Test websocket endpoint handles unknown message types"""
        with patch("backend.shared.websocket_gateway.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = MagicMock()
            mock_manager.send_personal_message = AsyncMock()
            
            app = create_websocket_app()
            
            ws = AsyncMock(spec=WebSocket)
            
            call_count = 0
            async def mock_receive_json():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # Send valid message type but no channel/action
                    return {"type": "info", "data": {"message": "hello"}}
                else:
                    raise WebSocketDisconnect()
            
            ws.receive_json = mock_receive_json
            
            endpoint = None
            for route in app.routes:
                if hasattr(route, 'path') and route.path == "/ws/{client_id}":
                    endpoint = route.endpoint
                    break
            
            await endpoint(ws, "test-client")
            
            # Should send error for unhandled message type
            args = mock_manager.send_personal_message.call_args
            assert args is not None
            assert args[0][0].type == MessageType.ERROR
            assert "error" in args[0][0].data

    @pytest.mark.asyncio
    async def test_websocket_endpoint_handles_general_exception(self):
        """Test websocket endpoint handles general exceptions"""
        with patch("backend.shared.websocket_gateway.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = MagicMock()
            
            app = create_websocket_app()
            
            ws = AsyncMock(spec=WebSocket)
            ws.receive_json = AsyncMock(side_effect=Exception("Unexpected error"))
            
            endpoint = None
            for route in app.routes:
                if hasattr(route, 'path') and route.path == "/ws/{client_id}":
                    endpoint = route.endpoint
                    break
            
            # Should handle exception and disconnect
            await endpoint(ws, "test-client")
            
            mock_manager.disconnect.assert_called_with("test-client")
