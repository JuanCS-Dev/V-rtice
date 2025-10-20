#!/usr/bin/env python3
"""
Fix ALL port mismatches - Correção massiva dos 23 serviços
Atualiza docker-compose.yml para match com Dockerfile ports
"""
import json
import subprocess
from pathlib import Path

# Load audit data
audit_file = Path("/home/juan/vertice-dev/docs/auditorias/deep_healthcheck_audit.json")
with audit_file.open() as f:
    audit_data = json.load(f)

# Build fix list
fixes = []

for service_data in audit_data:
    service = service_data['service']
    dockerfile_port = service_data.get('dockerfile_port')
    compose_config = service_data.get('compose_config')
    
    if not dockerfile_port or not compose_config or not compose_config.get('port'):
        continue
    
    compose_port_info = compose_config['port']
    compose_internal = compose_port_info['internal']
    compose_mapping = compose_port_info['mapping']
    
    # Port mismatch?
    if dockerfile_port != compose_internal:
        # Extract external port
        external_port = compose_mapping.split(':')[0].strip('"')
        
        # New mapping: EXTERNAL:DOCKERFILE_PORT
        new_mapping = f'"{external_port}:{dockerfile_port}"'
        old_mapping = f'"{compose_mapping}"'
        
        fixes.append({
            'service': service,
            'old': old_mapping,
            'new': new_mapping,
            'dockerfile_port': dockerfile_port,
            'compose_port': compose_internal
        })

# Report plan
print("=" * 100)
print(f"PORT MISMATCH FIX PLAN - {len(fixes)} SERVICES")
print("=" * 100)

for fix in fixes:
    print(f"\n{fix['service']}:")
    print(f"  Dockerfile: {fix['dockerfile_port']}")
    print(f"  Compose OLD: {fix['old']}")
    print(f"  Compose NEW: {fix['new']}")

# Backup
compose_file = Path("/home/juan/vertice-dev/docker-compose.yml")
backup_file = Path(f"/home/juan/vertice-dev/docker-compose.yml.backup_massive_port_fix_{subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()}")

subprocess.run(['cp', str(compose_file), str(backup_file)])
print(f"\n{'=' * 100}")
print(f"✅ Backup criado: {backup_file.name}")
print('=' * 100)

# Apply fixes
content = compose_file.read_text()
changes_made = 0

for fix in fixes:
    old = fix['old']
    new = fix['new']
    
    if old in content:
        content = content.replace(old, new)
        changes_made += 1
        print(f"✅ {fix['service']}: {old} → {new}")
    else:
        print(f"⚠️  {fix['service']}: Pattern não encontrado ({old})")

# Save
compose_file.write_text(content)

print(f"\n{'=' * 100}")
print(f"✅ {changes_made}/{len(fixes)} fixes aplicados")
print(f"✅ docker-compose.yml atualizado")
print('=' * 100)

# Save fix list for rebuild
fix_list_file = Path("/home/juan/vertice-dev/docs/auditorias/services_to_rebuild_phase5.txt")
with fix_list_file.open('w') as f:
    for fix in fixes:
        f.write(f"{fix['service']}\n")

print(f"✅ Lista de serviços para rebuild: {fix_list_file}")
print('=' * 100)
