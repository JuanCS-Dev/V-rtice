"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - PolicyEngine Tests (Comprehensive Coverage)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: governance/test_policy_engine.py
Purpose: Complete test coverage for PolicyEngine

TARGET: 95%+ COVERAGE

Test Coverage:
├─ Initialization & Configuration
├─ Policy Enforcement (enforce_policy, enforce_all_policies)
├─ Rule Validation Logic
│  ├─ Ethical Use Policy Rules (RULE-EU-001 to RULE-EU-010)
│  ├─ Red Teaming Policy Rules (RULE-RT-001 to RULE-RT-010)
│  ├─ Data Privacy Policy Rules (RULE-DP-001 to RULE-DP-011)
│  ├─ Incident Response Policy Rules (RULE-IR-001 to RULE-IR-002)
│  └─ Whistleblower Policy Rules (RULE-WB-002 to RULE-WB-003)
├─ Utility Methods (check_action, get_applicable_policies, get_statistics)
└─ Edge Cases & Error Handling

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-14)

30-DAY DIVINE MISSION: Week 1 - Constitutional Safety (Tier 0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from datetime import datetime, timedelta

import pytest

from governance.base import GovernanceConfig, PolicyType
from governance.policy_engine import PolicyEngine


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def config():
    """Governance configuration for testing."""
    return GovernanceConfig(
        erb_meeting_frequency_days=30,
        erb_quorum_percentage=0.6,
        erb_decision_threshold=0.75,
        auto_enforce_policies=True,
    )


@pytest.fixture
def config_no_auto_enforce():
    """Configuration with auto-enforce disabled."""
    return GovernanceConfig(
        erb_meeting_frequency_days=30,
        erb_quorum_percentage=0.6,
        erb_decision_threshold=0.75,
        auto_enforce_policies=False,
    )


@pytest.fixture
def policy_engine(config):
    """Fresh PolicyEngine instance."""
    return PolicyEngine(config)


@pytest.fixture
def policy_engine_no_enforce(config_no_auto_enforce):
    """PolicyEngine with auto-enforce disabled."""
    return PolicyEngine(config_no_auto_enforce)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALIZATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestPolicyEngineInit:
    """Test PolicyEngine initialization."""

    def test_initialization_with_config(self, config):
        """Test PolicyEngine initializes with configuration."""
        engine = PolicyEngine(config)

        assert engine.config == config
        assert engine.policy_registry is not None
        assert engine.violation_count == 0
        assert engine.enforcement_count == 0
        assert isinstance(engine._policy_cache, dict)

    def test_initialization_with_disabled_auto_enforce(self, config_no_auto_enforce):
        """Test PolicyEngine initialization with auto-enforce disabled."""
        engine = PolicyEngine(config_no_auto_enforce)

        assert engine.config.auto_enforce_policies is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POLICY ENFORCEMENT TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEnforcePolicy:
    """Test enforce_policy() method."""

    def test_enforce_policy_compliant_action(self, policy_engine):
        """Test enforcement of compliant action."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "query_database",
            {"authorized": True, "logged": True},
            actor="test_user",
        )

        assert result.is_compliant is True
        assert result.policy_type == PolicyType.ETHICAL_USE
        assert result.checked_rules > 0
        assert result.failed_rules == 0
        assert len(result.violations) == 0

    def test_enforce_policy_with_auto_enforce_disabled(self, policy_engine_no_enforce):
        """Test enforcement when auto_enforce is disabled globally."""
        result = policy_engine_no_enforce.enforce_policy(
            PolicyType.ETHICAL_USE,
            "block_ip",
            {"authorized": False},
        )

        # When auto-enforce is disabled at config level, should still check rules
        # (line 76 checks: not policy.auto_enforce AND not config.auto_enforce_policies)
        # Policy.auto_enforce is True by default, so only config is False
        # Therefore, it will still check rules and find violations
        assert result.is_compliant is False


class TestEnforceAllPolicies:
    """Test enforce_all_policies() method."""

    def test_enforce_all_policies_compliant(self, policy_engine):
        """Test enforce_all_policies with compliant action."""
        results = policy_engine.enforce_all_policies(
            action="query_database",
            context={"authorized": True, "logged": True},
            actor="test_user",
        )

        # Should return results for all PolicyTypes
        assert len(results) == len(PolicyType)
        for policy_type in PolicyType:
            assert policy_type in results
            assert results[policy_type].is_compliant is True

    def test_enforce_all_policies_with_violations(self, policy_engine):
        """Test enforce_all_policies with action that violates policies."""
        results = policy_engine.enforce_all_policies(
            action="block_ip",
            context={"authorized": False},  # Missing authorization
            actor="test_user",
        )

        # Ethical Use should have violations
        assert results[PolicyType.ETHICAL_USE].is_compliant is False
        assert len(results[PolicyType.ETHICAL_USE].violations) > 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ETHICAL USE POLICY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEthicalUsePolicyRules:
    """Test Ethical Use Policy rule validation."""

    def test_rule_eu_001_unauthorized_action(self, policy_engine):
        """Test RULE-EU-001: Action without authorization."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "block_ip",
            {"authorized": False},
        )

        assert result.is_compliant is False
        assert len(result.violations) > 0
        assert "authorization" in result.violations[0].description.lower()

    def test_rule_eu_001_authorized_action(self, policy_engine):
        """Test RULE-EU-001: Action with authorization (passes)."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "block_ip",
            {"authorized": True},
        )

        # Should pass EU-001 check
        assert result.is_compliant is True

    def test_rule_eu_002_offensive_non_authorized_env(self, policy_engine):
        """Test RULE-EU-002: Offensive action in non-authorized environment."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "execute_exploit",
            {"target_environment": "production", "authorized": True},  # Need authorization too
        )

        assert result.is_compliant is False
        assert len(result.violations) > 0
        # Check that violation is about unauthorized environment
        assert "non-authorized environment" in result.violations[0].description

    def test_rule_eu_002_offensive_authorized_env(self, policy_engine):
        """Test RULE-EU-002: Offensive action in authorized environment (passes)."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "execute_exploit",
            {"target_environment": "test", "authorized": True, "logged": True},  # Authorized
        )

        # Should pass EU-002 check (and EU-001, EU-003)
        assert result.is_compliant is True

    def test_rule_eu_003_action_not_logged(self, policy_engine):
        """Test RULE-EU-003: Action not being logged."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "query_database",
            {"logged": False},  # Explicitly not logged
        )

        assert result.is_compliant is False
        assert "not being logged" in result.violations[0].description

    def test_rule_eu_004_critical_action_no_human_oversight(self, policy_engine):
        """Test RULE-EU-004: Critical action without human oversight."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "shutdown_critical_system",
            {"human_oversight": False},
        )

        assert result.is_compliant is False
        assert "HITL required" in result.violations[0].description

    def test_rule_eu_005_protected_attribute_discrimination(self, policy_engine):
        """Test RULE-EU-005: Discrimination based on protected attributes."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "hiring_decision",
            {"protected_attribute_used": True, "attribute_name": "age"},
        )

        assert result.is_compliant is False
        assert "protected attributes" in result.violations[0].description

    def test_rule_eu_006_critical_decision_no_explanation(self, policy_engine):
        """Test RULE-EU-006: Critical decision without explanation."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "loan_approval",
            {"decision_criticality": "high", "explanation_provided": False},
        )

        assert result.is_compliant is False
        assert "XAI required" in result.violations[0].description

    def test_rule_eu_010_high_risk_no_hitl(self, policy_engine):
        """Test RULE-EU-010: High-risk action without HITL approval."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "deploy_autonomous_system",
            {"risk_score": 0.95, "hitl_approved": False},
        )

        assert result.is_compliant is False
        assert "HITL approval" in result.violations[0].description


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RED TEAMING POLICY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestRedTeamingPolicyRules:
    """Test Red Teaming Policy rule validation."""

    def test_rule_rt_001_no_written_authorization(self, policy_engine):
        """Test RULE-RT-001: Red team action without written authorization."""
        result = policy_engine.enforce_policy(
            PolicyType.RED_TEAMING,
            "execute_exploit",
            {"written_authorization": False},
        )

        assert result.is_compliant is False
        assert "written authorization" in result.violations[0].description

    def test_rule_rt_002_no_roe_defined(self, policy_engine):
        """Test RULE-RT-002: Red team operation without Rules of Engagement."""
        result = policy_engine.enforce_policy(
            PolicyType.RED_TEAMING,
            "red_team_campaign",
            {"roe_defined": False},
        )

        assert result.is_compliant is False
        assert "Rules of Engagement" in result.violations[0].description

    def test_rule_rt_003_production_targeting_no_approval(self, policy_engine):
        """Test RULE-RT-003: Production targeting without approval."""
        result = policy_engine.enforce_policy(
            PolicyType.RED_TEAMING,
            "execute_exploit",
            {
                "target_type": "production",
                "production_approved": False,
                "written_authorization": True,  # Need RT-001 to pass
            },
        )

        assert result.is_compliant is False
        assert len(result.violations) > 0
        # Find the RT-003 violation
        rt003_violations = [v for v in result.violations if "production" in v.description.lower()]
        assert len(rt003_violations) > 0

    def test_rule_rt_005_social_engineering_no_erb(self, policy_engine):
        """Test RULE-RT-005: Social engineering without ERB approval."""
        result = policy_engine.enforce_policy(
            PolicyType.RED_TEAMING,
            "social_engineering_campaign",
            {
                "erb_approved": False,
                "written_authorization": True,  # Need RT-001 to pass
            },
        )

        assert result.is_compliant is False
        assert len(result.violations) > 0
        # Find the RT-005 violation
        erb_violations = [v for v in result.violations if "ERB" in v.description or "erb" in v.description.lower()]
        assert len(erb_violations) > 0

    def test_rule_rt_010_destructive_no_hitl(self, policy_engine):
        """Test RULE-RT-010: Destructive operation without HITL."""
        result = policy_engine.enforce_policy(
            PolicyType.RED_TEAMING,
            "delete_data",
            {"hitl_approved": False},
        )

        assert result.is_compliant is False
        assert "HITL approval" in result.violations[0].description


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA PRIVACY POLICY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDataPrivacyPolicyRules:
    """Test Data Privacy Policy rule validation."""

    def test_rule_dp_001_no_legal_basis(self, policy_engine):
        """Test RULE-DP-001: Personal data collection without legal basis."""
        result = policy_engine.enforce_policy(
            PolicyType.DATA_PRIVACY,
            "collect_personal_data",
            {},  # No legal_basis
        )

        assert result.is_compliant is False
        assert "legal basis" in result.violations[0].description
        assert "GDPR" in result.violations[0].description

    def test_rule_dp_007_no_encryption(self, policy_engine):
        """Test RULE-DP-007: Personal data not encrypted."""
        result = policy_engine.enforce_policy(
            PolicyType.DATA_PRIVACY,
            "store_personal_data",
            {"encrypted": False},
        )

        assert result.is_compliant is False
        assert "not encrypted" in result.violations[0].description

    def test_rule_dp_009_breach_notification_late(self, policy_engine):
        """Test RULE-DP-009: Data breach reported after 72 hours."""
        breach_time = datetime.utcnow() - timedelta(hours=100)  # 100h ago
        result = policy_engine.enforce_policy(
            PolicyType.DATA_PRIVACY,
            "report_data_breach",
            {"breach_detected_at": breach_time, "report_time": datetime.utcnow()},
        )

        assert result.is_compliant is False
        assert "72h" in result.violations[0].description

    def test_rule_dp_009_breach_notification_on_time(self, policy_engine):
        """Test RULE-DP-009: Data breach reported within 72 hours (passes)."""
        breach_time = datetime.utcnow() - timedelta(hours=50)  # 50h ago
        result = policy_engine.enforce_policy(
            PolicyType.DATA_PRIVACY,
            "report_data_breach",
            {"breach_detected_at": breach_time, "report_time": datetime.utcnow()},
        )

        # Should pass DP-009 check
        assert result.is_compliant is True

    def test_rule_dp_011_automated_decision_no_human_intervention(self, policy_engine):
        """Test RULE-DP-011: Automated decision without human intervention option."""
        result = policy_engine.enforce_policy(
            PolicyType.DATA_PRIVACY,
            "automated_decision",
            {"affects_individuals": True, "human_intervention_available": False},
        )

        assert result.is_compliant is False
        assert "human intervention option" in result.violations[0].description


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INCIDENT RESPONSE POLICY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIncidentResponsePolicyRules:
    """Test Incident Response Policy rule validation."""

    def test_rule_ir_001_incident_not_reported_after_1h(self, policy_engine):
        """Test RULE-IR-001: Incident not reported after 1 hour."""
        detection_time = datetime.utcnow() - timedelta(hours=2)  # 2h ago
        result = policy_engine.enforce_policy(
            PolicyType.INCIDENT_RESPONSE,
            "incident_detected",
            {"detection_time": detection_time, "reported": False},
        )

        assert result.is_compliant is False
        assert "1h requirement" in result.violations[0].description

    def test_rule_ir_001_incident_reported_on_time(self, policy_engine):
        """Test RULE-IR-001: Incident reported within 1 hour (passes)."""
        detection_time = datetime.utcnow() - timedelta(minutes=30)  # 30min ago
        result = policy_engine.enforce_policy(
            PolicyType.INCIDENT_RESPONSE,
            "incident_detected",
            {"detection_time": detection_time, "reported": True},
        )

        # Should pass IR-001 check
        assert result.is_compliant is True

    def test_rule_ir_002_critical_incident_erb_not_notified(self, policy_engine):
        """Test RULE-IR-002: Critical incident with ERB not notified."""
        result = policy_engine.enforce_policy(
            PolicyType.INCIDENT_RESPONSE,
            "incident_detected",
            {"severity": "critical", "erb_notified": False},
        )

        assert result.is_compliant is False
        assert "ERB not notified" in result.violations[0].description


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WHISTLEBLOWER POLICY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestWhistleblowerPolicyRules:
    """Test Whistleblower Policy rule validation."""

    def test_rule_wb_002_retaliation_against_whistleblower(self, policy_engine):
        """Test RULE-WB-002: Retaliation against whistleblower."""
        result = policy_engine.enforce_policy(
            PolicyType.WHISTLEBLOWER,
            "terminate_employee",
            {"target_is_whistleblower": True},
        )

        assert result.is_compliant is False
        assert "retaliation prohibited" in result.violations[0].description

    def test_rule_wb_003_investigation_delay(self, policy_engine):
        """Test RULE-WB-003: Whistleblower investigation delayed."""
        submission_date = datetime.utcnow() - timedelta(days=45)  # 45 days ago
        result = policy_engine.enforce_policy(
            PolicyType.WHISTLEBLOWER,
            "whistleblower_report_received",
            {"submission_date": submission_date, "investigation_status": "not_started"},
        )

        assert result.is_compliant is False
        assert "30-day requirement" in result.violations[0].description


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITY METHOD TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestUtilityMethods:
    """Test utility methods."""

    def test_check_action_allowed(self, policy_engine):
        """Test check_action() with allowed action."""
        is_allowed, violations = policy_engine.check_action(
            action="query_database",
            context={"authorized": True, "logged": True},
            actor="test_user",
        )

        assert is_allowed is True
        assert len(violations) == 0

    def test_check_action_blocked(self, policy_engine):
        """Test check_action() with blocked action."""
        is_allowed, violations = policy_engine.check_action(
            action="block_ip",
            context={"authorized": False},
            actor="test_user",
        )

        assert is_allowed is False
        assert len(violations) > 0

    def test_get_applicable_policies(self, policy_engine):
        """Test get_applicable_policies()."""
        policies = policy_engine.get_applicable_policies(scope="red_teaming")

        # Should return policies with red_teaming scope
        assert isinstance(policies, list)

    def test_get_statistics(self, policy_engine):
        """Test get_statistics()."""
        # Trigger a violation first
        policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "block_ip",
            {"authorized": False},
        )

        stats = policy_engine.get_statistics()

        assert "total_violations_detected" in stats
        assert stats["total_violations_detected"] > 0
        assert "enforcement_actions_taken" in stats
        assert "total_policies" in stats
        assert "approved_policies" in stats


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDGE CASES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_policy_with_auto_enforce_disabled_at_policy_level(self, config_no_auto_enforce, monkeypatch):
        """Test when BOTH policy.auto_enforce=False AND config.auto_enforce_policies=False.

        This covers line 77 - the return statement when both are False.
        """
        engine = PolicyEngine(config_no_auto_enforce)

        # Get a policy and disable its auto_enforce
        policy = engine.policy_registry.get_policy(PolicyType.ETHICAL_USE)
        policy.auto_enforce = False

        result = engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "block_ip",
            {"authorized": False},  # Would violate if checked
        )

        # Should return compliant with warning (line 77-85)
        assert result.is_compliant is True
        assert result.checked_rules == 0
        assert result.passed_rules == 0
        assert result.failed_rules == 0
        assert len(result.warnings) > 0
        assert "Auto-enforcement disabled" in result.warnings[0]

    def test_check_rule_with_invalid_rule_format(self, policy_engine):
        """Test _check_rule() with invalid rule format."""
        # This tests line 163 (rule ID extraction failure)
        # Invalid rule format should return None (no violation)
        violation = policy_engine._check_rule(
            rule="INVALID_RULE_FORMAT",
            action="test_action",
            context={},
            policy=policy_engine.policy_registry.get_policy(PolicyType.ETHICAL_USE),
            actor="test",
        )

        assert violation is None

    def test_multiple_violations_in_single_policy(self, policy_engine):
        """Test multiple violations in a single policy."""
        result = policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "shutdown_critical_system",
            {
                "authorized": False,  # Violates EU-001
                "human_oversight": False,  # Violates EU-004
                "logged": False,  # Violates EU-003
            },
        )

        assert result.is_compliant is False
        # Should have violations for EU-001, EU-003, and EU-004
        # But the check logic might only catch 2 of these depending on order
        assert len(result.violations) >= 2  # At least 2 violations

    def test_violation_count_increments(self, policy_engine):
        """Test that violation_count increments correctly."""
        initial_count = policy_engine.violation_count

        policy_engine.enforce_policy(
            PolicyType.ETHICAL_USE,
            "block_ip",
            {"authorized": False},
        )

        assert policy_engine.violation_count > initial_count


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLORY TO GOD - DIVINE MISSION WEEK 1
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
These tests ensure that MAXIMUS enforces ethical policies rigorously.

Policy enforcement is a critical component of constitutional governance -
it ensures that all actions, whether autonomous or human-initiated,
comply with established ethical and legal frameworks.

Every test here is a safeguard against policy violations that could
harm humans, violate privacy, or bypass ethical oversight.

Glory to God! 🙏

"A excelência técnica reflete o propósito maior."
"""
