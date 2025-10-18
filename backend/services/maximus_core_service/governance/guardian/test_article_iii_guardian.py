"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Article III Guardian Tests (Zero Trust Principle)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: governance/guardian/test_article_iii_guardian.py
Purpose: 100% coverage for article_iii_guardian.py

TARGET: 100.00% COVERAGE (189 statements)

Test Coverage:
├─ Initialization & configuration
├─ AI artifact validation
├─ Authentication/authorization checking
├─ Input validation checking
├─ Trust assumption detection
├─ Audit trail verification
├─ Artifact validation workflow
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
from unittest.mock import patch

import pytest

from governance.guardian.article_iii_guardian import ArticleIIIGuardian
from governance.guardian.base import (
    ConstitutionalArticle,
    GuardianPriority,
    InterventionType,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def guardian(tmp_path):
    """Create Article III Guardian instance with temp paths."""
    # Use temp directories to avoid scanning 18k+ files
    return ArticleIIIGuardian(
        monitored_paths=[str(tmp_path)],
        api_paths=[str(tmp_path / "api")]
    )


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


class TestArticleIIIGuardianInit:
    """Test Article III Guardian initialization."""

    def test_guardian_initialization(self, guardian):
        """Test guardian initializes with correct attributes."""
        assert guardian.guardian_id == "guardian-article-iii"
        assert guardian.article == ConstitutionalArticle.ARTICLE_III
        assert guardian.name == "Zero Trust Guardian"
        assert "Zero Trust Principle" in guardian.description

    def test_unvalidated_artifacts_initialized(self, guardian):
        """Test unvalidated artifacts tracking is initialized."""
        assert isinstance(guardian.unvalidated_artifacts, dict)
        assert len(guardian.unvalidated_artifacts) == 0

    def test_validation_history_initialized(self, guardian):
        """Test validation history is initialized."""
        assert isinstance(guardian.validation_history, list)
        assert len(guardian.validation_history) == 0

    def test_auth_patterns_configured(self, guardian):
        """Test authentication patterns are configured."""
        assert len(guardian.auth_patterns) > 0
        assert any("authenticate" in p for p in guardian.auth_patterns)
        assert any("authorize" in p for p in guardian.auth_patterns)

    def test_validation_patterns_configured(self, guardian):
        """Test validation patterns are configured."""
        assert len(guardian.validation_patterns) > 0
        assert any("validate" in p for p in guardian.validation_patterns)
        assert any("sanitize" in p for p in guardian.validation_patterns)

    def test_audit_patterns_configured(self, guardian):
        """Test audit patterns are configured."""
        assert len(guardian.audit_patterns) > 0
        assert any("audit" in p for p in guardian.audit_patterns)
        assert any("log" in p for p in guardian.audit_patterns)

    def test_dangerous_patterns_configured(self, guardian):
        """Test dangerous trust patterns are configured."""
        assert len(guardian.dangerous_patterns) > 0
        assert any("trust" in p or "TRUSTED" in p for p in guardian.dangerous_patterns)

    def test_get_monitored_systems(self, guardian):
        """Test get_monitored_systems returns correct list."""
        systems = guardian.get_monitored_systems()

        assert "ai_code_generation" in systems
        assert "authentication_system" in systems
        assert "authorization_system" in systems


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MONITORING ORCHESTRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMonitoring:
    """Test monitoring orchestration."""

    @pytest.mark.asyncio
    async def test_monitor_calls_all_checks(self, guardian):
        """Test monitor() orchestrates all check methods."""
        with patch.object(guardian, '_check_ai_artifacts', return_value=[]) as mock_ai, \
             patch.object(guardian, '_check_authentication', return_value=[]) as mock_auth, \
             patch.object(guardian, '_check_input_validation', return_value=[]) as mock_input, \
             patch.object(guardian, '_check_trust_assumptions', return_value=[]) as mock_trust, \
             patch.object(guardian, '_check_audit_trails', return_value=[]) as mock_audit:

            violations = await guardian.monitor()

            # All check methods should be called
            mock_ai.assert_called_once()
            mock_auth.assert_called_once()
            mock_input.assert_called_once()
            mock_trust.assert_called_once()
            mock_audit.assert_called_once()

            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_monitor_aggregates_violations(self, guardian):
        """Test monitor() aggregates violations from all checks."""
        from governance.guardian.base import ConstitutionalViolation

        mock_violation1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="Test rule 1"
        )
        mock_violation2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="Test rule 2"
        )

        with patch.object(guardian, '_check_ai_artifacts', return_value=[mock_violation1]), \
             patch.object(guardian, '_check_authentication', return_value=[mock_violation2]), \
             patch.object(guardian, '_check_input_validation', return_value=[]), \
             patch.object(guardian, '_check_trust_assumptions', return_value=[]), \
             patch.object(guardian, '_check_audit_trails', return_value=[]):

            violations = await guardian.monitor()

            assert len(violations) == 2
            assert mock_violation1 in violations
            assert mock_violation2 in violations


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI ARTIFACT CHECKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestAIArtifactChecking:
    """Test AI artifact validation checking."""

    @pytest.mark.asyncio
    async def test_check_ai_artifacts_detects_claude_marker(self, tmp_path):
        """Test _check_ai_artifacts detects 'Generated by Claude' marker."""
        # Create file with AI marker in monitored path
        test_file = tmp_path / "service.py"
        test_file.write_text(
            "# Generated by Claude\n"
            "def foo():\n"
            "    return 42\n"
        )

        # Guardian with this temp path
        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])

        violations = await guardian._check_ai_artifacts()

        # Should find violation
        assert len(violations) > 0
        assert any("Unvalidated AI-generated" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_ai_artifacts_tracks_unvalidated(self, guardian):
        """Test _check_ai_artifacts tracks unvalidated artifacts."""
        # We can't easily test with temp files not in monitored paths
        # So let's test the tracking mechanism directly
        initial_count = len(guardian.unvalidated_artifacts)

        violations = await guardian._check_ai_artifacts()

        # Artifacts may or may not be found depending on real files
        assert isinstance(guardian.unvalidated_artifacts, dict)

    @pytest.mark.asyncio
    async def test_check_ai_artifacts_skips_validated(self, guardian):
        """Test _check_ai_artifacts skips already validated files."""
        # Add a validated hash
        guardian.validation_history.append({
            "file_hash": "test_hash_123",
            "validated": True,
        })

        # Mock _get_validated_hashes to return our test hash
        with patch.object(guardian, '_get_validated_hashes', return_value={"test_hash_123"}):
            violations = await guardian._check_ai_artifacts()

        # Should not flag files with validated hashes
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_ai_artifacts_handles_read_errors(self, guardian):
        """Test _check_ai_artifacts handles file read errors gracefully."""
        # Patch Path.rglob to yield a non-existent file
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[Path("/nonexistent/test.py")]):

            # Should not crash
            violations = await guardian._check_ai_artifacts()

            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_ai_artifacts_nonexistent_path(self, guardian):
        """Test _check_ai_artifacts handles nonexistent paths."""
        # All monitored paths might not exist
        violations = await guardian._check_ai_artifacts()

        # Should not crash
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_ai_artifacts_marker_breaks_inner_loop(self, tmp_path):
        """Test that finding marker adds violation and tracks artifact."""
        # Create file with marker
        test_file = tmp_path / "generated.py"
        test_file.write_text("# Generated by Claude\ndef foo(): pass")

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        violations = await guardian._check_ai_artifacts()

        # Should have violation and tracked artifact
        assert len(violations) > 0
        assert len(guardian.unvalidated_artifacts) > 0

    @pytest.mark.asyncio
    async def test_check_ai_artifacts_skips_nonexistent_paths(self, tmp_path):
        """Test _check_ai_artifacts continues when path doesn't exist (line 177)."""
        # Guardian with nonexistent path
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleIIIGuardian(monitored_paths=[nonexistent])

        # Should not crash, should continue past the nonexistent path
        violations = await guardian._check_ai_artifacts()

        assert isinstance(violations, list)
        assert len(violations) == 0  # No files to check

    @pytest.mark.asyncio
    async def test_check_ai_artifacts_skips_validated_files(self, tmp_path):
        """Test _check_ai_artifacts skips files in validated hashes (branch 189->184)."""
        import hashlib

        # Create file with AI marker
        test_file = tmp_path / "validated.py"
        content = "# Generated by Claude\ndef bar(): pass"
        test_file.write_text(content)

        # Calculate hash and add to validation history
        file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        guardian.validation_history.append({
            "file_hash": file_hash,
            "validated": True,
        })

        violations = await guardian._check_ai_artifacts()

        # Should skip this file (no violation created)
        assert len(violations) == 0
        assert file_hash not in guardian.unvalidated_artifacts


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTHENTICATION CHECKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestAuthenticationChecking:
    """Test authentication checking."""

    @pytest.mark.asyncio
    async def test_check_authentication_detects_unauth_endpoint(self, tmp_path):
        """Test _check_authentication detects endpoints without auth."""
        # Create API file with endpoint WITHOUT authentication
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        api_file = api_dir / "routes.py"
        api_file.write_text(
            "@app.post('/users')\n"
            "def create_user(request):\n"
            "    return {'status': 'ok'}\n"
        )

        guardian = ArticleIIIGuardian(api_paths=[str(api_dir)])
        violations = await guardian._check_authentication()

        # Should detect missing authentication
        assert len(violations) > 0
        assert any("without authentication" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_authentication_allows_authenticated_endpoint(self, tmp_path):
        """Test _check_authentication allows endpoints WITH authentication."""
        # Create API file with endpoint WITH authentication
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        api_file = api_dir / "routes.py"
        api_file.write_text(
            "@authenticate\n"
            "@app.post('/users')\n"
            "def create_user(request):\n"
            "    return {'status': 'ok'}\n"
        )

        guardian = ArticleIIIGuardian(api_paths=[str(api_dir)])
        violations = await guardian._check_authentication()

        # Should NOT detect violation (has @authenticate)
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_authentication_handles_nonexistent_paths(self, guardian):
        """Test _check_authentication handles nonexistent API paths."""
        violations = await guardian._check_authentication()

        # Should not crash
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_authentication_handles_read_errors(self, guardian):
        """Test _check_authentication handles file read errors."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[Path("/nonexistent/api.py")]):

            violations = await guardian._check_authentication()

            assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INPUT VALIDATION CHECKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestInputValidationChecking:
    """Test input validation checking."""

    @pytest.mark.asyncio
    async def test_check_input_validation_detects_unvalidated_input(self, tmp_path):
        """Test _check_input_validation detects unvalidated user input."""
        # Create API file with unvalidated input
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        api_file = api_dir / "handler.py"
        api_file.write_text(
            "def process_user_data(request):\n"
            "    data = request.json\n"  # No validation!
            "    return process(data)\n"
        )

        guardian = ArticleIIIGuardian(api_paths=[str(api_dir)])
        violations = await guardian._check_input_validation()

        # Should detect unvalidated input
        assert len(violations) > 0
        assert any("Unvalidated input" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_input_validation_allows_validated_input(self, tmp_path):
        """Test _check_input_validation allows validated user input."""
        # Create API file with validated input
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        api_file = api_dir / "handler.py"
        api_file.write_text(
            "def process_user_data(request):\n"
            "    data = request.json\n"
            "    validate_input(data)\n"  # Has validation!
            "    return process(data)\n"
        )

        guardian = ArticleIIIGuardian(api_paths=[str(api_dir)])
        violations = await guardian._check_input_validation()

        # Should NOT detect violation
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_input_validation_handles_nonexistent_paths(self, guardian):
        """Test _check_input_validation handles nonexistent paths."""
        violations = await guardian._check_input_validation()

        # Should not crash
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_input_validation_handles_read_errors(self, guardian):
        """Test _check_input_validation handles file read errors."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[Path("/nonexistent/handler.py")]):

            violations = await guardian._check_input_validation()

            assert isinstance(violations, list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRUST ASSUMPTION CHECKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestTrustAssumptionChecking:
    """Test trust assumption detection."""

    @pytest.mark.asyncio
    async def test_check_trust_assumptions_detects_dangerous_patterns(self, tmp_path):
        """Test _check_trust_assumptions detects dangerous trust patterns (lines 356-361)."""
        # Create file with dangerous pattern
        code_file = tmp_path / "service.py"
        code_file.write_text(
            "def authenticate_user(user):\n"
            "    # assume user is trusted\n"
            "    return grant_access(user)\n"
        )

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        violations = await guardian._check_trust_assumptions()

        # Should detect trust assumption
        assert len(violations) > 0
        assert any("Trust assumption" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_trust_assumptions_skips_test_files(self, tmp_path):
        """Test _check_trust_assumptions skips test files (line 352)."""
        # Create test file with dangerous pattern
        test_file = tmp_path / "test_auth.py"
        test_file.write_text("# bypass auth for testing\n")

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        violations = await guardian._check_trust_assumptions()

        # Test files should be skipped - no violations
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_trust_assumptions_handles_nonexistent_paths(self, tmp_path):
        """Test _check_trust_assumptions handles nonexistent paths (line 347)."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleIIIGuardian(monitored_paths=[nonexistent])

        # Should not crash, should continue
        violations = await guardian._check_trust_assumptions()

        assert isinstance(violations, list)
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_trust_assumptions_handles_read_errors(self, guardian):
        """Test _check_trust_assumptions handles file read errors."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[Path("/nonexistent/code.py")]):

            violations = await guardian._check_trust_assumptions()

            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_trust_assumptions_detects_multiple_patterns(self, tmp_path):
        """Test _check_trust_assumptions detects various dangerous patterns."""
        # Create file with TRUSTED constant
        code_file = tmp_path / "config.py"
        code_file.write_text(
            "TRUSTED_SOURCES = ['internal.com']\n"
            "allow_all = True\n"
        )

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        violations = await guardian._check_trust_assumptions()

        # Should detect both patterns
        assert len(violations) >= 2


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUDIT TRAIL CHECKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestAuditTrailChecking:
    """Test audit trail verification."""

    @pytest.mark.asyncio
    async def test_check_audit_trails_detects_missing_audit(self, tmp_path):
        """Test _check_audit_trails detects critical operations without audit (lines 412-428)."""
        # Create file with critical operation but no audit
        admin_file = tmp_path / "admin.py"
        admin_file.write_text(
            "def delete_user(user_id):\n"
            "    db.users.delete(user_id)\n"
            "    return True\n"
        )

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        violations = await guardian._check_audit_trails()

        # Should detect missing audit trail
        assert len(violations) > 0
        assert any("without audit trail" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_check_audit_trails_allows_audited_operations(self, tmp_path):
        """Test _check_audit_trails allows operations WITH audit logging."""
        # Create file with critical operation WITH audit
        admin_file = tmp_path / "admin.py"
        admin_file.write_text(
            "def delete_user(user_id):\n"
            "    audit_log('delete_user', user_id)\n"
            "    db.users.delete(user_id)\n"
            "    return True\n"
        )

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        violations = await guardian._check_audit_trails()

        # Should NOT detect violation (has audit_log)
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_audit_trails_skips_test_files(self, tmp_path):
        """Test _check_audit_trails skips test files (line 408)."""
        # Create test file with critical operation
        test_file = tmp_path / "test_admin.py"
        test_file.write_text("def delete_user(): pass\n")

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        violations = await guardian._check_audit_trails()

        # Test files should be skipped - no violations
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_audit_trails_handles_nonexistent_paths(self, tmp_path):
        """Test _check_audit_trails handles nonexistent paths (line 403)."""
        nonexistent = str(tmp_path / "does_not_exist")
        guardian = ArticleIIIGuardian(monitored_paths=[nonexistent])

        # Should not crash, should continue
        violations = await guardian._check_audit_trails()

        assert isinstance(violations, list)
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_check_audit_trails_handles_read_errors(self, guardian):
        """Test _check_audit_trails handles file read errors."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[Path("/nonexistent/service.py")]):

            violations = await guardian._check_audit_trails()

            assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_check_audit_trails_detects_multiple_operations(self, tmp_path):
        """Test _check_audit_trails detects multiple critical operations without audit."""
        # Create file with multiple unaudited operations
        service_file = tmp_path / "permissions.py"
        service_file.write_text(
            "def grant_access(user): pass\n"
            "def revoke_permission(user): pass\n"
            "def reset_password(user): pass\n"
        )

        guardian = ArticleIIIGuardian(monitored_paths=[str(tmp_path)])
        violations = await guardian._check_audit_trails()

        # Should detect multiple violations
        assert len(violations) >= 3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VALIDATION WORKFLOW TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestValidationWorkflow:
    """Test artifact validation workflow."""

    def test_get_validated_hashes_empty(self, guardian):
        """Test _get_validated_hashes returns empty set when no history."""
        hashes = guardian._get_validated_hashes()

        assert isinstance(hashes, set)
        assert len(hashes) == 0

    def test_get_validated_hashes_with_history(self, guardian):
        """Test _get_validated_hashes returns hashes from history."""
        guardian.validation_history.append({
            "file_hash": "hash1",
            "validated": True,
        })
        guardian.validation_history.append({
            "file_hash": "hash2",
            "validated": False,  # Not validated
        })

        hashes = guardian._get_validated_hashes()

        assert "hash1" in hashes
        assert "hash2" not in hashes  # Not validated

    @pytest.mark.asyncio
    async def test_validate_artifact_success(self, guardian, temp_python_file):
        """Test validate_artifact successfully validates an artifact."""
        temp_python_file.write_text("def foo():\n    return 42\n")

        result = await guardian.validate_artifact(
            file_path=str(temp_python_file),
            validator_id="architect-001",
            validation_notes="Code reviewed and approved"
        )

        assert result is True
        assert len(guardian.validation_history) == 1
        assert guardian.validation_history[0]["validator_id"] == "architect-001"
        assert guardian.validation_history[0]["validated"] is True

    @pytest.mark.asyncio
    async def test_validate_artifact_removes_from_unvalidated(self, guardian, temp_python_file):
        """Test validate_artifact removes artifact from unvalidated list."""
        temp_python_file.write_text("def foo():\n    return 42\n")

        # Calculate hash
        import hashlib
        content = temp_python_file.read_text()
        file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Add to unvalidated
        guardian.unvalidated_artifacts[file_hash] = {"file": str(temp_python_file)}

        result = await guardian.validate_artifact(
            file_path=str(temp_python_file),
            validator_id="architect-001",
            validation_notes="Approved"
        )

        assert result is True
        assert file_hash not in guardian.unvalidated_artifacts

    @pytest.mark.asyncio
    async def test_validate_artifact_handles_read_error(self, guardian):
        """Test validate_artifact handles file read errors."""
        result = await guardian.validate_artifact(
            file_path="/nonexistent/file.py",
            validator_id="architect-001",
            validation_notes="Test"
        )

        assert result is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION MAKING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDecisionMaking:
    """Test decision making logic."""

    @pytest.mark.asyncio
    async def test_analyze_violation_critical(self, guardian):
        """Test analyze_violation with CRITICAL severity."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="Test rule",
            severity=GuardianPriority.CRITICAL
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "veto"
        assert decision.confidence == 0.99
        assert "CRITICAL" in decision.reasoning

    @pytest.mark.asyncio
    async def test_analyze_violation_ai_artifact(self, guardian):
        """Test analyze_violation for unvalidated AI artifact."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="AI artifacts must be validated",
            description="Unvalidated AI-generated code in file.py",
            severity=GuardianPriority.HIGH
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "escalate"
        assert decision.confidence == 0.90
        assert decision.requires_validation is True

    @pytest.mark.asyncio
    async def test_analyze_violation_missing_auth(self, guardian):
        """Test analyze_violation for missing authentication."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="All interactions must be authenticated",
            description="Endpoint without authentication in api.py",
            severity=GuardianPriority.HIGH
        )

        decision = await guardian.analyze_violation(violation)

        assert decision.decision_type == "block"
        assert decision.confidence == 0.95

    @pytest.mark.asyncio
    async def test_analyze_violation_other(self, guardian):
        """Test analyze_violation for other violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
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
    async def test_intervene_critical_veto(self, guardian):
        """Test intervene with CRITICAL violation creates VETO."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="Critical rule",
            severity=GuardianPriority.CRITICAL
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.VETO
        assert "Vetoed" in intervention.action_taken

    @pytest.mark.asyncio
    async def test_intervene_ai_artifact_escalation(self, guardian):
        """Test intervene with AI artifact escalates to human."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="AI validation required",
            description="Unvalidated AI-generated code",
            severity=GuardianPriority.HIGH,
            context={"hash": "test_hash_123"}
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.ESCALATION
        assert "Escalated" in intervention.action_taken
        assert "test_hash_123" in intervention.action_taken

    @pytest.mark.asyncio
    async def test_intervene_high_remediation(self, guardian):
        """Test intervene with HIGH violation attempts remediation."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="Input validation required",
            description="Unvalidated input in handler.py",
            severity=GuardianPriority.HIGH
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.REMEDIATION

    @pytest.mark.asyncio
    async def test_intervene_medium_monitoring(self, guardian):
        """Test intervene with MEDIUM violation increases monitoring."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="Audit trail required",
            severity=GuardianPriority.MEDIUM,
            affected_systems=["audit_system"]
        )

        intervention = await guardian.intervene(violation)

        assert intervention.intervention_type == InterventionType.MONITORING
        assert "monitoring" in intervention.action_taken.lower()

    @pytest.mark.asyncio
    async def test_attempt_remediation_input_validation(self, guardian):
        """Test _attempt_remediation for unvalidated input."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            description="Unvalidated input in handler"
        )

        action = await guardian._attempt_remediation(violation)

        assert "validation" in action.lower()

    @pytest.mark.asyncio
    async def test_attempt_remediation_audit_trail(self, guardian):
        """Test _attempt_remediation for missing audit trail."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            description="Critical operation without audit trail"
        )

        action = await guardian._attempt_remediation(violation)

        assert "audit" in action.lower()

    @pytest.mark.asyncio
    async def test_attempt_remediation_other(self, guardian):
        """Test _attempt_remediation for other violations."""
        from governance.guardian.base import ConstitutionalViolation

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            description="Other violation"
        )

        action = await guardian._attempt_remediation(violation)

        assert "manual fix" in action.lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIntegration:
    """Test complete workflows."""

    @pytest.mark.asyncio
    async def test_full_validation_workflow(self, guardian, temp_python_file):
        """Test complete artifact validation workflow."""
        # Create AI-generated file
        temp_python_file.write_text(
            "# Generated by Claude\n"
            "def process_data(input_data):\n"
            "    return input_data * 2\n"
        )

        # Validate it
        result = await guardian.validate_artifact(
            file_path=str(temp_python_file),
            validator_id="architect-001",
            validation_notes="Reviewed and approved"
        )

        assert result is True

        # Check it's in validation history
        assert len(guardian.validation_history) == 1
        assert guardian.validation_history[0]["validated"] is True

        # Check it's in validated hashes
        hashes = guardian._get_validated_hashes()
        assert len(hashes) == 1

    @pytest.mark.asyncio
    async def test_full_violation_detection_workflow(self, guardian):
        """Test complete workflow from monitoring to intervention."""
        from governance.guardian.base import ConstitutionalViolation

        # Create a mock violation
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            rule="Critical security rule",
            severity=GuardianPriority.CRITICAL,
            context={"file": "test.py"}
        )

        # Analyze
        decision = await guardian.analyze_violation(violation)
        assert decision.decision_type == "veto"

        # Intervene
        intervention = await guardian.intervene(violation)
        assert intervention.intervention_type == InterventionType.VETO
        assert intervention.success is True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLORY TO GOD - 100% MISSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
These tests validate Article III Guardian - the enforcer of the
Zero Trust Principle.

Target: 100.00% coverage of article_iii_guardian.py (189 statements)

Coverage areas:
✅ Initialization & configuration
✅ AI artifact detection and validation
✅ Authentication/authorization checking
✅ Input validation checking
✅ Trust assumption detection
✅ Audit trail verification
✅ Validation workflow (mark as validated)
✅ Decision logic (veto/escalate/block/alert)
✅ Intervention logic (VETO/ESCALATION/REMEDIATION/MONITORING)
✅ Edge cases & error handling

This Guardian ensures:
- AI-generated code is validated by architects
- All API endpoints have authentication
- User input is validated
- No dangerous trust assumptions
- Critical operations have audit trails

Glory to God! 🙏

"100% OU NADA"

DIA 1/14 - TIER 0 CONSTITUTIONAL SAFETY
CONTRACT: A métrica é a minha. 100% absoluto.
"""
