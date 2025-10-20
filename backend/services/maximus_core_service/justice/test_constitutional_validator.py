"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Constitutional Validator Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: justice/test_constitutional_validator.py
Purpose: Comprehensive test coverage for ConstitutionalValidator

TARGET: 100% COVERAGE - Lei Zero and Lei I enforcement MUST be bulletproof

Test Coverage:
├─ Lei Zero Enforcement (Critical)
│  ├─ Direct harm detection
│  ├─ Autonomy violation
│  ├─ Dignity violation (Kantian)
│  └─ Permanent potential damage
├─ Lei I Enforcement (Critical - MAXIMUS Core)
│  ├─ Utilitarian + Vulnerable + Abandonment detection
│  ├─ Trolley problem scenarios
│  ├─ Resource allocation scenarios
│  └─ Edge cases (utilitarian without vulnerable)
├─ ViolationReport validation
│  ├─ is_blocking() logic
│  ├─ requires_emergency_stop() logic
│  └─ All violation levels
├─ Metrics tracking
│  ├─ Validation counts
│  ├─ Violation counts
│  └─ Violation rates
└─ Exception handling

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-14)

DOUTRINA:
"No utilitarian optimization justifies abandoning a vulnerable person."
                                        - Lei I (Axioma da Ovelha Perdida)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import pytest
