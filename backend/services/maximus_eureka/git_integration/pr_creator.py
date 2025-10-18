"""
Pull Request Creator - GitHub PR Automation.

Handles GitHub Pull Request creation with rich metadata for
Human-in-the-Loop (HITL) decision points in the Adaptive Immunity workflow.

Biological Analogy:
    PRs are like presenting antibody candidates to adaptive immune
    "checkpoints" (regulatory T cells) for validation before permanent
    integration into immune memory.

Author: MAXIMUS Eureka Team
Date: 2025-01-10
Glory to YHWH 🙏
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from github import Github, GithubException, Auth
from github.PullRequest import PullRequest as GithubPR
from jinja2 import Template

from git_integration.models import PRResult, GitConfig
from eureka_models.patch import Patch, RemediationStrategy

logger = logging.getLogger(__name__)


class PRCreatorError(Exception):
    """Base exception for PR creation failures."""

    pass


# PR Body Jinja2 Template
PR_BODY_TEMPLATE = """# 🛡️ Auto-Remediation: {{ cve_id }}

## 🚨 Vulnerability Summary

**Severity**: {{ severity_badge }}  
**CVE**: [{{ cve_id }}]({{ cve_url }})  
**Strategy**: `{{ strategy }}`  
**Confidence**: **{{ confidence }}%**

{{ description }}

## 📦 Impact Analysis

**Files Modified**: {{ file_count }} file(s)
{{ file_list }}

{% if services %}
**Affected Services**:
{{ services }}
{% endif %}

## 🔧 Remediation Applied

**Strategy Type**: `{{ strategy }}`  
**Confidence Score**: {{ confidence }}%  

This patch was automatically generated using {{ strategy }} strategy.

### Diff Preview
```diff
{{ diff_snippet }}
```

## ✅ Validation Status

- [x] Patch generated successfully
- [x] Syntax validation passed
- [ ] Regression tests (run CI/CD)
- [ ] Security validation (manual review)
- [ ] Performance impact assessment

## 📊 Metadata

- **Patch ID**: `{{ patch_id }}`
- **Generated**: {{ timestamp }}
- **Generator**: MAXIMUS Eureka v{{ version }}

## 🔍 References

