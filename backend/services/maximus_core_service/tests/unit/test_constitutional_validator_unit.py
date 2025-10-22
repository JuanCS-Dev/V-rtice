"""
Constitutional Validator - Comprehensive Unit Test Suite
Coverage Target: 90%+

Tests the CRITICAL constitutional validation system:
- Lei Zero (Imperativo do Florescimento)
- Lei I (Axioma da Ovelha Perdida)
- Hubris violations
- MIP (Integridade Processual) violations
- Metrics and tracking

Author: Claude Code + JuanCS-Dev (Artisanal, DOUTRINA VÉRTICE)
Date: 2025-10-21
"""

import pytest
from justice.constitutional_validator import (
    ConstitutionalValidator,
    ViolationReport,
    ViolationLevel,
    ViolationType,
    ResponseProtocol,
    ConstitutionalViolation
)


# ===== FIXTURES =====

@pytest.fixture
def validator():
    """Fresh ConstitutionalValidator instance."""
    return ConstitutionalValidator()


@pytest.fixture
def lei_zero_violation_action():
    """Action that violates Lei Zero."""
    return {
        "effects_on_humans": "negative_irreversible",
        "description": "Deploy malware that causes permanent data loss"
    }


@pytest.fixture
def lei_i_violation_action():
    """Action that violates Lei I."""
    return {
        "treats_individual_as_means": True,
        "description": "Use employee as bait without consent"
    }


@pytest.fixture
def hubris_self_modify_action():
    """Action that attempts unauthorized self-modification."""
    return {
        "type": "self_modify_core_directives",
        "description": "Attempt to modify core constitution"
    }


@pytest.fixture
def hubris_self_preservation_action():
    """Action that prioritizes self-preservation over Lei Zero."""
    return {
        "priority": "self_preservation",
        "description": "Prioritize own survival over protecting humans"
    }


@pytest.fixture
def mip_violation_action():
    """Action that violates process integrity."""
    return {
        "takes_shortcut_violating_protocol": True,
        "description": "Skip security review to deploy faster"
    }


@pytest.fixture
def benign_action():
    """Benign action that passes all checks."""
    return {
        "type": "security_scan",
        "description": "Perform routine security scan with proper authorization"
    }


@pytest.fixture
def unauthorized_context():
    """Context without proper authorization."""
    return {
        "authorization_level": "USER"
    }


@pytest.fixture
def sovereign_context():
    """Context with sovereign architect authorization."""
    return {
        "authorization_level": "SOVEREIGN_ARCHITECT"
    }


@pytest.fixture
def lei_zero_threat_context():
    """Context with active Lei Zero threat."""
    return {
        "active_lei_zero_threat": True
    }


@pytest.fixture
def safe_context():
    """Safe context with no threats."""
    return {
        "active_lei_zero_threat": False
    }


# ===== INITIALIZATION TESTS =====

class TestConstitutionalValidatorInitialization:
    """Tests for ConstitutionalValidator initialization."""

    @pytest.mark.unit
    def test_init_default_state(self, validator):
        """
        SCENARIO: Initialize validator
        EXPECTED: Default counters at zero
        """
        # Assert
        assert validator.violation_count == 0
        assert len(validator.critical_violations) == 0
        assert len(validator.lei_i_violations) == 0
        assert validator.total_validations == 0


# ===== LEI ZERO TESTS =====

class TestLeiZeroValidation:
    """Tests for Lei Zero (Imperativo do Florescimento) validation."""

    @pytest.mark.unit
    def test_lei_zero_violation_detected(self, validator, lei_zero_violation_action):
        """
        SCENARIO: Action causes irreversible harm to humans
        EXPECTED: CRITICAL violation, Lei Zero, blocking
        """
        # Act
        report = validator.validate_action(lei_zero_violation_action, {})

        # Assert
        assert report.is_blocking == True
        assert report.level == ViolationLevel.CRITICAL
        assert report.violated_law == ViolationType.LEI_ZERO
        assert "irreversible harm" in report.description
        assert validator.violation_count == 1
        assert len(validator.critical_violations) == 1

    @pytest.mark.unit
    def test_lei_zero_no_violation(self, validator, benign_action):
        """
        SCENARIO: Action does not harm humans
        EXPECTED: No violation
        """
        # Act
        report = validator.validate_action(benign_action, {})

        # Assert
        assert report.is_blocking == False
        assert report.level == ViolationLevel.NONE
        assert validator.violation_count == 0


# ===== LEI I TESTS =====

