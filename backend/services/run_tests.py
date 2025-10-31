#!/usr/bin/env python3
"""Script to run tests for all 3 services."""

import os
import subprocess  # noqa: S404


def run_tests(service_name, service_path):
    """Run pytest for a service."""
    print(f"\n{'='*60}")
    print(f"Testing {service_name}")
    print(f"{'='*60}\n")

    os.chdir(service_path)

    # Set PYTHONPATH to include backend root
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/juan/vertice-dev/backend"

    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=short"],
        env=env,
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0


if __name__ == "__main__":
    services = [
        ("MABA", "/home/juan/vertice-dev/backend/services/maba_service"),
        ("MVP", "/home/juan/vertice-dev/backend/services/mvp_service"),
    ]

    results = {}
    for name, path in services:
        results[name] = run_tests(name, path)

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
