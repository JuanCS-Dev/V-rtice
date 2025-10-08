"""
HITL Risk Assessor

Comprehensive risk assessment engine for security decisions. Analyzes multiple
risk dimensions to determine overall risk level and recommend automation level.

Risk Dimensions:
- Threat Severity: How dangerous is the threat?
- Asset Criticality: How important are affected assets?
- Business Impact: What's the business consequence?
- Action Reversibility: Can the action be undone?
- Blast Radius: How many assets/users affected?
- Compliance Impact: Regulatory implications?

Risk Score: 0.0 (no risk) to 1.0 (maximum risk)
Risk Level: LOW, MEDIUM, HIGH, CRITICAL

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import logging
from dataclasses import dataclass, field

from .base import (
    ActionType,
    DecisionContext,
    RiskLevel,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Risk Data Classes
# ============================================================================


@dataclass
class RiskFactors:
    """
    Individual risk factors that contribute to overall risk score.

    Each factor is scored 0.0 (low risk) to 1.0 (high risk).
    """

    # Threat factors
    threat_severity: float = 0.0  # Threat score from detection engine
    threat_confidence: float = 0.0  # Confidence in threat identification
    threat_novelty: float = 0.0  # Is this a new/unknown threat?

    # Asset factors
    asset_criticality: float = 0.0  # Business criticality of assets
    asset_count: float = 0.0  # Number of affected assets (normalized)
    data_sensitivity: float = 0.0  # Sensitivity of data on assets

    # Business factors
    financial_impact: float = 0.0  # Estimated financial loss
    operational_impact: float = 0.0  # Impact on operations
    reputational_impact: float = 0.0  # Reputation/brand damage

    # Action factors
    action_reversibility: float = 0.0  # Can action be undone? (0=fully reversible)
    action_aggressiveness: float = 0.0  # How aggressive is action?
    action_scope: float = 0.0  # Scope of action (local vs global)

    # Compliance factors
    compliance_impact: float = 0.0  # Regulatory/compliance implications
    privacy_impact: float = 0.0  # Privacy/PII implications

    # Environmental factors
    time_of_day: float = 0.0  # Higher risk outside business hours
    operator_availability: float = 0.0  # Are operators available?

    def get_all_factors(self) -> dict[str, float]:
        """Get all risk factors as dict."""
        return {
            "threat_severity": self.threat_severity,
            "threat_confidence": self.threat_confidence,
            "threat_novelty": self.threat_novelty,
            "asset_criticality": self.asset_criticality,
            "asset_count": self.asset_count,
            "data_sensitivity": self.data_sensitivity,
            "financial_impact": self.financial_impact,
            "operational_impact": self.operational_impact,
            "reputational_impact": self.reputational_impact,
            "action_reversibility": self.action_reversibility,
            "action_aggressiveness": self.action_aggressiveness,
            "action_scope": self.action_scope,
            "compliance_impact": self.compliance_impact,
            "privacy_impact": self.privacy_impact,
            "time_of_day": self.time_of_day,
            "operator_availability": self.operator_availability,
        }

    def get_max_factor(self) -> tuple[str, float]:
        """Get highest risk factor."""
        factors = self.get_all_factors()
        max_factor = max(factors.items(), key=lambda x: x[1])
        return max_factor


@dataclass
class RiskScore:
    """
    Computed risk score with breakdown by category.
    """

    # Overall risk score (0.0 to 1.0)
    overall_score: float = 0.0

    # Risk level
    risk_level: RiskLevel = RiskLevel.LOW

    # Category scores
    threat_risk: float = 0.0
    asset_risk: float = 0.0
    business_risk: float = 0.0
    action_risk: float = 0.0
    compliance_risk: float = 0.0
    environmental_risk: float = 0.0

    # Contributing factors
    factors: RiskFactors = field(default_factory=RiskFactors)

    # Risk justification
    justification: str = ""
    key_concerns: list[str] = field(default_factory=list)

    # Recommendations
    recommended_automation: str | None = None
    mitigation_suggestions: list[str] = field(default_factory=list)

    def get_category_breakdown(self) -> dict[str, float]:
        """Get risk breakdown by category."""
        return {
            "threat": self.threat_risk,
            "asset": self.asset_risk,
            "business": self.business_risk,
            "action": self.action_risk,
            "compliance": self.compliance_risk,
            "environmental": self.environmental_risk,
        }

    def get_summary(self) -> str:
        """Get human-readable risk summary."""
        parts = [
            f"Risk Level: {self.risk_level.value.upper()}",
            f"Score: {self.overall_score:.2f}",
        ]

        if self.key_concerns:
            parts.append(f"Concerns: {', '.join(self.key_concerns[:3])}")

        return " | ".join(parts)


# ============================================================================
# Risk Assessor
# ============================================================================


class RiskAssessor:
    """
    Comprehensive risk assessment engine.

    Analyzes security decisions across multiple risk dimensions and computes
    an overall risk score and level.
    """

    # Risk level thresholds
    CRITICAL_THRESHOLD = 0.75  # ≥0.75 → CRITICAL
    HIGH_THRESHOLD = 0.50  # ≥0.50 → HIGH (>50% risk is high)
    MEDIUM_THRESHOLD = 0.30  # ≥0.30 → MEDIUM
    # <0.30 → LOW

    # Category weights (must sum to 1.0)
    WEIGHTS = {
        "threat": 0.25,
        "asset": 0.20,
        "business": 0.20,
        "action": 0.15,
        "compliance": 0.10,
        "environmental": 0.10,
    }

    # Action aggressiveness scores
    ACTION_AGGRESSIVENESS = {
        ActionType.SEND_ALERT: 0.0,
        ActionType.CREATE_TICKET: 0.0,
        ActionType.COLLECT_LOGS: 0.1,
        ActionType.COLLECT_FORENSICS: 0.2,
        ActionType.THROTTLE_CONNECTION: 0.3,
        ActionType.SUSPEND_PROCESS: 0.4,
        ActionType.BLOCK_IP: 0.5,
        ActionType.BLOCK_DOMAIN: 0.5,
        ActionType.QUARANTINE_FILE: 0.6,
        ActionType.KILL_PROCESS: 0.6,
        ActionType.ISOLATE_HOST: 0.7,
        ActionType.DISABLE_USER: 0.7,
        ActionType.LOCK_ACCOUNT: 0.7,
        ActionType.DELETE_FILE: 0.8,
        ActionType.RESET_PASSWORD: 0.8,
        ActionType.DELETE_DATA: 0.9,
        ActionType.ENCRYPT_DATA: 0.5,
        ActionType.BACKUP_DATA: 0.2,
    }

    # Action reversibility scores (0=fully reversible, 1=irreversible)
    ACTION_REVERSIBILITY = {
        ActionType.SEND_ALERT: 0.0,
        ActionType.CREATE_TICKET: 0.0,
        ActionType.COLLECT_LOGS: 0.0,
        ActionType.THROTTLE_CONNECTION: 0.1,
        ActionType.BLOCK_IP: 0.2,
        ActionType.BLOCK_DOMAIN: 0.2,
        ActionType.SUSPEND_PROCESS: 0.2,
        ActionType.ISOLATE_HOST: 0.3,
        ActionType.QUARANTINE_FILE: 0.3,
        ActionType.KILL_PROCESS: 0.4,
        ActionType.DISABLE_USER: 0.4,
        ActionType.LOCK_ACCOUNT: 0.4,
        ActionType.RESET_PASSWORD: 0.6,
        ActionType.DELETE_FILE: 0.8,
        ActionType.DELETE_DATA: 0.9,
        ActionType.ENCRYPT_DATA: 0.5,
        ActionType.BACKUP_DATA: 0.1,
    }

    def __init__(self):
        """Initialize risk assessor."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def assess_risk(self, context: DecisionContext) -> RiskScore:
        """
        Perform comprehensive risk assessment.

        Args:
            context: Decision context to assess

        Returns:
            RiskScore with overall score, level, and breakdown
        """
        # Compute individual risk factors
        factors = self._compute_risk_factors(context)

        # Compute category scores
        threat_risk = self._compute_threat_risk(factors, context)
        asset_risk = self._compute_asset_risk(factors, context)
        business_risk = self._compute_business_risk(factors, context)
        action_risk = self._compute_action_risk(factors, context)
        compliance_risk = self._compute_compliance_risk(factors, context)
        environmental_risk = self._compute_environmental_risk(factors, context)

        # Compute weighted overall score
        overall_score = (
            self.WEIGHTS["threat"] * threat_risk
            + self.WEIGHTS["asset"] * asset_risk
            + self.WEIGHTS["business"] * business_risk
            + self.WEIGHTS["action"] * action_risk
            + self.WEIGHTS["compliance"] * compliance_risk
            + self.WEIGHTS["environmental"] * environmental_risk
        )

        # Determine risk level
        risk_level = self._score_to_level(overall_score)

        # Generate justification and concerns
        justification, key_concerns = self._generate_justification(factors, overall_score, risk_level)

        # Generate recommendations
        mitigation_suggestions = self._generate_mitigation_suggestions(factors, context)

        # Build risk score
        risk_score = RiskScore(
            overall_score=overall_score,
            risk_level=risk_level,
            threat_risk=threat_risk,
            asset_risk=asset_risk,
            business_risk=business_risk,
            action_risk=action_risk,
            compliance_risk=compliance_risk,
            environmental_risk=environmental_risk,
            factors=factors,
            justification=justification,
            key_concerns=key_concerns,
            mitigation_suggestions=mitigation_suggestions,
        )

        self.logger.info(
            f"Risk assessment complete: {risk_level.value} "
            f"(score={overall_score:.2f}, action={context.action_type.value})"
        )

        return risk_score

    def _compute_risk_factors(self, context: DecisionContext) -> RiskFactors:
        """Compute individual risk factors from context."""
        factors = RiskFactors()

        # Threat factors
        factors.threat_severity = context.threat_score
        factors.threat_confidence = context.confidence
        factors.threat_novelty = self._assess_threat_novelty(context)

        # Asset factors
        factors.asset_criticality = self._assess_asset_criticality(context)
        factors.asset_count = self._normalize_asset_count(len(context.affected_assets))
        factors.data_sensitivity = self._assess_data_sensitivity(context)

        # Business factors
        factors.financial_impact = self._normalize_financial_impact(context.estimated_cost)
        factors.operational_impact = self._assess_operational_impact(context)
        factors.reputational_impact = self._assess_reputational_impact(context)

        # Action factors
        factors.action_reversibility = self.ACTION_REVERSIBILITY.get(context.action_type, 0.5)
        factors.action_aggressiveness = self.ACTION_AGGRESSIVENESS.get(context.action_type, 0.5)
        factors.action_scope = self._assess_action_scope(context)

        # Compliance factors
        factors.compliance_impact = self._assess_compliance_impact(context)
        factors.privacy_impact = self._assess_privacy_impact(context)

        # Environmental factors
        factors.time_of_day = self._assess_time_of_day()
        factors.operator_availability = self._assess_operator_availability()

        return factors

    def _compute_threat_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """Compute threat-related risk (0.0 to 1.0)."""
        # Weight threat factors
        threat_risk = (
            0.5 * factors.threat_severity
            + 0.3 * (1.0 - factors.threat_confidence)  # Lower confidence = higher risk
            + 0.2 * factors.threat_novelty
        )
        return min(1.0, threat_risk)

    def _compute_asset_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """Compute asset-related risk."""
        asset_risk = 0.5 * factors.asset_criticality + 0.3 * factors.data_sensitivity + 0.2 * factors.asset_count
        return min(1.0, asset_risk)

    def _compute_business_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """Compute business impact risk."""
        business_risk = (
            0.4 * factors.financial_impact + 0.3 * factors.operational_impact + 0.3 * factors.reputational_impact
        )
        return min(1.0, business_risk)

    def _compute_action_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """Compute action-related risk."""
        action_risk = (
            0.5 * factors.action_reversibility + 0.3 * factors.action_aggressiveness + 0.2 * factors.action_scope
        )
        return min(1.0, action_risk)

    def _compute_compliance_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """Compute compliance/regulatory risk."""
        compliance_risk = 0.6 * factors.compliance_impact + 0.4 * factors.privacy_impact
        return min(1.0, compliance_risk)

    def _compute_environmental_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """Compute environmental risk (time, availability, etc.)."""
        environmental_risk = (
            0.5 * factors.time_of_day + 0.5 * (1.0 - factors.operator_availability)  # Low availability = high risk
        )
        return min(1.0, environmental_risk)

    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level."""
        if score >= self.CRITICAL_THRESHOLD:
            return RiskLevel.CRITICAL
        if score >= self.HIGH_THRESHOLD:
            return RiskLevel.HIGH
        if score >= self.MEDIUM_THRESHOLD:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _generate_justification(self, factors: RiskFactors, score: float, level: RiskLevel) -> tuple[str, list[str]]:
        """Generate human-readable justification for risk assessment."""
        concerns = []

        # Identify high-risk factors (>0.7)
        all_factors = factors.get_all_factors()
        for factor_name, factor_value in all_factors.items():
            if factor_value >= 0.7:
                concerns.append(f"{factor_name.replace('_', ' ').title()}: {factor_value:.1%}")

        # Generate justification
        if level == RiskLevel.CRITICAL:
            justification = (
                f"CRITICAL RISK (score={score:.2f}): Multiple high-risk factors identified. "
                f"Immediate executive oversight required."
            )
        elif level == RiskLevel.HIGH:
            justification = (
                f"HIGH RISK (score={score:.2f}): Significant risk factors present. Senior operator approval required."
            )
        elif level == RiskLevel.MEDIUM:
            justification = f"MEDIUM RISK (score={score:.2f}): Moderate risk. Operator review recommended."
        else:
            justification = f"LOW RISK (score={score:.2f}): Minimal risk factors. May proceed with supervision."

        return justification, concerns

    def _generate_mitigation_suggestions(self, factors: RiskFactors, context: DecisionContext) -> list[str]:
        """Generate risk mitigation suggestions."""
        suggestions = []

        if factors.threat_confidence < 0.7:
            suggestions.append("Collect additional threat intelligence before acting")

        if factors.asset_criticality >= 0.8:
            suggestions.append("Consider isolating critical assets during investigation")

        if factors.action_reversibility >= 0.7:
            suggestions.append("Backup data before executing irreversible action")

        if factors.compliance_impact >= 0.7:
            suggestions.append("Consult legal/compliance team before proceeding")

        if factors.operator_availability < 0.3:
            suggestions.append("Wait for operator availability or escalate immediately")

        return suggestions

    # Helper methods for factor assessment

    def _assess_threat_novelty(self, context: DecisionContext) -> float:
        """Assess if threat is novel/unknown (0=known, 1=novel)."""
        # Check if threat has similar past incidents
        if context.similar_past_decisions:
            return 0.2  # Known threat pattern
        if context.threat_type in ["zero_day", "unknown", "novel"]:
            return 0.9  # Novel threat
        return 0.5  # Moderately novel

    def _assess_asset_criticality(self, context: DecisionContext) -> float:
        """Assess criticality of affected assets."""
        criticality_map = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0,
        }
        return criticality_map.get(context.asset_criticality.lower(), 0.5)

    def _normalize_asset_count(self, count: int) -> float:
        """Normalize asset count to 0-1 scale."""
        # 1 asset = 0.1, 10 assets = 0.5, 100+ assets = 1.0
        if count <= 1:
            return 0.1
        if count <= 10:
            return 0.1 + (count - 1) * 0.044  # Linear 0.1 to 0.5
        if count <= 100:
            return 0.5 + (count - 10) * 0.0056  # Linear 0.5 to 1.0
        return 1.0

    def _assess_data_sensitivity(self, context: DecisionContext) -> float:
        """Assess sensitivity of data on affected assets."""
        # Check metadata for data classification
        data_class = context.metadata.get("data_classification", "internal")
        sensitivity_map = {
            "public": 0.0,
            "internal": 0.3,
            "confidential": 0.6,
            "restricted": 0.8,
            "top_secret": 1.0,
        }
        return sensitivity_map.get(data_class.lower(), 0.5)

    def _normalize_financial_impact(self, cost: float) -> float:
        """Normalize financial impact to 0-1 scale."""
        # $0 = 0.0, $10K = 0.3, $100K = 0.6, $1M+ = 1.0
        if cost <= 0:
            return 0.0
        if cost < 10000:
            return cost / 33333  # Linear 0 to 0.3
        if cost < 100000:
            return 0.3 + (cost - 10000) / 300000  # Linear 0.3 to 0.6
        if cost < 1000000:
            return 0.6 + (cost - 100000) / 2250000  # Linear 0.6 to 1.0
        return 1.0

    def _assess_operational_impact(self, context: DecisionContext) -> float:
        """Assess impact on business operations."""
        business_impact = context.business_impact.lower()
        if "critical" in business_impact or "severe" in business_impact:
            return 1.0
        if "high" in business_impact or "major" in business_impact:
            return 0.8
        if "moderate" in business_impact or "medium" in business_impact:
            return 0.5
        if "low" in business_impact or "minor" in business_impact:
            return 0.3
        return 0.5  # Default moderate

    def _assess_reputational_impact(self, context: DecisionContext) -> float:
        """Assess potential reputational damage."""
        # High for public-facing assets, data breaches
        if "public" in context.metadata.get("asset_type", ""):
            return 0.7
        if "customer_data" in context.metadata.get("data_type", ""):
            return 0.8
        return 0.3

    def _assess_action_scope(self, context: DecisionContext) -> float:
        """Assess scope of action (local=0.0, global=1.0)."""
        scope = context.action_params.get("scope", "local")
        if scope == "global":
            return 1.0
        if scope == "organization":
            return 0.8
        if scope == "department":
            return 0.5
        if scope == "host":
            return 0.2
        return 0.1  # Local/single entity

    def _assess_compliance_impact(self, context: DecisionContext) -> float:
        """Assess regulatory/compliance implications."""
        # Check for compliance tags
        compliance_tags = context.metadata.get("compliance_tags", [])
        if any(tag in compliance_tags for tag in ["hipaa", "gdpr", "pci-dss"]):
            return 0.9  # High compliance impact
        if compliance_tags:
            return 0.6  # Some compliance requirements
        return 0.2  # Minimal compliance impact

    def _assess_privacy_impact(self, context: DecisionContext) -> float:
        """Assess PII/privacy implications."""
        if "pii" in context.metadata.get("data_type", ""):
            return 0.9
        if "user_data" in context.metadata.get("data_type", ""):
            return 0.6
        return 0.2

    def _assess_time_of_day(self) -> float:
        """Assess risk based on time of day (higher risk outside business hours)."""
        from datetime import datetime

        hour = datetime.utcnow().hour
        # Business hours (9-17 UTC): low risk
        # Outside hours: higher risk due to reduced oversight
        if 9 <= hour < 17:
            return 0.2  # Business hours
        if 17 <= hour < 22 or 6 <= hour < 9:
            return 0.5  # Evening/early morning
        return 0.8  # Night (22-6)

    def _assess_operator_availability(self) -> float:
        """Assess operator availability (0=none, 1=full)."""
        # In production, this would check actual operator shifts/availability
        # For now, use time-based heuristic
        from datetime import datetime

        hour = datetime.utcnow().hour
        if 9 <= hour < 17:
            return 0.9  # Business hours
        if 17 <= hour < 22:
            return 0.6  # Evening shift
        return 0.3  # Night shift (limited)
