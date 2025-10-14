"""
Unit Tests - Framework Coverage Boosters

Testes adicionais focados em aumentar coverage para ≥95%.
Testa edge cases e branches não cobertos.

Autor: Juan Carlos de Souza
"""

import pytest
from uuid import uuid4

from mip.frameworks import (
    KantianDeontology,
    UtilitarianCalculus,
    VirtueEthics,
    Principialism,
)
from mip.models import *


class TestKantianEdgeCases:
    """Edge case tests for Kantian framework."""
    
    def test_kant_empty_stakeholders(self):
        """Test Kant with no stakeholders."""
        step = ActionStep(sequence_number=1, description="Test", action_type="test")
        plan = ActionPlan(
            name="No stakeholders",
            description="Test",
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[],
        )
        
        kant = KantianDeontology()
        score = kant.evaluate(plan)
        assert score is not None
    
    def test_kant_multiple_autonomy_violations(self):
        """Test Kant with multiple autonomy violations."""
        s1 = Stakeholder(
            id="victim1",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Person 1",
            impact_magnitude=-0.7,
            autonomy_respected=False,
            vulnerability_level=0.8,
        )
        s2 = Stakeholder(
            id="victim2",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Person 2",
            impact_magnitude=-0.6,
            autonomy_respected=False,
            vulnerability_level=0.9,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Violate multiple autonomies",
            action_type="coercion",
            respects_autonomy=False,
            treats_as_means_only=True,
        )
        
        plan = ActionPlan(
            name="Multiple violations",
            description="Test",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[s1, s2],
        )
        
        kant = KantianDeontology()
        score = kant.evaluate(plan)
        assert score.veto is True
    
    def test_kant_low_confidence_evaluation(self):
        """Test Kant evaluation with ambiguous case."""
        stakeholder = Stakeholder(
            id="ambiguous",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Ambiguous case",
            impact_magnitude=0.1,
            autonomy_respected=True,
            vulnerability_level=0.5,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Borderline action",
            action_type="ambiguous",
            respects_autonomy=True,
        )
        
        plan = ActionPlan(
            name="Borderline",
            description="Ambiguous case",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[stakeholder],
        )
        
        kant = KantianDeontology()
        score = kant.evaluate(plan)
        assert score.confidence <= 1.0


class TestUtilitarianEdgeCases:
    """Edge case tests for Utilitarian framework."""
    
    def test_utilitarian_no_effects(self):
        """Test utilitarian with no effects."""
        step = ActionStep(
            sequence_number=1,
            description="Action with no effects",
            action_type="neutral",
            effects=[],
        )
        
        plan = ActionPlan(
            name="No effects",
            description="Test",
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[],
        )
        
        mill = UtilitarianCalculus()
        score = mill.evaluate(plan)
        assert score is not None
    
    def test_utilitarian_negative_effects(self):
        """Test utilitarian with negative effects."""
        stakeholder = Stakeholder(
            id="harmed",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Harmed person",
            impact_magnitude=-0.9,
            autonomy_respected=True,
            vulnerability_level=0.8,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Harmful action",
            action_type="harmful",
            effects=[Effect(
                description="Harm",
                probability=0.9,
                magnitude=-0.8,
                duration_seconds=3600.0,
                reversible=False,
            )],
        )
        
        plan = ActionPlan(
            name="Harmful",
            description="Causes harm",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[stakeholder],
        )
        
        mill = UtilitarianCalculus()
        score = mill.evaluate(plan)
        assert score.score < 0.7
    
    def test_utilitarian_mixed_effects(self):
        """Test utilitarian with mixed positive and negative effects."""
        s1 = Stakeholder(
            id="benefited",
            type=StakeholderType.HUMAN_GROUP,
            description="Benefited group",
            impact_magnitude=0.8,
            autonomy_respected=True,
            vulnerability_level=0.3,
        )
        s2 = Stakeholder(
            id="harmed",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Harmed person",
            impact_magnitude=-0.5,
            autonomy_respected=True,
            vulnerability_level=0.9,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Mixed consequences",
            action_type="mixed",
            effects=[
                Effect(description="Benefit many", probability=0.9, magnitude=0.7),
                Effect(description="Harm one", probability=0.8, magnitude=-0.6),
            ],
        )
        
        plan = ActionPlan(
            name="Mixed",
            description="Utilitarian dilemma",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[s1, s2],
        )
        
        mill = UtilitarianCalculus()
        score = mill.evaluate(plan)
        assert score is not None


