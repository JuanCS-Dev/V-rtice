#!/usr/bin/env python3
"""
Fix broken f-strings in primoroso calls
"""
import re
from pathlib import Path

def fix_fstrings(file_path: Path) -> bool:
    content = file_path.read_text()
    original = content

    # Fix broken f-strings in primoroso calls
    # Pattern: primoroso.X("... {var} ...") → primoroso.X(f"... {var} ...")

    # Look for primoroso calls with {} but missing f-string
    def add_f_prefix(match):
        func = match.group(1)
        quote = match.group(2)
        string_content = match.group(3)

        # If string contains {}, it needs f-prefix
        if '{' in string_content and '}' in string_content:
            return f'{func}(f{quote}{string_content}{quote}'
        else:
            return match.group(0)

    # Match primoroso.function("string with {}")
    content = re.sub(
        r'(primoroso\.\w+)\((["\'])([^"\']*\{[^}]+\}[^"\']*)\2',
        add_f_prefix,
        content
    )

    # Fix broken Panel calls (missing closing parenthesis)
    # console.print(Panel(\n  ... \n  border_style="..." → add ))
    content = re.sub(
        r'(console\.print\(Panel\([^)]+border_style=["\'][^"\']+["\'])(\s*\n)(?![\s]*\)\))',
        r'\1))\2',
        content,
        flags=re.MULTILINE
    )

    # Fix primoroso.error("\n[bold]...") → console.print("\n[bold]...")
    content = re.sub(
        r'primoroso\.error\(f?"\n\[bold\]([^"]+)\[/bold\]"',
        r'console.print(f"\n[bold]\1[/bold]"',
        content
    )

    # Fix duplicate closing )
    content = re.sub(r'\)\)\)', r'))', content)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def main():
    commands_dir = Path("vertice/commands")

    files = [
        "analytics.py", "ask.py", "compliance.py", "context.py",
        "detect.py", "dlp.py", "hunt.py", "incident.py",
        "malware.py", "monitor.py", "policy.py", "scan.py",
        "threat.py", "threat_intel.py", "ip.py", "maximus.py"
    ]

    fixed = []
    for file_name in files:
        file_path = commands_dir / file_name
        if file_path.exists():
            try:
                if fix_fstrings(file_path):
                    print(f"✅ Fixed: {file_name}")
                    fixed.append(file_name)
                else:
                    print(f"⏭️  No changes: {file_name}")
            except Exception as e:
                print(f"❌ Error in {file_name}: {e}")

    print(f"\n📊 Fixed {len(fixed)} files")


if __name__ == "__main__":
    main()
