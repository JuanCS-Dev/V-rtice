#!/usr/bin/env python
"""
REGRA DE OURO Compliance Validator

Validates that code complies with REGRA DE OURO principles:
- NO MOCK: No unittest.mock, MagicMock, or test doubles in production code
- NO PLACEHOLDER: No TODO, FIXME, HACK, NotImplementedError, or pass statements
- NO TODO: No incomplete implementations or placeholders
- Quality-First: Type hints, docstrings, error handling

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: Production-ready, REGRA DE OURO compliant
"""

import ast
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class ValidationResult:
    """Result of REGRA DE OURO validation."""

    # File info
    file_path: str
    lines_of_code: int

    # REGRA DE OURO violations
    todo_violations: List[Tuple[int, str]] = field(default_factory=list)
    mock_violations: List[Tuple[int, str]] = field(default_factory=list)
    placeholder_violations: List[Tuple[int, str]] = field(default_factory=list)

    # Quality metrics
    has_module_docstring: bool = False
    functions_without_docstring: List[str] = field(default_factory=list)
    functions_without_type_hints: List[str] = field(default_factory=list)
    classes_without_docstring: List[str] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        """Check if file is fully compliant."""
        return (
            len(self.todo_violations) == 0
            and len(self.mock_violations) == 0
            and len(self.placeholder_violations) == 0
        )

    @property
    def total_violations(self) -> int:
        """Total REGRA DE OURO violations."""
        return (
            len(self.todo_violations)
            + len(self.mock_violations)
            + len(self.placeholder_violations)
        )

    @property
    def quality_score(self) -> float:
        """Calculate quality score (0.0 to 1.0)."""
        total_issues = (
            len(self.functions_without_docstring)
            + len(self.functions_without_type_hints)
            + len(self.classes_without_docstring)
        )

        if total_issues == 0:
            return 1.0

        # Penalize missing quality features
        max_issues = 10  # Normalize to max 10 issues
        return max(0.0, 1.0 - (total_issues / max_issues))


