"""Tests for Human Approval Workflow - High-Risk Patch Approval.

Validates approval workflow, notifications, timeouts, and state management.

Biblical Foundation: Proverbs 15:22 - "Plans fail for lack of counsel"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
from datetime import datetime, timedelta

from core.human_approval import ApprovalStatus, HumanApprovalWorkflow
import pytest

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def approval_workflow():
    """HumanApprovalWorkflow instance (no notifiers)."""
    return HumanApprovalWorkflow(
        slack_notifier=None, email_notifier=None, audit_logger=None
    )


@pytest.fixture
def mock_slack_notifier():
    """Mock Slack notifier."""

    class MockSlackNotifier:
        def __init__(self):
            self.messages_sent = []

        async def send_message(self, channel: str, message: str):
            self.messages_sent.append({"channel": channel, "message": message})

    return MockSlackNotifier()


@pytest.fixture
def mock_email_notifier():
    """Mock Email notifier."""

    class MockEmailNotifier:
        def __init__(self):
            self.emails_sent = []

        async def send_email(self, to: str, subject: str, body: str):
            self.emails_sent.append({"to": to, "subject": subject, "body": body})

    return MockEmailNotifier()


# ============================================================================
# TESTS: Approval Request Creation
# ============================================================================


class TestApprovalRequestCreation:
    """Test creating and managing approval requests."""

    @pytest.mark.asyncio
    async def test_request_approval_creates_pending_request(self, approval_workflow):
        """
        GIVEN: High-risk patch requiring approval
        WHEN: request_approval() is called
        THEN: Pending request created, waits for decision
        """
        # Start approval request in background
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-001",
                patch="def fix(): pass",
                risk_score=0.85,
                impact_estimate="High impact on production",
                timeout_seconds=5,  # Short timeout for testing
            )
        )

        # Wait for request to be created
        await asyncio.sleep(0.1)

        # Check pending requests
        pending = await approval_workflow.get_pending_requests()
        assert len(pending) == 1
        assert pending[0]["anomaly_id"] == "anomaly-001"
        assert pending[0]["risk_score"] == 0.85

        # Approve it
        approval_id = pending[0]["approval_id"]
        approved = await approval_workflow.approve(approval_id, approver="admin")
        assert approved is True

        # Wait for task to complete
        result = await task

        assert result["approved"] is True
        assert result["approver"] == "admin"

    @pytest.mark.asyncio
    async def test_request_timeout_auto_rejects(self, approval_workflow):
        """
        GIVEN: Approval request with short timeout
        WHEN: No approval given before timeout
        THEN: Request auto-rejects with EXPIRED status
        """
        result = await approval_workflow.request_approval(
            anomaly_id="anomaly-002",
            patch="def fix(): pass",
            risk_score=0.75,
            impact_estimate="Medium impact",
            timeout_seconds=1,  # 1 second timeout
        )

        assert result["approved"] is False
        assert result["status"] == ApprovalStatus.EXPIRED.value
        assert result["approver"] is None


# ============================================================================
# TESTS: Approval Actions
# ============================================================================


class TestApprovalActions:
    """Test approve/reject/cancel actions."""

    @pytest.mark.asyncio
    async def test_approve_pending_request(self, approval_workflow):
        """
        GIVEN: Pending approval request
        WHEN: approve() is called
        THEN: Request marked as approved
        """
        # Create request
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-003",
                patch="def fix(): pass",
                risk_score=0.8,
                impact_estimate="High",
                timeout_seconds=10,
            )
        )

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        approval_id = pending[0]["approval_id"]

        # Approve
        success = await approval_workflow.approve(
            approval_id, approver="john.doe", notes="LGTM"
        )

        assert success is True

        # Check result
        result = await task
        assert result["approved"] is True
        assert result["approver"] == "john.doe"
        assert result["notes"] == "LGTM"
        assert result["status"] == ApprovalStatus.APPROVED.value

    @pytest.mark.asyncio
    async def test_reject_pending_request(self, approval_workflow):
        """
        GIVEN: Pending approval request
        WHEN: reject() is called
        THEN: Request marked as rejected
        """
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-004",
                patch="def fix(): pass",
                risk_score=0.9,
                impact_estimate="Very high",
                timeout_seconds=10,
            )
        )

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        approval_id = pending[0]["approval_id"]

        # Reject
        success = await approval_workflow.reject(
            approval_id,
            approver="jane.smith",
            reason="Too risky for production",
            notes="Need more testing",
        )

        assert success is True

        # Check result
        result = await task
        assert result["approved"] is False
        assert result["approver"] == "jane.smith"
        assert result["rejection_reason"] == "Too risky for production"
        assert result["notes"] == "Need more testing"
        assert result["status"] == ApprovalStatus.REJECTED.value

    @pytest.mark.asyncio
    async def test_cancel_pending_request(self, approval_workflow):
        """
        GIVEN: Pending approval request
        WHEN: cancel() is called
        THEN: Request marked as cancelled
        """
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-005",
                patch="def fix(): pass",
                risk_score=0.7,
                impact_estimate="Medium",
                timeout_seconds=10,
            )
        )

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        approval_id = pending[0]["approval_id"]

        # Cancel
        success = await approval_workflow.cancel(approval_id)
        assert success is True

        # Check result
        result = await task
        assert result["status"] == ApprovalStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_approve_nonexistent_request(self, approval_workflow):
        """
        GIVEN: No pending requests
        WHEN: approve() called with invalid ID
        THEN: Returns False
        """
        success = await approval_workflow.approve("non-existent-id", approver="admin")
        assert success is False

    @pytest.mark.asyncio
    async def test_cannot_approve_already_resolved(self, approval_workflow):
        """
        GIVEN: Already approved request
        WHEN: approve() called again
        THEN: Returns False (cannot re-approve)
        """
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-006",
                patch="def fix(): pass",
                risk_score=0.75,
                impact_estimate="Medium",
                timeout_seconds=10,
            )
        )

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        approval_id = pending[0]["approval_id"]

        # First approval
        await approval_workflow.approve(approval_id, approver="admin1")

        # Second approval attempt
        success = await approval_workflow.approve(approval_id, approver="admin2")
        assert success is False

        await task


# ============================================================================
# TESTS: Request Status Queries
# ============================================================================


class TestRequestStatusQueries:
    """Test querying request status."""

    @pytest.mark.asyncio
    async def test_get_pending_requests_empty(self, approval_workflow):
        """
        GIVEN: No pending requests
        WHEN: get_pending_requests() is called
        THEN: Returns empty list
        """
        pending = await approval_workflow.get_pending_requests()
        assert pending == []

    @pytest.mark.asyncio
    async def test_get_pending_requests_multiple(self, approval_workflow):
        """
        GIVEN: Multiple pending requests
        WHEN: get_pending_requests() is called
        THEN: Returns all pending requests
        """
        # Create 3 requests
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                approval_workflow.request_approval(
                    anomaly_id=f"anomaly-{i}",
                    patch=f"def fix_{i}(): pass",
                    risk_score=0.7 + i * 0.05,
                    impact_estimate="High",
                    timeout_seconds=10,
                )
            )
            tasks.append(task)

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        assert len(pending) == 3

        # Approve all
        for req in pending:
            await approval_workflow.approve(req["approval_id"], approver="admin")

        # Wait for tasks
        await asyncio.gather(*tasks)

    @pytest.mark.asyncio
    async def test_get_request_status(self, approval_workflow):
        """
        GIVEN: Approval request
        WHEN: get_request_status() is called
        THEN: Returns detailed status
        """
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-007",
                patch="def fix(): pass",
                risk_score=0.82,
                impact_estimate="High impact",
                timeout_seconds=10,
            )
        )

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        approval_id = pending[0]["approval_id"]

        # Get status
        status = await approval_workflow.get_request_status(approval_id)

        assert status is not None
        assert status["approval_id"] == approval_id
        assert status["anomaly_id"] == "anomaly-007"
        assert status["status"] == ApprovalStatus.PENDING.value
        assert status["risk_score"] == 0.82
        assert status["remaining_seconds"] > 0

        # Approve and complete
        await approval_workflow.approve(approval_id, approver="admin")
        await task

    @pytest.mark.asyncio
    async def test_get_request_status_not_found(self, approval_workflow):
        """
        GIVEN: No requests
        WHEN: get_request_status() called with invalid ID
        THEN: Returns None
        """
        status = await approval_workflow.get_request_status("invalid-id")
        assert status is None


# ============================================================================
# TESTS: Notification Integration
# ============================================================================


class TestNotificationIntegration:
    """Test Slack/Email notification integration."""

    @pytest.mark.asyncio
    async def test_slack_notification_sent(self, mock_slack_notifier):
        """
        GIVEN: Workflow with Slack notifier
        WHEN: request_approval() is called
        THEN: Slack notification sent
        """
        workflow = HumanApprovalWorkflow(slack_notifier=mock_slack_notifier)

        task = asyncio.create_task(
            workflow.request_approval(
                anomaly_id="anomaly-008",
                patch="def fix(): pass",
                risk_score=0.88,
                impact_estimate="Critical",
                timeout_seconds=5,
            )
        )

        await asyncio.sleep(0.2)

        # Check Slack message sent
        assert len(mock_slack_notifier.messages_sent) == 1
        message = mock_slack_notifier.messages_sent[0]
        assert message["channel"] == "#penelope-approvals"
        assert "anomaly-008" in message["message"]
        assert "0.88" in message["message"]

        # Approve to complete
        pending = await workflow.get_pending_requests()
        await workflow.approve(pending[0]["approval_id"], approver="admin")
        await task

    @pytest.mark.asyncio
    async def test_email_notification_sent(self, mock_email_notifier):
        """
        GIVEN: Workflow with email notifier
        WHEN: request_approval() is called
        THEN: Email notification sent
        """
        workflow = HumanApprovalWorkflow(email_notifier=mock_email_notifier)

        task = asyncio.create_task(
            workflow.request_approval(
                anomaly_id="anomaly-009",
                patch="def fix(): pass",
                risk_score=0.92,
                impact_estimate="Critical",
                timeout_seconds=5,
            )
        )

        await asyncio.sleep(0.2)

        # Check email sent
        assert len(mock_email_notifier.emails_sent) == 1
        email = mock_email_notifier.emails_sent[0]
        assert email["to"] == "ops-team@vertice.ai"
        assert (
            "PENELOPE" in email["subject"]
        )  # Subject contains approval_id, not anomaly_id
        assert "anomaly-009" in email["body"]  # Body contains anomaly_id
        assert "0.92" in email["body"]

        # Approve to complete
        pending = await workflow.get_pending_requests()
        await workflow.approve(pending[0]["approval_id"], approver="admin")
        await task


# ============================================================================
# TESTS: Timeout Behavior
# ============================================================================


class TestTimeoutBehavior:
    """Test timeout and expiration logic."""

    @pytest.mark.asyncio
    async def test_request_expires_after_timeout(self, approval_workflow):
        """
        GIVEN: Request with 1 second timeout
        WHEN: No action taken
        THEN: Request expires and auto-rejects
        """
        result = await approval_workflow.request_approval(
            anomaly_id="anomaly-010",
            patch="def fix(): pass",
            risk_score=0.75,
            impact_estimate="Medium",
            timeout_seconds=1,
        )

        assert result["status"] == ApprovalStatus.EXPIRED.value
        assert result["approved"] is False

    @pytest.mark.asyncio
    async def test_cannot_approve_expired_request(self, approval_workflow):
        """
        GIVEN: Expired approval request
        WHEN: approve() is called
        THEN: Returns False (too late)
        """
        # Create request with very short timeout
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-011",
                patch="def fix(): pass",
                risk_score=0.8,
                impact_estimate="High",
                timeout_seconds=1,
            )
        )

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        approval_id = pending[0]["approval_id"]

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Try to approve (should fail)
        success = await approval_workflow.approve(approval_id, approver="admin")
        assert success is False

        await task


# ============================================================================
# TESTS: Cleanup and Maintenance
# ============================================================================


class TestCleanupMaintenance:
    """Test cleanup of old requests."""

    @pytest.mark.asyncio
    async def test_cleanup_old_requests(self, approval_workflow):
        """
        GIVEN: Old completed requests
        WHEN: cleanup_old_requests() is called
        THEN: Old requests removed from memory
        """
        # Create and approve request
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-012",
                patch="def fix(): pass",
                risk_score=0.7,
                impact_estimate="Medium",
                timeout_seconds=5,
            )
        )

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        approval_id = pending[0]["approval_id"]

        # Approve
        await approval_workflow.approve(approval_id, approver="admin")
        await task

        # Manually age the request
        request = approval_workflow.pending_requests[approval_id]
        request.requested_at = datetime.utcnow() - timedelta(hours=25)

        # Cleanup (max_age_hours=24)
        removed = await approval_workflow.cleanup_old_requests(max_age_hours=24)

        assert removed == 1
        assert approval_id not in approval_workflow.pending_requests

    @pytest.mark.asyncio
    async def test_cleanup_preserves_recent_requests(self, approval_workflow):
        """
        GIVEN: Recent completed request
        WHEN: cleanup_old_requests() is called
        THEN: Recent request preserved
        """
        task = asyncio.create_task(
            approval_workflow.request_approval(
                anomaly_id="anomaly-013",
                patch="def fix(): pass",
                risk_score=0.7,
                impact_estimate="Medium",
                timeout_seconds=5,
            )
        )

        await asyncio.sleep(0.1)

        pending = await approval_workflow.get_pending_requests()
        approval_id = pending[0]["approval_id"]

        # Approve
        await approval_workflow.approve(approval_id, approver="admin")
        await task

        # Cleanup (request is fresh, should not be removed)
        removed = await approval_workflow.cleanup_old_requests(max_age_hours=24)

        assert removed == 0
        assert approval_id in approval_workflow.pending_requests


# ============================================================================
# TESTS: Concurrency
# ============================================================================


class TestConcurrency:
    """Test concurrent approval requests."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, approval_workflow):
        """
        GIVEN: Multiple approval requests at once
        WHEN: All processed concurrently
        THEN: Each tracked independently
        """
        # Create 5 concurrent requests
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                approval_workflow.request_approval(
                    anomaly_id=f"anomaly-{i}",
                    patch=f"def fix_{i}(): pass",
                    risk_score=0.7 + i * 0.03,
                    impact_estimate="High",
                    timeout_seconds=10,
                )
            )
            tasks.append(task)

        await asyncio.sleep(0.2)

        # Check all pending
        pending = await approval_workflow.get_pending_requests()
        assert len(pending) == 5

        # Approve all
        for req in pending:
            await approval_workflow.approve(req["approval_id"], approver="admin")

        # Wait for all
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r["approved"] for r in results)


