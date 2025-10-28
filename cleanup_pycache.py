#!/usr/bin/env python3
"""Clean all __pycache__ directories from the project."""
import os
import shutil
import sys

dirs_removed = 0
errors = 0

for root, dirs, files in os.walk('.'):
    # Skip .venv, node_modules, .git
    if any(skip in root for skip in ['.venv', 'node_modules', '.git', 'venv', 'ENV']):
        dirs[:] = []  # Don't recurse into these directories
        continue

    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(pycache_path)
            dirs_removed += 1
            dirs.remove('__pycache__')  # Don't traverse into removed dir
        except PermissionError:
            errors += 1
            print(f"Permission denied: {pycache_path}", file=sys.stderr)
        except Exception as e:
            errors += 1
            print(f"Error removing {pycache_path}: {e}", file=sys.stderr)

print(f'✅ Removed {dirs_removed} __pycache__ directories')
if errors > 0:
    print(f'⚠️  {errors} directories could not be removed (permission issues)')
    sys.exit(1)
