"""
Guardian Coordinator - Comprehensive Test Suite

Tests for the central coordinator of all Guardian Agents implementing
Anexo D: A Doutrina da "Execução Constitucional".

Coverage target: 100%

Author: Claude Code + JuanCS-Dev
Date: 2025-10-14
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from .base import (
    ConstitutionalArticle,
    ConstitutionalViolation,
    GuardianDecision,
    GuardianIntervention,
    GuardianPriority,
    InterventionType,
    VetoAction,
)
from .coordinator import GuardianCoordinator

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def coordinator():
    """Create GuardianCoordinator instance."""
    return GuardianCoordinator()


@pytest.fixture
def sample_violation():
    """Create sample constitutional violation."""
    return ConstitutionalViolation(
        article=ConstitutionalArticle.ARTICLE_II,
        clause="Seção 2",
        rule="No MOCKS or PLACEHOLDERS in production code",
        description="Found TODO in production code",
        severity=GuardianPriority.HIGH,
        evidence=["# TODO: implement this"],
        affected_systems=["maximus_core"],
        recommended_action="Remove TODO and implement feature",
    )


@pytest.fixture
def sample_intervention():
    """Create sample guardian intervention."""
    return GuardianIntervention(
        guardian_id="guardian-article-ii",
        intervention_type=InterventionType.WARNING,
        decision=GuardianDecision.WARN,
        reason="Code quality issue detected",
        context={"file": "test.py", "line": 42},
    )


@pytest.fixture
def sample_veto():
    """Create sample veto action."""
    violation = ConstitutionalViolation(
        article=ConstitutionalArticle.ARTICLE_V,
        clause="Seção 1",
        rule="Governance before autonomy",
        description="Autonomous system without governance",
        severity=GuardianPriority.CRITICAL,
        evidence=["Missing safety checks"],
        affected_systems=["autonomous_agent"],
        recommended_action="Block deployment",
    )

    return VetoAction(
        guardian_id="guardian-article-v",
        target_operation="deploy_autonomous_agent",
        reason="Missing governance controls",
        violation=violation,
        override_allowed=True,
    )


# ============================================================================
# LIFECYCLE TESTS
# ============================================================================


class TestCoordinatorLifecycle:
    """Test coordinator lifecycle management."""

    @pytest.mark.asyncio
    async def test_init_all_guardians(self, coordinator):
        """Test coordinator initializes all Guardian Agents."""
        assert "article_ii" in coordinator.guardians
        assert "article_iii" in coordinator.guardians
        assert "article_iv" in coordinator.guardians
        assert "article_v" in coordinator.guardians
        assert len(coordinator.guardians) == 4

    @pytest.mark.asyncio
    async def test_start_coordinator(self, coordinator):
        """Test starting the coordinator."""
        assert not coordinator._is_active

        await coordinator.start()

        assert coordinator._is_active
        assert coordinator._coordination_task is not None

        # Verify all guardians started
        for guardian in coordinator.guardians.values():
            assert guardian.is_active()

        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_start_already_active(self, coordinator):
        """Test starting already active coordinator is idempotent."""
        await coordinator.start()
        assert coordinator._is_active

        # Start again - should be idempotent
        await coordinator.start()
        assert coordinator._is_active

        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_stop_coordinator(self, coordinator):
        """Test stopping the coordinator."""
        await coordinator.start()
        assert coordinator._is_active

        await coordinator.stop()

        assert not coordinator._is_active
        for guardian in coordinator.guardians.values():
            assert not guardian.is_active()

    @pytest.mark.asyncio
    async def test_stop_not_active(self, coordinator):
        """Test stopping inactive coordinator."""
        assert not coordinator._is_active

        # Should not raise error
        await coordinator.stop()

        assert not coordinator._is_active


# ============================================================================
# VIOLATION HANDLING TESTS
# ============================================================================


class TestViolationHandling:
    """Test violation handling and aggregation."""

    @pytest.mark.asyncio
    async def test_handle_violation_updates_metrics(self, coordinator, sample_violation):
        """Test handling violation updates metrics."""
        initial_count = coordinator.metrics.total_violations_detected

        await coordinator._handle_violation(sample_violation)

        assert coordinator.metrics.total_violations_detected == initial_count + 1
        assert sample_violation in coordinator.all_violations

    @pytest.mark.asyncio
    async def test_handle_violation_by_article(self, coordinator):
        """Test violations counted by article."""
        violation_ii = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test rule",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Test",
        )

        violation_iii = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            clause="Test",
            rule="Test rule",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Test",
        )

        await coordinator._handle_violation(violation_ii)
        await coordinator._handle_violation(violation_iii)

        assert coordinator.metrics.violations_by_article["ARTICLE_II"] == 1
        assert coordinator.metrics.violations_by_article["ARTICLE_III"] == 1

    @pytest.mark.asyncio
    async def test_handle_violation_by_severity(self, coordinator):
        """Test violations counted by severity."""
        violation_high = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test rule",
            description="Test",
            severity=GuardianPriority.HIGH,
            evidence=[],
            affected_systems=[],
            recommended_action="Test",
        )

        violation_critical = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test rule",
            description="Test",
            severity=GuardianPriority.CRITICAL,
            evidence=[],
            affected_systems=[],
            recommended_action="Test",
        )

        await coordinator._handle_violation(violation_high)
        await coordinator._handle_violation(violation_critical)

        assert coordinator.metrics.violations_by_severity["HIGH"] == 1
        assert coordinator.metrics.violations_by_severity["CRITICAL"] == 1

    @pytest.mark.asyncio
    async def test_handle_critical_violation_sends_alert(self, coordinator):
        """Test critical violation triggers alert."""
        critical_violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            clause="Critical",
            rule="Critical rule",
            description="Critical violation",
            severity=GuardianPriority.CRITICAL,
            evidence=["Critical evidence"],
            affected_systems=["critical_system"],
            recommended_action="Immediate action",
        )

        # Mock _send_critical_alert
        coordinator._send_critical_alert = AsyncMock()

        await coordinator._handle_violation(critical_violation)

        # Verify alert was sent
        coordinator._send_critical_alert.assert_called_once_with(critical_violation)


# ============================================================================
# INTERVENTION HANDLING TESTS
# ============================================================================


class TestInterventionHandling:
    """Test intervention and veto handling."""

    @pytest.mark.asyncio
    async def test_handle_intervention_increments_counter(
        self, coordinator, sample_intervention
    ):
        """Test handling intervention increments counter."""
        initial_count = coordinator.metrics.interventions_made

        await coordinator._handle_intervention(sample_intervention)

        assert coordinator.metrics.interventions_made == initial_count + 1
        assert sample_intervention in coordinator.all_interventions

    @pytest.mark.asyncio
    async def test_handle_veto_increments_counter(self, coordinator, sample_veto):
        """Test handling veto increments counter."""
        initial_count = coordinator.metrics.vetos_enacted

        await coordinator._handle_veto(sample_veto)

        assert coordinator.metrics.vetos_enacted == initial_count + 1
        assert sample_veto in coordinator.all_vetos

    @pytest.mark.asyncio
    async def test_veto_escalation_threshold(self, coordinator):
        """Test veto escalation when threshold reached."""
        coordinator.veto_escalation_threshold = 3

        # Mock _escalate_vetos
        coordinator._escalate_vetos = AsyncMock()

        # Create 3 recent vetos
        for i in range(3):
            veto = VetoAction(
                guardian_id=f"guardian-{i}",
                target_operation=f"operation-{i}",
                reason="Test reason",
                violation=None,
            )
            await coordinator._handle_veto(veto)

        # Verify escalation was triggered
        coordinator._escalate_vetos.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_escalation_below_threshold(self, coordinator):
        """Test no escalation when below threshold."""
        coordinator.veto_escalation_threshold = 5

        # Mock _escalate_vetos
        coordinator._escalate_vetos = AsyncMock()

        # Create 2 vetos (below threshold)
        for i in range(2):
            veto = VetoAction(
                guardian_id=f"guardian-{i}",
                target_operation=f"operation-{i}",
                reason="Test reason",
                violation=None,
            )
            await coordinator._handle_veto(veto)

        # No escalation should occur
        coordinator._escalate_vetos.assert_not_called()

    @pytest.mark.asyncio
    async def test_escalate_multiple_vetos(self, coordinator):
        """Test escalation of multiple vetos."""
        vetos = [
            VetoAction(
                guardian_id=f"guardian-{i}",
                target_operation=f"operation-{i}",
                reason="Test reason",
                violation=None,
            )
            for i in range(3)
        ]

        # Should not raise error
        await coordinator._escalate_vetos(vetos)


# ============================================================================
# CONFLICT RESOLUTION TESTS
# ============================================================================


class TestConflictResolution:
    """Test conflict resolution between Guardians."""

    @pytest.mark.asyncio
    async def test_resolve_no_conflicts(self, coordinator):
        """Test conflict resolution with no conflicts."""
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test rule",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Fix code",
            context={"file": "test.py"},
        )

        coordinator.all_violations = [violation]

        # Should not raise error
        await coordinator._resolve_conflicts()

        # No conflicts should be created
        assert len(coordinator.conflict_resolutions) == 0

    @pytest.mark.asyncio
    async def test_resolve_same_target_conflicts(self, coordinator):
        """Test resolving conflicts on same target."""
        violation1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test rule 1",
            description="Violation 1",
            severity=GuardianPriority.HIGH,
            evidence=[],
            affected_systems=[],
            recommended_action="Allow deployment",
            context={"file": "test.py"},
            detected_at=datetime.utcnow(),
        )

        violation2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            clause="Test",
            rule="Test rule 2",
            description="Violation 2",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Block deployment",
            context={"file": "test.py"},
            detected_at=datetime.utcnow(),
        )

        coordinator.all_violations = [violation1, violation2]

        await coordinator._resolve_conflicts()

        # Conflict should be detected and resolved
        assert len(coordinator.conflict_resolutions) > 0

    def test_is_conflicting_opposite_actions(self, coordinator):
        """Test detecting conflicting actions."""
        v1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Allow deployment",
        )

        v2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Block deployment",
        )

        is_conflict = coordinator._is_conflicting(v1, v2)

        assert is_conflict is True

    def test_is_conflicting_same_action(self, coordinator):
        """Test non-conflicting same actions."""
        v1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Fix code",
        )

        v2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Fix code",
        )

        is_conflict = coordinator._is_conflicting(v1, v2)

        assert is_conflict is False

    def test_article_precedence_article_v_highest(self, coordinator):
        """Test Article V has highest precedence."""
        precedence_v = coordinator._get_article_precedence("ARTICLE_V")
        precedence_ii = coordinator._get_article_precedence("ARTICLE_II")
        precedence_iii = coordinator._get_article_precedence("ARTICLE_III")
        precedence_iv = coordinator._get_article_precedence("ARTICLE_IV")

        assert precedence_v < precedence_ii
        assert precedence_v < precedence_iii
        assert precedence_v < precedence_iv

    def test_severity_priority_critical_highest(self, coordinator):
        """Test CRITICAL severity has highest priority."""
        priority_critical = coordinator._get_severity_priority(GuardianPriority.CRITICAL)
        priority_high = coordinator._get_severity_priority(GuardianPriority.HIGH)
        priority_medium = coordinator._get_severity_priority(GuardianPriority.MEDIUM)
        priority_low = coordinator._get_severity_priority(GuardianPriority.LOW)

        assert priority_critical < priority_high
        assert priority_high < priority_medium
        assert priority_medium < priority_low


# ============================================================================
# PATTERN DETECTION TESTS
# ============================================================================


class TestPatternDetection:
    """Test violation pattern detection."""

    @pytest.mark.asyncio
    async def test_analyze_violation_patterns_insufficient_data(self, coordinator):
        """Test pattern analysis with insufficient data."""
        # Only 5 violations (need 10 minimum)
        for i in range(5):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_II,
                clause="Test",
                rule="Test rule",
                description=f"Violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=[],
                recommended_action="Fix",
            )
            coordinator.all_violations.append(violation)

        # Should not raise error
        await coordinator._analyze_violation_patterns()

    @pytest.mark.asyncio
    async def test_detect_hot_spots(self, coordinator):
        """Test detection of violation hot spots."""
        # Mock _handle_violation to prevent infinite loop
        original_handle = coordinator._handle_violation
        coordinator._handle_violation = AsyncMock()

        # Create 15 violations with same rule (hot spot)
        for i in range(15):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_II,
                clause="Test",
                rule="REPEATED_RULE",
                description=f"Violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=["test_system"],
                recommended_action="Fix",
                detected_at=datetime.utcnow(),
            )
            coordinator.all_violations.append(violation)

        await coordinator._analyze_violation_patterns()

        # Pattern violation should be created
        coordinator._handle_violation.assert_called_once()

    @pytest.mark.asyncio
    async def test_pattern_violation_creation(self, coordinator):
        """Test pattern violation is created correctly."""
        original_handle = coordinator._handle_violation
        coordinator._handle_violation = AsyncMock()

        # Create violations with repeated system
        for i in range(15):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_II,
                clause="Test",
                rule="Test rule",
                description=f"Violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=["repeated_system"],
                recommended_action="Fix",
                detected_at=datetime.utcnow(),
            )
            coordinator.all_violations.append(violation)

        await coordinator._analyze_violation_patterns()

        # Verify pattern violation was created
        coordinator._handle_violation.assert_called_once()
        pattern_violation = coordinator._handle_violation.call_args[0][0]
        assert "Pattern detected" in pattern_violation.description


# ============================================================================
# THRESHOLD CHECKING TESTS
# ============================================================================


class TestThresholds:
    """Test critical threshold checking."""

    @pytest.mark.asyncio
    async def test_check_critical_compliance_threshold(self, coordinator):
        """Test critical alert when compliance drops below threshold."""
        # Set compliance score below 80%
        coordinator.metrics.compliance_score = 75.0

        # Add a violation to avoid index error
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Fix",
        )
        coordinator.all_violations.append(violation)

        # Mock alert
        coordinator._send_critical_alert = AsyncMock()

        await coordinator._check_critical_thresholds()

        # Verify alert was sent
        coordinator._send_critical_alert.assert_called()

    @pytest.mark.asyncio
    async def test_check_veto_rate_threshold(self, coordinator):
        """Test critical alert when veto rate is too high."""
        # Create 6 recent vetos (threshold is 5)
        for i in range(6):
            veto = VetoAction(
                guardian_id=f"guardian-{i}",
                target_operation=f"op-{i}",
                reason="Test",
                violation=None,
            )
            coordinator.all_vetos.append(veto)

        # Add a violation to avoid index error
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            evidence=[],
            affected_systems=[],
            recommended_action="Fix",
        )
        coordinator.all_violations.append(violation)

        # Mock alert
        coordinator._send_critical_alert = AsyncMock()

        await coordinator._check_critical_thresholds()

        # Verify alert was sent
        coordinator._send_critical_alert.assert_called()

    @pytest.mark.asyncio
    async def test_send_critical_alert_writes_file(self, coordinator, sample_violation):
        """Test critical alert writes to file."""
        # Cleanup any existing file
        alert_file = Path("/tmp/guardian_critical_alerts.json")
        if alert_file.exists():
            alert_file.unlink()

        await coordinator._send_critical_alert(sample_violation)

        # Verify file was created
        assert alert_file.exists()

        # Verify contents
        alerts = json.loads(alert_file.read_text())
        assert len(alerts) >= 1
        assert alerts[-1]["severity"] == "CRITICAL"

        # Cleanup
        alert_file.unlink()


# ============================================================================
# METRICS TESTS
# ============================================================================


class TestMetrics:
    """Test metrics calculation and updates."""

    def test_update_metrics_compliance_score(self, coordinator):
        """Test compliance score calculation."""
        coordinator.metrics.total_violations_detected = 50

        coordinator._update_metrics()

        # (1000 + 50 - 50) / (1000 + 50) = 95.24%
        assert 95.0 <= coordinator.metrics.compliance_score <= 96.0

    def test_metrics_to_dict(self, coordinator):
        """Test metrics serialization."""
        coordinator.metrics.total_violations_detected = 10
        coordinator.metrics.interventions_made = 5
        coordinator.metrics.vetos_enacted = 2

        metrics_dict = coordinator.metrics.to_dict()

        assert metrics_dict["total_violations_detected"] == 10
        assert metrics_dict["interventions_made"] == 5
        assert metrics_dict["vetos_enacted"] == 2
        assert "compliance_score" in metrics_dict
        assert "last_updated" in metrics_dict


# ============================================================================
# REPORTING TESTS
# ============================================================================


class TestReporting:
    """Test compliance reporting."""

    @pytest.mark.asyncio
    async def test_get_status(self, coordinator):
        """Test get_status returns complete status."""
        await coordinator.start()

        status = coordinator.get_status()

        assert status["coordinator_id"] == coordinator.coordinator_id
        assert status["is_active"] is True
        assert "guardians" in status
        assert "metrics" in status
        assert "active_vetos" in status
        assert "recent_violations" in status

        await coordinator.stop()

    def test_generate_compliance_report(self, coordinator):
        """Test compliance report generation."""
        # Add some test data
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test rule",
            description="Test violation",
            severity=GuardianPriority.HIGH,
            evidence=["Evidence"],
            affected_systems=["test_system"],
            recommended_action="Fix",
            detected_at=datetime.utcnow(),
        )
        coordinator.all_violations.append(violation)

        report = coordinator.generate_compliance_report(period_hours=24)

        assert "report_id" in report
        assert "period_start" in report
        assert "period_end" in report
        assert "coordinator_metrics" in report
        assert "guardian_reports" in report
        assert "summary" in report
        assert "top_violations" in report
        assert "recommendations" in report

    def test_get_top_violations(self, coordinator):
        """Test getting top violations by frequency."""
        # Create violations with repeated rules
        for i in range(5):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_II,
                clause="Test",
                rule="COMMON_RULE",
                description=f"Violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=[],
                recommended_action="Fix",
            )
            coordinator.all_violations.append(violation)

        for i in range(3):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_III,
                clause="Test",
                rule="LESS_COMMON_RULE",
                description=f"Violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=[],
                recommended_action="Fix",
            )
            coordinator.all_violations.append(violation)

        top_violations = coordinator._get_top_violations(coordinator.all_violations)

        assert len(top_violations) > 0
        # Most common should be first
        assert top_violations[0]["count"] >= top_violations[-1]["count"]

    def test_generate_recommendations_quality_issues(self, coordinator):
        """Test recommendations for quality violations."""
        # Create 15 Article II violations
        for i in range(15):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_II,
                clause="Test",
                rule="Quality rule",
                description=f"Quality violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=[],
                recommended_action="Fix",
            )
            coordinator.all_violations.append(violation)

        recommendations = coordinator._generate_recommendations(
            coordinator.all_violations
        )

        assert any("quality" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_security_issues(self, coordinator):
        """Test recommendations for security violations."""
        # Create 10 Article III violations
        for i in range(10):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_III,
                clause="Test",
                rule="Security rule",
                description=f"Security violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=[],
                recommended_action="Fix",
            )
            coordinator.all_violations.append(violation)

        recommendations = coordinator._generate_recommendations(
            coordinator.all_violations
        )

        assert any("zero trust" in rec.lower() or "security" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_resilience_issues(self, coordinator):
        """Test recommendations for resilience violations."""
        # Create 10 Article IV violations
        for i in range(10):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_IV,
                clause="Test",
                rule="Resilience rule",
                description=f"Resilience violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=[],
                recommended_action="Fix",
            )
            coordinator.all_violations.append(violation)

        recommendations = coordinator._generate_recommendations(
            coordinator.all_violations
        )

        assert any("antifragility" in rec.lower() or "resilience" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_governance_issues(self, coordinator):
        """Test recommendations for governance violations."""
        # Create 5 Article V violations
        for i in range(5):
            violation = ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_V,
                clause="Test",
                rule="Governance rule",
                description=f"Governance violation {i}",
                severity=GuardianPriority.MEDIUM,
                evidence=[],
                affected_systems=[],
                recommended_action="Fix",
            )
            coordinator.all_violations.append(violation)

        recommendations = coordinator._generate_recommendations(
            coordinator.all_violations
        )

        assert any("governance" in rec.lower() or "prior legislation" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_all_compliant(self, coordinator):
        """Test recommendations when system is compliant."""
        # No violations
        coordinator.all_violations = []

        recommendations = coordinator._generate_recommendations([])

        assert any("compliant" in rec.lower() for rec in recommendations)


# ============================================================================
# VETO OVERRIDE TESTS
# ============================================================================


class TestVetoOverride:
    """Test veto override functionality."""

    @pytest.mark.asyncio
    async def test_override_veto_success(self, coordinator, sample_veto):
        """Test successful veto override."""
        coordinator.all_vetos.append(sample_veto)

        result = await coordinator.override_veto(
            veto_id=sample_veto.veto_id,
            override_reason="Emergency deployment required",
            approver_id="cto@vertice.ai",
        )

        assert result is True
        assert sample_veto.metadata["overridden"] is True
        assert sample_veto.metadata["override_reason"] == "Emergency deployment required"
        assert sample_veto.metadata["override_approver"] == "cto@vertice.ai"

    @pytest.mark.asyncio
    async def test_override_veto_not_found(self, coordinator):
        """Test override of non-existent veto."""
        result = await coordinator.override_veto(
            veto_id="non-existent-veto",
            override_reason="Test",
            approver_id="test@test.com",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_override_veto_not_allowed(self, coordinator):
        """Test override of non-overridable veto."""
        veto = VetoAction(
            guardian_id="guardian-critical",
            target_operation="critical_operation",
            reason="Critical safety violation",
            violation=None,
            override_allowed=False,  # Cannot be overridden
        )
        coordinator.all_vetos.append(veto)

        result = await coordinator.override_veto(
            veto_id=veto.veto_id,
            override_reason="Emergency",
            approver_id="ceo@vertice.ai",
        )

        assert result is False


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
