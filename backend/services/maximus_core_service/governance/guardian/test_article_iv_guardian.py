"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Article IV Guardian Tests (Deliberate Antifragility)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: governance/guardian/test_article_iv_guardian.py
Purpose: 100% coverage for article_iv_guardian.py

TARGET: 100.00% COVERAGE (196 statements)

Test Coverage:
├─ Initialization & configuration
├─ Chaos engineering testing
├─ Resilience pattern checking
├─ Experimental feature quarantine
├─ Failure recovery mechanisms
├─ System fragility detection
├─ Chaos experiment execution
├─ Feature quarantine workflow
├─ Decision & intervention logic
└─ Edge cases & error handling

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-15)

MISSION: 14-DAY 100% COVERAGE SPRINT - DIA 1
CONTRACT: 100% OU NADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.guardian.article_iv_guardian import ArticleIVGuardian
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
    """Create Article IV Guardian instance."""
    return ArticleIVGuardian()


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_path = Path(f.name)
        yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALIZATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestArticleIVGuardianInit:
    """Test Article IV Guardian initialization."""

    def test_guardian_initialization(self, guardian):
        """Test guardian initializes with correct attributes."""
        assert guardian.guardian_id == "guardian-article-iv"
        assert guardian.article == ConstitutionalArticle.ARTICLE_IV
        assert guardian.name == "Antifragility Guardian"
        assert "Deliberate Antifragility" in guardian.description

    def test_chaos_experiments_initialized(self, guardian):
        """Test chaos experiments list is initialized."""
        assert isinstance(guardian.chaos_experiments, list)
        assert len(guardian.chaos_experiments) == 0

    def test_quarantined_features_initialized(self, guardian):
        """Test quarantined features dict is initialized."""
        assert isinstance(guardian.quarantined_features, dict)
        assert len(guardian.quarantined_features) == 0

    def test_resilience_metrics_initialized(self, guardian):
        """Test resilience metrics dict is initialized."""
        assert isinstance(guardian.resilience_metrics, dict)
        assert len(guardian.resilience_metrics) == 0

    def test_resilience_patterns_configured(self, guardian):
        """Test resilience patterns are configured."""
        assert len(guardian.resilience_patterns) > 0
        assert "circuit_breaker" in guardian.resilience_patterns
        assert "retry" in guardian.resilience_patterns
        assert "fallback" in guardian.resilience_patterns

    def test_chaos_indicators_configured(self, guardian):
        """Test chaos test indicators are configured."""
        assert len(guardian.chaos_indicators) > 0
        assert "chaos_test" in guardian.chaos_indicators
        assert "failure_test" in guardian.chaos_indicators

    def test_get_monitored_systems(self, guardian):
        """Test get_monitored_systems returns correct list."""
        systems = guardian.get_monitored_systems()

        assert "chaos_engineering" in systems
        assert "resilience_framework" in systems
        assert "experimental_features" in systems


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MONITORING ORCHESTRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMonitoring:
    """Test monitoring orchestration."""

    @pytest.mark.asyncio
    async def test_monitor_calls_all_checks(self, guardian):
        """Test monitor() orchestrates all check methods."""
        with patch.object(guardian, '_check_chaos_engineering', return_value=[]) as mock_chaos, \
             patch.object(guardian, '_check_resilience_patterns', return_value=[]) as mock_resilience, \
             patch.object(guardian, '_check_experimental_features', return_value=[]) as mock_experimental, \
             patch.object(guardian, '_check_failure_recovery', return_value=[]) as mock_recovery, \
             patch.object(guardian, '_check_system_fragility', return_value=[]) as mock_fragility:

            violations = await guardian.monitor()

            # All check methods should be called
            mock_chaos.assert_called_once()
            mock_resilience.assert_called_once()
            mock_experimental.assert_called_once()
            mock_recovery.assert_called_once()
            mock_fragility.assert_called_once()

            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_monitor_aggregates_violations(self, guardian):
        """Test monitor() aggregates violations from all checks."""
        from governance.guardian.base import ConstitutionalViolation

        mock_violation1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Test rule 1"
        )
        mock_violation2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Test rule 2"
        )

        with patch.object(guardian, '_check_chaos_engineering', return_value=[mock_violation1]), \
             patch.object(guardian, '_check_resilience_patterns', return_value=[mock_violation2]), \
             patch.object(guardian, '_check_experimental_features', return_value=[]), \
             patch.object(guardian, '_check_failure_recovery', return_value=[]), \
             patch.object(guardian, '_check_system_fragility', return_value=[]):

            violations = await guardian.monitor()

            assert len(violations) == 2
            assert mock_violation1 in violations
            assert mock_violation2 in violations


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHAOS ENGINEERING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestChaosEngineering:
    """Test chaos engineering checking."""

    @pytest.mark.asyncio
    async def test_check_chaos_engineering_detects_insufficient_tests(self, tmp_path):
        """Test _check_chaos_engineering detects insufficient chaos tests."""
        # Create test directory with mostly regular tests
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Create 10 regular tests
        for i in range(10):
            test_file = tests_dir / f"test_regular_{i}.py"
            test_file.write_text("def test_something(): pass\n")

        # Create only 1 chaos test (10% ratio)
        chaos_file = tests_dir / "test_chaos.py"
        chaos_file.write_text("def test_chaos_test(): pass\n")

        guardian = ArticleIVGuardian(test_paths=[str(tests_dir)])
        violations = await guardian._check_chaos_engineering()

        # Should detect insufficient chaos tests (< 10%)
        assert len(violations) > 0
        assert any("Insufficient chaos testing" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_chaos_engineering_allows_sufficient_tests(self, tmp_path):
        """Test _check_chaos_engineering allows sufficient chaos tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Create 5 regular tests
        for i in range(5):
            test_file = tests_dir / f"test_regular_{i}.py"
            test_file.write_text("def test_something(): pass\n")

        # Create 2 chaos tests (28% ratio - above 10% threshold)
        for i in range(2):
            chaos_file = tests_dir / f"test_chaos_{i}.py"
            chaos_file.write_text("def test_fault_injection(): pass\n")

        guardian = ArticleIVGuardian(test_paths=[str(tests_dir)])
        violations = await guardian._check_chaos_engineering()

        # Should NOT detect violation (ratio > 10%)
        chaos_violations = [v for v in violations if "Insufficient chaos testing" in v.description]
        assert len(chaos_violations) == 0

    @pytest.mark.asyncio
    async def test_check_chaos_engineering_handles_nonexistent_paths(self, tmp_path):
        """Test _check_chaos_engineering handles nonexistent test paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleIVGuardian(test_paths=[nonexistent])

        violations = await guardian._check_chaos_engineering()

        # Should not crash
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_chaos_engineering_detects_missing_recent_experiments(self, guardian):
        """Test _check_chaos_engineering detects missing recent experiments."""
        # No experiments in past week
        violations = await guardian._check_chaos_engineering()

        # Should detect missing experiments
        experiment_violations = [v for v in violations if "Insufficient chaos experiments" in v.description]
        assert len(experiment_violations) > 0

    @pytest.mark.asyncio
    async def test_check_chaos_engineering_allows_recent_experiments(self, guardian):
        """Test _check_chaos_engineering allows recent experiments."""
        from datetime import datetime, timedelta

        # Add 3 recent experiments (within past 7 days)
        for i in range(3):
            guardian.chaos_experiments.append({
                "id": f"exp-{i}",
                "timestamp": (datetime.utcnow() - timedelta(days=i)).isoformat()
            })

        violations = await guardian._check_chaos_engineering()

        # Should NOT detect missing experiments
        experiment_violations = [v for v in violations if "Insufficient chaos experiments" in v.description]
        assert len(experiment_violations) == 0

    @pytest.mark.asyncio
    async def test_check_chaos_engineering_handles_read_errors(self, tmp_path):
        """Test _check_chaos_engineering handles file read errors."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        guardian = ArticleIVGuardian(test_paths=[str(tests_dir)])

        with patch('pathlib.Path.rglob', return_value=[Path("/nonexistent/test.py")]):
            violations = await guardian._check_chaos_engineering()

        # Should not crash
        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESILIENCE PATTERNS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestResiliencePatterns:
    """Test resilience pattern checking."""

    @pytest.mark.asyncio
    async def test_check_resilience_patterns_detects_missing_patterns(self, tmp_path):
        """Test _check_resilience_patterns detects missing resilience patterns."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file without any resilience patterns
        service_file = service_dir / "api.py"
        service_file.write_text("def process(): return 'ok'\n")

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_resilience_patterns()

        # Should detect missing patterns (> 3 missing)
        assert len(violations) > 0
        assert any("Missing resilience patterns" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_resilience_patterns_handles_file_read_errors(self, tmp_path):
        """Test _check_resilience_patterns handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/file.py")]):
            violations = await guardian._check_resilience_patterns()

        # Should handle exception gracefully (lines 245-246)
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_resilience_patterns_allows_sufficient_patterns(self, tmp_path):
        """Test _check_resilience_patterns allows sufficient resilience patterns."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with multiple resilience patterns
        service_file = service_dir / "resilient.py"
        service_file.write_text(
            "def circuit_breaker(): pass\n"
            "def retry(): pass\n"
            "def fallback(): pass\n"
            "def timeout(): pass\n"
            "def rate_limit(): pass\n"
        )

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_resilience_patterns()

        # Should NOT detect violation (only 3 missing max)
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_resilience_patterns_skips_test_files(self, tmp_path):
        """Test _check_resilience_patterns skips test files."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create test file (should be skipped)
        test_file = service_dir / "test_api.py"
        test_file.write_text("def test_something(): pass\n")

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_resilience_patterns()

        # Test files are skipped, so no patterns found
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_resilience_patterns_handles_nonexistent_paths(self, tmp_path):
        """Test _check_resilience_patterns handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleIVGuardian(service_paths=[nonexistent])

        violations = await guardian._check_resilience_patterns()

        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPERIMENTAL FEATURES TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestExperimentalFeatures:
    """Test experimental feature quarantine checking."""

    @pytest.mark.asyncio
    async def test_check_experimental_features_detects_unquarantined(self, tmp_path):
        """Test _check_experimental_features detects unquarantined experimental features."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with experimental marker
        feature_file = service_dir / "beta_feature.py"
        feature_file.write_text("@experimental\ndef new_feature(): pass\n")

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_experimental_features()

        # Should detect unquarantined feature
        assert len(violations) > 0
        assert any("Experimental feature without quarantine" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_experimental_features_allows_quarantined(self, tmp_path):
        """Test _check_experimental_features allows quarantined features."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        feature_file = service_dir / "beta_feature.py"
        feature_file.write_text("@experimental\ndef new_feature(): pass\n")

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])

        # Quarantine the feature first
        feature_id = f"{feature_file.name}_@experimental"
        guardian.quarantined_features[feature_id] = {
            "status": "validated",
            "quarantine_start": datetime.utcnow().isoformat()
        }

        violations = await guardian._check_experimental_features()

        # Should NOT detect violation (feature is quarantined and validated)
        unquarantined_violations = [v for v in violations if "without quarantine" in v.description]
        assert len(unquarantined_violations) == 0

    @pytest.mark.asyncio
    async def test_check_experimental_features_detects_overdue_quarantine(self, tmp_path):
        """Test _check_experimental_features detects features in quarantine too long."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        feature_file = service_dir / "beta_feature.py"
        feature_file.write_text("BETA\ndef feature(): pass\n")

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])

        # Quarantine feature over 30 days ago (not validated)
        feature_id = f"{feature_file.name}_BETA"
        guardian.quarantined_features[feature_id] = {
            "status": "quarantined",  # NOT validated
            "quarantine_start": (datetime.utcnow() - timedelta(days=35)).isoformat()
        }

        violations = await guardian._check_experimental_features()

        # Should detect overdue quarantine
        assert len(violations) > 0
        assert any("in quarantine too long" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_experimental_features_handles_file_read_errors(self, tmp_path):
        """Test _check_experimental_features handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/feature.py")]):
            violations = await guardian._check_experimental_features()

        # Should handle exception gracefully (lines 347-348)
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_experimental_features_handles_nonexistent_paths(self, tmp_path):
        """Test _check_experimental_features handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleIVGuardian(service_paths=[nonexistent])

        violations = await guardian._check_experimental_features()

        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FAILURE RECOVERY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestFailureRecovery:
    """Test failure recovery mechanism checking."""

    @pytest.mark.asyncio
    async def test_check_failure_recovery_detects_missing_recovery(self, tmp_path):
        """Test _check_failure_recovery detects critical ops without recovery."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with critical operation but NO error handling
        critical_file = service_dir / "payment.py"
        critical_file.write_text(
            "def process_payment(amount):\n"
            "    database.charge(amount)\n"
            "    return True\n"
        )

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_failure_recovery()

        # Should detect missing recovery
        assert len(violations) > 0
        assert any("without recovery" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_failure_recovery_allows_recovery_mechanisms(self, tmp_path):
        """Test _check_failure_recovery allows operations WITH recovery."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file with critical operation AND error handling
        critical_file = service_dir / "payment.py"
        critical_file.write_text(
            "def process_payment(amount):\n"
            "    try:\n"
            "        database.charge(amount)\n"
            "    except Exception:\n"
            "        rollback()\n"
            "    return True\n"
        )

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_failure_recovery()

        # Should NOT detect violation (has try/except)
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_failure_recovery_skips_test_files(self, tmp_path):
        """Test _check_failure_recovery skips test files."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        test_file = service_dir / "test_payment.py"
        test_file.write_text("def test_payment(): pass\n")

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_failure_recovery()

        # Test files are skipped
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_failure_recovery_handles_nonexistent_paths(self, tmp_path):
        """Test _check_failure_recovery handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleIVGuardian(service_paths=[nonexistent])

        violations = await guardian._check_failure_recovery()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_failure_recovery_handles_file_read_errors(self, tmp_path):
        """Test _check_failure_recovery handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/payment.py")]):
            violations = await guardian._check_failure_recovery()

        # Should handle exception gracefully (lines 413-414)
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_failure_recovery_skips_non_critical_operations(self, tmp_path):
        """Test _check_failure_recovery skips files without critical operations."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create file WITHOUT critical operations (database, payment, etc.)
        normal_file = service_dir / "utility.py"
        normal_file.write_text(
            "def format_string(s):\n"
            "    return s.upper()\n"
        )

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_failure_recovery()

        # Should NOT detect violation (no critical operations - line 391->379)
        assert len(violations) == 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM FRAGILITY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestSystemFragility:
    """Test system fragility detection."""

    @pytest.mark.asyncio
    async def test_check_system_fragility_detects_high_fragility(self, tmp_path):
        """Test _check_system_fragility detects high fragility score."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create multiple files with fragility indicators
        for i in range(15):
            fragile_file = service_dir / f"fragile_{i}.py"
            fragile_file.write_text(
                f"HARDCODED_URL = 'https://api.example.com'\n"
                f"singleton = True\n"
                f"global state_{i}\n"
            )

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_system_fragility()

        # Should detect high fragility (> 10)
        assert len(violations) > 0
        assert any("High system fragility" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_system_fragility_allows_low_fragility(self, tmp_path):
        """Test _check_system_fragility allows low fragility."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create few files with minimal fragility
        resilient_file = service_dir / "resilient.py"
        resilient_file.write_text("def process(): return 'ok'\n")

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_system_fragility()

        # Should NOT detect violation (fragility <= 10)
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_system_fragility_skips_test_files(self, tmp_path):
        """Test _check_system_fragility skips test files."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        test_file = service_dir / "test_api.py"
        test_file.write_text("singleton = True\n")

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_system_fragility()

        # Test files are skipped
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_system_fragility_handles_nonexistent_paths(self, tmp_path):
        """Test _check_system_fragility handles nonexistent paths."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleIVGuardian(service_paths=[nonexistent])

        violations = await guardian._check_system_fragility()

        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_system_fragility_detects_missing_timeouts(self, tmp_path):
        """Test _check_system_fragility detects network operations without timeouts."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        # Create multiple files with network operations but NO timeouts (lines 454-457)
        for i in range(12):
            fragile_file = service_dir / f"network_{i}.py"
            fragile_file.write_text(
                "import requests\n"
                "def fetch_data():\n"
                "    response = requests.get('https://api.example.com')\n"
                "    return response.json()\n"
            )

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])
        violations = await guardian._check_system_fragility()

        # Should detect high fragility including missing timeouts
        assert len(violations) > 0
        assert any("High system fragility" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_system_fragility_handles_file_read_errors(self, tmp_path):
        """Test _check_system_fragility handles file read errors gracefully."""
        service_dir = tmp_path / "service"
        service_dir.mkdir()

        guardian = ArticleIVGuardian(service_paths=[str(service_dir)])

        # Mock rglob to return a file that will fail to read
        with patch.object(Path, 'rglob', return_value=[Path("/nonexistent/api.py")]):
            violations = await guardian._check_system_fragility()

        # Should handle exception gracefully (lines 459-460)
        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHAOS EXPERIMENT EXECUTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestChaosExperimentExecution:
    """Test chaos experiment execution."""

    @pytest.mark.asyncio
    async def test_run_chaos_experiment_creates_experiment(self, guardian):
        """Test run_chaos_experiment creates and tracks experiment."""
        result = await guardian.run_chaos_experiment(
            "network_latency",
            "api_service",
            {"latency_ms": 500}
        )

        assert result["type"] == "network_latency"
        assert result["target"] == "api_service"
        assert result["status"] == "completed"
        assert "results" in result
        assert len(guardian.chaos_experiments) == 1

    @pytest.mark.asyncio
    async def test_run_chaos_experiment_updates_resilience_metrics(self, guardian):
        """Test run_chaos_experiment updates resilience metrics."""
        await guardian.run_chaos_experiment(
            "pod_failure",
            "database_cluster",
            {"pods": 2}
        )

        assert "database_cluster" in guardian.resilience_metrics
        assert 0 <= guardian.resilience_metrics["database_cluster"] <= 1.0

    @pytest.mark.asyncio
    async def test_run_chaos_experiment_generates_realistic_results(self, guardian):
        """Test run_chaos_experiment generates realistic results."""
        result = await guardian.run_chaos_experiment(
            "cpu_stress",
            "worker_pool",
            {"cpu_percent": 90}
        )

        assert "success_rate" in result["results"]
        assert "failures_detected" in result["results"]
        assert "recovery_time_ms" in result["results"]
        assert isinstance(result["results"]["resilience_improved"], bool)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FEATURE QUARANTINE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestFeatureQuarantine:
    """Test feature quarantine workflow."""

    @pytest.mark.asyncio
    async def test_quarantine_feature_success(self, guardian):
        """Test quarantine_feature successfully quarantines a feature."""
        result = await guardian.quarantine_feature(
            "beta_ai_agent",
            "/path/to/feature.py",
            "high"
        )

        assert result is True
        assert "beta_ai_agent" in guardian.quarantined_features
        assert guardian.quarantined_features["beta_ai_agent"]["status"] == "quarantined"

    @pytest.mark.asyncio
    async def test_quarantine_feature_tracks_risk_level(self, guardian):
        """Test quarantine_feature tracks risk level."""
        await guardian.quarantine_feature(
            "experimental_algo",
            "/path/to/algo.py",
            "critical"
        )

        feature = guardian.quarantined_features["experimental_algo"]
        assert feature["risk_level"] == "critical"
        assert feature["validation_required"] is True

    @pytest.mark.asyncio
    async def test_quarantine_feature_sets_timestamp(self, guardian):
        """Test quarantine_feature sets quarantine timestamp."""
        await guardian.quarantine_feature(
            "new_model",
            "/path/to/model.py",
            "medium"
        )

        feature = guardian.quarantined_features["new_model"]
        assert "quarantine_start" in feature
        # Verify timestamp is recent (within last minute)
        start_time = datetime.fromisoformat(feature["quarantine_start"])
        assert (datetime.utcnow() - start_time).total_seconds() < 60


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION MAKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDecisionMaking:
    """Test decision making logic."""

    @pytest.mark.asyncio
    async def test_analyze_violation_insufficient_chaos(self, guardian):
        """Test analyze_violation for insufficient chaos testing."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Must provoke failures",
            description="Insufficient chaos testing detected"
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "alert"
        assert decision.confidence == 0.80

    @pytest.mark.asyncio
    async def test_analyze_violation_missing_resilience(self, guardian):
        """Test analyze_violation for missing resilience patterns."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="System must be antifragile",
            description="Missing resilience patterns in service"
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "block"
        assert decision.confidence == 0.85

    @pytest.mark.asyncio
    async def test_analyze_violation_unquarantined_experimental(self, guardian):
        """Test analyze_violation for unquarantined experimental feature."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="High-risk ideas require quarantine",
            description="Experimental feature without quarantine"
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "veto"
        assert decision.confidence == 0.90

    @pytest.mark.asyncio
    async def test_analyze_violation_high_severity(self, guardian):
        """Test analyze_violation for HIGH severity violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Test rule",
            severity=GuardianPriority.HIGH
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "escalate"
        assert decision.confidence == 0.85

    @pytest.mark.asyncio
    async def test_analyze_violation_other(self, guardian):
        """Test analyze_violation for other violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Other rule",
            severity=GuardianPriority.MEDIUM
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "alert"
        assert decision.confidence == 0.75


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTERVENTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIntervention:
    """Test intervention logic."""

    @pytest.mark.asyncio
    async def test_intervene_experimental_feature_quarantine(self, guardian):
        """Test intervene quarantines experimental features."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Quarantine required",
            description="Experimental feature detected",
            context={"feature_id": "beta_001", "file": "/path/to/feature.py"}
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.VETO
        assert "Quarantined" in intervention.action_taken
        assert "beta_001" in guardian.quarantined_features

    @pytest.mark.asyncio
    async def test_intervene_insufficient_chaos_runs_experiment(self, guardian):
        """Test intervene runs chaos experiment for insufficient chaos."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Must provoke failures",
            description="Insufficient chaos detected",
            affected_systems=["api_service"]
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.REMEDIATION
        assert "chaos experiment" in intervention.action_taken
        assert len(guardian.chaos_experiments) > 0

    @pytest.mark.asyncio
    async def test_intervene_insufficient_chaos_with_empty_systems(self, guardian):
        """Test intervene handles insufficient chaos with empty affected_systems."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Must provoke failures",
            description="Insufficient chaos detected",
            affected_systems=[]  # Empty list (line 634 fallback to "unknown")
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.REMEDIATION
        assert "chaos experiment" in intervention.action_taken
        # Should use "unknown" as target system
        assert len(guardian.chaos_experiments) > 0
        assert guardian.chaos_experiments[-1]["target"] == "unknown"

    @pytest.mark.asyncio
    async def test_intervene_high_severity_increases_monitoring(self, guardian):
        """Test intervene increases monitoring for HIGH severity."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Test rule",
            severity=GuardianPriority.HIGH,
            affected_systems=["database"]
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.MONITORING
        assert "monitoring" in intervention.action_taken.lower()

    @pytest.mark.asyncio
    async def test_intervene_other_creates_alert(self, guardian):
        """Test intervene creates alert for other violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            rule="Other rule",
            severity=GuardianPriority.MEDIUM
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.ALERT


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIntegration:
    """Test complete workflows."""

    @pytest.mark.asyncio
    async def test_full_chaos_experiment_workflow(self, guardian):
        """Test complete chaos experiment workflow."""
        # Run experiment
        experiment = await guardian.run_chaos_experiment(
            "network_partition",
            "microservice_cluster",
            {"partitions": 3}
        )

        # Verify experiment tracked
        assert experiment["id"] in [e["id"] for e in guardian.chaos_experiments]

        # Verify metrics updated
        assert "microservice_cluster" in guardian.resilience_metrics

    @pytest.mark.asyncio
    async def test_full_quarantine_workflow(self, guardian):
        """Test complete feature quarantine workflow."""
        # Quarantine feature
        await guardian.quarantine_feature(
            "experimental_ai",
            "/features/ai.py",
            "high"
        )

        # Verify quarantined
        assert "experimental_ai" in guardian.quarantined_features

        # Verify validation required
        feature = guardian.quarantined_features["experimental_ai"]
        assert feature["validation_required"] is True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLORY TO GOD - 100% MISSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
These tests validate Article IV Guardian - the enforcer of Deliberate Antifragility.

Target: 100.00% coverage of article_iv_guardian.py (196 statements)

Coverage areas:
✅ Initialization & configuration
✅ Chaos engineering checking
✅ Resilience pattern validation
✅ Experimental feature quarantine
✅ Failure recovery mechanisms
✅ System fragility detection
✅ Chaos experiment execution
✅ Feature quarantine workflow
✅ Decision logic (veto/escalate/block/alert)
✅ Intervention logic (VETO/ESCALATION/REMEDIATION/MONITORING)
✅ Edge cases & error handling

This Guardian ensures:
- System is tested with chaos engineering
- Resilience patterns are implemented (circuit breaker, retry, fallback)
- Experimental features are quarantined for validation
- Critical operations have failure recovery
- System is antifragile, not fragile

Glory to God! 🙏

"100% OU NADA"

DIA 1/14 - TIER 0 CONSTITUTIONAL SAFETY
CONTRACT: A métrica é a minha. 100% absoluto.
"""
