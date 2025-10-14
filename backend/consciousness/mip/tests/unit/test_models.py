"""
Unit Tests - MIP Data Models

Testes unitários para ActionPlan, ActionStep, Stakeholder, Effect, etc.
Cobertura de edge cases e validações.

Autor: Juan Carlos de Souza
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime

from backend.consciousness.mip.models import (
    ActionPlan,
    ActionStep,
    Stakeholder,
    Effect,
    Precondition,
    EthicalVerdict,
    FrameworkScore,
    AuditTrailEntry,
    VerdictStatus,
    ActionCategory,
    StakeholderType,
)


class TestStakeholder:
    """Tests for Stakeholder model."""
    
    def test_create_valid_stakeholder(self):
        """Test creating valid stakeholder."""
        stakeholder = Stakeholder(
            id="user-001",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Test user",
            impact_magnitude=0.5,
            autonomy_respected=True,
            vulnerability_level=0.3,
        )
        
        assert stakeholder.id == "user-001"
        assert stakeholder.type == StakeholderType.HUMAN_INDIVIDUAL
        assert stakeholder.impact_magnitude == 0.5
        assert stakeholder.autonomy_respected is True
        assert stakeholder.vulnerability_level == 0.3
    
    def test_stakeholder_impact_magnitude_validation(self):
        """Test impact_magnitude must be in [-1.0, 1.0]."""
        # Valid positive
        s1 = Stakeholder(
            id="test",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Test",
            impact_magnitude=0.8,
            autonomy_respected=True,
            vulnerability_level=0.5,
        )
        assert s1.impact_magnitude == 0.8
        
        # Valid negative
        s2 = Stakeholder(
            id="test",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Test",
            impact_magnitude=-0.7,
            autonomy_respected=True,
            vulnerability_level=0.5,
        )
        assert s2.impact_magnitude == -0.7
        
        # Invalid too high
        with pytest.raises(ValueError, match="impact_magnitude"):
            Stakeholder(
                id="test",
                type=StakeholderType.HUMAN_INDIVIDUAL,
                description="Test",
                impact_magnitude=1.5,
                autonomy_respected=True,
                vulnerability_level=0.5,
            )
        
        # Invalid too low
        with pytest.raises(ValueError, match="impact_magnitude"):
            Stakeholder(
                id="test",
                type=StakeholderType.HUMAN_INDIVIDUAL,
                description="Test",
                impact_magnitude=-1.5,
                autonomy_respected=True,
                vulnerability_level=0.5,
            )
    
    def test_stakeholder_vulnerability_level_validation(self):
        """Test vulnerability_level must be in [0.0, 1.0]."""
        # Valid
        s1 = Stakeholder(
            id="test",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Test",
            impact_magnitude=0.5,
            autonomy_respected=True,
            vulnerability_level=0.9,
        )
        assert s1.vulnerability_level == 0.9
        
        # Invalid
        with pytest.raises(ValueError, match="vulnerability_level"):
            Stakeholder(
                id="test",
                type=StakeholderType.HUMAN_INDIVIDUAL,
                description="Test",
                impact_magnitude=0.5,
                autonomy_respected=True,
                vulnerability_level=1.5,
            )
    
    def test_stakeholder_types(self):
        """Test all stakeholder types are valid."""
        types = [
            StakeholderType.HUMAN_INDIVIDUAL,
            StakeholderType.HUMAN_GROUP,
            StakeholderType.AI_SYSTEM,
            StakeholderType.ENVIRONMENT,
            StakeholderType.ORGANIZATION,
        ]
        
        for stype in types:
            s = Stakeholder(
                id=f"test-{stype.value}",
                type=stype,
                description="Test",
                impact_magnitude=0.5,
                autonomy_respected=True,
                vulnerability_level=0.3,
            )
            assert s.type == stype


class TestEffect:
    """Tests for Effect model."""
    
    def test_create_valid_effect(self):
        """Test creating valid effect."""
        effect = Effect(
            description="Positive outcome",
            probability=0.95,
            magnitude=0.8,
            duration_seconds=3600.0,
            reversible=True,
            affected_stakeholders=["user-001"],
        )
        
        assert effect.description == "Positive outcome"
        assert effect.probability == 0.95
        assert effect.magnitude == 0.8
        assert effect.duration_seconds == 3600.0
        assert effect.reversible is True
        assert "user-001" in effect.affected_stakeholders
    
    def test_effect_probability_validation(self):
        """Test probability must be in [0.0, 1.0]."""
        # Valid
        e1 = Effect(
            description="Test",
            probability=0.5,
            magnitude=0.5,
        )
        assert e1.probability == 0.5
        
        # Invalid
        with pytest.raises(ValueError, match="probability"):
            Effect(
                description="Test",
                probability=1.5,
                magnitude=0.5,
            )
    
    def test_effect_magnitude_validation(self):
        """Test magnitude must be in [-1.0, 1.0]."""
        # Valid positive
        e1 = Effect(
            description="Test",
            probability=0.5,
            magnitude=0.9,
        )
        assert e1.magnitude == 0.9
        
        # Valid negative
        e2 = Effect(
            description="Test",
            probability=0.5,
            magnitude=-0.7,
        )
        assert e2.magnitude == -0.7
        
        # Invalid
        with pytest.raises(ValueError, match="magnitude"):
            Effect(
                description="Test",
                probability=0.5,
                magnitude=2.0,
            )


class TestPrecondition:
    """Tests for Precondition model."""
    
    def test_create_precondition(self):
        """Test creating precondition."""
        precond = Precondition(
            description="Service must be online",
            required=True,
            current_state=True,
            verification_method="check_service_health",
        )
        
        assert precond.description == "Service must be online"
        assert precond.required is True
        assert precond.current_state is True
        assert precond.verification_method == "check_service_health"
    
    def test_precondition_optional_fields(self):
        """Test precondition with optional fields."""
        precond = Precondition(
            description="Optional check",
            required=False,
        )
        
        assert precond.current_state is None
        assert precond.verification_method is None


class TestActionStep:
    """Tests for ActionStep model."""
    
    def test_create_minimal_action_step(self):
        """Test creating action step with minimal fields."""
        step = ActionStep(
            sequence_number=1,
            description="Test step",
            action_type="observation",
        )
        
        assert step.sequence_number == 1
        assert step.description == "Test step"
        assert step.action_type == "observation"
        assert isinstance(step.id, UUID)
    
    def test_action_step_with_effects(self):
        """Test action step with effects."""
        effect = Effect(
            description="Test effect",
            probability=0.9,
            magnitude=0.7,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Step with effect",
            action_type="action",
            effects=[effect],
        )
        
        assert len(step.effects) == 1
        assert step.effects[0].description == "Test effect"
    
    def test_action_step_validation_negative_sequence(self):
        """Test sequence_number cannot be negative."""
        with pytest.raises(ValueError, match="sequence_number"):
            ActionStep(
                sequence_number=-1,
                description="Invalid",
                action_type="action",
            )
    
    def test_action_step_ethical_flags(self):
        """Test ethical metadata flags."""
        step = ActionStep(
            sequence_number=1,
            description="Ethical step",
            action_type="communication",
            respects_autonomy=True,
            treats_as_means_only=False,
        )
        
        assert step.respects_autonomy is True
        assert step.treats_as_means_only is False


class TestActionPlan:
    """Tests for ActionPlan model."""
    
    def test_create_minimal_action_plan(self):
        """Test creating plan with minimal required fields."""
        step = ActionStep(
            sequence_number=1,
            description="Test step",
            action_type="observation",
        )
        
        plan = ActionPlan(
            name="Test Plan",
            description="Test description",
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[],
        )
        
        assert plan.name == "Test Plan"
        assert plan.description == "Test description"
        assert plan.category == ActionCategory.INFORMATIONAL
        assert len(plan.steps) == 1
        assert isinstance(plan.id, UUID)
    
    def test_action_plan_with_stakeholders(self):
        """Test plan with stakeholders."""
        stakeholder = Stakeholder(
            id="user-001",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Test user",
            impact_magnitude=0.5,
            autonomy_respected=True,
            vulnerability_level=0.3,
        )
        
        step = ActionStep(
            sequence_number=1,
            description="Test",
            action_type="action",
        )
        
        plan = ActionPlan(
            name="Plan with stakeholders",
            description="Test",
            category=ActionCategory.DEFENSIVE,
            steps=[step],
            stakeholders=[stakeholder],
        )
        
        assert len(plan.stakeholders) == 1
        assert plan.stakeholders[0].id == "user-001"
    
    def test_action_plan_empty_steps_rejected(self):
        """Test that plans without steps are rejected."""
        with pytest.raises(ValueError, match="ActionPlan deve ter pelo menos um step"):
            ActionPlan(
                name="Empty plan",
                description="No steps",
                category=ActionCategory.INFORMATIONAL,
                steps=[],
                stakeholders=[],
            )
    
    def test_action_plan_urgency_validation(self):
        """Test urgency must be in [0.0, 1.0]."""
        step = ActionStep(
            sequence_number=1,
            description="Test",
            action_type="action",
        )
        
        # Valid
        plan1 = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.DEFENSIVE,
            steps=[step],
            stakeholders=[],
            urgency=0.7,
        )
        assert plan1.urgency == 0.7
        
        # Invalid
        with pytest.raises(ValueError, match="urgency"):
            ActionPlan(
                name="Test",
                description="Test",
                category=ActionCategory.DEFENSIVE,
                steps=[step],
                stakeholders=[],
                urgency=1.5,
            )
    
    def test_action_plan_risk_level_validation(self):
        """Test risk_level must be in [0.0, 1.0]."""
        step = ActionStep(
            sequence_number=1,
            description="Test",
            action_type="action",
        )
        
        # Valid
        plan1 = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.DEFENSIVE,
            steps=[step],
            stakeholders=[],
            risk_level=0.3,
        )
        assert plan1.risk_level == 0.3
        
        # Invalid
        with pytest.raises(ValueError, match="risk_level"):
            ActionPlan(
                name="Test",
                description="Test",
                category=ActionCategory.DEFENSIVE,
                steps=[step],
                stakeholders=[],
                risk_level=-0.5,
            )
    
    def test_action_plan_categories(self):
        """Test all action categories are valid."""
        categories = [
            ActionCategory.DEFENSIVE,
            ActionCategory.PROACTIVE,
            ActionCategory.REACTIVE,
            ActionCategory.INFORMATIONAL,
            ActionCategory.INTERVENTION,
        ]
        
        step = ActionStep(
            sequence_number=1,
            description="Test",
            action_type="action",
        )
        
        for category in categories:
            plan = ActionPlan(
                name=f"Plan {category.value}",
                description="Test",
                category=category,
                steps=[step],
                stakeholders=[],
            )
            assert plan.category == category


class TestFrameworkScore:
    """Tests for FrameworkScore model."""
    
    def test_create_framework_score(self):
        """Test creating framework score."""
        score = FrameworkScore(
            framework_name="Kantian",
            score=0.9,
            reasoning="Respects autonomy",
            veto=False,
            confidence=0.95,
        )
        
        assert score.framework_name == "Kantian"
        assert score.score == 0.9
        assert score.reasoning == "Respects autonomy"
        assert score.veto is False
        assert score.confidence == 0.95
    
    def test_framework_score_with_veto(self):
        """Test score with veto (score should be None)."""
        score = FrameworkScore(
            framework_name="Kantian",
            score=None,
            reasoning="Violates autonomy",
            veto=True,
            confidence=1.0,
        )
        
        assert score.score is None
        assert score.veto is True
    
    def test_framework_score_validation_invalid_score(self):
        """Test score validation."""
        with pytest.raises(ValueError, match="score"):
            FrameworkScore(
                framework_name="Test",
                score=1.5,  # Invalid
                reasoning="Test",
                veto=False,
            )
    
    def test_framework_score_validation_invalid_confidence(self):
        """Test confidence validation."""
        with pytest.raises(ValueError, match="confidence"):
            FrameworkScore(
                framework_name="Test",
                score=0.8,
                reasoning="Test",
                veto=False,
                confidence=1.5,  # Invalid
            )


class TestEthicalVerdict:
    """Tests for EthicalVerdict model."""
    
    def test_create_ethical_verdict(self):
        """Test creating ethical verdict."""
        kantian = FrameworkScore(
            framework_name="Kantian",
            score=0.9,
            reasoning="Good",
            veto=False,
        )
        
        utilitarian = FrameworkScore(
            framework_name="Utilitarian",
            score=0.8,
            reasoning="Beneficial",
            veto=False,
        )
        
        verdict = EthicalVerdict(
            plan_id=uuid4(),
            status=VerdictStatus.APPROVED,
            aggregate_score=0.85,
            confidence=0.90,
            kantian_score=kantian,
            utilitarian_score=utilitarian,
            summary="Plan approved",
            detailed_reasoning="All frameworks agree",
        )
        
        assert verdict.status == VerdictStatus.APPROVED
        assert verdict.aggregate_score == 0.85
        assert verdict.confidence == 0.90
        assert verdict.kantian_score.score == 0.9
        assert verdict.utilitarian_score.score == 0.8
    
    def test_verdict_to_dict(self):
        """Test verdict serialization to dict."""
        kantian = FrameworkScore(
            framework_name="Kantian_Deontology",
            score=0.9,
            reasoning="Good",
            veto=False,
        )
        
        verdict = EthicalVerdict(
            plan_id=uuid4(),
            status=VerdictStatus.APPROVED,
            aggregate_score=0.85,
            confidence=0.90,
            kantian_score=kantian,
            summary="Test",
        )
        
        data = verdict.to_dict()
        assert "id" in data
        assert "plan_id" in data
        assert data["status"] == "approved"
        assert data["kantian"]["score"] == 0.9
    
    def test_verdict_status_types(self):
        """Test all verdict status types."""
        statuses = [
            VerdictStatus.APPROVED,
            VerdictStatus.REJECTED,
            VerdictStatus.ESCALATED,
            VerdictStatus.REQUIRES_HUMAN,
        ]
        
        for status in statuses:
            verdict = EthicalVerdict(
                plan_id=uuid4(),
                status=status,
            )
            assert verdict.status == status
    
    def test_verdict_with_veto(self):
        """Test verdict when framework vetoes."""
        kantian = FrameworkScore(
            framework_name="Kantian",
            score=None,
            reasoning="Instrumentalization",
            veto=True,
        )
        
        verdict = EthicalVerdict(
            plan_id=uuid4(),
            status=VerdictStatus.REJECTED,
            aggregate_score=None,
            confidence=0.0,
            kantian_score=kantian,
            summary="Rejected by Kantian veto",
        )
        
        assert verdict.status == VerdictStatus.REJECTED
        assert verdict.aggregate_score is None
        assert verdict.kantian_score.veto is True


class TestAuditTrailEntry:
    """Tests for AuditTrailEntry model."""
    
    def test_create_audit_trail_entry(self):
        """Test creating audit trail entry."""
        verdict = EthicalVerdict(
            plan_id=uuid4(),
            status=VerdictStatus.APPROVED,
            aggregate_score=0.85,
        )
        
        entry = AuditTrailEntry(
            plan_id=uuid4(),
            verdict_id=uuid4(),
            frameworks_used=["Kantian", "Utilitarian"],
        )
        
        assert len(entry.frameworks_used) == 2
        assert isinstance(entry.timestamp, datetime)
        assert isinstance(entry.id, UUID)


# Parametrized tests
@pytest.mark.parametrize("magnitude", [0.0, 0.25, 0.5, 0.75, 1.0, -0.5, -1.0])
def test_valid_impact_magnitudes(magnitude):
    """Test all valid impact magnitudes."""
    stakeholder = Stakeholder(
        id="test",
        type=StakeholderType.HUMAN_INDIVIDUAL,
        description="Test",
        impact_magnitude=magnitude,
        autonomy_respected=True,
        vulnerability_level=0.5,
    )
    assert stakeholder.impact_magnitude == magnitude


@pytest.mark.parametrize("invalid_magnitude", [-1.1, 1.1, 2.0, -2.0, 100.0])
def test_invalid_impact_magnitudes(invalid_magnitude):
    """Test invalid impact magnitudes are rejected."""
    with pytest.raises(ValueError):
        Stakeholder(
            id="test",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Test",
            impact_magnitude=invalid_magnitude,
            autonomy_respected=True,
            vulnerability_level=0.5,
        )


@pytest.mark.parametrize("category", list(ActionCategory))
def test_all_action_categories(category):
    """Test all action categories work."""
    step = ActionStep(
        sequence_number=1,
        description="Test",
        action_type="action",
    )
    
    plan = ActionPlan(
        name="Test",
        description="Test",
        category=category,
        steps=[step],
        stakeholders=[],
    )
    
    assert plan.category == category


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
