#!/usr/bin/env python3
"""
FIX ENVIRONMENT VARIABLE PORTS - Correção de URLs em Environment Variables
Atualiza TODAS as referências de porta em variáveis de ambiente do docker-compose.yml
"""

import json
from pathlib import Path

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def main():
    print(f"{CYAN}╔══════════════════════════════════════════════════════════╗{NC}")
    print(f"{CYAN}║  FIX ENV VAR PORTS - Correção de URLs Internas          ║{NC}")
    print(f"{CYAN}╚══════════════════════════════════════════════════════════╝{NC}")
    print()

    manifest_path = Path("/home/juan/vertice-dev/docs/port_manifest.json")
    compose_path = Path("/home/juan/vertice-dev/docker-compose.yml")

    # Load manifest to get real ports
    with open(manifest_path, 'r') as f:
        services = json.load(f)

    # Create mapping: container_name -> real_port
    port_map = {}
    for svc in services:
        container = svc['container']
        real_port = svc['real_port']

        # Extract service name from container (remove vertice- prefix and standardize)
        # Examples: vertice-strategic-planning -> strategic_planning
        #           maximus-core -> maximus_core
        service_name = container.replace('vertice-', '').replace('-', '_')
        port_map[service_name] = real_port

        # Also add without modifications for exact matches
        port_map[container] = real_port

    print(f"{CYAN}📋 Loaded {len(port_map)} service port mappings{NC}")
    print()

    # Read docker-compose.yml
    with open(compose_path, 'r') as f:
        compose_content = f.read()

    original_content = compose_content
    fixes_applied = 0

    # Fix patterns like: SERVICE_NAME_URL=http://service_name:OLD_PORT
    for service_key, real_port in port_map.items():
        # Try various naming patterns
        patterns_to_try = [
            service_key,
            service_key.replace('_', '-'),
            service_key.replace('_', ''),
        ]

        for pattern in patterns_to_try:
            # Look for http://pattern:ANYPORT
            import re

            # Pattern: http://service:port or http://service:port/
            url_pattern = f'http://{pattern}:\\d+'
            matches = re.findall(url_pattern, compose_content, re.IGNORECASE)

            for match in matches:
                # Extract old port
                old_port = match.split(':')[-1]

                if old_port != str(real_port):
                    # Replace with correct port
                    new_url = f'http://{pattern}:{real_port}'
                    compose_content = compose_content.replace(match, new_url)
                    print(f"{GREEN}✅ Fixed: {match} → {new_url}{NC}")
                    fixes_applied += 1

    print()
    print(f"{CYAN}📊 Total fixes applied: {fixes_applied}{NC}")

    if fixes_applied > 0:
        # Save updated file
        with open(compose_path, 'w') as f:
            f.write(compose_content)
        print(f"{GREEN}✅ docker-compose.yml updated!{NC}")
    else:
        print(f"{YELLOW}⚠ No env var fixes needed{NC}")

    return 0

if __name__ == '__main__':
    exit(main())
