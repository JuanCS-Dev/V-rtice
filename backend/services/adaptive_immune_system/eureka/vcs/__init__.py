"""
VCS Module - Version Control System Integration.

Integrates with Git hosting platforms:
- GitHub (PR creation, reviews, status checks)
- GitLab (MR creation, CI/CD)

Features:
- Automated PR/MR creation
- Rich PR descriptions with security context
- Branch management
- Status callbacks
"""

from .github_client import GitHubClient, GitHubRepository, PullRequest
from .pr_description_generator import (
    PRDescriptionGenerator,
    PRDescriptionContext,
)

__all__ = [
    "GitHubClient",
    "GitHubRepository",
    "PullRequest",
    "PRDescriptionGenerator",
    "PRDescriptionContext",
]
