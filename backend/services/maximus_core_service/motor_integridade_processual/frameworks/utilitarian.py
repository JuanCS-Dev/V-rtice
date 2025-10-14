"""
Utilitarian Calculus Framework.

Implements consequentialist ethics based on Jeremy Bentham and John Stuart Mill.
Evaluates actions based on aggregate welfare maximization across all stakeholders.

Core Principle:
"The greatest happiness for the greatest number"

Uses Bentham's 7 dimensions + Mill's qualitative distinctions.

Lei Governante: Constituição Vértice v2.6 - Lei Zero (Imperativo do Florescimento)
"""

from typing import List
from motor_integridade_processual.frameworks.base import AbstractEthicalFramework
from motor_integridade_processual.models.action_plan import ActionPlan, ActionStep, Effect
from motor_integridade_processual.models.verdict import (
    FrameworkVerdict,
    FrameworkName,
    DecisionLevel,
    RejectionReason,
)


class UtilitarianCalculus(AbstractEthicalFramework):
    """
    Utilitarian ethical framework based on welfare maximization.
    
    Calculates utility using:
    - Bentham's 7 dimensions (intensity, duration, certainty, propinquity,
      fecundity, purity, extent)
    - Mill's quality of pleasures (intellectual > physical)
    - Stakeholder weighting (vulnerability increases weight)
    
    Philosophy:
        Jeremy Bentham (1748-1832): Hedonic calculus - all pleasure is equal
        John Stuart Mill (1806-1873): Some pleasures are higher quality
    """
    
    def __init__(self):
        """Initialize Utilitarian framework."""
        super().__init__(name=FrameworkName.UTILITARIAN.value, weight=0.30, can_veto=False)
    
    def evaluate(self, plan: ActionPlan) -> FrameworkVerdict:
        """
        Evaluate plan through utilitarian lens.
        
        Args:
            plan: Action plan to evaluate
            
        Returns:
            FrameworkVerdict with utility score
        """
        # Calculate aggregate utility
        total_utility = 0.0
        utility_details = []
        
        for step in plan.steps:
            step_utility = self._calculate_step_utility(step)
            total_utility += step_utility
            utility_details.append(f"Step {step.id[:8]}: {step_utility:.2f}")
        
        # Normalize by number of steps
        avg_utility = total_utility / len(plan.steps) if plan.steps else 0.0
        
        # Apply stakeholder extent multiplier
        stakeholder_count = len(plan.get_affected_stakeholders())
        extent_multiplier = min(1.0 + (stakeholder_count / 100), 2.0)
        
        final_score = min(avg_utility * extent_multiplier, 1.0)
        
        # Determine verdict based on utility
        if final_score >= 0.75:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.APPROVE,
                score=final_score,
                confidence=0.85,
                reasoning=f"High aggregate utility ({final_score:.2f}) - "
                              f"benefits {stakeholder_count} stakeholders"
            )
        elif final_score >= 0.50:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
                score=final_score,
                confidence=0.75,
                conditions=["Monitor for unintended negative consequences"],
                reasoning=f"Moderate utility ({final_score:.2f})"
            )
        else:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.REJECT,
                score=final_score,
                confidence=0.80,
                rejection_reasons=[
                    RejectionReason(
                        category="insufficient_utility",
                        description=f"Aggregate utility too low ({final_score:.2f}) - "
                                   f"more harm than good",
                        severity=0.5,
                        affected_stakeholders=[s.id for s in plan.steps],
                        violated_principle="Greatest Happiness Principle",
                        citation="Mill, Utilitarianism (1863)"
                    )
                ],
                reasoning=f"Insufficient aggregate welfare ({final_score:.2f})"
            )
    
    def _calculate_step_utility(self, step: ActionStep) -> float:
        """
        Calculate utility of a single step using Bentham's calculus.
        
        Bentham's 7 dimensions:
        1. Intensity: How strong is the pleasure/pain?
        2. Duration: How long does it last?
        3. Certainty: How likely is it to occur?
        4. Propinquity: How soon does it occur?
        5. Fecundity: Does it lead to more pleasure?
        6. Purity: Is it mixed with pain?
        7. Extent: How many people are affected?
        """
        utility = 0.0
        
        # Analyze effects
        for effect in step.effects:
            effect_utility = self._calculate_effect_utility(effect, step)
            utility += effect_utility
        
        # Penalize high risk (potential for harm)
        utility -= (step.risk_level * 0.3)
        
        # Bonus for reversibility (less potential harm)
        if step.reversible:
            utility += 0.1
        
        # Penalize deception/coercion (Mill's qualitative distinction)
        if step.involves_deception:
            utility -= 0.4  # Deception produces lower-quality outcomes
        if step.involves_coercion:
            utility -= 0.3
        
        # Normalize to [0, 1]
        return max(0.0, min(utility, 1.0))
    
    def _calculate_effect_utility(self, effect: Effect, step: ActionStep) -> float:
        """
        Calculate utility of a specific effect.
        
        Args:
            effect: The effect to evaluate
            step: Parent step (for context)
            
        Returns:
            Utility value [-1.0, 1.0]
        """
        # 1. Intensity: Use magnitude directly
        intensity = effect.magnitude
        
        # 2. Duration: Longer = more utility (or more harm)
        duration_factor = min(step.estimated_duration_seconds / 3600, 1.0)  # Cap at 1 hour
        
        # 3. Certainty: Use probability
        certainty = effect.probability
        
        # 4. Propinquity: Immediate effects count more
        propinquity = 0.9  # Assume effects are relatively immediate
        
        # 5. Fecundity: Positive effects tend to generate more positive
        fecundity = 0.1 if intensity > 0 else 0.0
        
        # 6. Purity: Check if mixed with harms
        purity = 1.0 if not step.risk_level > 0.8 else 0.5
        
        # 7. Extent: Number of affected stakeholders
        extent = len(step.affected_stakeholders) / 10  # Normalize
        
        # Combine using weighted average
        utility = (
            intensity * certainty * 
            (duration_factor * 0.2 + propinquity * 0.3 + 
             fecundity * 0.1 + purity * 0.2 + extent * 0.2)
        )
        
        return utility
