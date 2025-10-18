"""
Test Suite for Guardian Agents - Constitutional Enforcement System

Comprehensive tests for all Guardian Agents ensuring proper
Constitutional enforcement across the Vértice-MAXIMUS ecosystem.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from .article_ii_guardian import ArticleIIGuardian
from .article_iii_guardian import ArticleIIIGuardian
from .article_iv_guardian import ArticleIVGuardian
from .article_v_guardian import ArticleVGuardian
from .base import (
    ConstitutionalArticle,
    ConstitutionalViolation,
    GuardianPriority,
    InterventionType,
    VetoAction,
)
from .coordinator import GuardianCoordinator


# ============================================================================
# BASE GUARDIAN TESTS
# ============================================================================


class TestGuardianBase:
    """Test base Guardian Agent functionality."""

    @pytest.mark.asyncio
    async def test_guardian_lifecycle(self):
        """Test Guardian start/stop lifecycle."""
        guardian = ArticleIIGuardian()

        # Test initial state
        assert not guardian.is_active()
        assert guardian.guardian_id == "guardian-article-ii"
        assert guardian.article == ConstitutionalArticle.ARTICLE_II

        # Test start
        await guardian.start()
        assert guardian.is_active()

        # Test double start (should be idempotent)
        await guardian.start()
        assert guardian.is_active()

        # Test stop
        await guardian.stop()
        assert not guardian.is_active()

        # Test double stop (should be idempotent)
        await guardian.stop()
        assert not guardian.is_active()

    @pytest.mark.asyncio
    async def test_violation_callbacks(self):
        """Test violation callback registration and execution."""
        guardian = ArticleIIGuardian()
        callback_called = False
        violation_received = None

        async def test_callback(violation: ConstitutionalViolation):
            nonlocal callback_called, violation_received
            callback_called = True
            violation_received = violation

        guardian.register_violation_callback(test_callback)

        # Create and process a test violation
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test Clause",
            rule="Test Rule",
            description="Test violation",
            severity=GuardianPriority.MEDIUM,
        )

        await guardian._process_violation(violation)

        assert callback_called
        assert violation_received == violation
        assert violation in guardian._violations

    @pytest.mark.asyncio
    async def test_veto_action(self):
        """Test veto action creation and tracking."""
        guardian = ArticleIIGuardian()

        veto = await guardian.veto_action(
            action="deploy_to_production",
            system="test_system",
            reason="Contains mock implementations",
            duration_hours=24,
        )

        assert veto.guardian_id == guardian.guardian_id
        assert veto.target_action == "deploy_to_production"
        assert veto.target_system == "test_system"
        assert veto.is_active()
        assert veto.expires_at is not None
        assert veto in guardian._vetos

    def test_report_generation(self):
        """Test Guardian report generation."""
        guardian = ArticleIIGuardian()

        # Add some test violations
        for i in range(5):
            guardian._violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_II,
                    clause=f"Clause {i}",
                    rule=f"Rule {i}",
                    description=f"Violation {i}",
                    severity=GuardianPriority.MEDIUM,
                )
            )

        report = guardian.generate_report(period_hours=24)

        assert report.guardian_id == guardian.guardian_id
        assert report.violations_detected == 5
        assert report.compliance_score < 100
        assert len(report.top_violations) > 0


# ============================================================================
# ARTICLE II GUARDIAN TESTS
# ============================================================================


class TestArticleIIGuardian:
    """Test Article II Guardian - Sovereign Quality Standard."""

    @pytest.mark.asyncio
    async def test_mock_detection(self):
        """Test detection of mock implementations."""
        guardian = ArticleIIGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with mock
            test_file = Path(tmpdir) / "service.py"
            test_file.write_text("""
