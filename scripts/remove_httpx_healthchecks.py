#!/usr/bin/env python3
"""
Remove httpx-based healthcheck overrides from docker-compose.yml
Let Dockerfiles control healthchecks (which use curl)
"""

import re
import sys
from pathlib import Path

def remove_httpx_healthchecks(dry_run: bool = True) -> int:
    """Remove healthcheck blocks that use httpx."""
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        print("❌ docker-compose.yml not found")
        return 1
    
    content = compose_file.read_text()
    lines = content.split('\n')
    
    # Find and remove healthcheck blocks with httpx
    i = 0
    removed_count = 0
    current_service = None
    skip_until_unindent = False
    healthcheck_indent = 0
    
    new_lines = []
    
    while i < len(lines):
        line = lines[i]
        
        # Track current service
        if re.match(r'^  \w+.*_service:', line):
            match = re.match(r'^  (\w+.*_service):', line)
            if match:
                current_service = match.group(1)
                skip_until_unindent = False
        
        # Found healthcheck line
        if '    healthcheck:' in line and not skip_until_unindent:
            # Check if next lines contain httpx
            j = i + 1
            healthcheck_indent = len(line) - len(line.lstrip())
            uses_httpx = False
            
            while j < len(lines):
                next_line = lines[j]
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If we're back to same or less indentation, healthcheck block ended
                if next_indent <= healthcheck_indent and next_line.strip():
                    break
                
                if 'httpx' in next_line:
                    uses_httpx = True
                    break
                
                j += 1
            
            if uses_httpx:
                print(f"✅ {current_service}: Removing httpx healthcheck override")
                skip_until_unindent = True
                removed_count += 1
                i += 1
                continue
        
        # Skip lines inside healthcheck block we're removing
        if skip_until_unindent:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= healthcheck_indent and line.strip():
                skip_until_unindent = False
                new_lines.append(line)
            # else: skip this line (part of healthcheck block)
        else:
            new_lines.append(line)
        
        i += 1
    
    if removed_count > 0:
        if dry_run:
            print(f"\n📋 DRY RUN: Would remove {removed_count} httpx healthcheck overrides")
            print("Run with --apply to actually apply changes")
            return 0
        else:
            # Backup
            backup_file = compose_file.parent / f"{compose_file.name}.backup.remove_httpx"
            backup_file.write_text(content)
            print(f"💾 Backup: {backup_file}")
            
            # Write fixed version
            compose_file.write_text('\n'.join(new_lines))
            print(f"✅ Removed {removed_count} httpx healthcheck overrides")
            print("ℹ️  Services will now use healthchecks defined in their Dockerfiles")
            return 0
    else:
        print("✅ No httpx healthcheck overrides found")
        return 0

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Remove httpx healthcheck overrides")
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    args = parser.parse_args()
    
    print("🔧 Scanning docker-compose.yml for httpx healthchecks...")
    return remove_httpx_healthchecks(dry_run=not args.apply)

if __name__ == "__main__":
    sys.exit(main())
