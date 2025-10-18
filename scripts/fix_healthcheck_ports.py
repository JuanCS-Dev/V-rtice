#!/usr/bin/env python3
"""
Fix healthcheck port mismatches in docker-compose.yml
Reads actual port from Dockerfile, updates healthcheck in docker-compose.yml
"""

import re
import sys
from pathlib import Path
from typing import Dict, Optional

def get_service_port_from_dockerfile(service_path: Path) -> Optional[int]:
    """Extract EXPOSE port from service Dockerfile."""
    dockerfile = service_path / "Dockerfile"
    if not dockerfile.exists():
        return None
    
    content = dockerfile.read_text()
    match = re.search(r'EXPOSE\s+(\d+)', content)
    if match:
        return int(match.group(1))
    
    # Try CMD line
    match = re.search(r'--port["\s]+(\d+)', content)
    if match:
        return int(match.group(1))
    
    return None

def scan_all_services() -> Dict[str, int]:
    """Scan all services and get their actual ports."""
    services_dir = Path("backend/services")
    port_map = {}
    
    for service_dir in services_dir.iterdir():
        if not service_dir.is_dir():
            continue
        
        port = get_service_port_from_dockerfile(service_dir)
        if port:
            port_map[service_dir.name] = port
    
    return port_map

def fix_docker_compose(port_map: Dict[str, int], dry_run: bool = True) -> int:
    """Fix healthcheck ports in docker-compose.yml."""
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        print("❌ docker-compose.yml not found")
        return 1
    
    content = compose_file.read_text()
    lines = content.split('\n')
    modified = False
    fixes_count = 0
    
    current_service = None
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Track current service
        if re.match(r'^  \w+.*_service:', line):
            match = re.match(r'^  (\w+.*_service):', line)
            if match:
                current_service = match.group(1)
        
        # Fix healthcheck with wrong port
        if current_service and current_service in port_map:
            correct_port = port_map[current_service]
            
            # Pattern: httpx.get('http://localhost:WRONG_PORT/health')
            if "httpx.get('http://localhost:" in line or 'httpx.get("http://localhost:' in line:
                old_line = line
                # Replace any port with correct one
                new_line = re.sub(
                    r"(httpx\.get\(['\"]http://localhost:)\d+(/health['\"])",
                    r"\g<1>" + str(correct_port) + r"\g<2>",
                    line
                )
                if new_line != old_line:
                    lines[i] = new_line
                    modified = True
                    fixes_count += 1
                    print(f"✅ {current_service}: Fixed healthcheck port to {correct_port}")
        
        i += 1
    
    if modified:
        if dry_run:
            print(f"\n📋 DRY RUN: Would fix {fixes_count} services")
            print("Run with --apply to actually apply changes")
            return 0
        else:
            # Backup
            backup_file = compose_file.parent / f"{compose_file.name}.backup.healthcheck"
            backup_file.write_text(content)
            print(f"💾 Backup: {backup_file}")
            
            # Write fixed version
            compose_file.write_text('\n'.join(lines))
            print(f"✅ Applied {fixes_count} fixes to docker-compose.yml")
            return 0
    else:
        print("✅ No healthcheck port mismatches found")
        return 0

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix healthcheck port mismatches")
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    parser.add_argument('--verbose', action='store_true', help='Show port mappings')
    args = parser.parse_args()
    
    print("🔍 Scanning service Dockerfiles...")
    port_map = scan_all_services()
    
    if args.verbose:
        print("\n📊 Service port mappings:")
        for service, port in sorted(port_map.items()):
            print(f"  {service:40s} -> {port}")
        print()
    
    print(f"Found {len(port_map)} services with defined ports")
    
    print("\n🔧 Checking docker-compose.yml...")
    return fix_docker_compose(port_map, dry_run=not args.apply)

if __name__ == "__main__":
    sys.exit(main())
