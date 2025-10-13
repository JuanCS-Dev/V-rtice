"""
GitHub Client - Automated Pull Request creation.

Creates security fix PRs with:
- Branch creation
- Commit with patch
- PR creation with rich description
- Labels and reviewers
- Status checks integration
"""

import asyncio
import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GitHubRepository(BaseModel):
    """GitHub repository information."""

    owner: str
    repo: str
    default_branch: str = "main"


class PullRequest(BaseModel):
    """GitHub Pull Request information."""

    number: int
    html_url: str
    title: str
    state: str
    created_at: datetime
    updated_at: datetime


class GitHubClient:
    """
    GitHub API client for automated PR creation.

    Features:
    - Branch management
    - File modifications via API
    - PR creation with templates
    - Labels and reviewers
    - Status checks
    """

    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        github_token: str,
        repository: GitHubRepository,
    ):
        """
        Initialize GitHub client.

        Args:
            github_token: GitHub Personal Access Token with repo scope
            repository: GitHubRepository instance
        """
        self.github_token = github_token
        self.repository = repository

        logger.info(
            f"GitHubClient initialized: {repository.owner}/{repository.repo}"
        )

    async def create_security_fix_pr(
        self,
        branch_name: str,
        commit_message: str,
        pr_title: str,
        pr_body: str,
        file_changes: Dict[str, str],
        labels: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
    ) -> PullRequest:
        """
        Create pull request with security fix.

        Args:
            branch_name: Branch name for PR (e.g., "fix/cve-2021-44228")
            commit_message: Commit message
            pr_title: PR title
            pr_body: PR description (markdown)
            file_changes: Dictionary mapping file paths to new content
            labels: Optional PR labels
            reviewers: Optional reviewers

        Returns:
            PullRequest instance

        Raises:
            RuntimeError: If PR creation fails
        """
        logger.info(f"🔀 Creating security fix PR: {branch_name}")

        # Step 1: Get base branch SHA
        base_sha = await self._get_branch_sha(self.repository.default_branch)

        # Step 2: Create new branch
        await self._create_branch(branch_name, base_sha)
        logger.info(f"✅ Created branch: {branch_name}")

        # Step 3: Commit file changes
        commit_sha = await self._commit_changes(
            branch_name, file_changes, commit_message
        )
        logger.info(f"✅ Committed changes: {commit_sha[:8]}")

        # Step 4: Create pull request
        pr = await self._create_pull_request(
            branch_name,
            self.repository.default_branch,
            pr_title,
            pr_body,
        )
        logger.info(f"✅ Created PR #{pr.number}: {pr.html_url}")

        # Step 5: Add labels if provided
        if labels:
            await self._add_labels(pr.number, labels)
            logger.info(f"✅ Added labels: {', '.join(labels)}")

        # Step 6: Request reviewers if provided
        if reviewers:
            await self._request_reviewers(pr.number, reviewers)
            logger.info(f"✅ Requested reviewers: {', '.join(reviewers)}")

        return pr

    async def _get_branch_sha(self, branch_name: str) -> str:
        """
        Get SHA of branch HEAD.

        Args:
            branch_name: Branch name

        Returns:
            Commit SHA
        """
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/git/ref/heads/{branch_name}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to get branch SHA: {error}")

                data = await response.json()
                return data["object"]["sha"]

    async def _create_branch(self, branch_name: str, base_sha: str) -> None:
        """
        Create new branch.

        Args:
            branch_name: Branch name
            base_sha: Base commit SHA
        """
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/git/refs"
        )

        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status not in [201, 422]:  # 422 = already exists
                    error = await response.text()
                    raise RuntimeError(f"Failed to create branch: {error}")

                if response.status == 422:
                    logger.warning(f"Branch {branch_name} already exists")

    async def _commit_changes(
        self,
        branch_name: str,
        file_changes: Dict[str, str],
        commit_message: str,
    ) -> str:
        """
        Commit file changes to branch.

        Args:
            branch_name: Branch name
            file_changes: Dictionary mapping file paths to content
            commit_message: Commit message

        Returns:
            Commit SHA
        """
        # Get current tree SHA
        branch_sha = await self._get_branch_sha(branch_name)
        tree_sha = await self._get_commit_tree(branch_sha)

        # Create blobs for each file
        blob_shas = {}
        for file_path, content in file_changes.items():
            blob_sha = await self._create_blob(content)
            blob_shas[file_path] = blob_sha

        # Create new tree
        new_tree_sha = await self._create_tree(tree_sha, blob_shas)

        # Create commit
        commit_sha = await self._create_commit(
            commit_message, new_tree_sha, [branch_sha]
        )

        # Update branch reference
        await self._update_ref(branch_name, commit_sha)

        return commit_sha

    async def _get_commit_tree(self, commit_sha: str) -> str:
        """Get tree SHA from commit."""
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/git/commits/{commit_sha}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to get commit tree: {error}")

                data = await response.json()
                return data["tree"]["sha"]

    async def _create_blob(self, content: str) -> str:
        """Create blob for file content."""
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/git/blobs"
        )

        # Encode content as base64
        content_b64 = base64.b64encode(content.encode()).decode()

        payload = {
            "content": content_b64,
            "encoding": "base64",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    raise RuntimeError(f"Failed to create blob: {error}")

                data = await response.json()
                return data["sha"]

    async def _create_tree(
        self, base_tree_sha: str, blob_shas: Dict[str, str]
    ) -> str:
        """Create tree with file changes."""
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/git/trees"
        )

        tree_items = [
            {
                "path": file_path,
                "mode": "100644",  # Regular file
                "type": "blob",
                "sha": blob_sha,
            }
            for file_path, blob_sha in blob_shas.items()
        ]

        payload = {
            "base_tree": base_tree_sha,
            "tree": tree_items,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    raise RuntimeError(f"Failed to create tree: {error}")

                data = await response.json()
                return data["sha"]

    async def _create_commit(
        self, message: str, tree_sha: str, parent_shas: List[str]
    ) -> str:
        """Create commit."""
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/git/commits"
        )

        payload = {
            "message": message,
            "tree": tree_sha,
            "parents": parent_shas,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    raise RuntimeError(f"Failed to create commit: {error}")

                data = await response.json()
                return data["sha"]

    async def _update_ref(self, branch_name: str, commit_sha: str) -> None:
        """Update branch reference to new commit."""
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/git/refs/heads/{branch_name}"
        )

        payload = {
            "sha": commit_sha,
            "force": False,
        }

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to update ref: {error}")

    async def _create_pull_request(
        self,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> PullRequest:
        """Create pull request."""
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/pulls"
        )

        payload = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body,
            "maintainer_can_modify": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    raise RuntimeError(f"Failed to create PR: {error}")

                data = await response.json()

                return PullRequest(
                    number=data["number"],
                    html_url=data["html_url"],
                    title=data["title"],
                    state=data["state"],
                    created_at=datetime.fromisoformat(
                        data["created_at"].replace("Z", "+00:00")
                    ),
                    updated_at=datetime.fromisoformat(
                        data["updated_at"].replace("Z", "+00:00")
                    ),
                )

    async def _add_labels(self, pr_number: int, labels: List[str]) -> None:
        """Add labels to pull request."""
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/issues/{pr_number}/labels"
        )

        payload = {"labels": labels}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.warning(f"Failed to add labels: {error}")

    async def _request_reviewers(
        self, pr_number: int, reviewers: List[str]
    ) -> None:
        """Request reviewers for pull request."""
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/pulls/{pr_number}/requested_reviewers"
        )

        payload = {"reviewers": reviewers}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    logger.warning(f"Failed to request reviewers: {error}")

    async def get_pull_request(self, pr_number: int) -> PullRequest:
        """
        Get pull request by number.

        Args:
            pr_number: PR number

        Returns:
            PullRequest instance
        """
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/pulls/{pr_number}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to get PR: {error}")

                data = await response.json()

                return PullRequest(
                    number=data["number"],
                    html_url=data["html_url"],
                    title=data["title"],
                    state=data["state"],
                    created_at=datetime.fromisoformat(
                        data["created_at"].replace("Z", "+00:00")
                    ),
                    updated_at=datetime.fromisoformat(
                        data["updated_at"].replace("Z", "+00:00")
                    ),
                )

    async def close_pull_request(self, pr_number: int) -> None:
        """
        Close pull request.

        Args:
            pr_number: PR number
        """
        url = (
            f"{self.BASE_URL}/repos/{self.repository.owner}/{self.repository.repo}"
            f"/pulls/{pr_number}"
        )

        payload = {"state": "closed"}

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to close PR: {error}")

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for GitHub API."""
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
