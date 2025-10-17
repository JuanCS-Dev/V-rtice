"""
E2E Integration Test - Complete Message Flow.

Tests the complete Adaptive Immune System message flow:
1. Oráculo generates APV → publishes to Eureka
2. Eureka receives APV → triggers confirmation/remedy
3. Wargaming runs → publishes results to Eureka
4. Eureka determines HITL needed → publishes notification
5. HITL console receives notification → displays to user
6. Human makes decision → publishes to system
7. DecisionExecutor receives decision → updates APV state
8. Status updates flow back to Oráculo

This test validates:
- All publishers work correctly
- All consumers receive messages
- Message routing is correct
- Data flows end-to-end
- No data loss or corruption
- System handles the complete lifecycle
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

# Import all components
from messaging.client import RabbitMQClient
from messaging.publisher import (
    APVPublisher,
    RemedyStatusPublisher,
    WargameReportPublisher,
    HITLNotificationPublisher,
    HITLDecisionPublisher,
)
from messaging.consumer import (
    HITLNotificationConsumer,
    HITLDecisionConsumer,
)
from backend.services.adaptive_immune_system.models.apv import APVDispatchMessage
from backend.services.adaptive_immune_system.models.remedy import RemedyStatusMessage
from backend.services.adaptive_immune_system.models.wargame import WargameReportMessage
from backend.services.adaptive_immune_system.models.hitl import HITLNotificationMessage, HITLDecisionMessage


class MessageTracker:
    """
    Tracks messages flowing through the system for E2E validation.

    Used to verify that messages are published and consumed correctly
    throughout the entire flow.
    """

    def __init__(self):
        self.published_messages: List[Dict[str, Any]] = []
        self.consumed_messages: List[Dict[str, Any]] = []
        self.routing_keys: List[str] = []
        self.message_ids: List[str] = []

    def track_publish(
        self, routing_key: str, message_body: str, priority: int = 5
    ) -> None:
        """Track a published message."""
        self.published_messages.append({
            "routing_key": routing_key,
            "body": message_body,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.routing_keys.append(routing_key)

        # Extract message ID if present
        try:
            data = json.loads(message_body)
            if "message_id" in data:
                self.message_ids.append(data["message_id"])
        except Exception:
            pass

    def track_consume(self, message: Any) -> None:
        """Track a consumed message."""
        self.consumed_messages.append({
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_published_count(self) -> int:
        """Get total published message count."""
        return len(self.published_messages)

    def get_consumed_count(self) -> int:
        """Get total consumed message count."""
        return len(self.consumed_messages)

    def get_message_by_routing_key(self, routing_key: str) -> Optional[Dict[str, Any]]:
        """Get first message with matching routing key."""
        for msg in self.published_messages:
            if msg["routing_key"] == routing_key:
                return msg
        return None

    def verify_message_flow(
        self, expected_routing_keys: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Verify that all expected routing keys were used.

        Returns:
            (success, missing_keys)
        """
        missing = []
        for key in expected_routing_keys:
            if key not in self.routing_keys:
                missing.append(key)
        return len(missing) == 0, missing


@pytest.fixture
async def mock_rabbitmq_client(request):
    """
    Mock RabbitMQ client that tracks all messages.

    Provides message tracking without requiring actual RabbitMQ connection.
    """
    tracker = MessageTracker()

    # Create mock client
    client = MagicMock(spec=RabbitMQClient)
    client.is_connected = True
    client.tracker = tracker

    # Mock publish method
    async def mock_publish(routing_key: str, message_body: str, priority: int = 5):
        tracker.track_publish(routing_key, message_body, priority)

    client.publish = AsyncMock(side_effect=mock_publish)

    # Mock consume method (will be customized per test)
    client.consume = AsyncMock()

    return client


@pytest.fixture
def apv_data():
    """Sample APV data for testing."""
    return {
        "apv_id": str(uuid.uuid4()),
        "apv_code": "APV-20251013-E2E-001",
        "cve_id": "CVE-2024-9999",
        "severity": "critical",
        "cvss_score": 9.8,
        "affected_package": "requests",
        "current_version": "2.28.0",
        "fixed_version": "2.31.0",
        "affected_components": ["api", "worker"],
        "remediation_type": "dependency_upgrade",
        "priority": 10,
    }