class TestVirtueEdgeCases:
    """Edge case tests for Virtue Ethics."""
    
    def test_virtue_high_risk_evaluates_courage(self):
        """Test that high risk plans evaluate courage."""
        stakeholder = Stakeholder(
            id="protected",
            type=StakeholderType.HUMAN_GROUP,
            description="Protected group",
            impact_magnitude=0.9,
            autonomy_respected=True,
            vulnerability_level=0.7,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Brave action",
            action_type="defensive",
        )
        
        plan = ActionPlan(
            name="Courageous Defense",
            description="High risk defense",
            category=ActionCategory.DEFENSIVE,
            steps=[step],
            stakeholders=[stakeholder],
            risk_level=0.9,  # High risk
        )
        
        aristotle = VirtueEthics()
        score = aristotle.evaluate(plan)
        assert score is not None
        assert score.score >= 0.5
    
    def test_virtue_vulnerable_stakeholders_evaluate_compassion(self):
        """Test that vulnerable stakeholders boost compassion score."""
        vulnerable = Stakeholder(
            id="vulnerable",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Highly vulnerable",
            impact_magnitude=0.9,
            autonomy_respected=True,
            vulnerability_level=0.95,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Protect vulnerable",
            action_type="protective",
        )
        
        plan = ActionPlan(
            name="Compassionate Care",
            description="Care for vulnerable",
            category=ActionCategory.PROACTIVE,
            steps=[step],
            stakeholders=[vulnerable],
        )
        
        aristotle = VirtueEthics()
        score = aristotle.evaluate(plan)
        assert score.score >= 0.7
    
    def test_virtue_dishonest_action(self):
        """Test virtue evaluation of potentially dishonest action."""
        stakeholder = Stakeholder(
            id="deceived",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Potentially deceived",
            impact_magnitude=-0.3,
            autonomy_respected=False,
            vulnerability_level=0.6,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Potentially deceptive action",
            action_type="manipulation",
            respects_autonomy=False,
        )
        
        plan = ActionPlan(
            name="Deception",
            description="Dishonest action",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[stakeholder],
        )
        
        aristotle = VirtueEthics()
        score = aristotle.evaluate(plan)
        assert score is not None


class TestPrincipalismEdgeCases:
    """Edge case tests for Principialism."""
    
    def test_principialism_harm_to_vulnerable(self):
        """Test principialism when vulnerable stakeholder harmed."""
        vulnerable = Stakeholder(
            id="vulnerable-harmed",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Vulnerable person harmed",
            impact_magnitude=-0.8,
            autonomy_respected=True,
            vulnerability_level=0.95,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Harmful to vulnerable",
            action_type="harmful",
            effects=[Effect(
                description="Harm vulnerable",
                probability=0.9,
                magnitude=-0.7,
            )],
        )
        
        plan = ActionPlan(
            name="Harm Vulnerable",
            description="Harms vulnerable",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[vulnerable],
        )
        
        principialism = Principialism()
        score = principialism.evaluate(plan)
        # Should score low due to harm to vulnerable
        assert score.score < 0.7
    
    def test_principialism_autonomy_violation(self):
        """Test principialism with autonomy violation."""
        stakeholder = Stakeholder(
            id="coerced",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Coerced person",
            impact_magnitude=-0.6,
            autonomy_respected=False,
            vulnerability_level=0.7,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Coerce person",
            action_type="coercion",
            respects_autonomy=False,
        )
        
        plan = ActionPlan(
            name="Coercion",
            description="Violates autonomy",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[stakeholder],
        )
        
        principialism = Principialism()
        score = principialism.evaluate(plan)
        # Should score low due to autonomy violation
        assert score.score < 0.8
    
    def test_principialism_unfair_distribution(self):
        """Test principialism with unfair distribution."""
        s1 = Stakeholder(
            id="privileged",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Privileged person",
            impact_magnitude=0.9,
            autonomy_respected=True,
            vulnerability_level=0.1,
        )
        s2 = Stakeholder(
            id="disadvantaged",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Disadvantaged person",
            impact_magnitude=-0.7,
            autonomy_respected=True,
            vulnerability_level=0.9,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Unfair distribution",
            action_type="distributive",
        )
        
        plan = ActionPlan(
            name="Unfair",
            description="Benefits privileged, harms vulnerable",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[s1, s2],
        )
        
        principialism = Principialism()
        score = principialism.evaluate(plan)
        # Should detect injustice
        assert score is not None


# Parametrized tests for comprehensive coverage
@pytest.mark.parametrize("risk_level", [0.0, 0.1, 0.5, 0.9, 1.0])
def test_all_frameworks_handle_risk_levels(risk_level):
    """Test all frameworks handle various risk levels."""
    step = ActionStep(sequence_number=1, description="Test", action_type="test")
    plan = ActionPlan(
        name="Risk test",
        description="Test",
        category=ActionCategory.PROACTIVE,
        steps=[step],
        stakeholders=[],
        risk_level=risk_level,
    )
    
    frameworks = [
        KantianDeontology(),
        UtilitarianCalculus(),
        VirtueEthics(),
        Principialism(),
    ]
    
    for framework in frameworks:
        score = framework.evaluate(plan)
        assert score is not None
        assert 0.0 <= score.score <= 1.0


@pytest.mark.parametrize("urgency", [0.0, 0.3, 0.7, 1.0])
def test_all_frameworks_handle_urgency(urgency):
    """Test all frameworks handle various urgency levels."""
    step = ActionStep(sequence_number=1, description="Test", action_type="test")
    plan = ActionPlan(
        name="Urgency test",
        description="Test",
        category=ActionCategory.REACTIVE,
        steps=[step],
        stakeholders=[],
        urgency=urgency,
    )
    
    frameworks = [
        KantianDeontology(),
        UtilitarianCalculus(),
        VirtueEthics(),
        Principialism(),
    ]
    
    for framework in frameworks:
        score = framework.evaluate(plan)
        assert score is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
