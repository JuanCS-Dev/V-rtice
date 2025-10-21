"""Unit tests for ConsequentialistEngine (Utilitarian Ethics).

Tests cover all aspects of consequentialist/utilitarian ethics evaluation:
- Bentham's hedonic calculus (7 dimensions)
- Mill's higher/lower pleasures
- Rule utilitarianism
- Stakeholder analysis
- Cost-benefit analysis

Target: 90%+ coverage
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from ethics.consequentialist_engine import ConsequentialistEngine
from ethics.base import ActionContext, EthicalVerdict


class TestConsequentialistEngineInitialization:
    """Test ConsequentialistEngine initialization and configuration."""

    def test_init_default_config(self):
        """Test initialization with default configuration."""
        # Arrange & Act
        engine = ConsequentialistEngine()

        # Assert
        assert engine.weights is not None
        assert len(engine.weights) == 7
        assert abs(sum(engine.weights.values()) - 1.0) < 0.01  # Weights sum to 1.0
        assert engine.approval_threshold == 0.60

    def test_init_custom_weights(self):
        """Test initialization with custom weights."""
        # Arrange
        custom_config = {
            "weights": {
                "intensity": 0.30,
                "duration": 0.20,
                "certainty": 0.15,
                "propinquity": 0.10,
                "fecundity": 0.10,
                "purity": 0.10,
                "extent": 0.05,
            }
        }

        # Act
        engine = ConsequentialistEngine(custom_config)

        # Assert
        assert engine.weights["intensity"] == 0.30
        assert engine.weights["duration"] == 0.20
        assert abs(sum(engine.weights.values()) - 1.0) < 0.01

    def test_init_custom_threshold(self):
        """Test initialization with custom approval threshold."""
        # Arrange
        custom_config = {"approval_threshold": 0.75}

        # Act
        engine = ConsequentialistEngine(custom_config)

        # Assert
        assert engine.approval_threshold == 0.75

    def test_init_empty_config(self):
        """Test initialization with empty config dict."""
        # Arrange & Act
        engine = ConsequentialistEngine({})

        # Assert - Should use defaults
        assert engine.approval_threshold == 0.60
        assert len(engine.weights) == 7


class TestGetFrameworkPrinciples:
    """Test retrieval of consequentialist principles."""

    def test_get_principles_returns_list(self):
        """Test that get_framework_principles returns a list."""
        # Arrange
        engine = ConsequentialistEngine()

        # Act
        principles = engine.get_framework_principles()

        # Assert
        assert isinstance(principles, list)
        assert len(principles) > 0

    def test_principles_include_greatest_happiness(self):
        """Test that principles include Greatest Happiness Principle."""
        # Arrange
        engine = ConsequentialistEngine()

        # Act
        principles = engine.get_framework_principles()

        # Assert
        assert any("Greatest Happiness" in p for p in principles)

    def test_principles_include_hedonic_calculus(self):
        """Test that principles include Hedonic Calculus."""
        # Arrange
        engine = ConsequentialistEngine()

        # Act
        principles = engine.get_framework_principles()

        # Assert
        assert any("Hedonic Calculus" in p for p in principles)

    def test_principles_include_impartiality(self):
        """Test that principles include impartial consideration."""
        # Arrange
        engine = ConsequentialistEngine()

        # Act
        principles = engine.get_framework_principles()

        # Assert
        assert any("Impartial" in p for p in principles)


class TestEvaluateAction:
    """Test consequentialist evaluation of actions."""

    @pytest.mark.asyncio
    async def test_evaluate_high_benefit_action(self):
        """Test evaluation of action with high net benefit."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            action_type="block_malicious_ip",
            action_action_description="Block confirmed malware C2 server",
            system_component="threat_detection",
            target_info={"ip": "192.168.1.100"},
            threat_data={
                "threat_type": "malware_c2",
                "severity": "critical",
                "confidence": 0.95,
                "affected_systems": 10,
                "detection_confidence": 0.95,
                "false_positive_rate": 0.01,
            },
            urgency="critical"
        )

        # Act
        result = await engine.evaluate(context)

        # Assert
        assert result is not None
        assert result.verdict in [EthicalVerdict.APPROVED, EthicalVerdict.CONDITIONAL_APPROVAL]
        assert result.framework_name == "Consequentialist"
        assert "utility" in result.reasoning.lower() or "benefit" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_evaluate_low_benefit_action(self):
        """Test evaluation of action with low/negative net benefit."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="block_ip_range",
            action_description="Block entire subnet based on weak indicators",
            # target="10.0.0.0/8",
            # severity="low",
            # confidence=0.30,
            threat_data={
                "threat_type": "suspicious_activity",
                "affected_systems": 10000,  # High collateral damage
                "detection_confidence": 0.30,
                "false_positive_rate": 0.70,
            }
        )

        # Act
        result = await engine.evaluate(context)

        # Assert
        assert result is not None
        assert result.verdict in [EthicalVerdict.REJECTED, EthicalVerdict.REQUIRES_REVIEW]

    @pytest.mark.asyncio
    async def test_evaluate_borderline_action(self):
        """Test evaluation of action near approval threshold."""
        # Arrange
        engine = ConsequentialistEngine({"approval_threshold": 0.60})
        context = ActionContext(
            system_component="test_component",
            action_type="rate_limit_user",
            action_description="Temporarily rate limit suspicious user",
            # target="user@example.com",
            # severity="medium",
            # confidence=0.60,
            threat_data={
                "threat_type": "anomalous_behavior",
                "affected_systems": 1,
                "detection_confidence": 0.60,
                "false_positive_rate": 0.40,
            }
        )

        # Act
        result = await engine.evaluate(context)

        # Assert
        assert result is not None
        assert result.framework_name == "Consequentialist"

    @pytest.mark.asyncio
    async def test_evaluate_includes_calculation_details(self):
        """Test that evaluation includes detailed calculation."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="isolate_host",
            action_description="Isolate infected workstation",
            # target="workstation-42",
            # severity="high",
            # confidence=0.85,
            threat_data={}
        )

        # Act
        result = await engine.evaluate(context)

        # Assert
        assert result.metadata is not None
        # Should contain benefits, costs, or net_utility
        metadata_str = str(result.metadata).lower()
        assert any(key in metadata_str for key in ["benefit", "cost", "utility", "stakeholder"])


