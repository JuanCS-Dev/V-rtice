"""
Regression Test Runner - Validates patches don't break existing functionality.

Runs existing test suite on patched version to ensure no regressions introduced.

Theoretical Foundation:
    Patches can fix vulnerabilities but inadvertently break existing functionality.
    Regression testing ensures changes are backward-compatible.
    
    Success criteria:
    - Pass rate ≥95% (some tests may be flaky)
    - No new failures introduced
    - Performance within acceptable range
    
    Integration with pytest for maximum compatibility.

Performance Targets:
    - Test execution: <5 min for typical suite
    - Result parsing: <1s
    - Pass rate threshold: ≥95%

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH - Keeper of all things
"""

import logging
import subprocess
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Individual test result"""
    
    test_name: str
    status: TestStatus
    duration_seconds: float
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "test_name": self.test_name,
            "status": self.status.value,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message
        }


@dataclass
class RegressionTestReport:
    """Complete regression test report"""
    
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    pass_rate: float
    total_duration_seconds: float
    test_results: List[TestResult]
    executed_at: datetime
    metadata: Dict
    
    @property
    def passed_threshold(self) -> bool:
        """Check if pass rate meets threshold (≥95%)"""
        return self.pass_rate >= 0.95
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "pass_rate": self.pass_rate,
            "total_duration_seconds": self.total_duration_seconds,
            "test_results": [t.to_dict() for t in self.test_results],
            "executed_at": self.executed_at.isoformat(),
            "metadata": self.metadata
        }
    
    def summary(self) -> str:
        """Human-readable summary"""
        status_emoji = "✅" if self.passed_threshold else "❌"
        return f"""{status_emoji} REGRESSION TEST REPORT
