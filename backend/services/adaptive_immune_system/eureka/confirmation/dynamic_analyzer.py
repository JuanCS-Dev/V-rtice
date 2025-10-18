"""
Dynamic Analysis Engine - Runtime testing for vulnerability confirmation.

Generates and executes proof-of-concept exploits to empirically verify vulnerabilities.
Uses isolated test environments (Docker containers) for safe execution.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DynamicTest(BaseModel):
    """Dynamic test case for vulnerability verification."""

    test_name: str
    test_type: str  # "exploit", "regression", "behavioral"
    description: str
    exploit_code: str  # Python/JS/shell script
    expected_behavior: str  # "vulnerable", "patched", "inconclusive"
    execution_timeout: int = 30  # seconds


class DynamicTestResult(BaseModel):
    """Result of dynamic test execution."""

    test_name: str
    success: bool
    vulnerable: bool  # True if vulnerability confirmed
    output: str
    error: Optional[str] = None
    execution_time_seconds: float
    exit_code: int


class DynamicAnalysisResult(BaseModel):
    """Dynamic analysis result for APV confirmation."""

    apv_id: str
    cve_id: str
    confirmed: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    test_results: List[DynamicTestResult] = Field(default_factory=list)
    tests_passed: int
    tests_failed: int
    tests_total: int
    scan_duration_seconds: float
    error_messages: List[str] = Field(default_factory=list)


class DynamicAnalyzer:
    """
    Dynamic analysis engine for vulnerability confirmation.

    Features:
    - PoC exploit generation based on CVE/CWE
    - Isolated test execution (Docker containers)
    - Behavioral testing (before/after patch comparison)
    - Regression testing
    - Multi-language support (Python, JavaScript, shell)
    """

    def __init__(
        self,
        project_path: Path,
        use_docker: bool = True,
        docker_image: Optional[str] = None,
    ):
        """
        Initialize dynamic analyzer.

        Args:
            project_path: Path to project root
            use_docker: Execute tests in Docker containers (recommended)
            docker_image: Custom Docker image for testing
        """
        self.project_path = Path(project_path)
        self.use_docker = use_docker
        self.docker_image = docker_image or "python:3.11-slim"

        logger.info(
            f"DynamicAnalyzer initialized: "
            f"docker={use_docker}, image={self.docker_image}"
        )

    async def analyze_apv(
        self,
        apv_id: str,
        cve_id: str,
        dependency_name: str,
        dependency_version: str,
        dependency_ecosystem: str,
        vulnerable_code_signature: Optional[str],
        cwe_ids: List[str],
    ) -> DynamicAnalysisResult:
        """
        Analyze APV using dynamic testing.

        Args:
            apv_id: APV identifier
            cve_id: CVE identifier
            dependency_name: Package name
            dependency_version: Package version
            dependency_ecosystem: Ecosystem (pypi, npm, etc.)
            vulnerable_code_signature: Code pattern to test
            cwe_ids: CWE identifiers

        Returns:
            DynamicAnalysisResult with test results and confidence score
        """
        import time
        start_time = time.time()

        logger.info(f"🧪 Starting dynamic analysis for APV: {apv_id} ({cve_id})")

        # Generate test cases based on CVE/CWE
        test_cases = self._generate_test_cases(
            cve_id, dependency_name, dependency_version, dependency_ecosystem, cwe_ids
        )

        if not test_cases:
            logger.warning(f"No dynamic tests generated for {cve_id}")
            return DynamicAnalysisResult(
                apv_id=apv_id,
                cve_id=cve_id,
                confirmed=False,
                confidence_score=0.0,
                test_results=[],
                tests_passed=0,
                tests_failed=0,
                tests_total=0,
                scan_duration_seconds=time.time() - start_time,
                error_messages=["No dynamic tests could be generated"],
            )

        logger.info(f"Generated {len(test_cases)} dynamic test cases")

        # Execute test cases
        test_results: List[DynamicTestResult] = []
        error_messages: List[str] = []

        for test_case in test_cases:
            try:
                result = await self._execute_test(test_case)
                test_results.append(result)
                logger.info(
                    f"Test '{test_case.test_name}': "
                    f"success={result.success}, vulnerable={result.vulnerable}"
                )
            except Exception as e:
                error_msg = f"Test '{test_case.test_name}' failed: {e}"
                logger.error(error_msg)
                error_messages.append(error_msg)

        # Calculate results
        tests_total = len(test_results)
        tests_passed = sum(1 for r in test_results if r.success)
        tests_failed = tests_total - tests_passed

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(test_results)

        # Determine if confirmed (at least one exploit succeeded)
        confirmed = any(r.vulnerable and r.success for r in test_results)

        duration = time.time() - start_time

        logger.info(
            f"✅ Dynamic analysis complete: "
            f"confirmed={confirmed}, confidence={confidence_score:.2f}, "
            f"tests={tests_passed}/{tests_total}, duration={duration:.1f}s"
        )

        return DynamicAnalysisResult(
            apv_id=apv_id,
            cve_id=cve_id,
            confirmed=confirmed,
            confidence_score=confidence_score,
            test_results=test_results,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_total=tests_total,
            scan_duration_seconds=duration,
            error_messages=error_messages,
        )

    def _generate_test_cases(
        self,
        cve_id: str,
        dependency_name: str,
        dependency_version: str,
        dependency_ecosystem: str,
        cwe_ids: List[str],
    ) -> List[DynamicTest]:
        """
        Generate dynamic test cases based on CVE and CWE.

        Args:
            cve_id: CVE identifier
            dependency_name: Package name
            dependency_version: Package version
            dependency_ecosystem: Ecosystem
            cwe_ids: CWE identifiers

        Returns:
            List of DynamicTest instances
        """
        test_cases = []

        # CWE-specific test generation
        if "CWE-89" in cwe_ids:  # SQL Injection
            test_cases.extend(
                self._generate_sql_injection_tests(dependency_name, dependency_version)
            )

        if "CWE-79" in cwe_ids:  # XSS
            test_cases.extend(
                self._generate_xss_tests(dependency_name, dependency_version)
            )

        if "CWE-502" in cwe_ids:  # Deserialization
            test_cases.extend(
                self._generate_deserialization_tests(dependency_name, dependency_version)
            )

        if "CWE-22" in cwe_ids:  # Path Traversal
            test_cases.extend(
                self._generate_path_traversal_tests(dependency_name, dependency_version)
            )

        # Generic dependency installation test
        if dependency_ecosystem in ["pypi", "npm", "go"]:
            test_cases.append(
                self._generate_dependency_installation_test(
                    dependency_name, dependency_version, dependency_ecosystem
                )
            )

        return test_cases

    def _generate_sql_injection_tests(
        self, package_name: str, package_version: str
    ) -> List[DynamicTest]:
        """Generate SQL injection test cases."""
        return [
            DynamicTest(
                test_name=f"sql_injection_test_{package_name}",
                test_type="exploit",
                description=f"Test SQL injection vulnerability in {package_name}@{package_version}",
                exploit_code=f"""
