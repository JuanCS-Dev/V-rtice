"""Human Approval Workflow - High-Risk Patch Approval.

Implements human-in-the-loop approval for high-risk healing patches.
Provides safety mechanism requiring human oversight before risky interventions.

Human Oversight Principle: Wisdom includes knowing when to seek counsel
Biblical Foundation: Proverbs 15:22 - "Plans fail for lack of counsel"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any
from uuid import uuid4

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Status of approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalRequest:
    """Individual approval request with metadata."""

    def __init__(
        self,
        approval_id: str,
        anomaly_id: str,
        patch: str,
        risk_score: float,
        impact_estimate: str,
        requested_at: datetime,
        timeout_seconds: int,
    ):
        """Initialize approval request.

        Args:
            approval_id: Unique identifier for this request
            anomaly_id: Anomaly being addressed
            patch: Code patch requiring approval
            risk_score: Calculated risk score (0.0-1.0)
            impact_estimate: Human-readable impact description
            requested_at: When approval was requested
            timeout_seconds: Seconds until auto-reject
        """
        self.approval_id = approval_id
        self.anomaly_id = anomaly_id
        self.patch = patch
        self.risk_score = risk_score
        self.impact_estimate = impact_estimate
        self.requested_at = requested_at
        self.timeout_seconds = timeout_seconds

        # State
        self.status = ApprovalStatus.PENDING
        self.approved_by: str | None = None
        self.approved_at: datetime | None = None
        self.rejection_reason: str | None = None
        self.notes: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if request has expired."""
        if self.status != ApprovalStatus.PENDING:
            return False

        elapsed = (datetime.utcnow() - self.requested_at).total_seconds()
        return elapsed >= self.timeout_seconds

    @property
    def remaining_seconds(self) -> float:
        """Get remaining seconds before expiration."""
        if self.status != ApprovalStatus.PENDING:
            return 0.0

        elapsed = (datetime.utcnow() - self.requested_at).total_seconds()
        remaining = max(0.0, self.timeout_seconds - elapsed)
        return remaining


