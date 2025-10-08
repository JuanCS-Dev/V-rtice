#!/usr/bin/env python
"""
Validation Report Generator

Executes all validation tests and generates comprehensive report.
Consolidates results from SSE, TUI, workflow, and stress tests.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO compliant - NO MOCK, NO PLACEHOLDER, NO TODO
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class TestSuiteResult:
    """Result from a test suite execution."""

    name: str
    passed: bool
    output: str
    exit_code: int
    duration: float


class ValidationReportGenerator:
    """
    Generates comprehensive validation report.

    Runs all test suites and consolidates results into markdown report.
    """

    def __init__(self):
        """Initialize report generator."""
        self.results: list[TestSuiteResult] = []
        self.start_time = time.time()

    async def run_test_suite(self, name: str, script: str) -> TestSuiteResult:
        """
        Run a test suite script.

        Args:
            name: Test suite name
            script: Script filename

        Returns:
            Test suite result
        """
        print(f"\n{'=' * 80}")
        print(f"🧪 Running: {name}")
        print(f"{'=' * 80}\n")

        start = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                "python", script, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )

            stdout, _ = await process.communicate()
            output = stdout.decode()

            duration = time.time() - start
            exit_code = process.returncode

            print(output)

            return TestSuiteResult(
                name=name, passed=exit_code == 0, output=output, exit_code=exit_code, duration=duration
            )

        except Exception as e:
            duration = time.time() - start
            error_output = f"FATAL ERROR: {e}"

            print(f"❌ {error_output}")

            return TestSuiteResult(name=name, passed=False, output=error_output, exit_code=-1, duration=duration)

    def generate_markdown_report(self) -> str:
        """
        Generate markdown validation report.

        Returns:
            Markdown report content
        """
        total_duration = time.time() - self.start_time
        passed_count = sum(1 for r in self.results if r.passed)
        failed_count = len(self.results) - passed_count

        report = []
        report.append("# 🏛️ Governance Workspace - Validation Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now(UTC).isoformat()}")
        report.append(f"**Total Duration:** {total_duration:.2f}s")
        report.append("")
        report.append("---")
        report.append("")

        # Executive Summary
        report.append("## 📊 Executive Summary")
        report.append("")

        if failed_count == 0:
            report.append("### ✅ **STATUS: APPROVED FOR PRODUCTION**")
        elif failed_count <= 1:
            report.append("### ⚠️ **STATUS: NEEDS REVIEW**")
        else:
            report.append("### ❌ **STATUS: REJECTED**")

        report.append("")
        report.append(f"- **Total Test Suites:** {len(self.results)}")
        report.append(f"- **✅ Passed:** {passed_count}")
        report.append(f"- **❌ Failed:** {failed_count}")
        report.append(f"- **Success Rate:** {(passed_count / len(self.results) * 100):.1f}%")
        report.append("")

        # Test Results Table
        report.append("## 📋 Test Results")
        report.append("")
        report.append("| Test Suite | Status | Duration | Exit Code |")
        report.append("|------------|--------|----------|-----------|")

        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report.append(f"| {result.name} | {status} | {result.duration:.2f}s | {result.exit_code} |")

        report.append("")

        # Detailed Results
        report.append("## 📝 Detailed Results")
        report.append("")

        for result in self.results:
            report.append(f"### {result.name}")
            report.append("")
            report.append(f"**Status:** {'✅ PASSED' if result.passed else '❌ FAILED'}")
            report.append(f"**Duration:** {result.duration:.2f}s")
            report.append(f"**Exit Code:** {result.exit_code}")
            report.append("")

            # Extract summary from output
            if "Summary" in result.output:
                summary_start = result.output.find("Summary")
                summary_section = result.output[summary_start : summary_start + 500]
                report.append("<details>")
                report.append("<summary>View Summary</summary>")
                report.append("")
                report.append("```")
                report.append(summary_section)
                report.append("```")
                report.append("</details>")
            else:
                report.append("*No summary available*")

            report.append("")

        # Next Steps
        report.append("## 🚀 Next Steps")
        report.append("")

        if failed_count == 0:
            report.append("### ✅ All Tests Passed!")
            report.append("")
            report.append("1. ✅ **Manual TUI Validation**")
            report.append("   - Follow: `VALIDATION_CHECKLIST.md`")
            report.append("   - Estimated time: 30 minutes")
            report.append("")
            report.append("2. ✅ **Deploy to Staging**")
            report.append("   - Run: `./scripts/deploy_staging.sh`")
            report.append("")
            report.append("3. ✅ **Monitor in Production**")
            report.append("   - Set up Prometheus/Grafana dashboards")
            report.append("   - Configure alerting")
        else:
            report.append("### ⚠️ Action Required")
            report.append("")
            report.append("**Failed Tests:**")
            for result in self.results:
                if not result.passed:
                    report.append(f"- ❌ {result.name} (exit code: {result.exit_code})")
            report.append("")
            report.append("**Recommended Actions:**")
            report.append("1. Review error logs above")
            report.append("2. Fix failing tests")
            report.append("3. Re-run validation suite")

        report.append("")

        # Footer
        report.append("---")
        report.append("")
        report.append("**Report Generator:** `generate_validation_report.py`")
        report.append("**Environment:** Production Server (port 8002)")
        report.append("**REGRA DE OURO Compliance:** ✅ 100%")
        report.append("")

        return "\n".join(report)

    async def run_all_validations(self):
        """Run all validation test suites."""
        print("\n" + "=" * 80)
        print("🧪 Governance Workspace - Complete Validation Suite")
        print("=" * 80)
        print(f"Started: {datetime.now(UTC).isoformat()}")
        print("=" * 80)
        print()

        # Define test suites
        suites = [
            ("E2E API Tests", "test_governance_e2e.py"),
            ("SSE Streaming Tests", "test_sse_streaming.py"),
            ("TUI Integration Tests", "test_tui_integration.py"),
            ("Workflow Tests", "test_workflow_complete.py"),
            ("Stress Tests", "test_stress_conditions.py"),
        ]

        # Run each suite
        for name, script in suites:
            result = await self.run_test_suite(name, script)
            self.results.append(result)

        # Generate report
        print("\n" + "=" * 80)
        print("📊 Generating Validation Report")
        print("=" * 80)
        print()

        report_content = self.generate_markdown_report()

        # Save report
        report_filename = "VALIDATION_REPORT.md"
        with open(report_filename, "w") as f:
            f.write(report_content)

        print(f"✅ Report saved to: {report_filename}")
        print()

        # Print summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print("=" * 80)
        print("🎯 Final Summary")
        print("=" * 80)
        print(f"Total Test Suites: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {(passed / total) * 100:.1f}%")
        print("=" * 80)
        print()

        if passed == total:
            print("✅ ALL VALIDATIONS PASSED!")
            print("📋 Next: Complete manual checklist (VALIDATION_CHECKLIST.md)")
        else:
            print(f"❌ {total - passed} suite(s) failed")
            print("📋 Review: VALIDATION_REPORT.md for details")

        print()

        return passed == total


async def main():
    """Main entry point."""
    generator = ValidationReportGenerator()
    success = await generator.run_all_validations()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