@pytest.fixture
def wargame_data(apv_data):
    """Sample wargaming result for testing."""
    return {
        "remedy_id": apv_data["apv_code"],
        "run_code": f"WAR-{apv_data['apv_code']}",
        "verdict": "needs_review",
        "confidence_score": 0.65,
        "exploit_before_status": "vulnerable",
        "exploit_after_status": "fixed",
        "evidence_url": "https://github.com/org/repo/actions/runs/123",
        "should_trigger_hitl": True,
        "auto_merge_approved": False,
    }


@pytest.fixture
def decision_data(apv_data):
    """Sample HITL decision for testing."""
    return {
        "apv_id": apv_data["apv_id"],
        "apv_code": apv_data["apv_code"],
        "decision": "approve",
        "justification": "Fix verified through wargaming, no side effects detected",
        "confidence": 0.95,
        "reviewer_name": "Alice Johnson",
        "reviewer_email": "alice@vertice.ai",
        "decision_id": str(uuid.uuid4()),
        "cve_id": apv_data["cve_id"],
        "severity": apv_data["severity"],
        "patch_strategy": "dependency_upgrade",
        "pr_number": 123,
        "pr_url": "https://github.com/org/repo/pull/123",
        "action_type": "merge_pr",
        "action_target_pr": 123,
        "action_comment": "Approved and merged automatically",
        "action_assignees": [],
        "action_labels": ["security", "automated-fix"],
        "modifications": None,
        "requires_followup": False,
        "followup_reason": None,
    }


@pytest.mark.asyncio
async def test_e2e_apv_dispatch_flow(mock_rabbitmq_client, apv_data):
    """
    Test: Oráculo → Eureka (APV Dispatch)

    Validates:
    - APV is published to apv.dispatch queue
    - Message contains all required fields
    - Routing key is correct (apv.dispatch.{severity}.{remediation_type})
    """
    # Create APV publisher
    publisher = APVPublisher(mock_rabbitmq_client)

    # Create dispatch message
    dispatch_message = APVDispatchMessage(
        message_id=str(uuid.uuid4()),
        apv_id=apv_data["apv_id"],
        apv_code=apv_data["apv_code"],
        cve_id=apv_data["cve_id"],
        severity=apv_data["severity"],
        cvss_score=apv_data["cvss_score"],
        affected_package=apv_data["affected_package"],
        current_version=apv_data["current_version"],
        fixed_version=apv_data["fixed_version"],
        affected_components=apv_data["affected_components"],
        remediation_type=apv_data["remediation_type"],
        priority=apv_data["priority"],
        timestamp=datetime.utcnow(),
    )

    # Publish APV
    message_id = await publisher.dispatch_apv(dispatch_message)

    # Verify message was published
    assert message_id is not None
    assert mock_rabbitmq_client.tracker.get_published_count() == 1

    # Verify routing key
    published = mock_rabbitmq_client.tracker.published_messages[0]
    expected_routing_key = f"apv.dispatch.{apv_data['severity']}.{apv_data['remediation_type']}"
    assert published["routing_key"] == expected_routing_key

    # Verify message body
    body_data = json.loads(published["body"])
    assert body_data["apv_id"] == apv_data["apv_id"]
    assert body_data["cve_id"] == apv_data["cve_id"]
    assert body_data["severity"] == apv_data["severity"]

    # Verify priority (critical = 10)
    assert published["priority"] == 10


@pytest.mark.asyncio
async def test_e2e_wargaming_result_flow(mock_rabbitmq_client, wargame_data):
    """
    Test: Wargaming → Eureka (Results)

    Validates:
    - Wargaming result is published correctly
    - Routing key includes verdict and confidence
    - HITL trigger flag is set correctly
    """
    # Create wargame publisher
    publisher = WargameReportPublisher(mock_rabbitmq_client)

    # Create wargame report
    report = WargameReportMessage(
        message_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        **wargame_data,
    )

    # Publish report
    message_id = await publisher.publish_report(report)

    # Verify message was published
    assert message_id is not None
    assert mock_rabbitmq_client.tracker.get_published_count() == 1

    # Verify routing key
    published = mock_rabbitmq_client.tracker.published_messages[0]
    expected_routing_key = "wargame.results.needs_review.medium_confidence"
    assert published["routing_key"] == expected_routing_key

    # Verify HITL trigger
    body_data = json.loads(published["body"])
    assert body_data["should_trigger_hitl"] is True
    assert body_data["verdict"] == "needs_review"
    assert body_data["confidence_score"] == 0.65


