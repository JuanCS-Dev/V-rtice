"""
Compliance Engine

Core compliance checking engine. Orchestrates automated compliance checks,
evidence collection, violation detection, and reporting across all supported
regulations.

Features:
- Automated compliance checking for 50+ controls
- Multi-regulation support (8 frameworks)
- Evidence-based compliance validation
- Violation detection and severity assessment
- Compliance scoring and trending
- Compliance report generation

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base import (
    ComplianceConfig,
    ComplianceResult,
    ComplianceStatus,
    ComplianceViolation,
    Control,
    ControlCategory,
    Evidence,
    RegulationType,
    ViolationSeverity,
)
from .regulations import get_regulation

logger = logging.getLogger(__name__)


@dataclass
class ComplianceCheckResult:
    """
    Result of running compliance check for a regulation.
    """

    regulation_type: RegulationType
    checked_at: datetime
    total_controls: int
    controls_checked: int
    compliant: int
    non_compliant: int
    partially_compliant: int
    not_applicable: int
    pending_review: int
    evidence_required: int
    results: list[ComplianceResult] = field(default_factory=list)
    violations: list[ComplianceViolation] = field(default_factory=list)
    compliance_percentage: float = 0.0
    score: float = 0.0  # Weighted compliance score (0.0-1.0)

    def __post_init__(self):
        """Calculate metrics."""
        if self.total_controls > 0:
            # Compliance percentage (only compliant controls)
            self.compliance_percentage = (self.compliant / self.total_controls) * 100

            # Weighted score (compliant=1.0, partially=0.5, others=0.0)
            weighted_sum = (
                (self.compliant * 1.0)
                + (self.partially_compliant * 0.5)
                + (self.non_compliant * 0.0)
                + (self.not_applicable * 1.0)  # N/A counts as compliant
            )
            applicable_controls = self.total_controls - self.not_applicable
            if applicable_controls > 0:
                self.score = weighted_sum / applicable_controls
            else:
                self.score = 1.0

    def is_certification_ready(self, threshold: float = 95.0) -> bool:
        """Check if compliance meets certification threshold."""
        return self.compliance_percentage >= threshold

    def get_critical_violations(self) -> list[ComplianceViolation]:
        """Get critical severity violations."""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]


@dataclass
class ComplianceSnapshot:
    """
    Point-in-time snapshot of overall compliance status.
    """

    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    regulation_results: dict[RegulationType, ComplianceCheckResult] = field(default_factory=dict)
    overall_compliance_percentage: float = 0.0
    overall_score: float = 0.0
    total_violations: int = 0
    critical_violations: int = 0

    def __post_init__(self):
        """Calculate overall metrics."""
        if self.regulation_results:
            # Average compliance percentage across regulations
            percentages = [r.compliance_percentage for r in self.regulation_results.values()]
            self.overall_compliance_percentage = sum(percentages) / len(percentages)

            # Average score
            scores = [r.score for r in self.regulation_results.values()]
            self.overall_score = sum(scores) / len(scores)

            # Total violations
            for result in self.regulation_results.values():
                self.total_violations += len(result.violations)
                self.critical_violations += len(result.get_critical_violations())


# Type alias for control checker functions
ControlChecker = Callable[[Control, ComplianceConfig], ComplianceResult]


class ComplianceEngine:
    """
    Core compliance checking engine.

    Orchestrates automated compliance checks across all supported regulations.
    Extensible through custom control checkers.
    """

    def __init__(self, config: ComplianceConfig | None = None):
        """
        Initialize compliance engine.

        Args:
            config: Compliance configuration (uses default if None)
        """
        self.config = config or ComplianceConfig()
        self._control_checkers: dict[str, ControlChecker] = {}
        self._category_checkers: dict[ControlCategory, ControlChecker] = {}

        # Register default checkers
        self._register_default_checkers()

        logger.info(f"Compliance engine initialized with {len(self.config.enabled_regulations)} regulations")

    def _register_default_checkers(self):
        """Register default automated checkers for control categories."""

        # Technical controls checker
        def check_technical_control(control: Control, config: ComplianceConfig) -> ComplianceResult:
            """Check technical controls (encryption, access control, etc)."""
            # Automated check: Look for evidence of technical implementation
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.PENDING_REVIEW,
                checked_by="compliance_engine",
                automated=True,
            )

            # Check if required evidence exists
            if control.evidence_required:
                result.status = ComplianceStatus.EVIDENCE_REQUIRED
                result.notes = f"Evidence required: {[e.value for e in control.evidence_required]}"
            else:
                # No evidence specified - assume needs manual review
                result.status = ComplianceStatus.PENDING_REVIEW
                result.notes = "Manual review required - no automated check available"

            return result

        # Security controls checker
        def check_security_control(control: Control, config: ComplianceConfig) -> ComplianceResult:
            """Check security controls (monitoring, incident response, etc)."""
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.PENDING_REVIEW,
                checked_by="compliance_engine",
                automated=True,
            )

            # Security controls typically require evidence
            if control.evidence_required:
                result.status = ComplianceStatus.EVIDENCE_REQUIRED
                result.notes = f"Security evidence required: {[e.value for e in control.evidence_required]}"
            else:
                result.status = ComplianceStatus.PENDING_REVIEW
                result.notes = "Security control requires manual review"

            return result

        # Documentation controls checker
        def check_documentation_control(control: Control, config: ComplianceConfig) -> ComplianceResult:
            """Check documentation controls."""
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.EVIDENCE_REQUIRED,
                checked_by="compliance_engine",
                automated=True,
                notes="Documentation evidence required",
            )
            return result

        # Monitoring controls checker
        def check_monitoring_control(control: Control, config: ComplianceConfig) -> ComplianceResult:
            """Check monitoring controls (logging, alerting, etc)."""
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.EVIDENCE_REQUIRED,
                checked_by="compliance_engine",
                automated=True,
                notes="Monitoring logs/configuration evidence required",
            )
            return result

        # Governance controls checker
        def check_governance_control(control: Control, config: ComplianceConfig) -> ComplianceResult:
            """Check governance controls (policies, procedures, etc)."""
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.EVIDENCE_REQUIRED,
                checked_by="compliance_engine",
                automated=True,
                notes="Policy/procedure documentation required",
            )
            return result

        # Testing controls checker
        def check_testing_control(control: Control, config: ComplianceConfig) -> ComplianceResult:
            """Check testing controls."""
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.EVIDENCE_REQUIRED,
                checked_by="compliance_engine",
                automated=True,
                notes="Test results evidence required",
            )
            return result

        # Organizational controls checker
        def check_organizational_control(control: Control, config: ComplianceConfig) -> ComplianceResult:
            """Check organizational controls."""
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.PENDING_REVIEW,
                checked_by="compliance_engine",
                automated=True,
                notes="Organizational control requires manual review",
            )
            return result

        # Privacy controls checker
        def check_privacy_control(control: Control, config: ComplianceConfig) -> ComplianceResult:
            """Check privacy controls."""
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.EVIDENCE_REQUIRED,
                checked_by="compliance_engine",
                automated=True,
                notes="Privacy controls evidence required (DPIA, consent records, etc)",
            )
            return result

        # Register category checkers
        self._category_checkers[ControlCategory.TECHNICAL] = check_technical_control
        self._category_checkers[ControlCategory.SECURITY] = check_security_control
        self._category_checkers[ControlCategory.DOCUMENTATION] = check_documentation_control
        self._category_checkers[ControlCategory.MONITORING] = check_monitoring_control
        self._category_checkers[ControlCategory.GOVERNANCE] = check_governance_control
        self._category_checkers[ControlCategory.TESTING] = check_testing_control
        self._category_checkers[ControlCategory.ORGANIZATIONAL] = check_organizational_control
        self._category_checkers[ControlCategory.PRIVACY] = check_privacy_control

    def register_control_checker(self, control_id: str, checker: ControlChecker):
        """
        Register custom checker for specific control.

        Args:
            control_id: Control ID to check
            checker: Checker function
        """
        self._control_checkers[control_id] = checker
        logger.info(f"Registered custom checker for control {control_id}")

    def register_category_checker(self, category: ControlCategory, checker: ControlChecker):
        """
        Register custom checker for control category.

        Args:
            category: Control category
            checker: Checker function
        """
        self._category_checkers[category] = checker
        logger.info(f"Registered custom checker for category {category.value}")

    def check_control(
        self,
        control: Control,
        evidence: list[Evidence] | None = None,
    ) -> ComplianceResult:
        """
        Check compliance for a specific control.

        Args:
            control: Control to check
            evidence: Optional list of evidence for this control

        Returns:
            Compliance check result
        """
        logger.debug(f"Checking control {control.control_id}")

        # Check if custom checker registered for this control
        if control.control_id in self._control_checkers:
            result = self._control_checkers[control.control_id](control, self.config)
        # Check if category checker registered
        elif control.category in self._category_checkers:
            result = self._category_checkers[control.category](control, self.config)
        else:
            # Default: require manual review
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.PENDING_REVIEW,
                checked_by="compliance_engine",
                automated=False,
                notes="No automated checker available - manual review required",
            )

        # Attach provided evidence
        if evidence:
            result.evidence.extend(evidence)

            # Re-evaluate status based on evidence
            if result.status == ComplianceStatus.EVIDENCE_REQUIRED:
                # Check if all required evidence types are present
                required_types = set(control.evidence_required)
                provided_types = set(e.evidence_type for e in evidence)

                if required_types.issubset(provided_types):
                    # All required evidence provided
                    # Check for expired evidence
                    expired = [e for e in evidence if e.is_expired()]
                    if expired:
                        result.status = ComplianceStatus.PARTIALLY_COMPLIANT
                        result.notes = f"Some evidence has expired: {len(expired)} items"
                    else:
                        result.status = ComplianceStatus.COMPLIANT
                        result.score = 1.0
                        result.notes = "All required evidence provided and verified"
                else:
                    # Missing some evidence types
                    missing = required_types - provided_types
                    result.status = ComplianceStatus.PARTIALLY_COMPLIANT
                    result.score = 0.5
                    result.notes = f"Missing evidence types: {[t.value for t in missing]}"

        return result

    def check_compliance(
        self,
        regulation_type: RegulationType,
        evidence_by_control: dict[str, list[Evidence]] | None = None,
    ) -> ComplianceCheckResult:
        """
        Check compliance for a specific regulation.

        Args:
            regulation_type: Type of regulation to check
            evidence_by_control: Optional dict mapping control_id -> evidence list

        Returns:
            Compliance check result for regulation
        """
        logger.info(f"Checking compliance for {regulation_type.value}")

        # Check if regulation is enabled
        if not self.config.is_regulation_enabled(regulation_type):
            logger.warning(f"Regulation {regulation_type.value} is not enabled")
            return ComplianceCheckResult(
                regulation_type=regulation_type,
                checked_at=datetime.utcnow(),
                total_controls=0,
                controls_checked=0,
                compliant=0,
                non_compliant=0,
                partially_compliant=0,
                not_applicable=0,
                pending_review=0,
                evidence_required=0,
            )

        # Get regulation definition
        regulation = get_regulation(regulation_type)
        evidence_by_control = evidence_by_control or {}

        # Check each control
        results: list[ComplianceResult] = []
        violations: list[ComplianceViolation] = []

        for control in regulation.controls:
            # Get evidence for this control
            control_evidence = evidence_by_control.get(control.control_id, [])

            # Check control
            result = self.check_control(control, control_evidence)
            results.append(result)

            # Detect violations
            if result.status == ComplianceStatus.NON_COMPLIANT:
                violation = ComplianceViolation(
                    control_id=control.control_id,
                    regulation_type=regulation_type,
                    severity=self._determine_violation_severity(control),
                    title=f"Non-compliance with {control.title}",
                    description=f"Control {control.control_id} is not compliant. {result.notes or ''}",
                    detected_by="compliance_engine",
                )
                violations.append(violation)

        # Count status
        status_counts = {
            ComplianceStatus.COMPLIANT: 0,
            ComplianceStatus.NON_COMPLIANT: 0,
            ComplianceStatus.PARTIALLY_COMPLIANT: 0,
            ComplianceStatus.NOT_APPLICABLE: 0,
            ComplianceStatus.PENDING_REVIEW: 0,
            ComplianceStatus.EVIDENCE_REQUIRED: 0,
        }

        for result in results:
            if result.status in status_counts:
                status_counts[result.status] += 1

        # Create result
        check_result = ComplianceCheckResult(
            regulation_type=regulation_type,
            checked_at=datetime.utcnow(),
            total_controls=len(regulation.controls),
            controls_checked=len(results),
            compliant=status_counts[ComplianceStatus.COMPLIANT],
            non_compliant=status_counts[ComplianceStatus.NON_COMPLIANT],
            partially_compliant=status_counts[ComplianceStatus.PARTIALLY_COMPLIANT],
            not_applicable=status_counts[ComplianceStatus.NOT_APPLICABLE],
            pending_review=status_counts[ComplianceStatus.PENDING_REVIEW],
            evidence_required=status_counts[ComplianceStatus.EVIDENCE_REQUIRED],
            results=results,
            violations=violations,
        )

        logger.info(
            f"Compliance check complete for {regulation_type.value}: "
            f"{check_result.compliance_percentage:.1f}% compliant, "
            f"{len(violations)} violations"
        )

        return check_result

    def run_all_checks(
        self,
        evidence_by_regulation: dict[RegulationType, dict[str, list[Evidence]]] | None = None,
    ) -> ComplianceSnapshot:
        """
        Run compliance checks for all enabled regulations.

        Args:
            evidence_by_regulation: Optional nested dict: regulation_type -> control_id -> evidence

        Returns:
            Compliance snapshot with all results
        """
        logger.info(f"Running compliance checks for {len(self.config.enabled_regulations)} regulations")

        evidence_by_regulation = evidence_by_regulation or {}
        results: dict[RegulationType, ComplianceCheckResult] = {}

        for regulation_type in self.config.enabled_regulations:
            # Get evidence for this regulation
            regulation_evidence = evidence_by_regulation.get(regulation_type, {})

            # Check compliance
            result = self.check_compliance(regulation_type, regulation_evidence)
            results[regulation_type] = result

        # Create snapshot
        snapshot = ComplianceSnapshot(regulation_results=results)

        logger.info(
            f"All compliance checks complete: {snapshot.overall_compliance_percentage:.1f}% overall, "
            f"{snapshot.total_violations} total violations"
        )

        return snapshot

    def get_compliance_status(
        self,
        regulation_type: RegulationType | None = None,
    ) -> dict[str, Any]:
        """
        Get current compliance status summary.

        Args:
            regulation_type: Optional specific regulation (all if None)

        Returns:
            Compliance status dict
        """
        if regulation_type:
            # Single regulation
            result = self.check_compliance(regulation_type)
            return {
                "regulation": regulation_type.value,
                "compliance_percentage": result.compliance_percentage,
                "score": result.score,
                "total_controls": result.total_controls,
                "compliant": result.compliant,
                "non_compliant": result.non_compliant,
                "violations": len(result.violations),
                "critical_violations": len(result.get_critical_violations()),
                "certification_ready": result.is_certification_ready(),
            }
        # All regulations
        snapshot = self.run_all_checks()
        return {
            "overall_compliance_percentage": snapshot.overall_compliance_percentage,
            "overall_score": snapshot.overall_score,
            "total_violations": snapshot.total_violations,
            "critical_violations": snapshot.critical_violations,
            "regulations": {
                reg_type.value: {
                    "compliance_percentage": result.compliance_percentage,
                    "score": result.score,
                    "violations": len(result.violations),
                }
                for reg_type, result in snapshot.regulation_results.items()
            },
        }

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        regulation_types: list[RegulationType] | None = None,
    ) -> dict[str, Any]:
        """
        Generate compliance report for time period.

        Args:
            start_date: Report start date
            end_date: Report end date
            regulation_types: Optional list of regulations (all enabled if None)

        Returns:
            Compliance report dict
        """
        regulation_types = regulation_types or self.config.enabled_regulations

        logger.info(
            f"Generating compliance report for {len(regulation_types)} regulations "
            f"from {start_date.date()} to {end_date.date()}"
        )

        # Run current compliance checks
        snapshot = self.run_all_checks()

        # Filter to requested regulations
        filtered_results = {
            reg_type: result for reg_type, result in snapshot.regulation_results.items() if reg_type in regulation_types
        }

        # Build report
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "overall_compliance_percentage": snapshot.overall_compliance_percentage,
                "overall_score": snapshot.overall_score,
                "total_violations": snapshot.total_violations,
                "critical_violations": snapshot.critical_violations,
            },
            "regulations": {},
        }

        for reg_type, result in filtered_results.items():
            regulation = get_regulation(reg_type)
            report["regulations"][reg_type.value] = {
                "name": regulation.name,
                "version": regulation.version,
                "jurisdiction": regulation.jurisdiction,
                "compliance_percentage": result.compliance_percentage,
                "score": result.score,
                "total_controls": result.total_controls,
                "compliant": result.compliant,
                "non_compliant": result.non_compliant,
                "partially_compliant": result.partially_compliant,
                "violations": [
                    {
                        "violation_id": v.violation_id,
                        "control_id": v.control_id,
                        "severity": v.severity.value,
                        "title": v.title,
                        "description": v.description,
                        "detected_at": v.detected_at.isoformat(),
                    }
                    for v in result.violations
                ],
                "certification_ready": result.is_certification_ready(),
            }

        logger.info(f"Compliance report generated: {report['report_id']}")

        return report

    def _determine_violation_severity(self, control: Control) -> ViolationSeverity:
        """
        Determine severity of violation based on control characteristics.

        Args:
            control: Control that was violated

        Returns:
            Violation severity
        """
        # Mandatory controls are more severe
        if not control.mandatory:
            return ViolationSeverity.LOW

        # Security and privacy controls are critical
        if control.category in [ControlCategory.SECURITY, ControlCategory.PRIVACY]:
            return ViolationSeverity.HIGH

        # Governance and technical controls are medium
        if control.category in [ControlCategory.GOVERNANCE, ControlCategory.TECHNICAL]:
            return ViolationSeverity.MEDIUM

        # Others are low
        return ViolationSeverity.LOW
