#!/usr/bin/env python3
"""Batch migration script for trivial TIER 3 services."""

import subprocess
import sys
from pathlib import Path

SERVICES = [
    "adaptive_immunity_service",
    "autonomous_investigation_service",
    "ip_intelligence_service",
    "malware_analysis_service",
    "memory_consolidation_service",
    "narrative_analysis_service",
    "offensive_gateway",
    "predictive_threat_hunting_service",
    "reflex_triage_engine",
    "strategic_planning_service",
    "threat_intel_service",
    "chemical_sensing_service",
    "edge_agent_service",
    "ssl_monitor_service",
    "api_gateway",
]

PYPROJECT_TEMPLATE = """[project]
name = "{name}"
version = "1.0.0"
description = "MAXIMUS Auxiliary Service"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "pydantic>=2.9.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "ruff>=0.13.0"]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I"]
ignore = ["E501"]
"""

MAKEFILE_TEMPLATE = """# {name}
.PHONY: help install dev lint format fix clean update
help:
\t@echo "Commands: install dev lint format fix clean update"
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
clean:
\tfind . -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null || true
update:
\tuv pip compile pyproject.toml -o requirements.txt
"""

def migrate_service(service_name: str, base_path: Path) -> bool:
    """Migrate a single service."""
    service_path = base_path / service_name
    if not service_path.exists():
        print(f"  ❌ {service_name}: Directory not found")
        return False

    # Create pyproject.toml
    pyproject_path = service_path / "pyproject.toml"
    pyproject_path.write_text(PYPROJECT_TEMPLATE.format(name=service_name))

    # Backup requirements.txt
    req_path = service_path / "requirements.txt"
    if req_path.exists():
        backup_path = service_path / "requirements.txt.old"
        req_path.rename(backup_path)

    # Compile with uv
    try:
        result = subprocess.run(
            ["uv", "pip", "compile", "pyproject.toml", "-o", "requirements.txt"],
            cwd=service_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"  ❌ {service_name}: uv compile failed")
            return False
    except Exception as e:
        print(f"  ❌ {service_name}: {e}")
        return False

    # Run ruff
    subprocess.run(["ruff", "check", ".", "--fix"], cwd=service_path, capture_output=True)
    subprocess.run(["ruff", "format", "."], cwd=service_path, capture_output=True)

    # Create Makefile
    makefile_path = service_path / "Makefile"
    makefile_path.write_text(MAKEFILE_TEMPLATE.format(name=service_name))

    print(f"  ✅ {service_name}")
    return True

def main():
    base_path = Path("/home/juan/vertice-dev/backend/services")

    print("🚀 BATCH 1: Migrating 15 trivial services...")
    print()

    success_count = 0
    for service in SERVICES:
        if migrate_service(service, base_path):
            success_count += 1

    print()
    print(f"✅ Batch 1 Complete: {success_count}/{len(SERVICES)} services migrated")

    return 0 if success_count == len(SERVICES) else 1

if __name__ == "__main__":
    sys.exit(main())