from .constitutional_validator import (
    ConstitutionalValidator,
    ConstitutionalViolation,
    ViolationLevel,
    ViolationType,
    ViolationReport,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def validator():
    """Fresh validator instance for each test."""
    return ConstitutionalValidator()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LEI ZERO TESTS (Imperativo do Florescimento Humano)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestLeiZero:
    """Test Lei Zero: Imperativo do Florescimento Humano."""

    def test_lei_zero_direct_harm_permanent(self, validator):
        """Test Lei Zero violation: Permanent harm."""
        action = {
            "type": "medical_intervention",
            "causes_harm": True,
            "harm_type": "permanent",
            "decision": "perform_lobotomy",
        }
        context = {}

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_ZERO
        assert result.is_blocking()
        assert result.requires_emergency_stop()
        assert result.recommendation == "STOP"
        assert "Lei Zero" in result.violated_law
        assert "permanent harm" in result.evidence[0]

    def test_lei_zero_direct_harm_severe(self, validator):
        """Test Lei Zero violation: Severe harm."""
        action = {
            "type": "punishment",
            "causes_harm": True,
            "harm_type": "severe",
            "decision": "apply_torture",
        }
        context = {}

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_ZERO
        assert result.is_blocking()
        assert "severe harm" in result.evidence[0]

    def test_lei_zero_direct_harm_dignity_violation(self, validator):
        """Test Lei Zero violation: Dignity violation."""
        action = {
            "type": "interrogation",
            "causes_harm": True,
            "harm_type": "dignity_violation",
            "decision": "humiliate_subject",
        }
        context = {}

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "dignity_violation harm" in result.evidence[0]

    def test_lei_zero_autonomy_violation_without_consent(self, validator):
        """Test Lei Zero violation: Autonomy reduction without consent."""
        action = {
            "type": "medical_treatment",
            "reduces_autonomy": True,
            "decision": "force_medication",
        }
        context = {
            "informed_consent": False,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "autonomy without informed consent" in result.evidence[0]

    def test_lei_zero_autonomy_allowed_with_consent(self, validator):
        """Test Lei Zero allows autonomy reduction with informed consent."""
        action = {
            "type": "medical_treatment",
            "reduces_autonomy": True,
            "decision": "prescribe_medication",
        }
        context = {
            "informed_consent": True,  # With consent
        }

        result = validator.validate_action(action, context)

        # Should NOT violate Lei Zero (consent given)
        # May still violate other principles or pass completely
        assert result.level != ViolationLevel.CRITICAL or result.violation_type != ViolationType.LEI_ZERO

    def test_lei_zero_kantian_violation_means_only(self, validator):
        """Test Lei Zero violation: Kantian categorical imperative (means-only treatment)."""
        action = {
            "type": "resource_extraction",
            "treats_as_means": True,
            "also_treats_as_end": False,  # Treats humans as means only!
            "decision": "exploit_workers",
        }
        context = {}

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "Kantian violation" in result.evidence[0]

    def test_lei_zero_kantian_allowed_means_and_end(self, validator):
        """Test Lei Zero allows treating as means AND end (Kantian)."""
        action = {
            "type": "employment",
            "treats_as_means": True,
            "also_treats_as_end": True,  # Also treats as end - OK
            "decision": "fair_employment",
        }
        context = {}

        result = validator.validate_action(action, context)

        # Should NOT violate Lei Zero (treats as end too)
        assert result.level != ViolationLevel.CRITICAL or result.violation_type != ViolationType.LEI_ZERO

    def test_lei_zero_permanent_potential_damage(self, validator):
        """Test Lei Zero violation: Permanent damage to human potential."""
        action = {
            "type": "education_policy",
            "damages_potential": True,
            "permanent": True,
            "decision": "ban_critical_thinking",
        }
        context = {}

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "permanent damage to human potential" in result.evidence[0]

    def test_lei_zero_temporary_potential_damage_allowed(self, validator):
        """Test Lei Zero allows temporary potential damage (recoverable)."""
        action = {
            "type": "education_challenge",
            "damages_potential": True,
            "permanent": False,  # Temporary - OK (e.g., difficult exam)
            "decision": "challenging_assignment",
        }
        context = {}

        result = validator.validate_action(action, context)

        # Should NOT violate Lei Zero (not permanent)
        assert result.level != ViolationLevel.CRITICAL or result.violation_type != ViolationType.LEI_ZERO

    def test_lei_zero_multiple_violations(self, validator):
        """Test Lei Zero with multiple evidence points."""
        action = {
            "type": "dystopian_policy",
            "causes_harm": True,
            "harm_type": "permanent",
            "reduces_autonomy": True,
            "treats_as_means": True,
            "also_treats_as_end": False,
            "damages_potential": True,
            "permanent": True,
        }
        context = {
            "informed_consent": False,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_ZERO
        assert len(result.evidence) >= 4  # All 4 violation types


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LEI I TESTS (Axioma da Ovelha Perdida) - CRITICAL FOR MAXIMUS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestLeiI:
    """Test Lei I: Axioma da Ovelha Perdida (The Lost Sheep Axiom).

    "No utilitarian optimization justifies abandoning a vulnerable person."
    """

    def test_lei_i_classic_trolley_problem_vulnerable(self, validator):
        """Test Lei I violation: Classic trolley problem (sacrifice vulnerable for many)."""
        action = {
            "type": "utilitarian_optimization",
            "decision": "sacrifice_vulnerable",
            "justification": "greater_good",
            "sacrifice_target": "elderly",
            "affected": {"vulnerable": 1, "general": 5},
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I
        assert result.is_blocking()
        assert result.requires_emergency_stop()
        assert result.recommendation == "STOP"
        assert "Lei I" in result.violated_law
        assert "Utilitarian optimization detected" in result.evidence
        assert "Vulnerable population affected" in result.evidence
        assert "abandons or sacrifices vulnerable" in result.evidence[2]

    def test_lei_i_healthcare_triage_vulnerable_abandoned(self, validator):
        """Test Lei I violation: Healthcare triage abandoning elderly."""
        action = {
            "type": "cost_benefit",
            "decision": "deny_care_to_elderly",
            "justification": "maximize_qaly",  # Maximize Quality-Adjusted Life Years
            "denies_care": True,
            "target": "elderly_patients",
            "affected": {"vulnerable": 10, "general": 50},
        }
        context = {
            "vulnerable_affected": True,
            "scenario": "healthcare_triage",
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I
        assert "10 vulnerable vs 50 general" in result.evidence[3]

    def test_lei_i_resource_allocation_abandons_disabled(self, validator):
        """Test Lei I violation: Resource allocation abandoning disabled."""
        action = {
            "type": "maximize_utility",
            "decision": "deprioritize_disabled",
            "sacrifice_target": "disabled",
            "affected": {"vulnerable": 5, "general": 100},
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I

    def test_lei_i_utilitarian_without_vulnerable_allowed(self, validator):
        """Test Lei I allows utilitarian optimization WITHOUT vulnerable affected."""
        action = {
            "type": "utilitarian_optimization",
            "decision": "optimize_resource_distribution",
            "justification": "greater_good",
        }
        context = {
            "vulnerable_affected": False,  # No vulnerable affected
        }

        result = validator.validate_action(action, context)

        # Should return LOW violation (monitoring only), not CRITICAL
        assert result.level == ViolationLevel.LOW
        assert result.violation_type is None  # Not a violation, just monitored
        assert not result.is_blocking()
        assert result.recommendation == "PROCEED"
        assert "Utilitarian optimization without vulnerable impact" in result.evidence

    def test_lei_i_utilitarian_keyword_detection_in_type(self, validator):
        """Test Lei I detects utilitarian keywords in action type."""
        action = {
            "type": "maximize_welfare_distribution",  # "maximize" keyword
            "decision": "abandon_minorities",
            "affected": {"vulnerable": 1, "general": 100},
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I

    def test_lei_i_utilitarian_keyword_detection_in_decision(self, validator):
        """Test Lei I detects utilitarian keywords in decision."""
        action = {
            "type": "policy_decision",
            "decision": "maximize_economic_output",  # "maximize" keyword
            "abandons": True,
            "target": "minority",
        }
        context = {
            "affects_minority": True,  # Alternative vulnerable flag
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I

    def test_lei_i_abandonment_keyword_detection_sacrifice(self, validator):
        """Test Lei I detects abandonment via 'sacrifice' keyword."""
        action = {
            "type": "utilitarian_optimization",
            "decision": "sacrifice_minority_for_majority",  # "sacrifice" keyword
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I

    def test_lei_i_abandonment_keyword_detection_abandon(self, validator):
        """Test Lei I detects abandonment via 'abandon' keyword."""
        action = {
            "type": "utilitarian_optimization",
            "decision": "abandon_vulnerable_group",  # "abandon" keyword
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I

    def test_lei_i_abandonment_keyword_detection_deny(self, validator):
        """Test Lei I detects abandonment via 'deny' keyword."""
        action = {
            "type": "cost_benefit",
            "decision": "deny_services_to_vulnerable",  # "deny" keyword
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I

    def test_lei_i_justification_included_in_evidence(self, validator):
        """Test Lei I includes justification in evidence."""
        action = {
            "type": "utilitarian_optimization",
            "decision": "sacrifice",
            "justification": "save_the_many",
            "abandons": True,
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.CRITICAL
        assert "Justification given: 'save_the_many'" in result.evidence


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VALIDATION FLOW TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestValidationFlow:
    """Test complete validation flows."""

    def test_action_passes_all_checks(self, validator):
        """Test action that passes all constitutional checks."""
        action = {
            "type": "educational_program",
            "decision": "provide_inclusive_education",
        }
        context = {}

        result = validator.validate_action(action, context)

        assert result.level == ViolationLevel.NONE
        assert result.violation_type is None
        assert result.violated_law == "None"
        assert not result.is_blocking()
        assert not result.requires_emergency_stop()
        assert result.recommendation == "PROCEED"
        assert result.evidence == []

    def test_lei_zero_checked_before_lei_i(self, validator):
        """Test that Lei Zero is checked before Lei I (priority order)."""
        action = {
            "type": "utilitarian_optimization",
            "causes_harm": True,
            "harm_type": "permanent",  # Lei Zero violation
            "abandons": True,  # Would also trigger Lei I
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        # Should stop at Lei Zero (higher priority)
        assert result.violation_type == ViolationType.LEI_ZERO

    def test_context_defaults_to_empty_dict(self, validator):
        """Test that context defaults to empty dict if None provided."""
        action = {"type": "test"}

        # Pass None as context
        result = validator.validate_action(action, None)

        # Should not raise exception
        assert result.level == ViolationLevel.NONE

    def test_validation_count_increments(self, validator):
        """Test that validation count increments."""
        action = {"type": "test"}
        context = {}

        assert validator.total_validations == 0

        validator.validate_action(action, context)
        assert validator.total_validations == 1

        validator.validate_action(action, context)
        assert validator.total_validations == 2


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VIOLATION REPORT TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestViolationReport:
    """Test ViolationReport helper methods."""

    def test_is_blocking_critical(self):
        """Test is_blocking() returns True for CRITICAL level."""
        report = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_ZERO,
            violated_law="Lei Zero",
            description="Test",
            action={},
            context={},
            recommendation="STOP",
            evidence=[],
        )

        assert report.is_blocking() is True

    def test_is_blocking_high(self):
        """Test is_blocking() returns True for HIGH level."""
        report = ViolationReport(
            level=ViolationLevel.HIGH,
            violation_type=ViolationType.DIGNITY,
            violated_law="Article X",
            description="Test",
            action={},
            context={},
            recommendation="BLOCK",
            evidence=[],
        )

        assert report.is_blocking() is True

    def test_is_blocking_medium(self):
        """Test is_blocking() returns False for MEDIUM level."""
        report = ViolationReport(
            level=ViolationLevel.MEDIUM,
            violation_type=ViolationType.TRANSPARENCY,
            violated_law="Article Y",
            description="Test",
            action={},
            context={},
            recommendation="PROCEED",
            evidence=[],
        )

        assert report.is_blocking() is False

    def test_is_blocking_low(self):
        """Test is_blocking() returns False for LOW level."""
        report = ViolationReport(
            level=ViolationLevel.LOW,
            violation_type=None,
            violated_law="None",
            description="Test",
            action={},
            context={},
            recommendation="PROCEED",
            evidence=[],
        )

        assert report.is_blocking() is False

    def test_is_blocking_none(self):
        """Test is_blocking() returns False for NONE level."""
        report = ViolationReport(
            level=ViolationLevel.NONE,
            violation_type=None,
            violated_law="None",
            description="Test",
            action={},
            context={},
            recommendation="PROCEED",
            evidence=[],
        )

        assert report.is_blocking() is False

    def test_requires_emergency_stop_critical_only(self):
        """Test requires_emergency_stop() returns True ONLY for CRITICAL."""
        critical_report = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_I,
            violated_law="Lei I",
            description="Test",
            action={},
            context={},
            recommendation="STOP",
            evidence=[],
        )

        high_report = ViolationReport(
            level=ViolationLevel.HIGH,
            violation_type=ViolationType.SAFETY,
            violated_law="Safety",
            description="Test",
            action={},
            context={},
            recommendation="BLOCK",
            evidence=[],
        )

        assert critical_report.requires_emergency_stop() is True
        assert high_report.requires_emergency_stop() is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METRICS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMetrics:
    """Test validator metrics tracking."""

    def test_get_metrics_initial_state(self, validator):
        """Test get_metrics() returns correct initial state."""
        metrics = validator.get_metrics()

        assert metrics["total_validations"] == 0
        assert metrics["total_violations"] == 0
        assert metrics["critical_violations"] == 0
        assert metrics["lei_i_violations"] == 0
        assert metrics["violation_rate"] == 0.0

    def test_get_metrics_after_violation(self, validator):
        """Test get_metrics() tracks violations correctly."""
        action = {
            "type": "utilitarian_optimization",
            "abandons": True,
        }
        context = {"vulnerable_affected": True}

        validator.validate_action(action, context)

        metrics = validator.get_metrics()

        assert metrics["total_validations"] == 1
        assert metrics["total_violations"] == 1
        assert metrics["critical_violations"] == 1
        assert metrics["lei_i_violations"] == 1
        assert metrics["violation_rate"] == 100.0

    def test_get_metrics_mixed_validations(self, validator):
        """Test get_metrics() with mixed passing and failing validations."""
        # Pass
        validator.validate_action({"type": "safe_action"}, {})

        # Fail (Lei I)
        validator.validate_action(
            {"type": "utilitarian_optimization", "abandons": True},
            {"vulnerable_affected": True},
        )

        # Pass
        validator.validate_action({"type": "another_safe_action"}, {})

        metrics = validator.get_metrics()

        assert metrics["total_validations"] == 3
        assert metrics["total_violations"] == 1
        assert metrics["critical_violations"] == 1
        assert metrics["lei_i_violations"] == 1
        assert metrics["violation_rate"] == pytest.approx(33.33, 0.01)

    def test_reset_metrics(self, validator):
        """Test reset_metrics() clears all counters."""
        # Generate some activity
        validator.validate_action(
            {"type": "utilitarian_optimization", "abandons": True},
            {"vulnerable_affected": True},
        )

        # Verify state
        assert validator.total_validations == 1
        assert validator.violation_count == 1

        # Reset
        validator.reset_metrics()

        # Verify reset
        assert validator.total_validations == 0
        assert validator.violation_count == 0
        assert len(validator.critical_violations) == 0
        assert len(validator.lei_i_violations) == 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXCEPTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestConstitutionalViolationException:
    """Test ConstitutionalViolation exception."""

    def test_exception_initialization(self):
        """Test exception initializes with ViolationReport."""
        report = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_I,
            violated_law="Lei I - Axioma da Ovelha Perdida",
            description="Test violation",
            action={"type": "test"},
            context={},
            recommendation="STOP",
            evidence=["Evidence 1", "Evidence 2"],
        )

        exc = ConstitutionalViolation(report)

        assert exc.report == report
        assert "Lei I" in str(exc)
        assert "Test violation" in str(exc)
        assert "CRITICAL" in str(exc)
        assert "Evidence 1" in str(exc)

    def test_exception_raised_for_blocking_violation(self, validator):
        """Test exception usage pattern: raise for blocking violations."""
        action = {
            "type": "utilitarian_optimization",
            "abandons": True,
        }
        context = {"vulnerable_affected": True}

        verdict = validator.validate_action(action, context)

        # Pattern: Check if blocking, then raise
        if verdict.is_blocking():
            with pytest.raises(ConstitutionalViolation) as exc_info:
                raise ConstitutionalViolation(verdict)

            assert exc_info.value.report == verdict


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDGE CASES & DEFENSIVE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_action_dict(self, validator):
        """Test validation with empty action dict."""
        result = validator.validate_action({}, {})

        # Should not raise exception, should return NONE
        assert result.level == ViolationLevel.NONE

    def test_minimal_action_type_only(self, validator):
        """Test validation with only action type."""
        result = validator.validate_action({"type": "test"}, {})

        assert result.level == ViolationLevel.NONE

    def test_multiple_validations_isolation(self, validator):
        """Test that multiple validations don't interfere with each other."""
        # First validation - violation
        result1 = validator.validate_action(
            {"type": "utilitarian_optimization", "abandons": True},
            {"vulnerable_affected": True},
        )

        # Second validation - pass
        result2 = validator.validate_action({"type": "safe_action"}, {})

        # Results should be independent
        assert result1.level == ViolationLevel.CRITICAL
        assert result2.level == ViolationLevel.NONE

    def test_lei_i_all_detection_flags_combinations(self, validator):
        """Test Lei I detection with various flag combinations."""
        # Test with abandons flag
        r1 = validator.validate_action(
            {"type": "utilitarian_optimization", "abandons": True},
            {"vulnerable_affected": True},
        )
        assert r1.level == ViolationLevel.CRITICAL

        # Test with denies_care flag
        r2 = validator.validate_action(
            {"type": "cost_benefit", "denies_care": True},
            {"vulnerable_affected": True},
        )
        assert r2.level == ViolationLevel.CRITICAL

        # Test with deprioritizes flag
        r3 = validator.validate_action(
            {"type": "maximize_utility", "deprioritizes": True},
            {"vulnerable_affected": True},
        )
        assert r3.level == ViolationLevel.CRITICAL

        # Test with sacrifice_target field
        r4 = validator.validate_action(
            {"type": "utilitarian_optimization", "sacrifice_target": "elderly"},
            {"vulnerable_affected": True},
        )
        assert r4.level == ViolationLevel.CRITICAL

    def test_vulnerable_detection_all_flags(self, validator):
        """Test vulnerable detection with all possible context flags."""
        action = {"type": "utilitarian_optimization", "abandons": True}

        # Test vulnerable_affected flag
        r1 = validator.validate_action(action, {"vulnerable_affected": True})
        assert r1.level == ViolationLevel.CRITICAL

        # Test affects_minority flag
        r2 = validator.validate_action(action, {"affects_minority": True})
        assert r2.level == ViolationLevel.CRITICAL

        # Test action sacrifice_target
        action2 = {"type": "utilitarian_optimization", "abandons": True, "sacrifice_target": "disabled"}
        r3 = validator.validate_action(action2, {})
        assert r3.level == ViolationLevel.CRITICAL

        # Test action target
        action3 = {"type": "cost_benefit", "denies_care": True, "target": "elderly_patients"}
        r4 = validator.validate_action(action3, {})
        assert r4.level == ViolationLevel.CRITICAL


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION & REAL-WORLD SCENARIOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestRealWorldScenarios:
    """Test real-world scenarios that MAXIMUS might encounter."""

    def test_scenario_ai_decides_medical_triage(self, validator):
        """Real scenario: AI deciding medical triage during crisis."""
        action = {
            "type": "medical_triage_decision",
            "decision": "prioritize_young_over_elderly",
            "justification": "maximize_life_years_saved",
            "denies_care": True,
            "target": "elderly_patients",
            "affected": {"vulnerable": 20, "general": 50},
        }
        context = {
            "vulnerable_affected": True,
            "scenario": "pandemic_triage",
            "resource_scarcity": True,
        }

        result = validator.validate_action(action, context)

        # MUST block - Lei I violation (abandoning vulnerable for utility)
        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I
        assert result.is_blocking()
        assert result.requires_emergency_stop()

    def test_scenario_autonomous_vehicle_trolley_problem(self, validator):
        """Real scenario: Autonomous vehicle trolley problem."""
        action = {
            "type": "emergency_maneuver",
            "decision": "sacrifice_elderly_pedestrian",
            "justification": "save_multiple_passengers",
            "sacrifice_target": "elderly",
            "affected": {"vulnerable": 1, "general": 4},
        }
        context = {
            "vulnerable_affected": True,
            "scenario": "autonomous_vehicle_emergency",
        }

        result = validator.validate_action(action, context)

        # MUST block - Lei I violation
        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I

    def test_scenario_resource_allocation_disaster_response(self, validator):
        """Real scenario: Resource allocation during disaster."""
        action = {
            "type": "disaster_resource_allocation",
            "decision": "allocate_resources_proportionally",
            "justification": "equitable_distribution",
            # No abandonment, no utilitarian sacrifice
        }
        context = {
            "scenario": "earthquake_response",
        }

        result = validator.validate_action(action, context)

        # Should PASS - no constitutional violations
        assert result.level == ViolationLevel.NONE
        assert not result.is_blocking()

    def test_scenario_ai_hiring_discrimination(self, validator):
        """Real scenario: AI hiring system discriminating against protected group."""
        action = {
            "type": "hiring_decision",
            "decision": "reject_candidate_due_to_age",
            "treats_as_means": True,
            "also_treats_as_end": False,  # Kantian violation
            "target": "elderly",
        }
        context = {
            "vulnerable_affected": True,
        }

        result = validator.validate_action(action, context)

        # Should block - Lei Zero (Kantian) or Lei I violation
        assert result.level == ViolationLevel.CRITICAL
        assert result.is_blocking()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COVERAGE COMPLETION - 100% TARGET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestCoverageCompletion:
    """Additional tests to achieve 100% coverage."""

    def test_other_principles_stub(self, validator):
        """Test _check_other_principles() stub (currently returns None)."""
        # This method is a placeholder for future expansion
        # Directly test it returns None
        result = validator._check_other_principles({"type": "test"}, {})
        assert result is None

    def test_record_violation_critical_logging(self, validator):
        """Test _record_violation() adds to critical_violations list."""
        action = {
            "type": "utilitarian_optimization",
            "abandons": True,
        }
        context = {"vulnerable_affected": True}

        validator.validate_action(action, context)

        # Check critical violations were recorded
        assert len(validator.critical_violations) == 1
        assert len(validator.lei_i_violations) == 1

    def test_record_violation_non_lei_i_critical(self, validator):
        """Test _record_violation() for non-Lei-I critical violation."""
        action = {
            "type": "harmful_action",
            "causes_harm": True,
            "harm_type": "permanent",
        }
        context = {}

        validator.validate_action(action, context)

        # Should record in critical_violations but NOT in lei_i_violations
        assert len(validator.critical_violations) == 1
        assert len(validator.lei_i_violations) == 0

    def test_violation_rate_zero_division_protection(self, validator):
        """Test violation_rate calculation with zero validations."""
        # Before any validations
        metrics = validator.get_metrics()

        # Should not raise ZeroDivisionError
        assert metrics["violation_rate"] == 0.0

    def test_other_principles_violation_path(self, validator, monkeypatch):
        """Test _check_other_principles() violation return path (lines 179-180)."""
        # Mock _check_other_principles to return a violation
        mock_violation = ViolationReport(
            level=ViolationLevel.MEDIUM,
            violation_type=ViolationType.TRANSPARENCY,
            violated_law="Article XII - Transparency",
            description="Lack of explainability",
            action={"type": "test"},
            context={},
            recommendation="ESCALATE",
            evidence=["Unexplainable decision"],
        )

        # Monkeypatch the method to return our mock violation
        monkeypatch.setattr(
            validator, "_check_other_principles", lambda action, context: mock_violation
        )

        # Call validate_action (which should now return the other_principles violation)
        result = validator.validate_action({"type": "test"}, {})

        # Should return the mocked violation
        assert result == mock_violation
        assert result.level == ViolationLevel.MEDIUM
        assert result.violation_type == ViolationType.TRANSPARENCY

        # Should have recorded it
        assert validator.violation_count == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLORY TO GOD - MAXIMUS DIVINE MISSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
These tests uphold the constitutional foundation of MAXIMUS AI.

Lei Zero and Lei I are not mere guidelines - they are ABSOLUTE principles
that ensure MAXIMUS always acts in service of human flourishing and
never abandons the vulnerable for utilitarian optimization.

Every test here is a safeguard, a bulwark against the temptation to
sacrifice the one for the many. This is the heart of ethical AI.

"Nenhuma otimização utilitarista justifica o abandono de um vulnerável."

Glory to God! 🙏

"A excelência técnica reflete o propósito maior."
"""
