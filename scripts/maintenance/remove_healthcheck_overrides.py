#!/usr/bin/env python3
"""
Remove healthcheck overrides do docker-compose.yml
Deixa apenas o healthcheck do Dockerfile (que está correto)
"""
import yaml
import subprocess
from pathlib import Path

compose_file = Path("/home/juan/vertice-dev/docker-compose.yml")

# Backup
backup_file = Path(f"/home/juan/vertice-dev/docker-compose.yml.backup_remove_healthchecks_{subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()}")
subprocess.run(['cp', str(compose_file), str(backup_file)])
print(f"✅ Backup criado: {backup_file.name}")

# Load
with compose_file.open() as f:
    compose_data = yaml.safe_load(f)

# Lista de serviços que NÃO devem ter override removido (infra)
KEEP_HEALTHCHECK = [
    'hcl-postgres', 'hcl-kafka', 'redis', 'postgres', 'mongodb',
    'rabbitmq', 'vault', 'prometheus', 'grafana', 'jaeger'
]

removed_count = 0
kept_count = 0

for service_name, service_config in compose_data.get("services", {}).items():
    if 'healthcheck' in service_config:
        if service_name in KEEP_HEALTHCHECK:
            kept_count += 1
            print(f"⏭️  KEEPING: {service_name} (infrastructure)")
        else:
            del service_config['healthcheck']
            removed_count += 1
            print(f"✅ REMOVED: {service_name}")

# Save
with compose_file.open('w') as f:
    yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False, width=120)

print(f"\n{'=' * 100}")
print(f"✅ {removed_count} healthcheck overrides removidos")
print(f"⏭️  {kept_count} healthcheck overrides mantidos (infra)")
print(f"✅ docker-compose.yml atualizado")
print('=' * 100)