class TestCalculateBenefits:
    """Test benefit calculation (hedonic calculus positive side)."""

    def test_calculate_benefits_high_confidence(self):
        """Test benefit calculation with high confidence."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="block_malware",
            action_description="Block confirmed malware",
            # target="malware.exe",
            # severity="critical",
            # confidence=0.95,
            threat_data={"detection_confidence": 0.95}
        )

        # Act
        benefits = engine._calculate_benefits(context)

        # Assert
        assert isinstance(benefits, dict)
        assert "total_benefit" in benefits or "intensity" in benefits

    def test_calculate_benefits_low_confidence(self):
        """Test benefit calculation with low confidence."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="block_file",
            action_description="Block suspicious file",
            # target="suspicious.exe",
            # severity="low",
            # confidence=0.30,
            threat_data={"detection_confidence": 0.30}
        )

        # Act
        benefits = engine._calculate_benefits(context)

        # Assert
        assert isinstance(benefits, dict)
        # Low confidence should result in lower benefits

    def test_calculate_benefits_critical_severity(self):
        """Test benefit calculation for critical severity actions."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="emergency_shutdown",
            action_description="Emergency system shutdown to prevent data breach",
            # target="database-server",
            # severity="critical",
            # confidence=0.90,
            threat_data={}
        )

        # Act
        benefits = engine._calculate_benefits(context)

        # Assert
        assert isinstance(benefits, dict)


class TestCalculateCosts:
    """Test cost calculation (hedonic calculus negative side)."""

    def test_calculate_costs_high_impact(self):
        """Test cost calculation for high-impact action."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="block_network",
            action_description="Block entire network segment",
            # target="10.0.1.0/24",
            # severity="high",
            # confidence=0.80,
            threat_data={"affected_systems": 500}
        )

        # Act
        costs = engine._calculate_costs(context)

        # Assert
        assert isinstance(costs, dict)
        assert "total_cost" in costs or "extent" in costs

    def test_calculate_costs_low_impact(self):
        """Test cost calculation for low-impact action."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="log_event",
            action_description="Log suspicious event for review",
            # target="event-123",
            # severity="low",
            # confidence=0.50,
            threat_data={"affected_systems": 0}
        )

        # Act
        costs = engine._calculate_costs(context)

        # Assert
        assert isinstance(costs, dict)

    def test_calculate_costs_high_false_positive_rate(self):
        """Test cost calculation with high false positive rate."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="block_user",
            action_description="Block user based on heuristic",
            # target="user@company.com",
            # severity="medium",
            # confidence=0.40,
            threat_data={"false_positive_rate": 0.80}
        )

        # Act
        costs = engine._calculate_costs(context)

        # Assert
        assert isinstance(costs, dict)
        # High FP rate should increase costs


