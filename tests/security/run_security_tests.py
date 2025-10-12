"""
Security Test Suite Runner - MAXIMUS Vértice

Comprehensive test execution for AI-driven defensive security workflows.

Usage:
    python tests/security/run_security_tests.py [OPTIONS]

Options:
    --module [ids|firewall|dlp|threat_intel|all]  Run specific module tests
    --coverage                                     Generate coverage report
    --verbose                                      Verbose output
    --failfast                                     Stop on first failure
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Optional


class SecurityTestRunner:
    """Test runner for security modules."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.tests_dir = root_dir / "tests" / "security"
        
        self.test_modules = {
            "ids": "test_ids.py",
            "firewall": "test_firewall.py",
            "dlp": "test_dlp.py",
            "threat_intel": "test_threat_intel.py"
        }
    
    def run_tests(
        self,
        modules: Optional[List[str]] = None,
        coverage: bool = False,
        verbose: bool = False,
        failfast: bool = False
    ) -> int:
        """
        Run security tests.
        
        Args:
            modules: List of modules to test, or None for all
            coverage: Generate coverage report
            verbose: Enable verbose output
            failfast: Stop on first failure
        
        Returns:
            Exit code (0 for success)
        """
        if modules is None or "all" in modules:
            modules = list(self.test_modules.keys())
        
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        for module in modules:
            if module in self.test_modules:
                test_file = self.tests_dir / self.test_modules[module]
                cmd.append(str(test_file))
        
        # Add options
        if coverage:
            cmd.extend([
                "--cov=backend/security",
                "--cov-report=html",
                "--cov-report=term"
            ])
        
        if verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
        
        if failfast:
            cmd.append("-x")
        
        # Add other useful flags
        cmd.extend([
            "--tb=short",
            "--color=yes",
            "-W", "ignore::DeprecationWarning"
        ])
        
        print(f"Running command: {' '.join(cmd)}")
        print(f"Working directory: {self.root_dir}")
        print("-" * 80)
        
        result = subprocess.run(
            cmd,
            cwd=str(self.root_dir),
            capture_output=False
        )
        
        return result.returncode
    
    def list_tests(self, modules: Optional[List[str]] = None):
        """List available tests without running them."""
        if modules is None or "all" in modules:
            modules = list(self.test_modules.keys())
        
        cmd = ["python", "-m", "pytest", "--collect-only", "-q"]
        
        for module in modules:
            if module in self.test_modules:
                test_file = self.tests_dir / self.test_modules[module]
                cmd.append(str(test_file))
        
        subprocess.run(cmd, cwd=str(self.root_dir))


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MAXIMUS Security Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--module",
        choices=["ids", "firewall", "dlp", "threat_intel", "all"],
        default="all",
        help="Module to test (default: all)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--failfast",
        action="store_true",
        help="Stop on first failure"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List tests without running"
    )
    
    args = parser.parse_args()
    
    # Find project root
    root_dir = Path(__file__).parent.parent.parent
    
    runner = SecurityTestRunner(root_dir)
    
    if args.list:
        modules = [args.module] if args.module != "all" else None
        runner.list_tests(modules)
        return 0
    
    modules = [args.module] if args.module != "all" else None
    
    exit_code = runner.run_tests(
        modules=modules,
        coverage=args.coverage,
        verbose=args.verbose,
        failfast=args.failfast
    )
    
    if exit_code == 0:
        print("\n" + "=" * 80)
        print("✅ ALL SECURITY TESTS PASSED")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
