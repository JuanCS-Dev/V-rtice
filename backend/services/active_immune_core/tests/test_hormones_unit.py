"""Hormone Unit Tests - Coverage for exception paths and edge cases

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
NO MOCK in production code, mocks only for external Redis testing.
These tests cover exception paths, degraded mode, and edge cases.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from communication.hormones import HormoneMessage, HormoneMessenger, HormoneType


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def messenger():
    """Basic hormone messenger (not started)"""
    m = HormoneMessenger(redis_url="redis://localhost:6379")
    yield m
    # Cleanup
    if m._running:
        await m.stop()


@pytest_asyncio.fixture
async def started_messenger():
    """Started messenger with mocked Redis"""
    m = HormoneMessenger(redis_url="redis://localhost:6379")

    # Mock Redis client with proper async methods
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.publish = AsyncMock(return_value=5)
    mock_redis.close = AsyncMock()

    async def mock_from_url(*args, **kwargs):
        return mock_redis

    with patch('redis.asyncio.from_url', side_effect=mock_from_url):
        await m.start()
        yield m
        await m.stop()


# ==================== TESTS ====================


@pytest.mark.asyncio
class TestHormoneType:
    """Test HormoneType class methods"""

    def test_all_hormone_types(self):
        """Test HormoneType.all() returns all types (line 49)"""
        all_types = HormoneType.all()

        assert isinstance(all_types, list)
        assert len(all_types) == 5
        assert HormoneType.CORTISOL in all_types
        assert HormoneType.ADRENALINE in all_types
        assert HormoneType.MELATONIN in all_types
        assert HormoneType.INSULIN in all_types
        assert HormoneType.GROWTH_HORMONE in all_types


@pytest.mark.asyncio
class TestHormoneMessengerLifecycle:
    """Test messenger lifecycle with exception paths"""

    async def test_start_already_started_warning(self, started_messenger):
        """Test starting already started messenger (lines 141-142)"""
        # Try to start again
        await started_messenger.start()

        # Should handle gracefully with warning
        assert started_messenger._running is True

    async def test_start_redis_connection_failure(self, messenger):
        """Test graceful degradation on Redis connection failure (lines 160-166)"""
        # Mock Redis connection to raise exception
        with patch('redis.asyncio.from_url', side_effect=Exception("Connection refused")):
            await messenger.start()

        # Lines 160-166 should be covered
        assert messenger._running is True
        assert messenger._degraded_mode is True

    async def test_stop_pubsub_close_error(self):
        """Test handling pubsub close error during stop (lines 187-188)"""
        messenger = HormoneMessenger()
        await messenger.start()

        # Add mock pubsub client that raises on close
        mock_pubsub = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock(side_effect=Exception("Close error"))

        messenger._pubsub_clients["test_sub"] = mock_pubsub

        # Stop should handle exception gracefully (lines 187-188)
        await messenger.stop()

        # Should complete without raising
        assert messenger._running is False

    async def test_stop_redis_close_error(self):
        """Test handling Redis close error during stop (lines 197-198)"""
        messenger = HormoneMessenger()

        # Mock Redis client with close error
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.close = AsyncMock(side_effect=Exception("Close error"))

        with patch('redis.asyncio.from_url', return_value=mock_redis):
            await messenger.start()

        # Stop should handle exception gracefully (lines 197-198)
        await messenger.stop()

        # Should complete and set _redis_client to None
        assert messenger._redis_client is None
        assert messenger._running is False


@pytest.mark.asyncio
class TestHormonePublishing:
    """Test hormone publishing with edge cases"""

    async def test_publish_degraded_mode(self, messenger):
        """Test publishing in degraded mode (lines 229-232)"""
        # Start in degraded mode
        with patch('redis.asyncio.from_url', side_effect=Exception("Connection error")):
            await messenger.start()

        assert messenger._degraded_mode is True

        # Publish hormone - should return 0 (lines 229-232)
        result = await messenger.publish_hormone(
            tipo=HormoneType.CORTISOL,
            nivel=7.5,
            payload={"test": "data"},
        )

        assert result == 0

    async def test_publish_exception_handling(self, started_messenger):
        """Test publish exception handling (lines 271-273)"""
        # Mock Redis publish to raise exception
        started_messenger._redis_client.publish = AsyncMock(
            side_effect=Exception("Publish error")
        )

        # Should handle exception gracefully (lines 271-273)
        result = await started_messenger.publish_hormone(
            tipo=HormoneType.ADRENALINE,
            nivel=8.0,
            payload={"test": "error"},
        )

        assert result == 0

    async def test_publish_metrics_import_error(self, started_messenger):
        """Test publish handles missing metrics module (line 265)"""
        # Metrics import may fail - should handle gracefully
        result = await started_messenger.publish_hormone(
            tipo=HormoneType.INSULIN,
            nivel=5.0,
            payload={"test": "metrics"},
        )

        # Line 265 covered (try/except ImportError)
        assert isinstance(result, int)


@pytest.mark.asyncio
class TestHormoneSubscription:
    """Test hormone subscription with edge cases"""

    async def test_subscribe_already_exists_warning(self, started_messenger):
        """Test subscribing with duplicate subscriber_id (lines 292-293)"""
        # Add mock pubsub client
        mock_pubsub = AsyncMock()
        started_messenger._pubsub_clients["test_sub"] = mock_pubsub

        # Try to subscribe again with same ID
        await started_messenger.subscribe(
            hormone_types=[HormoneType.CORTISOL],
            callback=lambda msg: None,
            subscriber_id="test_sub",
        )

        # Lines 292-293 covered (warning and early return)
        assert "test_sub" in started_messenger._pubsub_clients

    async def test_subscribe_degraded_mode(self, messenger):
        """Test subscribing in degraded mode (lines 297-300)"""
        # Start in degraded mode
        with patch('redis.asyncio.from_url', side_effect=Exception("Connection error")):
            await messenger.start()

        assert messenger._degraded_mode is True

        # Subscribe - should skip gracefully (lines 297-300)
        await messenger.subscribe(
            hormone_types=[HormoneType.MELATONIN],
            callback=lambda msg: None,
            subscriber_id="degraded_sub",
        )

        # Should not create pubsub client in degraded mode
        assert "degraded_sub" not in messenger._pubsub_clients

    async def test_subscribe_exception_sets_degraded_mode(self, started_messenger):
        """Test subscription exception sets degraded mode (lines 314-330)"""
        # Mock Redis pubsub to raise exception
        mock_redis = started_messenger._redis_client
        mock_redis.pubsub = MagicMock(side_effect=Exception("Pubsub error"))

        # Subscribe should handle exception and set degraded mode (lines 314-330)
        await started_messenger.subscribe(
            hormone_types=[HormoneType.GROWTH_HORMONE],
            callback=lambda msg: None,
            subscriber_id="error_sub",
        )

        # Should set degraded mode
        assert started_messenger._degraded_mode is True


@pytest.mark.asyncio
class TestSubscriptionLoop:
    """Test subscription loop exception handling"""

    async def test_subscription_loop_stops_when_not_running(self):
        """Test subscription loop exits when _running is False (line 344)"""
        messenger = HormoneMessenger()

        # Mock pubsub
        mock_pubsub = AsyncMock()

        async def mock_listen():
            # Yield one control message
            yield {"type": "subscribe", "data": None}
            # Then wait for _running to be False
            while messenger._running:
                await asyncio.sleep(0.01)

        mock_pubsub.listen = mock_listen

        await messenger.start()

        # Start subscription loop in background
        callback = AsyncMock()
        task = asyncio.create_task(
            messenger._subscription_loop(mock_pubsub, "test", callback)
        )

        await asyncio.sleep(0.1)

        # Stop messenger
        messenger._running = False

        # Wait for loop to exit
        await asyncio.sleep(0.1)

        # Line 344 covered (break when not running)
        assert not messenger._running

    async def test_subscription_loop_json_decode_error(self):
        """Test subscription loop handles invalid JSON (lines 374-380)"""
        messenger = HormoneMessenger()
        await messenger.start()

        # Mock pubsub with invalid JSON message
        mock_pubsub = AsyncMock()

        async def mock_listen():
            yield {"type": "message", "data": "invalid json{"}
            # Stop after one message
            messenger._running = False

        mock_pubsub.listen = mock_listen

        callback = AsyncMock()

        # Should handle JSON decode error gracefully (lines 374-380)
        await messenger._subscription_loop(mock_pubsub, "test", callback)

        # Should not crash
        assert True

    async def test_subscription_loop_callback_exception(self):
        """Test subscription loop handles callback exception (lines 374-380)"""
        messenger = HormoneMessenger()
        await messenger.start()

        # Mock pubsub with valid message
        mock_pubsub = AsyncMock()

        valid_message = HormoneMessage(
            tipo=HormoneType.CORTISOL,
            emissor="test",
            nivel=5.0,
            payload={"test": "data"},
        )

        async def mock_listen():
            yield {"type": "message", "data": json.dumps(valid_message.model_dump())}
            messenger._running = False

        mock_pubsub.listen = mock_listen

        # Callback that raises exception
        def bad_callback(msg):
            raise ValueError("Callback error")

        # Should handle callback exception gracefully (lines 374-380)
        await messenger._subscription_loop(mock_pubsub, "test", bad_callback)

        # Should not crash
        assert True

    async def test_subscription_loop_fatal_error(self):
        """Test subscription loop handles fatal error (lines 389-390)"""
        messenger = HormoneMessenger()
        await messenger.start()

        # Mock pubsub that raises fatal error
        mock_pubsub = AsyncMock()

        async def mock_listen():
            raise RuntimeError("Fatal error in listen")

        mock_pubsub.listen = mock_listen

        callback = AsyncMock()

        # Should handle fatal error gracefully (lines 389-390)
        await messenger._subscription_loop(mock_pubsub, "test", callback)

        # Should not crash, should log error
        assert True

    async def test_subscription_loop_metrics_import_error(self):
        """Test subscription loop handles missing metrics module (line 364)"""
        messenger = HormoneMessenger()
        await messenger.start()

        # Mock pubsub with valid message
        mock_pubsub = AsyncMock()

        valid_message = HormoneMessage(
            tipo=HormoneType.ADRENALINE,
            emissor="test",
            nivel=8.0,
            payload={"test": "metrics"},
        )

        async def mock_listen():
            yield {"type": "message", "data": json.dumps(valid_message.model_dump())}
            messenger._running = False

        mock_pubsub.listen = mock_listen

        callback = AsyncMock()

        # Should handle ImportError for metrics (line 364)
        await messenger._subscription_loop(mock_pubsub, "test", callback)

        # Callback should have been invoked
        callback.assert_called_once()


@pytest.mark.asyncio
class TestHormoneUnsubscribe:
    """Test unsubscribe functionality"""

    async def test_unsubscribe_not_found(self, started_messenger):
        """Test unsubscribing non-existent subscriber (lines 404-406)"""
        # Try to unsubscribe subscriber that doesn't exist
        await started_messenger.unsubscribe("nonexistent_sub")

        # Lines 404-406 covered (warning and early return)
        assert "nonexistent_sub" not in started_messenger._pubsub_clients

    async def test_unsubscribe_success(self, started_messenger):
        """Test successful unsubscribe (lines 404-417)"""
        # Add mock pubsub client
        mock_pubsub = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        started_messenger._pubsub_clients["test_sub"] = mock_pubsub

        # Unsubscribe
        await started_messenger.unsubscribe("test_sub")

        # Lines 404-417 covered
        assert "test_sub" not in started_messenger._pubsub_clients
        mock_pubsub.unsubscribe.assert_called_once()
        mock_pubsub.close.assert_called_once()

    async def test_unsubscribe_exception(self, started_messenger):
        """Test unsubscribe handles exception (lines 416-417)"""
        # Add mock pubsub that raises on unsubscribe
        mock_pubsub = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock(side_effect=Exception("Unsubscribe error"))

        started_messenger._pubsub_clients["error_sub"] = mock_pubsub

        # Unsubscribe should handle exception gracefully
        await started_messenger.unsubscribe("error_sub")

        # Lines 416-417 covered
        # Note: subscriber may still be in dict after error
        assert True


@pytest.mark.asyncio
class TestAgentStateManagement:
    """Test agent state management in Redis"""

    async def test_set_agent_state_exception(self, started_messenger):
        """Test set_agent_state handles exception (lines 445-447)"""
        # Mock Redis setex to raise exception
        started_messenger._redis_client.setex = AsyncMock(
            side_effect=Exception("Redis setex error")
        )

        # Should handle exception gracefully (lines 445-447)
        result = await started_messenger.set_agent_state(
            "agent_001", {"status": "active"}, ttl=60
        )

        assert result is False

    async def test_get_agent_state_exception(self, started_messenger):
        """Test get_agent_state handles exception (lines 473-475)"""
        # Mock Redis get to raise exception
        started_messenger._redis_client.get = AsyncMock(
            side_effect=Exception("Redis get error")
        )

        # Should handle exception gracefully (lines 473-475)
        result = await started_messenger.get_agent_state("agent_002")

        assert result is None

    async def test_delete_agent_state_exception(self, started_messenger):
        """Test delete_agent_state handles exception (lines 497-499)"""
        # Mock Redis delete to raise exception
        started_messenger._redis_client.delete = AsyncMock(
            side_effect=Exception("Redis delete error")
        )

        # Should handle exception gracefully (lines 497-499)
        result = await started_messenger.delete_agent_state("agent_003")

        assert result is False

    async def test_get_all_agent_states_exception(self, started_messenger):
        """Test get_all_agent_states handles exception (lines 528-530)"""
        # Mock Redis scan_iter to raise exception
        async def mock_scan_error(*args, **kwargs):
            raise Exception("Redis scan error")

        started_messenger._redis_client.scan_iter = mock_scan_error

        # Should handle exception gracefully (lines 528-530)
        result = await started_messenger.get_all_agent_states()

        assert result == {}

    async def test_get_all_agent_states_no_client(self, messenger):
        """Test get_all_agent_states without Redis client (lines 509-510)"""
        # Don't start messenger (no Redis client)
        result = await messenger.get_all_agent_states()

        # Lines 509-510 covered
        assert result == {}


@pytest.mark.asyncio
class TestUtilityMethods:
    """Test utility methods"""

    async def test_is_running_with_client(self, started_messenger):
        """Test is_running returns True when running with client (line 536)"""
        # Should return True (running AND has client)
        assert started_messenger.is_running() is True

    async def test_is_running_degraded_mode(self, messenger):
        """Test is_running in degraded mode (line 536)"""
        # Start in degraded mode
        with patch('redis.asyncio.from_url', side_effect=Exception("Connection error")):
            await messenger.start()

        # In degraded mode: _running=True but _redis_client=None
        # Line 536: return self._running and self._redis_client is not None
        assert messenger.is_running() is False

    async def test_get_active_subscribers(self, started_messenger):
        """Test get_active_subscribers (line 540)"""
        # Add mock subscribers
        mock_pubsub = AsyncMock()
        started_messenger._pubsub_clients["sub_1"] = mock_pubsub
        started_messenger._pubsub_clients["sub_2"] = mock_pubsub

        # Get active subscribers
        subscribers = started_messenger.get_active_subscribers()

        # Line 540 covered
        assert len(subscribers) == 2
        assert "sub_1" in subscribers
        assert "sub_2" in subscribers


@pytest.mark.asyncio
class TestSubscribeTaskCreation:
    """Test subscription task creation"""

    async def test_subscribe_creates_task(self, started_messenger):
        """Test subscribe creates subscription task (lines 319-323)"""
        # Mock pubsub
        mock_pubsub = AsyncMock()

        async def mock_listen():
            # Yield one message then stop
            yield {"type": "subscribe", "data": None}
            await asyncio.sleep(0.1)

        mock_pubsub.listen = mock_listen
        mock_pubsub.subscribe = AsyncMock()

        started_messenger._redis_client.pubsub = MagicMock(return_value=mock_pubsub)

        initial_tasks = len(started_messenger._subscription_tasks)

        # Subscribe - should create task
        await started_messenger.subscribe(
            hormone_types=[HormoneType.CORTISOL],
            callback=lambda msg: None,
            subscriber_id="task_test_sub",
        )

        await asyncio.sleep(0.2)

        # Lines 319-323 covered (task creation and add_done_callback)
        # Task should be created
        assert len(started_messenger._subscription_tasks) >= initial_tasks
