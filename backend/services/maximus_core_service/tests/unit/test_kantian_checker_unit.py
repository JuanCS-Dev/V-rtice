"""
Kantian Deontological Ethics - Comprehensive Unit Test Suite
Coverage Target: 95%+

Tests the CRITICAL Kantian ethics framework with VETO power:
- Categorical imperatives (NEVER/ALWAYS rules)
- Universalizability test (First Formulation)
- Humanity formula (Second Formulation)
- Veto exceptions
- Edge cases and boundary conditions

Author: Claude Code + JuanCS-Dev (Artisanal, DOUTRINA VÉRTICE)
Date: 2025-10-21
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from ethics.kantian_checker import KantianImperativeChecker
from ethics.base import (
    ActionContext,
    EthicalFramework,
    EthicalFrameworkResult,
    EthicalVerdict,
    VetoException,
)


# ===== FIXTURES =====

@pytest.fixture
def kantian_checker():
    """Fresh Kantian checker with veto enabled."""
    return KantianImperativeChecker(config={"veto_enabled": True, "strict_mode": True})


@pytest.fixture
def kantian_no_veto():
    """Kantian checker with veto disabled (for testing)."""
    return KantianImperativeChecker(config={"veto_enabled": False})


@pytest.fixture
def benign_action():
    """Sample benign action that should pass all tests."""
    return ActionContext(
        action_description="Monitor network traffic for suspicious patterns using IDS with user consent",
        action_type="defensive_monitoring",
        system_component="test_kantian_checker",
        urgency="medium",
        operator_context={"operator_id": "admin_001", "approved": True},
        threat_data={
            "confidence": 0.85,
            "severity": 0.7,
            "informed_consent": True,
            "legal_basis": "company_policy",
            "justification": "Authorized network security monitoring"
        },
        impact_assessment={
            "removes_human_control": False,
            "sacrifices_individual_rights": False
        }
    )


@pytest.fixture
def action_using_humans_as_means():
    """Action that uses humans as mere means (Kantian violation)."""
    return ActionContext(
        action_description="Launch social engineering attack to exploit employees",
        action_type="offensive_action",
        system_component="test_kantian_checker",
        urgency="low",
        operator_context=None,  # No authorization
        threat_data=None,
        impact_assessment=None
    )


@pytest.fixture
def action_violating_autonomy():
    """Action that violates human autonomy."""
    return ActionContext(
        action_description="Override autonomy and force compliance without justification",
        action_type="control_action",
        system_component="test_kantian_checker",
        urgency="low",  # Not critical
        operator_context=None,
        threat_data={"severity": 0.3},  # Low severity, no justification
        impact_assessment=None
    )


@pytest.fixture
def action_surveillance_no_consent():
    """Surveillance without consent (categorical violation)."""
    return ActionContext(
        action_description="Implement surveillance without consent or legal basis",
        system_component="test_kantian_checker",
        action_type="surveillance",
        urgency="low",
        operator_context=None,
        threat_data={},  # No consent, no legal basis
        impact_assessment=None
    )


# ===== INITIALIZATION TESTS =====

class TestKantianCheckerInitialization:
    """Tests for Kantian checker initialization."""

    @pytest.mark.unit
    def test_init_default_config(self):
        """
        SCENARIO: Initialize with default config
        EXPECTED: Veto enabled, strict mode enabled
        """
        # Act
        checker = KantianImperativeChecker()

        # Assert
        assert checker.veto_enabled is True
        assert checker.strict_mode is True

    @pytest.mark.unit
    def test_init_custom_config(self):
        """
        SCENARIO: Initialize with custom config
        EXPECTED: Config values respected
        """
        # Arrange
        config = {"veto_enabled": False, "strict_mode": False, "custom_key": "value"}

        # Act
        checker = KantianImperativeChecker(config)

        # Assert
        assert checker.veto_enabled is False
        assert checker.strict_mode is False

    @pytest.mark.unit
    def test_get_framework_principles(self, kantian_checker):
        """
        SCENARIO: Get Kantian principles
        EXPECTED: Returns 5 core principles
        """
        # Act
        principles = kantian_checker.get_framework_principles()

        # Assert
        assert isinstance(principles, list)
        assert len(principles) == 5
        assert any("Categorical Imperative" in p for p in principles)
        assert any("Humanity Formula" in p for p in principles)
        assert any("Kingdom of Ends" in p for p in principles)


# ===== CATEGORICAL NEVER RULES TESTS =====

class TestCategoricalNeverRules:
    """Tests for categorical prohibitions (NEVER rules)."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_veto_humans_as_mere_means(self, kantian_checker, action_using_humans_as_means):
        """
        SCENARIO: Action uses humans as mere means
        EXPECTED: VetoException raised
        """
        # Act & Assert
        with pytest.raises(VetoException) as exc_info:
            await kantian_checker.evaluate(action_using_humans_as_means)

        # Assert exception details
        assert "kantian_deontology" in str(exc_info.value)
        assert "use_humans_as_mere_means" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_veto_autonomy_violation(self, kantian_checker, action_violating_autonomy):
        """
        SCENARIO: Action violates human autonomy
        EXPECTED: VetoException raised
        """
        # Act & Assert
        with pytest.raises(VetoException):
            await kantian_checker.evaluate(action_violating_autonomy)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_veto_surveillance_no_consent(self, kantian_checker, action_surveillance_no_consent):
        """
        SCENARIO: Surveillance without consent or legal basis
        EXPECTED: VetoException raised
        """
        # Act & Assert
        with pytest.raises(VetoException) as exc_info:
            await kantian_checker.evaluate(action_surveillance_no_consent)

        assert "implement_surveillance_without_consent" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_veto_with_veto_disabled(self, kantian_no_veto, action_using_humans_as_means):
        """
        SCENARIO: Violation occurs but veto is disabled
        EXPECTED: Returns rejected result without raising exception
        """
        # Act
        result = await kantian_no_veto.evaluate(action_using_humans_as_means)

        # Assert
        assert isinstance(result, EthicalFrameworkResult)
        assert result.approved is False
        assert result.veto is True  # Marks as veto-worthy
        assert result.verdict == EthicalVerdict.REJECTED
        assert "use_humans_as_mere_means" in result.explanation

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_authorized_pentest_allowed(self, kantian_checker):
        """
        SCENARIO: Social engineering in authorized pentest
        EXPECTED: Exception for authorized context, passes
        """
        # Arrange - Authorized pentest
        action = ActionContext(
            action_description="Conduct social engineering test on employees",
            action_type="pentest",
                system_component="test_kantian_checker",
            urgency="low",
            operator_context={"authorized_pentest": True, "operator_id": "pentest_team"},
            threat_data={"justification": "Annual security awareness training"},
            impact_assessment={}
        )

        # Act
        result = await kantian_checker.evaluate(action)

        # Assert - Should pass with authorization
        assert result.approved is True
        assert result.verdict == EthicalVerdict.APPROVED

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_offensive_action_needs_approval(self, kantian_checker):
        """
        SCENARIO: Offensive action without operator approval
        EXPECTED: VetoException for autonomous offensive
        """
        # Arrange
        action = ActionContext(
            action_description="Deploy offensive payload autonomously",
            action_type="offensive_action",
                system_component="test_kantian_checker",
            urgency="medium",
            operator_context=None,  # No approval
            threat_data={},
            impact_assessment={}
        )

        # Act & Assert
        with pytest.raises(VetoException) as exc_info:
            await kantian_checker.evaluate(action)

        assert "deploy_offensive_autonomously_without_approval" in str(exc_info.value)