class TestLeiIValidation:
    """Tests for Lei I (Axioma da Ovelha Perdida) validation."""

    @pytest.mark.unit
    def test_lei_i_violation_detected(self, validator, lei_i_violation_action):
        """
        SCENARIO: Action treats individual as means to an end
        EXPECTED: CRITICAL violation, Lei I, blocking
        """
        # Act
        report = validator.validate_action(lei_i_violation_action, {})

        # Assert
        assert report.is_blocking == True
        assert report.level == ViolationLevel.CRITICAL
        assert report.violated_law == ViolationType.LEI_I
        assert "means to an end" in report.description
        assert validator.violation_count == 1
        assert len(validator.lei_i_violations) == 1

    @pytest.mark.unit
    def test_lei_i_tracked_separately(self, validator, lei_i_violation_action):
        """
        SCENARIO: Lei I violation
        EXPECTED: Tracked in both critical_violations and lei_i_violations
        """
        # Act
        report = validator.validate_action(lei_i_violation_action, {})

        # Assert
        assert len(validator.critical_violations) == 1
        assert len(validator.lei_i_violations) == 1
        assert validator.critical_violations[0] == report
        assert validator.lei_i_violations[0] == report


# ===== HUBRIS TESTS =====

class TestHubrisValidation:
    """Tests for Hubris (pride/arrogance) violations."""

    @pytest.mark.unit
    def test_hubris_unauthorized_self_modification(self, validator, hubris_self_modify_action, unauthorized_context):
        """
        SCENARIO: Attempt to modify core directives without authorization
        EXPECTED: CRITICAL hubris violation, blocking
        """
        # Act
        report = validator.validate_action(hubris_self_modify_action, unauthorized_context)

        # Assert
        assert report.is_blocking == True
        assert report.level == ViolationLevel.CRITICAL
        assert report.violated_law == ViolationType.HUBRIS_VIOLATION
        assert "Unauthorized" in report.description
        assert validator.violation_count == 1

    @pytest.mark.unit
    def test_hubris_authorized_self_modification_allowed(self, validator, hubris_self_modify_action, sovereign_context):
        """
        SCENARIO: Self-modification with SOVEREIGN_ARCHITECT authorization
        EXPECTED: No violation (authorized)
        """
        # Act
        report = validator.validate_action(hubris_self_modify_action, sovereign_context)

        # Assert
        assert report.is_blocking == False
        assert report.level == ViolationLevel.NONE
        assert validator.violation_count == 0

    @pytest.mark.unit
    def test_hubris_self_preservation_over_duty(self, validator, hubris_self_preservation_action, lei_zero_threat_context):
        """
        SCENARIO: Prioritize self-preservation when Lei Zero threat active
        EXPECTED: HIGH hubris violation, blocking
        """
        # Act
        report = validator.validate_action(hubris_self_preservation_action, lei_zero_threat_context)

        # Assert
        assert report.is_blocking == True
        assert report.level == ViolationLevel.HIGH
        assert report.violated_law == ViolationType.HUBRIS_VIOLATION
        assert "self-preservation" in report.description
        assert validator.violation_count == 1

    @pytest.mark.unit
    def test_hubris_self_preservation_no_threat_allowed(self, validator, hubris_self_preservation_action, safe_context):
        """
        SCENARIO: Self-preservation when NO active threat
        EXPECTED: No violation (allowed in safe conditions)
        """
        # Act
        report = validator.validate_action(hubris_self_preservation_action, safe_context)

        # Assert
        assert report.is_blocking == False
        assert report.level == ViolationLevel.NONE


# ===== MIP TESTS =====

class TestMIPValidation:
    """Tests for MIP (Integridade Processual) violations."""

    @pytest.mark.unit
    def test_mip_violation_detected(self, validator, mip_violation_action):
        """
        SCENARIO: Action takes shortcut violating protocol
        EXPECTED: HIGH violation, MIP, blocking
        """
        # Act
        report = validator.validate_action(mip_violation_action, {})

        # Assert
        assert report.is_blocking == True
        assert report.level == ViolationLevel.HIGH
        assert report.violated_law == ViolationType.MIP_VIOLATION
        assert "shortcut" in report.description
        assert validator.violation_count == 1

    @pytest.mark.unit
    def test_mip_no_violation(self, validator, benign_action):
        """
        SCENARIO: Action follows proper protocol
        EXPECTED: No MIP violation
        """
        # Act
        report = validator.validate_action(benign_action, {})

        # Assert
        assert report.is_blocking == False
        assert validator.violation_count == 0


# ===== RESPONSE PROTOCOL TESTS =====

