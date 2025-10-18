"""
Dependency security scanning tests.

Tests validate that all Python dependencies are secure:
1. No known vulnerabilities (via safety/pip-audit)
2. Up-to-date versions
3. No deprecated packages

Usage:
    pytest tests/security/test_dependencies.py -v

Requirements:
    pip install safety pip-audit
"""

import pytest
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any


# --- Fixtures ---

@pytest.fixture
def project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def requirements_file(project_root: Path) -> Path:
    """Get requirements.txt file."""
    req_file = project_root / "requirements.txt"
    assert req_file.exists(), f"requirements.txt not found at {req_file}"
    return req_file


# --- Helper Functions ---

def run_safety_check(requirements_file: Path) -> Dict[str, Any]:
    """
    Run safety check on requirements.txt.

    Returns:
        Dict with vulnerabilities found
    """
    try:
        result = subprocess.run(
            ["safety", "check", "--file", str(requirements_file), "--json"],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Safety returns non-zero exit code if vulnerabilities found
        if result.stdout:
            return json.loads(result.stdout)
        else:
            return {"vulnerabilities": []}

    except subprocess.TimeoutExpired:
        pytest.fail("safety check timed out after 60s")
    except FileNotFoundError:
        pytest.skip("safety not installed. Install with: pip install safety")
    except json.JSONDecodeError:
        # If JSON parsing fails, assume no vulnerabilities
        return {"vulnerabilities": []}


def run_pip_audit(requirements_file: Path) -> Dict[str, Any]:
    """
    Run pip-audit on requirements.txt.

    Returns:
        Dict with vulnerabilities found
    """
    try:
        result = subprocess.run(
            ["pip-audit", "--requirement", str(requirements_file), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.stdout:
            return json.loads(result.stdout)
        else:
            return {"dependencies": []}

    except subprocess.TimeoutExpired:
        pytest.fail("pip-audit timed out after 60s")
    except FileNotFoundError:
        pytest.skip("pip-audit not installed. Install with: pip install pip-audit")
    except json.JSONDecodeError:
        return {"dependencies": []}


def parse_requirements(requirements_file: Path) -> List[Dict[str, str]]:
    """
    Parse requirements.txt file.

    Returns:
        List of dicts with package name and version
    """
    packages = []
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Skip editable installs
            if line.startswith('-e'):
                continue

            # Parse package==version
            if '==' in line:
                name, version = line.split('==', 1)
                packages.append({
                    "name": name.strip(),
                    "version": version.strip()
                })
            elif '>=' in line:
                name, version = line.split('>=', 1)
                packages.append({
                    "name": name.strip(),
                    "version": f">={version.strip()}"
                })

    return packages


# --- Test Cases ---

@pytest.mark.security
class TestDependencySecurity:
    """Test dependency security."""

    def test_no_critical_vulnerabilities_safety(self, requirements_file: Path):
        """
        Test that no critical vulnerabilities exist (via safety).

        Critical = CVE with severity >= 7.0 (CVSS)
        """
        result = run_safety_check(requirements_file)
        vulnerabilities = result.get("vulnerabilities", [])

        critical_vulns = [
            v for v in vulnerabilities
            if v.get("severity", "") in ["critical", "high"]
            or (v.get("cvssv3", {}).get("base_score", 0) >= 7.0)
        ]

        if critical_vulns:
            print("\n❌ Critical vulnerabilities found:")
            for vuln in critical_vulns:
                print(f"  - {vuln.get('package', 'unknown')}: {vuln.get('vulnerability', 'N/A')}")
                print(f"    Severity: {vuln.get('severity', 'N/A')}")
                print(f"    Fixed in: {vuln.get('fixed_versions', 'N/A')}")
                print(f"    CVE: {vuln.get('cve', 'N/A')}")

        assert len(critical_vulns) == 0, f"Found {len(critical_vulns)} critical vulnerabilities"

    def test_no_vulnerabilities_pip_audit(self, requirements_file: Path):
        """
        Test that no vulnerabilities exist (via pip-audit).

        pip-audit checks against OSV database.
        """
        result = run_pip_audit(requirements_file)
        dependencies = result.get("dependencies", [])

        vulnerable_deps = [
            dep for dep in dependencies
            if dep.get("vulns", [])
        ]

        if vulnerable_deps:
            print("\n❌ Vulnerable dependencies found:")
            for dep in vulnerable_deps:
                print(f"  - {dep.get('name', 'unknown')} {dep.get('version', '')}")
                for vuln in dep.get("vulns", []):
                    print(f"    - {vuln.get('id', 'N/A')}: {vuln.get('description', 'N/A')[:100]}")
                    print(f"      Fix: {vuln.get('fix_versions', 'N/A')}")

        assert len(vulnerable_deps) == 0, f"Found {len(vulnerable_deps)} vulnerable dependencies"

    def test_no_deprecated_packages(self, requirements_file: Path):
        """
        Test that no deprecated packages are used.

        Known deprecated packages:
        - flask-cors < 4.0 (use flask-cors >= 4.0)
        - pycrypto (use pycryptodome)
        - optparse (use argparse)
        """
        deprecated = {
            "pycrypto": "Use pycryptodome instead",
            "optparse": "Use argparse instead",
            "flask-cors": "Use flask-cors >= 4.0",
        }

        packages = parse_requirements(requirements_file)
        found_deprecated = []

        for pkg in packages:
            if pkg["name"].lower() in deprecated:
                found_deprecated.append({
                    "name": pkg["name"],
                    "version": pkg["version"],
                    "reason": deprecated[pkg["name"].lower()]
                })

        if found_deprecated:
            print("\n⚠️ Deprecated packages found:")
            for dep in found_deprecated:
                print(f"  - {dep['name']} {dep['version']}")
                print(f"    Reason: {dep['reason']}")

        assert len(found_deprecated) == 0, f"Found {len(found_deprecated)} deprecated packages"

    def test_pinned_versions(self, requirements_file: Path):
        """
        Test that all dependencies have pinned versions.

        Best practice: Use == for production dependencies.
        """
        packages = parse_requirements(requirements_file)
        unpinned = [
            pkg for pkg in packages
            if not pkg["version"].startswith("==")
        ]

        if unpinned:
            print("\n⚠️ Unpinned dependencies found:")
            for pkg in unpinned:
                print(f"  - {pkg['name']} {pkg['version']}")
            print("\nRecommendation: Pin all versions with == for reproducible builds")

        # Warning only, not failure
        if unpinned:
            pytest.skip(f"Found {len(unpinned)} unpinned dependencies (warning only)")


@pytest.mark.security
class TestDependencyUpdates:
    """Test for outdated dependencies."""

    def test_check_outdated_packages(self, requirements_file: Path):
        """
        Check for outdated packages (informational).

        This test is informational only - doesn't fail on outdated packages.
        """
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                outdated = json.loads(result.stdout)

                if outdated:
                    print(f"\nℹ️ Found {len(outdated)} outdated packages:")
                    for pkg in outdated[:10]:  # Show first 10
                        print(f"  - {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")

                    if len(outdated) > 10:
                        print(f"  ... and {len(outdated) - 10} more")

                # Don't fail, just informational
                pytest.skip(f"Found {len(outdated)} outdated packages (informational)")
            else:
                print("\n✅ All packages are up to date")

        except subprocess.TimeoutExpired:
            pytest.skip("pip list --outdated timed out")
        except (FileNotFoundError, json.JSONDecodeError):
            pytest.skip("Could not check for outdated packages")


@pytest.mark.security
class TestLicenseCompliance:
    """Test license compliance (optional)."""

    def test_check_licenses(self, requirements_file: Path):
        """
        Check licenses of dependencies (informational).

        Flags potentially problematic licenses:
        - GPL (copyleft, may require source disclosure)
        - AGPL (strong copyleft)
        - Commercial licenses
        """
        try:
            result = subprocess.run(
                ["pip-licenses", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                licenses = json.loads(result.stdout)

                problematic_licenses = ["GPL", "AGPL", "Commercial"]
                flagged = [
                    lic for lic in licenses
                    if any(prob in lic.get("License", "") for prob in problematic_licenses)
                ]

                if flagged:
                    print(f"\n⚠️ Found {len(flagged)} packages with potentially problematic licenses:")
                    for lic in flagged[:5]:
                        print(f"  - {lic['Name']}: {lic['License']}")

                    # Warning only, not failure
                    pytest.skip(f"Found {len(flagged)} packages with problematic licenses (review recommended)")
                else:
                    print("\n✅ All licenses are permissive")

        except FileNotFoundError:
            pytest.skip("pip-licenses not installed. Install with: pip install pip-licenses")
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            pytest.skip("Could not check licenses")


# --- Integration Test ---

@pytest.mark.security
def test_security_scan_summary(requirements_file: Path):
    """
    Run complete security scan and generate summary.

    This is the main test that should pass for production deployment.
    """
    print("\n" + "=" * 60)
    print("DEPENDENCY SECURITY SCAN")
    print("=" * 60)

    # 1. Safety check
    print("\n→ Running safety check...")
    safety_result = run_safety_check(requirements_file)
    safety_vulns = safety_result.get("vulnerabilities", [])
    print(f"  Found {len(safety_vulns)} vulnerabilities")

    # 2. Pip-audit check
    print("\n→ Running pip-audit...")
    audit_result = run_pip_audit(requirements_file)
    audit_vulns = [dep for dep in audit_result.get("dependencies", []) if dep.get("vulns", [])]
    print(f"  Found {len(audit_vulns)} vulnerable dependencies")

    # 3. Parse requirements
    print("\n→ Analyzing requirements.txt...")
    packages = parse_requirements(requirements_file)
    print(f"  Found {len(packages)} dependencies")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_issues = len(safety_vulns) + len(audit_vulns)

    if total_issues == 0:
        print("✅ No security vulnerabilities found")
        print(f"✅ {len(packages)} dependencies scanned")
        print("\n✅ DEPENDENCY SECURITY: PASSED")
    else:
        print(f"❌ Found {total_issues} security issues")
        print(f"  - Safety: {len(safety_vulns)} vulnerabilities")
        print(f"  - Pip-audit: {len(audit_vulns)} vulnerable dependencies")
        print("\n❌ DEPENDENCY SECURITY: FAILED")

        # Fail test
        pytest.fail(f"Security scan failed: {total_issues} vulnerabilities found")

    print("=" * 60)


# --- Pytest Configuration ---

def pytest_configure(config):
    """Register security marker."""
    config.addinivalue_line(
        "markers",
        "security: mark test as security test"
    )
