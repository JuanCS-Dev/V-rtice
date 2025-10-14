"""Alternative suggestion engine."""

from typing import List
from motor_integridade_processual.models.action_plan import ActionPlan, ActionStep

class AlternativeSuggester:
    """Suggests ethical alternatives for rejected plans."""
    
    def suggest_alternatives(self, plan: ActionPlan) -> List[str]:
        """Generate alternative suggestions."""
        suggestions = []
        
        for step in plan.steps:
            if step.involves_deception:
                suggestions.append(f"Replace deceptive step '{step.description}' with transparent communication")
            if step.risk_level > 0.7:
                suggestions.append(f"Reduce risk in step '{step.description}' or add safeguards")
            if step.involves_coercion:
                suggestions.append(f"Obtain voluntary consent for '{step.description}'")
        
        return suggestions[:5]  # Top 5
