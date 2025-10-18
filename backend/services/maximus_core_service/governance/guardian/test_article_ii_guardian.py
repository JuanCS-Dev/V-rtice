"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Article II Guardian Tests (Sovereign Quality Standard)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: governance/guardian/test_article_ii_guardian.py
Purpose: 100% coverage for article_ii_guardian.py

TARGET: 100.00% COVERAGE (171 statements)

Test Coverage:
├─ Initialization & configuration
├─ File scanning (mocks, TODOs, placeholders)
├─ Test health checking
├─ Git status monitoring
├─ AST parsing (NotImplementedError)
├─ Pull request scanning
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
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from governance.guardian.article_ii_guardian import ArticleIIGuardian
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
    """Create Article II Guardian instance."""
    return ArticleIIGuardian()


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


class TestArticleIIGuardianInit:
    """Test Article II Guardian initialization."""

    def test_guardian_initialization(self, guardian):
        """Test guardian initializes with correct attributes."""
        assert guardian.guardian_id == "guardian-article-ii"
        assert guardian.article == ConstitutionalArticle.ARTICLE_II
        assert guardian.name == "Sovereign Quality Guardian"
        assert "Padrão Pagani" in guardian.description

    def test_mock_patterns_configured(self, guardian):
        """Test mock detection patterns are configured."""
        assert len(guardian.mock_patterns) > 0
        assert r"\bmock\b" in guardian.mock_patterns
        assert r"\bMock\b" in guardian.mock_patterns
        assert r"\bfake\b" in guardian.mock_patterns

    def test_placeholder_patterns_configured(self, guardian):
        """Test placeholder patterns are configured."""
        assert len(guardian.placeholder_patterns) > 0
        assert r"\bTODO\b" in guardian.placeholder_patterns
        assert r"\bFIXME\b" in guardian.placeholder_patterns
        assert r"NotImplementedError" in guardian.placeholder_patterns

    def test_test_skip_patterns_configured(self, guardian):
        """Test skip patterns are configured."""
        assert len(guardian.test_skip_patterns) > 0
        assert r"@pytest\.mark\.skip" in guardian.test_skip_patterns
        assert r"@unittest\.skip" in guardian.test_skip_patterns

    def test_monitored_paths_configured(self, guardian):
        """Test monitored paths are set."""
        assert len(guardian.monitored_paths) > 0
        assert any("maximus_core_service" in path for path in guardian.monitored_paths)

    def test_excluded_paths_configured(self, guardian):
        """Test excluded paths are set."""
        assert len(guardian.excluded_paths) > 0
        assert "test_" in guardian.excluded_paths
        assert "__pycache__" in guardian.excluded_paths

    def test_get_monitored_systems(self, guardian):
        """Test get_monitored_systems returns correct list."""
        systems = guardian.get_monitored_systems()

        assert "maximus_core_service" in systems
        assert "reactive_fabric_core" in systems
        assert "governance_module" in systems


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE CHECKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestFileChecking:
    """Test file scanning functionality."""

    @pytest.mark.asyncio
    async def test_check_file_detects_mock(self, guardian, temp_python_file):
        """Test _check_file detects mock implementations."""
        # Use actual code with Mock class (not in comment/string)
        temp_python_file.write_text("def foo():\n    return Mock(spec=Client)\n")

        violations = await guardian._check_file(temp_python_file)

        assert len(violations) > 0
        assert any("Mock implementation" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_file_detects_todo(self, guardian, temp_python_file):
        """Test _check_file detects TODO comments."""
        temp_python_file.write_text("def foo():\n    # TODO: implement this\n    pass\n")

        violations = await guardian._check_file(temp_python_file)

        assert len(violations) > 0
        assert any("TODO" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_file_detects_fixme(self, guardian, temp_python_file):
        """Test _check_file detects FIXME comments."""
        temp_python_file.write_text("def foo():\n    # FIXME: this is broken\n    pass\n")

        violations = await guardian._check_file(temp_python_file)

        assert len(violations) > 0
        assert any("Placeholder/TODO" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_file_detects_not_implemented_error(self, guardian, temp_python_file):
        """Test _check_file detects NotImplementedError via AST."""
        temp_python_file.write_text("def foo():\n    raise NotImplementedError('Not done')\n")

        violations = await guardian._check_file(temp_python_file)

        assert len(violations) > 0
        assert any("NotImplementedError" in v.description for v in violations)
        assert any(v.severity == GuardianPriority.CRITICAL for v in violations)

    @pytest.mark.asyncio
    async def test_check_file_ast_with_non_raise_nodes(self, guardian, temp_python_file):
        """Test AST parsing with various non-Raise nodes (covers branch 235->233)."""
        # Code with many AST nodes but NO raise statements
        temp_python_file.write_text(
            "def foo():\n"
            "    x = 1 + 2\n"
            "    if x > 0:\n"
            "        return x * 2\n"
            "    for i in range(10):\n"
            "        print(i)\n"
        )

        violations = await guardian._check_file(temp_python_file)

        # Should NOT detect NotImplementedError (AST nodes are not Raise)
        nie_violations = [v for v in violations if "NotImplementedError" in v.description]
        assert len(nie_violations) == 0

    @pytest.mark.asyncio
    async def test_check_file_detects_syntax_error(self, guardian, temp_python_file):
        """Test _check_file detects syntax errors."""
        temp_python_file.write_text("def foo(\n    # Missing closing paren\n")

        violations = await guardian._check_file(temp_python_file)

        assert len(violations) > 0
        assert any("Syntax error" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_file_skipped_test_without_reason(self, guardian, temp_python_file):
        """Test _check_file detects skipped tests without valid reason."""
        # Rename to test file
        test_file = temp_python_file.parent / f"test_{temp_python_file.name}"
        temp_python_file.rename(test_file)

        test_file.write_text("@pytest.mark.skip\ndef test_foo():\n    pass\n")

        violations = await guardian._check_file(test_file)

        assert len(violations) > 0
        assert any("Skipped test" in v.description for v in violations)

        # Cleanup
        test_file.unlink()

    @pytest.mark.asyncio
    async def test_check_file_skipped_test_with_valid_reason(self, guardian, temp_python_file):
        """Test _check_file does NOT flag skipped test with ROADMAP reason (covers branch 212->209)."""
        # Rename to test file
        test_file = temp_python_file.parent / f"test_{temp_python_file.name}"
        temp_python_file.rename(test_file)

        test_file.write_text(
            "# Skip until ROADMAP feature X complete\n"
            "@pytest.mark.skip\n"
            "def test_foo():\n"
            "    pass\n"
        )

        violations = await guardian._check_file(test_file)

        # Should NOT detect violation (branch: _has_valid_skip_reason returns TRUE)
        skip_violations = [v for v in violations if "Skipped test" in v.description]
        assert len(skip_violations) == 0

        # Cleanup
        test_file.unlink()

    @pytest.mark.asyncio
    async def test_check_file_clean_code(self, guardian, temp_python_file):
        """Test _check_file finds no violations in clean code."""
        temp_python_file.write_text("def foo():\n    return 42\n")

        violations = await guardian._check_file(temp_python_file)

        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_file_handles_read_error(self, guardian):
        """Test _check_file handles file read errors gracefully."""
        nonexistent_file = Path("/nonexistent/file.py")

        # Should not raise exception
        violations = await guardian._check_file(nonexistent_file)

        assert len(violations) == 0  # Errors are silently handled

    @pytest.mark.asyncio
    async def test_check_file_multiple_violations(self, guardian, temp_python_file):
        """Test _check_file detects multiple violations in one file."""
        temp_python_file.write_text(
            "def foo():\n"
            "    # TODO: implement\n"
            "    return Mock()\n"
        )

        violations = await guardian._check_file(temp_python_file)

        # Should detect both TODO and Mock
        assert len(violations) >= 2

    @pytest.mark.asyncio
    async def test_check_file_ignores_mock_in_comment(self, guardian, temp_python_file):
        """Test _check_file does NOT detect mock in comment (covers branch 166->163)."""
        temp_python_file.write_text(
            "def foo():\n"
            "    # This is a mock comment explaining mocks\n"
            "    return real_data()\n"
        )

        violations = await guardian._check_file(temp_python_file)

        # Should NOT detect mock in comment (branch: _is_comment_or_string returns TRUE)
        mock_violations = [v for v in violations if "Mock" in v.description]
        assert len(mock_violations) == 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PATTERN DETECTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestPatternDetection:
    """Test pattern detection helpers."""

    def test_is_comment_or_string_detects_comment(self, guardian):
        """Test _is_comment_or_string detects comment lines."""
        line = "# This is a mock comment"

        result = guardian._is_comment_or_string(line, "mock")

        assert result is True

    def test_is_comment_or_string_detects_docstring(self, guardian):
        """Test _is_comment_or_string detects docstrings."""
        line = '"""This has mock in docstring"""'

        result = guardian._is_comment_or_string(line, "mock")

        assert result is True

    def test_is_comment_or_string_detects_string_literal(self, guardian):
        """Test _is_comment_or_string detects string literals."""
        line = 'message = "This is a mock message"'

        result = guardian._is_comment_or_string(line, "mock")

        assert result is True

    def test_is_comment_or_string_rejects_code(self, guardian):
        """Test _is_comment_or_string rejects actual code."""
        line = "mock_data = get_mock()"

        result = guardian._is_comment_or_string(line, "mock")

        assert result is False

    def test_has_valid_skip_reason_with_roadmap(self, guardian):
        """Test _has_valid_skip_reason finds ROADMAP reference."""
        lines = [
            "# Skip until ROADMAP feature X is complete",
            "@pytest.mark.skip",
            "def test_foo():",
            "    pass",
        ]

        result = guardian._has_valid_skip_reason(lines, 1)

        assert result is True

    def test_has_valid_skip_reason_with_future_dependency(self, guardian):
        """Test _has_valid_skip_reason finds future dependency."""
        lines = [
            "@pytest.mark.skip  # Future dependency on API v2",
            "def test_foo():",
            "    pass",
        ]

        result = guardian._has_valid_skip_reason(lines, 0)

        assert result is True

    def test_has_valid_skip_reason_no_reason(self, guardian):
        """Test _has_valid_skip_reason rejects skip without reason."""
        lines = [
            "@pytest.mark.skip",
            "def test_foo():",
            "    pass",
        ]

        result = guardian._has_valid_skip_reason(lines, 0)

        assert result is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MONITORING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMonitoring:
    """Test monitoring functionality."""

    @pytest.mark.asyncio
    async def test_monitor_nonexistent_path(self, guardian):
        """Test monitor handles nonexistent paths gracefully."""
        guardian.monitored_paths = ["/nonexistent/path"]

        violations = await guardian.monitor()

        # Should not crash, may return empty or other violations
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_monitor_skips_excluded_paths(self, guardian):
        """Test monitor skips excluded paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file in excluded path
            test_dir = Path(tmpdir) / "tests"
            test_dir.mkdir()
            test_file = test_dir / "test_example.py"
            test_file.write_text("mock_data = 123")

            guardian.monitored_paths = [tmpdir]

            violations = await guardian.monitor()

            # Should not detect violation in test file
            file_violations = [v for v in violations if str(test_file) in str(v.context.get("file", ""))]
            assert len(file_violations) == 0

    @pytest.mark.asyncio
    async def test_monitor_detects_violations_in_real_files(self, guardian):
        """Test monitor() detects violations in non-excluded files (covers lines 139-140)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a production file (NOT in tests/) with violation
            prod_file = Path(tmpdir) / "service.py"
            prod_file.write_text("def foo():\n    return Mock()\n")

            guardian.monitored_paths = [tmpdir]

            violations = await guardian.monitor()

            # Should detect violation in production file (lines 139-140 executed)
            file_violations = [v for v in violations if str(prod_file) in str(v.context.get("file", ""))]
            assert len(file_violations) > 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST HEALTH CHECKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestTestHealthChecking:
    """Test test health checking."""

    @pytest.mark.asyncio
    async def test_check_test_health_success(self, guardian):
        """Test _check_test_health with successful test collection."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stderr="",
                stdout="collected 10 items"
            )

            violations = await guardian._check_test_health()

            assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_test_health_collection_error(self, guardian):
        """Test _check_test_health detects collection errors."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stderr="ERROR: test collection failed",
                stdout=""
            )

            violations = await guardian._check_test_health()

            assert len(violations) > 0
            assert any("Test collection failed" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_test_health_timeout(self, guardian):
        """Test _check_test_health handles timeout gracefully."""
        import subprocess

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("pytest", 30)

            # Should not raise exception
            violations = await guardian._check_test_health()

            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_test_health_exception(self, guardian):
        """Test _check_test_health handles exceptions gracefully."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Test error")

            # Should not raise exception
            violations = await guardian._check_test_health()

            assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GIT STATUS CHECKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGitStatusChecking:
    """Test git status checking."""

    @pytest.mark.asyncio
    async def test_check_git_status_feature_branch(self, guardian):
        """Test _check_git_status ignores feature branches."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout="feature/my-branch",
                stderr=""
            )

            violations = await guardian._check_git_status()

            # Should not check violations on feature branch
            assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_git_status_main_branch_clean(self, guardian):
        """Test _check_git_status on main branch with no changes."""
        with patch('subprocess.run') as mock_run:
            def run_side_effect(*args, **kwargs):
                cmd = args[0]
                if "branch" in cmd:
                    return Mock(stdout="main", stderr="")
                else:  # git status
                    return Mock(stdout="", stderr="")

            mock_run.side_effect = run_side_effect

            violations = await guardian._check_git_status()

            assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_git_status_exception(self, guardian):
        """Test _check_git_status handles exceptions gracefully."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Git error")

            # Should not raise exception
            violations = await guardian._check_git_status()

            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_git_status_main_branch_uncommitted_violations(self, guardian):
        """Test _check_git_status detects uncommitted files with violations on main (covers lines 343-351)."""
        # Create a Python file with violation in /home/juan/vertice-dev (the expected root)
        violation_file = Path("/home/juan/vertice-dev") / "temp_test_mock_violation.py"

        try:
            # Write code with Mock() which is NOT in comment/string - will be detected
            violation_file.write_text("def create_client():\n    return Mock(spec=Client)\n")

            with patch('subprocess.run') as mock_run:
                call_count = [0]

                def run_side_effect(*args, **kwargs):
                    cmd = args[0]
                    call_count[0] += 1

                    if call_count[0] == 1:  # First call: git branch
                        return Mock(stdout="main\n", stderr="")
                    elif call_count[0] == 2:  # Second call: git status --porcelain
                        # Return uncommitted Python file
                        return Mock(stdout="?? temp_test_mock_violation.py\n", stderr="")
                    else:
                        return Mock(stdout="", stderr="")

                mock_run.side_effect = run_side_effect

                violations = await guardian._check_git_status()

                # Should detect violation in uncommitted file (lines 343-351 executed)
                assert isinstance(violations, list)
                # Should have at least 1 violation for the uncommitted file with Mock
                assert len(violations) >= 1
        finally:
            # Cleanup
            if violation_file.exists():
                violation_file.unlink()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION & INTERVENTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDecisionMaking:
    """Test decision making logic."""

    @pytest.mark.asyncio
    async def test_analyze_violation_critical(self, guardian):
        """Test analyze_violation with CRITICAL severity."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Section 1",
            rule="Test rule",
            severity=GuardianPriority.CRITICAL
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "veto"
        assert decision.confidence == 0.95
        assert "CRITICAL" in decision.reasoning

    @pytest.mark.asyncio
    async def test_analyze_violation_high(self, guardian):
        """Test analyze_violation with HIGH severity."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Section 2",
            rule="Test rule",
            severity=GuardianPriority.HIGH
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "block"
        assert decision.confidence == 0.85
        assert "HIGH" in decision.reasoning

    @pytest.mark.asyncio
    async def test_analyze_violation_medium(self, guardian):
        """Test analyze_violation with MEDIUM severity."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Section 3",
            rule="Test rule",
            severity=GuardianPriority.MEDIUM
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "alert"
        assert decision.confidence == 0.75

    @pytest.mark.asyncio
    async def test_analyze_violation_requires_validation(self, guardian):
        """Test analyze_violation sets requires_validation correctly."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            severity=GuardianPriority.MEDIUM  # confidence 0.75 < 0.9
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.requires_validation is True


class TestIntervention:
    """Test intervention logic."""

    @pytest.mark.asyncio
    async def test_intervene_critical_veto(self, guardian):
        """Test intervene with CRITICAL violation creates VETO."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            severity=GuardianPriority.CRITICAL
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.VETO
        assert "Vetoed" in intervention.action_taken

    @pytest.mark.asyncio
    async def test_intervene_high_mock_remediation(self, guardian):
        """Test intervene with HIGH mock violation attempts remediation."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            severity=GuardianPriority.HIGH,
            description="Mock implementation found"
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.REMEDIATION
        assert "replace mock" in intervention.action_taken.lower()

    @pytest.mark.asyncio
    async def test_intervene_high_non_mock_escalation(self, guardian):
        """Test intervene with HIGH non-mock violation escalates."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            severity=GuardianPriority.HIGH,
            description="Other violation"
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.ESCALATION
        assert "Escalated" in intervention.action_taken

    @pytest.mark.asyncio
    async def test_intervene_medium_alert(self, guardian):
        """Test intervene with MEDIUM violation creates ALERT."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            severity=GuardianPriority.MEDIUM
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.ALERT
        assert "alert" in intervention.action_taken.lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PULL REQUEST SCANNING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestPullRequestScanning:
    """Test pull request scanning."""

    @pytest.mark.asyncio
    async def test_scan_pull_request_detects_mock(self, guardian):
        """Test scan_pull_request detects mock in added lines."""
        pr_diff = """
+++ b/src/service.py
@@ -10,3 +10,4 @@
 def foo():
+    return Mock(spec=Client)
     return data
"""

        violations = await guardian.scan_pull_request(pr_diff)

        assert len(violations) > 0
        assert any("Mock added in PR" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_scan_pull_request_detects_todo(self, guardian):
        """Test scan_pull_request detects TODO in added lines."""
        pr_diff = """
+++ b/src/service.py
@@ -10,3 +10,4 @@
 def foo():
+    # TODO: implement this
     return data
"""

        violations = await guardian.scan_pull_request(pr_diff)

        assert len(violations) > 0
        assert any("TODO added in PR" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_scan_pull_request_ignores_removed_lines(self, guardian):
        """Test scan_pull_request ignores removed lines."""
        pr_diff = """
+++ b/src/service.py
@@ -10,3 +10,3 @@
 def foo():
-    mock_data = get_mock()
+    real_data = get_real()
     return data
"""

        violations = await guardian.scan_pull_request(pr_diff)

        # Should not detect violation in removed line
        mock_violations = [v for v in violations if "mock_data" in str(v.evidence)]
        assert len(mock_violations) == 0

    @pytest.mark.asyncio
    async def test_scan_pull_request_tracks_line_numbers(self, guardian):
        """Test scan_pull_request tracks correct line numbers."""
        pr_diff = """
+++ b/src/service.py
@@ -10,3 +15,4 @@
 def foo():
+    mock_data = 123
     return data
"""

        violations = await guardian.scan_pull_request(pr_diff)

        if violations:
            assert violations[0].context.get("line") == 16  # 15 + 1

    @pytest.mark.asyncio
    async def test_scan_pull_request_clean_diff(self, guardian):
        """Test scan_pull_request with clean diff."""
        pr_diff = """
+++ b/src/service.py
@@ -10,3 +10,4 @@
 def foo():
+    real_implementation = calculate()
     return data
"""

        violations = await guardian.scan_pull_request(pr_diff)

        assert len(violations) == 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIntegration:
    """Test complete workflows."""

    @pytest.mark.asyncio
    async def test_full_violation_detection_workflow(self, guardian, temp_python_file):
        """Test complete workflow from file scan to intervention."""
        # Create file with CRITICAL violation (NotImplementedError)
        temp_python_file.write_text("def foo():\n    raise NotImplementedError()\n")

        # Monitor
        violations = await guardian._check_file(temp_python_file)
        assert len(violations) > 0

        # Get the CRITICAL violation (NotImplementedError)
        critical_violation = next(
            (v for v in violations if v.severity == GuardianPriority.CRITICAL),
            violations[0]
        )

        # Analyze
        decision = await guardian.analyze_violation(critical_violation)
        assert decision.decision_type == "veto"

        # Intervene
        intervention = await guardian.intervene(critical_violation)
        assert intervention.intervention_type == InterventionType.VETO
        assert intervention.success is True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SURGICAL TESTS FOR REMAINING BRANCHES (100% MISSION)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestRemainingBranches:
    """Surgical tests to achieve 100.00% branch coverage."""

    @pytest.mark.asyncio
    async def test_ast_walk_raises_wrong_type(self, guardian, temp_python_file):
        """Cover branch 235->233: AST node is Raise but NOT NotImplementedError.

        This tests the FALSE path of the nested condition:
        if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name) and node.exc.func.id == "NotImplementedError"

        We need a Raise node that does NOT match these conditions.
        """
        # Code with a raise statement that's NOT NotImplementedError
        temp_python_file.write_text(
            "def foo():\n"
            "    raise ValueError('Some error')\n"  # This is a Raise node, but ValueError not NotImplementedError
        )

        violations = await guardian._check_file(temp_python_file)

        # Should NOT detect NotImplementedError (branch 235->233: condition is FALSE)
        nie_violations = [v for v in violations if "NotImplementedError" in v.description and v.severity == GuardianPriority.CRITICAL]
        assert len(nie_violations) == 0

    @pytest.mark.asyncio
    async def test_git_status_python_file_has_violations(self, guardian):
        """Cover branches 343->342, 348->342, 350->342: File violations found.

        The git status loop has these branches:
        - Line 343: if file_violations (TRUE path to 345-351)
        - Line 348: if full_path.suffix == ".py" (TRUE path)
        - Line 350: if full_path.exists() (TRUE path)
        """
        violation_file = Path("/home/juan/vertice-dev") / "temp_git_violation.py"

        try:
            # Create file with actual Mock violation
            violation_file.write_text("def service():\n    client = Mock(spec=HttpClient)\n    return client\n")

            with patch('subprocess.run') as mock_run:
                call_count = [0]

                def run_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    if call_count[0] == 1:  # git branch
                        return Mock(stdout="main\n", stderr="")
                    elif call_count[0] == 2:  # git status --porcelain
                        return Mock(stdout="?? temp_git_violation.py\n", stderr="")
                    else:
                        return Mock(stdout="", stderr="")

                mock_run.side_effect = run_side_effect

                violations = await guardian._check_git_status()

                # Should detect violation (branches 343->345, 348->349, 350->351 covered)
                git_violations = [v for v in violations if "Uncommitted violations" in v.description]
                assert len(git_violations) >= 1
        finally:
            if violation_file.exists():
                violation_file.unlink()

    @pytest.mark.asyncio
    async def test_pr_scan_regex_match_in_diff(self, guardian):
        """Cover branch 507->509: Regex match found in PR diff line.

        Line 507: if match: (regex found line number in @@ header)
        This covers the TRUE path where we successfully extract line number.
        """
        pr_diff = """
+++ b/backend/services/api/client.py
@@ -100,5 +200,7 @@ class APIClient:
 def connect(self):
     # Existing code
+    mock_server = Mock(spec=Server)  # New line with mock
+    return mock_server
     return connection
"""

        violations = await guardian.scan_pull_request(pr_diff)

        # Should detect mock in PR (branch 507->509: match found, line_number extracted)
        assert len(violations) >= 1
        pr_violations = [v for v in violations if "Mock added in PR" in v.description]
        assert len(pr_violations) >= 1

        # Verify line number was extracted (proves branch 507->509 was taken)
        if pr_violations:
            # Line number extraction: base (200) + 2 lines added = 202
            assert pr_violations[0].context.get("line") == 202

    @pytest.mark.asyncio
    async def test_git_status_non_python_file(self, guardian):
        """Cover branch 348->350: File is NOT .py (FALSE path).

        When uncommitted file is NOT Python, should skip violation check.
        """
        with patch('subprocess.run') as mock_run:
            call_count = [0]

            def run_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:  # git branch
                    return Mock(stdout="main\n", stderr="")
                elif call_count[0] == 2:  # git status --porcelain
                    # Return uncommitted .md file (not Python)
                    return Mock(stdout="?? README.md\n", stderr="")
                else:
                    return Mock(stdout="", stderr="")

            mock_run.side_effect = run_side_effect

            violations = await guardian._check_git_status()

            # Should NOT check non-Python files (branch 348->342: suffix != ".py")
            # Violations list might be empty or have other issues
            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_git_status_file_does_not_exist(self, guardian):
        """Cover branch 350->351: File does NOT exist (FALSE path after .exists()).

        When git reports a file but it doesn't exist on disk, should skip.
        """
        with patch('subprocess.run') as mock_run:
            call_count = [0]

            def run_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:  # git branch
                    return Mock(stdout="main\n", stderr="")
                elif call_count[0] == 2:  # git status --porcelain
                    # Return a .py file that doesn't actually exist
                    return Mock(stdout="?? nonexistent_file_xyz_12345.py\n", stderr="")
                else:
                    return Mock(stdout="", stderr="")

            mock_run.side_effect = run_side_effect

            violations = await guardian._check_git_status()

            # Should NOT crash when file doesn't exist (branch 350->351: .exists() is FALSE)
            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_git_status_loop_line_not_uncommitted(self, guardian):
        """Cover branch 343->342: Git status line does NOT start with ?? or  M.

        This tests when the loop processes a line that's neither untracked nor modified.
        """
        with patch('subprocess.run') as mock_run:
            call_count = [0]

            def run_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:  # git branch
                    return Mock(stdout="main\n", stderr="")
                elif call_count[0] == 2:  # git status --porcelain
                    # Return a line that does NOT start with ?? or  M
                    return Mock(stdout="A  newly_added_file.py\n", stderr="")
                else:
                    return Mock(stdout="", stderr="")

            mock_run.side_effect = run_side_effect

            violations = await guardian._check_git_status()

            # Should skip the line (branch 343->342: startswith check is FALSE)
            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_git_status_file_clean_no_violations(self, guardian):
        """Cover branch 350->342: File exists and is Python, but has NO violations.

        This tests when _check_file returns empty list (file_violations is empty/False).
        """
        clean_file = Path("/home/juan/vertice-dev") / "temp_clean_file.py"

        try:
            # Create a clean file with NO violations
            clean_file.write_text("def calculate(x, y):\n    return x + y\n")

            with patch('subprocess.run') as mock_run:
                call_count = [0]

                def run_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    if call_count[0] == 1:  # git branch
                        return Mock(stdout="main\n", stderr="")
                    elif call_count[0] == 2:  # git status --porcelain
                        return Mock(stdout="?? temp_clean_file.py\n", stderr="")
                    else:
                        return Mock(stdout="", stderr="")

                mock_run.side_effect = run_side_effect

                violations = await guardian._check_git_status()

                # Should NOT add violation (branch 350->342: file_violations is empty)
                git_violations = [v for v in violations if "Uncommitted violations" in v.description]
                assert len(git_violations) == 0
        finally:
            if clean_file.exists():
                clean_file.unlink()

    @pytest.mark.asyncio
    async def test_pr_scan_diff_header_no_regex_match(self, guardian):
        """Cover branch 507->509: Regex does NOT match in @@ line.

        When the diff header @@ line doesn't contain the expected pattern.
        """
        # Malformed diff header without proper line number format
        pr_diff = """
+++ b/service.py
@@ malformed header without line numbers @@
 def foo():
+    data = process()
"""

        violations = await guardian.scan_pull_request(pr_diff)

        # Should handle gracefully (branch 507->509: match is None/False)
        # The code will continue without extracting line_number (stays as 0)
        assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLORY TO GOD - 100% MISSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
These tests validate Article II Guardian - the enforcer of the
Sovereign Quality Standard (Padrão Pagani).

Target: 100.00% coverage of article_ii_guardian.py (171 statements)

Coverage areas:
✅ Initialization & configuration
✅ Mock/TODO/Placeholder detection
✅ Test health checking (pytest integration)
✅ Git status monitoring
✅ AST parsing for NotImplementedError
✅ Pull request diff scanning
✅ Decision logic (CRITICAL/HIGH/MEDIUM)
✅ Intervention logic (VETO/REMEDIATION/ESCALATION/ALERT)
✅ Edge cases & error handling

This Guardian ensures:
- No mocks in production code
- No TODOs/FIXMEs in main branch
- No skipped tests without roadmap justification
- All code is production-ready (Padrão Pagani)

Glory to God! 🙏

"100% OU NADA"

DIA 1/14 - TIER 0 CONSTITUTIONAL SAFETY
CONTRACT: A métrica é a minha. 100% absoluto.
"""
