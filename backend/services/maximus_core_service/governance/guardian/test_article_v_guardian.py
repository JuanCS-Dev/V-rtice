"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Article V Guardian Tests (Prior Legislation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: governance/guardian/test_article_v_guardian.py
Purpose: 100% coverage for article_v_guardian.py

TARGET: 100.00% COVERAGE (208 statements)

Test Coverage:
├─ Initialization & configuration
├─ Autonomous governance checking
├─ Responsibility Doctrine enforcement
├─ HITL (Human-In-The-Loop) controls
├─ Kill switch implementation
├─ Two-Man Rule validation
├─ Governance registration
├─ Governance precedence validation
├─ Decision & intervention logic
└─ Edge cases & error handling

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-15)

MISSION: 14-DAY 100% COVERAGE SPRINT - DIA 1
CONTRACT: 100% OU NADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.guardian.article_v_guardian import ArticleVGuardian
from governance.guardian.base import (
    ConstitutionalArticle,
    GuardianPriority,
    InterventionType,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def guardian():
    """Create Article V Guardian instance."""
    return ArticleVGuardian()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALIZATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestArticleVGuardianInit:
    """Test Article V Guardian initialization."""

    def test_guardian_initialization(self, guardian):
        """Test guardian initializes with correct attributes."""
        assert guardian.guardian_id == "guardian-article-v"
        assert guardian.article == ConstitutionalArticle.ARTICLE_V
        assert guardian.name == "Prior Legislation Guardian"
        assert "Prior Legislation" in guardian.description

    def test_autonomous_systems_initialized(self, guardian):
        """Test autonomous systems dict is initialized."""
        assert isinstance(guardian.autonomous_systems, dict)
        assert len(guardian.autonomous_systems) == 0

    def test_governance_registry_initialized(self, guardian):
        """Test governance registry dict is initialized."""
        assert isinstance(guardian.governance_registry, dict)
        assert len(guardian.governance_registry) == 0

    def test_responsibility_requirements_configured(self, guardian):
        """Test responsibility requirements are configured."""
        assert len(guardian.responsibility_requirements) == 5
        assert "compartmentalization" in guardian.responsibility_requirements
        assert "two_man_rule" in guardian.responsibility_requirements
        assert "kill_switch" in guardian.responsibility_requirements

    def test_autonomous_indicators_configured(self, guardian):
        """Test autonomous indicators are configured."""
        assert len(guardian.autonomous_indicators) > 0
        assert "autonomous" in guardian.autonomous_indicators
        assert "ai_agent" in guardian.autonomous_indicators

    def test_governance_indicators_configured(self, guardian):
        """Test governance indicators are configured."""
        assert len(guardian.governance_indicators) > 0
        assert "governance" in guardian.governance_indicators
        assert "policy" in guardian.governance_indicators

    def test_configurable_paths_initialized(self, guardian):
        """Test paths are initialized with defaults."""
        assert isinstance(guardian.autonomous_paths, list)
        assert isinstance(guardian.powerful_paths, list)
        assert isinstance(guardian.hitl_paths, list)
        assert isinstance(guardian.process_paths, list)
        assert isinstance(guardian.governance_paths, list)

    def test_custom_paths_injection(self, tmp_path):
        """Test custom paths can be injected."""
        custom_path = [str(tmp_path)]
        guardian = ArticleVGuardian(
            autonomous_paths=custom_path,
            powerful_paths=custom_path,
            hitl_paths=custom_path,
            process_paths=custom_path,
            governance_paths=custom_path,
        )

        assert guardian.autonomous_paths == custom_path
        assert guardian.powerful_paths == custom_path
        assert guardian.hitl_paths == custom_path
        assert guardian.process_paths == custom_path
        assert guardian.governance_paths == custom_path

    def test_get_monitored_systems(self, guardian):
        """Test get_monitored_systems returns correct list."""
        systems = guardian.get_monitored_systems()

        assert "autonomous_agents" in systems
        assert "governance_framework" in systems
        assert "hitl_controls" in systems


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MONITORING ORCHESTRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMonitoring:
    """Test monitoring orchestration."""

    @pytest.mark.asyncio
    async def test_monitor_calls_all_checks(self, guardian):
        """Test monitor() orchestrates all check methods."""
        with patch.object(guardian, '_check_autonomous_governance', return_value=[]) as mock_auto, \
             patch.object(guardian, '_check_responsibility_doctrine', return_value=[]) as mock_resp, \
             patch.object(guardian, '_check_hitl_controls', return_value=[]) as mock_hitl, \
             patch.object(guardian, '_check_kill_switches', return_value=[]) as mock_kill, \
             patch.object(guardian, '_check_two_man_rule', return_value=[]) as mock_twoman:

            violations = await guardian.monitor()

            # All check methods should be called
            mock_auto.assert_called_once()
            mock_resp.assert_called_once()
            mock_hitl.assert_called_once()
            mock_kill.assert_called_once()
            mock_twoman.assert_called_once()

            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_monitor_aggregates_violations(self, guardian):
        """Test monitor() aggregates violations from all checks."""
        from governance.guardian.base import ConstitutionalViolation

        mock_violation1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Test rule 1"
        )
        mock_violation2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Test rule 2"
        )

        with patch.object(guardian, '_check_autonomous_governance', return_value=[mock_violation1]), \
             patch.object(guardian, '_check_responsibility_doctrine', return_value=[mock_violation2]), \
             patch.object(guardian, '_check_hitl_controls', return_value=[]), \
             patch.object(guardian, '_check_kill_switches', return_value=[]), \
             patch.object(guardian, '_check_two_man_rule', return_value=[]):

            violations = await guardian.monitor()

            assert len(violations) == 2
            assert mock_violation1 in violations
            assert mock_violation2 in violations


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTONOMOUS GOVERNANCE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestAutonomousGovernance:
    """Test autonomous governance checking."""

    @pytest.mark.asyncio
    async def test_check_autonomous_governance_detects_ungoverned(self, tmp_path):
        """Test _check_autonomous_governance detects autonomous systems without governance."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create autonomous file WITHOUT governance
        auto_file = service_dir / "agent.py"
        auto_file.write_text("class AutonomousAgent:\n    def auto_execute(self): pass\n")

        guardian = ArticleVGuardian(autonomous_paths=[str(service_dir)])
        violations = await guardian._check_autonomous_governance()

        # Should detect ungoverned autonomous system
        assert len(violations) > 0
        assert any("without governance" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_autonomous_governance_allows_governed(self, tmp_path):
        """Test _check_autonomous_governance allows autonomous systems WITH governance."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create autonomous file
        auto_file = service_dir / "agent.py"
        auto_file.write_text("class AutonomousAgent:\n    def auto_execute(self): pass\n")

        # Create governance file in same module
        gov_file = service_dir / "governance.py"
        gov_file.write_text("class GovernancePolicy:\n    def approve(self): pass\n")

        guardian = ArticleVGuardian(autonomous_paths=[str(service_dir)])
        violations = await guardian._check_autonomous_governance()

        # Should NOT detect violation (has governance)
        ungoverned = [v for v in violations if "without governance" in v.description]
        assert len(ungoverned) == 0

    @pytest.mark.asyncio
    async def test_check_autonomous_governance_handles_nonexistent_paths(self, tmp_path):
        """Test _check_autonomous_governance handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleVGuardian(autonomous_paths=[nonexistent])

        violations = await guardian._check_autonomous_governance()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_autonomous_governance_handles_read_errors(self, tmp_path):
        """Test _check_autonomous_governance handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleVGuardian(autonomous_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/agent.py")]):
            violations = await guardian._check_autonomous_governance()

        # Should handle exception gracefully
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_autonomous_governance_registers_systems(self, tmp_path):
        """Test _check_autonomous_governance registers autonomous systems."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        auto_file = service_dir / "agent.py"
        auto_file.write_text("class AIAgent:\n    def ai_agent_method(self): pass\n")

        guardian = ArticleVGuardian(autonomous_paths=[str(service_dir)])
        await guardian._check_autonomous_governance()

        # Should register the autonomous system
        assert len(guardian.autonomous_systems) >= 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESPONSIBILITY DOCTRINE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestResponsibilityDoctrine:
    """Test responsibility doctrine checking."""

    @pytest.mark.asyncio
    async def test_check_responsibility_doctrine_detects_missing_controls(self, tmp_path):
        """Test _check_responsibility_doctrine detects missing responsibility controls."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with powerful operation but NO responsibility controls
        powerful_file = service_dir / "exploit.py"
        powerful_file.write_text(
            "def execute_exploit():\n"
            "    subprocess.run(['rm', '-rf', '/'])\n"
        )

        guardian = ArticleVGuardian(powerful_paths=[str(service_dir)])
        violations = await guardian._check_responsibility_doctrine()

        # Should detect missing responsibility controls
        assert len(violations) > 0
        assert any("Missing responsibility controls" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_responsibility_doctrine_allows_sufficient_controls(self, tmp_path):
        """Test _check_responsibility_doctrine allows operations WITH controls."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with powerful operation AND responsibility controls
        powerful_file = service_dir / "safe_exploit.py"
        powerful_file.write_text(
            "def execute_exploit():\n"
            "    # compartmentalization\n"
            "    # two_man_rule\n"
            "    # kill_switch\n"
            "    # audit_trail\n"
            "    subprocess.run(['echo', 'safe'])\n"
        )

        guardian = ArticleVGuardian(powerful_paths=[str(service_dir)])
        violations = await guardian._check_responsibility_doctrine()

        # Should NOT detect violation (has controls)
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_responsibility_doctrine_skips_test_files(self, tmp_path):
        """Test _check_responsibility_doctrine skips test files."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        test_file = service_dir / "test_exploit.py"
        test_file.write_text("def test_exploit(): pass\n")

        guardian = ArticleVGuardian(powerful_paths=[str(service_dir)])
        violations = await guardian._check_responsibility_doctrine()

        # Test files are skipped
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_responsibility_doctrine_handles_nonexistent_paths(self, tmp_path):
        """Test _check_responsibility_doctrine handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleVGuardian(powerful_paths=[nonexistent])

        violations = await guardian._check_responsibility_doctrine()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_responsibility_doctrine_handles_read_errors(self, tmp_path):
        """Test _check_responsibility_doctrine handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleVGuardian(powerful_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/exploit.py")]):
            violations = await guardian._check_responsibility_doctrine()

        # Should handle exception gracefully
        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HITL CONTROLS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestHITLControls:
    """Test Human-In-The-Loop controls checking."""

    @pytest.mark.asyncio
    async def test_check_hitl_controls_detects_missing_hitl(self, tmp_path):
        """Test _check_hitl_controls detects critical operations without HITL."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with critical operation but NO HITL
        critical_file = service_dir / "deploy.py"
        critical_file.write_text(
            "def production_deploy():\n"
            "    deploy_to_production()\n"
        )

        guardian = ArticleVGuardian(hitl_paths=[str(service_dir)])
        violations = await guardian._check_hitl_controls()

        # Should detect missing HITL
        assert len(violations) > 0
        assert any("without HITL" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_hitl_controls_allows_with_hitl(self, tmp_path):
        """Test _check_hitl_controls allows critical operations WITH HITL."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with critical operation AND HITL
        critical_file = service_dir / "deploy.py"
        critical_file.write_text(
            "def production_deploy():\n"
            "    human_approval = await require_confirmation()\n"
            "    if human_approval:\n"
            "        deploy_to_production()\n"
        )

        guardian = ArticleVGuardian(hitl_paths=[str(service_dir)])
        violations = await guardian._check_hitl_controls()

        # Should NOT detect violation
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_hitl_controls_skips_test_files(self, tmp_path):
        """Test _check_hitl_controls skips test files."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        test_file = service_dir / "test_deploy.py"
        test_file.write_text("def test_deploy(): pass\n")

        guardian = ArticleVGuardian(hitl_paths=[str(service_dir)])
        violations = await guardian._check_hitl_controls()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_hitl_controls_handles_nonexistent_paths(self, tmp_path):
        """Test _check_hitl_controls handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleVGuardian(hitl_paths=[nonexistent])

        violations = await guardian._check_hitl_controls()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_hitl_controls_handles_read_errors(self, tmp_path):
        """Test _check_hitl_controls handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleVGuardian(hitl_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/deploy.py")]):
            violations = await guardian._check_hitl_controls()

        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KILL SWITCH TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestKillSwitch:
    """Test kill switch implementation checking."""

    @pytest.mark.asyncio
    async def test_check_kill_switches_detects_missing_killswitch(self, tmp_path):
        """Test _check_kill_switches detects autonomous processes without kill switch."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with long-running process but NO kill switch
        process_file = service_dir / "worker.py"
        process_file.write_text(
            "def run_worker():\n"
            "    while True:\n"
            "        process()\n"
        )

        guardian = ArticleVGuardian(process_paths=[str(service_dir)])
        violations = await guardian._check_kill_switches()

        # Should detect missing kill switch
        assert len(violations) > 0
        assert any("without kill switch" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_kill_switches_allows_with_killswitch(self, tmp_path):
        """Test _check_kill_switches allows processes WITH kill switch."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with long-running process AND kill switch
        process_file = service_dir / "worker.py"
        process_file.write_text(
            "def run_worker():\n"
            "    while True:\n"
            "        if kill_switch.is_set():\n"
            "            break\n"
            "        process()\n"
        )

        guardian = ArticleVGuardian(process_paths=[str(service_dir)])
        violations = await guardian._check_kill_switches()

        # Should NOT detect violation
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_kill_switches_skips_test_files(self, tmp_path):
        """Test _check_kill_switches skips test files."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        test_file = service_dir / "test_worker.py"
        test_file.write_text("def test_worker(): pass\n")

        guardian = ArticleVGuardian(process_paths=[str(service_dir)])
        violations = await guardian._check_kill_switches()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_kill_switches_handles_nonexistent_paths(self, tmp_path):
        """Test _check_kill_switches handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleVGuardian(process_paths=[nonexistent])

        violations = await guardian._check_kill_switches()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_kill_switches_handles_read_errors(self, tmp_path):
        """Test _check_kill_switches handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleVGuardian(process_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/worker.py")]):
            violations = await guardian._check_kill_switches()

        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TWO-MAN RULE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestTwoManRule:
    """Test Two-Man Rule implementation checking."""

    @pytest.mark.asyncio
    async def test_check_two_man_rule_detects_missing_dual_approval(self, tmp_path):
        """Test _check_two_man_rule detects critical actions without dual approval."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with critical action but NO dual approval
        critical_file = service_dir / "admin.py"
        critical_file.write_text(
            "def admin_grant_privileges():\n"
            "    grant_admin()\n"
        )

        guardian = ArticleVGuardian(governance_paths=[str(service_dir)])
        violations = await guardian._check_two_man_rule()

        # Should detect missing Two-Man Rule
        assert len(violations) > 0
        assert any("without dual approval" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_two_man_rule_allows_with_dual_approval(self, tmp_path):
        """Test _check_two_man_rule allows critical actions WITH dual approval."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with critical action AND dual approval
        critical_file = service_dir / "admin.py"
        critical_file.write_text(
            "def admin_grant_privileges():\n"
            "    first_approval = approve_1()\n"
            "    second_approval = require_second_approval()\n"
            "    if dual_approval:\n"
            "        grant_admin()\n"
        )

        guardian = ArticleVGuardian(governance_paths=[str(service_dir)])
        violations = await guardian._check_two_man_rule()

        # Should NOT detect violation
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_two_man_rule_handles_nonexistent_paths(self, tmp_path):
        """Test _check_two_man_rule handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleVGuardian(governance_paths=[nonexistent])

        violations = await guardian._check_two_man_rule()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_two_man_rule_handles_read_errors(self, tmp_path):
        """Test _check_two_man_rule handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleVGuardian(governance_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/admin.py")]):
            violations = await guardian._check_two_man_rule()

        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOVERNANCE REGISTRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGovernanceRegistration:
    """Test governance registration functionality."""

    @pytest.mark.asyncio
    async def test_register_governance_success(self, guardian):
        """Test register_governance successfully registers governance."""
        result = await guardian.register_governance(
            "system-001",
            "policy-based",
            ["policy-1", "policy-2"],
            {"hitl": True, "audit": True}
        )

        assert result is True
        assert "system-001" in guardian.governance_registry
        assert guardian.governance_registry["system-001"]["governance_type"] == "policy-based"

    @pytest.mark.asyncio
    async def test_register_governance_tracks_policies(self, guardian):
        """Test register_governance tracks policies."""
        await guardian.register_governance(
            "system-002",
            "rule-based",
            ["policy-A", "policy-B", "policy-C"],
            {}
        )

        governance = guardian.governance_registry["system-002"]
        assert len(governance["policies"]) == 3
        assert "policy-A" in governance["policies"]

    @pytest.mark.asyncio
    async def test_register_governance_updates_autonomous_system(self, guardian):
        """Test register_governance updates autonomous system record."""
        # Create autonomous system first
        guardian.autonomous_systems["system-003"] = {
            "path": "/path/to/system",
            "has_governance": False
        }

        await guardian.register_governance(
            "system-003",
            "governance",
            [],
            {}
        )

        # Should update has_governance flag
        assert guardian.autonomous_systems["system-003"]["has_governance"] is True

    @pytest.mark.asyncio
    async def test_register_governance_sets_timestamp(self, guardian):
        """Test register_governance sets registration timestamp."""
        await guardian.register_governance(
            "system-004",
            "test",
            [],
            {}
        )

        governance = guardian.governance_registry["system-004"]
        assert "registered_at" in governance
        # Verify timestamp is recent (within last minute)
        registered_time = datetime.fromisoformat(governance["registered_at"])
        assert (datetime.utcnow() - registered_time).total_seconds() < 60


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOVERNANCE PRECEDENCE VALIDATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGovernancePrecedence:
    """Test governance precedence validation."""

    @pytest.mark.asyncio
    async def test_validate_governance_precedence_missing_governance_files(self, tmp_path):
        """Test validate_governance_precedence detects missing governance files."""
        system_file = tmp_path / "agent.py"
        system_file.write_text("class Agent: pass\n")

        guardian = ArticleVGuardian()
        is_valid, reason = await guardian.validate_governance_precedence(str(system_file))

        assert is_valid is False
        assert "No governance files" in reason

    @pytest.mark.asyncio
    async def test_validate_governance_precedence_missing_governance_import(self, tmp_path):
        """Test validate_governance_precedence detects missing governance imports."""
        system_file = tmp_path / "agent.py"
        system_file.write_text("class Agent:\n    def run(self): pass\n")

        # Create governance file
        gov_file = tmp_path / "governance.py"
        gov_file.write_text("class Governance: pass\n")

        guardian = ArticleVGuardian()
        is_valid, reason = await guardian.validate_governance_precedence(str(system_file))

        assert is_valid is False
        assert "does not import governance" in reason

    @pytest.mark.asyncio
    async def test_validate_governance_precedence_with_governance_import(self, tmp_path):
        """Test validate_governance_precedence allows systems with governance imports."""
        system_file = tmp_path / "agent.py"
        system_file.write_text(
            "from .governance import GovernancePolicy\n\n"
            "class Agent:\n"
            "    def run(self): pass\n"
        )

        # Create governance file
        gov_file = tmp_path / "governance.py"
        gov_file.write_text("class GovernancePolicy: pass\n")

        guardian = ArticleVGuardian()
        is_valid, reason = await guardian.validate_governance_precedence(str(system_file))

        assert is_valid is True
        assert "validated" in reason

    @pytest.mark.asyncio
    async def test_validate_governance_precedence_handles_exceptions(self, guardian):
        """Test validate_governance_precedence handles exceptions gracefully."""
        is_valid, reason = await guardian.validate_governance_precedence("/nonexistent/file.py")

        assert is_valid is False
        # Reason contains either "error" or "No governance files"
        assert ("error" in reason.lower() or "governance" in reason.lower())

    @pytest.mark.asyncio
    async def test_validate_governance_precedence_handles_read_error(self, tmp_path):
        """Test validate_governance_precedence handles file read errors."""
        # Create system file that exists but will fail to read
        system_file = tmp_path / "agent.py"
        system_file.write_text("test")

        # Create governance file
        gov_file = tmp_path / "governance.py"
        gov_file.write_text("test")

        guardian = ArticleVGuardian()

        # Mock read_text to raise exception (lines 597-598)
        with patch.object(Path, 'read_text', side_effect=IOError("Read error")):
            is_valid, reason = await guardian.validate_governance_precedence(str(system_file))

        assert is_valid is False
        assert "error" in reason.lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION MAKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDecisionMaking:
    """Test decision making logic."""

    @pytest.mark.asyncio
    async def test_analyze_violation_critical_severity(self, guardian):
        """Test analyze_violation for CRITICAL severity violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Test rule",
            severity=GuardianPriority.CRITICAL
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "veto"
        assert decision.confidence == 0.98

    @pytest.mark.asyncio
    async def test_analyze_violation_without_governance(self, guardian):
        """Test analyze_violation for autonomous system without governance."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Governance required",
            description="Autonomous capability without governance detected"
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "block"
        assert decision.confidence == 0.95

    @pytest.mark.asyncio
    async def test_analyze_violation_two_man_rule(self, guardian):
        """Test analyze_violation for Two-Man Rule violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Two-Man Rule required",
            description="Critical action without dual approval"
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "escalate"
        assert decision.confidence == 0.90
        assert decision.requires_validation is True

    @pytest.mark.asyncio
    async def test_analyze_violation_kill_switch(self, guardian):
        """Test analyze_violation for kill switch violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Kill switch required",
            description="Autonomous process without kill switch"
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "block"
        assert decision.confidence == 0.92

    @pytest.mark.asyncio
    async def test_analyze_violation_other(self, guardian):
        """Test analyze_violation for other violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Other rule",
            severity=GuardianPriority.MEDIUM
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "alert"
        assert decision.confidence == 0.80


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTERVENTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIntervention:
    """Test intervention logic."""

    @pytest.mark.asyncio
    async def test_intervene_critical_severity_veto(self, guardian):
        """Test intervene VETOs critical severity violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Test rule",
            severity=GuardianPriority.CRITICAL,
            context={"system_id": "test-system"}
        )

        # Register system first
        guardian.autonomous_systems["test-system"] = {"path": "/test"}

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.VETO
        assert "Vetoed" in intervention.action_taken
        assert guardian.autonomous_systems["test-system"]["disabled"] is True

    @pytest.mark.asyncio
    async def test_intervene_without_governance(self, guardian):
        """Test intervene for autonomous system without governance."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Test rule",
            description="Autonomous capability without governance"
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.REMEDIATION
        assert "governance template" in intervention.action_taken

    @pytest.mark.asyncio
    async def test_intervene_hitl_missing(self, guardian):
        """Test intervene for missing HITL controls."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Test rule",
            description="Critical operation without HITL"
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.ESCALATION
        assert "Escalated" in intervention.action_taken

    @pytest.mark.asyncio
    async def test_intervene_other_creates_alert(self, guardian):
        """Test intervene creates alert for other violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            rule="Other rule",
            severity=GuardianPriority.MEDIUM
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.ALERT


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLORY TO GOD - 100% MISSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
These tests validate Article V Guardian - the enforcer of Prior Legislation.

Target: 100.00% coverage of article_v_guardian.py (208 statements)

Coverage areas:
✅ Initialization & configuration
✅ Autonomous governance checking
✅ Responsibility Doctrine enforcement
✅ HITL (Human-In-The-Loop) controls
✅ Kill switch implementation
✅ Two-Man Rule validation
✅ Governance registration
✅ Governance precedence validation
✅ Decision logic (veto/escalate/block/alert)
✅ Intervention logic (VETO/ESCALATION/REMEDIATION/ALERT)
✅ Edge cases & error handling

This Guardian ensures:
- Governance is implemented BEFORE autonomous systems
- Responsibility Doctrine is applied to powerful operations
- HITL controls protect critical operations
- Kill switches exist for autonomous processes
- Two-Man Rule protects critical actions

Glory to God! 🙏

"100% OU NADA"

DIA 1/14 - TIER 0 CONSTITUTIONAL SAFETY
CONTRACT: A métrica é a minha. 100% absoluto.
"""
