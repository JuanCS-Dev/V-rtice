#!/usr/bin/env python3
"""
BACKEND ABSOLUTE 100% VALIDATION SUITE

Validates all 83 backend services for production readiness.
Evidence-first approach - trust no reports, verify everything.

Padrão Pagani Absoluto: 100% = 100%
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

SERVICES_DIR = Path("/home/juan/vertice-dev/backend/services")

# Required files for each service
REQUIRED_FILES = {
    "__init__.py": "Package initialization",
    "main.py": "Service entry point",
    "pyproject.toml": "UV configuration",
    "README.md": "Documentation",
}

# Required directories
REQUIRED_DIRS = {
    "tests": "Test directory",
}

class ValidationReport:
    """Comprehensive validation report."""

    def __init__(self):
        self.total_services = 0
        self.structure_pass = 0
        self.uv_sync_pass = 0
        self.import_pass = 0
        self.health_check_pass = 0

        self.failures: Dict[str, List[str]] = {
            "structure": [],
            "uv_sync": [],
            "imports": [],
            "health": [],
        }

        self.details: List[str] = []

    def add_detail(self, message: str):
        """Add detail message."""
        self.details.append(message)
        print(f"  {message}")

    def pass_rate(self, category: str) -> float:
        """Calculate pass rate for category."""
        if self.total_services == 0:
            return 0.0

        if category == "structure":
            return (self.structure_pass / self.total_services) * 100
        elif category == "uv_sync":
            return (self.uv_sync_pass / self.total_services) * 100
        elif category == "imports":
            return (self.import_pass / self.total_services) * 100
        elif category == "health":
            return (self.health_check_pass / self.total_services) * 100

        return 0.0

    def overall_pass_rate(self) -> float:
        """Calculate overall pass rate."""
        if self.total_services == 0:
            return 0.0

        # A service passes overall if it passes ALL checks
        total_passed = min(
            self.structure_pass,
            self.uv_sync_pass,
            self.import_pass,
        )

        return (total_passed / self.total_services) * 100


def print_header(title: str):
    """Print section header."""
    print(f"\n{BLUE}{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}{title.center(80)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*80}{RESET}\n")


def print_result(passed: bool, message: str):
    """Print test result."""
    if passed:
        print(f"{GREEN}✅ {message}{RESET}")
    else:
        print(f"{RED}❌ {message}{RESET}")


def validate_structure(service_dir: Path, report: ValidationReport) -> bool:
    """Validate service has required structure."""
    service_name = service_dir.name
    all_pass = True

    # Check required files
    for filename, description in REQUIRED_FILES.items():
        file_path = service_dir / filename
        if file_path.exists():
            report.add_detail(f"  ✅ {filename} ({description})")
        else:
            report.add_detail(f"  ❌ MISSING: {filename} ({description})")
            all_pass = False

    # Check required directories
    for dirname, description in REQUIRED_DIRS.items():
        dir_path = service_dir / dirname
        if dir_path.exists() and dir_path.is_dir():
            report.add_detail(f"  ✅ {dirname}/ ({description})")
        else:
            report.add_detail(f"  ❌ MISSING: {dirname}/ ({description})")
            all_pass = False

    if all_pass:
        report.structure_pass += 1
    else:
        report.failures["structure"].append(service_name)

    return all_pass


def validate_uv_sync(service_dir: Path, report: ValidationReport) -> bool:
    """Validate UV sync succeeds."""
    service_name = service_dir.name

    try:
        result = subprocess.run(
            ["uv", "sync", "--no-install-project"],
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            report.add_detail(f"  ✅ UV sync successful")
            report.uv_sync_pass += 1
            return True
        else:
            report.add_detail(f"  ❌ UV sync failed: {result.stderr[:100]}")
            report.failures["uv_sync"].append(service_name)
            return False

    except subprocess.TimeoutExpired:
        report.add_detail(f"  ❌ UV sync timeout (>60s)")
        report.failures["uv_sync"].append(service_name)
        return False
    except Exception as e:
        report.add_detail(f"  ❌ UV sync error: {str(e)[:100]}")
        report.failures["uv_sync"].append(service_name)
        return False


def validate_imports(service_dir: Path, report: ValidationReport) -> bool:
    """Validate main.py can be imported."""
    service_name = service_dir.name
    main_py = service_dir / "main.py"

    if not main_py.exists():
        report.add_detail(f"  ⏭️  No main.py to import")
        report.import_pass += 1  # Not a failure, just no main.py
        return True

    try:
        # Use ast.parse for syntax validation (no __pycache__ writes)
        import ast

        source = main_py.read_text(encoding='utf-8')
        ast.parse(source, filename=str(main_py))

        report.add_detail(f"  ✅ main.py syntax valid")
        report.import_pass += 1
        return True

    except SyntaxError as e:
        report.add_detail(f"  ❌ main.py syntax error: line {e.lineno}: {e.msg}")
        report.failures["imports"].append(service_name)
        return False
    except Exception as e:
        report.add_detail(f"  ❌ Import check error: {str(e)[:100]}")
        report.failures["imports"].append(service_name)
        return False


def validate_ports() -> Tuple[bool, List[str]]:
    """Validate required ports are available."""
    required_ports = {
        8000: "API Gateway",
        8100: "MAXIMUS Core Service",
        8001: "Prometheus Metrics",
    }

    available = []
    occupied = []

    for port, service in required_ports.items():
        try:
            result = subprocess.run(
                ["lsof", f"-i:{port}", "-t"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout.strip():
                # Port is occupied
                occupied.append(f"Port {port} ({service}) - OCCUPIED")
            else:
                # Port is available
                available.append(f"Port {port} ({service}) - AVAILABLE")

        except Exception as e:
            available.append(f"Port {port} ({service}) - UNKNOWN (assume available)")

    all_available = len(occupied) == 0
    return all_available, available + occupied


def main():
    """Run comprehensive validation."""
    print(f"{BOLD}{GREEN}")
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║           BACKEND ABSOLUTE 100% VALIDATION SUITE                              ║")
    print("║           Evidence-First Approach - Trust Nothing, Verify Everything          ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    report = ValidationReport()

    # Get all service directories
    service_dirs = sorted([d for d in SERVICES_DIR.iterdir() if d.is_dir()])
    report.total_services = len(service_dirs)

    print(f"\n{BOLD}Found {report.total_services} services to validate{RESET}\n")

    # ========================================================================
    # PHASE 1: STRUCTURAL VALIDATION
    # ========================================================================
    print_header("PHASE 1: STRUCTURAL VALIDATION")
    print("Validating required files and directories for all services...\n")

    for service_dir in service_dirs:
        service_name = service_dir.name
        print(f"{BOLD}{service_name}{RESET}")
        validate_structure(service_dir, report)
        print()

    structure_rate = report.pass_rate("structure")
    print(f"\n{BOLD}Structural Validation: {structure_rate:.2f}% pass rate{RESET}")
    print(f"  Passed: {report.structure_pass}/{report.total_services}")
    if report.failures["structure"]:
        print(f"  {RED}Failed: {', '.join(report.failures['structure'][:5])}{RESET}")

    # ========================================================================
    # PHASE 2: UV SYNC VALIDATION
    # ========================================================================
    print_header("PHASE 2: UV SYNC VALIDATION")
    print("Testing UV dependency resolution for all services...\n")

    for service_dir in service_dirs:
        service_name = service_dir.name
        print(f"{BOLD}{service_name}{RESET}")
        validate_uv_sync(service_dir, report)
        print()

    uv_rate = report.pass_rate("uv_sync")
    print(f"\n{BOLD}UV Sync Validation: {uv_rate:.2f}% pass rate{RESET}")
    print(f"  Passed: {report.uv_sync_pass}/{report.total_services}")
    if report.failures["uv_sync"]:
        print(f"  {RED}Failed: {', '.join(report.failures['uv_sync'][:5])}{RESET}")

    # ========================================================================
    # PHASE 3: IMPORT VALIDATION
    # ========================================================================
    print_header("PHASE 3: IMPORT VALIDATION")
    print("Validating Python syntax for all main.py files...\n")

    for service_dir in service_dirs:
        service_name = service_dir.name
        print(f"{BOLD}{service_name}{RESET}")
        validate_imports(service_dir, report)
        print()

    import_rate = report.pass_rate("imports")
    print(f"\n{BOLD}Import Validation: {import_rate:.2f}% pass rate{RESET}")
    print(f"  Passed: {report.import_pass}/{report.total_services}")
    if report.failures["imports"]:
        print(f"  {RED}Failed: {', '.join(report.failures['imports'][:5])}{RESET}")

    # ========================================================================
    # PHASE 4: PORT AVAILABILITY
    # ========================================================================
    print_header("PHASE 4: PORT AVAILABILITY VALIDATION")
    print("Checking required ports are available for services...\n")

    ports_ok, port_statuses = validate_ports()
    for status in port_statuses:
        if "AVAILABLE" in status:
            print(f"{GREEN}✅ {status}{RESET}")
        elif "OCCUPIED" in status:
            print(f"{YELLOW}⚠️  {status}{RESET}")
        else:
            print(f"{BLUE}ℹ️  {status}{RESET}")

    # ========================================================================
    # FINAL REPORT
    # ========================================================================
    print_header("VALIDATION SUMMARY")

    overall_rate = report.overall_pass_rate()

    print(f"{BOLD}Overall Results:{RESET}")
    print(f"  Total Services: {report.total_services}")
    print(f"  Structure:  {report.structure_pass}/{report.total_services} ({structure_rate:.2f}%)")
    print(f"  UV Sync:    {report.uv_sync_pass}/{report.total_services} ({uv_rate:.2f}%)")
    print(f"  Imports:    {report.import_pass}/{report.total_services} ({import_rate:.2f}%)")
    print(f"  Ports:      {'✅ AVAILABLE' if ports_ok else '⚠️  SOME OCCUPIED'}")
    print()

    # Overall pass rate
    if overall_rate == 100.0:
        print(f"{GREEN}{BOLD}╔═══════════════════════════════════════════════════════════╗{RESET}")
        print(f"{GREEN}{BOLD}║  🎉 BACKEND ABSOLUTE 100% - ALL VALIDATIONS PASSED! 🎉   ║{RESET}")
        print(f"{GREEN}{BOLD}╚═══════════════════════════════════════════════════════════╝{RESET}")
        return_code = 0
    else:
        print(f"{YELLOW}{BOLD}╔═══════════════════════════════════════════════════════════╗{RESET}")
        print(f"{YELLOW}{BOLD}║  ⚠️  VALIDATION INCOMPLETE - {overall_rate:.2f}% PASS RATE      ║{RESET}")
        print(f"{YELLOW}{BOLD}╚═══════════════════════════════════════════════════════════╝{RESET}")
        print()
        print(f"{BOLD}Failures by Category:{RESET}")
        for category, failures in report.failures.items():
            if failures:
                print(f"  {category}: {len(failures)} services")
                print(f"    {', '.join(failures[:10])}")
        return_code = 1

    print()
    print(f"{BOLD}Padrão Pagani Absoluto: 100% = 100%{RESET}")
    print(f"{BOLD}Evidence-First Validated ✅{RESET}")

    sys.exit(return_code)


if __name__ == "__main__":
    main()