Total Tests: {self.total_tests}
Passed: {self.passed} ({self.pass_rate * 100:.1f}%)
Failed: {self.failed}
Skipped: {self.skipped}
Errors: {self.errors}
Duration: {self.total_duration_seconds:.1f}s
Threshold: {'PASSED' if self.passed_threshold else 'FAILED'} (≥95% required)"""


class RegressionTestRunner:
    """
    Runs regression tests on patched code.
    
    Executes existing pytest suite and validates pass rate.
    
    Usage:
        >>> runner = RegressionTestRunner()
        >>> report = await runner.run_tests(
        ...     test_dir="/path/to/tests",
        ...     environment="patched"
        ... )
        >>> if report.passed_threshold:
        ...     print("Regression tests passed!")
        >>> else:
        ...     print(f"Failed: {report.failed} tests")
    """
    
    def __init__(
        self,
        pytest_args: Optional[List[str]] = None,
        pass_rate_threshold: float = 0.95
    ):
        """
        Initialize regression test runner.
        
        Args:
            pytest_args: Additional pytest arguments
            pass_rate_threshold: Minimum pass rate (default 95%)
        """
        self.pytest_args = pytest_args or []
        self.pass_rate_threshold = pass_rate_threshold
        
        logger.info(
            f"Initialized RegressionTestRunner: threshold={pass_rate_threshold}"
        )
    
    async def run_tests(
        self,
        test_dir: Path | str,
        environment: str = "default",
        timeout: int = 300
    ) -> RegressionTestReport:
        """
        Run regression tests.
        
        Args:
            test_dir: Directory containing tests
            environment: Environment name (e.g., "patched", "vulnerable")
            timeout: Max execution time in seconds
        
        Returns:
            RegressionTestReport with results
        """
        test_dir = Path(test_dir)
        start_time = datetime.now()
        
        logger.info(f"Running regression tests in {test_dir} (env: {environment})")
        
        try:
            # Run pytest with JSON output
            result = await self._run_pytest(test_dir, timeout)
            
            # Parse results
            test_results = self._parse_pytest_output(result)
            
            # Calculate metrics
            total = len(test_results)
            passed = len([t for t in test_results if t.status == TestStatus.PASSED])
            failed = len([t for t in test_results if t.status == TestStatus.FAILED])
            skipped = len([t for t in test_results if t.status == TestStatus.SKIPPED])
            errors = len([t for t in test_results if t.status == TestStatus.ERROR])
            
            pass_rate = passed / total if total > 0 else 0.0
            
            duration = (datetime.now() - start_time).total_seconds()
            
            report = RegressionTestReport(
                total_tests=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                pass_rate=pass_rate,
                total_duration_seconds=duration,
                test_results=test_results,
                executed_at=start_time,
                metadata={
                    "test_dir": str(test_dir),
                    "environment": environment,
                    "pytest_args": self.pytest_args
                }
            )
            
            logger.info(
                f"Regression tests complete: {passed}/{total} passed "
                f"({pass_rate * 100:.1f}%)"
            )
            
            return report
            
        except subprocess.TimeoutExpired:
            logger.error(f"Regression tests timeout after {timeout}s")
            
            return RegressionTestReport(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                pass_rate=0.0,
                total_duration_seconds=timeout,
                test_results=[],
                executed_at=start_time,
                metadata={"error": "timeout", "environment": environment}
            )
        
        except Exception as e:
            logger.error(f"Regression tests error: {e}", exc_info=True)
            
            return RegressionTestReport(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                pass_rate=0.0,
                total_duration_seconds=(datetime.now() - start_time).total_seconds(),
                test_results=[],
                executed_at=start_time,
                metadata={"error": str(e), "environment": environment}
            )
    
    async def _run_pytest(
        self,
        test_dir: Path,
        timeout: int
    ) -> subprocess.CompletedProcess:
        """
        Run pytest and capture output.
        
        Args:
            test_dir: Test directory
            timeout: Timeout in seconds
        
        Returns:
            CompletedProcess with results
        """
        # Build pytest command
        cmd = [
            "pytest",
            str(test_dir),
            "--json-report",
            "--json-report-file=/tmp/pytest_report.json",
            "-v",
            "--tb=short",
        ] + self.pytest_args
        
        logger.debug(f"Running: {' '.join(cmd)}")
        
        # Run pytest
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return result
    
    def _parse_pytest_output(
        self,
        result: subprocess.CompletedProcess
    ) -> List[TestResult]:
        """
        Parse pytest output to extract test results.
        
        Args:
            result: CompletedProcess from pytest
        
        Returns:
            List of TestResult objects
        """
        test_results = []
        
        # Try to parse JSON report first
        json_report_path = Path("/tmp/pytest_report.json")
        if json_report_path.exists():
            try:
                with open(json_report_path) as f:
                    data = json.load(f)
                
                for test in data.get("tests", []):
                    test_results.append(TestResult(
                        test_name=test.get("nodeid", "unknown"),
                        status=TestStatus(test.get("outcome", "error")),
                        duration_seconds=test.get("duration", 0.0),
                        error_message=test.get("call", {}).get("longrepr")
                    ))
                
                return test_results
            
            except Exception as e:
                logger.warning(f"Failed to parse JSON report: {e}")
        
        # Fallback: Parse stdout
        return self._parse_pytest_stdout(result.stdout)
    
    def _parse_pytest_stdout(self, stdout: str) -> List[TestResult]:
        """
        Parse pytest stdout output (fallback).
        
        Args:
            stdout: pytest stdout
        
        Returns:
            List of TestResult objects
        """
        test_results = []
        
        for line in stdout.splitlines():
            # Look for test results (e.g., "test_foo.py::test_bar PASSED")
            if " PASSED" in line or " FAILED" in line or " SKIPPED" in line:
                parts = line.split()
                if len(parts) >= 2:
                    test_name = parts[0]
                    status_str = parts[1].lower()
                    
                    status = TestStatus.PASSED
                    if "failed" in status_str:
                        status = TestStatus.FAILED
                    elif "skipped" in status_str:
                        status = TestStatus.SKIPPED
                    
                    test_results.append(TestResult(
                        test_name=test_name,
                        status=status,
                        duration_seconds=0.0,
                        error_message=None
                    ))
        
        return test_results


# Convenience function
async def run_regression_tests(
    test_dir: Path | str,
    environment: str = "patched",
    pass_rate_threshold: float = 0.95
) -> RegressionTestReport:
    """
    Quick function to run regression tests.
    
    Args:
        test_dir: Test directory
        environment: Environment name
        pass_rate_threshold: Minimum pass rate
    
    Returns:
        RegressionTestReport
    
    Example:
        >>> report = await run_regression_tests("/path/to/tests")
        >>> if report.passed_threshold:
        ...     print("All regression tests passed!")
    """
    runner = RegressionTestRunner(pass_rate_threshold=pass_rate_threshold)
    return await runner.run_tests(test_dir, environment)