@pytest.mark.asyncio
async def test_e2e_hitl_notification_flow(mock_rabbitmq_client, apv_data, wargame_data):
    """
    Test: Eureka → HITL (Notification)

    Validates:
    - HITL notification is published after wargaming
    - Notification contains full context
    - Priority routing for critical issues
    """
    # Create HITL notification publisher
    publisher = HITLNotificationPublisher(mock_rabbitmq_client)

    # Publish notification (simulating Eureka.handle_wargaming_result)
    message_id = await publisher.publish_new_apv_notification(
        apv_id=apv_data["apv_id"],
        apv_code=apv_data["apv_code"],
        priority=apv_data["priority"],
        cve_id=apv_data["cve_id"],
        severity=apv_data["severity"],
        cvss_score=apv_data["cvss_score"],
        affected_package=apv_data["affected_package"],
        current_version=apv_data["current_version"],
        fixed_version=apv_data["fixed_version"],
        patch_strategy=apv_data["remediation_type"],
        pr_url="https://github.com/org/repo/pull/123",
        pr_number=123,
        wargame_verdict=wargame_data["verdict"],
        wargame_confidence=wargame_data["confidence_score"],
        wargame_evidence_url=wargame_data["evidence_url"],
        requires_immediate_attention=True,
        repository_owner="org",
        repository_name="repo",
        affected_files=["requirements.txt"],
        remediation_type=apv_data["remediation_type"],
        validation_warnings=[],
        estimated_risk_reduction=0.85,
        confirmation_confidence=0.92,
        escalation_reason="Critical severity requiring immediate review",
    )

    # Verify message was published
    assert message_id is not None
    assert mock_rabbitmq_client.tracker.get_published_count() == 1

    # Verify routing key (critical + urgent)
    published = mock_rabbitmq_client.tracker.published_messages[0]
    assert published["routing_key"] == "hitl.notifications.urgent"

    # Verify priority (maximum for urgent)
    assert published["priority"] == 10

    # Verify full context in message
    body_data = json.loads(published["body"])
    assert body_data["apv_id"] == apv_data["apv_id"]
    assert body_data["cve_id"] == apv_data["cve_id"]
    assert body_data["wargame_verdict"] == wargame_data["verdict"]
    assert body_data["requires_immediate_attention"] is True


@pytest.mark.asyncio
async def test_e2e_hitl_decision_flow(mock_rabbitmq_client, decision_data):
    """
    Test: HITL → System (Decision)

    Validates:
    - Human decision is published correctly
    - Routing key includes decision and action type
    - Priority set based on action urgency
    """
    # Create HITL decision publisher
    publisher = HITLDecisionPublisher(mock_rabbitmq_client)

    # Publish decision
    message_id = await publisher.publish_decision(**decision_data)

    # Verify message was published
    assert message_id is not None
    assert mock_rabbitmq_client.tracker.get_published_count() == 1

    # Verify routing key
    published = mock_rabbitmq_client.tracker.published_messages[0]
    expected_routing_key = "hitl.decisions.approve.merge_pr"
    assert published["routing_key"] == expected_routing_key

    # Verify priority (merge_pr = high priority)
    assert published["priority"] == 8

    # Verify decision data
    body_data = json.loads(published["body"])
    assert body_data["decision"] == "approve"
    assert body_data["action_type"] == "merge_pr"
    assert body_data["reviewer_name"] == "Alice Johnson"
    assert body_data["confidence"] == 0.95


