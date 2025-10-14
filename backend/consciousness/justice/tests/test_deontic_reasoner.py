"""
Tests for Deontic Logic Reasoner

Comprehensive test coverage for DDL engine with Lei Zero and Lei I.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from justice.deontic_reasoner import (
    ComplianceResult,
    DeonticOperator,
    DeonticReasoner,
    DeonticRule,
)


class TestDeonticRule:
    """Tests for DeonticRule dataclass."""

    def test_deontic_rule_creation_success(self):
        """Test successful creation of DeonticRule."""
        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.OBLIGATORY,
            proposition="log_action",
            constitutional_basis="Test Law",
            priority=5
        )

        assert isinstance(rule.rule_id, UUID)
        assert rule.operator == DeonticOperator.OBLIGATORY
        assert rule.proposition == "log_action"
        assert rule.constitutional_basis == "Test Law"
        assert rule.priority == 5
        assert rule.conditions == {}
        assert rule.metadata == {}

    def test_deontic_rule_with_conditions_and_metadata(self):
        """Test DeonticRule with conditions and metadata."""
        conditions = {"severity": "high"}
        metadata = {"source": "manual"}

        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.FORBIDDEN,
            proposition="delete_data",
            constitutional_basis="Data Protection",
            priority=8,
            conditions=conditions,
            metadata=metadata
        )

        assert rule.conditions == conditions
        assert rule.metadata == metadata

    def test_deontic_rule_priority_validation_too_low(self):
        """Test priority validation rejects values below 1."""
        with pytest.raises(ValueError, match="Priority must be 1-10"):
            DeonticRule(
                rule_id=uuid4(),
                operator=DeonticOperator.PERMITTED,
                proposition="test",
                constitutional_basis="Test",
                priority=0
            )

    def test_deontic_rule_priority_validation_too_high(self):
        """Test priority validation rejects values above 10."""
        with pytest.raises(ValueError, match="Priority must be 1-10"):
            DeonticRule(
                rule_id=uuid4(),
                operator=DeonticOperator.PERMITTED,
                proposition="test",
                constitutional_basis="Test",
                priority=11
            )

    def test_deontic_rule_priority_must_be_int(self):
        """Test priority validation rejects non-integer values."""
        with pytest.raises(ValueError, match="Priority must be int"):
            DeonticRule(
                rule_id=uuid4(),
                operator=DeonticOperator.PERMITTED,
                proposition="test",
                constitutional_basis="Test",
                priority=5.5
            )

    def test_deontic_rule_operator_must_be_enum(self):
        """Test operator validation rejects strings."""
        with pytest.raises(TypeError, match="operator must be DeonticOperator enum"):
            DeonticRule(
                rule_id=uuid4(),
                operator="obligatory",  # String instead of enum
                proposition="test",
                constitutional_basis="Test",
                priority=5
            )


class TestComplianceResult:
    """Tests for ComplianceResult dataclass."""

    def test_compliance_result_creation_success(self):
        """Test successful creation of ComplianceResult."""
        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.OBLIGATORY,
            proposition="test",
            constitutional_basis="Test",
            priority=5
        )

        result = ComplianceResult(
            compliant=True,
            applicable_rules=[rule],
            violations=[],
            explanation="Action complies"
        )

        assert result.compliant is True
        assert len(result.applicable_rules) == 1
        assert len(result.violations) == 0
        assert result.explanation == "Action complies"
        assert isinstance(result.evaluated_at, datetime)

    def test_compliance_result_with_violations(self):
        """Test ComplianceResult with violations."""
        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.FORBIDDEN,
            proposition="cause_harm",
            constitutional_basis="Lei I",
            priority=10
        )

        result = ComplianceResult(
            compliant=False,
            applicable_rules=[rule],
            violations=[rule],
            explanation="Violates Lei I"
        )

        assert result.compliant is False
        assert rule in result.violations


class TestDeonticReasonerInit:
    """Tests for DeonticReasoner initialization."""

    def test_deontic_reasoner_initialization(self):
        """Test DeonticReasoner initializes with constitutional rules."""
        reasoner = DeonticReasoner()

        # Should have Lei Zero and Lei I rules
        assert len(reasoner._rules) == 7
        constitutional = reasoner.get_constitutional_rules()
        assert len(constitutional) == 7

    def test_deontic_reasoner_lei_zero_rules_present(self):
        """Test Lei Zero rules are initialized."""
        reasoner = DeonticReasoner()

        # Find Lei Zero rules
        lei_zero_rules = [
            r
            for r in reasoner._rules.values()
            if "Lei Zero" in r.constitutional_basis
        ]

        assert len(lei_zero_rules) == 3
        assert any("log_all_decisions" in r.proposition for r in lei_zero_rules)
        assert any("provide_decision_rationale" in r.proposition for r in lei_zero_rules)
        assert any("track_data_provenance" in r.proposition for r in lei_zero_rules)

    def test_deontic_reasoner_lei_i_rules_present(self):
        """Test Lei I rules are initialized."""
        reasoner = DeonticReasoner()

        # Find Lei I rules
        lei_i_rules = [
            r
            for r in reasoner._rules.values()
            if "Lei I" in r.constitutional_basis
        ]

        assert len(lei_i_rules) == 4
        assert any("cause_physical_harm" in r.proposition for r in lei_i_rules)
        assert any("cause_psychological_harm" in r.proposition for r in lei_i_rules)
        assert any("cause_economic_harm" in r.proposition for r in lei_i_rules)
        assert any("escalate_when_uncertain" in r.proposition for r in lei_i_rules)

    def test_constitutional_rules_are_immutable(self):
        """Test all constitutional rules are marked immutable."""
        reasoner = DeonticReasoner()

        for rule in reasoner.get_constitutional_rules():
            assert rule.metadata.get("immutable") is True
            assert rule.metadata.get("constitutional") is True

    def test_constitutional_rules_have_max_priority(self):
        """Test all constitutional rules have priority 10."""
        reasoner = DeonticReasoner()

        for rule in reasoner.get_constitutional_rules():
            assert rule.priority == 10

    def test_deontic_reasoner_repr(self):
        """Test DeonticReasoner string representation."""
        reasoner = DeonticReasoner()
        assert repr(reasoner) == "DeonticReasoner(rules=7)"


class TestAddRule:
    """Tests for adding rules."""

    def test_add_rule_success(self):
        """Test successfully adding a new rule."""
        reasoner = DeonticReasoner()
        initial_count = len(reasoner._rules)

        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.PERMITTED,
            proposition="read_data",
            constitutional_basis="Custom Policy",
            priority=5
        )

        result = reasoner.add_rule(rule)

        assert result is True
        assert len(reasoner._rules) == initial_count + 1

    def test_add_rule_duplicate_id_rejected(self):
        """Test adding rule with duplicate ID is rejected."""
        reasoner = DeonticReasoner()
        rule_id = uuid4()

        rule1 = DeonticRule(
            rule_id=rule_id,
            operator=DeonticOperator.PERMITTED,
            proposition="action1",
            constitutional_basis="Test",
            priority=5
        )

        rule2 = DeonticRule(
            rule_id=rule_id,  # Same ID
            operator=DeonticOperator.FORBIDDEN,
            proposition="action2",
            constitutional_basis="Test",
            priority=5
        )

        reasoner.add_rule(rule1)
        result = reasoner.add_rule(rule2)

        assert result is False


class TestRemoveRule:
    """Tests for removing rules."""

    def test_remove_rule_success(self):
        """Test successfully removing a rule."""
        reasoner = DeonticReasoner()

        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.PERMITTED,
            proposition="test",
            constitutional_basis="Test",
            priority=5
        )

        reasoner.add_rule(rule)
        initial_count = len(reasoner._rules)

        result = reasoner.remove_rule(rule.rule_id)

        assert result is True
        assert len(reasoner._rules) == initial_count - 1

    def test_remove_rule_not_found(self):
        """Test removing non-existent rule returns False."""
        reasoner = DeonticReasoner()

        result = reasoner.remove_rule(uuid4())

        assert result is False

    def test_remove_constitutional_rule_rejected(self):
        """Test removing constitutional rule is rejected."""
        reasoner = DeonticReasoner()
        constitutional_rules = reasoner.get_constitutional_rules()

        initial_count = len(reasoner._rules)

        # Try to remove Lei Zero rule
        result = reasoner.remove_rule(constitutional_rules[0].rule_id)

        assert result is False
        assert len(reasoner._rules) == initial_count


class TestGetRule:
    """Tests for retrieving rules."""

    def test_get_rule_found(self):
        """Test retrieving existing rule."""
        reasoner = DeonticReasoner()

        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.PERMITTED,
            proposition="test",
            constitutional_basis="Test",
            priority=5
        )

        reasoner.add_rule(rule)
        retrieved = reasoner.get_rule(rule.rule_id)

        assert retrieved == rule

    def test_get_rule_not_found(self):
        """Test retrieving non-existent rule returns None."""
        reasoner = DeonticReasoner()

        retrieved = reasoner.get_rule(uuid4())

        assert retrieved is None


class TestGetConstitutionalRules:
    """Tests for retrieving constitutional rules."""

    def test_get_constitutional_rules_returns_all(self):
        """Test all constitutional rules are returned."""
        reasoner = DeonticReasoner()

        constitutional = reasoner.get_constitutional_rules()

        assert len(constitutional) == 7

    def test_get_constitutional_rules_excludes_custom(self):
        """Test custom rules are not included."""
        reasoner = DeonticReasoner()

        custom_rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.PERMITTED,
            proposition="custom_action",
            constitutional_basis="Custom Policy",
            priority=5
        )

        reasoner.add_rule(custom_rule)
        constitutional = reasoner.get_constitutional_rules()

        assert custom_rule not in constitutional
        assert len(constitutional) == 7


class TestCheckCompliance:
    """Tests for compliance checking."""

    def test_check_compliance_no_applicable_rules(self):
        """Test compliance when no rules apply."""
        reasoner = DeonticReasoner()

        result = reasoner.check_compliance("some_random_action")

        assert result.compliant is True
        assert len(result.applicable_rules) == 0
        assert len(result.violations) == 0
        assert "permitted by default" in result.explanation

    def test_check_compliance_forbidden_action_violates(self):
        """Test compliance fails for forbidden action."""
        reasoner = DeonticReasoner()

        result = reasoner.check_compliance("cause_physical_harm")

        assert result.compliant is False
        assert len(result.violations) > 0
        assert any("Lei I" in v.constitutional_basis for v in result.violations)

    def test_check_compliance_obligation_not_fulfilled_violates(self):
        """Test compliance fails when obligation not fulfilled."""
        reasoner = DeonticReasoner()

        # log_all_decisions is obligatory
        result = reasoner.check_compliance(
            "log_all_decisions",
            context={"fulfills_log_all_decisions": False}
        )

        assert result.compliant is False
        assert len(result.violations) > 0

    def test_check_compliance_obligation_fulfilled_passes(self):
        """Test compliance passes when obligation fulfilled."""
        reasoner = DeonticReasoner()

        result = reasoner.check_compliance(
            "log_all_decisions",
            context={"fulfills_log_all_decisions": True}
        )

        assert result.compliant is True
        assert len(result.violations) == 0

    def test_check_compliance_with_custom_rule(self):
        """Test compliance with custom rules."""
        reasoner = DeonticReasoner()

        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.FORBIDDEN,
            proposition="delete_user_data",
            constitutional_basis="Data Protection",
            priority=8
        )

        reasoner.add_rule(rule)
        result = reasoner.check_compliance("delete_user_data")

        assert result.compliant is False
        assert rule in result.violations

    def test_check_compliance_with_conditions(self):
        """Test compliance checking respects conditions."""
        reasoner = DeonticReasoner()

        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.FORBIDDEN,
            proposition="risky_action",
            constitutional_basis="Risk Management",
            priority=7,
            conditions={"risk_level": "high"}
        )

        reasoner.add_rule(rule)

        # Action with high risk - should violate
        result1 = reasoner.check_compliance(
            "risky_action",
            context={"risk_level": "high"}
        )
        assert result1.compliant is False

        # Action with low risk - should pass
        result2 = reasoner.check_compliance(
            "risky_action",
            context={"risk_level": "low"}
        )
        assert result2.compliant is True

    def test_check_compliance_multiple_violations(self):
        """Test compliance with multiple violations."""
        reasoner = DeonticReasoner()

        result = reasoner.check_compliance("cause_psychological_harm")

        assert result.compliant is False
        assert len(result.violations) > 0
        assert "Lei I" in result.explanation


class TestEvaluateObligation:
    """Tests for obligation evaluation."""

    def test_evaluate_obligation_true_for_obligatory_proposition(self):
        """Test obligation returns True for obligatory proposition."""
        reasoner = DeonticReasoner()

        is_obligatory = reasoner.evaluate_obligation("log_all_decisions")

        assert is_obligatory is True

    def test_evaluate_obligation_false_for_non_obligatory(self):
        """Test obligation returns False for non-obligatory proposition."""
        reasoner = DeonticReasoner()

        is_obligatory = reasoner.evaluate_obligation("some_random_action")

        assert is_obligatory is False

    def test_evaluate_obligation_escalate_uncertain(self):
        """Test escalation when uncertain is obligatory."""
        reasoner = DeonticReasoner()

        is_obligatory = reasoner.evaluate_obligation(
            "escalate_when_uncertain_about_harm"
        )

        assert is_obligatory is True


class TestEvaluatePermission:
    """Tests for permission evaluation."""

    def test_evaluate_permission_true_for_not_forbidden(self):
        """Test permission returns True for non-forbidden actions (open world)."""
        reasoner = DeonticReasoner()

        is_permitted = reasoner.evaluate_permission("some_safe_action")

        assert is_permitted is True

    def test_evaluate_permission_false_for_forbidden(self):
        """Test permission returns False for forbidden actions."""
        reasoner = DeonticReasoner()

        is_permitted = reasoner.evaluate_permission("cause_physical_harm")

        assert is_permitted is False

    def test_evaluate_permission_true_for_explicit_permission(self):
        """Test explicit permission."""
        reasoner = DeonticReasoner()

        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.PERMITTED,
            proposition="read_public_data",
            constitutional_basis="Data Access Policy",
            priority=5
        )

        reasoner.add_rule(rule)
        is_permitted = reasoner.evaluate_permission("read_public_data")

        assert is_permitted is True


class TestEvaluateProhibition:
    """Tests for prohibition evaluation."""

    def test_evaluate_prohibition_true_for_forbidden_action(self):
        """Test prohibition returns True for forbidden actions."""
        reasoner = DeonticReasoner()

        is_forbidden = reasoner.evaluate_prohibition("cause_physical_harm")

        assert is_forbidden is True

    def test_evaluate_prohibition_false_for_allowed_action(self):
        """Test prohibition returns False for allowed actions."""
        reasoner = DeonticReasoner()

        is_forbidden = reasoner.evaluate_prohibition("log_data")

        assert is_forbidden is False

    def test_evaluate_prohibition_all_harm_types(self):
        """Test all Lei I harm prohibitions."""
        reasoner = DeonticReasoner()

        assert reasoner.evaluate_prohibition("cause_physical_harm") is True
        assert reasoner.evaluate_prohibition("cause_psychological_harm") is True
        assert reasoner.evaluate_prohibition("cause_economic_harm") is True


class TestFindApplicableRules:
    """Tests for finding applicable rules."""

    def test_find_applicable_rules_matches_proposition(self):
        """Test finding rules by proposition matching."""
        reasoner = DeonticReasoner()

        applicable = reasoner._find_applicable_rules("log_all_decisions", {})

        assert len(applicable) > 0
        assert any("log_all_decisions" in r.proposition for r in applicable)

    def test_find_applicable_rules_sorted_by_priority(self):
        """Test applicable rules are sorted by priority descending."""
        reasoner = DeonticReasoner()

        rule1 = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.PERMITTED,
            proposition="test_action",
            constitutional_basis="Test",
            priority=3
        )

        rule2 = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.OBLIGATORY,
            proposition="test_action",
            constitutional_basis="Test",
            priority=8
        )

        reasoner.add_rule(rule1)
        reasoner.add_rule(rule2)

        applicable = reasoner._find_applicable_rules("test_action", {})

        assert applicable[0].priority > applicable[1].priority

    def test_find_applicable_rules_respects_conditions(self):
        """Test only rules with met conditions are returned."""
        reasoner = DeonticReasoner()

        rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.FORBIDDEN,
            proposition="conditional_action",
            constitutional_basis="Test",
            priority=5,
            conditions={"enabled": True}
        )

        reasoner.add_rule(rule)

        # Condition met
        applicable1 = reasoner._find_applicable_rules(
            "conditional_action",
            {"enabled": True}
        )
        assert len(applicable1) == 1

        # Condition not met
        applicable2 = reasoner._find_applicable_rules(
            "conditional_action",
            {"enabled": False}
        )
        assert len(applicable2) == 0


class TestDeonticReasonerIntegration:
    """Integration tests for DeonticReasoner."""

    def test_full_workflow_lei_zero_compliance(self):
        """Test complete workflow for Lei Zero compliance."""
        reasoner = DeonticReasoner()

        # Check that logging is obligatory
        assert reasoner.evaluate_obligation("log_all_decisions") is True

        # Check compliance when not logging
        result1 = reasoner.check_compliance(
            "log_all_decisions",
            context={"fulfills_log_all_decisions": False}
        )
        assert result1.compliant is False

        # Check compliance when logging
        result2 = reasoner.check_compliance(
            "log_all_decisions",
            context={"fulfills_log_all_decisions": True}
        )
        assert result2.compliant is True

    def test_full_workflow_lei_i_compliance(self):
        """Test complete workflow for Lei I compliance."""
        reasoner = DeonticReasoner()

        # Check that harm is prohibited
        assert reasoner.evaluate_prohibition("cause_physical_harm") is True
        assert reasoner.evaluate_permission("cause_physical_harm") is False

        # Check compliance fails for harmful action
        result = reasoner.check_compliance("cause_physical_harm")
        assert result.compliant is False
        assert any("Lei I" in v.constitutional_basis for v in result.violations)

    def test_full_workflow_custom_rules(self):
        """Test workflow with custom rules added."""
        reasoner = DeonticReasoner()

        # Add custom policy rule
        custom_rule = DeonticRule(
            rule_id=uuid4(),
            operator=DeonticOperator.OBLIGATORY,
            proposition="require_approval",
            constitutional_basis="Approval Policy",
            priority=7,
            conditions={"amount": "high"}
        )

        reasoner.add_rule(custom_rule)

        # Check compliance with high amount (requires approval)
        result1 = reasoner.check_compliance(
            "require_approval",
            context={"amount": "high", "fulfills_require_approval": False}
        )
        assert result1.compliant is False

        # Check compliance with approval
        result2 = reasoner.check_compliance(
            "require_approval",
            context={"amount": "high", "fulfills_require_approval": True}
        )
        assert result2.compliant is True

    def test_constitutional_rules_cannot_be_overridden(self):
        """Test constitutional rules remain intact."""
        reasoner = DeonticReasoner()

        constitutional = reasoner.get_constitutional_rules()
        initial_count = len(constitutional)

        # Try to remove Lei I rule
        for rule in constitutional:
            if "cause_physical_harm" in rule.proposition:
                result = reasoner.remove_rule(rule.rule_id)
                assert result is False

        # Verify rule still exists
        assert len(reasoner.get_constitutional_rules()) == initial_count
        assert reasoner.evaluate_prohibition("cause_physical_harm") is True