class HumanApprovalWorkflow:
    """Human-in-the-loop approval workflow for high-risk patches.

    Implements safety mechanism requiring human approval before deploying
    high-risk patches. Prevents autonomous system from making dangerous
    decisions without oversight.

    Architecture:
    - Async request/response pattern with timeout
    - Notification via Slack/Email (pluggable)
    - State management for pending approvals
    - Prometheus metrics for tracking
    - Audit trail integration

    Workflow:
    1. request_approval() creates request, sends notification
    2. Human reviews patch details in Slack/UI
    3. approve() or reject() called (via API or Slack command)
    4. Original request_approval() call resolves with decision
    5. If timeout reached, auto-reject

    Biblical Principle: Seek counsel in important decisions (Proverbs 15:22)
    """

    # Prometheus metrics
    approval_requests_total = Counter(
        "penelope_approval_requests_total",
        "Total approval requests created",
        ["status"],  # pending, approved, rejected, expired
    )

    approval_pending_gauge = Gauge(
        "penelope_approval_pending",
        "Current number of pending approval requests",
    )

    approval_response_time = Histogram(
        "penelope_approval_response_seconds",
        "Time from request to approval/rejection",
        buckets=[60, 300, 600, 1800, 3600, 7200, 14400],  # 1m to 4h
    )

    high_risk_patches_total = Counter(
        "penelope_high_risk_patches_total",
        "Total high-risk patches requiring approval",
    )

    def __init__(
        self,
        slack_notifier: Any | None = None,
        email_notifier: Any | None = None,
        audit_logger: Any | None = None,
    ):
        """Initialize Human Approval Workflow.

        Args:
            slack_notifier: Optional Slack notification client
            email_notifier: Optional email notification client
            audit_logger: Optional audit logger for tracking approvals
        """
        self.slack_notifier = slack_notifier
        self.email_notifier = email_notifier
        self.audit_logger = audit_logger

        # Active approval requests
        self.pending_requests: dict[str, ApprovalRequest] = {}

        # Approval events (for async waiting)
        self.approval_events: dict[str, asyncio.Event] = {}

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info("Human Approval Workflow initialized")

    async def request_approval(
        self,
        anomaly_id: str,
        patch: str,
        risk_score: float,
        impact_estimate: str,
        timeout_seconds: int = 7200,  # 2 hours default
    ) -> dict[str, Any]:
        """Request human approval for high-risk patch.

        Creates approval request, sends notifications, and waits for
        human decision (or timeout).

        Args:
            anomaly_id: Anomaly requiring intervention
            patch: Code patch to be applied
            risk_score: Risk assessment score (0.0-1.0)
            impact_estimate: Human-readable impact description
            timeout_seconds: Seconds to wait before auto-reject (default: 2 hours)

        Returns:
            Dict with approval result:
            - approved: bool
            - approval_id: str
            - approver: str | None
            - approved_at: datetime | None
            - rejection_reason: str | None
            - notes: str | None
            - status: ApprovalStatus
        """
        approval_id = str(uuid4())
        requested_at = datetime.utcnow()

        # Create approval request
        request = ApprovalRequest(
            approval_id=approval_id,
            anomaly_id=anomaly_id,
            patch=patch,
            risk_score=risk_score,
            impact_estimate=impact_estimate,
            requested_at=requested_at,
            timeout_seconds=timeout_seconds,
        )

        async with self._lock:
            self.pending_requests[approval_id] = request
            self.approval_events[approval_id] = asyncio.Event()

        # Update metrics
        self.approval_requests_total.labels(status="pending").inc()
        self.approval_pending_gauge.inc()
        self.high_risk_patches_total.inc()

        logger.warning(
            f"🚨 High-risk patch approval requested: {approval_id} "
            f"(anomaly: {anomaly_id}, risk: {risk_score:.2f})"
        )

        # Send notifications
        await self._send_notifications(request)

        # Wait for approval (with timeout)
        try:
            result = await self._wait_for_decision(approval_id, timeout_seconds)
            return result
        finally:
            # Cleanup
            async with self._lock:
                if approval_id in self.approval_events:
                    del self.approval_events[approval_id]

    async def approve(
        self, approval_id: str, approver: str, notes: str | None = None
    ) -> bool:
        """Approve pending request.

        Args:
            approval_id: Request to approve
            approver: Name/ID of approver
            notes: Optional approval notes

        Returns:
            True if approved successfully, False if request not found/expired
        """
        async with self._lock:
            request = self.pending_requests.get(approval_id)

            if not request:
                logger.error(f"Approval request not found: {approval_id}")
                return False

            if request.status != ApprovalStatus.PENDING:
                logger.error(
                    f"Approval request already resolved: {approval_id} (status: {request.status})"
                )
                return False

            if request.is_expired:
                request.status = ApprovalStatus.EXPIRED
                self._update_metrics_on_decision(request)
                logger.warning(f"Approval request expired: {approval_id}")
                return False

            # Approve
            request.status = ApprovalStatus.APPROVED
            request.approved_by = approver
            request.approved_at = datetime.utcnow()
            request.notes = notes

            # Update metrics
            self._update_metrics_on_decision(request)

            logger.info(
                f"✅ Patch approved: {approval_id} by {approver} "
                f"(anomaly: {request.anomaly_id})"
            )

            # Log to audit trail
            if self.audit_logger:
                await self._log_approval_decision(request)

            # Notify waiting coroutine
            if approval_id in self.approval_events:
                self.approval_events[approval_id].set()

            return True

    async def reject(
        self, approval_id: str, approver: str, reason: str, notes: str | None = None
    ) -> bool:
        """Reject pending request.

        Args:
            approval_id: Request to reject
            approver: Name/ID of person rejecting
            reason: Reason for rejection
            notes: Optional additional notes

        Returns:
            True if rejected successfully, False if request not found
        """
        async with self._lock:
            request = self.pending_requests.get(approval_id)

            if not request:
                logger.error(f"Approval request not found: {approval_id}")
                return False

            if request.status != ApprovalStatus.PENDING:
                logger.error(
                    f"Approval request already resolved: {approval_id} (status: {request.status})"
                )
                return False

            # Reject
            request.status = ApprovalStatus.REJECTED
            request.approved_by = approver  # Person who rejected
            request.approved_at = datetime.utcnow()
            request.rejection_reason = reason
            request.notes = notes

            # Update metrics
            self._update_metrics_on_decision(request)

            logger.warning(
                f"❌ Patch rejected: {approval_id} by {approver} " f"(reason: {reason})"
            )

            # Log to audit trail
            if self.audit_logger:
                await self._log_approval_decision(request)

            # Notify waiting coroutine
            if approval_id in self.approval_events:
                self.approval_events[approval_id].set()

            return True

    async def cancel(self, approval_id: str) -> bool:
        """Cancel pending approval request.

        Args:
            approval_id: Request to cancel

        Returns:
            True if cancelled, False if not found
        """
        async with self._lock:
            request = self.pending_requests.get(approval_id)

            if not request:
                return False

            if request.status != ApprovalStatus.PENDING:
                return False

            request.status = ApprovalStatus.CANCELLED
            self._update_metrics_on_decision(request)

            logger.info(f"Approval request cancelled: {approval_id}")

            # Notify waiting coroutine
            if approval_id in self.approval_events:
                self.approval_events[approval_id].set()

            return True

    async def get_pending_requests(self) -> list[dict[str, Any]]:
        """Get all pending approval requests.

        Returns:
            List of pending request summaries
        """
        async with self._lock:
            pending = []
            for request in self.pending_requests.values():
                if request.status == ApprovalStatus.PENDING and not request.is_expired:
                    pending.append(
                        {
                            "approval_id": request.approval_id,
                            "anomaly_id": request.anomaly_id,
                            "risk_score": request.risk_score,
                            "impact_estimate": request.impact_estimate,
                            "requested_at": request.requested_at.isoformat(),
                            "remaining_seconds": request.remaining_seconds,
                            "patch_preview": request.patch[:200] + "..."
                            if len(request.patch) > 200
                            else request.patch,
                        }
                    )
            return pending

    async def get_request_status(self, approval_id: str) -> dict[str, Any] | None:
        """Get status of specific approval request.

        Args:
            approval_id: Request to query

        Returns:
            Request status dict or None if not found
        """
        async with self._lock:
            request = self.pending_requests.get(approval_id)

            if not request:
                return None

            return {
                "approval_id": request.approval_id,
                "anomaly_id": request.anomaly_id,
                "status": request.status.value,
                "risk_score": request.risk_score,
                "impact_estimate": request.impact_estimate,
                "requested_at": request.requested_at.isoformat(),
                "approved_by": request.approved_by,
                "approved_at": request.approved_at.isoformat()
                if request.approved_at
                else None,
                "rejection_reason": request.rejection_reason,
                "notes": request.notes,
                "is_expired": request.is_expired,
                "remaining_seconds": request.remaining_seconds,
            }

    async def cleanup_old_requests(self, max_age_hours: int = 24) -> int:
        """Remove old completed/expired requests from memory.

        Args:
            max_age_hours: Remove requests older than this (default: 24h)

        Returns:
            Number of requests cleaned up
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed = 0

        async with self._lock:
            to_remove = []
            for approval_id, request in self.pending_requests.items():
                if (
                    request.status != ApprovalStatus.PENDING
                    and request.requested_at < cutoff
                ):
                    to_remove.append(approval_id)

            for approval_id in to_remove:
                del self.pending_requests[approval_id]
                removed += 1

        if removed > 0:
            logger.debug(f"Cleaned up {removed} old approval requests")

        return removed

    async def _wait_for_decision(
        self, approval_id: str, timeout_seconds: int
    ) -> dict[str, Any]:
        """Wait for approval decision or timeout.

        Args:
            approval_id: Request to wait for
            timeout_seconds: Max seconds to wait

        Returns:
            Approval result dict
        """
        event = self.approval_events.get(approval_id)
        if not event:
            raise RuntimeError(f"No event found for approval {approval_id}")

        try:
            # Wait for event or timeout
            await asyncio.wait_for(event.wait(), timeout=timeout_seconds)

            # Get final status
            async with self._lock:
                request = self.pending_requests.get(approval_id)
                if not request:
                    raise RuntimeError(f"Request disappeared: {approval_id}")

                return self._build_result(request)

        except asyncio.TimeoutError:
            # Timeout - auto-reject
            async with self._lock:
                request = self.pending_requests.get(approval_id)
                if request and request.status == ApprovalStatus.PENDING:
                    request.status = ApprovalStatus.EXPIRED
                    self._update_metrics_on_decision(request)

                    logger.warning(
                        f"⏱️  Approval request expired (timeout): {approval_id}"
                    )

                    # Log to audit trail
                    if self.audit_logger:
                        await self._log_approval_decision(request)

                return self._build_result(request)

    async def _send_notifications(self, request: ApprovalRequest) -> None:
        """Send approval notifications via Slack/Email.

        Args:
            request: Approval request to notify about
        """
        # Slack notification
        if self.slack_notifier:
            try:
                await self._send_slack_notification(request)
            except Exception as e:
                logger.error(f"Failed to send Slack notification: {e}")

        # Email notification
        if self.email_notifier:
            try:
                await self._send_email_notification(request)
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")

    async def _send_slack_notification(self, request: ApprovalRequest) -> None:
        """Send Slack notification for approval request.

        Args:
            request: Request to notify about
        """
        message = f"""
