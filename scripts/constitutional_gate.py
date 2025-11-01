#!/usr/bin/env python3
"""
Constitutional Gate - CI/CD Validator (PRODUCTION READY)

Valida compliance constitucional em CI/CD pipeline com robustez empresarial.

Falha o build se:
- Serviço não tem observabilidade constitucional
- Cobertura de testes < 90%
- Violações P1 detectadas (TODOs, NotImplementedError, placeholders)
- CRS/LEI/FPC fora dos requisitos

Usage:
    python scripts/constitutional_gate.py <service_name>
    python scripts/constitutional_gate.py --all  # Check all services
    python scripts/constitutional_gate.py --json  # JSON output for CI/CD

Exit codes:
    0: PASSED - Constitutional compliance OK
    1: FAILED - Constitutional violations detected
    2: ERROR - Script error (invalid input, service not found)

Author: Vértice Platform Team
Version: 2.0.0 (Production Ready)
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class ConstitutionalGate:
    """Validates constitutional compliance for CI/CD with production-grade robustness."""

    # Security: Only allow alphanumeric, underscore, hyphen in service names
    VALID_SERVICE_NAME = re.compile(r"^[a-zA-Z0-9_-]+$")

    def __init__(
        self,
        service_name: str,
        base_path: Path | None = None,
        json_output: bool = False,
    ):
        """
        Initialize constitutional gate validator.

        Args:
            service_name: Name of service to validate
            base_path: Optional base path (for testing), defaults to backend/services
            json_output: If True, output results as JSON
        """
        # Validate service name to prevent path traversal
        if not self.VALID_SERVICE_NAME.match(service_name):
            raise ValidationError(
                f"Invalid service name: '{service_name}'. "
                f"Only alphanumeric, underscore, and hyphen allowed."
            )

        self.service_name = service_name
        self.json_output = json_output
        self.violations: list[str] = []
        self.warnings: list[str] = []

        # Setup paths with security validation
        self.services_dir = base_path or Path("backend/services")
        self.service_path = self.services_dir / service_name

        # Validate paths exist and are within expected directory
        self._validate_paths()

        logger.info(f"Initialized validation for service: {service_name}")

    def _validate_paths(self):
        """Validate that paths exist and are within expected directory tree."""
        # Check services directory exists
        if not self.services_dir.exists():
            raise ValidationError(
                f"Services directory not found: {self.services_dir.absolute()}"
            )

        # Check service directory exists
        if not self.service_path.exists():
            raise ValidationError(
                f"Service not found: {self.service_name} "
                f"(expected at {self.service_path.absolute()})"
            )

        if not self.service_path.is_dir():
            raise ValidationError(
                f"Service path is not a directory: {self.service_path.absolute()}"
            )

        # Security: Prevent path traversal by ensuring service_path is within services_dir
        try:
            self.service_path.resolve().relative_to(self.services_dir.resolve())
        except ValueError:
            raise ValidationError(
                f"Security violation: Service path '{self.service_path}' "
                f"is outside services directory '{self.services_dir}'"
            )

        logger.debug(f"Path validation passed for {self.service_name}")

    def validate(self) -> bool:
        """
        Run all validation checks.

        Returns:
            bool: True if all checks passed, False otherwise
        """
        if not self.json_output:
            print("=" * 80)
            print(f"🏛️  CONSTITUTIONAL GATE - {self.service_name}")
            print("=" * 80)

        checks = [
            ("Observability", self.check_observability),
            ("Test Coverage", self.check_test_coverage),
            ("P1 Violations", self.check_p1_violations),
            ("Dockerfile", self.check_dockerfile),
        ]

        all_passed = True
        check_results = {}

        for check_name, check_func in checks:
            if not self.json_output:
                print(f"\n📋 {check_name}...")

            try:
                passed = check_func()
                check_results[check_name] = "PASSED" if passed else "FAILED"

                if not passed:
                    all_passed = False
                    if not self.json_output:
                        print("  ❌ FAILED")
                    logger.warning(
                        f"Check failed: {check_name} for {self.service_name}"
                    )
                else:
                    if not self.json_output:
                        print("  ✅ PASSED")
                    logger.debug(f"Check passed: {check_name} for {self.service_name}")

            except Exception as e:
                logger.error(f"Error in check {check_name}: {e}", exc_info=True)
                self.violations.append(
                    f"Check '{check_name}' failed with error: {str(e)}"
                )
                check_results[check_name] = "ERROR"
                all_passed = False
                if not self.json_output:
                    print(f"  💥 ERROR: {e}")

        # Output results
        if self.json_output:
            self._output_json(all_passed, check_results)
        else:
            self._output_text(all_passed)

        return all_passed

    def _output_text(self, all_passed: bool):
        """Output results in human-readable text format."""
        print("\n" + "=" * 80)
        if all_passed:
            print("✅ CONSTITUTIONAL GATE: PASSED")
            logger.info(f"Service {self.service_name} PASSED constitutional gate")
        else:
            print("❌ CONSTITUTIONAL GATE: FAILED")
            logger.warning(f"Service {self.service_name} FAILED constitutional gate")

        if self.violations:
            print("\n🚨 VIOLATIONS:")
            for v in self.violations:
                print(f"  • {v}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for w in self.warnings:
                print(f"  • {w}")

        print("=" * 80)

    def _output_json(self, all_passed: bool, check_results: dict[str, str]):
        """Output results in JSON format for CI/CD parsing."""
        result = {
            "service": self.service_name,
            "status": "PASSED" if all_passed else "FAILED",
            "checks": check_results,
            "violations": self.violations,
            "warnings": self.warnings,
        }
        print(json.dumps(result, indent=2))

    def check_observability(self) -> bool:
        """Check that service has constitutional observability."""
        shared_dir = self.service_path / "shared"

        # Check shared directory exists
        if not shared_dir.exists():
            self.violations.append(
                "Missing 'shared' directory - constitutional libraries not found"
            )
            return False

        required_files = [
            "constitutional_metrics.py",
            "constitutional_tracing.py",
            "health_checks.py",
        ]

        missing = []
        for filename in required_files:
            file_path = shared_dir / filename
            if not file_path.exists():
                missing.append(filename)
            elif not file_path.is_file():
                self.warnings.append(f"{filename} exists but is not a regular file")

        if missing:
            self.violations.append(
                f"Missing constitutional libraries: {', '.join(missing)}"
            )
            return False

        # Check main.py has imports
        main_file = self._find_main_file()

        if main_file:
            try:
                content = main_file.read_text(encoding="utf-8", errors="replace")

                # Check for MetricsExporter
                if "MetricsExporter" not in content:
                    self.violations.append(
                        f"{main_file.name} missing MetricsExporter initialization"
                    )
                    return False

                # Check for ConstitutionalTracer
                if (
                    "constitutional_tracer" not in content
                    and "ConstitutionalTracer" not in content
                ):
                    self.violations.append(
                        f"{main_file.name} missing ConstitutionalTracer initialization"
                    )
                    return False

                logger.debug(f"Observability imports found in {main_file.name}")

            except (OSError, PermissionError) as e:
                logger.error(f"Failed to read {main_file}: {e}")
                self.violations.append(f"Cannot read {main_file.name}: {e}")
                return False
        else:
            self.warnings.append(
                "No main entry point found (main.py, server.py, or app.py)"
            )

        return True

    def _find_main_file(self) -> Path | None:
        """Find main entry point file (main.py, server.py, or app.py)."""
        for filename in ["main.py", "server.py", "app.py"]:
            file_path = self.service_path / filename
            if file_path.exists() and file_path.is_file():
                return file_path
        return None

    def check_test_coverage(self) -> bool:
        """Check test coverage >= 90%."""
        coverage_file = self.service_path / "coverage.json"

        if not coverage_file.exists():
            self.warnings.append("coverage.json not found - run tests first")
            return True  # Warning, not failure

        try:
            with coverage_file.open(encoding="utf-8") as f:
                data = json.load(f)

            # Validate JSON structure
            if not isinstance(data, dict):
                raise ValueError("coverage.json is not a valid JSON object")

            totals = data.get("totals", {})
            if not isinstance(totals, dict):
                raise ValueError("coverage.json missing 'totals' object")

            total_coverage = totals.get("percent_covered")

            # Handle missing or invalid coverage value
            if total_coverage is None:
                raise ValueError("coverage.json missing 'percent_covered' field")

            if not isinstance(total_coverage, (int, float)):
                raise ValueError(
                    f"Invalid percent_covered type: {type(total_coverage)}"
                )

            if total_coverage < 90.0:
                self.violations.append(
                    f"Test coverage {total_coverage:.1f}% < 90% requirement"
                )
                logger.warning(
                    f"Low test coverage for {self.service_name}: {total_coverage:.1f}%"
                )
                return False

            if not self.json_output:
                print(f"  📊 Coverage: {total_coverage:.1f}%")
            logger.info(f"Test coverage for {self.service_name}: {total_coverage:.1f}%")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in coverage.json: {e}")
            self.warnings.append("Failed to parse coverage.json: Invalid JSON")
            return True  # Warning, not failure

        except ValueError as e:
            logger.error(f"Invalid coverage.json structure: {e}")
            self.warnings.append(f"Invalid coverage.json structure: {e}")
            return True  # Warning, not failure

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to read coverage.json: {e}")
            self.warnings.append(f"Cannot read coverage.json: {e}")
            return True  # Warning, not failure

    def check_p1_violations(self) -> bool:
        """Check for P1 violations (TODOs, NotImplementedError, placeholders)."""
        exclude_patterns = [
            "/tests/",
            "/test/",
            "test_",
            "/scripts/",
            "/.venv/",
            "/site-packages/",
            "/.pytest_cache/",
            "/__pycache__/",
            ".pyc",
        ]

        violations_found = {"todos": 0, "not_impl": 0, "placeholders": 0}
        violation_examples = {"todos": [], "not_impl": [], "placeholders": []}

        try:
            # Use rglob with error handling
            python_files = list(self.service_path.rglob("*.py"))
            logger.debug(f"Scanning {len(python_files)} Python files for P1 violations")

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to scan directory {self.service_path}: {e}")
            self.violations.append(f"Cannot scan service directory: {e}")
            return False

        for py_file in python_files:
            # Skip excluded patterns
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue

            try:
                # Read file with UTF-8, fallback to latin-1
                try:
                    content = py_file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    logger.debug(f"UTF-8 decode failed for {py_file}, trying latin-1")
                    content = py_file.read_text(encoding="latin-1")

                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    # Skip validation comments
                    if any(
                        x in line
                        for x in [
                            "NO TODO",
                            "NO MOCK",
                            "NO PLACEHOLDER",
                            '"TODO"',
                            "'TODO'",
                            "# noqa",
                        ]
                    ):
                        continue

                    # Check for real TODOs
                    if re.search(r"#\s*TODO\b", line, re.IGNORECASE):
                        violations_found["todos"] += 1
                        if len(violation_examples["todos"]) < 5:  # Show first 5
                            try:
                                rel_path = py_file.relative_to(self.service_path)
                                violation_examples["todos"].append(f"{rel_path}:{i}")
                            except ValueError:
                                # Fallback if relative_to fails
                                violation_examples["todos"].append(
                                    f"{py_file.name}:{i}"
                                )

                    # Check for NotImplementedError
                    if "raise NotImplementedError" in line:
                        violations_found["not_impl"] += 1
                        if len(violation_examples["not_impl"]) < 5:
                            try:
                                rel_path = py_file.relative_to(self.service_path)
                                violation_examples["not_impl"].append(f"{rel_path}:{i}")
                            except ValueError:
                                violation_examples["not_impl"].append(
                                    f"{py_file.name}:{i}"
                                )

                    # Check for placeholders
                    if re.search(r"\bplaceholder for\b", line, re.IGNORECASE):
                        violations_found["placeholders"] += 1
                        if len(violation_examples["placeholders"]) < 5:
                            try:
                                rel_path = py_file.relative_to(self.service_path)
                                violation_examples["placeholders"].append(
                                    f"{rel_path}:{i}"
                                )
                            except ValueError:
                                violation_examples["placeholders"].append(
                                    f"{py_file.name}:{i}"
                                )

            except (OSError, PermissionError) as e:
                logger.warning(f"Skipping file {py_file}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error processing {py_file}: {e}")
                continue

        # Report violations
        total_violations = sum(violations_found.values())

        if total_violations > 0:
            # Add examples to violations list
            for vtype, examples in violation_examples.items():
                if examples:
                    for example in examples:
                        vtype_name = {
                            "todos": "TODO",
                            "not_impl": "NotImplementedError",
                            "placeholders": "Placeholder",
                        }[vtype]
                        self.violations.append(f"{vtype_name} in {example}")

            # Add summary
            self.violations.append(
                f"Total P1 violations: {total_violations} "
                f"(TODOs: {violations_found['todos']}, "
                f"NotImplemented: {violations_found['not_impl']}, "
                f"Placeholders: {violations_found['placeholders']})"
            )

            logger.warning(
                f"P1 violations in {self.service_name}: {total_violations} total"
            )
            return False

        logger.debug(f"No P1 violations found in {self.service_name}")
        return True

    def check_dockerfile(self) -> bool:
        """Check Dockerfile has constitutional best practices."""
        dockerfile = self.service_path / "Dockerfile"

        if not dockerfile.exists():
            self.warnings.append("No Dockerfile found")
            return True  # Warning, not failure

        try:
            content = dockerfile.read_text(encoding="utf-8", errors="replace")

            # Check for HEALTHCHECK
            if "HEALTHCHECK" not in content:
                self.warnings.append("Dockerfile missing HEALTHCHECK")

            # Check for non-root user
            if "USER " not in content or "USER root" in content:
                self.warnings.append("Dockerfile should use non-root USER")

            # Check for metrics port
            if "9090" not in content and "METRICS_PORT" not in content:
                self.warnings.append("Dockerfile should expose metrics port (9090)")

            # Check for multi-stage build (best practice)
            if "FROM" in content and content.count("FROM") == 1:
                self.warnings.append(
                    "Consider using multi-stage build for smaller image size"
                )

            logger.debug(f"Dockerfile check completed for {self.service_name}")
            return True  # Warnings only, not failures

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to read Dockerfile: {e}")
            self.warnings.append(f"Cannot read Dockerfile: {e}")
            return True  # Warning, not failure


def main():
    parser = argparse.ArgumentParser(
        description="Constitutional Gate - CI/CD Validator (Production Ready)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s penelope_service              # Validate single service
  %(prog)s --all                         # Validate all services
  %(prog)s --all --strict                # Fail on warnings
  %(prog)s maximus_core_service --json   # JSON output for CI/CD
        """,
    )
    parser.add_argument(
        "service_name",
        nargs="?",
        help="Service name to validate (or use --all for all services)",
    )
    parser.add_argument("--all", action="store_true", help="Check all services")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (not just violations)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format for CI/CD parsing",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    try:
        if args.all:
            # Validate all services
            services_dir = Path("backend/services")

            if not services_dir.exists():
                logger.error(f"Services directory not found: {services_dir.absolute()}")
                print(
                    f"❌ ERROR: Services directory not found: {services_dir.absolute()}"
                )
                sys.exit(2)

            try:
                services = [
                    d.name
                    for d in services_dir.iterdir()
                    if d.is_dir() and not d.name.startswith(".")
                ]
            except (OSError, PermissionError) as e:
                logger.error(f"Failed to list services: {e}")
                print(f"❌ ERROR: Cannot list services directory: {e}")
                sys.exit(2)

            if not services:
                logger.warning("No services found to validate")
                print("⚠️  No services found in backend/services")
                sys.exit(0)

            logger.info(f"Starting validation of {len(services)} services")
            if not args.json:
                print(f"🔍 Checking {len(services)} services...")

            failed_services = []
            warning_services = []
            all_results = []

            for service_name in services:
                try:
                    gate = ConstitutionalGate(service_name, json_output=args.json)
                    passed = gate.validate()

                    if args.json:
                        # Collect results for final JSON output
                        all_results.append(
                            {
                                "service": service_name,
                                "status": "PASSED" if passed else "FAILED",
                                "violations": gate.violations,
                                "warnings": gate.warnings,
                            }
                        )

                    if not passed:
                        failed_services.append(service_name)
                    elif args.strict and gate.warnings:
                        warning_services.append(service_name)

                except ValidationError as e:
                    logger.error(f"Validation error for {service_name}: {e}")
                    if not args.json:
                        print(f"⚠️  Skipping {service_name}: {e}")
                    failed_services.append(service_name)
                    if args.json:
                        all_results.append(
                            {
                                "service": service_name,
                                "status": "ERROR",
                                "violations": [str(e)],
                                "warnings": [],
                            }
                        )

            # Output summary
            if args.json:
                summary = {
                    "total_services": len(services),
                    "passed": len(services)
                    - len(failed_services)
                    - len(warning_services),
                    "failed": len(failed_services),
                    "warnings": len(warning_services) if args.strict else 0,
                    "results": all_results,
                }
                print(json.dumps(summary, indent=2))
            else:
                print("\n" + "=" * 80)
                passed_count = (
                    len(services)
                    - len(failed_services)
                    - (len(warning_services) if args.strict else 0)
                )
                print(f"SUMMARY: {passed_count}/{len(services)} services passed")

                if failed_services:
                    print(f"\n❌ Failed services ({len(failed_services)}):")
                    for svc in failed_services:
                        print(f"   • {svc}")

                if args.strict and warning_services:
                    print(f"\n⚠️  Services with warnings ({len(warning_services)}):")
                    for svc in warning_services:
                        print(f"   • {svc}")

                print("=" * 80)

            # Exit with appropriate code
            if failed_services or (args.strict and warning_services):
                logger.info(
                    f"Validation completed: {len(failed_services)} failed, "
                    f"{len(warning_services)} warnings"
                )
                sys.exit(1)

            logger.info("All services passed constitutional gate")
            sys.exit(0)

        elif args.service_name:
            # Validate single service
            gate = ConstitutionalGate(args.service_name, json_output=args.json)
            passed = gate.validate()

            if args.strict and gate.warnings:
                if not args.json:
                    print("\n⚠️  Strict mode: Failing due to warnings")
                logger.warning(
                    f"Strict mode: {args.service_name} failed due to warnings"
                )
                sys.exit(1)

            exit_code = 0 if passed else 1
            logger.info(
                f"Service {args.service_name} validation: "
                f"{'PASSED' if passed else 'FAILED'}"
            )
            sys.exit(exit_code)

        else:
            parser.print_help()
            sys.exit(2)

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        if args.json:
            error_result = {"error": str(e), "status": "ERROR"}
            print(json.dumps(error_result, indent=2))
        else:
            print(f"\n❌ ERROR: {e}")
        sys.exit(2)

    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        print("\n⚠️  Validation interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        if args.json:
            error_result = {"error": f"Unexpected error: {str(e)}", "status": "ERROR"}
            print(json.dumps(error_result, indent=2))
        else:
            print(f"\n💥 UNEXPECTED ERROR: {e}")
            print("Please report this issue to Vértice Platform Team")
        sys.exit(2)


if __name__ == "__main__":
    main()
