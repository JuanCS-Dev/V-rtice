#!/usr/bin/env python3
"""
Fix Backend Import Structure - Batch Script
Migra de relative/namespace imports para absolute imports
Conforme Constituição Vértice v2.7 - FASE 1
"""
import os
import re
from pathlib import Path
from typing import List, Tuple

def scan_import_issues(backend_path: Path) -> List[Tuple[Path, str, str]]:
    """Scan all Python files for problematic imports"""
    issues = []
    
    for py_file in backend_path.rglob("*.py"):
        # Skip __pycache__ and .venv
        if '__pycache__' in str(py_file) or '.venv' in str(py_file) or 'venv' in str(py_file):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Pattern 1: from services.X import Y
                if re.match(r'^\s*from\s+services\.', line):
                    issues.append((py_file, line.strip(), f"Line {i}: Namespace collision"))
                
                # Pattern 2: from models import (without backend prefix)
                elif re.match(r'^\s*from\s+models\s+import', line):
                    issues.append((py_file, line.strip(), f"Line {i}: Ambiguous models import"))
                
                # Pattern 3: from config import (sem backend prefix)
                elif re.match(r'^\s*from\s+config\s+import', line) and 'backend.services' not in line:
                    issues.append((py_file, line.strip(), f"Line {i}: Ambiguous config import"))
        
        except Exception as e:
            print(f"⚠️  Error reading {py_file}: {e}")
    
    return issues

def fix_imports(backend_path: Path, dry_run: bool = True) -> int:
    """Fix import statements in all Python files"""
    fixed_count = 0
    
    for py_file in backend_path.rglob("*.py"):
        if '__pycache__' in str(py_file) or '.venv' in str(py_file) or 'venv' in str(py_file):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8')
            original = content
            
            # Fix 1: from services.X → from backend.services.X
            content = re.sub(
                r'from services\.([a-zA-Z0-9_]+)',
                r'from backend.services.\1',
                content
            )
            
            # Fix 2: import services.X → import backend.services.X
            content = re.sub(
                r'import services\.([a-zA-Z0-9_]+)',
                r'import backend.services.\1',
                content
            )
            
            if content != original:
                if not dry_run:
                    py_file.write_text(content, encoding='utf-8')
                fixed_count += 1
                print(f"✅ Fixed: {py_file.relative_to(backend_path.parent)}")
        
        except Exception as e:
            print(f"⚠️  Error fixing {py_file}: {e}")
    
    return fixed_count

def remove_pytest_plugins(backend_path: Path, dry_run: bool = True) -> int:
    """Remove pytest_plugins from non-root conftest.py files"""
    removed_count = 0
    root_conftest = backend_path.parent / "conftest.py"
    
    for conftest in backend_path.rglob("conftest.py"):
        if conftest == root_conftest:
            continue  # Skip root conftest
        
        if '__pycache__' in str(conftest) or '.venv' in str(conftest):
            continue
        
        try:
            content = conftest.read_text(encoding='utf-8')
            original = content
            
            # Remove pytest_plugins lines
            lines = content.split('\n')
            filtered_lines = [
                line for line in lines
                if 'pytest_plugins' not in line
            ]
            
            if len(filtered_lines) < len(lines):
                new_content = '\n'.join(filtered_lines)
                if not dry_run:
                    conftest.write_text(new_content, encoding='utf-8')
                removed_count += 1
                print(f"✅ Removed pytest_plugins from: {conftest.relative_to(backend_path.parent)}")
        
        except Exception as e:
            print(f"⚠️  Error processing {conftest}: {e}")
    
    return removed_count

def main():
    backend_path = Path(__file__).parent.parent / "backend"
    
    print("=" * 80)
    print("BACKEND IMPORT FIX - FASE 1")
    print("=" * 80)
    print()
    
    # Step 1: Scan issues
    print("📊 Scanning import issues...")
    issues = scan_import_issues(backend_path)
    print(f"   Found {len(issues)} problematic imports\n")
    
    if issues:
        print("Sample issues (first 10):")
        for file, line, desc in issues[:10]:
            print(f"   {file.name}: {line[:60]}")
        print()
    
    # Step 2: Dry run
    print("🔍 DRY RUN - Simulating fixes...")
    fixed = fix_imports(backend_path, dry_run=True)
    removed = remove_pytest_plugins(backend_path, dry_run=True)
    print(f"   Would fix {fixed} files")
    print(f"   Would remove pytest_plugins from {removed} conftest.py files\n")
    
    # Step 3: Execute
    confirm = input("Execute fixes? (yes/no): ").strip().lower()
    if confirm == 'yes':
        print("\n⚙️  Executing fixes...")
        fixed = fix_imports(backend_path, dry_run=False)
        removed = remove_pytest_plugins(backend_path, dry_run=False)
        print(f"\n✅ Fixed {fixed} files")
        print(f"✅ Cleaned {removed} conftest.py files")
        print("\n🎯 FASE 1 - Step 2 COMPLETO")
    else:
        print("\n❌ Aborted by user")

if __name__ == "__main__":
    main()
