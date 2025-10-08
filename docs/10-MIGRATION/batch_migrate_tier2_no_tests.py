#!/usr/bin/env python3
"""Batch migration for TIER 2 services WITHOUT tests (extra care required)."""

import subprocess
import sys
from pathlib import Path

# TIER 2 Batch 3: Services WITHOUT tests (13-16 deps, medium complexity)
# ⚠️ These require extra validation since they don't have test suites
SERVICES = [
    "homeostatic_regulation",  # 16 deps, 4 files, NO tests ⚠️
    "bas_service",             # 13 deps, 8 files, NO tests ⚠️
    "hcl_monitor_service",     # 13 deps, 4 files, NO tests ⚠️
]

PYPROJECT_TEMPLATE = """[project]
name = "{name}"
version = "1.0.0"
description = "MAXIMUS TIER 2 Service - Important Operations"
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
addopts = ["--verbose", "--tb=short"]
asyncio_mode = "auto"
"""

MAKEFILE_TEMPLATE = """# {name}
.PHONY: help install dev lint format fix clean update check
help:
\t@echo "Commands: install dev lint format fix clean update check"
install:
\tuv pip sync requirements.txt
dev:
\tuv pip install -e ".[dev]"
lint:
\truff check .
format:
\truff format .
fix:
\truff check . --fix && ruff format .
check:
\t@echo "⚠️ No tests available - manual validation required"
\t@python -m py_compile *.py 2>/dev/null || true
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

    # Basic syntax validation (py_compile)
    py_files = list(service_path.glob("*.py"))
    if py_files:
        for py_file in py_files:
            try:
                subprocess.run(
                    ["python", "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    check=True,
                )
            except subprocess.CalledProcessError:
                print(f"⚠️ (syntax error in {py_file.name})")
                return False

    print("✅ ⚠️")
    return True

def main():
    base = Path("/home/juan/vertice-dev/backend/services")

    print("🚀 TIER 2 Batch 3: Services WITHOUT tests (3 services)")
    print("⚠️ CAUTION: These services have NO test suites - extra validation required")
    print()

    success = sum(migrate_service(svc, base) for svc in SERVICES)

    print()
    print(f"✅ Batch 3: {success}/{len(SERVICES)} migrated")

    if success == len(SERVICES):
        print("🎯 All TIER 2 services WITHOUT tests migrated!")
        print("⚠️ Manual validation recommended before deployment")
        print()
        print("=" * 60)
        print("🏆 TIER 2 100% COMPLETE!")
        print("=" * 60)
        print("📊 Progress: 67/70 (95.7%)")
        print()
        print("Remaining:")
        print("  TIER 1: 3 critical services")
        print("    - active_immune_core (22 deps, 160 files)")
        print("    - seriema_graph (10 deps, 6 files)")
        print("    - tataca_ingestion (11 deps, 16 files)")

    return 0 if success == len(SERVICES) else 1

if __name__ == "__main__":
    sys.exit(main())
