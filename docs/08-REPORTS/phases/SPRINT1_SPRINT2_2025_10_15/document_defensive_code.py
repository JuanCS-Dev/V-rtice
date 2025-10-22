#!/usr/bin/env python3
"""
Helper script to document defensive code and convert TODOs.
"""

import re
from pathlib import Path
from typing import List, Tuple

def analyze_todo_context(file_path: Path, line_num: int, todo_line: str) -> dict:
    """Analyze a TODO comment and its context."""
    lines = file_path.read_text().split('\n')

    # Get context (5 lines before and after)
    start = max(0, line_num - 6)
    end = min(len(lines), line_num + 5)
    context = lines[start:end]

    # Determine TODO type
    todo_type = "unknown"
    if "implement real" in todo_line.lower():
        todo_type = "stub_implementation"
    elif "fixme" in todo_line.lower():
        todo_type = "bug_fix"
    elif "hack" in todo_line.lower():
        todo_type = "workaround"
    elif "improve\|optimize\|enhance" in todo_line.lower():
        todo_type = "enhancement"

    return {
        'file': str(file_path),
        'line': line_num,
        'todo': todo_line.strip(),
        'type': todo_type,
        'context': context,
    }

def suggest_defensive_doc(todo_info: dict) -> str:
    """Suggest defensive code documentation for a TODO."""
    if todo_info['type'] == "stub_implementation":
        return f"""
    \"\"\"Defensive implementation.

    This method provides a safe default behavior. {todo_info['todo'].replace('# ', '').replace('TODO: ', '')}

    Current behavior is intentional for fail-safe operation.
    See docs/architecture/defensive-code.md
    \"\"\"
"""
    return ""

def main():
    """Analyze TODOs and suggest improvements."""
    services_dir = Path("/home/juan/vertice-dev/backend/services")

    print("🔍 DEFENSIVE CODE DOCUMENTATION HELPER")
    print("=" * 80)
    print()

    # Focus on top services
    focus_services = [
        "active_immune_core",
        "ethical_audit_service",
        "reflex_triage_engine",
    ]

    for service_name in focus_services:
        service_dir = services_dir / service_name
        if not service_dir.exists():
            continue

        print(f"\n📂 {service_name}")
        print("-" * 80)

        # Find TODOs in production code
        py_files = [f for f in service_dir.rglob("*.py")
                   if "test" not in f.name.lower()
                   and "tests" not in str(f)
                   and ".venv" not in str(f)]

        todos_found = []
        for py_file in py_files:
            try:
                lines = py_file.read_text().split('\n')
                for i, line in enumerate(lines, 1):
                    if re.search(r'TODO|FIXME|HACK', line, re.IGNORECASE):
                        if "implement real" in line.lower():
                            todos_found.append((py_file, i, line))
            except Exception:
                continue

        print(f"Found {len(todos_found)} 'implement real' TODOs")

        # Show first 5 examples
        for py_file, line_num, todo in todos_found[:5]:
            rel_path = py_file.relative_to(service_dir)
            print(f"\n  {rel_path}:{line_num}")
            print(f"  {todo.strip()}")

    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. For each TODO, decide:
   - IMPLEMENT: Add real functionality
   - DOCUMENT: Keep as defensive code with documentation
   - REMOVE: If no longer relevant

2. Defensive code template:
   '''
   def method(self):
       \"\"\"Defensive implementation.

       Returns safe default. Full implementation deferred because:
       - Requires external system integration (specify which)
       - Current default is fail-safe behavior
       - Planned for future sprint

       See: docs/architecture/defensive-code.md
       \"\"\"
       return safe_default
   '''

3. Priority: Start with files with most TODOs
""")

if __name__ == "__main__":
    main()
