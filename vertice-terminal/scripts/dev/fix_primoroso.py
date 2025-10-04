#!/usr/bin/env python3
"""
Fix incorrect primoroso.error() replacements
"""
import re
from pathlib import Path

def fix_file(file_path: Path) -> bool:
    content = file_path.read_text()
    original = content

    # Fix: primoroso.error("[green]...") → primoroso.success("...")
    content = re.sub(
        r'primoroso\.error\("\[(?:bold )?green\]([^"]+?)(?:\[/(?:bold )?green\])?"',
        r'primoroso.success("\1"',
        content
    )

    # Fix: primoroso.error("[yellow]...") → primoroso.warning("...")
    content = re.sub(
        r'primoroso\.error\("\[(?:dim )?yellow\]([^"]+?)(?:\[/(?:dim )?yellow\])?"',
        r'primoroso.warning("\1"',
        content
    )

    # Fix: primoroso.error("[cyan]...") → primoroso.info("...")
    content = re.sub(
        r'primoroso\.error\("\[cyan\]([^"]+?)(?:\[/cyan\])?"',
        r'primoroso.info("\1"',
        content
    )

    # Fix: primoroso.error("[dim]...") → console.print(f"[dim]...")
    content = re.sub(
        r'primoroso\.error\("\[dim\]([^"]+?)(?:\[/dim\])?"',
        r'console.print(f"[dim]\1[/dim]"',
        content
    )

    # Fix: primoroso.error("[bold green]✓ ...") → primoroso.success("...")
    content = re.sub(
        r'primoroso\.error\("\[bold green\]✓\s*([^"]+?)(?:\[/bold green\])?"',
        r'primoroso.success("\1"',
        content
    )

    # Remove stray )) from broken replacements
    content = re.sub(r'\n\s*\)\)\s*$', '', content, flags=re.MULTILINE)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def main():
    commands_dir = Path("vertice/commands")

    # Files to fix
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
                if fix_file(file_path):
                    print(f"✅ Fixed: {file_name}")
                    fixed.append(file_name)
                else:
                    print(f"⏭️  No changes: {file_name}")
            except Exception as e:
                print(f"❌ Error in {file_name}: {e}")

    print(f"\n📊 Fixed {len(fixed)} files")


if __name__ == "__main__":
    main()
