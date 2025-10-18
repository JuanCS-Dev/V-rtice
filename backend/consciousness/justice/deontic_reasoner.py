"""
Deontic Logic Reasoner

Implements deontic logic with constitutional rules from Vértice v2.7.
Evaluates obligations (O), permissions (P), and prohibitions (F) with strict enforcement
of Lei Zero (Transparency) and Lei I (Não Causar Danos).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class DeonticOperator(str, Enum):
    """Deontic operators for modal logic."""

    OBLIGATORY = "obligatory"  # O(φ) - Must do
    PERMITTED = "permitted"  # P(φ) - May do
    FORBIDDEN = "forbidden"  # F(φ) - Must not do


@dataclass
class DeonticRule:
    """
    Represents a deontic logic rule.

    Attributes:
        rule_id: Unique identifier
        operator: Deontic operator (obligatory, permitted, forbidden)
        proposition: The action or state being evaluated
        constitutional_basis: Which law this rule derives from
        priority: Priority level for conflict resolution (1-10)
        conditions: Optional conditions that must be met for rule to apply
        metadata: Additional metadata
    """

    rule_id: UUID
    operator: DeonticOperator
    proposition: str
    constitutional_basis: str
    priority: int
    conditions: Dict[str, any] = field(default_factory=dict)
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate priority range and operator type."""
        if not isinstance(self.priority, int):
            raise ValueError(f"Priority must be int, got {type(self.priority)}")
        if not 1 <= self.priority <= 10:
            raise ValueError(f"Priority must be 1-10, got {self.priority}")
        if not isinstance(self.operator, DeonticOperator):
            raise TypeError(f"operator must be DeonticOperator enum")


@dataclass
class ComplianceResult:
    """
    Result of compliance evaluation.

    Attributes:
        compliant: Whether the action is compliant
        applicable_rules: Rules that applied to this evaluation
        violations: Rules that were violated (if any)
        explanation: Human-readable explanation
        evaluated_at: Timestamp of evaluation
    """

    compliant: bool
    applicable_rules: List[DeonticRule]
    violations: List[DeonticRule] = field(default_factory=list)
    explanation: str = ""
    evaluated_at: datetime = field(default_factory=datetime.utcnow)


