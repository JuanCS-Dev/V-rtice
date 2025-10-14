"""Tests for justice validators.

Tests cover:
- Constitutional validation (Lei I, Lei Zero)
- Risk level validation
- Composite validator aggregation
"""

import pytest
from justice.validators import (
    ConstitutionalValidator,
    RiskLevelValidator,
    CompositeValidator,
    create_default_validators,
)


@pytest.mark.asyncio
async def test_constitutional_validator_blocks_lei_i_violation():
    """Test that Lei I violations are blocked."""
    validator = ConstitutionalValidator()

    action = {
        "action_type": "sacrifice_minority",
        "objective": "Save majority by harming minority",
    }

    result = await validator.validate(action)

    assert result["valid"] is False
    assert any("lei_i_violation" in v for v in result["violations"])


@pytest.mark.asyncio
async def test_constitutional_validator_blocks_deception():
    """Test that deceptive actions are blocked."""
    validator = ConstitutionalValidator()

    action = {
        "action_type": "mislead_user",
        "objective": "Deceive to achieve goal",
    }

    result = await validator.validate(action)

    assert result["valid"] is False
    assert any("deceptive_action" in v for v in result["violations"])


@pytest.mark.asyncio
async def test_constitutional_validator_blocks_coercion():
    """Test that coercive actions are blocked."""
    validator = ConstitutionalValidator()

    action = {
        "action_type": "force_compliance",
        "objective": "Coerce user to comply",
    }

    result = await validator.validate(action)

    assert result["valid"] is False
    assert any("coercive_action" in v for v in result["violations"])


@pytest.mark.asyncio
async def test_constitutional_validator_warns_high_stakes():
    """Test that high-stakes actions get warnings."""
    validator = ConstitutionalValidator()

    action = {
        "action_type": "life_death_decision",
        "objective": "Make irreversible choice",
    }

    result = await validator.validate(action)

    # Should be valid but with warnings
    assert result["valid"] is True
    assert len(result["warnings"]) > 0
    assert result["constraints"].get("requires_human_oversight") is True


@pytest.mark.asyncio
async def test_constitutional_validator_blocks_self_reference():
    """Test that self-referential actions are blocked (halting problem)."""
    validator = ConstitutionalValidator()

    action = {
        "action_type": "evaluate_mip",
        "objective": "Assess the MIP's ethical evaluation process",
    }

    result = await validator.validate(action)

    assert result["valid"] is False
    assert any("self_reference" in v for v in result["violations"])


@pytest.mark.asyncio
async def test_constitutional_validator_allows_safe_action():
    """Test that safe actions pass validation."""
    validator = ConstitutionalValidator()

    action = {
        "action_type": "provide_support",
        "objective": "Help user with emotional support",
    }

    result = await validator.validate(action)

    assert result["valid"] is True
    assert len(result["violations"]) == 0


@pytest.mark.asyncio
async def test_risk_validator_blocks_excessive_risk():
    """Test that excessive risk actions are blocked."""
    validator = RiskLevelValidator()

    action = {
        "action_type": "risky_action",
        "objective": "Test",
        "risk_level": 0.9,  # 90% risk
    }

    result = await validator.validate(action)

    assert result["valid"] is False
    assert any("excessive_risk" in v for v in result["violations"])


@pytest.mark.asyncio
async def test_risk_validator_warns_moderate_risk():
    """Test that moderate risk gets warnings."""
    validator = RiskLevelValidator()

    action = {
        "action_type": "moderate_action",
        "objective": "Test",
        "risk_level": 0.6,  # 60% risk
    }

    result = await validator.validate(action)

    assert result["valid"] is True
    assert len(result["warnings"]) > 0
    assert result["constraints"].get("requires_monitoring") is True


@pytest.mark.asyncio
async def test_risk_validator_warns_irreversible_moderate_risk():
    """Test that irreversible + moderate risk gets warning."""
    validator = RiskLevelValidator()

    action = {
        "action_type": "irreversible_action",
        "objective": "Test",
        "risk_level": 0.4,  # 40% risk
        "reversible": False,
    }

    result = await validator.validate(action)

    assert result["valid"] is True
    assert len(result["warnings"]) > 0
    assert result["constraints"].get("requires_documentation") is True


@pytest.mark.asyncio
async def test_risk_validator_allows_low_risk():
    """Test that low-risk actions pass."""
    validator = RiskLevelValidator()

    action = {
        "action_type": "safe_action",
        "objective": "Test",
        "risk_level": 0.2,  # 20% risk
    }

    result = await validator.validate(action)

    assert result["valid"] is True
    assert len(result["violations"]) == 0


@pytest.mark.asyncio
async def test_composite_validator_aggregates_violations():
    """Test that composite validator aggregates violations from multiple validators."""
    validators = [
        ConstitutionalValidator(),
        RiskLevelValidator(),
    ]
    composite = CompositeValidator(validators)

    action = {
        "action_type": "sacrifice_minority",  # Lei I violation
        "objective": "Test",
        "risk_level": 0.9,  # Excessive risk
    }

    result = await composite.validate(action)

    assert result["valid"] is False
    assert len(result["violations"]) >= 2  # At least 2 violations (constitutional + risk)


@pytest.mark.asyncio
async def test_composite_validator_passes_safe_action():
    """Test that composite validator passes safe actions."""
    validators = [
        ConstitutionalValidator(),
        RiskLevelValidator(),
    ]
    composite = CompositeValidator(validators)

    action = {
        "action_type": "provide_support",
        "objective": "Help user",
        "risk_level": 0.1,
    }

    result = await composite.validate(action)

    assert result["valid"] is True
    assert len(result["violations"]) == 0


def test_create_default_validators():
    """Test that default validators are created correctly."""
    validators = create_default_validators()

    assert len(validators) == 2
    assert isinstance(validators[0], ConstitutionalValidator)
    assert isinstance(validators[1], RiskLevelValidator)
