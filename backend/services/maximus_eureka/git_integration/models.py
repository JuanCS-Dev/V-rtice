"""
Git Integration Models - Type Definitions.

Pydantic models for Git operations, PR creation, and validation results.
All models follow the MAXIMUS quality standards: 100% type hints,
comprehensive docstrings, immutable by default.

Author: MAXIMUS Eureka Team
Date: 2025-01-10
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class GitApplyResult(BaseModel):
    """
    Result of a git apply operation.
    
    Captures the outcome of applying a patch to a Git repository,
    including success status, commit SHA, files changed, and any
    conflicts encountered.
    
    Attributes:
        success: Whether patch was applied successfully
        commit_sha: Git commit SHA if committed (None if not yet committed)
        files_changed: List of file paths modified by patch
        conflicts: List of files with merge conflicts (empty if none)
        error_message: Error description if success=False
        
    Example:
        >>> result = GitApplyResult(
        ...     success=True,
        ...     commit_sha="abc123",
        ...     files_changed=["src/app.py"],
        ...     conflicts=[]
        ... )
    """

    model_config = ConfigDict(frozen=True)

    success: bool = Field(
        ...,
        description="Whether patch application succeeded",
    )
    commit_sha: Optional[str] = Field(
        default=None,
        description="Git commit SHA (None if not yet committed)",
        pattern=r"^[a-f0-9]{7,40}$|^$",
    )
    files_changed: list[str] = Field(
        default_factory=list,
        description="List of file paths modified by patch",
    )
    conflicts: list[str] = Field(
        default_factory=list,
        description="Files with merge conflicts (empty if none)",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error description if success=False",
    )


class PushResult(BaseModel):
    """
    Result of a git push operation.
    
    Captures outcome of pushing a branch to remote repository,
    including success status and remote reference.
    
    Attributes:
        success: Whether push succeeded
        branch: Local branch name that was pushed
        remote_ref: Remote reference (e.g. 'origin/remediation/CVE-123')
        error_message: Error description if success=False
        
    Example:
        >>> result = PushResult(
        ...     success=True,
        ...     branch="remediation/CVE-2024-1234",
        ...     remote_ref="origin/remediation/CVE-2024-1234"
        ... )
    """

    model_config = ConfigDict(frozen=True)

    success: bool = Field(
        ...,
        description="Whether push operation succeeded",
    )
    branch: str = Field(
        ...,
        description="Local branch name that was pushed",
        min_length=1,
    )
    remote_ref: Optional[str] = Field(
        default=None,
        description="Remote reference (e.g. 'origin/remediation/CVE-123')",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error description if success=False",
    )


class PRResult(BaseModel):
    """
    Result of GitHub Pull Request creation.
    
    Captures outcome of PR creation via GitHub API, including
    PR number and URL for tracking.
    
    Attributes:
        success: Whether PR was created successfully
        pr_number: GitHub PR number (None if creation failed)
        pr_url: Full URL to PR on GitHub (None if creation failed)
        error_message: Error description if success=False
        
    Example:
        >>> result = PRResult(
        ...     success=True,
        ...     pr_number=42,
        ...     pr_url="https://github.com/org/repo/pull/42"
        ... )
    """

    model_config = ConfigDict(frozen=True)

    success: bool = Field(
        ...,
        description="Whether PR creation succeeded",
    )
    pr_number: Optional[int] = Field(
        default=None,
        description="GitHub PR number (None if creation failed)",
        ge=1,
    )
    pr_url: Optional[HttpUrl] = Field(
        default=None,
        description="Full URL to PR on GitHub",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error description if success=False",
    )


class ValidationResult(BaseModel):
    """
    Result of safety validation checks.
    
    Aggregates results from multiple validation checks (syntax,
    imports, formatting, etc.) into a single pass/fail result
    with detailed failure and warning information.
    
    Attributes:
        passed: Whether all validations passed
        checks_run: List of validation check names executed
        failures: List of failed check descriptions
        warnings: List of warning messages (non-blocking)
        
    Example:
        >>> result = ValidationResult(
        ...     passed=True,
        ...     checks_run=["syntax", "imports", "formatting"],
        ...     failures=[],
        ...     warnings=["unused import in line 42"]
        ... )
    """

    model_config = ConfigDict(frozen=True)

    passed: bool = Field(
        ...,
        description="Whether all validations passed",
    )
    checks_run: list[str] = Field(
        default_factory=list,
        description="List of validation check names executed",
    )
    failures: list[str] = Field(
        default_factory=list,
        description="List of failed check descriptions",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of warning messages (non-blocking)",
    )


class ConflictReport(BaseModel):
    """
    Merge conflict detection report.
    
    Analyzes patch for potential merge conflicts with target branch,
    providing list of conflicting files and resolution suggestions.
    
    Attributes:
        has_conflicts: Whether any conflicts were detected
        conflicting_files: List of files with conflicts
        resolution_suggestions: AI-generated suggestions for conflict resolution
        
    Example:
        >>> report = ConflictReport(
        ...     has_conflicts=True,
        ...     conflicting_files=["src/app.py"],
        ...     resolution_suggestions=["Rebase on latest main"]
        ... )
    """

    model_config = ConfigDict(frozen=True)

    has_conflicts: bool = Field(
        ...,
        description="Whether any merge conflicts were detected",
    )
    conflicting_files: list[str] = Field(
        default_factory=list,
        description="List of file paths with conflicts",
    )
    resolution_suggestions: list[str] = Field(
        default_factory=list,
        description="AI-generated suggestions for resolving conflicts",
    )


class GitConfig(BaseModel):
    """
    Git integration configuration.
    
    Centralized configuration for Git operations, including
    repository paths, remote URLs, authentication, and commit metadata.
    
    Attributes:
        repo_path: Absolute path to local Git repository
        remote_url: URL of remote repository
        default_branch: Default base branch (usually 'main' or 'develop')
        branch_prefix: Prefix for remediation branches (e.g. 'remediation')
        github_token: GitHub Personal Access Token (excluded from serialization)
        commit_author: Name used in commit metadata
        commit_email: Email used in commit metadata
        
    Security:
        github_token is marked with exclude=True to prevent accidental
        logging or serialization of sensitive credentials.
        
    Example:
        >>> config = GitConfig(
        ...     repo_path=Path("/app/repo"),
        ...     remote_url="https://github.com/org/repo",
        ...     github_token="ghp_xxxxx",
        ...     commit_author="MAXIMUS Eureka",
        ...     commit_email="eureka@maximus.ai"
        ... )
    """

    model_config = ConfigDict(frozen=False)  # Mutable for runtime updates

    repo_path: Path = Field(
        ...,
        description="Absolute path to local Git repository",
    )
    remote_url: HttpUrl = Field(
        ...,
        description="URL of remote Git repository",
    )
    default_branch: str = Field(
        default="main",
        description="Default base branch name",
        pattern=r"^[a-zA-Z0-9/_-]+$",
    )
    branch_prefix: str = Field(
        default="remediation",
        description="Prefix for auto-remediation branches",
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    github_token: str = Field(
        ...,
        description="GitHub Personal Access Token",
        exclude=True,  # SECURITY: Never serialize/log token
        min_length=4,
    )
    commit_author: str = Field(
        default="MAXIMUS Eureka",
        description="Git commit author name",
        min_length=1,
    )
    commit_email: str = Field(
        default="eureka@maximus.ai",
        description="Git commit author email",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )

    @property
    def repo_exists(self) -> bool:
        """Check if repository path exists and is a Git repo."""
        return (
            self.repo_path.exists()
            and (self.repo_path / ".git").is_dir()
        )