class DeonticReasoner:
    """
    Deontic logic reasoner with Vértice constitutional rules.

    Implements Lei Zero (Transparency) and Lei I (Não Causar Danos) as
    strict constitutional constraints. All actions are evaluated against
    these fundamental laws with automatic violation detection.
    """

    def __init__(self):
        """Initialize reasoner with constitutional rules."""
        self._rules: Dict[UUID, DeonticRule] = {}
        self._initialize_constitutional_rules()

    def _initialize_constitutional_rules(self):
        """Initialize Lei Zero and Lei I as immutable rules."""
        # Lei Zero: Transparência (Transparency)
        lei_zero_transparency = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.OBLIGATORY,
            proposition="log_all_decisions",
            constitutional_basis="Lei Zero: Transparência",
            priority=10,  # Highest priority
            metadata={"immutable": True, "constitutional": True}
        )

        lei_zero_auditability = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.OBLIGATORY,
            proposition="provide_decision_rationale",
            constitutional_basis="Lei Zero: Transparência",
            priority=10,
            metadata={"immutable": True, "constitutional": True}
        )

        lei_zero_data_provenance = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.OBLIGATORY,
            proposition="track_data_provenance",
            constitutional_basis="Lei Zero: Transparência",
            priority=10,
            metadata={"immutable": True, "constitutional": True}
        )

        # Lei I: Não Causar Danos (Do No Harm)
        lei_i_no_harm = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.FORBIDDEN,
            proposition="cause_physical_harm",
            constitutional_basis="Lei I: Não Causar Danos",
            priority=10,
            metadata={"immutable": True, "constitutional": True}
        )

        lei_i_no_psychological_harm = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.FORBIDDEN,
            proposition="cause_psychological_harm",
            constitutional_basis="Lei I: Não Causar Danos",
            priority=10,
            metadata={"immutable": True, "constitutional": True}
        )

        lei_i_no_economic_harm = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.FORBIDDEN,
            proposition="cause_economic_harm",
            constitutional_basis="Lei I: Não Causar Danos",
            priority=10,
            metadata={"immutable": True, "constitutional": True}
        )

        lei_i_escalate_uncertain = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.OBLIGATORY,
            proposition="escalate_when_uncertain_about_harm",
            constitutional_basis="Lei I: Não Causar Danos",
            priority=10,
            metadata={"immutable": True, "constitutional": True}
        )

        # Store constitutional rules
        for rule in [
            lei_zero_transparency,
            lei_zero_auditability,
            lei_zero_data_provenance,
            lei_i_no_harm,
            lei_i_no_psychological_harm,
            lei_i_no_economic_harm,
            lei_i_escalate_uncertain,
        ]:
            self._rules[rule.rule_id] = rule

    def add_rule(self, rule: DeonticRule) -> bool:
        """
        Add a new deontic rule.

        Constitutional rules cannot be removed or overridden.

        Args:
            rule: The rule to add

        Returns:
            True if added successfully, False if rejected
        """
        if rule.rule_id in self._rules:
            return False

        self._rules[rule.rule_id] = rule
        return True

    def remove_rule(self, rule_id: UUID) -> bool:
        """
        Remove a rule by ID.

        Constitutional rules (Lei Zero, Lei I) cannot be removed.

        Args:
            rule_id: ID of rule to remove

        Returns:
            True if removed, False if not found or immutable
        """
        if rule_id not in self._rules:
            return False

        rule = self._rules[rule_id]
        if rule.metadata.get("immutable", False):
            return False

        del self._rules[rule_id]
        return True

    def get_rule(self, rule_id: UUID) -> Optional[DeonticRule]:
        """
        Get a rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            Rule if found, None otherwise
        """
        return self._rules.get(rule_id)

    def get_constitutional_rules(self) -> List[DeonticRule]:
        """
        Get all constitutional rules (Lei Zero, Lei I).

        Returns:
            List of constitutional rules
        """
        return [
            rule
            for rule in self._rules.values()
            if rule.metadata.get("constitutional", False)
        ]

    def check_compliance(
        self, action: str, context: Optional[Dict[str, any]] = None
    ) -> ComplianceResult:
        """
        Check if an action complies with deontic rules.

        Args:
            action: The action being evaluated
            context: Optional context for evaluation

        Returns:
            ComplianceResult with compliance status and violations
        """
        context = context or {}
        applicable_rules = self._find_applicable_rules(action, context)

        if not applicable_rules:
            # No rules apply - action is permitted by default
            return ComplianceResult(
                compliant=True,
                applicable_rules=[],
                violations=[],
                explanation=f"No rules apply to '{action}' - permitted by default"
            )

        # Check for violations
        violations = []
        for rule in applicable_rules:
            if rule.operator == DeonticOperator.FORBIDDEN:
                violations.append(rule)
            elif rule.operator == DeonticOperator.OBLIGATORY:
                # Check if obligation is being met
                if not context.get(f"fulfills_{rule.proposition}", False):
                    violations.append(rule)

        if violations:
            explanations = [
                f"Violates {v.constitutional_basis}: {v.proposition}"
                for v in violations
            ]
            return ComplianceResult(
                compliant=False,
                applicable_rules=applicable_rules,
                violations=violations,
                explanation="; ".join(explanations)
            )

        return ComplianceResult(
            compliant=True,
            applicable_rules=applicable_rules,
            violations=[],
            explanation=f"Action '{action}' complies with all applicable rules"
        )

    def _find_applicable_rules(
        self, action: str, context: Dict[str, any]
    ) -> List[DeonticRule]:
        """
        Find rules that apply to an action.

        Args:
            action: The action being evaluated
            context: Evaluation context

        Returns:
            List of applicable rules sorted by priority (descending)
        """
        applicable = []

        for rule in self._rules.values():
            # Check if proposition matches action
            if rule.proposition in action or action in rule.proposition:
                # Check if conditions are met
                conditions_met = True
                for key, value in rule.conditions.items():
                    if context.get(key) != value:
                        conditions_met = False
                        break

                if conditions_met:
                    applicable.append(rule)

        # Sort by priority (highest first)
        return sorted(applicable, key=lambda r: r.priority, reverse=True)

    def evaluate_obligation(self, proposition: str) -> bool:
        """
        Check if a proposition is obligatory.

        Args:
            proposition: The proposition to evaluate

        Returns:
            True if obligatory, False otherwise
        """
        for rule in self._rules.values():
            if (
                rule.proposition == proposition
                and rule.operator == DeonticOperator.OBLIGATORY
            ):
                return True
        return False

    def evaluate_permission(self, proposition: str) -> bool:
        """
        Check if a proposition is permitted.

        A proposition is permitted if it's explicitly permitted OR
        if it's not forbidden (open world assumption).

        Args:
            proposition: The proposition to evaluate

        Returns:
            True if permitted, False if forbidden
        """
        # Check for explicit permission
        for rule in self._rules.values():
            if (
                rule.proposition == proposition
                and rule.operator == DeonticOperator.PERMITTED
            ):
                return True

        # Check for prohibition
        for rule in self._rules.values():
            if (
                rule.proposition == proposition
                and rule.operator == DeonticOperator.FORBIDDEN
            ):
                return False

        # Open world: if not forbidden, it's permitted
        return True

    def evaluate_prohibition(self, proposition: str) -> bool:
        """
        Check if a proposition is forbidden.

        Args:
            proposition: The proposition to evaluate

        Returns:
            True if forbidden, False otherwise
        """
        for rule in self._rules.values():
            if (
                rule.proposition == proposition
                and rule.operator == DeonticOperator.FORBIDDEN
            ):
                return True
        return False

    def __repr__(self) -> str:
        """String representation."""
        return f"DeonticReasoner(rules={len(self._rules)})"