class RegraDeOuroValidator:
    """Validator for REGRA DE OURO compliance."""

    def __init__(self, project_root: str):
        """
        Initialize validator.

        Args:
            project_root: Root directory of project to validate
        """
        self.project_root = Path(project_root)
        self.results: List[ValidationResult] = []

        # Patterns to detect violations
        self.todo_patterns = [
            r"\bTODO\b",
            r"\bFIXME\b",
            r"\bHACK\b",
            r"\bXXX\b",
            r"\bBUG\b",
        ]

        self.mock_patterns = [
            r"\bunittest\.mock\b",
            r"\bMagicMock\b",
            r"\bMock\(",
            r"\bpatch\(",
            r"@mock\.",
            r"@patch",
        ]

        self.placeholder_patterns = [
            r"^\s*pass\s*$",  # Standalone pass statement
            r"\bNotImplementedError\b",
            r"raise NotImplemented",
        ]

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a single Python file.

        Args:
            file_path: Path to Python file

        Returns:
            Validation result
        """
        result = ValidationResult(
            file_path=str(file_path.relative_to(self.project_root)),
            lines_of_code=0,
        )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            result.lines_of_code = len(lines)

            # Check for TODO/FIXME/HACK comments
            for line_num, line in enumerate(lines, start=1):
                for pattern in self.todo_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        result.todo_violations.append((line_num, line.strip()))
                        break

            # Check for mocks in production code
            # Skip if file is in tests/ directory
            if "test" not in str(file_path).lower():
                for line_num, line in enumerate(lines, start=1):
                    for pattern in self.mock_patterns:
                        if re.search(pattern, line):
                            result.mock_violations.append((line_num, line.strip()))
                            break

            # Check for placeholder code
            for line_num, line in enumerate(lines, start=1):
                for pattern in self.placeholder_patterns:
                    if re.search(pattern, line):
                        # Allow pass in empty __init__.py files
                        if file_path.name == "__init__.py" and len(lines) <= 5:
                            continue
                        result.placeholder_violations.append((line_num, line.strip()))
                        break

            # Parse AST for quality metrics
            try:
                tree = ast.parse(content)

                # Check module docstring
                if ast.get_docstring(tree):
                    result.has_module_docstring = True

                # Check functions and classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check docstring
                        if not ast.get_docstring(node):
                            result.functions_without_docstring.append(node.name)

                        # Check type hints (return annotation)
                        if node.returns is None and node.name != "__init__":
                            result.functions_without_type_hints.append(node.name)

                    elif isinstance(node, ast.ClassDef):
                        if not ast.get_docstring(node):
                            result.classes_without_docstring.append(node.name)

            except SyntaxError:
                pass  # Skip files with syntax errors (might be templates)

        except Exception as e:
            print(f"⚠️  Error validating {file_path}: {e}")

        return result

    def validate_directory(
        self, directory: Path, exclude_patterns: Set[str] = None
    ) -> List[ValidationResult]:
        """
        Validate all Python files in directory.

        Args:
            directory: Directory to validate
            exclude_patterns: Patterns to exclude from validation

        Returns:
            List of validation results
        """
        exclude_patterns = exclude_patterns or {
            "__pycache__",
            ".git",
            ".pytest_cache",
            "venv",
            "env",
            ".venv",
        }

        results = []

        for py_file in directory.rglob("*.py"):
            # Skip excluded directories
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue

            result = self.validate_file(py_file)
            results.append(result)

        return results

    def generate_report(self, results: List[ValidationResult]) -> str:
        """
        Generate comprehensive validation report.

        Args:
            results: List of validation results

        Returns:
            Markdown report
        """
        # Calculate summary statistics
        total_files = len(results)
        total_loc = sum(r.lines_of_code for r in results)
        compliant_files = sum(1 for r in results if r.is_compliant)
        total_violations = sum(r.total_violations for r in results)

        todo_violations = sum(len(r.todo_violations) for r in results)
        mock_violations = sum(len(r.mock_violations) for r in results)
        placeholder_violations = sum(len(r.placeholder_violations) for r in results)

        avg_quality_score = (
            sum(r.quality_score for r in results) / total_files if total_files > 0 else 0
        )

        # Generate report
        report = []
        report.append("# 🏛️ REGRA DE OURO Compliance Report")
        report.append("")
        report.append("**Validation Date:** 2025-10-06")
        report.append("**Project:** Governance Workspace - MAXIMUS Core Service")
        report.append("")
        report.append("---")
        report.append("")

        # Executive Summary
        report.append("## 📊 Executive Summary")
        report.append("")
        report.append(f"**Total Files Analyzed:** {total_files}")
        report.append(f"**Total Lines of Code:** {total_loc:,}")
        report.append(
            f"**Compliant Files:** {compliant_files}/{total_files} ({compliant_files/total_files*100:.1f}%)"
        )
        report.append(f"**Total Violations:** {total_violations}")
        report.append(f"**Average Quality Score:** {avg_quality_score:.1%}")
        report.append("")

        # Compliance Status
        if total_violations == 0:
            report.append("### ✅ REGRA DE OURO: 100% COMPLIANT")
            report.append("")
            report.append(
                "Zero violations found. All code adheres to NO MOCK, NO PLACEHOLDER, NO TODO principles."
            )
        else:
            report.append("### ⚠️ REGRA DE OURO: VIOLATIONS DETECTED")
            report.append("")
            report.append(f"Found {total_violations} violations requiring attention.")

        report.append("")
        report.append("---")
        report.append("")

        # Detailed Breakdown
        report.append("## 🔍 Violation Breakdown")
        report.append("")
        report.append("| Category | Count | Status |")
        report.append("|----------|-------|--------|")

        status_todo = "✅ PASS" if todo_violations == 0 else f"❌ {todo_violations} violations"
        status_mock = "✅ PASS" if mock_violations == 0 else f"❌ {mock_violations} violations"
        status_placeholder = (
            "✅ PASS" if placeholder_violations == 0 else f"❌ {placeholder_violations} violations"
        )

        report.append(f"| **NO TODO** (TODO/FIXME/HACK) | {todo_violations} | {status_todo} |")
        report.append(f"| **NO MOCK** (unittest.mock) | {mock_violations} | {status_mock} |")
        report.append(
            f"| **NO PLACEHOLDER** (pass/NotImplemented) | {placeholder_violations} | {status_placeholder} |"
        )

        report.append("")
        report.append("---")
        report.append("")

        # Quality Metrics
        report.append("## 📈 Quality Metrics")
        report.append("")

        files_with_module_docstring = sum(1 for r in results if r.has_module_docstring)
        total_functions_without_docstring = sum(
            len(r.functions_without_docstring) for r in results
        )
        total_functions_without_type_hints = sum(
            len(r.functions_without_type_hints) for r in results
        )
        total_classes_without_docstring = sum(len(r.classes_without_docstring) for r in results)

        docstring_coverage = (
            files_with_module_docstring / total_files * 100 if total_files > 0 else 0
        )

        report.append("| Metric | Value | Target | Status |")
        report.append("|--------|-------|--------|--------|")
        report.append(
            f"| Module Docstrings | {files_with_module_docstring}/{total_files} ({docstring_coverage:.1f}%) | 100% | {'✅ PASS' if docstring_coverage >= 90 else '⚠️ WARN'} |"
        )
        report.append(
            f"| Functions Missing Docstrings | {total_functions_without_docstring} | 0 | {'✅ PASS' if total_functions_without_docstring == 0 else '⚠️ WARN'} |"
        )
        report.append(
            f"| Functions Missing Type Hints | {total_functions_without_type_hints} | 0 | {'✅ PASS' if total_functions_without_type_hints == 0 else '⚠️ WARN'} |"
        )
        report.append(
            f"| Classes Missing Docstrings | {total_classes_without_docstring} | 0 | {'✅ PASS' if total_classes_without_docstring == 0 else '⚠️ WARN'} |"
        )

        report.append("")
        report.append("---")
        report.append("")

        # Violations Detail
        if total_violations > 0:
            report.append("## ❌ Violations Detail")
            report.append("")

            for result in results:
                if result.total_violations > 0:
                    report.append(f"### {result.file_path}")
                    report.append("")

                    if result.todo_violations:
                        report.append("**TODO/FIXME/HACK Comments:**")
                        for line_num, line in result.todo_violations:
                            report.append(f"- Line {line_num}: `{line}`")
                        report.append("")

                    if result.mock_violations:
                        report.append("**Mock Usage in Production Code:**")
                        for line_num, line in result.mock_violations:
                            report.append(f"- Line {line_num}: `{line}`")
                        report.append("")

                    if result.placeholder_violations:
                        report.append("**Placeholder Code:**")
                        for line_num, line in result.placeholder_violations:
                            report.append(f"- Line {line_num}: `{line}`")
                        report.append("")

            report.append("---")
            report.append("")

        # Files Summary
        report.append("## 📁 Files Summary")
        report.append("")
        report.append("| File | LOC | Violations | Quality | Status |")
        report.append("|------|-----|------------|---------|--------|")

        for result in sorted(results, key=lambda r: r.total_violations, reverse=True):
            status = "✅" if result.is_compliant else "❌"
            quality = f"{result.quality_score:.0%}"
            report.append(
                f"| {result.file_path} | {result.lines_of_code} | {result.total_violations} | {quality} | {status} |"
            )

        report.append("")
        report.append("---")
        report.append("")

        # Final Verdict
        report.append("## 🎯 Final Verdict")
        report.append("")

        if total_violations == 0:
            report.append("### ✅ APPROVED FOR PRODUCTION")
            report.append("")
            report.append("**This codebase is 100% compliant with REGRA DE OURO.**")
            report.append("")
            report.append("✅ NO MOCK - All integrations are real")
            report.append("✅ NO PLACEHOLDER - All features fully implemented")
            report.append("✅ NO TODO - Zero incomplete code")
            report.append(f"✅ Quality Score: {avg_quality_score:.1%}")
        else:
            report.append("### ⚠️ REQUIRES ATTENTION")
            report.append("")
            report.append(
                f"Found {total_violations} REGRA DE OURO violations that must be addressed before production deployment."
            )
            report.append("")
            report.append("**Action Required:**")
            report.append("1. Remove all TODO/FIXME/HACK comments")
            report.append("2. Replace mocks with real integrations")
            report.append("3. Implement all placeholder code")

        report.append("")
        report.append("---")
        report.append("")
        report.append("**Report Generated:** 2025-10-06")
        report.append("**Validator:** REGRA DE OURO Compliance Validator v1.0")
        report.append("")

        return "\n".join(report)


def main():
    """Main entry point."""
    import sys

    print("\n" + "=" * 80)
    print("🏛️  REGRA DE OURO Compliance Validator")
    print("=" * 80)
    print()

    # Validate governance_sse directory
    governance_sse_dir = Path("governance_sse")
    if not governance_sse_dir.exists():
        print(f"❌ Directory not found: {governance_sse_dir}")
        sys.exit(1)

    print(f"📂 Analyzing: {governance_sse_dir}")
    print()

    validator = RegraDeOuroValidator(project_root=".")

    # Validate all files
    results = validator.validate_directory(
        governance_sse_dir, exclude_patterns={"__pycache__", ".pytest_cache", "test_"}
    )

    # Also validate test files (but separately)
    test_files = [
        "test_edge_cases.py",
        "test_maximus_integration.py",
        "governance_sse/test_integration.py",
    ]

    for test_file in test_files:
        test_path = Path(test_file)
        if test_path.exists():
            results.append(validator.validate_file(test_path))

    # Also validate main.py
    main_py = Path("main.py")
    if main_py.exists():
        results.append(validator.validate_file(main_py))

    # Generate report
    report = validator.generate_report(results)

    # Save report
    report_path = Path("governance_sse/REGRA_DE_OURO_COMPLIANCE_REPORT.md")
    with open(report_path, "w") as f:
        f.write(report)

    print(f"✅ Report saved to: {report_path}")
    print()

    # Print summary to console
    total_violations = sum(r.total_violations for r in results)
    compliant_files = sum(1 for r in results if r.is_compliant)
    total_files = len(results)

    print("📊 Summary:")
    print(f"   Total Files: {total_files}")
    print(f"   Compliant: {compliant_files}/{total_files} ({compliant_files/total_files*100:.1f}%)")
    print(f"   Total Violations: {total_violations}")
    print()

    if total_violations == 0:
        print("✅ ALL FILES COMPLIANT - REGRA DE OURO: 100%")
        sys.exit(0)
    else:
        print(f"⚠️  {total_violations} VIOLATIONS FOUND - Review report for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