🚨 **High-Risk Patch Approval Required**

**Approval ID**: `{request.approval_id}`
**Anomaly ID**: `{request.anomaly_id}`
**Risk Score**: {request.risk_score:.2f} / 1.0
**Impact**: {request.impact_estimate}

**Patch Preview**:
```
{request.patch[:500]}{'...' if len(request.patch) > 500 else ''}
```

**Actions**:
- ✅ Approve: `/penelope approve {request.approval_id}`
- ❌ Reject: `/penelope reject {request.approval_id} <reason>`
- 🔍 Details: https://penelope.vertice.ai/approval/{request.approval_id}

**Timeout**: {request.timeout_seconds // 60} minutes (auto-reject after)
        """.strip()

        # Call Slack notifier (implementation depends on client)
        await self.slack_notifier.send_message(
            channel="#penelope-approvals", message=message
        )

    async def _send_email_notification(self, request: ApprovalRequest) -> None:
        """Send email notification for approval request.

        Args:
            request: Request to notify about
        """
        subject = f"PENELOPE: High-Risk Patch Approval Required ({request.approval_id})"

        body = f"""
High-risk patch requires human approval.

Approval ID: {request.approval_id}
Anomaly ID: {request.anomaly_id}
Risk Score: {request.risk_score:.2f} / 1.0
Impact: {request.impact_estimate}

Patch Preview:
{request.patch[:1000]}

Review and approve/reject at:
https://penelope.vertice.ai/approval/{request.approval_id}

Timeout: {request.timeout_seconds // 60} minutes
        """.strip()

        # Call email notifier (implementation depends on client)
        await self.email_notifier.send_email(
            to="ops-team@vertice.ai", subject=subject, body=body
        )

    async def _log_approval_decision(self, request: ApprovalRequest) -> None:
        """Log approval decision to audit trail.

        Args:
            request: Request with final decision
        """
        if not self.audit_logger:
            return

        # Log to generic audit logger
        await self.audit_logger.log(
            event_type="approval_decision",
            action=request.status.value,
            resource=f"patch_approval:{request.approval_id}",
            details={
                "anomaly_id": request.anomaly_id,
                "risk_score": request.risk_score,
                "approved_by": request.approved_by,
                "rejection_reason": request.rejection_reason,
                "notes": request.notes,
            },
            success=request.status == ApprovalStatus.APPROVED,
            severity="warning" if request.status == ApprovalStatus.APPROVED else "info",
        )

    def _update_metrics_on_decision(self, request: ApprovalRequest) -> None:
        """Update Prometheus metrics when decision is made.

        Args:
            request: Request with final status
        """
        self.approval_requests_total.labels(status=request.status.value).inc()
        self.approval_pending_gauge.dec()

        if request.approved_at:
            response_time = (request.approved_at - request.requested_at).total_seconds()
            self.approval_response_time.observe(response_time)

    def _build_result(self, request: ApprovalRequest) -> dict[str, Any]:
        """Build approval result dict.

        Args:
            request: Request to build result from

        Returns:
            Result dictionary
        """
        return {
            "approved": request.status == ApprovalStatus.APPROVED,
            "approval_id": request.approval_id,
            "approver": request.approved_by,
            "approved_at": request.approved_at.isoformat()
            if request.approved_at
            else None,
            "rejection_reason": request.rejection_reason,
            "notes": request.notes,
            "status": request.status.value,
        }
