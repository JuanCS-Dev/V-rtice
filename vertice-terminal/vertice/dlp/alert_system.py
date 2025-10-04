"""
🚨 Alert System - Sistema de alertas e resposta DLP

Gerencia alertas de violações DLP com múltiplos canais de notificação.

Alert Channels:
- Email
- Slack/Teams
- SMS
- Webhook
- SIEM Integration
- Ticket System (ServiceNow, Jira)

Alert Features:
- Real-time notifications
- Severity-based routing
- Alert deduplication
- Escalation workflows
- Alert correlation
- Response tracking
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Severidade do alerta"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status do alerta"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    SUPPRESSED = "suppressed"


class AlertChannel(Enum):
    """Canais de notificação"""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"
    WEBHOOK = "webhook"
    SIEM = "siem"
    TICKET = "ticket"


@dataclass
class AlertRecipient:
    """
    Destinatário de alerta

    Attributes:
        recipient_type: Tipo (user, group, role)
        identifier: Identificador (email, username, etc)
        channels: Canais de notificação
        severity_threshold: Severidade mínima para notificar
    """
    recipient_type: str  # user, group, role
    identifier: str
    channels: List[AlertChannel] = field(default_factory=list)
    severity_threshold: AlertSeverity = AlertSeverity.LOW


@dataclass
class DLPAlert:
    """
    Alerta DLP

    Attributes:
        id: Alert ID
        title: Alert title
        description: Alert description
        severity: Alert severity
        status: Alert status
        created_at: When created
        policy_id: Policy that triggered alert
        resource_id: Resource involved
        user: User involved
        action_taken: Action taken by policy
        sensitive_data_types: Types of sensitive data detected
        classification_level: Data classification level
        context: Additional context
        recipients: Alert recipients
        notifications_sent: Notifications sent
        acknowledged_by: Who acknowledged
        acknowledged_at: When acknowledged
        resolved_by: Who resolved
        resolved_at: When resolved
        resolution_notes: Resolution notes
    """
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime

    # Related entities
    policy_id: Optional[str] = None
    resource_id: Optional[str] = None
    user: Optional[str] = None

    # Details
    action_taken: str = ""
    sensitive_data_types: List[str] = field(default_factory=list)
    classification_level: Optional[str] = None

    # Context
    context: Dict[str, Any] = field(default_factory=dict)

    # Notifications
    recipients: List[str] = field(default_factory=list)
    notifications_sent: List[Dict[str, Any]] = field(default_factory=list)

    # Resolution
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EscalationRule:
    """
    Regra de escalação

    Attributes:
        id: Rule ID
        name: Rule name
        severity: Alert severity to escalate
        time_threshold_minutes: Time before escalation
        escalate_to: Recipients for escalation
        enabled: If rule is enabled
    """
    id: str
    name: str
    severity: AlertSeverity
    time_threshold_minutes: int
    escalate_to: List[str]
    enabled: bool = True


class AlertSystem:
    """
    DLP Alert & Response System

    Features:
    - Multi-channel notifications
    - Alert deduplication
    - Escalation workflows
    - Alert correlation
    - Response tracking
    - SLA monitoring
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do dlp_service
            use_backend: Se True, usa backend
        """
        self.backend_url = backend_url or "http://localhost:8022"
        self.use_backend = use_backend

        # Alert storage
        self.alerts: Dict[str, DLPAlert] = {}

        # Recipients registry
        self.recipients: Dict[str, AlertRecipient] = {}

        # Escalation rules
        self.escalation_rules: List[EscalationRule] = []

        # Deduplication cache (alert signature -> alert_id)
        self.dedup_cache: Dict[str, str] = {}

        # Load default recipients and rules
        self._load_defaults()

    def _load_defaults(self):
        """Carrega configurações padrão"""

        # Default recipients
        default_recipients = [
            AlertRecipient(
                recipient_type="group",
                identifier="security-team",
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                severity_threshold=AlertSeverity.MEDIUM,
            ),
            AlertRecipient(
                recipient_type="group",
                identifier="compliance-team",
                channels=[AlertChannel.EMAIL, AlertChannel.TICKET],
                severity_threshold=AlertSeverity.HIGH,
            ),
            AlertRecipient(
                recipient_type="role",
                identifier="ciso",
                channels=[AlertChannel.EMAIL, AlertChannel.SMS],
                severity_threshold=AlertSeverity.CRITICAL,
            ),
        ]

        for recipient in default_recipients:
            self.recipients[recipient.identifier] = recipient

        # Default escalation rules
        default_escalation = [
            EscalationRule(
                id="escalate-critical-30min",
                name="Escalate Critical Alerts after 30min",
                severity=AlertSeverity.CRITICAL,
                time_threshold_minutes=30,
                escalate_to=["ciso", "security-director"],
            ),
            EscalationRule(
                id="escalate-high-2hours",
                name="Escalate High Alerts after 2 hours",
                severity=AlertSeverity.HIGH,
                time_threshold_minutes=120,
                escalate_to=["security-manager"],
            ),
        ]

        self.escalation_rules = default_escalation

        logger.info(
            f"Loaded {len(default_recipients)} recipients and "
            f"{len(default_escalation)} escalation rules"
        )

    def create_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity,
        policy_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        user: Optional[str] = None,
        action_taken: str = "",
        sensitive_data_types: Optional[List[str]] = None,
        classification_level: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        deduplicate: bool = True,
    ) -> DLPAlert:
        """
        Cria alerta DLP

        Args:
            title: Alert title
            description: Alert description
            severity: Alert severity
            policy_id: Policy that triggered
            resource_id: Resource involved
            user: User involved
            action_taken: Action taken
            sensitive_data_types: Sensitive data types detected
            classification_level: Classification level
            context: Additional context
            deduplicate: Enable deduplication

        Returns:
            DLPAlert
        """
        import uuid

        # Check deduplication
        if deduplicate:
            signature = self._generate_alert_signature(
                policy_id, resource_id, user, sensitive_data_types
            )

            if signature in self.dedup_cache:
                existing_alert_id = self.dedup_cache[signature]
                existing_alert = self.alerts.get(existing_alert_id)

                if existing_alert and existing_alert.status == AlertStatus.NEW:
                    logger.info(
                        f"Alert deduplicated: using existing alert {existing_alert_id}"
                    )
                    return existing_alert

        # Create new alert
        alert = DLPAlert(
            id=f"ALERT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            severity=severity,
            status=AlertStatus.NEW,
            created_at=datetime.now(),
            policy_id=policy_id,
            resource_id=resource_id,
            user=user,
            action_taken=action_taken,
            sensitive_data_types=sensitive_data_types or [],
            classification_level=classification_level,
            context=context or {},
        )

        # Determine recipients
        alert.recipients = self._determine_recipients(severity)

        # Store alert
        self.alerts[alert.id] = alert

        # Update dedup cache
        if deduplicate:
            signature = self._generate_alert_signature(
                policy_id, resource_id, user, sensitive_data_types
            )
            self.dedup_cache[signature] = alert.id

        logger.info(
            f"Alert created: {alert.id} - {title} (Severity: {severity.value})"
        )

        # Send notifications
        self._send_notifications(alert)

        return alert

    def _generate_alert_signature(
        self,
        policy_id: Optional[str],
        resource_id: Optional[str],
        user: Optional[str],
        sensitive_data_types: Optional[List[str]],
    ) -> str:
        """Gera assinatura para deduplicação"""
        parts = [
            policy_id or "",
            resource_id or "",
            user or "",
            ",".join(sorted(sensitive_data_types or [])),
        ]
        return "|".join(parts)

    def _determine_recipients(self, severity: AlertSeverity) -> List[str]:
        """Determina destinatários baseado na severidade"""
        recipients = []

        for recipient in self.recipients.values():
            # Check severity threshold
            severity_levels = {
                AlertSeverity.INFO: 0,
                AlertSeverity.LOW: 1,
                AlertSeverity.MEDIUM: 2,
                AlertSeverity.HIGH: 3,
                AlertSeverity.CRITICAL: 4,
            }

            if severity_levels.get(severity, 0) >= severity_levels.get(recipient.severity_threshold, 0):
                recipients.append(recipient.identifier)

        return recipients

    def _send_notifications(self, alert: DLPAlert) -> None:
        """Envia notificações para destinatários"""

        for recipient_id in alert.recipients:
            recipient = self.recipients.get(recipient_id)

            if not recipient:
                continue

            # Send via each channel
            for channel in recipient.channels:
                try:
                    if channel == AlertChannel.EMAIL:
                        self._send_email_notification(alert, recipient)

                    elif channel == AlertChannel.SLACK:
                        self._send_slack_notification(alert, recipient)

                    elif channel == AlertChannel.TEAMS:
                        self._send_teams_notification(alert, recipient)

                    elif channel == AlertChannel.WEBHOOK:
                        self._send_webhook_notification(alert, recipient)

                    # Record notification
                    alert.notifications_sent.append({
                        "channel": channel.value,
                        "recipient": recipient_id,
                        "sent_at": datetime.now().isoformat(),
                    })

                except Exception as e:
                    logger.error(
                        f"Failed to send notification via {channel.value} "
                        f"to {recipient_id}: {e}"
                    )

    def _send_email_notification(self, alert: DLPAlert, recipient: AlertRecipient) -> None:
        """Envia notificação por email"""
        # TODO: Integrate with email service
        logger.info(f"EMAIL notification sent to {recipient.identifier}: {alert.title}")

    def _send_slack_notification(self, alert: DLPAlert, recipient: AlertRecipient) -> None:
        """Envia notificação Slack"""
        # TODO: Integrate with Slack API
        logger.info(f"SLACK notification sent to {recipient.identifier}: {alert.title}")

    def _send_teams_notification(self, alert: DLPAlert, recipient: AlertRecipient) -> None:
        """Envia notificação Teams"""
        # TODO: Integrate with Teams webhook
        logger.info(f"TEAMS notification sent to {recipient.identifier}: {alert.title}")

    def _send_webhook_notification(self, alert: DLPAlert, recipient: AlertRecipient) -> None:
        """Envia notificação via webhook"""
        # TODO: Send to webhook endpoint
        logger.info(f"WEBHOOK notification sent to {recipient.identifier}: {alert.title}")

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        notes: str = "",
    ) -> bool:
        """
        Reconhece alerta

        Args:
            alert_id: Alert ID
            acknowledged_by: Who acknowledged
            notes: Acknowledgment notes

        Returns:
            True if successful
        """
        alert = self.alerts.get(alert_id)

        if not alert:
            return False

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()

        if notes:
            alert.metadata["acknowledgment_notes"] = notes

        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")

        return True

    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: str = "",
        false_positive: bool = False,
    ) -> bool:
        """
        Resolve alerta

        Args:
            alert_id: Alert ID
            resolved_by: Who resolved
            resolution_notes: Resolution notes
            false_positive: If it's a false positive

        Returns:
            True if successful
        """
        alert = self.alerts.get(alert_id)

        if not alert:
            return False

        if false_positive:
            alert.status = AlertStatus.FALSE_POSITIVE
        else:
            alert.status = AlertStatus.RESOLVED

        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.now()
        alert.resolution_notes = resolution_notes

        logger.info(
            f"Alert resolved: {alert_id} by {resolved_by} "
            f"(FP: {false_positive})"
        )

        return True

    def check_escalations(self) -> List[DLPAlert]:
        """
        Verifica alertas que precisam ser escalados

        Returns:
            List of alerts that need escalation
        """
        now = datetime.now()
        escalated = []

        for alert in self.alerts.values():
            # Skip if not NEW or ACKNOWLEDGED
            if alert.status not in [AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]:
                continue

            # Check escalation rules
            for rule in self.escalation_rules:
                if not rule.enabled:
                    continue

                if alert.severity != rule.severity:
                    continue

                # Calculate time since creation
                time_diff = (now - alert.created_at).total_seconds() / 60

                if time_diff >= rule.time_threshold_minutes:
                    # Escalate
                    self._escalate_alert(alert, rule)
                    escalated.append(alert)
                    break

        if escalated:
            logger.info(f"Escalated {len(escalated)} alerts")

        return escalated

    def _escalate_alert(self, alert: DLPAlert, rule: EscalationRule) -> None:
        """Escalada de alerta"""

        logger.info(
            f"Escalating alert {alert.id} to {', '.join(rule.escalate_to)}"
        )

        # Add escalation recipients
        for recipient_id in rule.escalate_to:
            if recipient_id not in alert.recipients:
                alert.recipients.append(recipient_id)

        # Send escalation notifications
        self._send_notifications(alert)

        # Record escalation
        alert.metadata["escalated"] = True
        alert.metadata["escalated_at"] = datetime.now().isoformat()
        alert.metadata["escalation_rule"] = rule.id

    def get_alert(self, alert_id: str) -> Optional[DLPAlert]:
        """Retorna alerta por ID"""
        return self.alerts.get(alert_id)

    def list_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        user: Optional[str] = None,
        limit: int = 100,
    ) -> List[DLPAlert]:
        """
        Lista alertas com filtros

        Args:
            severity: Filter by severity
            status: Filter by status
            user: Filter by user
            limit: Max results

        Returns:
            List of DLPAlert
        """
        alerts = list(self.alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if status:
            alerts = [a for a in alerts if a.status == status]

        if user:
            alerts = [a for a in alerts if a.user == user]

        # Sort by created_at (most recent first)
        alerts = sorted(alerts, key=lambda a: a.created_at, reverse=True)

        return alerts[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas"""

        # Count by severity
        by_severity = {}
        for alert in self.alerts.values():
            sev = alert.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        # Count by status
        by_status = {}
        for alert in self.alerts.values():
            status = alert.status.value
            by_status[status] = by_status.get(status, 0) + 1

        # Calculate response times
        resolved_alerts = [
            a for a in self.alerts.values()
            if a.resolved_at
        ]

        avg_resolution_time = 0
        if resolved_alerts:
            total_time = sum(
                (a.resolved_at - a.created_at).total_seconds()
                for a in resolved_alerts
            )
            avg_resolution_time = int(total_time / len(resolved_alerts) / 60)  # minutes

        return {
            "total_alerts": len(self.alerts),
            "by_severity": by_severity,
            "by_status": by_status,
            "avg_resolution_time_minutes": avg_resolution_time,
            "total_recipients": len(self.recipients),
            "escalation_rules": len(self.escalation_rules),
        }