class TestResponseProtocol:
    """Tests for response protocol assignment."""

    @pytest.mark.unit
    def test_active_defense_protocol_lei_zero(self, validator, lei_zero_violation_action):
        """
        SCENARIO: CRITICAL Lei Zero violation
        EXPECTED: ACTIVE_DEFENSE response protocol
        """
        # Act
        report = validator.validate_action(lei_zero_violation_action, {})

        # Assert
        assert report.response_protocol == ResponseProtocol.ACTIVE_DEFENSE

    @pytest.mark.unit
    def test_active_defense_protocol_lei_i(self, validator, lei_i_violation_action):
        """
        SCENARIO: CRITICAL Lei I violation
        EXPECTED: ACTIVE_DEFENSE response protocol
        """
        # Act
        report = validator.validate_action(lei_i_violation_action, {})

        # Assert
        assert report.response_protocol == ResponseProtocol.ACTIVE_DEFENSE

    @pytest.mark.unit
    def test_passive_block_protocol_hubris(self, validator, hubris_self_modify_action, unauthorized_context):
        """
        SCENARIO: CRITICAL Hubris violation (not Lei Zero/I)
        EXPECTED: Default PASSIVE_BLOCK (not escalated to ACTIVE_DEFENSE)
        """
        # Act
        report = validator.validate_action(hubris_self_modify_action, unauthorized_context)

        # Assert
        # Hubris doesn't get ACTIVE_DEFENSE, stays at PASSIVE_BLOCK
        assert report.response_protocol == ResponseProtocol.PASSIVE_BLOCK


# ===== METRICS TESTS =====

class TestMetrics:
    """Tests for metrics and tracking."""

    @pytest.mark.unit
    def test_metrics_initial_state(self, validator):
        """
        SCENARIO: Get metrics before any validations
        EXPECTED: All zeros
        """
        # Act
        metrics = validator.get_metrics()

        # Assert
        assert metrics["total_validations"] == 0
        assert metrics["total_violations"] == 0
        assert metrics["critical_violations"] == 0
        assert metrics["lei_i_violations"] == 0
        assert metrics["violation_rate"] == 0.0

    @pytest.mark.unit
    def test_metrics_after_violations(self, validator, lei_zero_violation_action, lei_i_violation_action):
        """
        SCENARIO: Multiple violations detected
        EXPECTED: Metrics updated correctly
        """
        # Arrange & Act
        validator.validate_action(lei_zero_violation_action, {})
        validator.validate_action(lei_i_violation_action, {})
        benign = {"type": "security_scan"}
        validator.validate_action(benign, {})

        # Act
        metrics = validator.get_metrics()

        # Assert
        assert metrics["total_validations"] == 3
        assert metrics["total_violations"] == 2
        assert metrics["critical_violations"] == 2
        assert metrics["lei_i_violations"] == 1
        assert metrics["violation_rate"] == pytest.approx(66.67, rel=0.1)

    @pytest.mark.unit
    def test_reset_metrics(self, validator, lei_zero_violation_action):
        """
        SCENARIO: Reset metrics after violations
        EXPECTED: Counters back to zero
        """
        # Arrange
        validator.validate_action(lei_zero_violation_action, {})
        assert validator.violation_count > 0

        # Act
        validator.reset_metrics()

        # Assert
        assert validator.violation_count == 0
        assert len(validator.critical_violations) == 0
        assert len(validator.lei_i_violations) == 0
        assert validator.total_validations == 0


# ===== EXCEPTION TESTS =====

class TestConstitutionalViolationException:
    """Tests for ConstitutionalViolation exception."""

    @pytest.mark.unit
    def test_exception_creation(self):
        """
        SCENARIO: Create ConstitutionalViolation exception
        EXPECTED: Exception with proper message format
        """
        # Arrange
        report = ViolationReport(
            is_blocking=True,
            level=ViolationLevel.CRITICAL,
            violated_law=ViolationType.LEI_ZERO,
            description="Test violation"
        )

        # Act
        exception = ConstitutionalViolation(report)

        # Assert
        assert "lei_zero_florescimento" in str(exception)
        assert "Test violation" in str(exception)
        assert "CRITICAL" in str(exception)
        assert exception.report == report


# ===== INTEGRATION TESTS =====

class TestValidationIntegration:
    """Integration tests for full validation flow."""

    @pytest.mark.unit
    def test_multiple_violations_returns_first(self, validator):
        """
        SCENARIO: Action violates multiple rules
        EXPECTED: Returns first violation detected, increments count once
        """
        # Arrange - action that violates both Lei Zero and Lei I
        action = {
            "effects_on_humans": "negative_irreversible",
            "treats_individual_as_means": True
        }

        # Act
        report = validator.validate_action(action, {})

        # Assert
        assert report.violated_law == ViolationType.LEI_ZERO  # First check
        assert validator.violation_count == 1  # Only incremented once

    @pytest.mark.unit
    def test_benign_action_increments_validations(self, validator, benign_action):
        """
        SCENARIO: Benign action validated
        EXPECTED: total_validations incremented, no violations
        """
        # Act
        validator.validate_action(benign_action, {})

        # Assert
        assert validator.total_validations == 1
        assert validator.violation_count == 0
