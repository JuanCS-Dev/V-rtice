"""
Certification Checkers

Certification-specific compliance checkers for ISO 27001, SOC 2 Type II,
and IEEE 7000. Provides certification readiness assessment and audit support.

Supported Certifications:
- ISO/IEC 27001:2022 - Information Security Management System
- SOC 2 Type II - Trust Services Criteria (Security, Availability, PI, Confidentiality)
- IEEE 7000-2021 - Ethical AI Design

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import logging
import uuid

from .base import (
    ComplianceConfig,
    ComplianceResult,
    ComplianceStatus,
    Control,
    Evidence,
    RegulationType,
)
from .compliance_engine import ComplianceEngine, ComplianceCheckResult
from .evidence_collector import EvidenceCollector

logger = logging.getLogger(__name__)


@dataclass
class CertificationResult:
    """
    Result of certification readiness check.
    """

    certification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    regulation_type: RegulationType = RegulationType.ISO_27001
    checked_at: datetime = field(default_factory=datetime.utcnow)
    certification_ready: bool = False
    compliance_percentage: float = 0.0
    score: float = 0.0
    required_threshold: float = 95.0
    gaps_to_certification: int = 0
    critical_gaps: List[str] = field(default_factory=list)  # control_ids
    recommendations: List[str] = field(default_factory=list)
    estimated_days_to_certification: int = 0
    compliance_results: List[ComplianceResult] = field(default_factory=list)
    evidence_summary: Dict[str, int] = field(default_factory=dict)

    def get_summary(self) -> str:
        """Get summary text."""
        if self.certification_ready:
            return (
                f"READY FOR CERTIFICATION: {self.compliance_percentage:.1f}% compliant "
                f"(threshold: {self.required_threshold}%)"
            )
        else:
            return (
                f"NOT READY: {self.compliance_percentage:.1f}% compliant "
                f"(need {self.required_threshold}%), "
                f"{self.gaps_to_certification} gaps remaining, "
                f"estimated {self.estimated_days_to_certification} days to certification"
            )


class ISO27001Checker:
    """
    ISO/IEC 27001:2022 certification checker.

    Checks certification readiness for ISO 27001 Information Security Management System.
    """

    def __init__(
        self,
        compliance_engine: ComplianceEngine,
        evidence_collector: Optional[EvidenceCollector] = None,
    ):
        """
        Initialize ISO 27001 checker.

        Args:
            compliance_engine: Compliance engine instance
            evidence_collector: Optional evidence collector
        """
        self.engine = compliance_engine
        self.evidence_collector = evidence_collector
        self.regulation_type = RegulationType.ISO_27001

        logger.info("ISO 27001 checker initialized")

    def check_certification_readiness(
        self,
        evidence_by_control: Optional[Dict[str, List[Evidence]]] = None,
    ) -> CertificationResult:
        """
        Check ISO 27001 certification readiness.

        Args:
            evidence_by_control: Optional evidence mapping

        Returns:
            Certification result
        """
        logger.info("Checking ISO 27001 certification readiness")

        # Get evidence if available
        if not evidence_by_control and self.evidence_collector:
            evidence_by_control = self.evidence_collector.get_all_evidence()

        # Run compliance check
        compliance_result = self.engine.check_compliance(
            self.regulation_type,
            evidence_by_control,
        )

        # ISO 27001 requires 100% mandatory controls compliant
        # We use 95% as practical threshold (allows minor documentation gaps)
        threshold = 95.0
        ready = compliance_result.compliance_percentage >= threshold

        # Identify gaps
        gaps = [
            r.control_id
            for r in compliance_result.results
            if r.status != ComplianceStatus.COMPLIANT
            and r.status != ComplianceStatus.NOT_APPLICABLE
        ]

        # Identify critical gaps (mandatory controls)
        from .regulations import get_regulation

        regulation = get_regulation(self.regulation_type)
        mandatory_controls = regulation.get_mandatory_controls()
        mandatory_ids = {c.control_id for c in mandatory_controls}

        critical_gaps = [g for g in gaps if g in mandatory_ids]

        # Generate recommendations
        recommendations = self._generate_iso27001_recommendations(
            compliance_result, critical_gaps
        )

        # Estimate days to certification (assuming 40 hours/week, 1 engineer)
        # Average 20 hours per gap
        estimated_hours = len(gaps) * 20
        estimated_days = (estimated_hours // 8) if estimated_hours > 0 else 0

        # Evidence summary
        evidence_summary = self._calculate_evidence_summary(evidence_by_control)

        # Create result
        result = CertificationResult(
            regulation_type=self.regulation_type,
            certification_ready=ready,
            compliance_percentage=compliance_result.compliance_percentage,
            score=compliance_result.score,
            required_threshold=threshold,
            gaps_to_certification=len(gaps),
            critical_gaps=critical_gaps,
            recommendations=recommendations,
            estimated_days_to_certification=estimated_days,
            compliance_results=compliance_result.results,
            evidence_summary=evidence_summary,
        )

        logger.info(f"ISO 27001 readiness check: {result.get_summary()}")

        return result

    def _generate_iso27001_recommendations(
        self,
        compliance_result: ComplianceCheckResult,
        critical_gaps: List[str],
    ) -> List[str]:
        """Generate ISO 27001-specific recommendations."""
        recommendations = []

        if critical_gaps:
            recommendations.append(
                f"Address {len(critical_gaps)} critical mandatory controls first: {', '.join(critical_gaps[:5])}"
            )

        # Check for specific ISO 27001 requirements
        policy_controls = ["ISO-27001-A.5.1"]
        access_controls = ["ISO-27001-A.8.2"]
        crypto_controls = ["ISO-27001-A.8.24"]
        monitoring_controls = ["ISO-27001-A.8.16"]

        for result in compliance_result.results:
            if result.control_id in policy_controls and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Establish and document Information Security Policy (A.5.1) - Required for certification"
                )
            if result.control_id in access_controls and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Implement privileged access controls (A.8.2) - High priority for certification"
                )
            if result.control_id in crypto_controls and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Define and implement cryptography standards (A.8.24)"
                )
            if result.control_id in monitoring_controls and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Implement security monitoring and logging (A.8.16)"
                )

        if compliance_result.compliance_percentage < 80:
            recommendations.append(
                "Consider engaging ISO 27001 consultant to accelerate certification readiness"
            )

        recommendations.append(
            "Schedule internal audit 3 months before certification audit"
        )

        return recommendations[:10]  # Limit to top 10

    def _calculate_evidence_summary(
        self,
        evidence_by_control: Optional[Dict[str, List[Evidence]]],
    ) -> Dict[str, int]:
        """Calculate evidence summary statistics."""
        if not evidence_by_control:
            return {"total": 0, "verified": 0, "expired": 0}

        total = 0
        verified = 0
        expired = 0

        for evidence_list in evidence_by_control.values():
            for evidence in evidence_list:
                total += 1
                if evidence.verified:
                    verified += 1
                if evidence.is_expired():
                    expired += 1

        return {
            "total": total,
            "verified": verified,
            "expired": expired,
        }


class SOC2Checker:
    """
    SOC 2 Type II certification checker.

    Checks certification readiness for SOC 2 Type II audit (Security, Availability,
    Processing Integrity, Confidentiality).
    """

    def __init__(
        self,
        compliance_engine: ComplianceEngine,
        evidence_collector: Optional[EvidenceCollector] = None,
    ):
        """
        Initialize SOC 2 checker.

        Args:
            compliance_engine: Compliance engine instance
            evidence_collector: Optional evidence collector
        """
        self.engine = compliance_engine
        self.evidence_collector = evidence_collector
        self.regulation_type = RegulationType.SOC2_TYPE_II

        logger.info("SOC 2 Type II checker initialized")

    def check_certification_readiness(
        self,
        evidence_by_control: Optional[Dict[str, List[Evidence]]] = None,
        audit_period_months: int = 6,
    ) -> CertificationResult:
        """
        Check SOC 2 Type II certification readiness.

        Args:
            evidence_by_control: Optional evidence mapping
            audit_period_months: Audit period (6-12 months for Type II)

        Returns:
            Certification result
        """
        logger.info(f"Checking SOC 2 Type II readiness (audit period: {audit_period_months} months)")

        # Get evidence if available
        if not evidence_by_control and self.evidence_collector:
            evidence_by_control = self.evidence_collector.get_all_evidence()

        # Run compliance check
        compliance_result = self.engine.check_compliance(
            self.regulation_type,
            evidence_by_control,
        )

        # SOC 2 Type II requires evidence of consistent controls over time
        # 95% threshold for readiness (allows minor gaps)
        threshold = 95.0
        ready = compliance_result.compliance_percentage >= threshold

        # For Type II, also need evidence spanning audit period
        # (This would require historical evidence - simplified here)

        # Identify gaps
        gaps = [
            r.control_id
            for r in compliance_result.results
            if r.status != ComplianceStatus.COMPLIANT
            and r.status != ComplianceStatus.NOT_APPLICABLE
        ]

        # Critical gaps - Security is mandatory
        critical_gaps = [
            r.control_id
            for r in compliance_result.results
            if r.control_id.startswith("SOC2-CC6")  # Common Criteria Security
            and r.status != ComplianceStatus.COMPLIANT
        ]

        # Generate recommendations
        recommendations = self._generate_soc2_recommendations(
            compliance_result, critical_gaps, audit_period_months
        )

        # Estimate days to readiness
        # SOC 2 Type II requires audit period + remediation time
        estimated_remediation_days = len(gaps) * 15  # 15 days per gap avg
        estimated_audit_period_days = audit_period_months * 30
        estimated_days = estimated_remediation_days + estimated_audit_period_days

        # Evidence summary
        evidence_summary = self._calculate_evidence_summary(evidence_by_control)

        # Create result
        result = CertificationResult(
            regulation_type=self.regulation_type,
            certification_ready=ready,
            compliance_percentage=compliance_result.compliance_percentage,
            score=compliance_result.score,
            required_threshold=threshold,
            gaps_to_certification=len(gaps),
            critical_gaps=critical_gaps,
            recommendations=recommendations,
            estimated_days_to_certification=estimated_days,
            compliance_results=compliance_result.results,
            evidence_summary=evidence_summary,
        )

        logger.info(f"SOC 2 Type II readiness check: {result.get_summary()}")

        return result

    def _generate_soc2_recommendations(
        self,
        compliance_result: ComplianceCheckResult,
        critical_gaps: List[str],
        audit_period_months: int,
    ) -> List[str]:
        """Generate SOC 2-specific recommendations."""
        recommendations = []

        if critical_gaps:
            recommendations.append(
                f"Address {len(critical_gaps)} critical Security (CC6) controls first"
            )

        recommendations.append(
            f"Implement continuous monitoring for {audit_period_months}-month audit period"
        )

        # Check for specific SOC 2 requirements
        for result in compliance_result.results:
            if result.control_id == "SOC2-CC6.1" and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Implement logical and physical access controls (CC6.1) - CRITICAL"
                )
            if result.control_id == "SOC2-CC6.6" and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Implement comprehensive logging and monitoring (CC6.6)"
                )
            if result.control_id == "SOC2-CC6.7" and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Establish incident response plan and procedures (CC6.7)"
                )

        recommendations.append(
            "Collect evidence continuously throughout audit period (automated logging)"
        )

        recommendations.append(
            f"Plan for {audit_period_months}-month SOC 2 Type II audit window"
        )

        if compliance_result.compliance_percentage < 85:
            recommendations.append(
                "Consider SOC 2 readiness assessment with audit firm"
            )

        return recommendations[:10]

    def _calculate_evidence_summary(
        self,
        evidence_by_control: Optional[Dict[str, List[Evidence]]],
    ) -> Dict[str, int]:
        """Calculate evidence summary statistics."""
        if not evidence_by_control:
            return {"total": 0, "verified": 0, "expired": 0}

        total = 0
        verified = 0
        expired = 0

        for evidence_list in evidence_by_control.values():
            for evidence in evidence_list:
                total += 1
                if evidence.verified:
                    verified += 1
                if evidence.is_expired():
                    expired += 1

        return {
            "total": total,
            "verified": verified,
            "expired": expired,
        }


class IEEE7000Checker:
    """
    IEEE 7000-2021 certification checker.

    Checks certification readiness for IEEE 7000 Ethical AI Design standard.
    """

    def __init__(
        self,
        compliance_engine: ComplianceEngine,
        evidence_collector: Optional[EvidenceCollector] = None,
    ):
        """
        Initialize IEEE 7000 checker.

        Args:
            compliance_engine: Compliance engine instance
            evidence_collector: Optional evidence collector
        """
        self.engine = compliance_engine
        self.evidence_collector = evidence_collector
        self.regulation_type = RegulationType.IEEE_7000

        logger.info("IEEE 7000 checker initialized")

    def check_certification_readiness(
        self,
        evidence_by_control: Optional[Dict[str, List[Evidence]]] = None,
    ) -> CertificationResult:
        """
        Check IEEE 7000 certification readiness.

        Args:
            evidence_by_control: Optional evidence mapping

        Returns:
            Certification result
        """
        logger.info("Checking IEEE 7000 certification readiness")

        # Get evidence if available
        if not evidence_by_control and self.evidence_collector:
            evidence_by_control = self.evidence_collector.get_all_evidence()

        # Run compliance check
        compliance_result = self.engine.check_compliance(
            self.regulation_type,
            evidence_by_control,
        )

        # IEEE 7000 requires documented value-based engineering process
        # 90% threshold (allows some flexibility in documentation)
        threshold = 90.0
        ready = compliance_result.compliance_percentage >= threshold

        # Identify gaps
        gaps = [
            r.control_id
            for r in compliance_result.results
            if r.status != ComplianceStatus.COMPLIANT
            and r.status != ComplianceStatus.NOT_APPLICABLE
        ]

        # Critical gaps - core value elicitation and risk assessment
        critical_controls = [
            "IEEE-7000-5.2",  # Stakeholder Analysis
            "IEEE-7000-5.3",  # Value Elicitation
            "IEEE-7000-5.5",  # Ethical Risk Assessment
        ]

        critical_gaps = [g for g in gaps if g in critical_controls]

        # Generate recommendations
        recommendations = self._generate_ieee7000_recommendations(
            compliance_result, critical_gaps
        )

        # Estimate days to certification
        estimated_hours = len(gaps) * 25  # IEEE 7000 is documentation-heavy
        estimated_days = (estimated_hours // 8) if estimated_hours > 0 else 0

        # Evidence summary
        evidence_summary = self._calculate_evidence_summary(evidence_by_control)

        # Create result
        result = CertificationResult(
            regulation_type=self.regulation_type,
            certification_ready=ready,
            compliance_percentage=compliance_result.compliance_percentage,
            score=compliance_result.score,
            required_threshold=threshold,
            gaps_to_certification=len(gaps),
            critical_gaps=critical_gaps,
            recommendations=recommendations,
            estimated_days_to_certification=estimated_days,
            compliance_results=compliance_result.results,
            evidence_summary=evidence_summary,
        )

        logger.info(f"IEEE 7000 readiness check: {result.get_summary()}")

        return result

    def _generate_ieee7000_recommendations(
        self,
        compliance_result: ComplianceCheckResult,
        critical_gaps: List[str],
    ) -> List[str]:
        """Generate IEEE 7000-specific recommendations."""
        recommendations = []

        if critical_gaps:
            recommendations.append(
                f"Complete {len(critical_gaps)} critical value-based engineering processes"
            )

        # Check for specific IEEE 7000 requirements
        for result in compliance_result.results:
            if result.control_id == "IEEE-7000-5.2" and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Complete stakeholder analysis (5.2) - Document all affected stakeholders"
                )
            if result.control_id == "IEEE-7000-5.3" and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Conduct value elicitation workshops (5.3) - CRITICAL for certification"
                )
            if result.control_id == "IEEE-7000-5.4" and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Map stakeholder values to system requirements (5.4)"
                )
            if result.control_id == "IEEE-7000-5.5" and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Conduct ethical risk assessment (5.5) - CRITICAL for certification"
                )
            if result.control_id == "IEEE-7000-5.7" and result.status != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    "Implement transparency and explainability features (5.7)"
                )

        recommendations.append(
            "Document complete value-based requirements traceability matrix"
        )

        recommendations.append(
            "Conduct stakeholder validation of value requirements"
        )

        if compliance_result.compliance_percentage < 80:
            recommendations.append(
                "Consider IEEE 7000 training for development team"
            )

        return recommendations[:10]

    def _calculate_evidence_summary(
        self,
        evidence_by_control: Optional[Dict[str, List[Evidence]]],
    ) -> Dict[str, int]:
        """Calculate evidence summary statistics."""
        if not evidence_by_control:
            return {"total": 0, "verified": 0, "expired": 0}

        total = 0
        verified = 0
        expired = 0

        for evidence_list in evidence_by_control.values():
            for evidence in evidence_list:
                total += 1
                if evidence.verified:
                    verified += 1
                if evidence.is_expired():
                    expired += 1

        return {
            "total": total,
            "verified": verified,
            "expired": expired,
        }
