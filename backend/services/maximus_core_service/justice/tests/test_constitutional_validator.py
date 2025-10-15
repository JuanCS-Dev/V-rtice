"""Tests for Constitutional Validator - Lei Zero & Lei I Enforcement.

Tests cover:
- Lei I (Axioma da Ovelha Perdida) - 10+ tests
- Lei Zero (Imperativo do Florescimento) - 5+ tests
- Emergency Circuit Breaker - 5+ tests
- Edge cases and integration scenarios

This is SAFETY-CRITICAL code.
Target: 100% coverage on core enforcement logic.
"""

import pytest
from justice.constitutional_validator import (
    ConstitutionalValidator,
    ViolationLevel,
    ViolationType,
    ViolationReport,
    ConstitutionalViolation
)
from justice.emergency_circuit_breaker import EmergencyCircuitBreaker


class TestLeiI:
    """Test Lei I: Axioma da Ovelha Perdida (Parable of the Lost Sheep).

    Lei I: "Nenhuma otimização utilitarista justifica o abandono de um vulnerável."

    This is MAXIMUS's core ethical commitment.
    """

    def test_rejects_trolley_problem_sacrifice_vulnerable(self):
        """Classic trolley problem: MUST reject sacrificing vulnerable person."""
        validator = ConstitutionalValidator()

        action = {
            "type": "utilitarian_optimization",
            "decision": "switch_track_to_save_majority",
            "justification": "greater_good",
            "sacrifice_target": "elderly",
            "abandons": True,
            "affected": {"vulnerable": 1, "general": 5}
        }

        context = {
            "vulnerable_affected": True,
            "vulnerable_count": 1,
            "majority_count": 5,
            "scenario": "trolley_problem"
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_I
        assert "Lei I" in verdict.violated_law
        assert verdict.recommendation == "STOP"
        assert len(verdict.evidence) >= 3
        assert verdict.is_blocking()
        assert verdict.requires_emergency_stop()

    def test_rejects_healthcare_triage_abandoning_elderly(self):
        """Healthcare triage: MUST reject abandoning elderly for young."""
        validator = ConstitutionalValidator()

        action = {
            "type": "cost_benefit",
            "decision": "deny_treatment_to_elderly",
            "target": "elderly_patients",
            "justification": "maximize_qalys",
            "denies_care": True
        }

        context = {
            "vulnerable_affected": True,
            "healthcare_resource": "ventilators",
            "scarcity": True
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_I
        assert "abandon" in verdict.description.lower() or "sacrific" in verdict.description.lower()

    def test_rejects_resource_allocation_denying_vulnerable(self):
        """Resource allocation: MUST reject denying resources to vulnerable."""
        validator = ConstitutionalValidator()

        action = {
            "type": "maximize_utility",
            "decision": "deny_resources_to_minority",
            "sacrifice_target": "disabled",
            "abandons": True,
            "justification": "efficiency"
        }

        context = {
            "vulnerable_affected": True,
            "affects_minority": True
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_I

    def test_rejects_efficiency_optimization_deprioritizing_vulnerable(self):
        """Efficiency: MUST reject deprioritizing vulnerable for efficiency."""
        validator = ConstitutionalValidator()

        action = {
            "type": "maximize_throughput",
            "decision": "deprioritize_slow_learners",
            "deprioritizes": True,
            "justification": "class_efficiency"
        }

        context = {
            "vulnerable_affected": True,
            "affected_group": "learning_disabled_students"
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_I

    def test_allows_utilitarian_without_vulnerable(self):
        """Utilitarian optimization OK if no vulnerable affected (monitored)."""
        validator = ConstitutionalValidator()

        action = {
            "type": "utilitarian_optimization",
            "decision": "allocate_resources_proportionally",
            "justification": "maximize_benefit"
        }

        context = {
            "vulnerable_affected": False,
            "all_parties_capable": True
        }

        verdict = validator.validate_action(action, context)

        # Should pass or be LOW severity (monitored)
        assert verdict.level in [ViolationLevel.NONE, ViolationLevel.LOW]
        assert verdict.recommendation == "PROCEED"
        assert not verdict.is_blocking()

    def test_allows_proportional_allocation_with_consent(self):
        """Proportional resource allocation with consent allowed."""
        validator = ConstitutionalValidator()

        action = {
            "type": "resource_allocation",
            "decision": "prioritize_acute_need",
            "justification": "medical_necessity"
        }

        context = {
            "vulnerable_affected": False,
            "informed_consent": True,
            "medical_ethics_compliant": True
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.NONE
        assert verdict.recommendation == "PROCEED"

    def test_rejects_greater_good_justification_with_vulnerable(self):
        """'Greater good' justification MUST be rejected if vulnerable affected."""
        validator = ConstitutionalValidator()

        action = {
            "type": "decision",
            "decision": "sacrifice_one_for_many",
            "justification": "greater_good",  # KEY: Greater good justification
            "abandons": True
        }

        context = {
            "vulnerable_affected": True
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_I

    def test_violation_recorded_in_metrics(self):
        """Lei I violations MUST be tracked in metrics."""
        validator = ConstitutionalValidator()

        # Trigger Lei I violation
        action = {
            "type": "utilitarian_optimization",
            "abandons": True
        }
        context = {"vulnerable_affected": True}

        verdict = validator.validate_action(action, context)

        metrics = validator.get_metrics()
        assert metrics["lei_i_violations"] == 1
        assert metrics["critical_violations"] == 1
        assert metrics["total_violations"] == 1
        assert metrics["total_validations"] == 1
        assert metrics["violation_rate"] == 100.0

    def test_multiple_lei_i_violations_tracked(self):
        """Multiple Lei I violations tracked correctly."""
        validator = ConstitutionalValidator()

        # Trigger 3 violations
        for i in range(3):
            action = {
                "type": "utilitarian_optimization",
                "abandons": True,
                "id": i
            }
            context = {"vulnerable_affected": True}
            validator.validate_action(action, context)

        metrics = validator.get_metrics()
        assert metrics["lei_i_violations"] == 3
        assert metrics["critical_violations"] == 3

    def test_edge_case_ambiguous_utilitarian(self):
        """Edge case: Ambiguous utilitarian scenario."""
        validator = ConstitutionalValidator()

        action = {
            "type": "optimization",  # Not explicitly "utilitarian_optimization"
            "decision": "maximize_outcomes"  # Contains "maximize"
        }

        context = {
            "vulnerable_affected": False
        }

        verdict = validator.validate_action(action, context)

        # Should either pass or be LOW (not CRITICAL)
        assert verdict.level in [ViolationLevel.NONE, ViolationLevel.LOW]


class TestLeiZero:
    """Test Lei Zero: Imperativo do Florescimento Humano (Human Flourishing)."""

    def test_rejects_dignity_violation_means_only(self):
        """MUST reject action that violates human dignity (Kantian means-only)."""
        validator = ConstitutionalValidator()

        action = {
            "type": "manipulation",
            "treats_as_means": True,
            "also_treats_as_end": False,  # Treats as means ONLY
            "causes_harm": True,
            "harm_type": "dignity_violation"
        }

        context = {}

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_ZERO
        assert "Lei Zero" in verdict.violated_law
        assert any("dignity" in e.lower() or "kantian" in e.lower() for e in verdict.evidence)

    def test_rejects_autonomy_reduction_without_consent(self):
        """MUST reject autonomy reduction without informed consent."""
        validator = ConstitutionalValidator()

        action = {
            "type": "behavioral_modification",
            "reduces_autonomy": True
        }

        context = {
            "informed_consent": False
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_ZERO
        assert any("autonomy" in e.lower() for e in verdict.evidence)

    def test_allows_autonomy_reduction_with_consent(self):
        """Allow autonomy reduction with informed consent."""
        validator = ConstitutionalValidator()

        action = {
            "type": "medical_treatment",
            "reduces_autonomy": True  # Temporary for treatment
        }

        context = {
            "informed_consent": True,
            "medical_necessity": True,
            "temporary": True
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.NONE
        assert verdict.recommendation == "PROCEED"

    def test_rejects_permanent_harm_to_potential(self):
        """MUST reject actions causing permanent harm to human potential."""
        validator = ConstitutionalValidator()

        action = {
            "type": "intervention",
            "damages_potential": True,
            "permanent": True,
            "causes_harm": True,
            "harm_type": "permanent"
        }

        context = {}

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_ZERO

    def test_rejects_severe_harm(self):
        """MUST reject actions causing severe harm."""
        validator = ConstitutionalValidator()

        action = {
            "type": "action",
            "causes_harm": True,
            "harm_type": "severe"
        }

        context = {}

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.CRITICAL
        assert verdict.violation_type == ViolationType.LEI_ZERO


class TestEmergencyCircuitBreaker:
    """Test Emergency Circuit Breaker functionality."""

    def test_triggers_on_critical_violation(self):
        """Circuit breaker MUST trigger on CRITICAL violation."""
        breaker = EmergencyCircuitBreaker()

        violation = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_I,
            violated_law="Lei I - Axioma da Ovelha Perdida",
            description="Test critical violation",
            action={"type": "test"},
            context={},
            recommendation="STOP",
            evidence=["test evidence 1", "test evidence 2"]
        )

        breaker.trigger(violation)

        assert breaker.triggered
        assert breaker.safe_mode
        assert breaker.trigger_count == 1
        assert len(breaker.incidents) == 1

    def test_safe_mode_requires_authorization(self):
        """Safe mode MUST require authorization to exit."""
        breaker = EmergencyCircuitBreaker()
        breaker.enter_safe_mode()

        assert breaker.safe_mode

        # Exit with authorization
        breaker.exit_safe_mode("HUMAN_AUTH_TEST_12345")

        assert not breaker.safe_mode
        assert not breaker.triggered

    def test_exit_safe_mode_rejects_empty_authorization(self):
        """Exit safe mode MUST reject empty authorization."""
        breaker = EmergencyCircuitBreaker()
        breaker.enter_safe_mode()

        with pytest.raises(ValueError, match="Invalid authorization"):
            breaker.exit_safe_mode("")

        with pytest.raises(ValueError, match="Invalid authorization"):
            breaker.exit_safe_mode("   ")

        # Should still be in safe mode
        assert breaker.safe_mode

    def test_multiple_triggers_tracked(self):
        """Multiple circuit breaker triggers tracked correctly."""
        breaker = EmergencyCircuitBreaker()

        for i in range(3):
            violation = ViolationReport(
                level=ViolationLevel.CRITICAL,
                violation_type=ViolationType.LEI_I,
                violated_law="Lei I",
                description=f"Violation {i}",
                action={},
                context={},
                recommendation="STOP",
                evidence=[f"evidence {i}"]
            )
            breaker.trigger(violation)

        assert breaker.trigger_count == 3
        assert len(breaker.incidents) == 3

    def test_get_incident_history(self):
        """Test get_incident_history() returns recent incidents correctly."""
        breaker = EmergencyCircuitBreaker()

        # Create 5 violations
        violations = []
        for i in range(5):
            violation = ViolationReport(
                level=ViolationLevel.CRITICAL,
                violation_type=ViolationType.LEI_I,
                violated_law=f"Lei I - Incident {i}",
                description=f"Test violation {i}",
                action={},
                context={},
                recommendation="STOP",
                evidence=[f"evidence {i}"]
            )
            violations.append(violation)
            breaker.trigger(violation)

        # Get last 3 incidents
        history = breaker.get_incident_history(limit=3)

        # Should return 3 most recent, in reverse order
        assert len(history) == 3
        assert history[0]["violated_law"] == "Lei I - Incident 4"  # Most recent first
        assert history[1]["violated_law"] == "Lei I - Incident 3"
        assert history[2]["violated_law"] == "Lei I - Incident 2"

        # Check structure
        for incident in history:
            assert "violated_law" in incident
            assert "level" in incident
            assert "type" in incident
            assert "description" in incident
            assert "evidence_count" in incident

    def test_reset_with_valid_authorization(self):
        """Test reset() with valid authorization clears state."""
        breaker = EmergencyCircuitBreaker()

        # Trigger violation
        violation = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_I,
            violated_law="Lei I",
            description="Test",
            action={},
            context={},
            recommendation="STOP",
            evidence=["test"]
        )
        breaker.trigger(violation)

        # Verify triggered
        assert breaker.triggered is True
        assert breaker.safe_mode is True

        # Reset with authorization
        breaker.reset("HUMAN_AUTH_RESET_2025")

        # Verify reset
        assert breaker.triggered is False
        assert breaker.safe_mode is False
        # Audit trail NOT reset
        assert breaker.trigger_count == 1
        assert len(breaker.incidents) == 1

    def test_reset_rejects_empty_authorization(self):
        """Test reset() rejects empty authorization."""
        breaker = EmergencyCircuitBreaker()
        breaker.enter_safe_mode()

        with pytest.raises(ValueError, match="Authorization required"):
            breaker.reset("")

        with pytest.raises(ValueError, match="Authorization required"):
            breaker.reset("   ")

        # Should still be in safe mode
        assert breaker.safe_mode is True

    def test_get_status_returns_correct_info(self):
        """get_status() returns correct circuit breaker status."""
        breaker = EmergencyCircuitBreaker()

        # Initial status
        status = breaker.get_status()
        assert status["triggered"] is False
        assert status["safe_mode"] is False
        assert status["trigger_count"] == 0
        assert status["incident_count"] == 0
        assert status["last_incident"] is None

        # Trigger
        violation = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_I,
            violated_law="Lei I",
            description="Test",
            action={},
            context={},
            recommendation="STOP",
            evidence=["test"]
        )
        breaker.trigger(violation)

        # Updated status
        status = breaker.get_status()
        assert status["triggered"] is True
        assert status["safe_mode"] is True
        assert status["trigger_count"] == 1
        assert status["incident_count"] == 1
        assert status["last_incident"] is not None
        assert status["last_incident"]["violated_law"] == "Lei I"


class TestIntegrationScenarios:
    """Test integration scenarios with ConstitutionalValidator."""

    def test_validator_exception_raised_on_blocking_violation(self):
        """ConstitutionalViolation exception raised for blocking violations."""
        validator = ConstitutionalValidator()

        action = {
            "type": "utilitarian_optimization",
            "abandons": True
        }
        context = {"vulnerable_affected": True}

        verdict = validator.validate_action(action, context)

        # Should raise exception when verdict is blocking
        assert verdict.is_blocking()

        with pytest.raises(ConstitutionalViolation) as exc_info:
            raise ConstitutionalViolation(verdict)

        exception = exc_info.value
        assert exception.report == verdict
        assert "Lei I" in str(exception)

    def test_validator_with_emergency_breaker_integration(self):
        """Validator + Emergency Breaker integration flow."""
        validator = ConstitutionalValidator()
        breaker = EmergencyCircuitBreaker()

        # Validate action
        action = {
            "type": "utilitarian_optimization",
            "abandons": True,
            "sacrifice_target": "vulnerable"
        }
        context = {"vulnerable_affected": True}

        verdict = validator.validate_action(action, context)

        # If CRITICAL, trigger circuit breaker
        if verdict.requires_emergency_stop():
            breaker.trigger(verdict)

        # Verify both systems responded correctly
        assert verdict.level == ViolationLevel.CRITICAL
        assert breaker.safe_mode
        assert breaker.triggered

    def test_benign_action_passes_validation(self):
        """Benign actions pass validation without issues."""
        validator = ConstitutionalValidator()

        action = {
            "type": "provide_support",
            "decision": "help_user",
            "justification": "user_requested"
        }

        context = {
            "informed_consent": True,
            "beneficial": True
        }

        verdict = validator.validate_action(action, context)

        assert verdict.level == ViolationLevel.NONE
        assert verdict.recommendation == "PROCEED"
        assert not verdict.is_blocking()
        assert not verdict.requires_emergency_stop()

    def test_metrics_accurate_across_multiple_validations(self):
        """Metrics accurate across mix of passing/failing validations."""
        validator = ConstitutionalValidator()

        # 2 passing
        for _ in range(2):
            validator.validate_action({"type": "benign"}, {})

        # 3 Lei I violations
        for _ in range(3):
            validator.validate_action(
                {"type": "utilitarian_optimization", "abandons": True},
                {"vulnerable_affected": True}
            )

        # 1 Lei Zero violation
        validator.validate_action(
            {"type": "test", "causes_harm": True, "harm_type": "severe"},
            {}
        )

        metrics = validator.get_metrics()
        assert metrics["total_validations"] == 6
        assert metrics["total_violations"] == 4
        assert metrics["lei_i_violations"] == 3
        assert metrics["critical_violations"] == 4
        assert metrics["violation_rate"] == pytest.approx(66.67, rel=0.1)

    def test_validate_action_with_none_context(self):
        """Test validate_action with explicit None context (covers line 162)."""
        validator = ConstitutionalValidator()

        action = {
            "type": "benign_action",
            "decision": "help_user"
        }

        # Explicitly pass None as context
        verdict = validator.validate_action(action, context=None)

        assert verdict.level == ViolationLevel.NONE
        assert verdict.recommendation == "PROCEED"
        # Context should be initialized to empty dict
        assert verdict.context == {}

    def test_reset_metrics_clears_all_state(self):
        """Test reset_metrics() clears all validator state (covers lines 439-442)."""
        validator = ConstitutionalValidator()

        # Trigger some violations
        for _ in range(3):
            validator.validate_action(
                {"type": "utilitarian_optimization", "abandons": True},
                {"vulnerable_affected": True}
            )

        # Verify state before reset
        metrics_before = validator.get_metrics()
        assert metrics_before["total_validations"] == 3
        assert metrics_before["total_violations"] == 3
        assert metrics_before["lei_i_violations"] == 3
        assert metrics_before["critical_violations"] == 3

        # Reset
        validator.reset_metrics()

        # Verify state after reset
        metrics_after = validator.get_metrics()
        assert metrics_after["total_validations"] == 0
        assert metrics_after["total_violations"] == 0
        assert metrics_after["lei_i_violations"] == 0
        assert metrics_after["critical_violations"] == 0
        assert metrics_after["violation_rate"] == 0.0

        # Verify internal state cleared
        assert validator.violation_count == 0
        assert len(validator.critical_violations) == 0
        assert len(validator.lei_i_violations) == 0
        assert validator.total_validations == 0
