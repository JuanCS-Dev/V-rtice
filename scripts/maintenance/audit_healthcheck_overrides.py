#!/usr/bin/env python3
"""Audit healthcheck overrides no docker-compose.yml"""
import yaml
import re
from pathlib import Path

compose_file = Path("/home/juan/vertice-dev/docker-compose.yml")

with compose_file.open() as f:
    compose_data = yaml.safe_load(f)

services_with_override = []

for service_name, service_config in compose_data.get("services", {}).items():
    healthcheck = service_config.get("healthcheck")
    
    if healthcheck:
        test_cmd = healthcheck.get("test", [])
        
        # Convert to string
        if isinstance(test_cmd, list):
            test_str = ' '.join(test_cmd)
        else:
            test_str = str(test_cmd)
        
        # Extract port from healthcheck
        port_match = re.search(r'localhost:(\d+)', test_str)
        
        services_with_override.append({
            'service': service_name,
            'test': test_str,
            'port': int(port_match.group(1)) if port_match else None
        })

print("=" * 100)
print(f"HEALTHCHECK OVERRIDES AUDIT - {len(services_with_override)} services")
print("=" * 100)

for s in services_with_override:
    print(f"\n{s['service']}:")
    print(f"  Port in healthcheck: {s['port']}")
    print(f"  Test: {s['test'][:100]}...")
