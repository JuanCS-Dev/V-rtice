#!/usr/bin/env python3
"""
Fix pyproject.toml files by adding setuptools package discovery configuration.
"""

import os
from pathlib import Path

SERVICES_DIR = Path("/home/juan/vertice-dev/backend/services")
SETUPTOOLS_CONFIG = """
[tool.setuptools.packages.find]
where = ["."]
include = ["*"]
exclude = []
"""

def fix_pyproject_toml(file_path: Path) -> bool:
    """Fix a pyproject.toml file by adding setuptools config if missing."""
    content = file_path.read_text()

    # Check if already has the config
    if "[tool.setuptools.packages.find]" in content:
        return False

    # Find the build-system section
    if "[build-system]" not in content:
        print(f"WARNING: {file_path} has no [build-system] section")
        return False

    # Add the config after [build-system] section
    lines = content.split("\n")
    new_lines = []
    added = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Add after build-backend line
        if not added and "build-backend" in line:
            new_lines.append("")
            new_lines.append("[tool.setuptools.packages.find]")
            new_lines.append('where = ["."]')
            new_lines.append('include = ["*"]')
            new_lines.append('exclude = []')
            added = True

    if added:
        file_path.write_text("\n".join(new_lines))
        return True

    return False

def main():
    """Fix all pyproject.toml files in services directory."""
    fixed_count = 0

    for service_dir in sorted(SERVICES_DIR.iterdir()):
        if not service_dir.is_dir():
            continue

        pyproject_path = service_dir / "pyproject.toml"
        if not pyproject_path.exists():
            continue

        if fix_pyproject_toml(pyproject_path):
            print(f"✅ Fixed: {service_dir.name}")
            fixed_count += 1
        else:
            print(f"⏭️  Skipped: {service_dir.name}")

    print(f"\n🎯 Total fixed: {fixed_count}")

if __name__ == "__main__":
    main()