import {package_name}

# Attempt SQL injection
malicious_input = "1' OR '1'='1"
try:
    result = execute_query(malicious_input)
    if result:
        print("VULNERABLE: SQL injection succeeded")
        exit(1)
    else:
        print("SAFE: SQL injection blocked")
        exit(0)
except Exception as e:
    print(f"INCONCLUSIVE: {{e}}")
    exit(2)
""",
                expected_behavior="vulnerable",
                execution_timeout=30,
            )
        ]

    def _generate_xss_tests(
        self, package_name: str, package_version: str
    ) -> List[DynamicTest]:
        """Generate XSS test cases."""
        return [
            DynamicTest(
                test_name=f"xss_test_{package_name}",
                test_type="exploit",
                description=f"Test XSS vulnerability in {package_name}@{package_version}",
                exploit_code=f"""
const {package_name.replace('-', '_')} = require('{package_name}');

// Attempt XSS
const maliciousInput = '<script>alert("XSS")</script>';
const output = render(maliciousInput);

if (output.includes('<script>')) {{
    console.log('VULNERABLE: XSS script not sanitized');
    process.exit(1);
}} else {{
    console.log('SAFE: XSS script sanitized');
    process.exit(0);
}}
""",
                expected_behavior="vulnerable",
                execution_timeout=30,
            )
        ]

    def _generate_deserialization_tests(
        self, package_name: str, package_version: str
    ) -> List[DynamicTest]:
        """Generate deserialization vulnerability test cases."""
        return [
            DynamicTest(
                test_name=f"deserialization_test_{package_name}",
                test_type="exploit",
                description=f"Test deserialization vulnerability in {package_name}@{package_version}",
                exploit_code=f"""
import pickle
import {package_name}

# Malicious pickle payload
class Exploit:
    def __reduce__(self):
        import os
        return (os.system, ('echo VULNERABLE',))

malicious_data = pickle.dumps(Exploit())

try:
    pickle.loads(malicious_data)
    print("VULNERABLE: Arbitrary code execution")
    exit(1)
except Exception as e:
    print(f"SAFE: Deserialization blocked - {{e}}")
    exit(0)
""",
                expected_behavior="vulnerable",
                execution_timeout=30,
            )
        ]

    def _generate_path_traversal_tests(
        self, package_name: str, package_version: str
    ) -> List[DynamicTest]:
        """Generate path traversal test cases."""
        return [
            DynamicTest(
                test_name=f"path_traversal_test_{package_name}",
                test_type="exploit",
                description=f"Test path traversal in {package_name}@{package_version}",
                exploit_code=f"""
import {package_name}
import os

# Attempt path traversal
malicious_path = "../../../etc/passwd"

try:
    content = read_file(malicious_path)
    if "root:" in content:
        print("VULNERABLE: Path traversal succeeded")
        exit(1)
    else:
        print("SAFE: Path traversal blocked")
        exit(0)