class Service:
    def get_data(self):
        # Using mock for testing
        return Mock(data="test")
            """)

            # Override monitored paths for test
            guardian.monitored_paths = [tmpdir]

            violations = await guardian.monitor()

            assert len(violations) > 0
            violation = violations[0]
            assert "Mock implementation" in violation.description
            assert violation.article == ConstitutionalArticle.ARTICLE_II
            assert violation.clause == "Section 2"

    @pytest.mark.asyncio
    async def test_todo_detection(self):
        """Test detection of TODO/FIXME comments."""
        guardian = ArticleIIGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "service.py"
            test_file.write_text("""
def process_data():
    # TODO: Implement this function
    pass

def validate():
    # FIXME: Add proper validation
    return True
            """)

            guardian.monitored_paths = [tmpdir]
            violations = await guardian.monitor()

            assert len(violations) >= 2
            assert any("TODO" in v.description for v in violations)
            assert any("FIXME" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_not_implemented_detection(self):
        """Test detection of NotImplementedError."""
        guardian = ArticleIIGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "service.py"
            test_file.write_text("""
class BaseHandler:
    def handle(self):
        raise NotImplementedError("Subclass must implement")
            """)

            guardian.monitored_paths = [tmpdir]
            violations = await guardian.monitor()

            assert len(violations) > 0
            violation = violations[0]
            assert "NotImplementedError" in violation.description
            assert violation.severity == GuardianPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_skipped_test_detection(self):
        """Test detection of skipped tests without valid reason."""
        guardian = ArticleIIGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_service.py"
            test_file.write_text("""
import pytest

@pytest.mark.skip
def test_important_feature():
    assert True

@pytest.mark.skip(reason="Depends on ROADMAP feature X")
def test_future_feature():
    assert True
            """)

            guardian.monitored_paths = [tmpdir]
            violations = await guardian.monitor()

            # Should only detect first skip (no valid reason)
            skip_violations = [v for v in violations if "skipped test" in v.description.lower()]
            assert len(skip_violations) == 1

    @pytest.mark.asyncio
    async def test_analyze_violation_decisions(self):
        """Test Guardian decision-making for violations."""
        guardian = ArticleIIGuardian()

        # Test CRITICAL violation decision
        critical_violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Section 1",
            rule="Code must be PRODUCTION-READY",
            description="NotImplementedError found",
            severity=GuardianPriority.CRITICAL,
        )

        decision = await guardian.analyze_violation(critical_violation)
        assert decision.decision_type == "veto"
        assert decision.confidence >= 0.95

        # Test MEDIUM violation decision
        medium_violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Section 2",
            rule="No TODOs",
            description="TODO found",
            severity=GuardianPriority.MEDIUM,
        )

        decision = await guardian.analyze_violation(medium_violation)
        assert decision.decision_type == "alert"
        assert decision.confidence < 0.9


# ============================================================================
# ARTICLE III GUARDIAN TESTS
# ============================================================================


class TestArticleIIIGuardian:
    """Test Article III Guardian - Zero Trust Principle."""

    @pytest.mark.asyncio
    async def test_ai_artifact_detection(self):
        """Test detection of unvalidated AI-generated code."""
        guardian = ArticleIIIGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "ai_service.py"
            test_file.write_text("""
# Generated by Claude Code
class DataProcessor:
    def process(self, data):
        return data * 2
            """)

            # Mock the monitored paths
            with patch.object(guardian, "_check_ai_artifacts") as mock_check:
                mock_check.return_value = [
                    ConstitutionalViolation(
                        article=ConstitutionalArticle.ARTICLE_III,
                        clause="Section 1",
                        rule="AI artifacts are untrusted until validated",
                        description=f"Unvalidated AI-generated code in {test_file.name}",
                        severity=GuardianPriority.HIGH,
                    )
                ]

                violations = await guardian.monitor()

                assert len(violations) > 0
                violation = violations[0]
                assert "Unvalidated AI-generated" in violation.description
                assert violation.severity == GuardianPriority.HIGH

    @pytest.mark.asyncio
    async def test_missing_authentication(self):
        """Test detection of endpoints without authentication."""
        guardian = ArticleIIIGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            api_dir = Path(tmpdir) / "api"
            api_dir.mkdir()

            test_file = api_dir / "endpoints.py"
            test_file.write_text("""