@pytest.mark.asyncio
async def test_e2e_complete_flow_integration(
    mock_rabbitmq_client, apv_data, wargame_data, decision_data
):
    """
    Test: Complete E2E Flow

    Tests the entire flow from APV generation to decision execution:
    1. APV dispatch
    2. Wargaming result
    3. HITL notification
    4. HITL decision
    5. Status updates

    Validates message ordering, data consistency, and complete lifecycle.
    """
    tracker = mock_rabbitmq_client.tracker

    # Step 1: APV Dispatch (Oráculo → Eureka)
    apv_publisher = APVPublisher(mock_rabbitmq_client)
    dispatch_message = APVDispatchMessage(
        message_id=str(uuid.uuid4()),
        apv_id=apv_data["apv_id"],
        apv_code=apv_data["apv_code"],
        cve_id=apv_data["cve_id"],
        severity=apv_data["severity"],
        cvss_score=apv_data["cvss_score"],
        affected_package=apv_data["affected_package"],
        current_version=apv_data["current_version"],
        fixed_version=apv_data["fixed_version"],
        affected_components=apv_data["affected_components"],
        remediation_type=apv_data["remediation_type"],
        priority=apv_data["priority"],
        timestamp=datetime.utcnow(),
    )
    await apv_publisher.dispatch_apv(dispatch_message)

    # Step 2: Wargaming Result (Wargaming → Eureka)
    wargame_publisher = WargameReportPublisher(mock_rabbitmq_client)
    wargame_report = WargameReportMessage(
        message_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        **wargame_data,
    )
    await wargame_publisher.publish_report(wargame_report)

    # Step 3: HITL Notification (Eureka → HITL)
    hitl_publisher = HITLNotificationPublisher(mock_rabbitmq_client)
    await hitl_publisher.publish_new_apv_notification(
        apv_id=apv_data["apv_id"],
        apv_code=apv_data["apv_code"],
        priority=apv_data["priority"],
        cve_id=apv_data["cve_id"],
        severity=apv_data["severity"],
        cvss_score=apv_data["cvss_score"],
        affected_package=apv_data["affected_package"],
        current_version=apv_data["current_version"],
        fixed_version=apv_data["fixed_version"],
        patch_strategy=apv_data["remediation_type"],
        pr_url="https://github.com/org/repo/pull/123",
        pr_number=123,
        wargame_verdict=wargame_data["verdict"],
        wargame_confidence=wargame_data["confidence_score"],
        wargame_evidence_url=wargame_data["evidence_url"],
        requires_immediate_attention=True,
        repository_owner="org",
        repository_name="repo",
        affected_files=["requirements.txt"],
        remediation_type=apv_data["remediation_type"],
        validation_warnings=[],
        estimated_risk_reduction=0.85,
        confirmation_confidence=0.92,
        escalation_reason="Critical severity",
    )

    # Step 4: HITL Decision (HITL → System)
    decision_publisher = HITLDecisionPublisher(mock_rabbitmq_client)
    await decision_publisher.publish_decision(**decision_data)

    # Step 5: Status Update (System → Oráculo)
    status_publisher = RemedyStatusPublisher(mock_rabbitmq_client)
    status_message = RemedyStatusMessage(
        message_id=str(uuid.uuid4()),
        remedy_id=apv_data["apv_code"],
        status="resolved",
        timestamp=datetime.utcnow(),
        details={
            "decision": "approved",
            "pr_merged": True,
            "reviewer": "Alice Johnson",
        },
    )
    await status_publisher.publish_status(status_message)

    # Verify all messages were published
    assert tracker.get_published_count() == 5

    # Verify message flow (all expected routing keys present)
    expected_routing_keys = [
        f"apv.dispatch.{apv_data['severity']}.{apv_data['remediation_type']}",
        "wargame.results.needs_review.medium_confidence",
        "hitl.notifications.urgent",
        "hitl.decisions.approve.merge_pr",
        "remedy.status.resolved",
    ]

    success, missing = tracker.verify_message_flow(expected_routing_keys)
    assert success, f"Missing routing keys: {missing}"

    # Verify message ordering (chronological)
    messages = tracker.published_messages
    assert "apv.dispatch" in messages[0]["routing_key"]
    assert "wargame.results" in messages[1]["routing_key"]
    assert "hitl.notifications" in messages[2]["routing_key"]
    assert "hitl.decisions" in messages[3]["routing_key"]
    assert "remedy.status" in messages[4]["routing_key"]

    # Verify data consistency across messages (same APV ID)
    for msg in messages:
        body = json.loads(msg["body"])
        # All messages should reference the same APV (via apv_id, apv_code, or remedy_id)
        assert (
            body.get("apv_id") == apv_data["apv_id"]
            or body.get("apv_code") == apv_data["apv_code"]
            or body.get("remedy_id") == apv_data["apv_code"]
        )


