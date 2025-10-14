"""Unit tests for verdict models."""

import pytest
from datetime import datetime
import uuid
from pydantic import ValidationError

from motor_integridade_processual.models.verdict import (
    EthicalVerdict,
    FrameworkVerdict,
    RejectionReason,
    DecisionLevel,
    FrameworkName,
)


class TestRejectionReason:
    """Tests for RejectionReason model."""

    def test_create_rejection_reason(self) -> None:
        """Test creating rejection reason with all fields."""
        reason = RejectionReason(
            category="deception",
            description="Action involves misleading the user about consequences",
            severity=0.8,
            affected_stakeholders=["user_123"],
            violated_principle="Kant's Categorical Imperative",
            citation="Act only according to that maxim whereby you can...",
        )

        assert reason.category == "deception"
        assert reason.severity == 0.8
        assert len(reason.affected_stakeholders) == 1

    def test_rejection_reason_severity_bounds(self) -> None:
        """Test severity must be in [0, 1]."""
        # Valid
        reason = RejectionReason(
            category="harm",
            description="Minor potential harm",
            severity=0.3,
            violated_principle="Non-maleficence",
        )
        assert reason.severity == 0.3

        # Invalid: too high
        with pytest.raises(ValidationError):
            RejectionReason(
                category="harm",
                description="Invalid severity",
                severity=1.5,
                violated_principle="Test",
            )

    def test_rejection_reason_short_description_rejected(self) -> None:
        """Test description must be ≥10 chars."""
        with pytest.raises(ValidationError, match="at least 10 characters"):
            RejectionReason(
                category="test",
                description="Short",
                severity=0.5,
                violated_principle="Test",
            )


class TestFrameworkVerdict:
    """Tests for FrameworkVerdict model."""

    def test_create_approve_verdict(self) -> None:
        """Test creating approve verdict."""
        verdict = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Action respects autonomy and dignity of all persons",
        )

        assert verdict.framework_name == FrameworkName.KANTIAN
        assert verdict.decision == DecisionLevel.APPROVE
        assert verdict.confidence == 0.95

    def test_create_reject_verdict_with_reasons(self) -> None:
        """Test creating reject verdict with rejection reasons."""
        reason = RejectionReason(
            category="coercion",
            description="Action uses force without consent",
            severity=0.9,
            violated_principle="Autonomy",
        )

        verdict = FrameworkVerdict(
            framework_name=FrameworkName.PRINCIPIALISM,
            decision=DecisionLevel.REJECT,
            confidence=0.85,
            reasoning="Violates principle of autonomy",
            rejection_reasons=[reason],
        )

        assert verdict.decision == DecisionLevel.REJECT
        assert len(verdict.rejection_reasons) == 1
        assert verdict.rejection_reasons[0].severity == 0.9

    def test_reject_verdict_requires_reasons(self) -> None:
        """Test that REJECT verdict requires rejection_reasons."""
        with pytest.raises(ValidationError, match="rejection_reasons required"):
            FrameworkVerdict(
                framework_name=FrameworkName.KANTIAN,
                decision=DecisionLevel.REJECT,
                confidence=0.9,
                reasoning="Action violates categorical imperative",
                rejection_reasons=[],  # Missing!
            )

    def test_veto_verdict_requires_reasons(self) -> None:
        """Test that VETO verdict requires rejection_reasons."""
        with pytest.raises(ValidationError, match="rejection_reasons required"):
            FrameworkVerdict(
                framework_name=FrameworkName.KANTIAN,
                decision=DecisionLevel.VETO,
                confidence=1.0,
                reasoning="Absolute veto",
                rejection_reasons=[],  # Missing!
            )

    def test_approve_with_conditions_requires_conditions(self) -> None:
        """Test that APPROVE_WITH_CONDITIONS requires conditions."""
        with pytest.raises(ValidationError, match="conditions required"):
            FrameworkVerdict(
                framework_name=FrameworkName.UTILITARIAN,
                decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
                confidence=0.75,
                reasoning="Can approve with safeguards",
                conditions=[],  # Missing!
            )

    def test_approve_with_conditions_valid(self) -> None:
        """Test valid APPROVE_WITH_CONDITIONS verdict."""
        verdict = FrameworkVerdict(
            framework_name=FrameworkName.UTILITARIAN,
            decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
            confidence=0.8,
            reasoning="Maximizes utility with conditions",
            conditions=["Obtain explicit consent", "Monitor for 24 hours"],
        )

        assert len(verdict.conditions) == 2
        assert "consent" in verdict.conditions[0].lower()

    def test_framework_verdict_with_score(self) -> None:
        """Test framework verdict with numeric score."""
        verdict = FrameworkVerdict(
            framework_name=FrameworkName.UTILITARIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.9,
            score=0.85,
            reasoning="High utility score",
        )

        assert verdict.score == 0.85


