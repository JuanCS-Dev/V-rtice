#!/usr/bin/env python3
"""
Script Automatizado de Resolução de Conflitos de Porta
Vertice Platform - Docker Compose Port Conflict Resolver

Resolve todos os conflitos de porta reorganizando serviços por categoria.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

# Novo esquema de portas organizado por categoria
PORT_MAPPING = {
    # OSINT Services: 8100-8149
    'sinesp_service': 8102,
    'cyber_service': 8103,
    'domain_service': 8104,
    'ip_intelligence_service': 8105,
    'nmap_service': 8106,
    'osint-service': 8100,
    'google_osint_service': 8101,
    'atlas_service': 8109,
    'auth_service': 8110,
    'vuln_scanner_service': 8111,
    'social_eng_service': 8112,
    'threat_intel_service': 8113,
    'malware_analysis_service': 8114,
    'ssl_monitor_service': 8115,
    'network_monitor_service': 8120,
    'maximus_orchestrator_service': 8125,
    'maximus_predict': 8126,
    'maximus_integration_service': 8127,
    'adr_core_service': 8130,

    # Maximus Core: 8150-8199
    'maximus_core_service': 8150,
    'maximus-eureka': 8151,
    'maximus-oraculo': 8152,

    # Cognitive Services: 8200-8299
    'visual_cortex_service': 8206,
    'auditory_cortex_service': 8207,
    'somatosensory_service': 8208,
    'chemical_sensing_service': 8209,
    'vestibular_service': 8210,
    'prefrontal_cortex_service': 8211,
    'digital_thalamus_service': 8212,
    'narrative_manipulation_filter': 8213,
    'ai_immune_system': 8214,
    'homeostatic_regulation': 8215,
    'strategic_planning_service': 8216,
    'memory_consolidation_service': 8217,
    'neuromodulation_service': 8218,

    # Immunis Services: 8300-8399
    'immunis_api_service': 8300,
    'immunis_macrophage_service': 8312,
    'immunis_neutrophil_service': 8313,
    'immunis_dendritic_service': 8314,
    'immunis_bcell_service': 8316,
    'immunis_helper_t_service': 8317,
    'immunis_cytotoxic_t_service': 8318,
    'immunis_nk_cell_service': 8319,

    # HCL Services: 8400-8449
    'hcl_kb_service': 8420,
    'hcl-kb-service': 8421,
    'hcl_monitor_service': 8423,
    'hcl-monitor': 8424,
    'hcl_analyzer_service': 8426,
    'hcl-analyzer': 8427,
    'hcl_planner_service': 8429,
    'hcl-planner': 8430,
    'hcl_executor_service': 8432,
    'hcl-executor': 8433,
    'hpc_service': 8440,
    'hpc-service': 8441,

    # Offensive Services: 8500-8549
    'network_recon_service': 8532,
    'vuln_intel_service': 8533,
    'web_attack_service': 8534,
    'c2_orchestration_service': 8535,
    'bas_service': 8536,
    'offensive_gateway': 8537,

    # Other Services: 8600-8699
    'rte_service': 8605,
    'rte-service': 8606,
    'tataca_ingestion': 8610,
    'seriema_graph': 8611,
}


def read_docker_compose(file_path):
    """Lê o arquivo docker-compose.yml"""
    with open(file_path, 'r') as f:
        return f.read()


def update_port_mappings(content):
    """Atualiza os mapeamentos de porta no docker-compose.yml"""
    lines = content.split('\n')
    updated_lines = []
    current_service = None
    changes_made = []

    for line in lines:
        # Detectar nome do serviço
        service_match = re.match(r'^  ([a-z_-]+):', line)
        if service_match:
            current_service = service_match.group(1)
            updated_lines.append(line)
            continue

        # Procurar por mapeamentos de porta
        port_match = re.search(r'^(\s+)-\s+"(\d+):(\d+)"(.*)$', line)
        if port_match and current_service and current_service in PORT_MAPPING:
            indent = port_match.group(1)
            old_external = port_match.group(2)
            internal_port = port_match.group(3)
            comment = port_match.group(4)

            new_external = PORT_MAPPING[current_service]

            # Atualizar apenas se a porta externa mudou
            if int(old_external) != new_external:
                new_line = f'{indent}- "{new_external}:{internal_port}"{comment}'
                updated_lines.append(new_line)
                changes_made.append(
                    f"  {current_service}: {old_external}:{internal_port} → {new_external}:{internal_port}"
                )
                continue

        updated_lines.append(line)

    return '\n'.join(updated_lines), changes_made


def update_environment_urls(content):
    """Atualiza as variáveis de ambiente com as novas portas"""
    lines = content.split('\n')
    updated_lines = []
    env_changes = []

    for line in lines:
        updated_line = line

        # Procurar por URLs de serviço nas variáveis de ambiente
        for service_name, new_port in PORT_MAPPING.items():
            # Pattern: SERVICE_URL=http://service_name:OLD_PORT
            pattern = rf'(\s+- \w+_URL=http://){service_name}:(\d+)'
            match = re.search(pattern, updated_line)

            if match:
                old_port = match.group(2)
                if int(old_port) != new_port:
                    updated_line = re.sub(
                        pattern,
                        rf'\1{service_name}:{new_port}',
                        updated_line
                    )
                    env_changes.append(
                        f"  ENV {service_name}: :{old_port} → :{new_port}"
                    )

        updated_lines.append(updated_line)

    return '\n'.join(updated_lines), env_changes


def write_docker_compose(file_path, content):
    """Escreve o arquivo docker-compose.yml atualizado"""
    with open(file_path, 'w') as f:
        f.write(content)


def main():
    print("=" * 70)
    print("VERTICE PLATFORM - PORT CONFLICT RESOLVER")
    print("=" * 70)
    print()

    # Paths
    project_dir = Path(__file__).parent.parent
    docker_compose_path = project_dir / 'docker-compose.yml'

    if not docker_compose_path.exists():
        print(f"❌ Erro: {docker_compose_path} não encontrado!")
        sys.exit(1)

    print(f"📁 Arquivo: {docker_compose_path}")
    print()

    # Ler conteúdo
    print("📖 Lendo docker-compose.yml...")
    content = read_docker_compose(docker_compose_path)

    # Atualizar mapeamentos de porta
    print("🔧 Atualizando mapeamentos de porta...")
    content, port_changes = update_port_mappings(content)

    if port_changes:
        print(f"✓ {len(port_changes)} portas externas atualizadas:")
        for change in port_changes[:10]:  # Mostrar primeiras 10
            print(change)
        if len(port_changes) > 10:
            print(f"  ... e mais {len(port_changes) - 10} mudanças")
    else:
        print("✓ Nenhuma porta externa precisou ser atualizada")
    print()

    # Atualizar variáveis de ambiente
    print("🔧 Atualizando variáveis de ambiente...")
    content, env_changes = update_environment_urls(content)

    if env_changes:
        print(f"✓ {len(env_changes)} variáveis de ambiente atualizadas:")
        for change in env_changes[:10]:  # Mostrar primeiras 10
            print(change)
        if len(env_changes) > 10:
            print(f"  ... e mais {len(env_changes) - 10} mudanças")
    else:
        print("✓ Nenhuma variável de ambiente precisou ser atualizada")
    print()

    # Escrever arquivo atualizado
    print("💾 Salvando docker-compose.yml atualizado...")
    write_docker_compose(docker_compose_path, content)
    print("✓ Arquivo salvo com sucesso!")
    print()

    # Resumo
    print("=" * 70)
    print("✅ RESOLUÇÃO CONCLUÍDA")
    print("=" * 70)
    print(f"Total de alterações em portas: {len(port_changes)}")
    print(f"Total de alterações em ENV: {len(env_changes)}")
    print()
    print("Próximos passos:")
    print("  1. docker compose down --remove-orphans")
    print("  2. docker compose up -d")
    print("=" * 70)


if __name__ == '__main__':
    main()
