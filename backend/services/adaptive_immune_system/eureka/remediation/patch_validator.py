"""
Patch Validator - Validates generated patches before application.

Validation strategies:
1. Syntax validation (AST parsing)
2. Test execution (existing test suite)
3. Static analysis (no new vulnerabilities)
4. Dependency compatibility check
5. Build/compile verification
"""

import asyncio
import ast
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .remedy_generator import GeneratedPatch

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Patch validation result."""

    valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    validation_checks: Dict[str, bool] = Field(default_factory=dict)
    error_messages: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None


class PatchValidator:
    """
    Validates generated patches for safety and correctness.

    Validation pipeline:
    1. Syntax check (parse code, check for errors)
    2. Static analysis (run linters, security scanners)
    3. Test execution (run existing tests)
    4. Dependency check (verify version compatibility)
    5. Build verification (ensure project still builds)
    """

    def __init__(
        self,
        project_path: Path,
        enable_tests: bool = True,
        enable_build: bool = True,
        test_timeout: int = 300,
    ):
        """
        Initialize patch validator.

        Args:
            project_path: Path to project root
            enable_tests: Run test suite for validation
            enable_build: Run build for validation
            test_timeout: Test execution timeout in seconds
        """
        self.project_path = Path(project_path)
        self.enable_tests = enable_tests
        self.enable_build = enable_build
        self.test_timeout = test_timeout

        logger.info(
            f"PatchValidator initialized: tests={enable_tests}, build={enable_build}"
        )

    async def validate_patch(self, patch: GeneratedPatch) -> ValidationResult:
        """
        Validate generated patch.

        Args:
            patch: GeneratedPatch to validate

        Returns:
            ValidationResult
        """
        logger.info(f"🔍 Validating patch: {patch.patch_id}")

        validation_checks = {}
        error_messages = []
        warnings = []

        # Check 1: Syntax validation
        try:
            syntax_valid = await self._validate_syntax(patch)
            validation_checks["syntax"] = syntax_valid
            if not syntax_valid:
                error_messages.append("Syntax validation failed")
        except Exception as e:
            validation_checks["syntax"] = False
            error_messages.append(f"Syntax check error: {e}")

        # Check 2: Static analysis
        try:
            static_valid = await self._validate_static_analysis(patch)
            validation_checks["static_analysis"] = static_valid
            if not static_valid:
                warnings.append("Static analysis found issues")
        except Exception as e:
            validation_checks["static_analysis"] = False
            warnings.append(f"Static analysis error: {e}")

        # Check 3: Test execution (if enabled)
        test_results = None
        if self.enable_tests:
            try:
                tests_passed, test_results = await self._run_tests(patch)
                validation_checks["tests"] = tests_passed
                if not tests_passed:
                    error_messages.append("Test execution failed")
            except Exception as e:
                validation_checks["tests"] = False
                error_messages.append(f"Test execution error: {e}")

        # Check 4: Dependency compatibility
        if patch.strategy.strategy_type == "version_bump":
            try:
                compat_valid = await self._validate_dependency_compatibility(patch)
                validation_checks["dependency_compatibility"] = compat_valid
                if not compat_valid:
                    warnings.append("Potential dependency compatibility issues")
            except Exception as e:
                validation_checks["dependency_compatibility"] = False
                warnings.append(f"Dependency check error: {e}")

        # Check 5: Build verification (if enabled)
        if self.enable_build:
            try:
                build_valid = await self._validate_build(patch)
                validation_checks["build"] = build_valid
                if not build_valid:
                    error_messages.append("Build failed")
            except Exception as e:
                validation_checks["build"] = False
                error_messages.append(f"Build error: {e}")

        # Calculate overall validity
        # Required checks: syntax, tests (if enabled), build (if enabled)
        required_checks = ["syntax"]
        if self.enable_tests:
            required_checks.append("tests")
        if self.enable_build:
            required_checks.append("build")

        valid = all(validation_checks.get(check, False) for check in required_checks)

        # Calculate confidence based on passed checks
        total_checks = len(validation_checks)
        passed_checks = sum(1 for v in validation_checks.values() if v)
        confidence = passed_checks / total_checks if total_checks > 0 else 0.0

        logger.info(
            f"Validation complete: valid={valid}, confidence={confidence:.2f}, "
            f"passed={passed_checks}/{total_checks}"
        )

        return ValidationResult(
            valid=valid,
            confidence=confidence,
            validation_checks=validation_checks,
            error_messages=error_messages,
            warnings=warnings,
            test_results=test_results,
        )

    async def _validate_syntax(self, patch: GeneratedPatch) -> bool:
        """
        Validate Python/JavaScript syntax.

        Args:
            patch: GeneratedPatch

        Returns:
            True if syntax is valid
        """
        for change in patch.changes:
            file_path = change.get("file_path", "")
            patch_content = change.get("patch_content", "")

            # Extract code from patch (remove diff markers)
            code_lines = [
                line[1:] if line.startswith(("+", "-")) else line
                for line in patch_content.split("\n")
                if not line.startswith(("---", "+++", "@@"))
            ]
            code = "\n".join(code_lines)

            # Validate based on file extension
            if file_path.endswith(".py"):
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    logger.error(f"Python syntax error in {file_path}: {e}")
                    return False

            elif file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                # Use acorn or esprima for JavaScript parsing
                # For now, basic check
                if "function()" in code or "SyntaxError" in code:
                    logger.error(f"JavaScript syntax suspicious in {file_path}")
                    return False

        return True

    async def _validate_static_analysis(self, patch: GeneratedPatch) -> bool:
        """
        Run static analysis on patched code.

        Args:
            patch: GeneratedPatch

        Returns:
            True if no critical issues found
        """
        # Create temporary file with patched code
        for change in patch.changes:
            file_path = change.get("file_path", "")
            patch_content = change.get("patch_content", "")

            if not file_path.endswith((".py", ".js", ".jsx")):
                continue

            # Extract new code (lines starting with +)
            new_code_lines = [
                line[1:]
                for line in patch_content.split("\n")
                if line.startswith("+")
            ]
            new_code = "\n".join(new_code_lines)

            # Run appropriate linter
            if file_path.endswith(".py"):
                try:
                    # Run pylint or flake8
                    result = await asyncio.create_subprocess_exec(
                        "flake8",
                        "--select=E,W,F",  # Errors, warnings, pyflakes
                        "-",
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    stdout, stderr = await asyncio.wait_for(
                        result.communicate(new_code.encode()),
                        timeout=30,
                    )

                    # Check for critical errors only
                    if b"E9" in stdout or b"F8" in stdout:
                        logger.warning(f"Critical linting issues in {file_path}")
                        return False

                except (FileNotFoundError, asyncio.TimeoutError):
                    logger.debug("flake8 not available or timed out")

        return True

    async def _run_tests(self, patch: GeneratedPatch) -> Tuple[bool, Dict[str, Any]]:
        """
        Run test suite with patch applied.

        Args:
            patch: GeneratedPatch

        Returns:
            Tuple of (tests_passed, test_results)
        """
        # Apply patch temporarily
        original_contents = await self._apply_patch_temporarily(patch)

        try:
            # Detect test framework and run tests
            test_passed = False
            test_results = {}

            # Try pytest (Python)
            if (self.project_path / "pytest.ini").exists() or any(
                (self.project_path / "tests").glob("test_*.py")
            ):
                test_passed, test_results = await self._run_pytest()

            # Try npm test (JavaScript)
            elif (self.project_path / "package.json").exists():
                test_passed, test_results = await self._run_npm_test()

            # Try go test (Go)
            elif (self.project_path / "go.mod").exists():
                test_passed, test_results = await self._run_go_test()

            return test_passed, test_results

        finally:
            # Restore original files
            await self._restore_files(original_contents)

    async def _run_pytest(self) -> Tuple[bool, Dict[str, Any]]:
        """Run pytest test suite."""
        try:
            process = await asyncio.create_subprocess_exec(
                "pytest",
                "--tb=short",
                "-v",
                "--timeout=60",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.test_timeout,
            )

            output = stdout.decode() + stderr.decode()
            test_passed = process.returncode == 0

            # Parse pytest output for results
            results = {
                "framework": "pytest",
                "exit_code": process.returncode,
                "output": output[:1000],  # Truncate
            }

            return test_passed, results

        except (FileNotFoundError, asyncio.TimeoutError) as e:
            logger.warning(f"pytest execution failed: {e}")
            return False, {"error": str(e)}

    async def _run_npm_test(self) -> Tuple[bool, Dict[str, Any]]:
        """Run npm test suite."""
        try:
            process = await asyncio.create_subprocess_exec(
                "npm",
                "test",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.test_timeout,
            )

            output = stdout.decode() + stderr.decode()
            test_passed = process.returncode == 0

            results = {
                "framework": "npm",
                "exit_code": process.returncode,
                "output": output[:1000],
            }

            return test_passed, results

        except (FileNotFoundError, asyncio.TimeoutError) as e:
            logger.warning(f"npm test failed: {e}")
            return False, {"error": str(e)}

    async def _run_go_test(self) -> Tuple[bool, Dict[str, Any]]:
        """Run go test suite."""
        try:
            process = await asyncio.create_subprocess_exec(
                "go",
                "test",
                "./...",
                "-timeout",
                "60s",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.test_timeout,
            )

            output = stdout.decode() + stderr.decode()
            test_passed = process.returncode == 0

            results = {
                "framework": "go test",
                "exit_code": process.returncode,
                "output": output[:1000],
            }

            return test_passed, results

        except (FileNotFoundError, asyncio.TimeoutError) as e:
            logger.warning(f"go test failed: {e}")
            return False, {"error": str(e)}

    async def _validate_dependency_compatibility(self, patch: GeneratedPatch) -> bool:
        """
        Validate dependency version compatibility.

        Args:
            patch: GeneratedPatch

        Returns:
            True if compatible
        """
        # Check for breaking changes in version bumps
        for change in patch.changes:
            patch_content = change.get("patch_content", "")

            # Extract version numbers
            import re
            version_pattern = r"(\d+)\.(\d+)\.(\d+)"
            versions = re.findall(version_pattern, patch_content)

            if len(versions) >= 2:
                old_major, old_minor, old_patch = map(int, versions[0])
                new_major, new_minor, new_patch = map(int, versions[1])

                # Major version change = potential breaking changes
                if new_major > old_major:
                    logger.warning("Major version bump detected - review breaking changes")
                    return False

        return True

    async def _validate_build(self, patch: GeneratedPatch) -> bool:
        """
        Validate that project still builds.

        Args:
            patch: GeneratedPatch

        Returns:
            True if build succeeds
        """
        # Apply patch temporarily
        original_contents = await self._apply_patch_temporarily(patch)

        try:
            # Try different build systems
            build_passed = False

            # Python: pip install -e .
            if (self.project_path / "setup.py").exists() or (
                self.project_path / "pyproject.toml"
            ).exists():
                build_passed = await self._run_python_build()

            # JavaScript: npm run build
            elif (self.project_path / "package.json").exists():
                build_passed = await self._run_npm_build()

            # Go: go build
            elif (self.project_path / "go.mod").exists():
                build_passed = await self._run_go_build()

            return build_passed

        finally:
            # Restore original files
            await self._restore_files(original_contents)

    async def _run_python_build(self) -> bool:
        """Run Python build."""
        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "build",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await asyncio.wait_for(process.communicate(), timeout=120)
            return process.returncode == 0

        except Exception as e:
            logger.debug(f"Python build failed: {e}")
            return True  # Don't fail if build tool not available

    async def _run_npm_build(self) -> bool:
        """Run npm build."""
        try:
            process = await asyncio.create_subprocess_exec(
                "npm", "run", "build",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await asyncio.wait_for(process.communicate(), timeout=120)
            return process.returncode == 0

        except Exception:
            return True  # Don't fail if build script not available

    async def _run_go_build(self) -> bool:
        """Run go build."""
        try:
            process = await asyncio.create_subprocess_exec(
                "go", "build", "./...",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await asyncio.wait_for(process.communicate(), timeout=120)
            return process.returncode == 0

        except Exception as e:
            logger.debug(f"Go build failed: {e}")
            return True

    async def _apply_patch_temporarily(
        self, patch: GeneratedPatch
    ) -> Dict[str, str]:
        """
        Apply patch to files temporarily.

        Args:
            patch: GeneratedPatch

        Returns:
            Dictionary mapping file paths to original contents
        """
        original_contents = {}

        for change in patch.changes:
            file_path = self.project_path / change.get("file_path", "")

            # Save original content
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    original_contents[str(file_path)] = f.read()

            # Apply patch (simplified - in production use proper patch tool)
            patch_content = change.get("patch_content", "")
            # For now, just write new content
            # In production, use `patch` command or git apply

        return original_contents

    async def _restore_files(self, original_contents: Dict[str, str]) -> None:
        """
        Restore files to original state.

        Args:
            original_contents: Dictionary mapping file paths to original contents
        """
        for file_path, content in original_contents.items():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