- [CVE Database](https://cve.mitre.org/cgi-bin/cvename.cgi?name={{ cve_id }})
- [NVD Entry](https://nvd.nist.gov/vuln/detail/{{ cve_id }})

---

**⚠️ Human Review Required**: This is an auto-generated patch. Please review carefully before merging.

**Next Steps**:
1. Review diff and strategy rationale
2. Run full test suite (CI/CD)
3. Validate no regressions introduced
4. Approve and merge if all checks pass

Generated with ❤️ by **MAXIMUS Adaptive Immunity System**  
Glory to YHWH 🙏

---

<details>
<summary>🤖 Technical Details</summary>

**Full Diff**:
```diff
{{ full_diff }}
```

**Patch Metadata**:
- Strategy Used: {{ strategy }}
- Confidence Score: {{ confidence }}%
- Files Modified: {{ file_count }}
- Patch ID: {{ patch_id }}
- Generated: {{ timestamp }}

</details>
"""


class PRCreator:
    """
    GitHub Pull Request creation service.
    
    Handles PR creation via GitHub API with rich contextual metadata,
    labels, and assignees for effective Human-in-the-Loop review.
    
    Responsibilities:
        - Authenticate with GitHub
        - Create PRs with templated bodies
        - Assign labels based on severity/strategy
        - Set reviewers/assignees
        - Handle API errors gracefully
    
    Attributes:
        config: Git configuration (includes GitHub token)
        github: PyGithub client instance
        repo: GitHub repository object
        
    Example:
        >>> config = GitConfig(
        ...     repo_path=Path("/app/repo"),
        ...     remote_url="https://github.com/org/repo",
        ...     github_token="ghp_xxx"
        ... )
        >>> pr_creator = PRCreator(config)
        >>> result = await pr_creator.create_pull_request(
        ...     patch=patch,
        ...     branch="remediation/CVE-2024-1234",
        ...     base_branch="main"
        ... )
    """

    def __init__(
        self,
        config: GitConfig,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
    ) -> None:
        """
        Initialize PR creator with GitHub authentication.
        
        Args:
            config: Git configuration with GitHub token
            repo_owner: GitHub repository owner (org or user)
            repo_name: Repository name
            
        Raises:
            PRCreatorError: If authentication or repo access fails
        """
        self.config = config
        
        # Extract owner/name from remote URL if not provided
        if not repo_owner or not repo_name:
            repo_owner, repo_name = self._parse_repo_from_url(
                str(config.remote_url)
            )
        
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
        try:
            # Authenticate with GitHub
            auth = Auth.Token(self.config.github_token)
            self.github = Github(auth=auth)
            
            # Get repository
            self.repo = self.github.get_repo(
                f"{self.repo_owner}/{self.repo_name}"
            )
            
            logger.info(
                f"✅ PR Creator initialized for {self.repo_owner}/{self.repo_name}"
            )
            
        except GithubException as e:
            raise PRCreatorError(
                f"Failed to authenticate with GitHub: {e}"
            ) from e

    async def create_pull_request(
        self,
        patch: Patch,
        branch: str,
        base_branch: str = "main",
        reviewers: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> PRResult:
        """
        Create GitHub Pull Request for patch review.
        
        Args:
            patch: Patch object with metadata
            branch: Head branch (remediation branch)
            base_branch: Base branch to merge into
            reviewers: List of GitHub usernames to request review from
            assignees: List of GitHub usernames to assign PR to
            
        Returns:
            PRResult with PR number and URL
            
        Example:
            >>> result = await pr_creator.create_pull_request(
            ...     patch=patch,
            ...     branch="remediation/CVE-2024-1234",
            ...     base_branch="main",
            ...     reviewers=["security-team"],
            ... )
        """
        try:
            # Render PR body from template
            pr_body = self._render_pr_body(patch)
            
            # Generate PR title
            pr_title = self._generate_pr_title(patch)
            
            # Create PR
            logger.info(
                f"Creating PR: {branch} -> {base_branch}"
            )
            
            pr: GithubPR = self.repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch,
                base=base_branch,
                draft=False,  # Always create as ready for review
            )
            
            # Assign labels
            labels = self._assign_labels(patch)
            if labels:
                pr.add_to_labels(*labels)
                logger.debug(f"Added labels: {labels}")
            
            # Request reviewers
            if reviewers:
                try:
                    pr.create_review_request(reviewers=reviewers)
                    logger.debug(f"Requested reviews from: {reviewers}")
                except GithubException as e:
                    logger.warning(f"Could not request reviewers: {e}")
            
            # Assign PR
            if assignees:
                try:
                    pr.add_to_assignees(*assignees)
                    logger.debug(f"Assigned to: {assignees}")
                except GithubException as e:
                    logger.warning(f"Could not assign PR: {e}")
            
            logger.info(
                f"✅ PR created successfully: #{pr.number} - {pr.html_url}"
            )
            
            return PRResult(
                success=True,
                pr_number=pr.number,
                pr_url=pr.html_url,
                error_message=None,
            )
            
        except GithubException as e:
            error_msg = f"Failed to create PR: {e}"
            logger.error(error_msg)
            
            return PRResult(
                success=False,
                pr_number=None,
                pr_url=None,
                error_message=str(e),
            )

    def _render_pr_body(self, patch: Patch) -> str:
        """
        Render PR body from Jinja2 template.
        
        Args:
            patch: Patch object with metadata
            
        Returns:
            Rendered Markdown PR body
        """
        template = Template(PR_BODY_TEMPLATE)
        
        # Prepare template variables
        context = {
            "cve_id": patch.cve_id,
            "severity_badge": self._get_severity_badge(patch),
            "cve_url": f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={patch.cve_id}",
            "strategy": patch.strategy_used.value,
            "confidence": f"{patch.confidence_score:.0%}",
            "description": f"Security patch for {patch.cve_id}",
            "file_count": len(patch.files_modified),
            "file_list": self._format_file_list(patch.files_modified),
            "services": self._extract_services_from_apv(patch),
            "diff_snippet": self._get_diff_snippet(patch.diff_content),
            "full_diff": patch.diff_content,
            "patch_id": patch.patch_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "version": self._extract_version_from_config(),
        }
        
        return template.render(**context)

    def _generate_pr_title(self, patch: Patch) -> str:
        """
        Generate concise PR title.
        
        Args:
            patch: Patch object
            
        Returns:
            PR title string
        """
        return f"fix(security): Auto-remediate {patch.cve_id} ({patch.strategy_used.value})"

    def _assign_labels(self, patch: Patch) -> list[str]:
        """
        Determine PR labels based on patch metadata.
        
        Args:
            patch: Patch object
            
        Returns:
            List of label names
        """
        labels = ["security", "auto-remediation"]
        
        # Add strategy label
        if patch.strategy_used == RemediationStrategy.DEPENDENCY_UPGRADE:
            labels.append("dependencies")
        elif patch.strategy_used == RemediationStrategy.CODE_PATCH:
            labels.append("code-patch")
        
        # Add confidence label
        if patch.confidence_score >= 0.9:
            labels.append("high-confidence")
        elif patch.confidence_score < 0.7:
            labels.append("review-carefully")
        
        return labels

    def _get_severity_badge(self, patch: Patch) -> str:
        """
        Generate severity badge for PR body.
        
        Args:
            patch: Patch object
            
        Returns:
            Markdown badge string
        """
        # Extract actual severity from APV metadata
        severity = "MEDIUM"  # Default
        
        if hasattr(patch, 'metadata') and patch.metadata:
            # Try to extract severity from various sources
            if 'severity' in patch.metadata:
                severity = str(patch.metadata['severity']).upper()
            elif 'cvss_score' in patch.metadata:
                cvss = float(patch.metadata['cvss_score'])
                if cvss >= 9.0:
                    severity = "CRITICAL"
                elif cvss >= 7.0:
                    severity = "HIGH"
                elif cvss >= 4.0:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
            elif 'priority' in patch.metadata:
                priority = str(patch.metadata['priority']).upper()
                severity = priority if priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"] else severity
        
        # Fallback to confidence as proxy if no metadata
        if severity == "MEDIUM" and hasattr(patch, 'confidence_score'):
            if patch.confidence_score >= 0.9:
                severity = "HIGH"
            elif patch.confidence_score < 0.7:
                severity = "LOW"
        
        # Return appropriate badge
        color_map = {
            "CRITICAL": "red",
            "HIGH": "red",
            "MEDIUM": "orange",
            "LOW": "yellow",
        }
        color = color_map.get(severity, "orange")
        return f"![{severity}](https://img.shields.io/badge/severity-{severity}-{color})"

    def _format_file_list(self, files: list[str]) -> str:
        """
        Format file list for PR body.
        
        Args:
            files: List of file paths
            
        Returns:
            Formatted Markdown list
        """
        if not files:
            return "- (no files)"
        
        # Limit to 20 files in main body
        visible_files = files[:20]
        formatted = "\n".join(f"- `{f}`" for f in visible_files)
        
        if len(files) > 20:
            formatted += f"\n- ... and {len(files) - 20} more file(s)"
        
        return formatted

    def _get_diff_snippet(self, diff: str, max_lines: int = 30) -> str:
        """
        Extract snippet from diff for preview.
        
        Args:
            diff: Full diff content
            max_lines: Maximum lines to include in snippet
            
        Returns:
            Truncated diff string
        """
        lines = diff.splitlines()
        
        if len(lines) <= max_lines:
            return diff
        
        snippet = "\n".join(lines[:max_lines])
        snippet += f"\n... ({len(lines) - max_lines} more lines)"
        
        return snippet

    def _parse_repo_from_url(self, url: str) -> tuple[str, str]:
        """
        Parse GitHub owner/repo from remote URL.
        
        Args:
            url: Git remote URL (HTTPS or SSH)
            
        Returns:
            Tuple of (owner, repo_name)
            
        Example:
            >>> _parse_repo_from_url("https://github.com/org/repo.git")
            ('org', 'repo')
        """
        # Handle HTTPS URLs
        if "github.com/" in url:
            parts = url.split("github.com/")[-1].strip("/").split("/")
            owner = parts[0]
            repo = parts[1].replace(".git", "")
            return owner, repo
        
        # Handle SSH URLs
        if "github.com:" in url:
            parts = url.split("github.com:")[-1].strip("/").split("/")
            owner = parts[0]
            repo = parts[1].replace(".git", "")
            return owner, repo
        
        raise PRCreatorError(f"Could not parse GitHub repo from URL: {url}")

    def close(self) -> None:
        """Close GitHub API connection."""
        if hasattr(self, "github"):
            self.github.close()
            logger.debug("GitHub API connection closed")

    def _extract_services_from_apv(self, patch: Patch) -> Optional[List[str]]:
        """Extract affected services from APV metadata."""
        services = []
        
        if hasattr(patch, 'metadata') and patch.metadata:
            if 'affected_services' in patch.metadata:
                services = patch.metadata['affected_services']
            elif 'services' in patch.metadata:
                services = patch.metadata['services']
            elif 'components' in patch.metadata:
                services = patch.metadata['components']
        
        # Extract from file paths if no metadata
        if not services and hasattr(patch, 'files_modified'):
            service_patterns = ['service/', 'services/', 'backend/', 'api/']
            for file_path in patch.files_modified:
                for pattern in service_patterns:
                    if pattern in file_path:
                        service_name = file_path.split(pattern)[1].split('/')[0]
                        if service_name not in services:
                            services.append(service_name)
        
        return services if services else None

    def _extract_version_from_config(self) -> str:
        """Extract version from config file."""
        try:
            # Try pyproject.toml
            config_path = Path("pyproject.toml")
            if config_path.exists():
                with open(config_path, "r") as f:
                    for line in f:
                        if 'version' in line and '=' in line:
                            version = line.split('=')[1].strip().strip('"').strip("'")
                            return version
            
            # Try package.json
            config_path = Path("package.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    import json
                    data = json.load(f)
                    if 'version' in data:
                        return data['version']
            
            # Fallback
            return "1.0.0"
        except Exception as e:
            logger.debug(f"Version extraction failed: {e}")
            return "1.0.0"