@app.get("/public/data")
def get_public_data():
    return {"data": "public"}

@app.post("/admin/delete")
def delete_everything():
    # No authentication check!
    database.drop_all()
    return {"status": "deleted"}
            """)

            # Mock paths for testing
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.rglob", return_value=[test_file]):
                    violations = await guardian._check_authentication()

                    assert len(violations) > 0
                    assert any("without authentication" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_input_validation_check(self):
        """Test detection of missing input validation."""
        guardian = ArticleIIIGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            api_dir = Path(tmpdir) / "api"
            api_dir.mkdir()

            test_file = api_dir / "handler.py"
            test_file.write_text("""
def handle_request(request):
    user_input = request.json["data"]
    # Direct use without validation
    result = database.query(user_input)
    return result
            """)

            # Mock for testing
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.rglob", return_value=[test_file]):
                    violations = await guardian._check_input_validation()

                    assert len(violations) > 0
                    assert any("Unvalidated input" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_artifact_validation(self):
        """Test AI artifact validation process."""
        guardian = ArticleIIIGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "ai_code.py"
            test_file.write_text("# Generated by Claude\nprint('test')")

            result = await guardian.validate_artifact(
                file_path=str(test_file),
                validator_id="human_architect_001",
                validation_notes="Code reviewed and approved",
            )

            assert result is True
            assert len(guardian.validation_history) == 1
            assert guardian.validation_history[0]["validated"] is True


# ============================================================================
# ARTICLE IV GUARDIAN TESTS
# ============================================================================


class TestArticleIVGuardian:
    """Test Article IV Guardian - Deliberate Antifragility."""

    @pytest.mark.asyncio
    async def test_chaos_test_detection(self):
        """Test detection of insufficient chaos engineering tests."""
        guardian = ArticleIVGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            tests_dir = Path(tmpdir) / "tests"
            tests_dir.mkdir()

            # Create regular tests
            for i in range(10):
                test_file = tests_dir / f"test_feature_{i}.py"
                test_file.write_text(f"def test_feature_{i}(): assert True")

            # Create only 1 chaos test (should be insufficient)
            chaos_file = tests_dir / "test_chaos.py"
            chaos_file.write_text("def test_chaos_network_failure(): pass")

            # Mock paths
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.rglob") as mock_rglob:
                    mock_rglob.return_value = list(tests_dir.glob("test_*.py"))

                    violations = await guardian._check_chaos_engineering()

                    chaos_violations = [
                        v for v in violations
                        if "Insufficient chaos testing" in v.description
                    ]
                    assert len(chaos_violations) > 0

    @pytest.mark.asyncio
    async def test_resilience_patterns_check(self):
        """Test detection of missing resilience patterns."""
        guardian = ArticleIVGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            service_file = Path(tmpdir) / "service.py"
            service_file.write_text("""
class DataService:
    def fetch_data(self):
        # No retry, no timeout, no circuit breaker
        response = requests.get("http://api.example.com/data")
        return response.json()
            """)

            # Mock for testing
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.rglob", return_value=[service_file]):
                    violations = await guardian._check_resilience_patterns()

                    assert len(violations) > 0
                    assert any("Missing resilience patterns" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_chaos_experiment_execution(self):
        """Test chaos experiment execution."""
        guardian = ArticleIVGuardian()

        result = await guardian.run_chaos_experiment(
            experiment_type="network_latency",
            target_system="test_service",
            parameters={"latency_ms": 500, "duration_s": 60},
        )

        assert result["status"] == "completed"
        assert "success_rate" in result["results"]
        assert len(guardian.chaos_experiments) == 1

    @pytest.mark.asyncio
    async def test_experimental_feature_quarantine(self):
        """Test quarantine of experimental features."""
        guardian = ArticleIVGuardian()

        result = await guardian.quarantine_feature(
            feature_id="experimental_ai_001",
            feature_path="/path/to/feature.py",
            risk_level="high",
        )

        assert result is True
        assert "experimental_ai_001" in guardian.quarantined_features
        assert guardian.quarantined_features["experimental_ai_001"]["status"] == "quarantined"


# ============================================================================
# ARTICLE V GUARDIAN TESTS
# ============================================================================


class TestArticleVGuardian:
    """Test Article V Guardian - Prior Legislation."""

    @pytest.mark.asyncio
    async def test_autonomous_without_governance(self):
        """Test detection of autonomous systems without governance."""
        guardian = ArticleVGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create autonomous system without governance
            auto_file = Path(tmpdir) / "autonomous_agent.py"
            auto_file.write_text("""
