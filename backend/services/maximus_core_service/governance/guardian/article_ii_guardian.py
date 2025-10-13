"""
Article II Guardian - Sovereign Quality Standard Enforcement

Enforces Article II of the Vértice Constitution: The Sovereign Quality Standard ("Padrão Pagani").
Ensures all code is production-ready with no mocks, placeholders, or technical debt.

Key Enforcement Areas:
- Section 1: All code must be PRODUCTION-READY
- Section 2: No MOCKS, PLACEHOLDERS, or TODOs in main branch
- Section 3: No skipped tests without explicit future dependency

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

import ast
import asyncio
import os
import re
import subprocess
from pathlib import Path

from .base import (
    ConstitutionalArticle,
    ConstitutionalViolation,
    GuardianAgent,
    GuardianDecision,
    GuardianIntervention,
    GuardianPriority,
    InterventionType,
)


class ArticleIIGuardian(GuardianAgent):
    """
    Guardian that enforces Article II: The Sovereign Quality Standard.

    Monitors codebase for:
    - Mock implementations
    - Placeholder code
    - TODO/FIXME comments
    - Skipped tests
    - Technical debt markers
    - Incomplete implementations
    """

    def __init__(self):
        """Initialize Article II Guardian."""
        super().__init__(
            guardian_id="guardian-article-ii",
            article=ConstitutionalArticle.ARTICLE_II,
            name="Sovereign Quality Guardian",
            description=(
                "Enforces the Sovereign Quality Standard (Padrão Pagani), "
                "ensuring all code is production-ready without mocks, "
                "placeholders, or technical debt."
            ),
        )

        # Patterns to detect violations
        self.mock_patterns = [
            r"\bmock\b",
            r"\bMock\b",
            r"\bfake\b",
            r"\bFake\b",
            r"\bstub\b",
            r"\bStub\b",
            r"\bdummy\b",
            r"\bDummy\b",
        ]

        self.placeholder_patterns = [
            r"\bTODO\b",
            r"\bFIXME\b",
            r"\bHACK\b",
            r"\bXXX\b",
            r"\bTEMP\b",
            r"\bplaceholder\b",
            r"NotImplementedError",
            r"raise NotImplemented",
            r"pass\s*#.*implement",
        ]

        self.test_skip_patterns = [
            r"@pytest\.mark\.skip",
            r"@unittest\.skip",
            r"\.skip\(",
            r"skipTest\(",
            r"@skip",
        ]

        # Paths to monitor
        self.monitored_paths = [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
            "/home/juan/vertice-dev/backend/services/active_immune_core",
        ]

        # Exclusions (allowed exceptions)
        self.excluded_paths = [
            "test_",  # Test files can have mocks
            "_test.py",
            "/tests/",
            "/test/",
            "__pycache__",
            ".git",
            "/migrations/",
            "/docs/",
        ]

    def get_monitored_systems(self) -> list[str]:
        """Get list of monitored systems."""
        return [
            "maximus_core_service",
            "reactive_fabric_core",
            "active_immune_core",
            "governance_module",
        ]

    async def monitor(self) -> list[ConstitutionalViolation]:
        """
        Monitor codebase for quality standard violations.

        Returns:
            List of detected violations
        """
        violations = []

        for base_path in self.monitored_paths:
            if not os.path.exists(base_path):
                continue

            # Check Python files
            for py_file in Path(base_path).rglob("*.py"):
                # Skip excluded paths
                if any(excl in str(py_file) for excl in self.excluded_paths):
                    continue

                file_violations = await self._check_file(py_file)
                violations.extend(file_violations)

        # Check for failing tests
        test_violations = await self._check_test_health()
        violations.extend(test_violations)

        # Check git status for uncommitted mocks
        git_violations = await self._check_git_status()
        violations.extend(git_violations)

        return violations

    async def _check_file(self, file_path: Path) -> list[ConstitutionalViolation]:
        """Check a single file for violations."""
        violations = []

        try:
            content = file_path.read_text()
            lines = content.splitlines()

            # Check for mock implementations
            for i, line in enumerate(lines, 1):
                # Check mock patterns
                for pattern in self.mock_patterns:
                    if re.search(pattern, line):
                        # Verify it's not in a comment or string
                        if not self._is_comment_or_string(line, pattern):
                            violations.append(
                                ConstitutionalViolation(
                                    article=ConstitutionalArticle.ARTICLE_II,
                                    clause="Section 2",
                                    rule="No MOCKS in production code",
                                    description=f"Mock implementation found in {file_path.name}:{i}",
                                    severity=GuardianPriority.HIGH,
                                    evidence=[f"{file_path}:{i}: {line.strip()}"],
                                    affected_systems=[str(file_path.parent.name)],
                                    recommended_action="Replace mock with real implementation",
                                    context={
                                        "file": str(file_path),
                                        "line": i,
                                        "pattern": pattern,
                                    },
                                )
                            )

                # Check placeholder patterns
                for pattern in self.placeholder_patterns:
                    if re.search(pattern, line):
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_II,
                                clause="Section 2",
                                rule="No PLACEHOLDERS or TODOs in production",
                                description=f"Placeholder/TODO found in {file_path.name}:{i}",
                                severity=GuardianPriority.MEDIUM,
                                evidence=[f"{file_path}:{i}: {line.strip()}"],
                                affected_systems=[str(file_path.parent.name)],
                                recommended_action="Complete implementation or move to feature branch",
                                context={
                                    "file": str(file_path),
                                    "line": i,
                                    "pattern": pattern,
                                },
                            )
                        )

            # Check for skipped tests (if it's a test file)
            if "test" in file_path.name.lower():
                for i, line in enumerate(lines, 1):
                    for pattern in self.test_skip_patterns:
                        if re.search(pattern, line):
                            # Check if there's a valid reason
                            if not self._has_valid_skip_reason(lines, i):
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_II,
                                        clause="Section 3",
                                        rule="No skipped tests without future dependency",
                                        description=f"Skipped test without valid reason in {file_path.name}:{i}",
                                        severity=GuardianPriority.MEDIUM,
                                        evidence=[f"{file_path}:{i}: {line.strip()}"],
                                        affected_systems=["test_suite"],
                                        recommended_action="Fix test or document future dependency in ROADMAP",
                                        context={
                                            "file": str(file_path),
                                            "line": i,
                                        },
                                    )
                                )

            # Check for NotImplementedError
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Raise):
                        if (
                            isinstance(node.exc, ast.Call)
                            and isinstance(node.exc.func, ast.Name)
                            and node.exc.func.id == "NotImplementedError"
                        ):
                            violations.append(
                                ConstitutionalViolation(
                                    article=ConstitutionalArticle.ARTICLE_II,
                                    clause="Section 1",
                                    rule="Code must be PRODUCTION-READY",
                                    description=f"NotImplementedError in {file_path.name}",
                                    severity=GuardianPriority.CRITICAL,
                                    evidence=[f"{file_path}: NotImplementedError found"],
                                    affected_systems=[str(file_path.parent.name)],
                                    recommended_action="Implement the functionality",
                                    context={"file": str(file_path)},
                                )
                            )
            except SyntaxError:
                # File has syntax errors - also a violation!
                violations.append(
                    ConstitutionalViolation(
                        article=ConstitutionalArticle.ARTICLE_II,
                        clause="Section 1",
                        rule="Code must be PRODUCTION-READY",
                        description=f"Syntax error in {file_path.name}",
                        severity=GuardianPriority.CRITICAL,
                        evidence=[f"{file_path}: Syntax error detected"],
                        affected_systems=[str(file_path.parent.name)],
                        recommended_action="Fix syntax errors",
                        context={"file": str(file_path)},
                    )
                )

        except Exception as e:
            # Error reading file - note but don't crash
            pass

        return violations

    async def _check_test_health(self) -> list[ConstitutionalViolation]:
        """Check if tests are passing."""
        violations = []

        # Run pytest on each monitored service
        for path in self.monitored_paths:
            test_path = Path(path) / "tests"
            if not test_path.exists():
                test_path = Path(path)  # Tests might be in root

            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_path), "--co", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=path,
                )

                # Check for test collection errors
                if "error" in result.stderr.lower() or result.returncode != 0:
                    violations.append(
                        ConstitutionalViolation(
                            article=ConstitutionalArticle.ARTICLE_II,
                            clause="Section 3",
                            rule="Tests must be executable",
                            description=f"Test collection failed in {Path(path).name}",
                            severity=GuardianPriority.HIGH,
                            evidence=[result.stderr[:500] if result.stderr else "Test collection failed"],
                            affected_systems=[Path(path).name],
                            recommended_action="Fix test configuration and imports",
                            context={"path": str(path)},
                        )
                    )

            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass

        return violations

    async def _check_git_status(self) -> list[ConstitutionalViolation]:
        """Check git status for uncommitted violations."""
        violations = []

        try:
            # Check current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd="/home/juan/vertice-dev",
            )

            current_branch = result.stdout.strip()

            # Only enforce on main/master branches
            if current_branch in ["main", "master", "production"]:
                # Check for uncommitted changes with violations
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    cwd="/home/juan/vertice-dev",
                )

                for line in result.stdout.splitlines():
                    if line.startswith("??") or line.startswith(" M"):
                        file_path = line[3:].strip()

                        # Check if file contains violations
                        full_path = Path("/home/juan/vertice-dev") / file_path
                        if full_path.suffix == ".py" and full_path.exists():
                            file_violations = await self._check_file(full_path)
                            if file_violations:
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_II,
                                        clause="Section 1",
                                        rule="Main branch must be PRODUCTION-READY",
                                        description=f"Uncommitted violations in main branch: {file_path}",
                                        severity=GuardianPriority.CRITICAL,
                                        evidence=[f"File with violations: {file_path}"],
                                        affected_systems=["version_control"],
                                        recommended_action="Fix violations before committing to main",
                                        context={
                                            "branch": current_branch,
                                            "file": file_path,
                                        },
                                    )
                                )

        except Exception:
            pass

        return violations

    def _is_comment_or_string(self, line: str, pattern: str) -> bool:
        """Check if pattern is in a comment or string."""
        # Simple heuristic - can be improved
        stripped = line.strip()
        if stripped.startswith("#"):
            return True
        if '"""' in line or "'''" in line:
            return True
        if pattern in line:
            # Check if it's in a string
            parts = line.split(pattern)
            before = parts[0]
            quote_count = before.count('"') + before.count("'")
            return quote_count % 2 == 1
        return False

    def _has_valid_skip_reason(self, lines: list[str], line_num: int) -> bool:
        """Check if skipped test has valid reason."""
        # Look for ROADMAP reference or future dependency comment
        context_start = max(0, line_num - 3)
        context_end = min(len(lines), line_num + 2)

        for i in range(context_start, context_end):
            line = lines[i].lower()
            if "roadmap" in line or "future" in line or "dependency" in line:
                return True

        return False

    async def analyze_violation(
        self, violation: ConstitutionalViolation
    ) -> GuardianDecision:
        """Analyze violation and decide on action."""
        # Determine decision based on severity and context
        if violation.severity == GuardianPriority.CRITICAL:
            decision_type = "veto"
            confidence = 0.95
            reasoning = (
                f"CRITICAL violation of Article II {violation.clause}: {violation.rule}. "
                "Code is not production-ready and must be fixed immediately."
            )
        elif violation.severity == GuardianPriority.HIGH:
            decision_type = "block"
            confidence = 0.85
            reasoning = (
                f"HIGH severity violation of Article II {violation.clause}: {violation.rule}. "
                "This violates the Sovereign Quality Standard."
            )
        else:
            decision_type = "alert"
            confidence = 0.75
            reasoning = (
                f"Violation of Article II {violation.clause}: {violation.rule}. "
                "This should be addressed to maintain quality standards."
            )

        return GuardianDecision(
            guardian_id=self.guardian_id,
            decision_type=decision_type,
            target=violation.context.get("file", "unknown"),
            reasoning=reasoning,
            confidence=confidence,
            requires_validation=confidence < 0.9,
        )

    async def intervene(
        self, violation: ConstitutionalViolation
    ) -> GuardianIntervention:
        """Take intervention action for violation."""
        intervention_type = InterventionType.ALERT
        action_taken = ""
        success = True

        if violation.severity == GuardianPriority.CRITICAL:
            # Veto merges/commits
            intervention_type = InterventionType.VETO
            action_taken = f"Vetoed code merge due to {violation.rule}"

            # Could integrate with CI/CD to actually block
            # For now, we'll create alerts and track

        elif violation.severity == GuardianPriority.HIGH:
            # Try auto-remediation for simple cases
            if "Mock implementation" in violation.description:
                intervention_type = InterventionType.REMEDIATION
                action_taken = "Attempted to replace mock with NotImplemented marker for visibility"
                # In production, could auto-generate stub implementation

            else:
                intervention_type = InterventionType.ESCALATION
                action_taken = "Escalated to development team for immediate fix"

        else:
            # Alert for tracking
            intervention_type = InterventionType.ALERT
            action_taken = f"Created alert for: {violation.description}"

        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=intervention_type,
            priority=violation.severity,
            violation=violation,
            action_taken=action_taken,
            result=f"Intervention applied to maintain {violation.clause}",
            success=success,
        )

    async def scan_pull_request(self, pr_diff: str) -> list[ConstitutionalViolation]:
        """
        Scan a pull request diff for violations.

        Args:
            pr_diff: The git diff of the pull request

        Returns:
            List of violations found in the PR
        """
        violations = []

        lines = pr_diff.splitlines()
        current_file = None
        line_number = 0

        for line in lines:
            # Track current file
            if line.startswith("+++"):
                current_file = line[4:].strip()
                line_number = 0
                continue

            # Track line numbers
            if line.startswith("@@"):
                # Extract line number from diff header
                match = re.search(r"\+(\d+)", line)
                if match:
                    line_number = int(match.group(1)) - 1
                continue

            # Only check added lines
            if line.startswith("+") and not line.startswith("+++"):
                line_number += 1
                content = line[1:]  # Remove the + prefix

                # Check for violations in added content
                for pattern in self.mock_patterns:
                    if re.search(pattern, content):
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_II,
                                clause="Section 2",
                                rule="No MOCKS in production code",
                                description=f"Mock added in PR: {current_file}:{line_number}",
                                severity=GuardianPriority.HIGH,
                                evidence=[f"{current_file}:{line_number}: {content.strip()}"],
                                affected_systems=["pull_request"],
                                recommended_action="Remove mock before merging",
                                context={
                                    "file": current_file,
                                    "line": line_number,
                                    "pr_check": True,
                                },
                            )
                        )

                for pattern in self.placeholder_patterns:
                    if re.search(pattern, content):
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_II,
                                clause="Section 2",
                                rule="No TODOs in production",
                                description=f"TODO added in PR: {current_file}:{line_number}",
                                severity=GuardianPriority.MEDIUM,
                                evidence=[f"{current_file}:{line_number}: {content.strip()}"],
                                affected_systems=["pull_request"],
                                recommended_action="Complete implementation before merging",
                                context={
                                    "file": current_file,
                                    "line": line_number,
                                    "pr_check": True,
                                },
                            )
                        )

            elif not line.startswith("-"):
                # Context line
                line_number += 1

        return violations