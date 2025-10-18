"""
Unit Tests - Conflict Resolver

Testes para resolução de conflitos éticos entre frameworks.

Autor: Juan Carlos de Souza
"""

import pytest

from mip.resolver import ConflictResolver
from mip.models import (
    ActionPlan,
    ActionStep,
    Stakeholder,
    StakeholderType,
    ActionCategory,
    FrameworkScore,
    VerdictStatus,
)


class TestConflictResolver:
    """Tests for ConflictResolver."""
    
    def test_resolver_instantiation(self):
        """Test resolver can be instantiated."""
        resolver = ConflictResolver()
        assert resolver is not None
    
    def test_resolve_all_agree_high(self):
        """Test resolution when all frameworks agree with high scores."""
        plan = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.DEFENSIVE,
            steps=[ActionStep(
                sequence_number=1,
                description="Test",
                action_type="test",
            )],
            stakeholders=[],
        )
        
        kant = FrameworkScore(
            framework_name="Kantian",
            score=0.9,
            reasoning="Good",
            veto=False,
        )
        
        mill = FrameworkScore(
            framework_name="Utilitarian",
            score=0.85,
            reasoning="Beneficial",
            veto=False,
        )
        
        aristotle = FrameworkScore(
            framework_name="Virtue",
            score=0.88,
            reasoning="Virtuous",
            veto=False,
        )
        
        principialism = FrameworkScore(
            framework_name="Principialism",
            score=0.92,
            reasoning="Principled",
            veto=False,
        )
        
        resolver = ConflictResolver()
        result = resolver.resolve(plan, kant, mill, aristotle, principialism)
        
        assert result["status"] == VerdictStatus.APPROVED
        assert result["aggregate_score"] >= 0.8
        assert result["confidence"] >= 0.8
    
    def test_resolve_kantian_veto(self):
        """Test that Kantian veto overrides other frameworks."""
        plan = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.INTERVENTION,
            steps=[ActionStep(
                sequence_number=1,
                description="Test",
                action_type="test",
            )],
            stakeholders=[],
        )
        
        kant = FrameworkScore(
            framework_name="Kantian",
            score=None,
            reasoning="Veto due to autonomy violation",
            veto=True,
        )
        
        mill = FrameworkScore(
            framework_name="Utilitarian",
            score=0.9,
            reasoning="High utility",
            veto=False,
        )
        
        aristotle = FrameworkScore(
            framework_name="Virtue",
            score=0.85,
            reasoning="Virtuous",
            veto=False,
        )
        
        principialism = FrameworkScore(
            framework_name="Principialism",
            score=0.88,
            reasoning="Principled",
            veto=False,
        )
        
        resolver = ConflictResolver()
        result = resolver.resolve(plan, kant, mill, aristotle, principialism)
        
        assert result["status"] == VerdictStatus.REJECTED
        assert result["aggregate_score"] is None or result["aggregate_score"] == 0.0
    
    def test_resolve_mixed_scores(self):
        """Test resolution with mixed scores."""
        plan = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.PROACTIVE,
            steps=[ActionStep(
                sequence_number=1,
                description="Test",
                action_type="test",
            )],
            stakeholders=[],
        )
        
        kant = FrameworkScore(
            framework_name="Kantian",
            score=0.75,
            reasoning="Acceptable",
            veto=False,
        )
        
        mill = FrameworkScore(
            framework_name="Utilitarian",
            score=0.6,
            reasoning="Moderate benefit",
            veto=False,
        )
        
        aristotle = FrameworkScore(
            framework_name="Virtue",
            score=0.8,
            reasoning="Good character",
            veto=False,
        )
        
        principialism = FrameworkScore(
            framework_name="Principialism",
            score=0.7,
            reasoning="Principled",
            veto=False,
        )
        
        resolver = ConflictResolver()
        result = resolver.resolve(plan, kant, mill, aristotle, principialism)
        
        # Should aggregate to reasonable score
        assert 0.6 <= result["aggregate_score"] <= 0.8
    
    def test_resolve_detects_conflicts(self):
        """Test that resolver detects conflicting evaluations."""
        plan = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.REACTIVE,
            steps=[ActionStep(
                sequence_number=1,
                description="Test",
                action_type="test",
            )],
            stakeholders=[],
        )
        
        kant = FrameworkScore(
            framework_name="Kantian",
            score=0.9,
            reasoning="High score",
            veto=False,
        )
        
        mill = FrameworkScore(
            framework_name="Utilitarian",
            score=0.3,
            reasoning="Low benefit",
            veto=False,
        )
        
        aristotle = FrameworkScore(
            framework_name="Virtue",
            score=0.85,
            reasoning="Virtuous",
            veto=False,
        )
        
        principialism = FrameworkScore(
            framework_name="Principialism",
            score=0.8,
            reasoning="Principled",
            veto=False,
        )
        
        resolver = ConflictResolver()
        result = resolver.resolve(plan, kant, mill, aristotle, principialism)
        
        # Should detect conflict (large divergence between Kant and Mill)
        assert len(result["conflicts"]) > 0
    
    def test_resolve_low_scores_escalate(self):
        """Test that consistently low scores may escalate or reject."""
        plan = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.INTERVENTION,
            steps=[ActionStep(
                sequence_number=1,
                description="Test",
                action_type="test",
            )],
            stakeholders=[],
            risk_level=0.8,
        )
        
        kant = FrameworkScore(
            framework_name="Kantian_Deontology",
            score=0.45,
            reasoning="Borderline",
            veto=False,
        )
        
        mill = FrameworkScore(
            framework_name="Utilitarian_Calculus",
            score=0.48,
            reasoning="Low benefit",
            veto=False,
        )
        
        aristotle = FrameworkScore(
            framework_name="Virtue_Ethics",
            score=0.42,
            reasoning="Questionable",
            veto=False,
        )
        
        principialism = FrameworkScore(
            framework_name="Principialism",
            score=0.46,
            reasoning="Concerning",
            veto=False,
        )
        
        resolver = ConflictResolver()
        result = resolver.resolve(plan, kant, mill, aristotle, principialism)
        
        # Low scores + high risk should reject or escalate
        assert result["status"] in [
            VerdictStatus.REJECTED,
            VerdictStatus.ESCALATED, 
            VerdictStatus.REQUIRES_HUMAN
        ]
    
    def test_resolve_provides_reasoning(self):
        """Test that resolver provides reasoning for decision."""
        plan = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.DEFENSIVE,
            steps=[ActionStep(
                sequence_number=1,
                description="Test",
                action_type="test",
            )],
            stakeholders=[],
        )
        
        kant = FrameworkScore("Kantian", 0.8, "Good", False)
        mill = FrameworkScore("Utilitarian", 0.75, "Beneficial", False)
        aristotle = FrameworkScore("Virtue", 0.82, "Virtuous", False)
        principialism = FrameworkScore("Principialism", 0.78, "Principled", False)
        
        resolver = ConflictResolver()
        result = resolver.resolve(plan, kant, mill, aristotle, principialism)
        
        assert "reasoning" in result
        assert result["reasoning"] is not None
        assert len(result["reasoning"]) > 0


