"""
Compliance Monitoring

Continuous compliance monitoring system. Monitors compliance status in real-time,
detects violations, sends alerts, and tracks metrics over time.

Features:
- Continuous compliance monitoring
- Real-time violation detection
- Automated alerting (critical violations, threshold breaches)
- Compliance metrics tracking
- Evidence expiration monitoring
- Remediation progress tracking
- Dashboard data generation

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging
import threading
import time
import uuid

from .base import (
    ComplianceConfig,
    ComplianceViolation,
    Evidence,
    RegulationType,
    ViolationSeverity,
)
from .compliance_engine import ComplianceEngine, ComplianceSnapshot
from .evidence_collector import EvidenceCollector
from .gap_analyzer import GapAnalyzer, RemediationPlan

logger = logging.getLogger(__name__)


@dataclass
class ComplianceAlert:
    """
    Compliance alert notification.
    """

    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str = ""  # violation, threshold_breach, evidence_expiring, remediation_overdue
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    title: str = ""
    message: str = ""
    regulation_type: Optional[RegulationType] = None
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, any] = field(default_factory=dict)

    def acknowledge(self, acknowledged_by: str):
        """Mark alert as acknowledged."""
        self.acknowledged = True
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = datetime.utcnow()


@dataclass
class MonitoringMetrics:
    """
    Compliance monitoring metrics snapshot.
    """

    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    overall_compliance_percentage: float = 0.0
    overall_score: float = 0.0
    compliance_by_regulation: Dict[str, float] = field(default_factory=dict)
    total_violations: int = 0
    critical_violations: int = 0
    high_violations: int = 0
    medium_violations: int = 0
    low_violations: int = 0
    total_evidence: int = 0
    expired_evidence: int = 0
    expiring_soon_evidence: int = 0  # Expiring in next 30 days
    remediation_plans_active: int = 0
    remediation_actions_overdue: int = 0
    compliance_trend: str = "stable"  # improving, stable, declining


class ComplianceMonitor:
    """
    Continuous compliance monitoring system.

    Monitors compliance status, detects violations, and sends alerts.
    """

    def __init__(
        self,
        compliance_engine: ComplianceEngine,
        evidence_collector: Optional[EvidenceCollector] = None,
        gap_analyzer: Optional[GapAnalyzer] = None,
        config: Optional[ComplianceConfig] = None,
    ):
        """
        Initialize compliance monitor.

        Args:
            compliance_engine: Compliance engine instance
            evidence_collector: Optional evidence collector
            gap_analyzer: Optional gap analyzer
            config: Compliance configuration
        """
        self.engine = compliance_engine
        self.evidence_collector = evidence_collector
        self.gap_analyzer = gap_analyzer
        self.config = config or ComplianceConfig()

        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._alerts: List[ComplianceAlert] = []
        self._metrics_history: List[MonitoringMetrics] = []
        self._alert_handlers: List[Callable[[ComplianceAlert], None]] = []

        logger.info("Compliance monitor initialized")

    def register_alert_handler(self, handler: Callable[[ComplianceAlert], None]):
        """
        Register alert handler callback.

        Args:
            handler: Function to call when alert is triggered
        """
        self._alert_handlers.append(handler)
        logger.info(f"Registered alert handler: {handler.__name__}")

    def start_monitoring(self, check_interval_seconds: int = 3600):
        """
        Start continuous compliance monitoring.

        Args:
            check_interval_seconds: Interval between checks (default 1 hour)
        """
        if self._monitoring:
            logger.warning("Monitoring already started")
            return

        self._monitoring = True

        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval_seconds,),
            daemon=True,
            name="compliance-monitor",
        )
        self._monitor_thread.start()

        logger.info(f"Compliance monitoring started (interval: {check_interval_seconds}s)")

    def stop_monitoring(self):
        """Stop compliance monitoring."""
        if not self._monitoring:
            return

        self._monitoring = False

        # Wait for thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=10)

        logger.info("Compliance monitoring stopped")

    def _monitoring_loop(self, check_interval: int):
        """
        Main monitoring loop.

        Args:
            check_interval: Seconds between checks
        """
        logger.info("Monitoring loop started")

        while self._monitoring:
            try:
                # Run compliance checks
                self._run_monitoring_checks()

                # Sleep until next check
                time.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(60)  # Sleep 1 min on error

        logger.info("Monitoring loop stopped")

    def _run_monitoring_checks(self):
        """Run all monitoring checks."""
        logger.debug("Running monitoring checks")

        # Get all evidence if available
        evidence_by_regulation = None
        if self.evidence_collector:
            all_evidence = self.evidence_collector.get_all_evidence()
            evidence_by_regulation = {
                reg_type: all_evidence
                for reg_type in self.config.enabled_regulations
            }

        # Run compliance checks
        snapshot = self.engine.run_all_checks(evidence_by_regulation)

        # Check thresholds
        self._check_compliance_thresholds(snapshot)

        # Detect new violations
        self._detect_violations(snapshot)

        # Check evidence expiration
        if self.evidence_collector:
            self._check_evidence_expiration()

        # Check remediation actions
        # (Would need access to remediation plans - skipping for now)

        # Update metrics
        metrics = self._calculate_metrics(snapshot)
        self._metrics_history.append(metrics)

        # Keep only last 30 days of metrics
        cutoff = datetime.utcnow() - timedelta(days=30)
        self._metrics_history = [
            m for m in self._metrics_history if m.timestamp > cutoff
        ]

        logger.debug(f"Monitoring checks complete, {len(self._alerts)} total alerts")

    def _check_compliance_thresholds(self, snapshot: ComplianceSnapshot):
        """
        Check if compliance is below configured thresholds.

        Args:
            snapshot: Compliance snapshot
        """
        threshold = self.config.alert_threshold_percentage

        # Check overall compliance
        if snapshot.overall_compliance_percentage < threshold:
            alert = ComplianceAlert(
                alert_type="threshold_breach",
                severity=ViolationSeverity.HIGH,
                title="Overall Compliance Below Threshold",
                message=(
                    f"Overall compliance is {snapshot.overall_compliance_percentage:.1f}%, "
                    f"below threshold of {threshold}%"
                ),
                metadata={
                    "current_compliance": snapshot.overall_compliance_percentage,
                    "threshold": threshold,
                    "snapshot_id": snapshot.snapshot_id,
                },
            )
            self._send_alert(alert)

        # Check per-regulation compliance
        for reg_type, result in snapshot.regulation_results.items():
            if result.compliance_percentage < threshold:
                alert = ComplianceAlert(
                    alert_type="threshold_breach",
                    severity=ViolationSeverity.MEDIUM,
                    title=f"{reg_type.value} Compliance Below Threshold",
                    message=(
                        f"{reg_type.value} compliance is {result.compliance_percentage:.1f}%, "
                        f"below threshold of {threshold}%"
                    ),
                    regulation_type=reg_type,
                    metadata={
                        "current_compliance": result.compliance_percentage,
                        "threshold": threshold,
                    },
                )
                self._send_alert(alert)

    def _detect_violations(self, snapshot: ComplianceSnapshot):
        """
        Detect new violations.

        Args:
            snapshot: Compliance snapshot
        """
        for reg_type, result in snapshot.regulation_results.items():
            for violation in result.violations:
                # Check if this is a new violation (not already alerted)
                if not self._is_violation_alerted(violation):
                    # Create alert for new violation
                    alert = ComplianceAlert(
                        alert_type="violation",
                        severity=violation.severity,
                        title=violation.title,
                        message=violation.description,
                        regulation_type=reg_type,
                        metadata={
                            "violation_id": violation.violation_id,
                            "control_id": violation.control_id,
                        },
                    )

                    # Send immediate alert for critical violations
                    if (
                        violation.severity == ViolationSeverity.CRITICAL
                        and self.config.alert_critical_violations_immediately
                    ):
                        self._send_alert(alert)

    def _check_evidence_expiration(self):
        """Check for expired or expiring evidence."""
        if not self.evidence_collector:
            return

        # Get expired evidence
        expired = self.evidence_collector.get_expired_evidence()

        if expired:
            alert = ComplianceAlert(
                alert_type="evidence_expiring",
                severity=ViolationSeverity.MEDIUM,
                title="Evidence Has Expired",
                message=f"{len(expired)} evidence items have expired and need renewal",
                metadata={
                    "expired_count": len(expired),
                    "evidence_ids": [e.evidence_id for e in expired],
                },
            )
            self._send_alert(alert)

        # Check for evidence expiring soon (30 days)
        all_evidence = self.evidence_collector.get_all_evidence()
        expiring_soon = []
        threshold_date = datetime.utcnow() + timedelta(days=30)

        for evidence_list in all_evidence.values():
            for evidence in evidence_list:
                if (
                    evidence.expiration_date
                    and evidence.expiration_date < threshold_date
                    and not evidence.is_expired()
                ):
                    expiring_soon.append(evidence)

        if expiring_soon:
            alert = ComplianceAlert(
                alert_type="evidence_expiring",
                severity=ViolationSeverity.LOW,
                title="Evidence Expiring Soon",
                message=f"{len(expiring_soon)} evidence items will expire in next 30 days",
                metadata={
                    "expiring_count": len(expiring_soon),
                    "evidence_ids": [e.evidence_id for e in expiring_soon],
                },
            )
            self._send_alert(alert)

    def _send_alert(self, alert: ComplianceAlert):
        """
        Send alert through registered handlers.

        Args:
            alert: Alert to send
        """
        # Add to alert history
        self._alerts.append(alert)

        # Keep only last 1000 alerts
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]

        logger.warning(
            f"COMPLIANCE ALERT [{alert.severity.value.upper()}]: {alert.title} - {alert.message}"
        )

        # Call registered handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler {handler.__name__} failed: {e}")

    def _is_violation_alerted(self, violation: ComplianceViolation) -> bool:
        """
        Check if violation has already been alerted.

        Args:
            violation: Violation to check

        Returns:
            True if already alerted
        """
        for alert in self._alerts:
            if alert.alert_type == "violation":
                if alert.metadata.get("violation_id") == violation.violation_id:
                    return True
        return False

    def _calculate_metrics(self, snapshot: ComplianceSnapshot) -> MonitoringMetrics:
        """
        Calculate monitoring metrics from snapshot.

        Args:
            snapshot: Compliance snapshot

        Returns:
            Monitoring metrics
        """
        # Count violations by severity
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        for result in snapshot.regulation_results.values():
            for violation in result.violations:
                if violation.severity == ViolationSeverity.CRITICAL:
                    critical_count += 1
                elif violation.severity == ViolationSeverity.HIGH:
                    high_count += 1
                elif violation.severity == ViolationSeverity.MEDIUM:
                    medium_count += 1
                elif violation.severity == ViolationSeverity.LOW:
                    low_count += 1

        # Evidence metrics
        total_evidence = 0
        expired_evidence = 0
        expiring_soon = 0

        if self.evidence_collector:
            all_evidence = self.evidence_collector.get_all_evidence()
            for evidence_list in all_evidence.values():
                total_evidence += len(evidence_list)
                for evidence in evidence_list:
                    if evidence.is_expired():
                        expired_evidence += 1
                    elif (
                        evidence.expiration_date
                        and evidence.expiration_date
                        < datetime.utcnow() + timedelta(days=30)
                    ):
                        expiring_soon += 1

        # Compliance trend
        trend = self._calculate_trend()

        # Create metrics
        metrics = MonitoringMetrics(
            overall_compliance_percentage=snapshot.overall_compliance_percentage,
            overall_score=snapshot.overall_score,
            compliance_by_regulation={
                reg_type.value: result.compliance_percentage
                for reg_type, result in snapshot.regulation_results.items()
            },
            total_violations=snapshot.total_violations,
            critical_violations=critical_count,
            high_violations=high_count,
            medium_violations=medium_count,
            low_violations=low_count,
            total_evidence=total_evidence,
            expired_evidence=expired_evidence,
            expiring_soon_evidence=expiring_soon,
            compliance_trend=trend,
        )

        return metrics

    def _calculate_trend(self) -> str:
        """
        Calculate compliance trend based on metrics history.

        Returns:
            Trend: improving, stable, declining
        """
        if len(self._metrics_history) < 2:
            return "stable"

        # Compare last metric with one from 7 days ago (if available)
        latest = self._metrics_history[-1]
        week_ago = None

        cutoff = datetime.utcnow() - timedelta(days=7)
        for metric in reversed(self._metrics_history[:-1]):
            if metric.timestamp < cutoff:
                week_ago = metric
                break

        if not week_ago:
            # Not enough history, compare with previous
            week_ago = self._metrics_history[-2]

        # Compare compliance percentages
        diff = latest.overall_compliance_percentage - week_ago.overall_compliance_percentage

        if diff > 2.0:
            return "improving"
        elif diff < -2.0:
            return "declining"
        else:
            return "stable"

    def get_current_metrics(self) -> Optional[MonitoringMetrics]:
        """
        Get current monitoring metrics.

        Returns:
            Latest metrics or None
        """
        if not self._metrics_history:
            return None
        return self._metrics_history[-1]

    def get_metrics_history(
        self,
        days: int = 30,
    ) -> List[MonitoringMetrics]:
        """
        Get metrics history for specified days.

        Args:
            days: Number of days of history

        Returns:
            List of metrics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [m for m in self._metrics_history if m.timestamp > cutoff]

    def get_alerts(
        self,
        alert_type: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        severity: Optional[ViolationSeverity] = None,
    ) -> List[ComplianceAlert]:
        """
        Get alerts filtered by criteria.

        Args:
            alert_type: Optional filter by alert type
            acknowledged: Optional filter by acknowledged status
            severity: Optional filter by severity

        Returns:
            List of matching alerts
        """
        alerts = self._alerts

        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge alert.

        Args:
            alert_id: Alert ID
            acknowledged_by: User acknowledging

        Returns:
            True if successful
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledge(acknowledged_by)
                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                return True

        return False

    def generate_dashboard_data(self) -> Dict[str, any]:
        """
        Generate dashboard data for compliance monitoring.

        Returns:
            Dashboard data dict
        """
        current_metrics = self.get_current_metrics()

        if not current_metrics:
            return {"error": "No metrics available"}

        # Get recent alerts
        recent_alerts = sorted(
            self._alerts,
            key=lambda a: a.triggered_at,
            reverse=True,
        )[:10]

        return {
            "current_metrics": {
                "overall_compliance": current_metrics.overall_compliance_percentage,
                "overall_score": current_metrics.overall_score,
                "trend": current_metrics.compliance_trend,
                "total_violations": current_metrics.total_violations,
                "critical_violations": current_metrics.critical_violations,
            },
            "compliance_by_regulation": current_metrics.compliance_by_regulation,
            "violations_by_severity": {
                "critical": current_metrics.critical_violations,
                "high": current_metrics.high_violations,
                "medium": current_metrics.medium_violations,
                "low": current_metrics.low_violations,
            },
            "evidence_health": {
                "total": current_metrics.total_evidence,
                "expired": current_metrics.expired_evidence,
                "expiring_soon": current_metrics.expiring_soon_evidence,
            },
            "recent_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "type": alert.alert_type,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "acknowledged": alert.acknowledged,
                }
                for alert in recent_alerts
            ],
        }
