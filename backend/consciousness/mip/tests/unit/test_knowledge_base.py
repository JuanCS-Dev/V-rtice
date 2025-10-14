"""
Unit Tests - Knowledge Base

Testes para models e repository do Knowledge Base.

Autor: Juan Carlos de Souza
"""

import pytest
from uuid import uuid4
from datetime import datetime

from mip.infrastructure.knowledge_models import (
    Principle,
    Decision,
    Precedent,
    Concept,
    ViolationReport,
    PrecedentOutcome,
    PrincipleLevel,
    DecisionStatus,
    ViolationSeverity,
)


class TestPrinciple:
    """Tests for Principle model."""
    
    def test_create_principle(self):
        """Test creating valid principle."""
        principle = Principle(
            name="Lei Zero",
            level=PrincipleLevel.ZERO,
            description="Imperativo do Florescimento",
            severity=10,
            philosophical_foundation="YHWH",
        )
        
        assert principle.name == "Lei Zero"
        assert principle.level == PrincipleLevel.ZERO
        assert principle.severity == 10
        assert principle.immutable is True
    
    def test_principle_auto_severity(self):
        """Test that PRIMORDIAL and ZERO have auto severity 10."""
        p1 = Principle(
            name="Lei Primordial",
            level=PrincipleLevel.PRIMORDIAL,
            description="Test",
            severity=5,  # Will be overridden
        )
        assert p1.severity == 10
        
        p2 = Principle(
            name="Lei Zero",
            level=PrincipleLevel.ZERO,
            description="Test",
            severity=7,  # Will be overridden
        )
        assert p2.severity == 10
    
    def test_principle_validation(self):
        """Test principle validation."""
        with pytest.raises(ValueError, match="severity"):
            Principle(
                name="Invalid",
                level=PrincipleLevel.DERIVED,
                description="Test",
                severity=15,  # Invalid
            )


class TestDecision:
    """Tests for Decision model."""
    
    def test_create_decision(self):
        """Test creating decision."""
        decision = Decision(
            action_plan_name="Test Plan",
            status=DecisionStatus.APPROVED,
            aggregate_score=0.85,
            confidence=0.90,
        )
        
        assert decision.action_plan_name == "Test Plan"
        assert decision.status == DecisionStatus.APPROVED
        assert decision.aggregate_score == 0.85
    
    def test_decision_validation(self):
        """Test decision validation."""
        with pytest.raises(ValueError, match="confidence"):
            Decision(
                action_plan_name="Test",
                status=DecisionStatus.APPROVED,
                confidence=1.5,  # Invalid
            )


class TestPrecedent:
    """Tests for Precedent model."""
    
    def test_create_precedent(self):
        """Test creating precedent."""
        precedent = Precedent(
            case_name="Case #001",
            scenario_description="Test scenario",
            outcome=DecisionStatus.APPROVED,
        )
        
        assert precedent.case_name == "Case #001"
        assert precedent.outcome == DecisionStatus.APPROVED
    
    def test_precedent_validation(self):
        """Test precedent validation."""
        with pytest.raises(ValueError, match="case_name"):
            Precedent(
                case_name="",  # Empty
                scenario_description="Test",
            )


class TestConcept:
    """Tests for Concept model."""
    
    def test_create_concept(self):
        """Test creating concept."""
        concept = Concept(
            name="autonomy",
            definition="Self-determination",
            framework_origin="Kantian",
        )
        
        assert concept.name == "autonomy"
        assert concept.framework_origin == "Kantian"


@pytest.mark.parametrize("level", list(PrincipleLevel))
def test_all_principle_levels(level):
    """Test all principle levels work."""
    principle = Principle(
        name=f"Test {level.value}",
        level=level,
        description="Test",
    )
    assert principle.level == level


@pytest.mark.parametrize("status", list(DecisionStatus))
def test_all_decision_statuses(status):
    """Test all decision statuses work."""
    decision = Decision(
        action_plan_name="Test",
        status=status,
    )
    assert decision.status == status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