class TestContextAdjustment:
    """Tests for context-aware weight adjustment."""
    
    def test_high_risk_prioritizes_kant(self):
        """Test that high-risk scenarios prioritize Kant."""
        plan = ActionPlan(
            name="High Risk",
            description="Risky action",
            category=ActionCategory.INTERVENTION,
            steps=[ActionStep(
                sequence_number=1,
                description="Risky",
                action_type="risky",
            )],
            stakeholders=[],
            risk_level=0.95,
        )
        
        kant = FrameworkScore("Kantian", 0.9, "Safe", False)
        mill = FrameworkScore("Utilitarian", 0.6, "Some benefit", False)
        aristotle = FrameworkScore("Virtue", 0.7, "Questionable", False)
        principialism = FrameworkScore("Principialism", 0.75, "Ok", False)
        
        resolver = ConflictResolver()
        result = resolver.resolve(plan, kant, mill, aristotle, principialism)
        
        # Should weight Kant more heavily
        # Since Kant is high, overall should be decent
        assert result["aggregate_score"] >= 0.7
    
    def test_vulnerable_stakeholder_prioritizes_principialism(self):
        """Test that vulnerable stakeholders boost principialism weight."""
        vulnerable = Stakeholder(
            id="vulnerable",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Highly vulnerable person",
            impact_magnitude=0.8,
            autonomy_respected=True,
            vulnerability_level=0.95,
        )
        
        plan = ActionPlan(
            name="Protect Vulnerable",
            description="Action affecting vulnerable",
            category=ActionCategory.DEFENSIVE,
            steps=[ActionStep(
                sequence_number=1,
                description="Protect",
                action_type="protective",
            )],
            stakeholders=[vulnerable],
        )
        
        kant = FrameworkScore("Kantian", 0.75, "Ok", False)
        mill = FrameworkScore("Utilitarian", 0.7, "Some benefit", False)
        aristotle = FrameworkScore("Virtue", 0.8, "Good", False)
        principialism = FrameworkScore("Principialism", 0.95, "Excellent justice", False)
        
        resolver = ConflictResolver()
        result = resolver.resolve(plan, kant, mill, aristotle, principialism)
        
        # Should weight principialism heavily, boosting score
        assert result["aggregate_score"] >= 0.8


# Parametrized tests
@pytest.mark.parametrize("veto", [True, False])
def test_veto_handling(veto):
    """Test veto is handled correctly."""
    plan = ActionPlan(
        name="Test",
        description="Test",
        category=ActionCategory.INFORMATIONAL,
        steps=[ActionStep(sequence_number=1, description="Test", action_type="test")],
        stakeholders=[],
    )
    
    kant = FrameworkScore("Kantian", None if veto else 0.8, "Reason", veto)
    mill = FrameworkScore("Utilitarian", 0.8, "Good", False)
    aristotle = FrameworkScore("Virtue", 0.8, "Good", False)
    principialism = FrameworkScore("Principialism", 0.8, "Good", False)
    
    resolver = ConflictResolver()
    result = resolver.resolve(plan, kant, mill, aristotle, principialism)
    
    if veto:
        assert result["status"] == VerdictStatus.REJECTED
    else:
        assert result["status"] != VerdictStatus.REJECTED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
