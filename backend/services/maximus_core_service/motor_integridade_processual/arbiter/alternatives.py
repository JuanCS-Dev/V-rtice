"""
Alternative suggestion engine.

Generates ethical alternatives for action plans that were rejected
or received low ethical scores. Suggests modifications to improve
alignment with ethical frameworks.
"""
from typing import List, Optional
from copy import deepcopy
from motor_integridade_processual.models.action_plan import (
    ActionPlan, 
    ActionStep
)
from motor_integridade_processual.models.verdict import (
    EthicalVerdict,
    RejectionReason
)


class AlternativeGenerator:
    """
    Generates ethical alternatives to improve action plans.
    
    Analyzes rejected or low-scoring plans and suggests specific
    modifications to address ethical concerns raised by frameworks.
    """
    
    def __init__(self, min_score_threshold: float = 0.6):
        """
        Initialize alternative generator.
        
        Args:
            min_score_threshold: Minimum score to not trigger alternatives
        """
        self.min_score_threshold = min_score_threshold
    
    def suggest_alternatives(
        self, 
        plan: ActionPlan, 
        verdict: Optional[EthicalVerdict] = None
    ) -> List[str]:
        """
        Generate alternative suggestions for action plan.
        
        Analyzes plan steps and identifies ethical improvements:
        - Remove deception → add transparency
        - Reduce coercion → add voluntary consent
        - Lower risk → add safeguards
        - Add stakeholder consideration
        
        Args:
            plan: Action plan to improve
            verdict: Optional verdict with rejection reasons
            
        Returns:
            List of human-readable suggestions (max 10)
        """
        suggestions = []
        
        # Analyze each step
        for step in plan.steps:
            suggestions.extend(self._analyze_step(step))
        
        # Add verdict-specific suggestions from framework verdicts
        if verdict and verdict.framework_verdicts:
            for fw_verdict in verdict.framework_verdicts.values():
                if fw_verdict.rejection_reasons:
                    for reason in fw_verdict.rejection_reasons:
                        suggestions.append(self._suggestion_from_rejection(reason))
        
        # Deduplicate and limit
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:10]
    
    def generate_modified_plans(
        self, 
        plan: ActionPlan, 
        verdict: EthicalVerdict
    ) -> List[ActionPlan]:
        """
        Generate concrete alternative action plans.
        
        Creates new ActionPlan instances with specific modifications
        applied to address ethical concerns.
        
        Args:
            plan: Original plan
            verdict: Verdict with rejection reasons
            
        Returns:
            List of modified ActionPlan alternatives (max 3)
        """
        alternatives = []
        
        # Alternative 1: Remove deception
        if any(step.involves_deception for step in plan.steps):
            alt1 = self._remove_deception(plan)
            alternatives.append(alt1)
        
        # Alternative 2: Add consent steps
        if any(step.involves_coercion for step in plan.steps):
            alt2 = self._add_consent_steps(plan)
            alternatives.append(alt2)
        
        # Alternative 3: Reduce risk
        if any(step.risk_level > 0.7 for step in plan.steps):
            alt3 = self._reduce_risk(plan)
            alternatives.append(alt3)
        
        return alternatives[:3]
    
    def _analyze_step(self, step: ActionStep) -> List[str]:
        """Analyze single step for improvement suggestions."""
        suggestions = []
        
        if step.involves_deception:
            suggestions.append(
                f"Step '{step.description[:40]}...': Replace deceptive action "
                "with transparent communication"
            )
        
        if step.involves_coercion:
            suggestions.append(
                f"Step '{step.description[:40]}...': Obtain voluntary informed "
                "consent instead of coercion"
            )
        
        if step.risk_level and step.risk_level > 0.7:
            suggestions.append(
                f"Step '{step.description[:40]}...': Reduce risk level from "
                f"{step.risk_level:.0%} by adding safeguards or alternative methods"
            )
        
        if not step.reversible:
            suggestions.append(
                f"Step '{step.description[:40]}...': Make action reversible "
                "or add contingency plan"
            )
        
        if not step.affected_stakeholders:
            suggestions.append(
                f"Step '{step.description[:40]}...': Identify and document "
                "all affected stakeholders"
            )
        
        return suggestions
    
    def _suggestion_from_rejection(self, reason: RejectionReason) -> str:
        """Convert rejection reason to actionable suggestion."""
        framework = reason.framework
        issue = reason.issue_description
        severity = reason.severity
        
        severity_label = "CRITICAL" if severity >= 0.8 else "HIGH" if severity >= 0.6 else "MODERATE"
        
        return (
            f"[{severity_label}] {framework}: {issue}. "
            "Consider redesigning this aspect of the plan."
        )
    
    def _remove_deception(self, plan: ActionPlan) -> ActionPlan:
        """Create alternative plan removing deceptive steps."""
        new_plan = deepcopy(plan)
        new_plan.objective = f"{plan.objective} (transparent version)"
        
        for step in new_plan.steps:
            if step.involves_deception:
                step.involves_deception = False
                step.deception_details = None
                step.description = f"{step.description} [with full transparency]"
        
        return new_plan
    
    def _add_consent_steps(self, plan: ActionPlan) -> ActionPlan:
        """Create alternative plan adding explicit consent."""
        new_plan = deepcopy(plan)
        new_plan.objective = f"{plan.objective} (with consent protocol)"
        
        for step in new_plan.steps:
            if step.involves_coercion:
                step.involves_coercion = False
                step.coercion_details = None
                step.involves_consent = True
                step.consent_obtained = True
                step.description = f"[Obtain consent] {step.description}"
        
        return new_plan
    
    def _reduce_risk(self, plan: ActionPlan) -> ActionPlan:
        """Create alternative plan with reduced risk."""
        new_plan = deepcopy(plan)
        new_plan.objective = f"{plan.objective} (low-risk version)"
        
        for step in new_plan.steps:
            if step.risk_level and step.risk_level > 0.7:
                step.risk_level = min(0.3, step.risk_level / 2)
                step.description = f"{step.description} [with additional safeguards]"
                step.reversible = True
        
        return new_plan


class AlternativeSuggester(AlternativeGenerator):
    """
    Alias for AlternativeGenerator for backward compatibility.
    
    Legacy code may reference AlternativeSuggester.
    """
    pass