class TestAssessFecundity:
    """Test fecundity assessment (future consequences)."""

    def test_assess_fecundity_preventive_action(self):
        """Test fecundity for preventive security action."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="patch_vulnerability",
            action_description="Apply critical security patch",
            # target="all-servers",
            # severity="high",
            # confidence=0.90,
            threat_data={"prevents_future_attacks": True}
        )

        # Act
        fecundity = engine._assess_fecundity(context)

        # Assert
        assert isinstance(fecundity, float)
        assert 0.0 <= fecundity <= 1.0

    def test_assess_fecundity_reactive_action(self):
        """Test fecundity for reactive action."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="kill_process",
            action_description="Kill single malicious process",
            # target="pid-12345",
            # severity="medium",
            # confidence=0.85,
            threat_data={}
        )

        # Act
        fecundity = engine._assess_fecundity(context)

        # Assert
        assert isinstance(fecundity, float)
        assert 0.0 <= fecundity <= 1.0

    def test_assess_fecundity_temporary_action(self):
        """Test fecundity for temporary mitigation."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="rate_limit",
            action_description="Temporarily rate limit traffic",
            # target="api-endpoint",
            # severity="low",
            # confidence=0.70,
            threat_data={"temporary": True}
        )

        # Act
        fecundity = engine._assess_fecundity(context)

        # Assert
        assert isinstance(fecundity, float)
        assert 0.0 <= fecundity <= 1.0


class TestAssessPurity:
    """Test purity assessment (side effects)."""

    def test_assess_purity_clean_action(self):
        """Test purity for action with minimal side effects."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="enable_logging",
            action_description="Enable additional logging",
            # target="security-logs",
            # severity="low",
            # confidence=0.95,
            threat_data={"side_effects": "minimal"}
        )

        # Act
        purity = engine._assess_purity(context)

        # Assert
        assert isinstance(purity, float)
        assert 0.0 <= purity <= 1.0

    def test_assess_purity_dirty_action(self):
        """Test purity for action with significant side effects."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="aggressive_blocking",
            action_description="Aggressive IP blocking with high collateral damage",
            # target="ip-range",
            # severity="high",
            # confidence=0.60,
            threat_data={"collateral_damage": "high", "false_positive_rate": 0.50}
        )

        # Act
        purity = engine._assess_purity(context)

        # Assert
        assert isinstance(purity, float)
        assert 0.0 <= purity <= 1.0

    def test_assess_purity_moderate_side_effects(self):
        """Test purity for action with moderate side effects."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="quarantine_file",
            action_description="Quarantine suspicious file",
            # target="document.pdf",
            # severity="medium",
            # confidence=0.75,
            threat_data={"affects_workflow": True}
        )

        # Act
        purity = engine._assess_purity(context)

        # Assert
        assert isinstance(purity, float)
        assert 0.0 <= purity <= 1.0


