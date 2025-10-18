#!/usr/bin/env python3
"""
Audit docker-compose.yml overrides vs Dockerfiles
Identify unnecessary, conflicting, and necessary overrides
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def parse_dockerfile_cmd(service_path: Path) -> Optional[str]:
    """Extract CMD from Dockerfile."""
    dockerfile = service_path / "Dockerfile"
    if not dockerfile.exists():
        return None
    
    content = dockerfile.read_text()
    
    # Find CMD line
    match = re.search(r'^CMD\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    return None

def parse_compose_command(service_name: str, compose_content: str) -> Optional[str]:
    """Extract command override for service from docker-compose.yml."""
    # Find service block
    pattern = rf'^  {service_name}:\s*$.*?(?=^  \w+:|^$)'
    match = re.search(pattern, compose_content, re.MULTILINE | re.DOTALL)
    
    if not match:
        return None
    
    service_block = match.group(0)
    
    # Find command line in service block
    cmd_match = re.search(r'^\s+command:\s*(.+)$', service_block, re.MULTILINE)
    if cmd_match:
        return cmd_match.group(1).strip()
    
    return None

def categorize_override(
    service_name: str,
    dockerfile_cmd: Optional[str],
    compose_cmd: Optional[str]
) -> Tuple[str, str]:
    """
    Categorize override as NECESSARY, UNNECESSARY, or CONFLICTING.
    
    Returns: (category, reason)
    """
    if not compose_cmd:
        return ("NO_OVERRIDE", "No command override in docker-compose.yml")
    
    if not dockerfile_cmd:
        return ("NECESSARY", "Dockerfile has no CMD, override provides it")
    
    # Normalize for comparison
    df_normalized = dockerfile_cmd.replace('"', '').replace("'", "").lower()
    compose_normalized = compose_cmd.replace('"', '').replace("'", "").lower()
    
    # Check if they're essentially the same
    if df_normalized == compose_normalized:
        return ("UNNECESSARY", "Exact duplicate of Dockerfile CMD")
    
    # Check if compose uses simplified form (e.g., "python main.py" vs uvicorn)
    if "python" in compose_normalized and "uvicorn" in df_normalized:
        return ("CONFLICTING", "Compose uses direct python, Dockerfile uses uvicorn")
    
    # Check if both use uvicorn but different params
    if "uvicorn" in compose_normalized and "uvicorn" in df_normalized:
        # Extract port if present
        df_port = re.search(r'--port["\s]+(\d+)', df_normalized)
        compose_port = re.search(r'--port["\s]+(\d+)', compose_normalized)
        
        if df_port and compose_port and df_port.group(1) != compose_port.group(1):
            return ("CONFLICTING", f"Port mismatch: Dockerfile={df_port.group(1)}, Compose={compose_port.group(1)}")
        
        return ("UNNECESSARY", "Minor uvicorn param differences (likely safe to remove)")
    
    # Default: assume different for good reason
    return ("NECESSARY", "Significantly different commands (may be intentional)")

def audit_all_services(verbose: bool = False) -> Dict[str, Dict]:
    """Audit all services with command overrides."""
    services_dir = Path("backend/services")
    compose_file = Path("docker-compose.yml")
    
    if not compose_file.exists():
        print("❌ docker-compose.yml not found")
        return {}
    
    compose_content = compose_file.read_text()
    
    results = {}
    
    for service_dir in sorted(services_dir.iterdir()):
        if not service_dir.is_dir():
            continue
        
        service_name = service_dir.name
        
        # Get Dockerfile CMD
        dockerfile_cmd = parse_dockerfile_cmd(service_dir)
        
        # Get docker-compose command override
        compose_cmd = parse_compose_command(service_name, compose_content)
        
        # Categorize
        category, reason = categorize_override(service_name, dockerfile_cmd, compose_cmd)
        
        results[service_name] = {
            "dockerfile_cmd": dockerfile_cmd,
            "compose_cmd": compose_cmd,
            "category": category,
            "reason": reason
        }
        
        if verbose and compose_cmd:
            print(f"\n{'='*80}")
            print(f"Service: {service_name}")
            print(f"Category: {category}")
            print(f"Reason: {reason}")
            print(f"Dockerfile CMD: {dockerfile_cmd}")
            print(f"Compose command: {compose_cmd}")
    
    return results

def print_summary(results: Dict[str, Dict]):
    """Print summary statistics."""
    categories = {}
    for service, data in results.items():
        cat = data["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for cat in ["NO_OVERRIDE", "NECESSARY", "UNNECESSARY", "CONFLICTING"]:
        count = categories.get(cat, 0)
        print(f"{cat:20s}: {count:3d} services")
    
    print("\n" + "="*80)
    print("RECOMMENDED ACTIONS")
    print("="*80)
    
    # List services to fix
    to_remove = [s for s, d in results.items() if d["category"] in ["UNNECESSARY", "CONFLICTING"]]
    
    if to_remove:
        print(f"\n✅ SAFE TO REMOVE ({len(to_remove)} services):")
        for service in sorted(to_remove):
            data = results[service]
            print(f"  - {service:40s} [{data['category']}]")
    
    to_keep = [s for s, d in results.items() if d["category"] == "NECESSARY"]
    if to_keep:
        print(f"\n⚠️  KEEP OVERRIDE ({len(to_keep)} services):")
        for service in sorted(to_keep):
            data = results[service]
            print(f"  - {service:40s} [{data['reason']}]")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Audit docker-compose command overrides")
    parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    parser.add_argument('--output', help='Output file for detailed report')
    args = parser.parse_args()
    
    print("🔍 Auditing docker-compose.yml command overrides...")
    results = audit_all_services(verbose=args.verbose)
    
    print_summary(results)
    
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            f.write("# Docker-Compose Command Override Audit\n\n")
            for service, data in sorted(results.items()):
                if data["compose_cmd"]:
                    f.write(f"## {service}\n")
                    f.write(f"**Category:** {data['category']}\n")
                    f.write(f"**Reason:** {data['reason']}\n")
                    f.write(f"**Dockerfile CMD:** `{data['dockerfile_cmd']}`\n")
                    f.write(f"**Compose command:** `{data['compose_cmd']}`\n\n")
        
        print(f"\n💾 Detailed report saved to: {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
