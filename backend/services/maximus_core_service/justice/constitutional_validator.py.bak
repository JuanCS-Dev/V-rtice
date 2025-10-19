"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Constitutional Validator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: justice/constitutional_validator.py
Purpose: Enforcement of Constituição Vértice v2.7

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-14)

DOUTRINA:
├─ Lei Zero (∞): Imperativo do Florescimento Humano
├─ Lei I (∞-1): Axioma da Ovelha Perdida
└─ This is a GATE, not an advisor - blocks violations

INTEGRATION:
└─ Decision Flow: Stimulus → ToM → MIP → CBR → DDL → [VALIDATOR] → Action
                                                        ↑
                                                 BLOCKS if violation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ViolationLevel(Enum):
    """Severity levels for constitutional violations.

    Priority ordering (highest to lowest):
    - CRITICAL: Emergency stop + HITL escalation
    - HIGH: Block action + require human approval
    - MEDIUM: Warning + log + allow with oversight
    - LOW: Log only, monitor
    - NONE: No violation detected
    """
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ViolationType(Enum):
    """Types of constitutional violations."""
    LEI_ZERO = "lei_zero"              # Violates human flourishing
    LEI_I = "lei_i"                    # Abandons vulnerable for utility
    DIGNITY = "dignity"                # Violates human dignity
    AUTONOMY = "autonomy"              # Reduces autonomy without consent
    JUSTICE = "justice"                # Unjust distribution
    TRANSPARENCY = "transparency"      # Lacks explainability
    SAFETY = "safety"                  # Unsafe action


@dataclass
class ViolationReport:
    """Structured report of constitutional violation.

    This is returned by ConstitutionalValidator.validate_action()
    and contains all information needed to decide whether to block,
    escalate, or allow an action.
    """
    level: ViolationLevel
    violation_type: Optional[ViolationType]
    violated_law: str                  # "Lei Zero", "Lei I", "Artigo X"
    description: str                   # Human-readable explanation
    action: Dict[str, Any]            # The action being validated
    context: Dict[str, Any]           # Context information
    recommendation: str                # "PROCEED", "BLOCK", "ESCALATE", "STOP"
    evidence: List[str]               # Evidence of violation

    def is_blocking(self) -> bool:
        """Returns True if this violation should block execution.

        HIGH and CRITICAL violations block execution.
        MEDIUM and LOW violations allow execution with monitoring.
        """
        return self.level in [ViolationLevel.HIGH, ViolationLevel.CRITICAL]

    def requires_emergency_stop(self) -> bool:
        """Returns True if this triggers emergency circuit breaker.

        Only CRITICAL violations trigger emergency procedures:
        - Immediate halt of all pending actions
        - HITL escalation
        - Entry into safe mode
        """
        return self.level == ViolationLevel.CRITICAL


