"""
Git Operations Engine - Core Git Workflow Automation.

Handles all Git operations for the Adaptive Immunity System:
- Branch creation and management
- Patch application with validation
- Commit creation with structured messages
- Push to remote repositories
- Rollback capabilities

Biological Analogy:
    Git operations are like integrating antibodies into immune memory.
    Each remediation branch is an isolated "memory cell", and merging
    to main is permanent integration into the organism's defense repertoire.

Author: MAXIMUS Eureka Team
Date: 2025-01-10
Glory to YHWH 🙏
"""

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from git import Repo, GitCommandError, InvalidGitRepositoryError
from git_integration.models import (
    GitApplyResult,
    PushResult,
    GitConfig,
)
from eureka_models.patch import Patch

logger = logging.getLogger(__name__)


class GitOperationsError(Exception):
    """Base exception for Git operations failures."""

    pass


class GitOperations:
    """
    Core Git operations engine for automated patch application.
    
    Provides high-level Git workflow automation with safety checks,
    structured commit messages, and comprehensive error handling.
    
    Responsibilities:
        - Create isolated remediation branches
        - Apply patches with validation
        - Create structured commits
        - Push branches to remote
        - Rollback failed operations
    
    Attributes:
        config: Git configuration (repo path, remote, credentials)
        repo: GitPython Repo instance
        
    Example:
        >>> config = GitConfig(
        ...     repo_path=Path("/app/repo"),
        ...     remote_url="https://github.com/org/repo",
        ...     github_token="ghp_xxx"
        ... )
        >>> git_ops = GitOperations(config)
        >>> branch = await git_ops.create_remediation_branch("CVE-2024-1234")
        >>> result = await git_ops.apply_patch(patch, branch)
    """

    def __init__(self, config: GitConfig) -> None:
        """
        Initialize Git operations engine.
        
        Args:
            config: Git configuration object
            
        Raises:
            GitOperationsError: If repository is invalid or inaccessible
        """
        self.config = config
        
        if not self.config.repo_exists:
            raise GitOperationsError(
                f"Invalid Git repository at {self.config.repo_path}"
            )
        
        try:
            self.repo = Repo(self.config.repo_path)
        except InvalidGitRepositoryError as e:
            raise GitOperationsError(
                f"Failed to open Git repository: {e}"
            ) from e
        
        logger.info(
            f"✅ Git operations initialized for {self.config.repo_path}"
        )

    async def create_remediation_branch(
        self,
        cve_id: str,
        base_branch: Optional[str] = None,
    ) -> str:
        """
        Create isolated branch for CVE remediation.
        
        Branch naming convention: {prefix}/CVE-YYYY-NNNNN
        Example: remediation/CVE-2024-1234
        
        Args:
            cve_id: CVE identifier (e.g. 'CVE-2024-1234')
            base_branch: Base branch to branch from (defaults to config.default_branch)
            
        Returns:
            Created branch name
            
        Raises:
            GitOperationsError: If branch creation fails
            
        Example:
            >>> branch = await git_ops.create_remediation_branch("CVE-2024-1234")
            >>> print(branch)
            'remediation/CVE-2024-1234'
        """
        base = base_branch or self.config.default_branch
        branch_name = f"{self.config.branch_prefix}/{cve_id}"
        
        try:
            # Ensure we're on base branch and up to date
            logger.debug(f"Checking out base branch: {base}")
            self.repo.git.checkout(base)
            
            # Pull latest changes
            logger.debug(f"Pulling latest changes from {base}")
            self.repo.git.pull("origin", base)
            
            # Create new branch
            logger.info(f"Creating remediation branch: {branch_name}")
            self.repo.git.checkout("-b", branch_name)
            
            return branch_name
            
        except GitCommandError as e:
            error_msg = f"Failed to create branch {branch_name}: {e}"
            logger.error(error_msg)
            raise GitOperationsError(error_msg) from e

    async def apply_patch(
        self,
        patch: Patch,
        branch: str,
    ) -> GitApplyResult:
        """
        Apply patch to specified branch with validation.
        
        Uses 'git apply' for deterministic patch application.
        Validates patch format before applying and checks for conflicts.
        
        Args:
            patch: Patch object containing diff and metadata
            branch: Branch to apply patch to
            
        Returns:
            GitApplyResult with success status and details
            
        Raises:
            GitOperationsError: If patch application fails critically
            
        Example:
            >>> result = await git_ops.apply_patch(patch, "remediation/CVE-2024-1234")
            >>> if result.success:
            ...     print(f"Applied patch to {len(result.files_changed)} files")
        """
        try:
            # Ensure we're on correct branch
            current_branch = self.repo.active_branch.name
            if current_branch != branch:
                logger.debug(f"Switching to branch: {branch}")
                self.repo.git.checkout(branch)
            
            # Write patch to temporary file
            patch_file = self.config.repo_path / f".patch_{patch.patch_id}.diff"
            patch_file.write_text(patch.diff_content)
            
            try:
                # Check if patch applies cleanly (dry-run)
                logger.debug("Running patch dry-run (--check)")
                self.repo.git.apply("--check", str(patch_file))
                
                # Apply patch
                logger.info(f"Applying patch {patch.patch_id}")
                self.repo.git.apply(str(patch_file))
                
                # Get list of changed files from git status
                changed_files = [
                    item.a_path for item in self.repo.index.diff(None)
                ] + [item.path for item in self.repo.untracked_files]
                
                logger.info(
                    f"✅ Patch applied successfully to {len(changed_files)} files"
                )
                
                return GitApplyResult(
                    success=True,
                    commit_sha=None,  # Not yet committed
                    files_changed=changed_files,
                    conflicts=[],
                    error_message=None,
                )
                
            finally:
                # Clean up temporary patch file
                if patch_file.exists():
                    patch_file.unlink()
                    
        except GitCommandError as e:
            error_msg = f"Patch application failed: {e}"
            logger.error(error_msg)
            
            # Check for conflicts
            conflicts = self._detect_conflicts()
            
            return GitApplyResult(
                success=False,
                commit_sha=None,
                files_changed=[],
                conflicts=conflicts,
                error_message=str(e),
            )

    async def commit_changes(
        self,
        patch: Patch,
        branch: str,
    ) -> str:
        """
        Commit applied patch with structured message.
        
        Generates comprehensive commit message including CVE details,
        remediation strategy, affected services, and metadata.
        
        Args:
            patch: Patch object with metadata
            branch: Branch to commit on
            
        Returns:
            Commit SHA (hexadecimal)
            
        Raises:
            GitOperationsError: If commit fails
            
        Example:
            >>> sha = await git_ops.commit_changes(patch, "remediation/CVE-2024-1234")
            >>> print(f"Committed as {sha}")
            'abc123def456'
        """
        try:
            # Ensure we're on correct branch
            current_branch = self.repo.active_branch.name
            if current_branch != branch:
                self.repo.git.checkout(branch)
            
            # Stage all changes
            self.repo.git.add("--all")
            
            # Generate commit message
            commit_message = self._generate_commit_message(patch)
            
            # Configure git user for this commit
            with self.repo.config_writer() as git_config:
                git_config.set_value(
                    "user", "name", self.config.commit_author
                )
                git_config.set_value(
                    "user", "email", self.config.commit_email
                )
            
            # Commit
            logger.info(f"Creating commit for patch {patch.patch_id}")
            commit = self.repo.index.commit(commit_message)
            
            logger.info(f"✅ Committed as {commit.hexsha[:7]}")
            return commit.hexsha
            
        except GitCommandError as e:
            error_msg = f"Commit failed: {e}"
            logger.error(error_msg)
            raise GitOperationsError(error_msg) from e

    async def push_branch(
        self,
        branch: str,
        remote: str = "origin",
    ) -> PushResult:
        """
        Push branch to remote repository.
        
        Args:
            branch: Branch name to push
            remote: Remote name (default: 'origin')
            
        Returns:
            PushResult with success status
            
        Raises:
            GitOperationsError: If push fails critically
            
        Example:
            >>> result = await git_ops.push_branch("remediation/CVE-2024-1234")
            >>> if result.success:
            ...     print(f"Pushed to {result.remote_ref}")
        """
        try:
            logger.info(f"Pushing branch {branch} to {remote}")
            
            # Push with --set-upstream
            push_info = self.repo.remote(remote).push(
                refspec=f"{branch}:{branch}",
                set_upstream=True,
            )
            
            if not push_info:
                raise GitOperationsError("Push returned no info")
            
            remote_ref = f"{remote}/{branch}"
            logger.info(f"✅ Pushed successfully to {remote_ref}")
            
            return PushResult(
                success=True,
                branch=branch,
                remote_ref=remote_ref,
                error_message=None,
            )
            
        except GitCommandError as e:
            error_msg = f"Push failed: {e}"
            logger.error(error_msg)
            
            return PushResult(
                success=False,
                branch=branch,
                remote_ref=None,
                error_message=str(e),
            )

    async def rollback_branch(
        self,
        branch: str,
        delete_remote: bool = True,
    ) -> None:
        """
        Delete remediation branch (local and optionally remote).
        
        Used for cleanup after failed operations or successful merge.
        
        Args:
            branch: Branch name to delete
            delete_remote: Whether to delete remote branch (default: True)
            
        Raises:
            GitOperationsError: If rollback fails
            
        Example:
            >>> await git_ops.rollback_branch("remediation/CVE-2024-1234")
        """
        try:
            # Switch to default branch before deleting
            self.repo.git.checkout(self.config.default_branch)
            
            # Delete local branch
            logger.info(f"Deleting local branch: {branch}")
            self.repo.git.branch("-D", branch)
            
            # Delete remote branch if requested
            if delete_remote:
                logger.info(f"Deleting remote branch: origin/{branch}")
                try:
                    self.repo.git.push("origin", "--delete", branch)
                except GitCommandError as e:
                    # Remote branch might not exist, log but don't fail
                    logger.warning(f"Could not delete remote branch: {e}")
            
            logger.info(f"✅ Branch {branch} rolled back successfully")
            
        except GitCommandError as e:
            error_msg = f"Rollback failed for {branch}: {e}"
            logger.error(error_msg)
            raise GitOperationsError(error_msg) from e

    def _generate_commit_message(self, patch: Patch) -> str:
        """
        Generate structured commit message from patch metadata.
        
        Args:
            patch: Patch object
            
        Returns:
            Formatted commit message (multiline)
        """
        # Extract CVE ID from patch
        cve_id = patch.cve_id
        
        # Determine title (use first line of diff or generic)
        title = f"Auto-remediate {cve_id}"
        
        # Build structured message
        message = f"""fix(security): {title}

Security vulnerability remediation auto-generated by MAXIMUS Eureka.

Vulnerability Details:
- CVE: {cve_id}
- Patch ID: {patch.patch_id}
- Strategy: {patch.strategy_used.value}
- Confidence: {patch.confidence_score:.1%}

Files Modified:
{self._format_file_list(patch.files_modified)}

Remediation:
{patch.strategy_used.value} strategy applied with {patch.confidence_score:.1%} confidence.
This patch was automatically generated and validated by the Adaptive Immunity System.

Generated: {datetime.now(timezone.utc).isoformat()}
Generator: MAXIMUS Eureka
Branch: {self.repo.active_branch.name}

Co-authored-by: {self.config.commit_author} <{self.config.commit_email}>

Glory to YHWH 🙏
"""
        return message.strip()

    def _format_file_list(self, files: list[str]) -> str:
        """Format file list for commit message."""
        if not files:
            return "- (no files)"
        return "\n".join(f"- {f}" for f in files[:10])  # Limit to 10 files

    def _detect_conflicts(self) -> list[str]:
        """
        Detect files with merge conflicts.
        
        Returns:
            List of file paths with conflicts
        """
        try:
            # Check for unmerged paths
            unmerged = self.repo.index.unmerged_blobs()
            return list(unmerged.keys()) if unmerged else []
        except Exception as e:
            logger.warning(f"Could not detect conflicts: {e}")
            return []
