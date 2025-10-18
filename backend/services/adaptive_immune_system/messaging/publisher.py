"""
RabbitMQ publishers for Adaptive Immune System.

Provides type-safe message publishing for APVs, remedies, wargame results,
and HITL notifications/decisions.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from .client import RabbitMQClient
from models.apv import APVDispatchMessage, APVStatusUpdate
from models.wargame import WargameReportMessage
from models.hitl import HITLNotificationMessage, HITLDecisionMessage, HITLStatusUpdate

logger = logging.getLogger(__name__)


class APVPublisher:
    """Publish APV dispatch messages (Oráculo → Eureka)."""

    def __init__(self, client: RabbitMQClient):
        """Initialize APV publisher."""
        self.client = client
        self.routing_key_prefix = "oraculo.apv"

    async def dispatch_apv(self, apv_message: APVDispatchMessage) -> None:
        """
        Dispatch APV to Eureka for vulnerability confirmation.

        Args:
            apv_message: APV dispatch message

        Raises:
            RuntimeError: If publish fails
        """
        try:
            # Determine routing key based on priority
            routing_key = f"{self.routing_key_prefix}.priority.{apv_message.priority}"
            if apv_message.priority <= 3:
                routing_key = f"{self.routing_key_prefix}.critical"

            # Serialize message
            message_body = apv_message.model_dump_json()

            # Publish with priority
            await self.client.publish(
                routing_key=routing_key,
                message_body=message_body,
                priority=11 - apv_message.priority,  # Invert priority (1=highest)
            )

            logger.info(
                f"✅ APV dispatched: {apv_message.apv_code} "
                f"(priority={apv_message.priority}, cve={apv_message.cve_id})"
            )

        except Exception as e:
            logger.error(f"Failed to dispatch APV {apv_message.apv_code}: {e}")
            raise


class RemedyStatusPublisher:
    """Publish remedy status updates (Eureka → Oráculo)."""

    def __init__(self, client: RabbitMQClient):
        """Initialize remedy status publisher."""
        self.client = client
        self.routing_key = "eureka.remedy.status"

    async def publish_status(self, status_update: APVStatusUpdate) -> None:
        """
        Publish APV status update back to Oráculo.

        Args:
            status_update: Status update message
        """
        try:
            message_body = status_update.model_dump_json()

            await self.client.publish(
                routing_key=self.routing_key,
                message_body=message_body,
                priority=5,
            )

            logger.info(
                f"✅ Status update published: {status_update.apv_code} → {status_update.status}"
            )

        except Exception as e:
            logger.error(f"Failed to publish status update: {e}")
            raise


class WargameReportPublisher:
    """Publish wargame reports (GitHub Actions → Eureka)."""

    def __init__(self, client: RabbitMQClient):
        """Initialize wargame report publisher."""
        self.client = client
        self.routing_key = "wargaming.results"

    async def publish_report(self, report: WargameReportMessage) -> None:
        """
        Publish wargaming validation report.

        Args:
            report: Wargame report message
        """
        try:
            message_body = report.model_dump_json()

            # Priority based on verdict
            priority = 8 if report.verdict == "success" else 5

            await self.client.publish(
                routing_key=f"{self.routing_key}.{report.verdict}",
                message_body=message_body,
                priority=priority,
            )

            logger.info(
                f"✅ Wargame report published: {report.run_code} → {report.verdict}"
            )

        except Exception as e:
            logger.error(f"Failed to publish wargame report: {e}")
            raise


class HITLNotificationPublisher:
    """Publish HITL notifications (System → HITL Console)."""

    def __init__(self, client: RabbitMQClient):
        """Initialize HITL notification publisher."""
        self.client = client
        self.routing_key_prefix = "hitl.notifications"

    async def publish_new_apv_notification(
        self,
        apv_id: str,
        apv_code: str,
        priority: int,
        cve_id: str,
        cve_title: str,
        severity: str,
        cvss_score: Optional[float],
        package_name: str,
        package_version: str,
        package_ecosystem: str,
        patch_strategy: str,
        patch_description: str,
        pr_number: Optional[int],
        pr_url: Optional[str],
        confirmation_confidence: float,
        false_positive_probability: float,
        wargame_verdict: str,
        wargame_confidence: float,
        wargame_run_url: Optional[str] = None,
        wargame_evidence: Optional[Dict[str, Any]] = None,
        affected_files: Optional[List[str]] = None,
        validation_warnings: Optional[List[str]] = None,
        requires_immediate_attention: bool = False,
        escalation_reason: Optional[str] = None,
    ) -> str:
        """
        Publish notification of new APV requiring human review.

        Called after wargaming completes to notify HITL console
        that an APV is ready for decision.

        Args:
            apv_id: APV unique identifier
            apv_code: APV code (e.g., "APV-2025-001")
            priority: Priority 1-10 (1=highest)
            cve_id: CVE identifier
            cve_title: CVE title/summary
            severity: Severity level
            cvss_score: CVSS score (0-10)
            package_name: Vulnerable package name
            package_version: Current package version
            package_ecosystem: Package ecosystem (npm, pip, etc)
            patch_strategy: Patch strategy used
            patch_description: Patch description
            pr_number: GitHub PR number
            pr_url: GitHub PR URL
            confirmation_confidence: Confirmation confidence (0-1)
            false_positive_probability: False positive probability (0-1)
            wargame_verdict: Wargame verdict (success/failure/inconclusive)
            wargame_confidence: Wargame confidence (0-1)
            wargame_run_url: GitHub Actions run URL
            wargame_evidence: Wargame evidence dict
            affected_files: List of affected files
            validation_warnings: List of validation warnings
            requires_immediate_attention: Urgency flag
            escalation_reason: Reason for escalation

        Returns:
            Message ID (UUID)

        Raises:
            RuntimeError: If publish fails
        """
        try:
            # Generate message ID
            message_id = str(uuid.uuid4())

            # Build notification message
            notification = HITLNotificationMessage(
                message_id=message_id,
                apv_id=apv_id,
                apv_code=apv_code,
                priority=priority,
                cve_id=cve_id,
                cve_title=cve_title,
                severity=severity,
                cvss_score=cvss_score,
                package_name=package_name,
                package_version=package_version,
                package_ecosystem=package_ecosystem,
                patch_strategy=patch_strategy,
                patch_description=patch_description,
                pr_number=pr_number,
                pr_url=pr_url,
                confirmation_confidence=confirmation_confidence,
                false_positive_probability=false_positive_probability,
                wargame_verdict=wargame_verdict,
                wargame_confidence=wargame_confidence,
                wargame_run_url=wargame_run_url,
                wargame_evidence=wargame_evidence or {},
                affected_files=affected_files or [],
                validation_warnings=validation_warnings or [],
                requires_immediate_attention=requires_immediate_attention,
                escalation_reason=escalation_reason,
            )

            # Determine routing key based on severity and urgency
            if requires_immediate_attention:
                routing_key = f"{self.routing_key_prefix}.urgent"
            elif severity in ("critical", "high"):
                routing_key = f"{self.routing_key_prefix}.{severity}"
            else:
                routing_key = f"{self.routing_key_prefix}.normal"

            # Serialize message
            message_body = notification.model_dump_json()

            # Determine message priority (RabbitMQ 0-10)
            msg_priority = 11 - priority  # Invert (APV priority 1 → RabbitMQ priority 10)
            if requires_immediate_attention:
                msg_priority = 10  # Maximum priority

            # Publish
            await self.client.publish(
                routing_key=routing_key,
                message_body=message_body,
                priority=msg_priority,
            )

            logger.info(
                f"✅ HITL notification published: {apv_code} "
                f"(severity={severity}, verdict={wargame_verdict}, msg_id={message_id})"
            )

            return message_id

        except Exception as e:
            logger.error(f"Failed to publish HITL notification for {apv_code}: {e}")
            raise

    async def publish_status_update(
        self,
        pending_reviews_count: int,
        reviews_completed_today: int,
        average_review_time_seconds: float,
        active_reviewers: int,
        decisions_last_hour: int,
        console_healthy: bool,
        database_healthy: bool,
        websocket_connections: int,
        critical_reviews_overdue: int = 0,
        high_priority_reviews_waiting: int = 0,
        alert_level: str = "normal",
        alert_message: Optional[str] = None,
    ) -> str:
        """
        Publish HITL system status update.

        Called periodically to monitor HITL console health and activity.

        Args:
            pending_reviews_count: Number of pending reviews
            reviews_completed_today: Reviews completed today
            average_review_time_seconds: Average review time
            active_reviewers: Number of active reviewers
            decisions_last_hour: Decisions made in last hour
            console_healthy: HITL console health status
            database_healthy: Database health status
            websocket_connections: Active WebSocket connections
            critical_reviews_overdue: Count of overdue critical reviews
            high_priority_reviews_waiting: High priority reviews waiting
            alert_level: Alert level (normal/warning/critical)
            alert_message: Alert message if any

        Returns:
            Message ID (UUID)
        """
        try:
            message_id = str(uuid.uuid4())

            status_update = HITLStatusUpdate(
                message_id=message_id,
                pending_reviews_count=pending_reviews_count,
                reviews_completed_today=reviews_completed_today,
                average_review_time_seconds=average_review_time_seconds,
                active_reviewers=active_reviewers,
                decisions_last_hour=decisions_last_hour,
                console_healthy=console_healthy,
                database_healthy=database_healthy,
                websocket_connections=websocket_connections,
                critical_reviews_overdue=critical_reviews_overdue,
                high_priority_reviews_waiting=high_priority_reviews_waiting,
                alert_level=alert_level,
                alert_message=alert_message,
            )

            routing_key = f"{self.routing_key_prefix}.status.{alert_level}"
            message_body = status_update.model_dump_json()

            await self.client.publish(
                routing_key=routing_key,
                message_body=message_body,
                priority=5,
            )

            logger.debug(f"✅ HITL status update published (alert_level={alert_level})")

            return message_id

        except Exception as e:
            logger.error(f"Failed to publish HITL status update: {e}")
            raise


class HITLDecisionPublisher:
    """Publish HITL decisions (HITL Console → System)."""

    def __init__(self, client: RabbitMQClient):
        """Initialize HITL decision publisher."""
        self.client = client
        self.routing_key_prefix = "hitl.decisions"

    async def publish_decision(
        self,
        apv_id: str,
        apv_code: str,
        decision: str,
        justification: str,
        confidence: float,
        reviewer_name: str,
        reviewer_email: str,
        decision_id: str,
        cve_id: str,
        severity: str,
        patch_strategy: str,
        pr_number: Optional[int],
        pr_url: Optional[str],
        action_type: str,
        action_target_pr: Optional[int] = None,
        action_comment: Optional[str] = None,
        action_assignees: Optional[List[str]] = None,
        action_labels: Optional[List[str]] = None,
        modifications: Optional[Dict[str, Any]] = None,
        requires_followup: bool = False,
        followup_reason: Optional[str] = None,
    ) -> str:
        """
        Publish human decision on APV.

        Called after human reviewer makes decision via HITL console.
        System consumes this message to execute the decision.

        Args:
            apv_id: APV unique identifier
            apv_code: APV code (e.g., "APV-2025-001")
            decision: Decision type (approve/reject/modify/escalate)
            justification: Human justification for decision
            confidence: Reviewer confidence (0-1)
            reviewer_name: Reviewer name
            reviewer_email: Reviewer email
            decision_id: Decision record ID
            cve_id: CVE identifier
            severity: Severity level
            patch_strategy: Patch strategy used
            pr_number: GitHub PR number
            pr_url: GitHub PR URL
            action_type: Action to execute (merge_pr/close_pr/request_changes/escalate_to_lead)
            action_target_pr: PR to act on
            action_comment: Comment to add to PR
            action_assignees: Users to assign
            action_labels: Labels to add
            modifications: Patch modifications (if decision=modify)
            requires_followup: Whether followup needed
            followup_reason: Reason for followup

        Returns:
            Message ID (UUID)

        Raises:
            RuntimeError: If publish fails
        """
        try:
            # Generate message ID
            message_id = str(uuid.uuid4())

            # Build decision message
            decision_msg = HITLDecisionMessage(
                message_id=message_id,
                apv_id=apv_id,
                apv_code=apv_code,
                decision=decision,
                justification=justification,
                confidence=confidence,
                reviewer_name=reviewer_name,
                reviewer_email=reviewer_email,
                decision_id=decision_id,
                cve_id=cve_id,
                severity=severity,
                patch_strategy=patch_strategy,
                pr_number=pr_number,
                pr_url=pr_url,
                action_type=action_type,
                action_target_pr=action_target_pr,
                action_comment=action_comment,
                action_assignees=action_assignees,
                action_labels=action_labels,
                modifications=modifications,
                requires_followup=requires_followup,
                followup_reason=followup_reason,
            )

            # Determine routing key based on decision type
            routing_key = f"{self.routing_key_prefix}.{decision}.{action_type}"

            # Serialize message
            message_body = decision_msg.model_dump_json()

            # Priority based on action urgency
            if action_type == "merge_pr":
                msg_priority = 8  # High priority for merges
            elif action_type == "escalate_to_lead":
                msg_priority = 9  # Higher priority for escalations
            else:
                msg_priority = 5  # Normal priority

            # Publish
            await self.client.publish(
                routing_key=routing_key,
                message_body=message_body,
                priority=msg_priority,
            )

            logger.info(
                f"✅ HITL decision published: {apv_code} → {decision} "
                f"(action={action_type}, reviewer={reviewer_name}, msg_id={message_id})"
            )

            return message_id

        except Exception as e:
            logger.error(f"Failed to publish HITL decision for {apv_code}: {e}")
            raise
