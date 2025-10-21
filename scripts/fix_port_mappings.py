#!/usr/bin/env python3
"""
🔧 Fix Port Mappings in docker-compose.yml

Corrige mismatches de portas baseado no relatório de auditoria.
Mantém portas externas, ajusta apenas mapeamento interno.

Uso: python fix_port_mappings.py
"""

import re
from pathlib import Path

# Mapeamento correto baseado na auditoria
PORT_FIXES = {
    # Service Name: (external_port, dockerfile_internal_port)
    "adaptive_immunity_service": ("8020", "8000"),
    "memory_consolidation_service": ("8019", "8041"),
    "immunis_treg_service": ("8018", "8033"),
    "immunis_macrophage_service": ("8312", "8030"),
    "immunis_neutrophil_service": ("8313", "8031"),
    "immunis_bcell_service": ("8316", "8026"),
    "immunis_dendritic_service": ("8314", "8028"),
    "immunis_nk_cell_service": ("8319", "8032"),
    "immunis_helper_t_service": ("8317", "8029"),
    "immunis_cytotoxic_t_service": ("8318", "8027"),
}

COMPOSE_FILE = Path("/home/juan/vertice-dev/docker-compose.yml")

def fix_port_mapping(content: str, service_name: str, external: str, internal: str) -> str:
    """
    Encontra e corrige o port mapping para um serviço específico.

    Estratégia:
    1. Encontrar a seção do serviço (service_name:)
    2. Encontrar a linha 'ports:' dentro dessa seção
    3. Substituir o próximo mapeamento de porta
    """

    # Pattern para encontrar a seção do serviço
    # Captura desde '  service_name:' até o próximo serviço (ou final)
    service_pattern = rf"(  {service_name}:\n(?:(?!^\w+:).*\n)*?)(    -\s+)(\d+):(\d+)"

    def replacer(match):
        before = match.group(1)  # Tudo antes da linha de porta
        prefix = match.group(2)  # '    - '
        current_external = match.group(3)
        current_internal = match.group(4)

        # Nova linha com porta corrigida
        new_line = f"{prefix}{external}:{internal}"

        print(f"  📝 {service_name}: {current_external}:{current_internal} → {external}:{internal}")

        return before + new_line

    # Fazer substituição
    new_content = re.sub(service_pattern, replacer, content, flags=re.MULTILINE)

    return new_content

def main():
    print("🔧 Iniciando correção de port mappings...")
    print()

    # Ler arquivo
    content = COMPOSE_FILE.read_text()

    # Aplicar cada fix
    modified_count = 0
    for service_name, (external, internal) in PORT_FIXES.items():
        print(f"🔍 Processando: {service_name}")

        old_content = content
        content = fix_port_mapping(content, service_name, external, internal)

        if content != old_content:
            modified_count += 1

    # Salvar arquivo modificado
    COMPOSE_FILE.write_text(content)

    print()
    print(f"✅ Arquivo atualizado: {COMPOSE_FILE}")
    print(f"📊 Total de serviços modificados: {modified_count}/{len(PORT_FIXES)}")
    print()
    print("🔍 Validando YAML...")

    # Validar sintaxe YAML (tentativa)
    import subprocess
    try:
        result = subprocess.run(
            ["docker-compose", "config"],
            cwd=COMPOSE_FILE.parent,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ YAML válido!")
        else:
            print(f"❌ YAML inválido:\n{result.stderr}")
            # Restaurar backup
            print("🔄 Restaurando backup...")
            import shutil
            backups = sorted(COMPOSE_FILE.parent.glob("docker-compose.yml.backup-*"))
            if backups:
                latest_backup = backups[-1]
                shutil.copy(latest_backup, COMPOSE_FILE)
                print(f"✅ Backup restaurado: {latest_backup.name}")
    except FileNotFoundError:
        print("⚠️  docker-compose não encontrado, validação pulada")
    except subprocess.TimeoutExpired:
        print("⚠️  Validação timeout, mas arquivo foi salvo")

if __name__ == "__main__":
    main()
