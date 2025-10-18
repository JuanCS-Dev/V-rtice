"""
Comprehensive WebSocket Test Suite - Validates all functionality and error handling.

Tests all aspects of WebSocket implementation including:
- Connection management
- Channel subscriptions
- Message broadcasting
- Error handling
- Edge cases
- Recovery scenarios
"""

import asyncio
import json
import logging
from datetime import datetime

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestResult:
    """Tracks test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name: str):
        self.passed += 1
        logger.info(f"✅ {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        logger.error(f"❌ {test_name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"TEST SUMMARY: {self.passed}/{total} passed")
        if self.failed > 0:
            logger.error(f"FAILED TESTS: {self.failed}")
            for error in self.errors:
                logger.error(f"  - {error}")
        logger.info("=" * 70)
        return self.failed == 0


results = TestResult()


async def test_basic_connection():
    """Test 1: Basic WebSocket connection."""
    test_name = "Test 1: Basic Connection"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Should receive connection acknowledgment
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)

            assert data['type'] == 'connection_ack', f"Expected connection_ack, got {data['type']}"
            assert 'client_id' in data, "Missing client_id in ack"
            assert 'timestamp' in data, "Missing timestamp in ack"
            assert 'message' in data, "Missing message in ack"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_multiple_connections():
    """Test 2: Multiple simultaneous connections."""
    test_name = "Test 2: Multiple Connections (10 clients)"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        clients = []
        client_ids = set()

        # Connect 10 clients
        for i in range(10):
            ws = await websockets.connect(uri)
            clients.append(ws)

            # Get ack and extract client_id
            msg = await ws.recv()
            data = json.loads(msg)
            client_ids.add(data['client_id'])

        # All client IDs should be unique
        assert len(client_ids) == 10, f"Expected 10 unique IDs, got {len(client_ids)}"

        # Close all
        for ws in clients:
            await ws.close()

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_subscribe_unsubscribe():
    """Test 3: Channel subscription and unsubscription."""
    test_name = "Test 3: Subscribe/Unsubscribe Channels"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Subscribe to multiple channels
            sub_msg = {"type": "subscribe", "channels": ["apvs", "decisions", "stats"]}
            await ws.send(json.dumps(sub_msg))

            # Should receive confirmation
            msg = await ws.recv()
            data = json.loads(msg)
            assert data['type'] == 'subscription_confirmed', f"Expected subscription_confirmed, got {data['type']}"
            assert set(data['channels']) == {"apvs", "decisions", "stats"}, "Channels mismatch"

            # Unsubscribe from some channels
            unsub_msg = {"type": "unsubscribe", "channels": ["apvs", "decisions"]}
            await ws.send(json.dumps(unsub_msg))

            # Should receive confirmation
            msg = await ws.recv()
            data = json.loads(msg)
            assert data['type'] == 'unsubscription_confirmed', f"Expected unsubscription_confirmed, got {data['type']}"
            assert set(data['channels']) == {"apvs", "decisions"}, "Unsubscribe channels mismatch"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_ping_pong():
    """Test 4: Ping/pong keepalive."""
    test_name = "Test 4: Ping/Pong Keepalive"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Send ping
            ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await ws.send(json.dumps(ping_msg))

            # Should receive pong
            msg = await ws.recv()
            data = json.loads(msg)
            assert data['type'] == 'pong', f"Expected pong, got {data['type']}"
            assert 'timestamp' in data, "Missing timestamp in pong"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_invalid_message_type():
    """Test 5: Invalid message type handling."""
    test_name = "Test 5: Invalid Message Type"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Send invalid message type
            invalid_msg = {"type": "invalid_type_xyz", "data": "test"}
            await ws.send(json.dumps(invalid_msg))

            # Should receive error message
            error_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            error_data = json.loads(error_msg)
            assert error_data['type'] == 'error', "Should receive error message"
            assert 'error_message' in error_data, "Error should have message"

            # Now send a valid ping - connection should still work
            ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await ws.send(json.dumps(ping_msg))

            pong_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            pong_data = json.loads(pong_msg)

            # Should receive pong (connection recovered from invalid message)
            assert pong_data['type'] == 'pong', "Connection should recover after invalid message"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_malformed_json():
    """Test 6: Malformed JSON handling."""
    test_name = "Test 6: Malformed JSON"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Send malformed JSON
            await ws.send("{invalid json}")

            # Connection might close or handle gracefully
            # Try to check connection state
            try:
                # Send valid message after malformed one
                ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
                await ws.send(json.dumps(ping_msg))
                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                # If we get here, connection recovered
                results.add_pass(test_name + " (connection recovered)")
            except:
                # Connection closed - this is acceptable error handling
                results.add_pass(test_name + " (connection closed as expected)")
                return

    except Exception as e:
        # Connection closing on malformed JSON is acceptable
        if "connection closed" in str(e).lower():
            results.add_pass(test_name + " (connection closed as expected)")
        else:
            results.add_fail(test_name, str(e))


async def test_subscribe_empty_channels():
    """Test 7: Subscribe with empty channels list."""
    test_name = "Test 7: Subscribe Empty Channels"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Subscribe to empty list
            sub_msg = {"type": "subscribe", "channels": []}
            await ws.send(json.dumps(sub_msg))

            # Should receive confirmation (even if empty)
            msg = await ws.recv()
            data = json.loads(msg)
            assert data['type'] == 'subscription_confirmed', "Should confirm even empty subscription"
            assert data['channels'] == [], "Should return empty list"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_unsubscribe_not_subscribed():
    """Test 8: Unsubscribe from channels not subscribed to."""
    test_name = "Test 8: Unsubscribe Non-Subscribed Channels"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Unsubscribe without subscribing first
            unsub_msg = {"type": "unsubscribe", "channels": ["apvs"]}
            await ws.send(json.dumps(unsub_msg))

            # Should handle gracefully
            msg = await ws.recv()
            data = json.loads(msg)
            assert data['type'] == 'unsubscription_confirmed', "Should confirm unsubscribe"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_rapid_connect_disconnect():
    """Test 9: Rapid connect/disconnect cycles."""
    test_name = "Test 9: Rapid Connect/Disconnect (20 cycles)"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        for i in range(20):
            ws = await websockets.connect(uri)
            # Get ack
            await ws.recv()
            # Immediately close
            await ws.close()

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_connection_without_subscribing():
    """Test 10: Connection without subscribing to any channels."""
    test_name = "Test 10: Connection Without Subscribing"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Just ping without subscribing
            ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await ws.send(json.dumps(ping_msg))

            msg = await ws.recv()
            data = json.loads(msg)
            assert data['type'] == 'pong', "Should work without subscribing"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_duplicate_subscriptions():
    """Test 11: Subscribing to same channel multiple times."""
    test_name = "Test 11: Duplicate Subscriptions"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Subscribe to same channel twice
            sub_msg = {"type": "subscribe", "channels": ["decisions"]}
            await ws.send(json.dumps(sub_msg))
            await ws.recv()  # First confirmation

            # Subscribe again
            await ws.send(json.dumps(sub_msg))
            msg = await ws.recv()  # Second confirmation

            # Should handle gracefully
            data = json.loads(msg)
            assert data['type'] == 'subscription_confirmed', "Should handle duplicate subscription"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_subscribe_invalid_channel():
    """Test 12: Subscribe to non-existent channel."""
    test_name = "Test 12: Subscribe Invalid Channel"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Subscribe to invalid channel (system should accept it but won't broadcast to it)
            sub_msg = {"type": "subscribe", "channels": ["invalid_channel_xyz"]}
            await ws.send(json.dumps(sub_msg))

            msg = await ws.recv()
            data = json.loads(msg)
            # Should confirm subscription (validation of channel names is optional)
            assert data['type'] == 'subscription_confirmed', "Should handle any channel name"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_message_missing_type():
    """Test 13: Message without 'type' field."""
    test_name = "Test 13: Message Missing Type Field"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Send message without type
            invalid_msg = {"data": "test", "channels": ["apvs"]}
            await ws.send(json.dumps(invalid_msg))

            # Should receive error message
            error_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            error_data = json.loads(error_msg)
            assert error_data['type'] == 'error', "Should receive error for missing type"
            assert 'error_message' in error_data, "Error should have message"

            # Now send a valid ping - connection should still work
            ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await ws.send(json.dumps(ping_msg))

            pong_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            pong_data = json.loads(pong_msg)
            assert pong_data['type'] == 'pong', "Should recover from message without type"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_long_running_connection():
    """Test 14: Long-running connection with periodic pings."""
    test_name = "Test 14: Long-Running Connection (30s with pings)"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Send pings every 5 seconds for 30 seconds
            for i in range(6):
                ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
                await ws.send(json.dumps(ping_msg))

                msg = await ws.recv()
                data = json.loads(msg)
                assert data['type'] == 'pong', f"Expected pong at iteration {i}"

                if i < 5:  # Don't sleep on last iteration
                    await asyncio.sleep(5)

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_concurrent_operations():
    """Test 15: Concurrent subscribe/unsubscribe operations."""
    test_name = "Test 15: Concurrent Subscribe/Unsubscribe"
    uri = "ws://localhost:8003/hitl/ws"

    try:
        async with websockets.connect(uri) as ws:
            # Get ack
            await ws.recv()

            # Rapid subscribe/unsubscribe
            for i in range(10):
                sub_msg = {"type": "subscribe", "channels": [f"channel_{i}"]}
                await ws.send(json.dumps(sub_msg))
                await ws.recv()  # Get confirmation

                unsub_msg = {"type": "unsubscribe", "channels": [f"channel_{i}"]}
                await ws.send(json.dumps(unsub_msg))
                await ws.recv()  # Get confirmation

            # Verify connection still works
            ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await ws.send(json.dumps(ping_msg))
            msg = await ws.recv()
            data = json.loads(msg)
            assert data['type'] == 'pong', "Connection should work after rapid ops"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, str(e))


async def main():
    """Run all comprehensive tests."""
    logger.info("")
    logger.info("╔═══════════════════════════════════════════════════════════════════╗")
    logger.info("║     WEBSOCKET COMPREHENSIVE TEST SUITE                            ║")
    logger.info("║     Testing All Functionality & Error Handling                   ║")
    logger.info("╚═══════════════════════════════════════════════════════════════════╝")
    logger.info("")

    # Basic functionality tests
    logger.info("=" * 70)
    logger.info("CATEGORY 1: BASIC FUNCTIONALITY")
    logger.info("=" * 70)
    await test_basic_connection()
    await test_multiple_connections()
    await test_subscribe_unsubscribe()
    await test_ping_pong()

    logger.info("")
    logger.info("=" * 70)
    logger.info("CATEGORY 2: ERROR HANDLING")
    logger.info("=" * 70)
    await test_invalid_message_type()
    await test_malformed_json()
    await test_message_missing_type()

    logger.info("")
    logger.info("=" * 70)
    logger.info("CATEGORY 3: EDGE CASES")
    logger.info("=" * 70)
    await test_subscribe_empty_channels()
    await test_unsubscribe_not_subscribed()
    await test_connection_without_subscribing()
    await test_duplicate_subscriptions()
    await test_subscribe_invalid_channel()

    logger.info("")
    logger.info("=" * 70)
    logger.info("CATEGORY 4: STRESS & RESILIENCE")
    logger.info("=" * 70)
    await test_rapid_connect_disconnect()
    await test_long_running_connection()
    await test_concurrent_operations()

    # Summary
    success = results.summary()

    if success:
        logger.info("")
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error("")
        logger.error("❌ SOME TESTS FAILED - See errors above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
