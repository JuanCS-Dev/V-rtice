#!/usr/bin/env python3
"""Batch migration for TIER 2 simple services (with tests)."""

import subprocess
import sys
from pathlib import Path

# TIER 2 Batch 1: Simple services with tests (8-18 deps, <12 files)
SERVICES = [
    "hsas_service",              # 8 deps, 11 files, tests
    "ethical_audit_service",     # 12 deps, 8 files, tests
    "hcl_analyzer_service",      # 14 deps, 6 files, tests
    "hcl_planner_service",       # 14 deps, 7 files, tests
    "social_eng_service",        # 14 deps, 8 files, tests
    "web_attack_service",        # 16 deps, 10 files, tests
    "digital_thalamus_service",  # 17 deps, 7 files, tests
    "vuln_intel_service",        # 18 deps, 8 files, tests
]

PYPROJECT_TEMPLATE = """[project]
name = "{name}"
version = "1.0.0"
description = "MAXIMUS TIER 2 Service - Critical Operations"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "pydantic>=2.9.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.13.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"test_*.py" = ["S101", "ANN001", "D103"]
"__init__.py" = ["F401"]

[tool.pytest.ini_options]
testpaths = [".", "tests"]
python_files = ["test_*.py"]
addopts = ["--verbose", "--tb=short", "--cov=.", "--cov-report=term-missing"]
asyncio_mode = "auto"
"""

MAKEFILE_TEMPLATE = """# {name}
.PHONY: help install dev test lint format fix clean update
help:
\t@echo "Commands: install dev test lint format fix clean update"
install:
\tuv pip sync requirements.txt
dev:
\tuv pip install -e ".[dev]"
test:
\tPYTHONPATH=. python -m pytest -v --tb=short
test-cov:
\tPYTHONPATH=. python -m pytest -v --cov=. --cov-report=term-missing
lint:
\truff check .
format:
\truff format .
fix:
\truff check . --fix && ruff format .
clean:
\tfind . -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null || true
\trm -rf .pytest_cache .coverage coverage.xml
update:
\tuv pip compile pyproject.toml -o requirements.txt
"""

def migrate_service(service_name: str, base_path: Path) -> bool:
    """Migrate a single service."""
    service_path = base_path / service_name
    if not service_path.exists():
        print(f"  ❌ {service_name}: Not found")
        return False

    print(f"  📦 {service_name}...", end=" ", flush=True)

    # Create pyproject.toml
    (service_path / "pyproject.toml").write_text(PYPROJECT_TEMPLATE.format(name=service_name))

    # Backup requirements
    req = service_path / "requirements.txt"
    if req.exists():
        req.rename(service_path / "requirements.txt.old")

    # Compile
    try:
        result = subprocess.run(
            ["uv", "pip", "compile", "pyproject.toml", "-o", "requirements.txt"],
            cwd=service_path,
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            print("❌ compile failed")
            return False
    except Exception as e:
        print(f"❌ {e}")
        return False

    # Ruff
    subprocess.run(["ruff", "check", ".", "--fix"], cwd=service_path, capture_output=True)
    subprocess.run(["ruff", "format", "."], cwd=service_path, capture_output=True)

    # Makefile
    (service_path / "Makefile").write_text(MAKEFILE_TEMPLATE.format(name=service_name))

    print("✅")
    return True

def main():
    base = Path("/home/juan/vertice-dev/backend/services")

    print("🚀 TIER 2 Batch 1: Simple services with tests (8 services)")
    print()

    success = sum(migrate_service(svc, base) for svc in SERVICES)

    print()
    print(f"✅ Batch 1: {success}/{len(SERVICES)} migrated")

    if success == len(SERVICES):
        print("🎯 All simple TIER 2 services migrated!")
        print("📊 Progress: 59/70 (84.3%)")

    return 0 if success == len(SERVICES) else 1

if __name__ == "__main__":
    sys.exit(main())