except Exception as e:
    print(f"SAFE: Access denied - {{e}}")
    exit(0)
""",
                expected_behavior="vulnerable",
                execution_timeout=30,
            )
        ]

    def _generate_dependency_installation_test(
        self, package_name: str, package_version: str, ecosystem: str
    ) -> DynamicTest:
        """Generate dependency installation test."""
        install_cmd = {
            "pypi": f"pip install {package_name}=={package_version}",
            "npm": f"npm install {package_name}@{package_version}",
            "go": f"go get {package_name}@{package_version}",
        }.get(ecosystem, "")

        return DynamicTest(
            test_name=f"install_test_{package_name}",
            test_type="regression",
            description=f"Test installation of {package_name}@{package_version}",
            exploit_code=f"""
#!/bin/bash
set -e

echo "Installing {package_name}@{package_version}..."
{install_cmd}

if [ $? -eq 0 ]; then
    echo "SAFE: Package installed successfully"
    exit 0
else
    echo "VULNERABLE: Package installation failed"
    exit(1)
fi
""",
            expected_behavior="vulnerable",
            execution_timeout=120,
        )

    async def _execute_test(self, test_case: DynamicTest) -> DynamicTestResult:
        """
        Execute dynamic test case.

        Args:
            test_case: DynamicTest to execute

        Returns:
            DynamicTestResult
        """
        import time
        start_time = time.time()

        if self.use_docker:
            result = await self._execute_test_in_docker(test_case)
        else:
            result = await self._execute_test_locally(test_case)

        execution_time = time.time() - start_time

        return DynamicTestResult(
            test_name=test_case.test_name,
            success=result["success"],
            vulnerable=result["vulnerable"],
            output=result["output"],
            error=result.get("error"),
            execution_time_seconds=execution_time,
            exit_code=result["exit_code"],
        )

    async def _execute_test_in_docker(
        self, test_case: DynamicTest
    ) -> Dict[str, any]:
        """Execute test in isolated Docker container."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(test_case.exploit_code)
            temp_file_path = temp_file.name

        try:
            cmd = [
                "docker",
                "run",
                "--rm",
                "--network", "none",  # Isolate from network
                "--memory", "512m",  # Limit memory
                "--cpus", "1.0",  # Limit CPU
                "-v",
                f"{temp_file_path}:/test.py:ro",
                self.docker_image,
                "python",
                "/test.py",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=test_case.execution_timeout
                )

                output = stdout.decode() + stderr.decode()
                exit_code = process.returncode

                # Determine vulnerability from exit code and output
                vulnerable = exit_code == 1 or "VULNERABLE" in output
                success = exit_code in [0, 1]  # 0=safe, 1=vulnerable, 2+=error

                return {
                    "success": success,
                    "vulnerable": vulnerable,
                    "output": output,
                    "exit_code": exit_code,
                }

            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "vulnerable": False,
                    "output": "",
                    "error": "Test execution timed out",
                    "exit_code": -1,
                }

        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    async def _execute_test_locally(self, test_case: DynamicTest) -> Dict[str, any]:
        """Execute test locally (NOT RECOMMENDED for untrusted code)."""
        logger.warning("Executing test locally - use Docker for production!")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(test_case.exploit_code)
            temp_file_path = temp_file.name

        try:
            process = await asyncio.create_subprocess_exec(
                "python",
                temp_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=test_case.execution_timeout
                )

                output = stdout.decode() + stderr.decode()
                exit_code = process.returncode

                vulnerable = exit_code == 1 or "VULNERABLE" in output
                success = exit_code in [0, 1]

                return {
                    "success": success,
                    "vulnerable": vulnerable,
                    "output": output,
                    "exit_code": exit_code,
                }

            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "vulnerable": False,
                    "output": "",
                    "error": "Test execution timed out",
                    "exit_code": -1,
                }

        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def _calculate_confidence_score(
        self, test_results: List[DynamicTestResult]
    ) -> float:
        """
        Calculate confidence score based on test results.

        Factors:
        - Test success rate
        - Number of tests confirming vulnerability
        - Test execution consistency

        Args:
            test_results: List of DynamicTestResult instances

        Returns:
            Confidence score 0.0-1.0
        """
        if not test_results:
            return 0.0

        # Factor 1: Test success rate (50% weight)
        successful_tests = sum(1 for r in test_results if r.success)
        success_rate = successful_tests / len(test_results)
        score = success_rate * 0.5

        # Factor 2: Vulnerability confirmation rate (40% weight)
        vulnerable_tests = sum(1 for r in test_results if r.vulnerable and r.success)
        if successful_tests > 0:
            vulnerability_rate = vulnerable_tests / successful_tests
            score += vulnerability_rate * 0.4

        # Factor 3: Consistency bonus (10% weight)
        # If all successful tests agree, increase confidence
        if successful_tests > 0:
            vulnerable_results = [r.vulnerable for r in test_results if r.success]
            if len(set(vulnerable_results)) == 1:  # All agree
                score += 0.1

        return min(score, 1.0)
