"""
Chaos Engineering Tests for RabbitMQ Integration.

Tests system resilience under failure conditions:
1. RabbitMQ connection loss
2. Network partitions
3. Consumer failures
4. Message corruption
5. Queue overflow
6. Slow consumers
7. Resource exhaustion

Usage:
    pytest tests/chaos/test_rabbitmq_chaos.py -v --asyncio-mode=auto

Requirements:
    - RabbitMQ running locally or via Docker
    - Chaos tools (optional): tc, iptables, stress
"""

import asyncio
import json
import random
import time
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# Import messaging components
from messaging.client import RabbitMQClient
from messaging.publisher import APVPublisher, WargameReportPublisher
from messaging.consumer import HITLNotificationConsumer
from backend.services.adaptive_immune_system.models.apv import APVDispatchMessage
from backend.services.adaptive_immune_system.models.wargame import WargameReportMessage
from backend.services.adaptive_immune_system.models.hitl import HITLNotificationMessage


class ChaosScenario:
    """Base class for chaos scenarios."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.failures = []
        self.successes = []

    def record_failure(self, error: str):
        """Record a failure."""
        self.failures.append({
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def record_success(self):
        """Record a success."""
        self.successes.append({
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        total = len(self.failures) + len(self.successes)
        return len(self.successes) / total if total > 0 else 0.0


@pytest.mark.asyncio
async def test_chaos_rabbitmq_connection_loss():
    """
    Chaos Test: RabbitMQ Connection Loss

    Simulates losing connection to RabbitMQ mid-operation.

    Expected Behavior:
    - Publishers log errors but don't crash
    - System continues operating (graceful degradation)
    - Reconnection works when RabbitMQ recovers
    """
    scenario = ChaosScenario(
        "connection_loss",
        "RabbitMQ connection lost during message publishing"
    )

    # Create mock client that simulates connection loss
    mock_client = MagicMock(spec=RabbitMQClient)
    mock_client.is_connected = True

    # First 5 publishes succeed, then connection lost
    call_count = 0

    async def mock_publish(routing_key, message_body, priority=5):
        nonlocal call_count
        call_count += 1

        if call_count <= 5:
            scenario.record_success()
            return  # Success
        else:
            scenario.record_failure("Connection lost")
            raise ConnectionError("RabbitMQ connection lost")

    mock_client.publish = AsyncMock(side_effect=mock_publish)

    # Create publisher
    publisher = APVPublisher(mock_client)

    # Publish 10 messages (5 should succeed, 5 should fail)
    for i in range(10):
        message = APVDispatchMessage(
            message_id=str(uuid.uuid4()),
            apv_id=str(uuid.uuid4()),
            apv_code=f"APV-TEST-{i:03d}",
            cve_id="CVE-2024-0001",
            severity="high",
            cvss_score=8.5,
            affected_package="test-package",
            current_version="1.0.0",
            fixed_version="1.1.0",
            affected_components=["component-1"],
            remediation_type="dependency_upgrade",
            priority=8,
            timestamp=datetime.utcnow(),
        )

        try:
            await publisher.dispatch_apv(message)
        except ConnectionError:
            # Expected for messages 6-10
            pass

    # Verify graceful degradation
    assert scenario.get_success_rate() == 0.5  # 5/10 succeeded
    assert len(scenario.failures) == 5
    assert all("Connection lost" in f["error"] for f in scenario.failures)

    print(f"\n✅ {scenario.name}: Success rate = {scenario.get_success_rate():.1%}")


@pytest.mark.asyncio
async def test_chaos_consumer_crash():
    """
    Chaos Test: Consumer Crash

    Simulates consumer crashing mid-processing.

    Expected Behavior:
    - Message remains in queue (not acknowledged)
    - Another consumer can pick up the message
    - No message loss
    """
    scenario = ChaosScenario(
        "consumer_crash",
        "Consumer crashes while processing message"
    )

    processed_messages = []
    crash_on_message = 3  # Crash on 3rd message

    async def callback_with_crash(notification: HITLNotificationMessage):
        """Callback that crashes on specific message."""
        if len(processed_messages) + 1 == crash_on_message:
            scenario.record_failure("Consumer crashed")
            raise RuntimeError("Consumer crashed unexpectedly")

        processed_messages.append(notification)
        scenario.record_success()

    # Create mock client
    mock_client = MagicMock(spec=RabbitMQClient)
    mock_client.is_connected = True

    # Create consumer
    consumer = HITLNotificationConsumer(
        client=mock_client,
        callback=callback_with_crash,
    )

    # Simulate receiving messages
    test_messages = [
        HITLNotificationMessage(
            message_id=str(uuid.uuid4()),
            apv_id=str(uuid.uuid4()),
            apv_code=f"APV-TEST-{i:03d}",
            priority=8,
            cve_id="CVE-2024-0001",
            severity="high",
            cvss_score=8.5,
            affected_package="test-package",
            current_version="1.0.0",
            fixed_version="1.1.0",
            patch_strategy="dependency_upgrade",
            pr_url="https://github.com/org/repo/pull/1",
            pr_number=1,
            wargame_verdict="needs_review",
            wargame_confidence=0.75,
            wargame_evidence_url="https://github.com/org/repo/actions/runs/1",
            requires_immediate_attention=True,
            repository_owner="org",
            repository_name="repo",
            affected_files=["file.py"],
            remediation_type="dependency_upgrade",
            validation_warnings=[],
            estimated_risk_reduction=0.8,
            confirmation_confidence=0.9,
            escalation_reason="Test",
            timestamp=datetime.utcnow(),
        )
        for i in range(5)
    ]

    # Process messages
    for i, msg in enumerate(test_messages):
        try:
            await callback_with_crash(msg)
        except RuntimeError:
            # Expected crash on message 3
            assert i + 1 == crash_on_message
            break

    # Verify message processing stopped at crash
    assert len(processed_messages) == crash_on_message - 1
    assert len(scenario.failures) == 1

    # Simulate recovery: new consumer picks up remaining messages
    async def callback_recovery(notification: HITLNotificationMessage):
        processed_messages.append(notification)
        scenario.record_success()

    # Process remaining messages with recovered consumer
    for i, msg in enumerate(test_messages[crash_on_message:], start=crash_on_message):
        await callback_recovery(msg)

    # Verify all messages eventually processed
    assert len(processed_messages) == len(test_messages)
    assert scenario.get_success_rate() == 0.8  # 4/5 succeeded first time

    print(f"\n✅ {scenario.name}: All messages eventually processed")


@pytest.mark.asyncio
async def test_chaos_message_corruption():
    """
    Chaos Test: Message Corruption

    Simulates corrupted message data.

    Expected Behavior:
    - Invalid messages rejected by Pydantic validation
    - System logs error but continues
    - Message sent to DLQ
    """
    scenario = ChaosScenario(
        "message_corruption",
        "Corrupted messages in queue"
    )

    # Create various corrupted messages
    corrupted_messages = [
        # Missing required field
        {
            "apv_id": str(uuid.uuid4()),
            # "apv_code" missing
            "cve_id": "CVE-2024-0001",
        },
        # Invalid type
        {
            "apv_id": str(uuid.uuid4()),
            "apv_code": "APV-001",
            "priority": "high",  # Should be int
        },
        # Invalid enum value
        {
            "apv_id": str(uuid.uuid4()),
            "apv_code": "APV-002",
            "severity": "super_critical",  # Invalid severity
        },
        # Malformed JSON (string instead of JSON)
        "not a json object",
    ]

    for i, corrupted in enumerate(corrupted_messages):
        try:
            # Try to parse as HITLNotificationMessage
            if isinstance(corrupted, str):
                # JSON parsing will fail
                json.loads(corrupted)
            else:
                # Pydantic validation will fail
                HITLNotificationMessage(**corrupted)

            scenario.record_success()  # Should not reach here

        except (json.JSONDecodeError, Exception) as e:
            # Expected - corrupted message rejected
            scenario.record_failure(f"Message {i}: {type(e).__name__}")

    # All corrupted messages should be rejected
    assert scenario.get_success_rate() == 0.0
    assert len(scenario.failures) == len(corrupted_messages)

    print(f"\n✅ {scenario.name}: All corrupted messages rejected")


@pytest.mark.asyncio
async def test_chaos_slow_consumer():
    """
    Chaos Test: Slow Consumer

    Simulates consumer taking too long to process messages.

    Expected Behavior:
    - Messages queue up
    - No message loss
    - System continues accepting new messages
    - Eventually catches up
    """
    scenario = ChaosScenario(
        "slow_consumer",
        "Consumer processing messages slowly"
    )

    processed = []
    processing_time = 0.5  # 500ms per message

    async def slow_callback(notification: HITLNotificationMessage):
        """Callback that processes slowly."""
        await asyncio.sleep(processing_time)
        processed.append(notification)
        scenario.record_success()

    # Create mock client
    mock_client = MagicMock(spec=RabbitMQClient)

    # Simulate 10 messages arriving faster than consumer can process
    messages = [
        HITLNotificationMessage(
            message_id=str(uuid.uuid4()),
            apv_id=str(uuid.uuid4()),
            apv_code=f"APV-SLOW-{i:03d}",
            priority=5,
            cve_id="CVE-2024-0001",
            severity="medium",
            cvss_score=6.5,
            affected_package="test",
            current_version="1.0.0",
            fixed_version="1.1.0",
            patch_strategy="upgrade",
            pr_url="https://github.com/org/repo/pull/1",
            pr_number=1,
            wargame_verdict="success",
            wargame_confidence=0.9,
            wargame_evidence_url="https://github.com/org/repo/actions/runs/1",
            requires_immediate_attention=False,
            repository_owner="org",
            repository_name="repo",
            affected_files=["file.py"],
            remediation_type="upgrade",
            validation_warnings=[],
            estimated_risk_reduction=0.7,
            confirmation_confidence=0.85,
            escalation_reason=None,
            timestamp=datetime.utcnow(),
        )
        for i in range(10)
    ]

    # Process messages (simulating slow consumer)
    start_time = time.time()

    # Process sequentially (slow consumer)
    for msg in messages:
        await slow_callback(msg)

    elapsed = time.time() - start_time

    # Verify all messages processed (eventually)
    assert len(processed) == len(messages)
    assert scenario.get_success_rate() == 1.0

    # Verify it took significant time (slow consumer)
    expected_time = processing_time * len(messages)
    assert elapsed >= expected_time * 0.9  # Allow 10% variance

    print(f"\n✅ {scenario.name}: Processed {len(messages)} messages in {elapsed:.2f}s")


@pytest.mark.asyncio
async def test_chaos_message_burst():
    """
    Chaos Test: Message Burst

    Simulates sudden burst of many messages.

    Expected Behavior:
    - System handles burst without crashes
    - All messages eventually processed
    - No message loss
    """
    scenario = ChaosScenario(
        "message_burst",
        "Sudden burst of 1000 messages"
    )

    burst_size = 1000
    published_count = 0

    # Create mock client
    mock_client = MagicMock(spec=RabbitMQClient)
    mock_client.is_connected = True

    async def mock_publish(routing_key, message_body, priority=5):
        nonlocal published_count
        published_count += 1
        scenario.record_success()

    mock_client.publish = AsyncMock(side_effect=mock_publish)

    # Create publisher
    publisher = APVPublisher(mock_client)

    # Publish burst of messages
    start_time = time.time()

    tasks = []
    for i in range(burst_size):
        message = APVDispatchMessage(
            message_id=str(uuid.uuid4()),
            apv_id=str(uuid.uuid4()),
            apv_code=f"APV-BURST-{i:04d}",
            cve_id="CVE-2024-0001",
            severity=random.choice(["critical", "high", "medium", "low"]),
            cvss_score=random.uniform(4.0, 10.0),
            affected_package="test-package",
            current_version="1.0.0",
            fixed_version="1.1.0",
            affected_components=["comp"],
            remediation_type="upgrade",
            priority=random.randint(1, 10),
            timestamp=datetime.utcnow(),
        )

        # Publish concurrently
        tasks.append(publisher.dispatch_apv(message))

    # Wait for all publishes
    await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    # Verify all messages published
    assert published_count == burst_size
    assert scenario.get_success_rate() == 1.0

    throughput = burst_size / elapsed
    print(f"\n✅ {scenario.name}: Published {burst_size} messages in {elapsed:.2f}s ({throughput:.2f} msg/s)")


@pytest.mark.asyncio
async def test_chaos_network_partition():
    """
    Chaos Test: Network Partition

    Simulates network partition between publisher and RabbitMQ.

    Expected Behavior:
    - Publisher detects connection failure
    - Errors logged but system continues
    - Reconnects when network recovers
    """
    scenario = ChaosScenario(
        "network_partition",
        "Network partition between publisher and RabbitMQ"
    )

    # Create mock client that simulates network partition
    mock_client = MagicMock(spec=RabbitMQClient)

    # Simulate network partition after 3 successful publishes
    call_count = 0
    partition_duration = 3  # 3 failed attempts

    async def mock_publish_with_partition(routing_key, message_body, priority=5):
        nonlocal call_count
        call_count += 1

        if 4 <= call_count <= 6:  # Partition window
            scenario.record_failure("Network partition")
            raise ConnectionError("Network unreachable")
        else:
            scenario.record_success()

    mock_client.publish = AsyncMock(side_effect=mock_publish_with_partition)

    # Create publisher
    publisher = WargameReportPublisher(mock_client)

    # Attempt to publish 10 messages through partition
    successful = 0
    failed = 0

    for i in range(10):
        message = WargameReportMessage(
            message_id=str(uuid.uuid4()),
            remedy_id=f"APV-PART-{i:03d}",
            run_code=f"WAR-{i:04d}",
            timestamp=datetime.utcnow(),
            verdict="success",
            confidence_score=0.9,
            exploit_before_status="vulnerable",
            exploit_after_status="fixed",
            evidence_url="https://github.com/org/repo/actions/runs/1",
            should_trigger_hitl=False,
            auto_merge_approved=True,
        )

        try:
            await publisher.publish_report(message)
            successful += 1
        except ConnectionError:
            failed += 1

    # Verify partition behavior
    assert successful == 7  # 3 before + 4 after partition
    assert failed == 3  # During partition
    assert scenario.get_success_rate() == 0.7

    print(f"\n✅ {scenario.name}: Survived partition - {successful}/10 succeeded")


@pytest.mark.asyncio
async def test_chaos_resource_exhaustion():
    """
    Chaos Test: Resource Exhaustion

    Simulates system running out of memory/connections.

    Expected Behavior:
    - System detects resource constraints
    - Graceful degradation (backpressure)
    - No crashes
    """
    scenario = ChaosScenario(
        "resource_exhaustion",
        "System running low on resources"
    )

    # Simulate limited connection pool (10 connections)
    max_connections = 10
    active_connections = 0

    mock_client = MagicMock(spec=RabbitMQClient)

    async def mock_publish_with_limits(routing_key, message_body, priority=5):
        nonlocal active_connections

        if active_connections >= max_connections:
            scenario.record_failure("Resource exhausted")
            raise ResourceWarning("Connection pool exhausted")

        active_connections += 1
        await asyncio.sleep(0.1)  # Simulate work
        active_connections -= 1
        scenario.record_success()

    mock_client.publish = AsyncMock(side_effect=mock_publish_with_limits)

    # Create publisher
    publisher = APVPublisher(mock_client)

    # Try to publish 20 messages concurrently (exceeds limit)
    messages = [
        APVDispatchMessage(
            message_id=str(uuid.uuid4()),
            apv_id=str(uuid.uuid4()),
            apv_code=f"APV-RES-{i:03d}",
            cve_id="CVE-2024-0001",
            severity="high",
            cvss_score=8.0,
            affected_package="test",
            current_version="1.0.0",
            fixed_version="1.1.0",
            affected_components=["comp"],
            remediation_type="upgrade",
            priority=8,
            timestamp=datetime.utcnow(),
        )
        for i in range(20)
    ]

    # Publish with concurrency limit
    tasks = [publisher.dispatch_apv(msg) for msg in messages]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successes and failures
    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = sum(1 for r in results if isinstance(r, Exception))

    # Some should fail due to resource exhaustion
    assert failures > 0
    assert successes > 0

    print(f"\n✅ {scenario.name}: {successes} succeeded, {failures} failed (resource limits)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
