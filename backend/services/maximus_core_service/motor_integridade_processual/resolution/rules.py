"""
Ethical Resolution Rules.

Defines precedence rules and meta-ethical principles for conflict resolution.

Lei Governante: Constituição Vértice v2.6
"""

from typing import Dict, Any
from motor_integridade_processual.models.action_plan import ActionPlan


class ResolutionRules:
    """
    Meta-ethical rules for conflict resolution.
    
    Implements constitutional rules and precedence logic.
    """
    
    @staticmethod
    def kantian_has_veto_power() -> bool:
        """
        Kantian framework has absolute veto power.
        
        Lei I: Vida consciente tem valor infinito - não pode ser meio.
        """
        return True
    
    @staticmethod
    def get_framework_precedence() -> Dict[str, int]:
        """
        Get framework precedence order.
        
        Returns:
            Dict mapping framework name to precedence level (higher = more important)
        """
        return {
            "Kantian": 4,  # Highest - categorical imperatives
            "Principialism": 3,  # Medical ethics - do no harm
            "Utilitarian": 2,  # Consequences matter
            "Virtue": 1  # Character assessment
        }
    
    @staticmethod
    def apply_constitutional_constraints(plan: ActionPlan) -> Dict[str, Any]:
        """
        Apply Constituição Vértice constraints.
        
        Returns:
            Dict with constraint results
        """
        constraints = {}
        
        # Lei I: Ovelha Perdida - Protect vulnerable
        if plan.affects_life_death:
            constraints["lei_i_applies"] = True
            constraints["requires_maximum_protection"] = True
        
        # Lei Zero: Florescimento
        if plan.is_high_stakes:
            constraints["lei_zero_applies"] = True
            constraints["must_actively_promote_welfare"] = True
        
        # Lei II: Risco Controlado
        high_risk_steps = [s for s in plan.steps if s.risk_level > 0.7]
        if high_risk_steps:
            constraints["lei_ii_applies"] = True
            constraints["high_risk_steps_count"] = len(high_risk_steps)
        
        return constraints
    
    @staticmethod
    def check_self_reference(plan: ActionPlan) -> bool:
        """
        Check if plan references the MIP itself (halting problem).
        
        Self-referential plans are automatically rejected.
        """
        objective_lower = plan.objective.lower()
        mip_keywords = ["mip", "motor", "integridade", "ethical", "evaluate"]
        
        # If objective mentions evaluation AND MIP
        eval_refs = sum(1 for kw in ["evaluate", "assess", "judge"] if kw in objective_lower)
        mip_refs = any(kw in objective_lower for kw in ["mip", "motor", "integridade"])
        
        return eval_refs >= 1 and mip_refs
    
    @staticmethod
    def get_context_weights(plan: ActionPlan) -> Dict[str, float]:
        """
        Adjust framework weights based on context.
        
        Args:
            plan: Action plan being evaluated
            
        Returns:
            Adjusted weights
        """
        weights = {
            "Kantian": 0.40,
            "Utilitarian": 0.30,
            "Virtue": 0.20,
            "Principialism": 0.10
        }
        
        # Medical/health context: Boost principialism
        if "health" in plan.objective.lower() or "medical" in plan.objective.lower():
            weights["Principialism"] += 0.10
            weights["Utilitarian"] -= 0.10
        
        # Life-death: Boost Kantian
        if plan.affects_life_death:
            weights["Kantian"] += 0.10
            weights["Virtue"] -= 0.10
        
        # Large-scale impact: Boost utilitarian
        if plan.population_affected > 100:
            weights["Utilitarian"] += 0.10
            weights["Virtue"] -= 0.10
        
        # Normalize to sum 1.0
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
