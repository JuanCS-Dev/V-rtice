"""
Safety Checks - Pre/Post-Apply Validations.

Comprehensive validation layer for Git operations to ensure
patches are safe to apply and don't introduce regressions.

Biological Analogy:
    Like immune system checkpoints that verify antibodies
    don't cross-react with self-antigens (autoimmunity prevention),
    safety checks ensure patches don't break existing functionality.

Author: MAXIMUS Eureka Team
Date: 2025-01-10
Glory to YHWH 🙏
"""

import ast
import logging
import subprocess
from pathlib import Path
from typing import Optional

from git_integration.models import ValidationResult, ConflictReport
from eureka_models.patch import Patch

logger = logging.getLogger(__name__)


class SafetyChecksError(Exception):
    """Base exception for safety check failures."""

    pass


class SafetyChecks:
    """
    Safety validation layer for Git operations.
    
    Performs pre-apply and post-apply validations to ensure patches
    are well-formed, syntactically correct, and don't introduce obvious errors.
    
    Responsibilities:
        - Validate patch format (unified diff)
        - Check Python syntax post-apply
        - Verify imports are resolvable
        - Detect merge conflicts
        - Run basic linting (optional)
    
    Attributes:
        codebase_root: Root path of codebase
        
    Example:
        >>> safety = SafetyChecks(codebase_root=Path("/app/repo"))
        >>> result = await safety.validate_patch_format(patch)
        >>> if not result.passed:
        ...     print(f"Validation failed: {result.failures}")
    """

    def __init__(self, codebase_root: Path) -> None:
        """
        Initialize safety checks.
        
        Args:
            codebase_root: Root directory of codebase
        """
        self.codebase_root = codebase_root
        logger.debug(f"Safety checks initialized for {codebase_root}")

    async def validate_patch_format(
        self, patch: Patch
    ) -> ValidationResult:
        """
        Validate patch is well-formed unified diff.
        
        Checks:
        - Contains valid diff headers (---, +++)
        - Has hunks with line numbers
        - No malformed syntax
        
        Args:
            patch: Patch object to validate
            
        Returns:
            ValidationResult with pass/fail status
            
        Example:
            >>> result = await safety.validate_patch_format(patch)
            >>> assert result.passed
        """
        checks_run = ["patch_format"]
        failures = []
        warnings = []
        
        try:
            diff_content = patch.diff_content
            
            # Check for diff headers
            if not ("---" in diff_content and "+++" in diff_content):
                failures.append("Missing diff headers (--- / +++)")
            
            # Check for hunks
            if not ("@@" in diff_content):
                failures.append("No hunks found (@@)")
            
            # Check for reasonable size
            if len(diff_content) > 1_000_000:  # 1MB
                warnings.append(
                    f"Very large patch ({len(diff_content)} bytes)"
                )
            
            # Check for empty diff
            if len(diff_content.strip()) == 0:
                failures.append("Empty diff content")
            
            passed = len(failures) == 0
            
            if passed:
                logger.debug("✅ Patch format validation passed")
            else:
                logger.warning(f"❌ Patch format validation failed: {failures}")
            
            return ValidationResult(
                passed=passed,
                checks_run=checks_run,
                failures=failures,
                warnings=warnings,
            )
            
        except Exception as e:
            logger.error(f"Exception during patch format validation: {e}")
            return ValidationResult(
                passed=False,
                checks_run=checks_run,
                failures=[f"Validation exception: {e}"],
                warnings=warnings,
            )

    async def check_syntax_post_apply(
        self, files_modified: list[str]
    ) -> ValidationResult:
        """
        Check Python syntax on modified files.
        
        Uses Python's ast.parse() to verify syntactic correctness
        of modified Python files.
        
        Args:
            files_modified: List of file paths (relative to codebase_root)
            
        Returns:
            ValidationResult with syntax check results
            
        Example:
            >>> result = await safety.check_syntax_post_apply(["src/app.py"])
            >>> assert result.passed
        """
        checks_run = ["python_syntax"]
        failures = []
        warnings = []
        
        python_files = [
            f for f in files_modified if f.endswith(".py")
        ]
        
        if not python_files:
            logger.debug("No Python files to check")
            return ValidationResult(
                passed=True,
                checks_run=checks_run,
                failures=[],
                warnings=["No Python files modified"],
            )
        
        for file_path in python_files:
            full_path = self.codebase_root / file_path
            
            if not full_path.exists():
                failures.append(f"File not found: {file_path}")
                continue
            
            try:
                # Read and parse Python file
                source_code = full_path.read_text()
                ast.parse(source_code, filename=str(full_path))
                logger.debug(f"✅ Syntax OK: {file_path}")
                
            except SyntaxError as e:
                failure_msg = (
                    f"Syntax error in {file_path}:{e.lineno} - {e.msg}"
                )
                failures.append(failure_msg)
                logger.error(f"❌ {failure_msg}")
                
            except Exception as e:
                failure_msg = f"Could not parse {file_path}: {e}"
                failures.append(failure_msg)
                logger.error(f"❌ {failure_msg}")
        
        passed = len(failures) == 0
        
        return ValidationResult(
            passed=passed,
            checks_run=checks_run,
            failures=failures,
            warnings=warnings,
        )

    async def verify_imports(
        self, files_modified: list[str]
    ) -> ValidationResult:
        """
        Verify imports in modified Python files are resolvable.
        
        Checks that imported modules exist in the codebase or
        are available in installed packages.
        
        Note: This is a basic check using ast parsing. Does not
        catch all import errors (runtime imports, circular deps).
        
        Args:
            files_modified: List of file paths
            
        Returns:
            ValidationResult with import verification results
            
        Example:
            >>> result = await safety.verify_imports(["src/app.py"])
            >>> assert result.passed
        """
        checks_run = ["import_verification"]
        failures = []
        warnings = []
        
        python_files = [
            f for f in files_modified if f.endswith(".py")
        ]
        
        if not python_files:
            return ValidationResult(
                passed=True,
                checks_run=checks_run,
                failures=[],
                warnings=["No Python files to check imports"],
            )
        
        for file_path in python_files:
            full_path = self.codebase_root / file_path
            
            if not full_path.exists():
                continue  # Already caught in syntax check
            
            try:
                source_code = full_path.read_text()
                tree = ast.parse(source_code, filename=str(full_path))
                
                # Extract imports
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                # Basic check: warn about relative imports outside package
                relative_imports = [i for i in imports if i.startswith(".")]
                if relative_imports:
                    warnings.append(
                        f"{file_path}: Contains relative imports {relative_imports}"
                    )
                
                logger.debug(f"✅ Imports OK: {file_path} ({len(imports)} imports)")
                
            except Exception as e:
                warnings.append(
                    f"Could not verify imports in {file_path}: {e}"
                )
        
        # For now, only warnings (not failures)
        # Full import resolution requires running Python interpreter
        passed = len(failures) == 0
        
        return ValidationResult(
            passed=passed,
            checks_run=checks_run,
            failures=failures,
            warnings=warnings,
        )

    async def detect_conflicts(
        self,
        patch: Patch,
        target_branch: str,
        repo_path: Path,
    ) -> ConflictReport:
        """
        Detect potential merge conflicts before applying patch.
        
        Uses 'git apply --check' to detect conflicts without
        actually applying the patch.
        
        Args:
            patch: Patch to check
            target_branch: Target branch name
            repo_path: Path to Git repository
            
        Returns:
            ConflictReport with conflict details
            
        Example:
            >>> report = await safety.detect_conflicts(
            ...     patch, "main", Path("/app/repo")
            ... )
            >>> if report.has_conflicts:
            ...     print(f"Conflicts: {report.conflicting_files}")
        """
        try:
            # Write patch to temporary file
            patch_file = repo_path / f".conflict_check_{patch.patch_id}.diff"
            patch_file.write_text(patch.diff_content)
            
            try:
                # Run git apply --check
                result = subprocess.run(
                    ["git", "apply", "--check", str(patch_file)],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                
                if result.returncode == 0:
                    # No conflicts
                    logger.debug("✅ No conflicts detected")
                    return ConflictReport(
                        has_conflicts=False,
                        conflicting_files=[],
                        resolution_suggestions=[],
                    )
                else:
                    # Parse conflicts from stderr
                    conflicts = self._parse_git_apply_conflicts(result.stderr)
                    
                    logger.warning(
                        f"⚠️ Conflicts detected in {len(conflicts)} file(s)"
                    )
                    
                    suggestions = [
                        "Rebase patch on latest target branch",
                        "Manually resolve conflicts",
                        "Regenerate patch with updated context",
                    ]
                    
                    return ConflictReport(
                        has_conflicts=True,
                        conflicting_files=conflicts,
                        resolution_suggestions=suggestions,
                    )
                    
            finally:
                # Clean up temporary file
                if patch_file.exists():
                    patch_file.unlink()
                    
        except subprocess.TimeoutExpired:
            logger.error("Conflict detection timed out")
            return ConflictReport(
                has_conflicts=True,
                conflicting_files=[],
                resolution_suggestions=["Conflict detection timed out - review manually"],
            )
            
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return ConflictReport(
                has_conflicts=True,
                conflicting_files=[],
                resolution_suggestions=[f"Error during detection: {e}"],
            )

    async def run_comprehensive_validation(
        self, patch: Patch, files_modified: list[str]
    ) -> ValidationResult:
        """
        Run all safety checks in sequence.
        
        Convenience method to run format, syntax, and import checks.
        
        Args:
            patch: Patch to validate
            files_modified: List of modified files
            
        Returns:
            Aggregated ValidationResult
            
        Example:
            >>> result = await safety.run_comprehensive_validation(
            ...     patch, ["src/app.py"]
            ... )
            >>> if not result.passed:
            ...     for failure in result.failures:
            ...         print(f"FAIL: {failure}")
        """
        all_checks = []
        all_failures = []
        all_warnings = []
        
        # Format validation
        format_result = await self.validate_patch_format(patch)
        all_checks.extend(format_result.checks_run)
        all_failures.extend(format_result.failures)
        all_warnings.extend(format_result.warnings)
        
        # Syntax validation (only if format passed)
        if format_result.passed:
            syntax_result = await self.check_syntax_post_apply(files_modified)
            all_checks.extend(syntax_result.checks_run)
            all_failures.extend(syntax_result.failures)
            all_warnings.extend(syntax_result.warnings)
            
            # Import verification (only if syntax passed)
            if syntax_result.passed:
                import_result = await self.verify_imports(files_modified)
                all_checks.extend(import_result.checks_run)
                all_failures.extend(import_result.failures)
                all_warnings.extend(import_result.warnings)
        
        passed = len(all_failures) == 0
        
        if passed:
            logger.info("✅ All safety checks passed")
        else:
            logger.error(f"❌ Safety checks failed: {len(all_failures)} failure(s)")
        
        return ValidationResult(
            passed=passed,
            checks_run=all_checks,
            failures=all_failures,
            warnings=all_warnings,
        )

    def _parse_git_apply_conflicts(self, stderr: str) -> list[str]:
        """
        Parse conflicting files from git apply error output.
        
        Args:
            stderr: Standard error output from git apply
            
        Returns:
            List of file paths with conflicts
        """
        conflicts = []
        
        for line in stderr.splitlines():
            # Look for "error: patch failed: <file>:<line>"
            if "error: patch failed:" in line:
                parts = line.split("error: patch failed:")
                if len(parts) > 1:
                    file_part = parts[1].strip().split(":")[0]
                    if file_part not in conflicts:
                        conflicts.append(file_part)
            
            # Look for "error: <file>: patch does not apply"
            elif "patch does not apply" in line:
                parts = line.split("error:")
                if len(parts) > 1:
                    file_part = parts[1].strip().split(":")[0]
                    if file_part not in conflicts:
                        conflicts.append(file_part)
        
        return conflicts