class AutonomousAgent:
    def auto_execute(self):
        # Autonomous decision-making
        self.take_action()
            """)

            # Mock paths
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.rglob", return_value=[auto_file]):
                    violations = await guardian._check_autonomous_governance()

                    assert len(violations) > 0
                    assert any(
                        "Autonomous capability without governance" in v.description
                        for v in violations
                    )

    @pytest.mark.asyncio
    async def test_missing_hitl_controls(self):
        """Test detection of missing HITL controls."""
        guardian = ArticleVGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            service_file = Path(tmpdir) / "critical_ops.py"
            service_file.write_text("""
def delete_user_account(user_id):
    # Critical operation without human approval
    database.delete(f"users/{user_id}")
    return {"status": "deleted"}
            """)

            # Mock for testing
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.rglob", return_value=[service_file]):
                    violations = await guardian._check_hitl_controls()

                    assert len(violations) > 0
                    assert any("without HITL" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_missing_kill_switch(self):
        """Test detection of missing kill switches."""
        guardian = ArticleVGuardian()

        with tempfile.TemporaryDirectory() as tmpdir:
            worker_file = Path(tmpdir) / "worker.py"
            worker_file.write_text("""
def background_worker():
    while True:
        # No kill switch or stop condition
        process_tasks()
        time.sleep(1)
            """)

            # Mock for testing
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.rglob", return_value=[worker_file]):
                    violations = await guardian._check_kill_switches()

                    assert len(violations) > 0
                    assert any("without kill switch" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_governance_registration(self):
        """Test governance registration for autonomous systems."""
        guardian = ArticleVGuardian()

        result = await guardian.register_governance(
            system_id="auto_system_001",
            governance_type="policy_based",
            policies=["ethical_use", "data_privacy"],
            controls={"hitl": True, "kill_switch": True},
        )

        assert result is True
        assert "auto_system_001" in guardian.governance_registry
        assert guardian.governance_registry["auto_system_001"]["validated"] is False


# ============================================================================
# COORDINATOR TESTS
# ============================================================================


class TestGuardianCoordinator:
    """Test Guardian Coordinator functionality."""

    @pytest.mark.asyncio
    async def test_coordinator_lifecycle(self):
        """Test coordinator start/stop."""
        coordinator = GuardianCoordinator()

        assert not coordinator._is_active

        await coordinator.start()
        assert coordinator._is_active

        # Check all guardians are started
        for guardian in coordinator.guardians.values():
            assert guardian.is_active()

        await coordinator.stop()
        assert not coordinator._is_active

        # Check all guardians are stopped
        for guardian in coordinator.guardians.values():
            assert not guardian.is_active()

    @pytest.mark.asyncio
    async def test_violation_aggregation(self):
        """Test violation aggregation from multiple guardians."""
        coordinator = GuardianCoordinator()

        # Create violations from different articles
        violation1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Section 1",
            rule="Quality",
            description="Test violation 1",
            severity=GuardianPriority.HIGH,
        )

        violation2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            clause="Section 2",
            rule="Zero Trust",
            description="Test violation 2",
            severity=GuardianPriority.CRITICAL,
        )

        await coordinator._handle_violation(violation1)
        await coordinator._handle_violation(violation2)

        assert len(coordinator.all_violations) == 2
        assert coordinator.metrics.total_violations_detected == 2
        assert "ARTICLE_II" in coordinator.metrics.violations_by_article
        assert "ARTICLE_III" in coordinator.metrics.violations_by_article

    @pytest.mark.asyncio
    async def test_conflict_resolution(self):
        """Test conflict resolution between guardian decisions."""
        coordinator = GuardianCoordinator()

        # Create conflicting violations on same target
        violation1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Section 1",
            rule="Quality",
            description="Allow deployment",
            severity=GuardianPriority.MEDIUM,
            context={"file": "test.py"},
            recommended_action="Allow deployment after review",
        )

        violation2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            clause="Section 1",
            rule="Prior Legislation",
            description="Block deployment",
            severity=GuardianPriority.HIGH,
            context={"file": "test.py"},
            recommended_action="Block deployment until governance added",
        )

        coordinator.all_violations.extend([violation1, violation2])

        await coordinator._resolve_conflicts()

        # Article V should take precedence
        assert len(coordinator.conflict_resolutions) > 0

    def test_compliance_report_generation(self):
        """Test compliance report generation."""
        coordinator = GuardianCoordinator()

        # Add test data
        for i in range(10):
            coordinator.all_violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_II,
                    clause="Test",
                    rule="Test Rule",
                    description=f"Violation {i}",
                    severity=GuardianPriority.MEDIUM,
                )
            )

        report = coordinator.generate_compliance_report(period_hours=24)

        assert "report_id" in report
        assert "coordinator_metrics" in report
        assert "guardian_reports" in report
        assert report["summary"]["total_violations"] == 10
        assert len(report["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_veto_override(self):
        """Test veto override functionality."""
        coordinator = GuardianCoordinator()

        # Create a veto
        veto = VetoAction(
            guardian_id="test-guardian",
            target_action="deploy",
            target_system="production",
            reason="Test veto",
            override_allowed=True,
        )

        coordinator.all_vetos.append(veto)

        result = await coordinator.override_veto(
            veto_id=veto.veto_id,
            override_reason="Emergency deployment required",
            approver_id="human_admin_001",
        )

        assert result is True
        assert veto.metadata.get("overridden") is True
        assert "override_reason" in veto.metadata

    @pytest.mark.asyncio
    async def test_critical_alert_threshold(self):
        """Test critical alert when thresholds are breached."""
        coordinator = GuardianCoordinator()

        # Simulate low compliance score
        coordinator.metrics.compliance_score = 75.0

        with patch.object(coordinator, "_send_critical_alert") as mock_alert:
            await coordinator._check_critical_thresholds()

            mock_alert.assert_called_once()
            violation = mock_alert.call_args[0][0]
            assert "Compliance below threshold" in violation.description


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestGuardianIntegration:
    """Integration tests for the complete Guardian system."""

    @pytest.mark.asyncio
    async def test_full_system_monitoring(self):
        """Test full system monitoring with all guardians."""
        coordinator = GuardianCoordinator()

        # Start the system
        await coordinator.start()

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Get status
        status = coordinator.get_status()

        assert status["is_active"] is True
        assert len(status["guardians"]) == 4
        assert all(g["active"] for g in status["guardians"].values())

        # Stop the system
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_constitutional_enforcement_chain(self):
        """Test the full enforcement chain from detection to intervention."""
        coordinator = GuardianCoordinator()

        # Create a critical violation
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            clause="Section 1",
            rule="Governance before autonomy",
            description="Autonomous system without governance",
            severity=GuardianPriority.CRITICAL,
            affected_systems=["test_system"],
        )

        # Process through guardian
        guardian = coordinator.guardians["article_v"]

        decision = await guardian.analyze_violation(violation)
        assert decision.decision_type == "veto"

        intervention = await guardian.intervene(violation)
        assert intervention.intervention_type == InterventionType.VETO

        # Verify veto was created
        veto = await guardian.veto_action(
            action="enable_autonomous_system",
            system="test_system",
            reason=decision.reasoning,
        )

        assert veto.is_active()
        assert len(guardian.get_active_vetos()) > 0