# ============================================================================
# INTEGRATION TEST: Full Approval Workflow
# ============================================================================


class TestFullApprovalWorkflow:
    """Test complete approval workflow lifecycle."""

    @pytest.mark.asyncio
    async def test_full_approval_lifecycle(
        self, mock_slack_notifier, mock_email_notifier
    ):
        """
        GIVEN: Complete workflow with notifiers
        WHEN: High-risk patch requires approval
        THEN: Complete lifecycle works correctly
        """
        workflow = HumanApprovalWorkflow(
            slack_notifier=mock_slack_notifier,
            email_notifier=mock_email_notifier,
            audit_logger=None,
        )

        # Step 1: Request approval
        task = asyncio.create_task(
            workflow.request_approval(
                anomaly_id="anomaly-critical",
                patch="def critical_fix():\n    # Fix production issue\n    pass",
                risk_score=0.95,
                impact_estimate="Critical production fix",
                timeout_seconds=10,
            )
        )

        await asyncio.sleep(0.2)

        # Step 2: Verify notifications sent
        assert len(mock_slack_notifier.messages_sent) == 1
        assert len(mock_email_notifier.emails_sent) == 1

        # Step 3: Check pending
        pending = await workflow.get_pending_requests()
        assert len(pending) == 1
        assert pending[0]["risk_score"] == 0.95

        # Step 4: Get detailed status
        approval_id = pending[0]["approval_id"]
        status = await workflow.get_request_status(approval_id)
        assert status["status"] == ApprovalStatus.PENDING.value

        # Step 5: Approve
        success = await workflow.approve(
            approval_id, approver="ops-lead", notes="Approved after review"
        )
        assert success is True

        # Step 6: Wait for result
        result = await task

        # Step 7: Verify result
        assert result["approved"] is True
        assert result["approver"] == "ops-lead"
        assert result["notes"] == "Approved after review"
        assert result["status"] == ApprovalStatus.APPROVED.value

        # Step 8: Verify no longer pending
        pending_after = await workflow.get_pending_requests()
        assert len(pending_after) == 0
