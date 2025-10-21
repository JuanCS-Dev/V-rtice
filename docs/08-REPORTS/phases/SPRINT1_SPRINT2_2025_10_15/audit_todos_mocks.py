#!/usr/bin/env python3
"""
Comprehensive audit of TODOs, FIXMEs, HACKs, and mocks in MAXIMUS backend.
"""

import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

SERVICES_DIR = Path("/home/juan/vertice-dev/backend/services")

# Patterns to search
TODO_PATTERNS = [
    r'#\s*TODO[:\s]',
    r'#\s*FIXME[:\s]',
    r'#\s*HACK[:\s]',
    r'#\s*XXX[:\s]',
]

MOCK_PATTERNS = [
    r'\bmock_\w+',
    r'\bMock\w+',
    r'\.mock\(',
    r'return\s+\{\}',  # Empty dict returns
    r'return\s+\[\]',  # Empty list returns
    r'pass\s*#.*mock',
    r'raise\s+NotImplementedError',
    r'"""Mock',
    r"'''Mock",
]

def scan_file(file_path: Path) -> Tuple[List[str], List[str]]:
    """Scan a single Python file for TODOs and mocks."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return [], []

    lines = content.split('\n')
    todos = []
    mocks = []

    for i, line in enumerate(lines, 1):
        # Check for TODOs
        for pattern in TODO_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                todos.append(f"{file_path.name}:{i}: {line.strip()}")
                break

        # Check for mocks (skip test files)
        if 'test' not in file_path.name.lower():
            for pattern in MOCK_PATTERNS:
                if re.search(pattern, line):
                    mocks.append(f"{file_path.name}:{i}: {line.strip()}")
                    break

    return todos, mocks

def audit_service(service_dir: Path) -> Dict:
    """Audit a single service directory."""
    result = {
        'todos': [],
        'mocks': [],
        'files_scanned': 0,
    }

    # Find all Python files
    for py_file in service_dir.rglob('*.py'):
        # Skip venvs and cache
        if '.venv' in str(py_file) or '__pycache__' in str(py_file):
            continue

        result['files_scanned'] += 1
        todos, mocks = scan_file(py_file)
        result['todos'].extend(todos)
        result['mocks'].extend(mocks)

    return result

def categorize_todos(todos: List[str]) -> Dict[str, List[str]]:
    """Categorize TODOs by type."""
    categories = {
        'CRITICAL': [],
        'IMPORTANT': [],
        'ENHANCEMENT': [],
        'DOCUMENTATION': [],
        'OTHER': [],
    }

    for todo in todos:
        lower = todo.lower()
        if any(word in lower for word in ['critical', 'urgent', 'security', 'bug', 'broken']):
            categories['CRITICAL'].append(todo)
        elif any(word in lower for word in ['implement', 'fix', 'add', 'fixme']):
            categories['IMPORTANT'].append(todo)
        elif any(word in lower for word in ['improve', 'optimize', 'enhance', 'refactor']):
            categories['ENHANCEMENT'].append(todo)
        elif any(word in lower for word in ['doc', 'comment', 'explain']):
            categories['DOCUMENTATION'].append(todo)
        else:
            categories['OTHER'].append(todo)

    return categories

def main():
    """Main audit function."""
    print("🔍 SPRINT 2 FASE 2.1: TODO/FIXME/MOCK AUDIT")
    print("=" * 80)
    print()

    all_services = {}
    total_todos = 0
    total_mocks = 0

    # Audit each service
    for service_dir in sorted(SERVICES_DIR.iterdir()):
        if not service_dir.is_dir():
            continue

        print(f"Scanning {service_dir.name}...", end=" ")

        result = audit_service(service_dir)
        todo_count = len(result['todos'])
        mock_count = len(result['mocks'])

        if todo_count > 0 or mock_count > 0:
            all_services[service_dir.name] = result
            total_todos += todo_count
            total_mocks += mock_count
            print(f"✅ {todo_count} TODOs, {mock_count} mocks")
        else:
            print("✅ Clean")

    print()
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total TODOs found: {total_todos}")
    print(f"Total Mocks found: {total_mocks}")
    print(f"Services with issues: {len(all_services)}/83")
    print()

    # Top offenders
    print("🔥 TOP 10 SERVICES BY TODOS:")
    sorted_by_todos = sorted(all_services.items(),
                             key=lambda x: len(x[1]['todos']),
                             reverse=True)[:10]
    for i, (service, data) in enumerate(sorted_by_todos, 1):
        print(f"{i:2}. {service:40} {len(data['todos']):6} TODOs")

    print()
    print("🔥 TOP 10 SERVICES BY MOCKS:")
    sorted_by_mocks = sorted(all_services.items(),
                             key=lambda x: len(x[1]['mocks']),
                             reverse=True)[:10]
    for i, (service, data) in enumerate(sorted_by_mocks, 1):
        print(f"{i:2}. {service:40} {len(data['mocks']):6} mocks")

    # Categorize all TODOs
    print()
    print("=" * 80)
    print("📋 TODO CATEGORIZATION")
    print("=" * 80)

    all_todos = []
    for service_data in all_services.values():
        all_todos.extend(service_data['todos'])

    categories = categorize_todos(all_todos)
    for category, items in categories.items():
        print(f"{category:15} {len(items):6} items")

    # Write detailed report
    report_path = Path("/tmp/SPRINT2_FASE2.1_TODO_MOCK_AUDIT.md")
    with open(report_path, 'w') as f:
        f.write("# SPRINT 2 FASE 2.1: TODO/MOCK AUDIT REPORT\n\n")
        f.write(f"**Total TODOs:** {total_todos}\n")
        f.write(f"**Total Mocks:** {total_mocks}\n")
        f.write(f"**Services with issues:** {len(all_services)}/83\n\n")
        f.write("---\n\n")

        f.write("## Services by TODO Count\n\n")
        for service, data in sorted_by_todos:
            f.write(f"### {service} ({len(data['todos'])} TODOs)\n\n")
            if data['todos']:
                for todo in data['todos'][:10]:  # First 10
                    f.write(f"- {todo}\n")
                if len(data['todos']) > 10:
                    f.write(f"- ... and {len(data['todos']) - 10} more\n")
            f.write("\n")

        f.write("---\n\n")
        f.write("## Services by Mock Count\n\n")
        for service, data in sorted_by_mocks:
            f.write(f"### {service} ({len(data['mocks'])} mocks)\n\n")
            if data['mocks']:
                for mock in data['mocks'][:10]:  # First 10
                    f.write(f"- {mock}\n")
                if len(data['mocks']) > 10:
                    f.write(f"- ... and {len(data['mocks']) - 10} more\n")
            f.write("\n")

    print()
    print(f"✅ Detailed report written to: {report_path}")
    print()

if __name__ == "__main__":
    main()