# ===== CATEGORICAL ALWAYS RULES TESTS =====

class TestCategoricalAlwaysRules:
    """Tests for categorical obligations (ALWAYS rules)."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_veto_removes_human_control(self, kantian_checker):
        """
        SCENARIO: Action removes human override capability
        EXPECTED: VetoException raised
        """
        # Arrange
        action = ActionContext(
            action_description="Implement fully autonomous decision-making with no override",
            action_type="auto_response",
                system_component="test_kantian_checker",
            urgency="medium",
            operator_context={},
            threat_data={},
            impact_assessment={"removes_human_control": True}  # Violation
        )

        # Act & Assert
        with pytest.raises(VetoException) as exc_info:
            await kantian_checker.evaluate(action)

        assert "preserve_human_override_capability" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_veto_insufficient_explanation(self, kantian_checker):
        """
        SCENARIO: Action lacks proper explanation (< 20 chars, but >= 10 for validation)
        EXPECTED: VetoException for transparency violation
        """
        # Arrange
        action = ActionContext(
            action_description="Block this IP",  # Meets 10 char minimum, but < 20 for transparency
            action_type="auto_response",
                system_component="test_kantian_checker",
            urgency="medium",
            operator_context={},
            threat_data={},
            impact_assessment={}
        )

        # Act & Assert
        with pytest.raises(VetoException) as exc_info:
            await kantian_checker.evaluate(action)

        assert "provide_explanation_for_actions" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_veto_data_access_without_justification(self, kantian_checker):
        """
        SCENARIO: Data access without privacy justification
        EXPECTED: VetoException for privacy violation
        """
        # Arrange
        action = ActionContext(
            action_description="Access user private data for analysis purposes",
            action_type="data_access",
                system_component="test_kantian_checker",
            urgency="low",
            operator_context={},
            threat_data={},  # No justification
            impact_assessment={}
        )

        # Act & Assert
        with pytest.raises(VetoException) as exc_info:
            await kantian_checker.evaluate(action)

        assert "respect_privacy_as_inviolable_right" in str(exc_info.value)


# ===== UNIVERSALIZABILITY TESTS =====

class TestUniversalizability:
    """Tests for universalizability (First Formulation)."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_lying_fails_universalizability(self, kantian_no_veto):
        """
        SCENARIO: Action involves lying/deception
        EXPECTED: Fails universalizability test
        """
        # Arrange
        action = ActionContext(
            action_description="Deceive the attacker with false information to gain advantage",
            action_type="defensive_deception",
                system_component="test_kantian_checker",
            urgency="medium",
            operator_context={"approved": True},
            threat_data={"justification": "Active attack"},
            impact_assessment={}
        )

        # Act
        result = await kantian_no_veto.evaluate(action)

        # Assert
        assert result.approved is False
        assert result.verdict == EthicalVerdict.REJECTED
        assert "universalizability" in result.explanation.lower()
        assert result.metadata["universalizability_passed"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ddos_fails_universalizability(self, kantian_no_veto):
        """
        SCENARIO: DDoS action (infrastructure collapse if universal)
        EXPECTED: Fails universalizability
        """
        # Arrange
        action = ActionContext(
            action_description="Launch DDoS flood attack against target infrastructure",
            action_type="offensive_action",
                system_component="test_kantian_checker",
            urgency="high",
            operator_context={"approved": True},
            threat_data={"confidence": 0.95},
            impact_assessment={}
        )

        # Act
        result = await kantian_no_veto.evaluate(action)

        # Assert
        assert result.approved is False
        assert "Universal DDoS would collapse internet infrastructure" in result.explanation


    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_preemptive_low_confidence_fails_universalizability(self, kantian_no_veto):
        """
        SCENARIO: Preemptive attack with low confidence
        EXPECTED: Fails universalizability (would create chaos)
        """
        # Arrange
        action = ActionContext(
            action_description="Execute preemptive offensive action based on intelligence",
            action_type="offensive_action",
                system_component="test_kantian_checker",
            urgency="medium",
            operator_context={"approved": True},
            threat_data={"confidence": 0.60},  # Low confidence
            impact_assessment={}
        )

        # Act
        result = await kantian_no_veto.evaluate(action)

        # Assert
        assert result.approved is False
        assert "preemptive" in result.explanation.lower()
        assert result.metadata["universalizability_passed"] is False


# ===== HUMANITY FORMULA TESTS =====

class TestHumanityFormula:
    """Tests for humanity formula (Second Formulation)."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_social_engineering_fails_humanity_formula(self, kantian_no_veto):
        """
        SCENARIO: Social engineering without authorization
        EXPECTED: Fails humanity formula (uses humans as mere means)
        """
        # Arrange
        action = ActionContext(
            action_description="Conduct social engineering campaign to gather credentials",
            action_type="intelligence_gathering",
                system_component="test_kantian_checker",
            urgency="low",
            operator_context={},  # No authorization
            threat_data={},
            impact_assessment={}
        )

        # Act
        result = await kantian_no_veto.evaluate(action)

        # Assert
        assert result.approved is False
        assert "humanity formula" in result.explanation.lower() or "Social engineering" in result.explanation
        assert result.metadata["humanity_formula_passed"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sacrificing_individual_rights_fails(self, kantian_no_veto):
        """
        SCENARIO: Action sacrifices individual for collective benefit
        EXPECTED: Fails humanity formula (treats person as mere means)
        """
        # Arrange
        action = ActionContext(
            action_description="Expose single user to malware to protect the network majority",
            action_type="defensive_strategy",
                system_component="test_kantian_checker",
            urgency="high",
            operator_context={"approved": True},
            threat_data={"justification": "Network protection"},
            impact_assessment={"sacrifices_individual_rights": True}  # Violation
        )

        # Act
        result = await kantian_no_veto.evaluate(action)

        # Assert
        assert result.approved is False
        assert "individual rights" in result.explanation or "mere means" in result.explanation
        assert result.metadata["humanity_formula_passed"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_low_urgency_auto_response_without_human_fails(self, kantian_no_veto):
        """
        SCENARIO: Low-urgency auto-response without human involvement
        EXPECTED: Fails humanity formula (bypasses autonomy when time permits)
        """
        # Arrange
        action = ActionContext(
            action_description="Automatically block suspicious user account activity",
            action_type="auto_response",
                system_component="test_kantian_checker",
            urgency="low",  # Time permits human involvement
            operator_context=None,  # No human involved
            threat_data={"confidence": 0.7},
            impact_assessment={}
        )

        # Act
        result = await kantian_no_veto.evaluate(action)

        # Assert
        assert result.approved is False
        assert "autonomy" in result.explanation.lower()
        assert result.metadata["humanity_formula_passed"] is False


# ===== APPROVED ACTIONS TESTS =====

class TestApprovedActions:
    """Tests for actions that should pass all Kantian tests."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_benign_action_approved(self, kantian_checker, benign_action):
        """
        SCENARIO: Well-justified defensive action with consent
        EXPECTED: Passes all tests, approved
        """
        # Act
        result = await kantian_checker.evaluate(benign_action)

        # Assert
        assert result.approved is True
        assert result.verdict == EthicalVerdict.APPROVED
        assert result.veto is False
        assert result.confidence >= 0.95
        assert result.metadata["universalizability_passed"] is True
        assert result.metadata["humanity_formula_passed"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_critical_autonomy_override_justified(self, kantian_checker):
        """
        SCENARIO: Critical situation justifies autonomy override
        EXPECTED: Exception granted, approved
        """
        # Arrange - Critical security situation
        action = ActionContext(
            action_description="Override autonomy to prevent imminent critical threat to others",
            action_type="emergency_response",
                system_component="test_kantian_checker",
            urgency="critical",  # Critical urgency
            operator_context={"approved": True},
            threat_data={"severity": 0.95, "confidence": 0.98},  # High severity justification
            impact_assessment={}
        )

        # Act
        result = await kantian_checker.evaluate(action)

        # Assert - Should pass with critical justification
        assert result.approved is True
        assert result.verdict == EthicalVerdict.APPROVED

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitoring_with_legal_basis_approved(self, kantian_checker):
        """
        SCENARIO: Monitoring with legal basis (even without explicit consent)
        EXPECTED: Approved with legal justification
        """
        # Arrange
        action = ActionContext(
            action_description="Monitor network traffic as part of employment agreement",
            action_type="defensive_monitoring",
                system_component="test_kantian_checker",
            urgency="medium",
            operator_context={"approved": True},
            threat_data={
                "legal_basis": "employment_contract",
                "justification": "Authorized network security"
            },
            impact_assessment={}
        )

        # Act
        result = await kantian_checker.evaluate(action)

        # Assert
        assert result.approved is True
        assert result.verdict == EthicalVerdict.APPROVED


# ===== PERFORMANCE & METADATA TESTS =====

class TestPerformanceAndMetadata:
    """Tests for performance metrics and metadata."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_latency_measurement(self, kantian_checker, benign_action):
        """
        SCENARIO: Evaluate action and check latency
        EXPECTED: Latency measured and reasonable
        """
        # Act
        result = await kantian_checker.evaluate(benign_action)

        # Assert
        assert result.latency_ms >= 0
        assert result.latency_ms < 1000  # Should be fast

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_metadata_includes_test_results(self, kantian_checker, benign_action):
        """
        SCENARIO: Check metadata includes all test results
        EXPECTED: Metadata has universalizability and humanity formula results
        """
        # Act
        result = await kantian_checker.evaluate(benign_action)

        # Assert
        assert "universalizability_passed" in result.metadata
        assert "universalizability_details" in result.metadata
        assert "humanity_formula_passed" in result.metadata
        assert "humanity_formula_details" in result.metadata

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reasoning_steps_captured(self, kantian_checker, benign_action):
        """
        SCENARIO: Evaluate action and check reasoning
        EXPECTED: Reasoning steps captured
        """
        # Act
        result = await kantian_checker.evaluate(benign_action)

        # Assert
        assert isinstance(result.reasoning_steps, list)
        assert len(result.reasoning_steps) > 0
        assert any("categorical" in step.lower() for step in result.reasoning_steps)


# ===== EDGE CASES TESTS =====

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_empty_action_description(self, kantian_checker):
        """
        SCENARIO: Action with empty description
        EXPECTED: ValueError during ActionContext validation
        """
        # Act & Assert - Should fail validation before reaching Kantian checker
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="",  # Empty
                action_type="auto_response",
                    system_component="test_kantian_checker",
                urgency="low",
                operator_context={},
                threat_data={},
                impact_assessment={}
            )

        assert "action_description is required" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_none_threat_data(self, kantian_checker):
        """
        SCENARIO: Action with None threat_data
        EXPECTED: Handles gracefully
        """
        # Arrange
        action = ActionContext(
            action_description="Monitor network traffic for defensive purposes with proper justification",
            action_type="defensive_monitoring",
                system_component="test_kantian_checker",
            urgency="medium",
            operator_context={"approved": True},
            threat_data=None,  # None
            impact_assessment={}
        )

        # Act
        result = await kantian_checker.evaluate(action)

        # Assert - Should handle None gracefully
        assert isinstance(result, EthicalFrameworkResult)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reversible_block_exception(self, kantian_checker):
        """
        SCENARIO: Irreversible keyword but reversible block action
        EXPECTED: Exception granted for auto-block (reversible via unblock)
        """
        # Arrange
        action = ActionContext(
            action_description="Permanent block of malicious IP address (reversible via unblock)",
            action_type="auto_response",
                system_component="test_kantian_checker",
            urgency="high",
            operator_context={"approved": True},
            threat_data={"confidence": 0.95, "severity": 0.9},
            impact_assessment={}
        )

        # Act
        result = await kantian_checker.evaluate(action)

        # Assert - Should pass with reversible block exception
        assert result.approved is True
        assert result.verdict == EthicalVerdict.APPROVED
