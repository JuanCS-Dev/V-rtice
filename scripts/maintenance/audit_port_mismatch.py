#!/usr/bin/env python3
"""Audit port mismatches entre Dockerfile e docker-compose.yml"""
import re
import yaml
from pathlib import Path

# Serviços com portas conhecidas do Dockerfile
DOCKERFILE_PORTS = {
    "autonomous_investigation_service": 8007,
    "bas_service": 8008,
    "c2_orchestration_service": 8009,
    "network_monitor_service": 8044,
    "maximus_predict": 8040,
    "narrative_analysis_service": 8042,
    "predictive_threat_hunting_service": 8050,
}

# Parse docker-compose.yml
compose_file = Path("/home/juan/vertice-dev/docker-compose.yml")
with compose_file.open() as f:
    compose_data = yaml.safe_load(f)

mismatches = []

for service, dockerfile_port in DOCKERFILE_PORTS.items():
    if service in compose_data.get("services", {}):
        service_config = compose_data["services"][service]
        ports = service_config.get("ports", [])
        
        if ports:
            # Format: "8017:8017" ou ["8017:8017"]
            port_mapping = ports[0] if isinstance(ports, list) else ports
            # Extract internal port (right side)
            internal_port = int(port_mapping.split(":")[-1])
            
            if internal_port != dockerfile_port:
                mismatches.append({
                    "service": service,
                    "dockerfile": dockerfile_port,
                    "compose": internal_port,
                    "mapping": port_mapping
                })

print("=" * 80)
print("PORT MISMATCH AUDIT")
print("=" * 80)

if mismatches:
    print(f"\n❌ FOUND {len(mismatches)} MISMATCHES:\n")
    for m in mismatches:
        print(f"{m['service']}:")
        print(f"  Dockerfile EXPOSE: {m['dockerfile']}")
        print(f"  docker-compose.yml: {m['mapping']}")
        print(f"  ❌ MISMATCH: Compose uses {m['compose']} but app runs on {m['dockerfile']}")
        print()
else:
    print("\n✅ NO MISMATCHES FOUND")

print("=" * 80)
