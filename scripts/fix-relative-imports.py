#!/usr/bin/env python3
"""
Fix Relative Imports - Batch Correction Script
Converts relative imports (from .module) to absolute imports
"""

import re
import os
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix relative imports in a Python file"""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content
    changes = []

    # Pattern 1: from .module import something
    pattern1 = r'^from \.([a-zA-Z_][a-zA-Z0-9_]*) import'
    replacement1 = r'from \1 import'
    content, count1 = re.subn(pattern1, replacement1, content, flags=re.MULTILINE)
    if count1 > 0:
        changes.append(f"  Fixed {count1} relative imports (from .module)")

    # Pattern 2: from ..module import something
    pattern2 = r'^from \.\.([a-zA-Z_][a-zA-Z0-9_]*) import'
    replacement2 = r'from \1 import'
    content, count2 = re.subn(pattern2, replacement2, content, flags=re.MULTILINE)
    if count2 > 0:
        changes.append(f"  Fixed {count2} parent imports (from ..module)")

    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True, changes
    return False, []

def main():
    print("=" * 70)
    print("FIX RELATIVE IMPORTS - BATCH CORRECTION")
    print("=" * 70)
    print()

    # Target directories
    services_dir = Path("/home/juan/vertice-dev/backend/services")

    # Find all Python files with relative imports
    target_files = []

    for service_dir in services_dir.iterdir():
        if not service_dir.is_dir():
            continue

        # Check main.py and api.py
        for filename in ['main.py', 'api.py']:
            file_path = service_dir / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    if re.search(r'^from \.', content, re.MULTILINE):
                        target_files.append(file_path)

    print(f"📁 Found {len(target_files)} files with relative imports")
    print()

    # Process each file
    fixed_count = 0
    for file_path in target_files:
        was_fixed, changes = fix_imports_in_file(file_path)
        if was_fixed:
            fixed_count += 1
            print(f"✓ {file_path.parent.name}/{file_path.name}")
            for change in changes:
                print(change)

    print()
    print("=" * 70)
    print(f"✅ COMPLETED: Fixed {fixed_count} files")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  docker compose restart <service_name>")
    print("=" * 70)

if __name__ == '__main__':
    main()