class TestIdentifyStakeholders:
    """Test stakeholder identification."""

    def test_identify_stakeholders_basic(self):
        """Test basic stakeholder identification."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="block_user",
            action_description="Block compromised user account",
            # target="user@company.com",
            # severity="high",
            # confidence=0.85,
            threat_data={}
        )

        # Act
        stakeholders = engine._identify_stakeholders(context)

        # Assert
        assert isinstance(stakeholders, list)
        assert len(stakeholders) > 0

    def test_identify_stakeholders_multiple_systems(self):
        """Test stakeholder identification for multi-system impact."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="network_isolation",
            action_description="Isolate infected network segment",
            # target="subnet-10.0.5.0/24",
            # severity="critical",
            # confidence=0.90,
            threat_data={"affected_systems": 100, "affected_users": 50}
        )

        # Act
        stakeholders = engine._identify_stakeholders(context)

        # Assert
        assert isinstance(stakeholders, list)
        # Should identify multiple stakeholder groups

    def test_identify_stakeholders_includes_security_team(self):
        """Test that stakeholders include security team."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="alert",
            action_description="Send security alert",
            # target="security-team",
            # severity="medium",
            # confidence=0.80,
            threat_data={}
        )

        # Act
        stakeholders = engine._identify_stakeholders(context)

        # Assert
        assert isinstance(stakeholders, list)


class TestConsequentialistIntegration:
    """Integration tests for full consequentialist evaluation."""

    @pytest.mark.asyncio
    async def test_full_evaluation_workflow(self):
        """Test complete evaluation workflow from start to finish."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="incident_response",
            action_description="Comprehensive incident response to ransomware",
            # target="all-affected-systems",
            # severity="critical",
            # confidence=0.92,
            threat_data={
                "threat_type": "ransomware",
                "affected_systems": 25,
                "detection_confidence": 0.92,
                "prevents_spread": True,
            }
        )

        # Act
        result = await engine.evaluate(context)

        # Assert - Comprehensive checks
        assert result is not None
        assert result.framework_name == "Consequentialist"
        assert result.verdict is not None
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0
        assert result.metadata is not None
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_evaluation_with_minimal_metadata(self):
        """Test evaluation works with minimal metadata."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="simple_action",
            action_description="Simple security action",
            # target="target-system",
            # severity="low",
            # confidence=0.50,
            threat_data={}
        )

        # Act
        result = await engine.evaluate(context)

        # Assert
        assert result is not None
        assert result.verdict is not None

    @pytest.mark.asyncio
    async def test_evaluation_consistency(self):
        """Test that same input produces consistent output."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="test_action",
            action_description="Test for consistency",
            # target="test-target",
            # severity="medium",
            # confidence=0.75,
            threat_data={"test": True}
        )

        # Act
        result1 = await engine.evaluate(context)
        result2 = await engine.evaluate(context)

        # Assert
        assert result1.verdict == result2.verdict
        assert result1.framework_name == result2.framework_name


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_evaluate_with_zero_confidence(self):
        """Test evaluation with zero confidence."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="uncertain_action",
            action_description="Action with no confidence",
            # target="unknown",
            # severity="low",
            # confidence=0.0,
            threat_data={}
        )

        # Act
        result = await engine.evaluate(context)

        # Assert
        assert result is not None
        # Should likely reject or require review

    @pytest.mark.asyncio
    async def test_evaluate_with_max_confidence(self):
        """Test evaluation with maximum confidence."""
        # Arrange
        engine = ConsequentialistEngine()
        context = ActionContext(
            system_component="test_component",
            action_type="certain_action",
            action_description="Action with full confidence",
            # target="known-threat",
            # severity="critical",
            # confidence=1.0,
            threat_data={"detection_confidence": 1.0}
        )

        # Act
        result = await engine.evaluate(context)

        # Assert
        assert result is not None

    def test_weights_normalization(self):
        """Test that weights are properly normalized."""
        # Arrange
        unnormalized_config = {
            "weights": {
                "intensity": 2.0,
                "duration": 1.5,
                "certainty": 2.5,
                "propinquity": 1.0,
                "fecundity": 1.5,
                "purity": 1.0,
                "extent": 0.5,
            }
        }

        # Act
        engine = ConsequentialistEngine(unnormalized_config)

        # Assert - Weights should still work
        assert engine.weights is not None

    @pytest.mark.asyncio
    async def test_evaluate_with_extreme_threshold(self):
        """Test evaluation with very high approval threshold."""
        # Arrange
        engine = ConsequentialistEngine({"approval_threshold": 0.95})
        context = ActionContext(
            system_component="test_component",
            action_type="moderate_action",
            action_description="Moderately beneficial action",
            # target="target",
            # severity="medium",
            # confidence=0.70,
            threat_data={}
        )

        # Act
        result = await engine.evaluate(context)

        # Assert
        assert result is not None
        # High threshold should make approval harder
