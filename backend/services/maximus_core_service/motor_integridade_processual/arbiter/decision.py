"""Decision Arbiter - Final decision formatting and justification."""

from motor_integridade_processual.models.verdict import EthicalVerdict, DecisionLevel
from motor_integridade_processual.models.action_plan import ActionPlan

class DecisionArbiter:
    """Formats and validates final decisions."""
    
    def finalize_verdict(self, verdict: EthicalVerdict, plan: ActionPlan) -> EthicalVerdict:
        """Validate and finalize verdict."""
        # Ensure decision is justified
        if not verdict.primary_reason or len(verdict.primary_reason) < 10:
            verdict.primary_reason = f"Decision: {verdict.final_decision.value} (score: {verdict.aggregate_score:.2f})"
        
        return verdict
    
    def format_explanation(self, verdict: EthicalVerdict) -> str:
        """Generate human-readable explanation."""
        return f"{verdict.final_decision.value}: {verdict.primary_reason} (confidence: {verdict.confidence:.0%})"
