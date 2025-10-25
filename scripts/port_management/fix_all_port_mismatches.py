#!/usr/bin/env python3
"""
FIX ALL PORT MISMATCHES - Correção Sistemática de TODAS as Portas
Lê port_manifest.json e corrige TODOS os mismatches em docker-compose.yml
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def print_header():
    print(f"{CYAN}╔══════════════════════════════════════════════════════════╗{NC}")
    print(f"{CYAN}║  FIX ALL PORT MISMATCHES - Correção Sistemática         ║{NC}")
    print(f"{CYAN}╚══════════════════════════════════════════════════════════╝{NC}")
    print()

def main():
    print_header()

    manifest_path = Path("/home/juan/vertice-dev/docs/port_manifest.json")
    compose_path = Path("/home/juan/vertice-dev/docker-compose.yml")

    # Check files exist
    if not manifest_path.exists():
        print(f"{RED}❌ Manifest não encontrado: {manifest_path}{NC}")
        return 1

    if not compose_path.exists():
        print(f"{RED}❌ docker-compose.yml não encontrado{NC}")
        return 1

    # Create backup
    timestamp = int(datetime.now().timestamp())
    backup_path = compose_path.parent / f"docker-compose.yml.backup.{timestamp}"
    print(f"{YELLOW}📦 Criando backup: {backup_path}{NC}")
    shutil.copy2(compose_path, backup_path)
    print()

    # Load manifest
    print(f"{BLUE}🔍 Carregando manifest...{NC}")
    with open(manifest_path, 'r') as f:
        services = json.load(f)

    # Filter mismatches
    mismatches = [s for s in services if s.get('mismatch', False)]

    if not mismatches:
        print(f"{GREEN}✅ Nenhum mismatch detectado no manifest!{NC}")
        return 0

    print(f"{CYAN}📊 Total de serviços com mismatch: {len(mismatches)}{NC}")
    print()

    # Read docker-compose.yml
    with open(compose_path, 'r') as f:
        compose_content = f.read()

    fixed = 0
    skipped = 0

    for service in mismatches:
        container = service['container']
        external = service['external_port']
        internal_mapped = service['internal_mapped']
        real_port = service['real_port']

        print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
        print(f"{YELLOW}🔧 Container: {container}{NC}")
        print(f"   External: {external}")
        print(f"   Mapped: {internal_mapped} → Real: {real_port}")

        # Pattern to find: "EXTERNAL:INTERNAL_MAPPED" or - EXTERNAL:INTERNAL_MAPPED
        port_pattern_quoted = f'"{external}:{internal_mapped}"'
        port_pattern_unquoted = f' {external}:{internal_mapped}'
        port_pattern_dash = f'- {external}:{internal_mapped}'

        found = False

        # Try quoted pattern
        if port_pattern_quoted in compose_content:
            print(f"{CYAN}   Corrigindo mapping (quoted): {external}:{internal_mapped} → {external}:{real_port}{NC}")
            compose_content = compose_content.replace(
                port_pattern_quoted,
                f'"{external}:{real_port}"'
            )
            found = True

        # Try unquoted pattern with leading space
        if port_pattern_unquoted in compose_content:
            print(f"{CYAN}   Corrigindo mapping (unquoted): {external}:{internal_mapped} → {external}:{real_port}{NC}")
            compose_content = compose_content.replace(
                port_pattern_unquoted,
                f' {external}:{real_port}'
            )
            found = True

        # Try dash pattern (list item)
        if port_pattern_dash in compose_content:
            print(f"{CYAN}   Corrigindo mapping (list): {external}:{internal_mapped} → {external}:{real_port}{NC}")
            compose_content = compose_content.replace(
                port_pattern_dash,
                f'- {external}:{real_port}'
            )
            found = True

        # Fix healthcheck references
        healthcheck_pattern = f'localhost:{internal_mapped}/health'
        if healthcheck_pattern in compose_content:
            print(f"{CYAN}   Corrigindo healthcheck: {internal_mapped} → {real_port}{NC}")
            compose_content = compose_content.replace(
                healthcheck_pattern,
                f'localhost:{real_port}/health'
            )
            found = True

        # Fix environment variable URLs (e.g., http://service:8001)
        # Match pattern like :PORT" or :PORT/
        env_pattern = f':{internal_mapped}"'
        if env_pattern in compose_content:
            print(f"{CYAN}   Corrigindo env vars: :{internal_mapped} → :{real_port}{NC}")
            compose_content = compose_content.replace(
                env_pattern,
                f':{real_port}"'
            )
            found = True

        env_pattern_slash = f':{internal_mapped}/'
        if env_pattern_slash in compose_content:
            print(f"{CYAN}   Corrigindo env vars (com /): :{internal_mapped}/ → :{real_port}/{NC}")
            compose_content = compose_content.replace(
                env_pattern_slash,
                f':{real_port}/'
            )
            found = True

        if found:
            print(f"{GREEN}   ✅ Corrigido!{NC}")
            fixed += 1
        else:
            print(f"{YELLOW}   ⚠ Não encontrado pattern {external}:{internal_mapped} no docker-compose{NC}")
            skipped += 1

        print()

    # Write updated docker-compose.yml
    with open(compose_path, 'w') as f:
        f.write(compose_content)

    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print()
    print(f"{GREEN}📊 RESUMO DA CORREÇÃO:{NC}")
    print(f"   Total analisado: {len(mismatches)}")
    print(f"   {GREEN}✅ Corrigidos: {fixed}{NC}")
    print(f"   {YELLOW}⚠ Não encontrados: {skipped}{NC}")
    print()
    print(f"{GREEN}✅ Correções aplicadas em: {compose_path}{NC}")
    print(f"{YELLOW}📦 Backup disponível em: {backup_path}{NC}")
    print()
    print(f"{CYAN}💡 Próximo passo: docker compose up -d para aplicar as mudanças{NC}")

    return 0

if __name__ == '__main__':
    exit(main())
