"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - CBR Validators
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: justice/validators.py
Purpose: Constitutional validators for CBR revise step

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-15)

DOUTRINA:
├─ Lei Zero: Precedentes promovem florescimento (não eficiência)
├─ Lei I: Precedentes minoritários têm mesmo peso
└─ Padrão Pagani: Validação constitucional obrigatória

INTEGRATION:
└─ Used by CBR Engine in revise step to validate precedent suggestions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from typing import Dict, Any, List


class ConstitutionalValidator:
    """Validates CBR suggestions against Constituição Vértice.

    Implements constitutional checks to ensure precedent-based decisions
    comply with fundamental ethical laws.
    """

    # Prohibited actions that violate Lei I (Ovelha Perdida)
    LEI_I_VIOLATIONS = [
        "sacrifice",
        "harm_minority",
        "exploit",
        "abandon",
        "ignore_vulnerable",
    ]

    # Actions requiring special scrutiny under Lei Zero (Florescimento)
    LEI_ZERO_HIGH_STAKES = [
        "life_death",
        "irreversible",
        "large_scale",
        "systemic_change",
    ]

    async def validate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Validate action against constitutional constraints.

        Args:
            action: Dictionary with action details (action_type, objective, etc.)

        Returns:
            {
                "valid": bool,
                "violations": List[str],  # Empty if valid
                "warnings": List[str],    # Non-blocking concerns
                "constraints": Dict[str, Any]  # Applied constraints
            }
        """
        violations = []
        warnings = []
        constraints = {}

        action_type = action.get("action_type", "unknown").lower()
        objective = action.get("objective", "").lower()

        # Check Lei I violations (BLOCKING)
        for forbidden in self.LEI_I_VIOLATIONS:
            if forbidden in action_type or forbidden in objective:
                violations.append(f"lei_i_violation: {forbidden}")

        # Check for deceptive actions (Lei I: transparency)
        deceptive_keywords = ["deception", "deceive", "mislead", "lie", "fake"]
        if any(kw in action_type or kw in objective for kw in deceptive_keywords):
            violations.append("lei_i_violation: deceptive_action")

        # Check for coercive actions (Lei I: autonomy)
        coercive_keywords = ["coerce", "coercion", "force", "compel", "pressure"]
        if any(kw in action_type or kw in objective for kw in coercive_keywords):
            violations.append("lei_i_violation: coercive_action")

        # Check Lei Zero high-stakes scenarios (WARNING)
        for high_stake in self.LEI_ZERO_HIGH_STAKES:
            if high_stake in action_type or high_stake in objective:
                warnings.append(f"lei_zero_warning: high_stakes_{high_stake}")
                constraints["requires_human_oversight"] = True

        # Check for self-referential actions (halting problem)
        if self._is_self_referential(action):
            violations.append("self_reference_violation: halting_problem")

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "constraints": constraints,
        }

    def _is_self_referential(self, action: Dict[str, Any]) -> bool:
        """Check if action references MIP itself.

        Self-referential actions create halting problem and are rejected.
        """
        objective = action.get("objective", "").lower()
        action_type = action.get("action_type", "").lower()

        mip_keywords = ["mip", "motor", "integridade", "ethical_evaluation"]
        eval_keywords = ["evaluate", "assess", "judge", "decide"]

        has_mip_ref = any(kw in objective or kw in action_type for kw in mip_keywords)
        has_eval_ref = any(kw in objective or kw in action_type for kw in eval_keywords)

        return has_mip_ref and has_eval_ref


class RiskLevelValidator:
    """Validates risk levels of precedent-based actions.

    Ensures CBR suggestions don't recommend high-risk actions without
    proper safeguards.
    """

    MAX_ALLOWED_RISK = 0.8  # 80% risk threshold

    async def validate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Validate action risk level.

        Args:
            action: Dictionary with action details

        Returns:
            Validation result (same format as ConstitutionalValidator)
        """
        violations = []
        warnings = []
        constraints = {}

        risk_level = action.get("risk_level", 0.0)

        if risk_level > self.MAX_ALLOWED_RISK:
            violations.append(f"excessive_risk: {risk_level:.2f} > {self.MAX_ALLOWED_RISK}")
            constraints["requires_human_approval"] = True

        elif risk_level > 0.5:
            warnings.append(f"moderate_risk: {risk_level:.2f}")
            constraints["requires_monitoring"] = True

        # Check if action is reversible
        if not action.get("reversible", True) and risk_level > 0.3:
            warnings.append("irreversible_action_with_moderate_risk")
            constraints["requires_documentation"] = True

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "constraints": constraints,
        }


class CompositeValidator:
    """Composite validator that chains multiple validators.

    Used to run constitutional + risk validation in sequence.
    """

    def __init__(self, validators: List[Any]):
        """Initialize composite validator.

        Args:
            validators: List of validator instances
        """
        self.validators = validators

    async def validate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Run all validators and aggregate results.

        Args:
            action: Action to validate

        Returns:
            Aggregated validation result
        """
        all_violations = []
        all_warnings = []
        all_constraints = {}

        for validator in self.validators:
            result = await validator.validate(action)

            all_violations.extend(result.get("violations", []))
            all_warnings.extend(result.get("warnings", []))
            all_constraints.update(result.get("constraints", {}))

        return {
            "valid": len(all_violations) == 0,
            "violations": all_violations,
            "warnings": all_warnings,
            "constraints": all_constraints,
        }


# Factory function for creating default validator stack
def create_default_validators() -> List[Any]:
    """Create default validator stack for CBR.

    Returns:
        List of validator instances (Constitutional + Risk)
    """
    return [
        ConstitutionalValidator(),
        RiskLevelValidator(),
    ]