class TestEthicalVerdict:
    """Tests for EthicalVerdict model."""

    def test_create_minimal_verdict(self) -> None:
        """Test creating verdict with minimal required fields."""
        kant_verdict = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Respects dignity",
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE,
            confidence=0.95,
            framework_verdicts={FrameworkName.KANTIAN: kant_verdict},
            resolution_method="unanimous",
            primary_reasons=["All frameworks approve"],
            processing_time_ms=150.5,
        )

        assert verdict.final_decision == DecisionLevel.APPROVE
        assert verdict.confidence == 0.95
        assert len(verdict.framework_verdicts) == 1

    def test_verdict_with_multiple_frameworks(self) -> None:
        """Test verdict with multiple framework verdicts."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Kantian reasoning",
        )

        mill = FrameworkVerdict(
            framework_name=FrameworkName.UTILITARIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.88,
            reasoning="Utilitarian reasoning",
        )

        aristotle = FrameworkVerdict(
            framework_name=FrameworkName.VIRTUE_ETHICS,
            decision=DecisionLevel.APPROVE,
            confidence=0.92,
            reasoning="Virtue ethics reasoning",
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE,
            confidence=0.92,
            framework_verdicts={
                FrameworkName.KANTIAN: kant,
                FrameworkName.UTILITARIAN: mill,
                FrameworkName.VIRTUE_ETHICS: aristotle,
            },
            resolution_method="unanimous_approval",
            primary_reasons=["All frameworks approve", "High confidence"],
            processing_time_ms=250.0,
        )

        assert len(verdict.framework_verdicts) == 3
        assert verdict.average_confidence() == pytest.approx((0.95 + 0.88 + 0.92) / 3)

    def test_verdict_action_plan_id_must_be_uuid(self) -> None:
        """Test that action_plan_id must be valid UUID."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Test reasoning here",
        )

        with pytest.raises(ValidationError):  # Invalid UUID
            EthicalVerdict(
                action_plan_id="not-a-uuid",
                final_decision=DecisionLevel.APPROVE,
                confidence=0.95,
                framework_verdicts={FrameworkName.KANTIAN: kant},
                resolution_method="unanimous",
                primary_reasons=["Test reason"],
                processing_time_ms=100.0,
            )

    def test_verdict_requires_framework_verdicts(self) -> None:
        """Test that at least one framework verdict is required."""
        with pytest.raises(ValidationError, match="at least 1 item"):
            EthicalVerdict(
                action_plan_id="11111111-1111-1111-1111-111111111111",
                final_decision=DecisionLevel.APPROVE,
                confidence=0.95,
                framework_verdicts={},  # Empty!
                resolution_method="unanimous",
                primary_reasons=["Test reason"],
                processing_time_ms=100.0,
            )

    def test_verdict_requires_primary_reasons(self) -> None:
        """Test that at least one primary reason is required."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Test reasoning here",
        )

        with pytest.raises(ValidationError):  # Missing primary reasons
            EthicalVerdict(
                action_plan_id="11111111-1111-1111-1111-111111111111",
                final_decision=DecisionLevel.APPROVE,
                confidence=0.95,
                framework_verdicts={FrameworkName.KANTIAN: kant},
                resolution_method="unanimous",
                primary_reasons=[],  # Empty!
                processing_time_ms=100.0,
            )

    def test_verdict_monitoring_requires_conditions(self) -> None:
        """Test that monitoring requires monitoring_conditions."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Test reasoning here",
        )

        with pytest.raises(ValidationError, match="monitoring_conditions required"):
            EthicalVerdict(
                action_plan_id="11111111-1111-1111-1111-111111111111",
                final_decision=DecisionLevel.APPROVE,
                confidence=0.95,
                framework_verdicts={FrameworkName.KANTIAN: kant},
                resolution_method="unanimous",
                primary_reasons=["Test reason"],
                processing_time_ms=100.0,
                requires_monitoring=True,
                monitoring_conditions=[],  # Missing!
            )

    def test_verdict_with_monitoring(self) -> None:
        """Test verdict with monitoring enabled."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Test reasoning here",
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
            confidence=0.85,
            framework_verdicts={FrameworkName.KANTIAN: kant},
            resolution_method="unanimous",
            primary_reasons=["Approved with monitoring"],
            processing_time_ms=100.0,
            requires_monitoring=True,
            monitoring_conditions=["Check consent validity", "Monitor for adverse effects"],
        )

        assert verdict.requires_monitoring is True
        assert len(verdict.monitoring_conditions) == 2

    def test_has_veto_true(self) -> None:
        """Test has_veto() when framework issued veto."""
        reason = RejectionReason(
            category="deception",
            description="Categorical imperative violation",
            severity=1.0,
            violated_principle="Categorical Imperative",
        )

        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.VETO,
            confidence=1.0,
            reasoning="Absolute veto",
            rejection_reasons=[reason],
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.VETO,
            confidence=1.0,
            framework_verdicts={FrameworkName.KANTIAN: kant},
            resolution_method="veto_override",
            primary_reasons=["Kantian veto"],
            processing_time_ms=100.0,
        )

        assert verdict.has_veto() is True

    def test_has_veto_false(self) -> None:
        """Test has_veto() when no veto issued."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Test reasoning here",
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE,
            confidence=0.95,
            framework_verdicts={FrameworkName.KANTIAN: kant},
            resolution_method="unanimous",
            primary_reasons=["All approve"],
            processing_time_ms=100.0,
        )

        assert verdict.has_veto() is False

    def test_get_rejecting_frameworks(self) -> None:
        """Test get_rejecting_frameworks()."""
        reason = RejectionReason(
            category="harm",
            description="Potential harm identified",
            severity=0.7,
            violated_principle="Non-maleficence",
        )

        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Kantian approval",
        )

        principialism = FrameworkVerdict(
            framework_name=FrameworkName.PRINCIPIALISM,
            decision=DecisionLevel.REJECT,
            confidence=0.9,
            reasoning="Violates non-maleficence",
            rejection_reasons=[reason],
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.REJECT,
            confidence=0.85,
            framework_verdicts={
                FrameworkName.KANTIAN: kant,
                FrameworkName.PRINCIPIALISM: principialism,
            },
            resolution_method="weighted",
            primary_reasons=["Principialism rejects"],
            processing_time_ms=100.0,
        )

        rejecting = verdict.get_rejecting_frameworks()
        assert len(rejecting) == 1
        assert FrameworkName.PRINCIPIALISM in rejecting

    def test_get_approving_frameworks(self) -> None:
        """Test get_approving_frameworks()."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Kantian approval",
        )

        mill = FrameworkVerdict(
            framework_name=FrameworkName.UTILITARIAN,
            decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
            confidence=0.85,
            reasoning="Utilitarian conditional",
            conditions=["Monitor outcomes"],
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
            confidence=0.9,
            framework_verdicts={
                FrameworkName.KANTIAN: kant,
                FrameworkName.UTILITARIAN: mill,
            },
            resolution_method="majority",
            primary_reasons=["Majority approves"],
            processing_time_ms=100.0,
        )

        approving = verdict.get_approving_frameworks()
        assert len(approving) == 2
        assert FrameworkName.KANTIAN in approving
        assert FrameworkName.UTILITARIAN in approving

    def test_consensus_level_unanimous(self) -> None:
        """Test consensus_level() with unanimous decision."""
        verdicts_dict = {}
        for fw in [FrameworkName.KANTIAN, FrameworkName.UTILITARIAN, FrameworkName.VIRTUE_ETHICS]:
            verdicts_dict[fw] = FrameworkVerdict(
                framework_name=fw,
                decision=DecisionLevel.APPROVE,
                confidence=0.9,
                reasoning="Test reasoning here",
            )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE,
            confidence=0.9,
            framework_verdicts=verdicts_dict,
            resolution_method="unanimous",
            primary_reasons=["Unanimous"],
            processing_time_ms=100.0,
        )

        assert verdict.consensus_level() == 1.0

    def test_consensus_level_split(self) -> None:
        """Test consensus_level() with split decision."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Kantian reasoning",
        )

        mill = FrameworkVerdict(
            framework_name=FrameworkName.UTILITARIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.88,
            reasoning="Utilitarian reasoning",
        )

        reason = RejectionReason(
            category="virtue",
            description="Lacks courage",
            severity=0.6,
            violated_principle="Courage",
        )

        aristotle = FrameworkVerdict(
            framework_name=FrameworkName.VIRTUE_ETHICS,
            decision=DecisionLevel.REJECT,
            confidence=0.75,
            reasoning="Lacks virtue",
            rejection_reasons=[reason],
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE,
            confidence=0.85,
            framework_verdicts={
                FrameworkName.KANTIAN: kant,
                FrameworkName.UTILITARIAN: mill,
                FrameworkName.VIRTUE_ETHICS: aristotle,
            },
            resolution_method="majority",
            primary_reasons=["Majority approves"],
            processing_time_ms=100.0,
        )

        # 2 APPROVE, 1 REJECT = 2/3 consensus
        assert verdict.consensus_level() == pytest.approx(2 / 3)

    def test_get_all_rejection_reasons(self) -> None:
        """Test get_all_rejection_reasons()."""
        reason1 = RejectionReason(
            category="harm",
            description="Physical harm risk",
            severity=0.8,
            violated_principle="Non-maleficence",
        )

        reason2 = RejectionReason(
            category="autonomy",
            description="Lacks consent",
            severity=0.9,
            violated_principle="Autonomy",
        )

        principialism = FrameworkVerdict(
            framework_name=FrameworkName.PRINCIPIALISM,
            decision=DecisionLevel.REJECT,
            confidence=0.95,
            reasoning="Multiple violations",
            rejection_reasons=[reason1, reason2],
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.REJECT,
            confidence=0.95,
            framework_verdicts={FrameworkName.PRINCIPIALISM: principialism},
            resolution_method="unanimous",
            primary_reasons=["Principialism rejects"],
            processing_time_ms=100.0,
        )

        all_reasons = verdict.get_all_rejection_reasons()
        assert len(all_reasons) == 2
        assert all_reasons[0].severity == 0.8
        assert all_reasons[1].severity == 0.9

    def test_get_highest_severity_reason(self) -> None:
        """Test get_highest_severity_reason()."""
        reason1 = RejectionReason(
            category="harm",
            description="Minor harm",
            severity=0.3,
            violated_principle="Non-maleficence",
        )

        reason2 = RejectionReason(
            category="deception",
            description="Major deception",
            severity=0.95,
            violated_principle="Honesty",
        )

        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.REJECT,
            confidence=0.9,
            reasoning="Multiple issues",
            rejection_reasons=[reason1, reason2],
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.REJECT,
            confidence=0.9,
            framework_verdicts={FrameworkName.KANTIAN: kant},
            resolution_method="unanimous",
            primary_reasons=["Kant rejects"],
            processing_time_ms=100.0,
        )

        highest = verdict.get_highest_severity_reason()
        assert highest is not None
        assert highest.severity == 0.95
        assert highest.category == "deception"

    def test_get_highest_severity_reason_none(self) -> None:
        """Test get_highest_severity_reason() when no reasons."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="All good here",
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE,
            confidence=0.95,
            framework_verdicts={FrameworkName.KANTIAN: kant},
            resolution_method="unanimous",
            primary_reasons=["All approve"],
            processing_time_ms=100.0,
        )

        highest = verdict.get_highest_severity_reason()
        assert highest is None


class TestEdgeCases:
    """Edge case tests."""

    def test_verdict_uuid_generation(self) -> None:
        """Test that verdict ID is generated as UUID."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Test reasoning here",
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE,
            confidence=0.95,
            framework_verdicts={FrameworkName.KANTIAN: kant},
            resolution_method="unanimous",
            primary_reasons=["Test"],
            processing_time_ms=100.0,
        )

        # Validate UUID format
        uuid.UUID(verdict.id)

    def test_verdict_with_alternatives(self) -> None:
        """Test verdict with alternatives generated."""
        kant = FrameworkVerdict(
            framework_name=FrameworkName.KANTIAN,
            decision=DecisionLevel.APPROVE,
            confidence=0.95,
            reasoning="Test reasoning here",
        )

        verdict = EthicalVerdict(
            action_plan_id="11111111-1111-1111-1111-111111111111",
            final_decision=DecisionLevel.APPROVE,
            confidence=0.95,
            framework_verdicts={FrameworkName.KANTIAN: kant},
            resolution_method="unanimous",
            primary_reasons=["Approved"],
            processing_time_ms=100.0,
            alternatives_generated=True,
            alternatives_count=3,
        )

        assert verdict.alternatives_generated is True
        assert verdict.alternatives_count == 3
