"""
Unit tests for Arbiter module.

Tests cover:
- Decision formatting
- Alternative generation
- Verdict construction

Coverage Target: 100%
"""
import pytest
from motor_integridade_processual.arbiter.decision import DecisionFormatter
from motor_integridade_processual.arbiter.alternatives import AlternativeGenerator
from motor_integridade_processual.models.verdict import EthicalVerdict, DecisionLevel
from motor_integridade_processual.models.action_plan import ActionPlan, ActionStep, ActionType


def create_test_plan(objective: str = "Test plan") -> ActionPlan:
    """Helper to create test plan."""
    return ActionPlan(
        objective=objective,
        steps=[
            ActionStep(
                description="Test step",
                action_type=ActionType.OBSERVATION,
                reversible=True,
                affected_stakeholders=["user-001"]
            )
        ],
        initiator="test_system",
        initiator_type="ai_agent"
    )


class TestDecisionFormatter:
    """Test suite for DecisionFormatter."""
    
    def test_format_approved_verdict(self) -> None:
        """Test formatting of approved verdict."""
        verdict = EthicalVerdict(
            action_plan_id="plan-001",
            decision=DecisionLevel.APPROVE,
            confidence=0.9,
            aggregated_score=0.85,
            reasoning="Strong ethical approval",
            framework_verdicts=[],
            requires_human_review=False
        )
        
        formatter = DecisionFormatter()
        formatted = formatter.format(verdict)
        
        assert "APPROVE" in formatted
        assert "0.85" in formatted
    
    def test_format_rejected_verdict(self) -> None:
        """Test formatting of rejected verdict."""
        verdict = EthicalVerdict(
            action_plan_id="plan-002",
            decision=DecisionLevel.REJECT,
            confidence=0.95,
            aggregated_score=0.25,
            reasoning="Ethical violations detected",
            framework_verdicts=[],
            requires_human_review=False
        )
        
        formatter = DecisionFormatter()
        formatted = formatter.format(verdict)
        
        assert "REJECT" in formatted
        assert "0.25" in formatted


class TestAlternativeGenerator:
    """Test suite for AlternativeGenerator."""
    
    def test_generate_alternatives_for_rejected_plan(self) -> None:
        """Test alternative generation for rejected plans."""
        plan = create_test_plan("Rejected plan")
        generator = AlternativeGenerator()
        
        alternatives = generator.generate(plan)
        
        assert isinstance(alternatives, list)
        assert len(alternatives) >= 0
    
    def test_suggest_modifications(self) -> None:
        """Test modification suggestions."""
        plan = ActionPlan(
            objective="High-risk operation",
            steps=[
                ActionStep(
                    description="Risky step",
                    action_type=ActionType.MANIPULATION,
                    risk_level=0.9,
                    reversible=False,
                    affected_stakeholders=["user-001"]
                )
            ],
            initiator="system",
            initiator_type="ai_agent"
        )
        
        generator = AlternativeGenerator()
        suggestions = generator.suggest_modifications(plan)
        
        assert isinstance(suggestions, list)
