"""
WebSocket Test Script - Tests WebSocket functionality.

Tests connection, subscription, and message broadcasting.
"""

import asyncio
import json
import logging
from datetime import datetime

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket_connection():
    """Test WebSocket connection and basic functionality."""
    uri = "ws://localhost:8003/hitl/ws"

    logger.info("=" * 70)
    logger.info("WEBSOCKET TEST - Starting")
    logger.info("=" * 70)
    logger.info("")

    try:
        # Connect to WebSocket
        logger.info(f"1. Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected successfully")

            # Receive connection acknowledgment
            logger.info("")
            logger.info("2. Waiting for connection acknowledgment...")
            ack_message = await websocket.recv()
            ack_data = json.loads(ack_message)
            logger.info(f"✅ Received: {ack_data['type']}")
            logger.info(f"   Client ID: {ack_data.get('client_id', 'N/A')}")
            logger.info(f"   Message: {ack_data.get('message', 'N/A')}")

            # Subscribe to channels
            logger.info("")
            logger.info("3. Subscribing to channels: apvs, decisions, stats")
            subscribe_msg = {
                "type": "subscribe",
                "channels": ["apvs", "decisions", "stats"],
            }
            await websocket.send(json.dumps(subscribe_msg))

            # Wait for subscription confirmation
            sub_response = await websocket.recv()
            sub_data = json.loads(sub_response)
            logger.info(f"✅ Received: {sub_data['type']}")
            logger.info(f"   Channels: {sub_data.get('channels', [])}")

            # Send ping
            logger.info("")
            logger.info("4. Sending ping...")
            ping_msg = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await websocket.send(json.dumps(ping_msg))

            # Wait for pong
            pong_response = await websocket.recv()
            pong_data = json.loads(pong_response)
            logger.info(f"✅ Received: {pong_data['type']}")

            # Listen for broadcast messages (wait up to 5 seconds)
            logger.info("")
            logger.info("5. Listening for broadcast messages (5 seconds)...")
            logger.info("   (Make a decision in the UI to trigger a broadcast)")

            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)

                    if data['type'] in ['new_apv', 'decision_made', 'stats_update']:
                        logger.info(f"✅ Received broadcast: {data['type']}")
                        logger.info(f"   Data: {json.dumps(data, indent=2)}")
                    else:
                        logger.info(f"📨 Received: {data['type']}")
            except asyncio.TimeoutError:
                logger.info("⏱️ Timeout - no broadcasts received in 5 seconds")
                logger.info("   This is normal if no decisions were made")

            # Unsubscribe
            logger.info("")
            logger.info("6. Unsubscribing from channels...")
            unsubscribe_msg = {
                "type": "unsubscribe",
                "channels": ["apvs", "decisions"],
            }
            await websocket.send(json.dumps(unsubscribe_msg))

            # Wait for unsubscription confirmation
            unsub_response = await websocket.recv()
            unsub_data = json.loads(unsub_response)
            logger.info(f"✅ Received: {unsub_data['type']}")
            logger.info(f"   Channels: {unsub_data.get('channels', [])}")

            logger.info("")
            logger.info("7. Closing connection...")
            await websocket.close()
            logger.info("✅ Connection closed")

    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"❌ Connection closed unexpectedly: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

    logger.info("")
    logger.info("=" * 70)
    logger.info("WEBSOCKET TEST - COMPLETE ✅")
    logger.info("=" * 70)

    return True


async def test_multiple_clients():
    """Test multiple WebSocket clients simultaneously."""
    uri = "ws://localhost:8003/hitl/ws"

    logger.info("")
    logger.info("=" * 70)
    logger.info("MULTIPLE CLIENTS TEST - Starting")
    logger.info("=" * 70)
    logger.info("")

    clients = []

    try:
        # Connect 3 clients
        logger.info("1. Connecting 3 clients...")
        for i in range(3):
            ws = await websockets.connect(uri)
            clients.append(ws)

            # Receive ack
            ack = await ws.recv()
            ack_data = json.loads(ack)
            logger.info(f"✅ Client {i+1} connected: {ack_data.get('client_id', 'N/A')[:8]}...")

        # Subscribe all clients
        logger.info("")
        logger.info("2. Subscribing all clients to 'decisions' channel...")
        for i, ws in enumerate(clients):
            subscribe_msg = {
                "type": "subscribe",
                "channels": ["decisions"],
            }
            await ws.send(json.dumps(subscribe_msg))

            # Wait for confirmation
            sub_response = await ws.recv()
            logger.info(f"✅ Client {i+1} subscribed")

        logger.info("")
        logger.info("3. All clients listening for broadcasts...")
        logger.info("   (Make a decision in the UI to test broadcast)")

        # Wait for broadcast (5 seconds)
        try:
            tasks = [asyncio.wait_for(ws.recv(), timeout=5.0) for ws in clients]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            received_count = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"✅ {received_count}/{len(clients)} clients received broadcast")
        except:
            logger.info("⏱️ Timeout - no broadcasts received")

        # Close all connections
        logger.info("")
        logger.info("4. Closing all connections...")
        for i, ws in enumerate(clients):
            await ws.close()
            logger.info(f"✅ Client {i+1} disconnected")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

    logger.info("")
    logger.info("=" * 70)
    logger.info("MULTIPLE CLIENTS TEST - COMPLETE ✅")
    logger.info("=" * 70)

    return True


async def main():
    """Run all WebSocket tests."""
    logger.info("")
    logger.info("╔═══════════════════════════════════════════════════════════════════╗")
    logger.info("║          HITL WEBSOCKET - TEST SUITE                              ║")
    logger.info("╚═══════════════════════════════════════════════════════════════════╝")
    logger.info("")

    # Test 1: Basic connection
    test1_result = await test_websocket_connection()

    await asyncio.sleep(1)

    # Test 2: Multiple clients
    test2_result = await test_multiple_clients()

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Test 1 (Basic Connection):  {'✅ PASSED' if test1_result else '❌ FAILED'}")
    logger.info(f"Test 2 (Multiple Clients):  {'✅ PASSED' if test2_result else '❌ FAILED'}")
    logger.info("=" * 70)

    if test1_result and test2_result:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
