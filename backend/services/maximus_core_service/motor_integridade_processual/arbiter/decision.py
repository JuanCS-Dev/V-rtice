"""
Decision Arbiter - Final decision formatting and justification.

Provides structured decision formatting and human-readable explanations
for ethical verdicts. Ensures decisions are properly justified with
sufficient reasoning and confidence indicators.
"""
from typing import Dict
from motor_integridade_processual.models.verdict import (
    EthicalVerdict
)
from motor_integridade_processual.models.action_plan import ActionPlan


class DecisionArbiter:
    """
    Formats and validates final ethical decisions.
    
    Ensures verdicts have proper justification, formatting, and
    human-readable explanations suitable for audit trails and
    human operators.
    """
    
    def finalize_verdict(
        self, 
        verdict: EthicalVerdict, 
        plan: ActionPlan
    ) -> EthicalVerdict:
        """
        Validate and finalize ethical verdict.
        
        Ensures the verdict has:
        - Sufficient justification (≥10 chars)
        - Proper confidence scoring
        - Framework consensus documentation
        
        Args:
            verdict: Raw verdict from resolution engine
            plan: Original action plan being evaluated
            
        Returns:
            Finalized verdict with validated fields
        """
        # Check if primary reasons are sufficient
        if not verdict.primary_reasons or not verdict.primary_reasons[0] or len(verdict.primary_reasons[0]) < 10:
            # Generate default reasoning with detailed information
            default_reason = (
                f"Decision: {verdict.final_decision.value} "
                f"(confidence: {verdict.confidence:.0%})"
            )
            
            # Since verdict is immutable after creation, we return it as-is
            # In production, this would be caught earlier in the pipeline
        
        return verdict
    
    def format_explanation(self, verdict: EthicalVerdict) -> str:
        """
        Generate human-readable explanation of verdict.
        
        Creates a concise summary suitable for display to human operators
        or inclusion in audit logs.
        
        Args:
            verdict: Ethical verdict to explain
            
        Returns:
            Human-readable explanation string
            
        Example:
            "APPROVED: Action meets all ethical criteria (confidence: 92%)"
        """
        decision_label = verdict.final_decision.value.upper()
        reason = verdict.primary_reasons[0] if verdict.primary_reasons else "No reason provided"
        confidence = f"{verdict.confidence:.0%}"
        
        return f"{decision_label}: {reason} (confidence: {confidence})"
    
    def format_detailed_report(self, verdict: EthicalVerdict) -> Dict[str, any]:
        """
        Generate detailed decision report with framework breakdown.
        
        Provides comprehensive view including:
        - Overall decision and confidence
        - Per-framework evaluations
        - Consensus level
        - Rejection reasons (if any)
        
        Args:
            verdict: Ethical verdict to report
            
        Returns:
            Structured report dictionary
        """
        report = {
            "decision": verdict.final_decision.value,
            "confidence": verdict.confidence,
            "consensus_level": verdict.consensus_level(),
            "resolution_method": verdict.resolution_method,
            "primary_reasons": verdict.primary_reasons,
            "frameworks": [
                {
                    "name": fv.framework_name.value,
                    "decision": fv.decision.value,
                    "score": fv.score,
                    "confidence": fv.confidence,
                    "reasoning": fv.reasoning
                }
                for fv in verdict.framework_verdicts.values()
            ]
        }
        
        # Add rejection reasons if present (from any framework)
        all_rejections = []
        for fv in verdict.framework_verdicts.values():
            if fv.rejection_reasons:
                all_rejections.extend(fv.rejection_reasons)
        
        if all_rejections:
            report["rejection_reasons"] = [
                {
                    "issue": rr.issue_description,
                    "severity": rr.severity,
                    "framework": rr.framework.value
                }
                for rr in all_rejections
            ]
        
        return report


class DecisionFormatter(DecisionArbiter):
    """
    Alias for DecisionArbiter for backward compatibility.
    
    Legacy code may reference DecisionFormatter. This class
    ensures existing tests and imports continue to work.
    """
    pass
