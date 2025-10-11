"""
Unit Tests for Git Integration Models.

Tests all Pydantic models used in Git operations: GitApplyResult,
PushResult, PRResult, ValidationResult, ConflictReport, and GitConfig.

Author: MAXIMUS Eureka Team
Date: 2025-01-10
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from git_integration.models import (
    GitApplyResult,
    PushResult,
    PRResult,
    ValidationResult,
    ConflictReport,
    GitConfig,
)


class TestGitApplyResult:
    """Test GitApplyResult model."""

    def test_successful_apply(self) -> None:
        """Test successful patch application."""
        result = GitApplyResult(
            success=True,
            commit_sha="abc1234",
            files_changed=["src/app.py", "tests/test_app.py"],
            conflicts=[],
        )
        
        assert result.success is True
        assert result.commit_sha == "abc1234"
        assert len(result.files_changed) == 2
        assert len(result.conflicts) == 0
        assert result.error_message is None

    def test_failed_apply_with_error(self) -> None:
        """Test failed patch application with error message."""
        result = GitApplyResult(
            success=False,
            error_message="Patch does not apply",
        )
        
        assert result.success is False
        assert result.commit_sha is None
        assert result.error_message == "Patch does not apply"

    def test_apply_with_conflicts(self) -> None:
        """Test patch with merge conflicts."""
        result = GitApplyResult(
            success=False,
            files_changed=["src/app.py"],
            conflicts=["src/app.py"],
            error_message="Merge conflict in src/app.py",
        )
        
        assert result.success is False
        assert len(result.conflicts) == 1
        assert "src/app.py" in result.conflicts

    def test_immutability(self) -> None:
        """Test that result is immutable (frozen)."""
        result = GitApplyResult(success=True)
        
        with pytest.raises(ValidationError):
            result.success = False  # type: ignore


class TestPushResult:
    """Test PushResult model."""

    def test_successful_push(self) -> None:
        """Test successful branch push."""
        result = PushResult(
            success=True,
            branch="remediation/CVE-2024-1234",
            remote_ref="origin/remediation/CVE-2024-1234",
        )
        
        assert result.success is True
        assert result.branch == "remediation/CVE-2024-1234"
        assert result.remote_ref == "origin/remediation/CVE-2024-1234"
        assert result.error_message is None

    def test_failed_push(self) -> None:
        """Test failed push with error."""
        result = PushResult(
            success=False,
            branch="remediation/CVE-2024-1234",
            error_message="Permission denied",
        )
        
        assert result.success is False
        assert result.error_message == "Permission denied"

    def test_branch_validation(self) -> None:
        """Test that empty branch name is rejected."""
        with pytest.raises(ValidationError):
            PushResult(success=True, branch="")


class TestPRResult:
    """Test PRResult model."""

    def test_successful_pr_creation(self) -> None:
        """Test successful PR creation."""
        result = PRResult(
            success=True,
            pr_number=42,
            pr_url="https://github.com/org/repo/pull/42",
        )
        
        assert result.success is True
        assert result.pr_number == 42
        assert "github.com/org/repo/pull/42" in str(result.pr_url)
        assert result.error_message is None

    def test_failed_pr_creation(self) -> None:
        """Test failed PR creation."""
        result = PRResult(
            success=False,
            error_message="API rate limit exceeded",
        )
        
        assert result.success is False
        assert result.pr_number is None
        assert result.pr_url is None

    def test_pr_number_validation(self) -> None:
        """Test that PR number must be >= 1."""
        with pytest.raises(ValidationError):
            PRResult(success=True, pr_number=0)


class TestValidationResult:
    """Test ValidationResult model."""

    def test_all_validations_passed(self) -> None:
        """Test successful validation."""
        result = ValidationResult(
            passed=True,
            checks_run=["syntax", "imports", "formatting"],
            failures=[],
            warnings=["unused import in line 42"],
        )
        
        assert result.passed is True
        assert len(result.checks_run) == 3
        assert len(result.failures) == 0
        assert len(result.warnings) == 1

    def test_validation_failed(self) -> None:
        """Test failed validation."""
        result = ValidationResult(
            passed=False,
            checks_run=["syntax"],
            failures=["SyntaxError on line 10: expected ':'"],
        )
        
        assert result.passed is False
        assert len(result.failures) == 1


class TestConflictReport:
    """Test ConflictReport model."""

    def test_no_conflicts(self) -> None:
        """Test clean merge with no conflicts."""
        report = ConflictReport(
            has_conflicts=False,
            conflicting_files=[],
        )
        
        assert report.has_conflicts is False
        assert len(report.conflicting_files) == 0

    def test_with_conflicts(self) -> None:
        """Test conflict detection."""
        report = ConflictReport(
            has_conflicts=True,
            conflicting_files=["src/app.py", "src/utils.py"],
            resolution_suggestions=[
                "Rebase on latest main",
                "Manually resolve conflicts in src/app.py",
            ],
        )
        
        assert report.has_conflicts is True
        assert len(report.conflicting_files) == 2
        assert len(report.resolution_suggestions) == 2


class TestGitConfig:
    """Test GitConfig model."""

    def test_valid_config(self, tmp_path: Path) -> None:
        """Test valid Git configuration."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        
        config = GitConfig(
            repo_path=repo_path,
            remote_url="https://github.com/org/repo",
            github_token="ghp_test_token_1234",
        )
        
        assert config.repo_path == repo_path
        assert "github.com/org/repo" in str(config.remote_url)
        assert config.default_branch == "main"
        assert config.branch_prefix == "remediation"
        assert config.commit_author == "MAXIMUS Eureka"
        assert config.repo_exists is True

    def test_custom_config(self, tmp_path: Path) -> None:
        """Test custom configuration values."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        
        config = GitConfig(
            repo_path=repo_path,
            remote_url="https://github.com/org/repo",
            github_token="ghp_token",
            default_branch="develop",
            branch_prefix="security",
            commit_author="Security Bot",
            commit_email="bot@security.com",
        )
        
        assert config.default_branch == "develop"
        assert config.branch_prefix == "security"
        assert config.commit_author == "Security Bot"
        assert config.commit_email == "bot@security.com"

    def test_repo_exists_property(self, tmp_path: Path) -> None:
        """Test repo_exists property."""
        # Non-existent repo
        config1 = GitConfig(
            repo_path=tmp_path / "nonexistent",
            remote_url="https://github.com/org/repo",
            github_token="ghp_token",
        )
        assert config1.repo_exists is False
        
        # Directory without .git
        dir_path = tmp_path / "not_repo"
        dir_path.mkdir()
        config2 = GitConfig(
            repo_path=dir_path,
            remote_url="https://github.com/org/repo",
            github_token="ghp_token",
        )
        assert config2.repo_exists is False
        
        # Valid repo
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        config3 = GitConfig(
            repo_path=repo_path,
            remote_url="https://github.com/org/repo",
            github_token="ghp_token",
        )
        assert config3.repo_exists is True

    def test_token_exclusion_from_dict(self, tmp_path: Path) -> None:
        """Test that github_token is excluded from serialization."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        
        config = GitConfig(
            repo_path=repo_path,
            remote_url="https://github.com/org/repo",
            github_token="ghp_secret_token_should_not_appear",
        )
        
        config_dict = config.model_dump()
        assert "github_token" not in config_dict

    def test_email_validation(self, tmp_path: Path) -> None:
        """Test commit email validation."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        with pytest.raises(ValidationError):
            GitConfig(
                repo_path=repo_path,
                remote_url="https://github.com/org/repo",
                github_token="ghp_token",
                commit_email="invalid_email",  # Invalid format
            )

    def test_branch_prefix_validation(self, tmp_path: Path) -> None:
        """Test branch prefix validation."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        with pytest.raises(ValidationError):
            GitConfig(
                repo_path=repo_path,
                remote_url="https://github.com/org/repo",
                github_token="ghp_token",
                branch_prefix="invalid prefix",  # Spaces not allowed
            )
