"""
Unit Tests - Base Framework Interface

Tests for the abstract EthicalFramework interface and validation methods.
"""

from uuid import uuid4

import pytest
from mip.base_framework import EthicalFramework
from mip.models import ActionCategory, ActionPlan, ActionStep, FrameworkScore


class ConcreteFramework(EthicalFramework):
    """Concrete implementation for testing."""

    @property
    def name(self) -> str:
        return "TestFramework"

    @property
    def version(self) -> str:
        return "1.0.0"

    def evaluate(self, plan: ActionPlan) -> FrameworkScore:
        return FrameworkScore(
            framework_name=self.name,
            score=0.5,
            reasoning="Test evaluation",
        )

    def can_veto(self) -> bool:
        return False


class TestEthicalFrameworkInterface:
    """Tests for EthicalFramework base class."""

    def test_validate_plan_with_valid_plan(self):
        """Test validation passes for valid plan."""
        framework = ConcreteFramework()
        plan = ActionPlan(
            name="Valid Plan",
            description="A valid action plan",
            category=ActionCategory.INFORMATIONAL,
            steps=[
                ActionStep(
                    sequence_number=1,
                    description="Step 1",
                    action_type="test"
                )
            ]
        )

        # Should not raise
        framework.validate_plan(plan)

    def test_validate_plan_rejects_empty_steps(self):
        """Test validation rejects plan with no steps."""
        framework = ConcreteFramework()

        # Create plan bypassing __post_init__ to test validate_plan
        invalid_plan = object.__new__(ActionPlan)
        invalid_plan.__dict__.update({
            'id': uuid4(),
            'name': 'Invalid Plan',
            'description': 'No steps',
            'category': ActionCategory.INFORMATIONAL,
            'steps': [],  # Empty!
            'stakeholders': [],
            'urgency': 0.5,
            'risk_level': 0.5,
            'reversibility': True,
            'novel_situation': False,
            'agent_justification': '',
            'expected_benefit': '',
            'submitted_by': 'test'
        })

        with pytest.raises(ValueError, match="pelo menos um step"):
            framework.validate_plan(invalid_plan)

    def test_validate_plan_rejects_empty_description(self):
        """Test validation rejects plan with no description."""
        framework = ConcreteFramework()

        # Create plan bypassing __post_init__
        invalid_plan = object.__new__(ActionPlan)
        invalid_plan.__dict__.update({
            'id': uuid4(),
            'name': 'Test',
            'description': '',  # Empty!
            'category': ActionCategory.INFORMATIONAL,
            'steps': [ActionStep(sequence_number=1, description="Step", action_type="test")],
            'stakeholders': [],
            'urgency': 0.5,
            'risk_level': 0.5,
            'reversibility': True,
            'novel_situation': False,
            'agent_justification': '',
            'expected_benefit': '',
            'submitted_by': 'test'
        })

        with pytest.raises(ValueError, match="descrição"):
            framework.validate_plan(invalid_plan)

    def test_concrete_implementation_required(self):
        """Test that abstract methods must be implemented."""
        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            EthicalFramework()  # type: ignore

    def test_framework_properties(self):
        """Test framework properties."""
        framework = ConcreteFramework()

        assert framework.name == "TestFramework"
        assert framework.version == "1.0.0"
        assert framework.can_veto() is False

    def test_framework_evaluate(self):
        """Test framework evaluation method."""
        framework = ConcreteFramework()
        plan = ActionPlan(
            name="Test Plan",
            description="Test",
            category=ActionCategory.INFORMATIONAL,
            steps=[ActionStep(sequence_number=1, description="Step", action_type="test")]
        )

        score = framework.evaluate(plan)

        assert score.framework_name == "TestFramework"
        assert score.score == 0.5
        assert score.reasoning == "Test evaluation"
