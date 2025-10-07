#!/usr/bin/env python
"""
SSE Streaming Validation

Automated validation of Server-Sent Events (SSE) streaming for Governance Workspace.
Tests real SSE connections, heartbeats, latency, and multi-client scenarios.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO compliant - NO MOCK, NO PLACEHOLDER, NO TODO
"""

import asyncio
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import httpx


@dataclass
class SSEEvent:
    """Parsed SSE event."""
    event_type: str
    event_id: str
    data: Dict
    timestamp: float = field(default_factory=time.time)


@dataclass
class SSETestMetrics:
    """Metrics collected during SSE testing."""
    events_received: int = 0
    heartbeats_received: int = 0
    decisions_received: int = 0
    connection_time: float = 0.0
    first_event_latency: float = 0.0
    avg_latency: float = 0.0
    latencies: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class SSEStreamingValidator:
    """
    Validates SSE streaming functionality with real server.

    Tests:
    - Connection establishment
    - Heartbeat delivery
    - Decision streaming
    - Multi-client support
    - Latency measurement
    - Reconnection handling
    """

    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        Initialize SSE validator.

        Args:
            base_url: Base URL of governance server
        """
        self.base_url = base_url
        self.metrics = SSETestMetrics()
        self.events: List[SSEEvent] = []

    async def parse_sse_stream(
        self,
        response: httpx.Response,
        duration: float = 10.0
    ) -> List[SSEEvent]:
        """
        Parse SSE stream from response.

        Args:
            response: HTTP response with SSE content
            duration: How long to listen (seconds)

        Returns:
            List of parsed SSE events
        """
        events: List[SSEEvent] = []
        start_time = time.time()

        event_type = ""
        event_id = ""
        data_lines: List[str] = []

        async for line in response.aiter_lines():
            # Check duration timeout
            if time.time() - start_time > duration:
                break

            line = line.strip()

            if not line:
                # Empty line = end of event
                if event_type and data_lines:
                    try:
                        # Join data lines and parse JSON
                        data_str = "\n".join(data_lines)
                        data = json.loads(data_str)

                        event = SSEEvent(
                            event_type=event_type,
                            event_id=event_id,
                            data=data,
                            timestamp=time.time()
                        )
                        events.append(event)

                        # Update metrics
                        self.metrics.events_received += 1
                        if event_type == "heartbeat":
                            self.metrics.heartbeats_received += 1
                        elif event_type == "decision_pending":
                            self.metrics.decisions_received += 1

                    except json.JSONDecodeError as e:
                        self.metrics.errors.append(f"JSON parse error: {e}")

                # Reset for next event
                event_type = ""
                event_id = ""
                data_lines = []
                continue

            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("id:"):
                event_id = line[3:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

        return events

    async def test_connection_establishment(self) -> bool:
        """
        Test that SSE connection can be established.

        Returns:
            True if connection successful
        """
        print("\n" + "="*80)
        print("🧪 Test: SSE Connection Establishment")
        print("="*80)

        try:
            # Create session and connect
            session_response = await self._create_session("sse_test_conn@test")
            session_id = session_response["session_id"]
            operator_id = session_response["operator_id"]

            start_time = time.time()

            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "GET",
                    f"{self.base_url}/api/v1/governance/stream/{operator_id}",
                    params={"session_id": session_id}
                ) as response:
                    self.metrics.connection_time = time.time() - start_time

                    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

                    content_type = response.headers.get("content-type", "")
                    assert "text/event-stream" in content_type, \
                        f"Wrong content-type: {content_type}"

                    # Read first event (connection confirmation)
                    events = await self.parse_sse_stream(response, duration=2.0)

                    assert len(events) > 0, "No events received"
                    assert events[0].event_type == "connected", "First event should be 'connected'"

            print(f"✅ Connection established in {self.metrics.connection_time:.3f}s")
            print(f"   Events received: {len(events)}")
            print(f"   First event: {events[0].event_type}")

            return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.metrics.errors.append(str(e))
            return False

    async def test_heartbeat_delivery(self) -> bool:
        """
        Test that heartbeats are delivered at correct intervals.

        Returns:
            True if heartbeats delivered correctly
        """
        print("\n" + "="*80)
        print("🧪 Test: Heartbeat Delivery")
        print("="*80)

        try:
            session_response = await self._create_session("sse_test_hb@test")
            session_id = session_response["session_id"]
            operator_id = session_response["operator_id"]

            heartbeat_times: List[float] = []

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "GET",
                    f"{self.base_url}/api/v1/governance/stream/{operator_id}",
                    params={"session_id": session_id}
                ) as response:
                    # Listen for 35 seconds to catch at least 1 heartbeat (30s interval + buffer)
                    events = await self.parse_sse_stream(response, duration=35.0)

            # Find heartbeat events
            for event in events:
                if event.event_type == "heartbeat":
                    heartbeat_times.append(event.timestamp)

            assert len(heartbeat_times) >= 1, f"Expected ≥1 heartbeat, got {len(heartbeat_times)}"

            # Validate heartbeat received
            print(f"✅ Heartbeats received: {len(heartbeat_times)}")
            print(f"   Expected: ≥1 heartbeat within 35s")
            print(f"   Heartbeat interval: 30s")

            # If we got multiple heartbeats, validate interval
            if len(heartbeat_times) >= 2:
                interval = heartbeat_times[1] - heartbeat_times[0]
                print(f"   Measured interval: {interval:.1f}s")
                # Allow 25-35s interval (30s ±5s tolerance)
                assert 25.0 <= interval <= 35.0, f"Interval {interval:.1f}s outside 25-35s range"

            return True

        except Exception as e:
            print(f"❌ Heartbeat test failed: {e}")
            self.metrics.errors.append(str(e))
            return False

    async def test_decision_streaming_latency(self) -> bool:
        """
        Test decision streaming and measure latency.

        Returns:
            True if latency acceptable
        """
        print("\n" + "="*80)
        print("🧪 Test: Decision Streaming Latency")
        print("="*80)

        try:
            session_response = await self._create_session("sse_test_lat@test")
            session_id = session_response["session_id"]
            operator_id = session_response["operator_id"]

            latencies: List[float] = []
            num_tests = 5
            enqueue_times = {}
            decisions_received = 0
            enqueue_done = False

            async def enqueue_decisions():
                """Enqueue decisions after a small delay."""
                nonlocal enqueue_done
                await asyncio.sleep(1)  # Wait for SSE to connect
                async with httpx.AsyncClient(timeout=10.0) as enqueue_client:
                    for i in range(num_tests):
                        enqueue_time = time.time()
                        decision_id = f"latency_test_{i}_{enqueue_time}"
                        await self._enqueue_decision(decision_id, enqueue_client)
                        enqueue_times[decision_id] = enqueue_time
                        await asyncio.sleep(0.1)  # Small stagger
                enqueue_done = True

            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "GET",
                    f"{self.base_url}/api/v1/governance/stream/{operator_id}",
                    params={"session_id": session_id}
                ) as sse_response:
                    # Start enqueuing decisions in background
                    enqueue_task = asyncio.create_task(enqueue_decisions())

                    try:
                        max_wait = 20.0  # Max 20s to receive all decisions
                        start_time = time.time()

                        async for line in sse_response.aiter_lines():
                            # Look for decision IDs in the stream
                            for decision_id in list(enqueue_times.keys()):
                                if decision_id in line:
                                    if decision_id not in [d[0] for d in [(k, v) for k, v in zip(enqueue_times.keys(), latencies)]]:
                                        receive_time = time.time()
                                        latency = (receive_time - enqueue_times[decision_id]) * 1000
                                        latencies.append(latency)
                                        decisions_received += 1
                                        break

                            # Stop if all received or timeout
                            if decisions_received >= num_tests:
                                break
                            if time.time() - start_time > max_wait:
                                break

                    finally:
                        # Clean up background task
                        if not enqueue_task.done():
                            enqueue_task.cancel()
                            try:
                                await enqueue_task
                            except asyncio.CancelledError:
                                pass

            # Calculate statistics
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

            self.metrics.latencies = latencies
            self.metrics.avg_latency = avg_latency

            print(f"✅ Latency measured across {len(latencies)} decisions:")
            print(f"   Min: {min_latency:.1f}ms")
            print(f"   Avg: {avg_latency:.1f}ms")
            print(f"   Max: {max_latency:.1f}ms")
            print(f"   P95: {p95_latency:.1f}ms")
            print(f"   Target: <550ms")

            assert p95_latency < 550.0, f"P95 latency {p95_latency:.1f}ms exceeds 550ms target"

            return True

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else f"{type(e).__name__} (no message)"
            print(f"❌ Latency test failed: {error_msg}")
            self.metrics.errors.append(error_msg)
            import traceback
            traceback.print_exc()
            return False

    async def test_multiple_clients(self) -> bool:
        """
        Test multiple clients receiving events simultaneously.

        Returns:
            True if all clients receive events
        """
        print("\n" + "="*80)
        print("🧪 Test: Multiple Concurrent Clients")
        print("="*80)

        try:
            num_clients = 5

            # Create sessions for all clients
            sessions = []
            for i in range(num_clients):
                session = await self._create_session(f"multi_client_{i}@test")
                sessions.append(session)

            # Connect all clients and enqueue one decision
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Enqueue single decision
                decision_id = f"multi_test_{time.time()}"
                await self._enqueue_decision(decision_id, client)

                # Each client should receive the decision
                received_count = 0

                async def check_client_receives(session):
                    """Check if client receives decision event."""
                    async with httpx.AsyncClient(timeout=10.0) as c:
                        async with c.stream(
                            "GET",
                            f"{self.base_url}/api/v1/governance/stream/{session['operator_id']}",
                            params={"session_id": session["session_id"]}
                        ) as response:
                            # Listen for decision event
                            async for line in response.aiter_lines():
                                if decision_id in line:
                                    return True
                                # Timeout after 5s
                                if time.time() - start_time > 5.0:
                                    return False
                    return False

                start_time = time.time()

                # Check all clients concurrently
                results = await asyncio.gather(*[
                    check_client_receives(session) for session in sessions
                ])

                received_count = sum(results)

            print(f"✅ Clients tested: {num_clients}")
            print(f"   Events received: {received_count}/{num_clients}")
            print(f"   Delivery rate: {(received_count/num_clients)*100:.1f}%")

            assert received_count == num_clients, \
                f"Not all clients received event ({received_count}/{num_clients})"

            return True

        except Exception as e:
            print(f"❌ Multi-client test failed: {e}")
            self.metrics.errors.append(str(e))
            return False

    async def _create_session(self, operator_id: str) -> Dict:
        """
        Create operator session.

        Args:
            operator_id: Operator identifier

        Returns:
            Session data
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/session/create",
                json={
                    "operator_id": operator_id,
                    "operator_name": "SSE Test Operator",
                    "role": "soc_operator"
                }
            )
            return response.json()

    async def _enqueue_decision(self, decision_id: str, client: httpx.AsyncClient) -> Dict:
        """
        Enqueue test decision.

        Args:
            decision_id: Decision identifier
            client: HTTP client to use

        Returns:
            Enqueue response
        """
        response = await client.post(
            f"{self.base_url}/api/v1/governance/test/enqueue",
            json={
                "decision_id": decision_id,
                "risk_level": "high",
                "action_type": "block_ip",
                "target": "192.168.1.1",
                "confidence": 0.95,
                "ai_reasoning": "SSE streaming test",
                "threat_score": 9.0,
                "threat_type": "test",
                "metadata": {}
            }
        )
        return response.json()

    async def run_all_tests(self) -> bool:
        """
        Run all SSE validation tests.

        Returns:
            True if all tests pass
        """
        print("\n" + "="*80)
        print("🧪 SSE Streaming Validation Suite")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print()

        results = []

        # Run tests sequentially
        results.append(("Connection Establishment", await self.test_connection_establishment()))
        results.append(("Heartbeat Delivery", await self.test_heartbeat_delivery()))
        results.append(("Decision Streaming Latency", await self.test_decision_streaming_latency()))
        results.append(("Multiple Concurrent Clients", await self.test_multiple_clients()))

        # Print summary
        print("\n" + "="*80)
        print("📊 SSE Validation Summary")
        print("="*80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        if self.metrics.latencies:
            print(f"\nPerformance:")
            print(f"  Avg Latency: {self.metrics.avg_latency:.1f}ms")
            print(f"  Connection Time: {self.metrics.connection_time:.3f}s")

        if self.metrics.errors:
            print(f"\n⚠️  Errors encountered:")
            for error in self.metrics.errors[:5]:  # Show first 5
                print(f"   - {error}")

        print("\n" + "="*80)

        if passed == total:
            print("✅ ALL SSE TESTS PASSED - Streaming is production-ready!")
        else:
            print(f"❌ {total - passed} test(s) failed - Review errors above")

        print("="*80)
        print()

        return passed == total


async def main():
    """Main entry point."""
    validator = SSEStreamingValidator()
    success = await validator.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