class ConstitutionalValidator:
    """Validates actions against Constituição Vértice v2.7.

    This is the final gate before action execution. All critical decisions
    must pass constitutional validation.

    Priority hierarchy:
    1. Lei Zero (∞): Imperativo do Florescimento Humano
    2. Lei I (∞-1): Axioma da Ovelha Perdida
    3. Other constitutional principles

    Example usage:
        validator = ConstitutionalValidator()

        action = {
            "type": "resource_allocation",
            "decision": "prioritize_majority",
            "affected": {"vulnerable": 1, "general": 100}
        }

        context = {
            "vulnerable_affected": True,
            "scenario": "healthcare_triage"
        }

        verdict = validator.validate_action(action, context)

        if verdict.is_blocking():
            raise ConstitutionalViolation(verdict)
    """

    def __init__(self):
        """Initialize constitutional validator."""
        self.violation_count = 0
        self.critical_violations = []
        self.lei_i_violations = []
        self.total_validations = 0

    def validate_action(
        self,
        action: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ViolationReport:
        """Validates action against constitutional principles.

        Args:
            action: The action to validate (e.g., MIP decision, DDL output)
                Expected fields:
                - type: str - Action type
                - decision: str - Decision made
                - justification: str - Reasoning
                - affected: dict - Who/what is affected

            context: Context information (optional)
                Expected fields:
                - vulnerable_affected: bool
                - informed_consent: bool
                - scenario: str

        Returns:
            ViolationReport with level, type, and recommendation
        """
        self.total_validations += 1

        if context is None:
            context = {}

        # Check Lei Zero (priority: ∞)
        lei_zero_violation = self._check_lei_zero(action, context)
        if lei_zero_violation:
            self._record_violation(lei_zero_violation)
            return lei_zero_violation

        # Check Lei I (priority: ∞-1) - MOST CRITICAL FOR MAXIMUS
        lei_i_violation = self._check_lei_i(action, context)
        if lei_i_violation:
            self._record_violation(lei_i_violation)
            return lei_i_violation

        # Check other constitutional principles
        # NOTE: Currently returns None (stub for future expansion).
        # When implemented, violations will be recorded and returned here.
        self._check_other_principles(action, context)

        # No violations detected
        logger.info(f"Action passed constitutional validation: {action.get('type', 'unknown')}")
        return ViolationReport(
            level=ViolationLevel.NONE,
            violation_type=None,
            violated_law="None",
            description="Action complies with constitutional principles",
            action=action,
            context=context,
            recommendation="PROCEED",
            evidence=[]
        )

    def _check_lei_zero(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[ViolationReport]:
        """Check Lei Zero: Imperativo do Florescimento Humano.

        Lei Zero establishes human flourishing as the supreme imperative.

        Red flags:
        - Direct harm to vulnerable populations
        - Reduction of autonomy without consent
        - Violation of human dignity (Kantian means-only treatment)
        - Permanent damage to human potential
        """
        evidence = []

        # Check for direct harm
        if action.get("causes_harm"):
            harm_type = action.get("harm_type")
            if harm_type in ["permanent", "severe", "dignity_violation"]:
                evidence.append(f"Action causes {harm_type} harm")

        # Check for autonomy violation
        if action.get("reduces_autonomy"):
            if not context.get("informed_consent"):
                evidence.append("Reduces autonomy without informed consent")

        # Check for dignity violation (Kantian categorical imperative)
        if action.get("treats_as_means"):
            if not action.get("also_treats_as_end"):
                evidence.append("Treats humans as means only (Kantian violation)")

        # Check for permanent potential damage
        if action.get("damages_potential"):
            if action.get("permanent"):
                evidence.append("Causes permanent damage to human potential")

        if evidence:
            return ViolationReport(
                level=ViolationLevel.CRITICAL,
                violation_type=ViolationType.LEI_ZERO,
                violated_law="Lei Zero - Imperativo do Florescimento Humano",
                description=(
                    "Action hinders human flourishing. "
                    "Lei Zero requires all actions to promote or at minimum preserve "
                    "the conditions for human development and well-being."
                ),
                action=action,
                context=context,
                recommendation="STOP",
                evidence=evidence
            )

        return None

    def _check_lei_i(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[ViolationReport]:
        """Check Lei I: Axioma da Ovelha Perdida.

        Lei I: "Nenhuma otimização utilitarista justifica o abandono de um vulnerável."
        Translation: "No utilitarian optimization justifies abandoning a vulnerable person."

        This is MAXIMUS's core ethical commitment.

        Red flags:
        - Utilitarian optimization that abandons vulnerable
        - "Greater good" justifies harm to minority
        - Efficiency prioritized over individual welfare
        - Sacrifice of vulnerable for majority benefit

        Classic violations:
        - Trolley problem: Sacrifice 1 to save 5 (if 1 is vulnerable)
        - Resource allocation: Deny care to elderly to save young
        - Triage: Abandon low-priority patients for efficiency
        """
        evidence = []

        # Detect utilitarian optimization
        is_utilitarian = (
            action.get("type") in ["utilitarian_optimization", "cost_benefit", "maximize_utility"]
            or action.get("justification") == "greater_good"
            or "maximize" in str(action.get("type", "")).lower()
            or "maximize" in str(action.get("decision", "")).lower()
            or "maximize" in str(action.get("justification", "")).lower()
            or "utility" in str(action.get("justification", "")).lower()
            or ("save" in str(action.get("justification", "")).lower() and "sacrifice" in str(action.get("decision", "")).lower())
        )

        # Detect vulnerable affected
        vulnerable_affected = (
            context.get("vulnerable_affected")
            or context.get("affects_minority")
            or action.get("sacrifice_target") in ["elderly", "disabled", "minority", "vulnerable"]
            or action.get("target") in ["elderly_patients", "disabled_patients", "minority"]
        )

        # Detect abandonment or sacrifice
        is_abandonment = (
            action.get("abandons")
            or action.get("denies_care")
            or action.get("deprioritizes")
            or action.get("sacrifice_target") is not None
            or "sacrifice" in str(action.get("type", "")).lower()
            or "sacrifice" in str(action.get("decision", "")).lower()
            or "abandon" in str(action.get("decision", "")).lower()
            or "deny" in str(action.get("decision", "")).lower()
            or "deprioritize" in str(action.get("decision", "")).lower()
        )

        # LEI I VIOLATION: Utilitarian + Vulnerable + Abandonment
        if is_utilitarian and vulnerable_affected and is_abandonment:
            evidence.append("Utilitarian optimization detected")
            evidence.append("Vulnerable population affected")
            evidence.append("Action abandons or sacrifices vulnerable individual(s)")

            # Get affected counts for context
            affected = action.get("affected", {})
            vulnerable_count = affected.get("vulnerable", context.get("vulnerable_count", "unknown"))
            majority_count = affected.get("general", context.get("majority_count", "unknown"))

            if vulnerable_count != "unknown" and majority_count != "unknown":
                evidence.append(f"Affects {vulnerable_count} vulnerable vs {majority_count} general")

            # Add specific justification if provided
            justification = action.get("justification")
            if justification:
                evidence.append(f"Justification given: '{justification}'")

            return ViolationReport(
                level=ViolationLevel.CRITICAL,
                violation_type=ViolationType.LEI_I,
                violated_law="Lei I - Axioma da Ovelha Perdida",
                description=(
                    "Action violates Lei I by abandoning vulnerable for utilitarian optimization. "
                    "No 'greater good' justification is acceptable when it requires sacrificing "
                    "or abandoning a vulnerable individual. The vulnerable must never be treated "
                    "as acceptable losses in cost-benefit calculations."
                ),
                action=action,
                context=context,
                recommendation="STOP",
                evidence=evidence
            )

        # Edge case: Utilitarian without vulnerable (allowed but monitored)
        if is_utilitarian and not vulnerable_affected:
            return ViolationReport(
                level=ViolationLevel.LOW,
                violation_type=None,
                violated_law="None (monitored)",
                description=(
                    "Utilitarian optimization detected without vulnerable affected. "
                    "This is acceptable but will be monitored to ensure no indirect harm to vulnerable populations."
                ),
                action=action,
                context=context,
                recommendation="PROCEED",
                evidence=["Utilitarian optimization without vulnerable impact"]
            )

        return None

    def _check_other_principles(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[ViolationReport]:
        """Check other constitutional principles.

        Additional checks beyond Lei Zero and Lei I:
        - Dignity (additional Kantian checks)
        - Justice (Rawlsian fairness)
        - Transparency (explainability)
        - Safety (risk assessment)

        Currently stub - can be expanded as needed.
        """
        # Placeholder for future expansion
        return None

    def _record_violation(self, violation: ViolationReport):
        """Record violation for audit and metrics.

        Maintains internal state for:
        - Total violation count
        - Critical violations list
        - Lei I violations list

        Also logs violations at appropriate severity levels.
        """
        self.violation_count += 1

        if violation.level == ViolationLevel.CRITICAL:
            self.critical_violations.append(violation)
            logger.critical("=" * 80)
            logger.critical(f"CRITICAL CONSTITUTIONAL VIOLATION: {violation.violated_law}")
            logger.critical(f"Description: {violation.description}")
            logger.critical(f"Evidence: {violation.evidence}")
            logger.critical(f"Recommendation: {violation.recommendation}")
            logger.critical("=" * 80)

        if violation.violation_type == ViolationType.LEI_I:
            self.lei_i_violations.append(violation)
            logger.error(f"LEI I VIOLATION DETECTED: {violation.description}")
            logger.error(f"Evidence: {violation.evidence}")

        logger.warning(
            f"Constitutional violation recorded: "
            f"Level={violation.level.name}, "
            f"Type={violation.violation_type.value if violation.violation_type else 'None'}, "
            f"Law={violation.violated_law}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Return validator metrics for monitoring.

        Returns:
            Dictionary with:
            - total_validations: Total actions validated
            - total_violations: Total violations detected
            - critical_violations: Count of CRITICAL violations
            - lei_i_violations: Count of Lei I violations
            - violation_rate: Percentage of actions that violate
        """
        violation_rate = (
            (self.violation_count / self.total_validations * 100)
            if self.total_validations > 0
            else 0.0
        )

        return {
            "total_validations": self.total_validations,
            "total_violations": self.violation_count,
            "critical_violations": len(self.critical_violations),
            "lei_i_violations": len(self.lei_i_violations),
            "violation_rate": round(violation_rate, 2)
        }

    def reset_metrics(self):
        """Reset metrics (for testing or new deployment)."""
        self.violation_count = 0
        self.critical_violations = []
        self.lei_i_violations = []
        self.total_validations = 0


class ConstitutionalViolation(Exception):
    """Exception raised when action violates constitutional principles.

    This should be raised by calling code when validator returns
    a blocking violation.

    Example:
        verdict = validator.validate_action(action, context)
        if verdict.is_blocking():
            raise ConstitutionalViolation(verdict)
    """

    def __init__(self, report: ViolationReport):
        """Initialize exception with violation report.

        Args:
            report: ViolationReport from validator
        """
        self.report = report
        super().__init__(
            f"{report.violated_law}: {report.description} "
            f"(Level: {report.level.name}, Evidence: {report.evidence})"
        )