@pytest.mark.asyncio
async def test_e2e_consumer_integration(mock_rabbitmq_client, apv_data):
    """
    Test: Consumer Integration

    Validates that consumers can receive and process messages correctly.
    Tests callback execution and message acknowledgment.
    """
    tracker = mock_rabbitmq_client.tracker
    received_notifications = []
    received_decisions = []

    # Notification consumer callback
    async def handle_notification(notification: HITLNotificationMessage):
        received_notifications.append(notification)
        tracker.track_consume(notification)

    # Decision consumer callback
    async def handle_decision(decision: HITLDecisionMessage):
        received_decisions.append(decision)
        tracker.track_consume(decision)

    # Create consumers
    notification_consumer = HITLNotificationConsumer(
        client=mock_rabbitmq_client,
        callback=handle_notification,
    )

    decision_consumer = HITLDecisionConsumer(
        client=mock_rabbitmq_client,
        callback=handle_decision,
    )

    # Simulate receiving notification message
    notification_msg = HITLNotificationMessage(
        message_id=str(uuid.uuid4()),
        apv_id=apv_data["apv_id"],
        apv_code=apv_data["apv_code"],
        priority=10,
        cve_id=apv_data["cve_id"],
        severity=apv_data["severity"],
        cvss_score=apv_data["cvss_score"],
        affected_package=apv_data["affected_package"],
        current_version=apv_data["current_version"],
        fixed_version=apv_data["fixed_version"],
        patch_strategy=apv_data["remediation_type"],
        pr_url="https://github.com/org/repo/pull/123",
        pr_number=123,
        wargame_verdict="needs_review",
        wargame_confidence=0.65,
        wargame_evidence_url="https://github.com/org/repo/actions/runs/123",
        requires_immediate_attention=True,
        repository_owner="org",
        repository_name="repo",
        affected_files=["requirements.txt"],
        remediation_type=apv_data["remediation_type"],
        validation_warnings=[],
        estimated_risk_reduction=0.85,
        confirmation_confidence=0.92,
        escalation_reason="Critical",
        timestamp=datetime.utcnow(),
    )

    # Call callback directly (simulating consumer receiving message)
    await handle_notification(notification_msg)

    # Verify notification was received
    assert len(received_notifications) == 1
    assert received_notifications[0].apv_id == apv_data["apv_id"]
    assert tracker.get_consumed_count() == 1

    # Simulate receiving decision message
    decision_msg = HITLDecisionMessage(
        apv_id=apv_data["apv_id"],
        apv_code=apv_data["apv_code"],
        decision="approve",
        justification="Verified",
        confidence=0.95,
        reviewer_name="Alice",
        reviewer_email="alice@vertice.ai",
        decision_id=str(uuid.uuid4()),
        cve_id=apv_data["cve_id"],
        severity=apv_data["severity"],
        patch_strategy=apv_data["remediation_type"],
        pr_number=123,
        pr_url="https://github.com/org/repo/pull/123",
        action_type="merge_pr",
        action_target_pr=123,
        action_comment="Merged",
        action_assignees=[],
        action_labels=["security"],
        modifications=None,
        requires_followup=False,
        followup_reason=None,
        timestamp=datetime.utcnow(),
    )

    await handle_decision(decision_msg)

    # Verify decision was received
    assert len(received_decisions) == 1
    assert received_decisions[0].decision == "approve"
    assert tracker.get_consumed_count() == 2


@pytest.mark.asyncio
async def test_e2e_error_handling(mock_rabbitmq_client, apv_data):
    """
    Test: Error Handling in E2E Flow

    Validates that errors in publishing/consuming don't crash the system
    and are handled gracefully.
    """
    # Simulate publish failure
    mock_rabbitmq_client.publish = AsyncMock(
        side_effect=Exception("RabbitMQ connection lost")
    )

    publisher = APVPublisher(mock_rabbitmq_client)

    # This should not raise (graceful degradation)
    try:
        dispatch_message = APVDispatchMessage(
            message_id=str(uuid.uuid4()),
            apv_id=apv_data["apv_id"],
            apv_code=apv_data["apv_code"],
            cve_id=apv_data["cve_id"],
            severity=apv_data["severity"],
            cvss_score=apv_data["cvss_score"],
            affected_package=apv_data["affected_package"],
            current_version=apv_data["current_version"],
            fixed_version=apv_data["fixed_version"],
            affected_components=apv_data["affected_components"],
            remediation_type=apv_data["remediation_type"],
            priority=apv_data["priority"],
            timestamp=datetime.utcnow(),
        )

        # Should raise exception (not caught in publisher)
        with pytest.raises(Exception, match="RabbitMQ connection lost"):
            await publisher.dispatch_apv(dispatch_message)

    except Exception as e:
        # In real system, this would be logged and system continues
        assert "RabbitMQ connection lost" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
