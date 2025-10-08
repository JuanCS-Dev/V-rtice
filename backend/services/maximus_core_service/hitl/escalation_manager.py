"""
HITL Escalation Manager

Manages escalation of decisions to higher authority based on:
- SLA timeout
- Risk level
- Multiple rejections
- Explicit operator escalation

Escalation Chain:
    soc_operator → soc_supervisor → security_manager → ciso

Notifications:
- Email for all escalations
- SMS for critical escalations
- Slack/Teams for team awareness

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .base import (
    DecisionStatus,
    EscalationConfig,
    HITLDecision,
    RiskLevel,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Escalation Types
# ============================================================================


class EscalationType(Enum):
    """Type of escalation."""

    TIMEOUT = "timeout"  # SLA timeout
    HIGH_RISK = "high_risk"  # Critical/High risk decision
    MULTIPLE_REJECTIONS = "multiple_rejections"  # Rejected multiple times
    OPERATOR_REQUEST = "operator_request"  # Explicit operator escalation
    STALE_DECISION = "stale_decision"  # Decision pending too long
    SYSTEM_OVERRIDE = "system_override"  # System-initiated override


# ============================================================================
# Escalation Data Classes
# ============================================================================


@dataclass
class EscalationRule:
    """
    Rule for when to escalate a decision.
    """

    # Rule identifier
    rule_id: str
    rule_name: str
    escalation_type: EscalationType

    # Trigger conditions
    risk_levels: list[RiskLevel] = field(default_factory=list)  # Empty = all levels
    max_rejections: int = 2
    timeout_threshold: timedelta | None = None

    # Escalation target
    target_role: str = "soc_supervisor"

    # Notification settings
    send_email: bool = True
    send_sms: bool = False
    send_slack: bool = True

    # Rule priority (higher = more important)
    priority: int = 0

    # Active flag
    active: bool = True

    def matches(self, decision: HITLDecision) -> bool:
        """
        Check if rule matches decision.

        Args:
            decision: Decision to check

        Returns:
            True if rule matches
        """
        if not self.active:
            return False

        # Check risk level filter
        if self.risk_levels and decision.risk_level not in self.risk_levels:
            return False

        # Type-specific checks
        if self.escalation_type == EscalationType.TIMEOUT:
            return decision.is_overdue()

        if self.escalation_type == EscalationType.HIGH_RISK:
            return decision.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        if self.escalation_type == EscalationType.MULTIPLE_REJECTIONS:
            rejection_count = decision.metadata.get("rejection_count", 0)
            return rejection_count >= self.max_rejections

        if self.escalation_type == EscalationType.STALE_DECISION:
            if self.timeout_threshold:
                age = decision.get_age()
                return age > self.timeout_threshold
            return False

        return False


@dataclass
class EscalationEvent:
    """
    Record of an escalation event.
    """

    # Event details
    event_id: str
    decision_id: str
    escalation_type: EscalationType
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Escalation details
    from_role: str = ""
    to_role: str = ""
    reason: str = ""

    # Triggered rule
    rule_id: str | None = None

    # Notification status
    email_sent: bool = False
    sms_sent: bool = False
    slack_sent: bool = False

    # Metadata
    metadata: dict[str, any] = field(default_factory=dict)


# ============================================================================
# Escalation Manager
# ============================================================================


class EscalationManager:
    """
    Manages decision escalation to higher authority.

    Monitors decisions for escalation triggers and automatically escalates
    based on configured rules.
    """

    # Default escalation chain
    DEFAULT_CHAIN = [
        "soc_operator",
        "soc_supervisor",
        "security_manager",
        "ciso",
        "ceo",
    ]

    def __init__(self, config: EscalationConfig | None = None):
        """
        Initialize escalation manager.

        Args:
            config: Escalation configuration
        """
        self.config = config or EscalationConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Escalation rules
        self.rules: list[EscalationRule] = []
        self._initialize_default_rules()

        # Escalation history
        self.escalation_history: list[EscalationEvent] = []

        # Notification handlers
        self._notification_handlers: dict[str, Callable] = {}

        # Metrics
        self.metrics = {
            "total_escalations": 0,
            "timeout_escalations": 0,
            "risk_escalations": 0,
            "rejection_escalations": 0,
            "operator_escalations": 0,
        }

        self.logger.info("Escalation Manager initialized")

    def _initialize_default_rules(self):
        """Initialize default escalation rules."""
        # Rule 1: Timeout escalation
        self.rules.append(
            EscalationRule(
                rule_id="timeout_escalation",
                rule_name="SLA Timeout Escalation",
                escalation_type=EscalationType.TIMEOUT,
                target_role=self.config.low_risk_escalation,
                send_email=True,
                send_slack=True,
                priority=100,
            )
        )

        # Rule 2: Critical risk escalation
        self.rules.append(
            EscalationRule(
                rule_id="critical_risk_escalation",
                rule_name="Critical Risk Escalation",
                escalation_type=EscalationType.HIGH_RISK,
                risk_levels=[RiskLevel.CRITICAL],
                target_role=self.config.critical_risk_escalation,
                send_email=True,
                send_sms=True,
                send_slack=True,
                priority=200,
            )
        )

        # Rule 3: High risk escalation
        self.rules.append(
            EscalationRule(
                rule_id="high_risk_escalation",
                rule_name="High Risk Escalation",
                escalation_type=EscalationType.HIGH_RISK,
                risk_levels=[RiskLevel.HIGH],
                target_role=self.config.high_risk_escalation,
                send_email=True,
                send_slack=True,
                priority=150,
            )
        )

        # Rule 4: Multiple rejections escalation
        self.rules.append(
            EscalationRule(
                rule_id="multiple_rejections",
                rule_name="Multiple Rejections Escalation",
                escalation_type=EscalationType.MULTIPLE_REJECTIONS,
                max_rejections=self.config.rejection_threshold,
                target_role="security_manager",
                send_email=True,
                send_slack=True,
                priority=120,
            )
        )

        self.logger.info(f"Initialized {len(self.rules)} default escalation rules")

    def add_rule(self, rule: EscalationRule):
        """Add custom escalation rule."""
        self.rules.append(rule)
        # Sort by priority (descending)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.info(f"Added escalation rule: {rule.rule_name}")

    def check_for_escalation(self, decision: HITLDecision) -> EscalationRule | None:
        """
        Check if decision should be escalated.

        Args:
            decision: Decision to check

        Returns:
            Matching escalation rule, or None
        """
        if not self.config.enabled:
            return None

        # Check rules in priority order
        for rule in self.rules:
            if rule.matches(decision):
                self.logger.info(f"Escalation rule matched: {rule.rule_name} (decision={decision.decision_id})")
                return rule

        return None

    def escalate_decision(
        self,
        decision: HITLDecision,
        escalation_type: EscalationType,
        reason: str,
        target_role: str | None = None,
        triggered_rule: EscalationRule | None = None,
    ) -> EscalationEvent:
        """
        Escalate decision to higher authority.

        Args:
            decision: Decision to escalate
            escalation_type: Type of escalation
            reason: Escalation reason
            target_role: Target role (auto-determined if not provided)
            triggered_rule: Rule that triggered escalation

        Returns:
            EscalationEvent record
        """
        # Determine target role
        if target_role is None:
            if triggered_rule:
                target_role = triggered_rule.target_role
            else:
                target_role = self.config.get_escalation_target(decision.risk_level)

        # Get current role
        from_role = decision.assigned_operator or "unassigned"

        # Create escalation event
        event = EscalationEvent(
            event_id=f"esc_{datetime.utcnow().timestamp()}",
            decision_id=decision.decision_id,
            escalation_type=escalation_type,
            from_role=from_role,
            to_role=target_role,
            reason=reason,
            rule_id=triggered_rule.rule_id if triggered_rule else None,
        )

        # Update decision
        decision.status = DecisionStatus.ESCALATED
        decision.escalated = True
        decision.escalated_to = target_role
        decision.escalated_at = datetime.utcnow()
        decision.escalation_reason = reason

        # Send notifications
        if triggered_rule:
            self._send_notifications(decision, event, triggered_rule)
        else:
            self._send_notifications(decision, event)

        # Record event
        self.escalation_history.append(event)

        # Update metrics
        self.metrics["total_escalations"] += 1
        metric_key = f"{escalation_type.value}_escalations"
        if metric_key in self.metrics:
            self.metrics[metric_key] += 1

        self.logger.info(
            f"Decision escalated: {decision.decision_id} → {target_role} "
            f"(type={escalation_type.value}, reason={reason})"
        )

        return event

    def _send_notifications(
        self,
        decision: HITLDecision,
        event: EscalationEvent,
        rule: EscalationRule | None = None,
    ):
        """Send escalation notifications."""
        # Determine which notifications to send
        send_email = rule.send_email if rule else self.config.send_email
        send_sms = rule.send_sms if rule else self.config.send_sms
        send_slack = rule.send_slack if rule else self.config.send_slack

        # Email notification
        if send_email:
            event.email_sent = self._send_email_notification(decision, event)

        # SMS notification (for critical only)
        if send_sms and decision.risk_level == RiskLevel.CRITICAL:
            event.sms_sent = self._send_sms_notification(decision, event)

        # Slack notification
        if send_slack:
            event.slack_sent = self._send_slack_notification(decision, event)

    def _send_email_notification(self, decision: HITLDecision, event: EscalationEvent) -> bool:
        """Send email notification."""
        handler = self._notification_handlers.get("email")
        if handler:
            try:
                handler(decision, event)
                self.logger.info(f"Email notification sent for escalation {event.event_id}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to send email notification: {e}")
                return False
        else:
            self.logger.debug("No email handler registered")
            return False

    def _send_sms_notification(self, decision: HITLDecision, event: EscalationEvent) -> bool:
        """Send SMS notification."""
        handler = self._notification_handlers.get("sms")
        if handler:
            try:
                handler(decision, event)
                self.logger.info(f"SMS notification sent for escalation {event.event_id}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to send SMS notification: {e}")
                return False
        else:
            self.logger.debug("No SMS handler registered")
            return False

    def _send_slack_notification(self, decision: HITLDecision, event: EscalationEvent) -> bool:
        """Send Slack notification."""
        handler = self._notification_handlers.get("slack")
        if handler:
            try:
                handler(decision, event)
                self.logger.info(f"Slack notification sent for escalation {event.event_id}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to send Slack notification: {e}")
                return False
        else:
            self.logger.debug("No Slack handler registered")
            return False

    def register_notification_handler(self, channel: str, handler: Callable):
        """
        Register notification handler.

        Args:
            channel: Notification channel ("email", "sms", "slack")
            handler: Handler function (decision, event) -> None
        """
        self._notification_handlers[channel] = handler
        self.logger.info(f"Registered notification handler for {channel}")

    def get_escalation_target(self, current_role: str, decision: HITLDecision) -> str:
        """
        Get next escalation target in chain.

        Args:
            current_role: Current assigned role
            decision: Decision to escalate

        Returns:
            Next role in escalation chain
        """
        # Use risk-based target if critical/high risk
        if decision.risk_level == RiskLevel.CRITICAL:
            return self.config.critical_risk_escalation
        if decision.risk_level == RiskLevel.HIGH:
            return self.config.high_risk_escalation

        # Otherwise, use escalation chain
        chain = self.config.sla_config.escalation_chain or self.DEFAULT_CHAIN

        try:
            current_index = chain.index(current_role)
            if current_index < len(chain) - 1:
                return chain[current_index + 1]
            # Already at top of chain
            return chain[-1]
        except ValueError:
            # Current role not in chain, use default
            return self.config.get_escalation_target(decision.risk_level)

    def get_metrics(self) -> dict[str, any]:
        """Get escalation metrics."""
        return {
            **self.metrics,
            "escalation_rate": (
                self.metrics["total_escalations"] / len(self.escalation_history) if self.escalation_history else 0.0
            ),
        }

    def get_escalation_history(self, decision_id: str | None = None, limit: int = 100) -> list[EscalationEvent]:
        """
        Get escalation history.

        Args:
            decision_id: Filter by decision ID (optional)
            limit: Maximum number of events to return

        Returns:
            List of escalation events
        """
        if decision_id:
            events = [e for e in self.escalation_history if e.decision_id == decision_id]
        else:
            events = self.escalation_history

        # Return most recent first
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
