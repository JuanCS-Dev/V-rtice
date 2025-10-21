#!/usr/bin/env python3
"""
🔍 AIR GAP DIAGNOSTIC - MAXIMUS Backend Infrastructure

Analisa o ecossistema backend completo para detectar:
1. Serviços implementados mas não declarados no docker-compose.yml
2. Serviços declarados no docker-compose mas sem implementação
3. Serviços sem containers rodando
4. Dependências quebradas (ENV vars apontando para serviços inexistentes)
5. Serviços órfãos (sem consumidores)
6. Comunicação inter-serviços ausente
"""

import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Paths
BASE_DIR = Path("/home/juan/vertice-dev")
COMPOSE_FILE = BASE_DIR / "docker-compose.yml"
SERVICES_DIR = BASE_DIR / "backend/services"


def load_docker_compose() -> Dict:
    """Load and parse docker-compose.yml"""
    with open(COMPOSE_FILE) as f:
        return yaml.safe_load(f)


def get_filesystem_services() -> Set[str]:
    """Get all service directories from filesystem"""
    return {
        d.name
        for d in SERVICES_DIR.iterdir()
        if d.is_dir() and d.name != "__pycache__"
    }


def get_compose_services(compose_data: Dict) -> Set[str]:
    """Get all service names from docker-compose.yml"""
    return set(compose_data.get("services", {}).keys())


def extract_service_dependencies(compose_data: Dict) -> Dict[str, Dict]:
    """
    Extrai dependências de cada serviço:
    - depends_on
    - environment variables apontando para outros serviços
    """
    services = compose_data.get("services", {})
    dependencies = {}

    for svc_name, svc_config in services.items():
        deps = {
            "depends_on": set(),
            "env_references": set(),
            "networks": set(svc_config.get("networks", [])),
            "ports": svc_config.get("ports", []),
        }

        # Explicit depends_on
        if "depends_on" in svc_config:
            depends_on = svc_config["depends_on"]
            if isinstance(depends_on, list):
                deps["depends_on"] = set(depends_on)
            elif isinstance(depends_on, dict):
                deps["depends_on"] = set(depends_on.keys())

        # Parse environment variables for service references
        env_vars = svc_config.get("environment", [])
        if isinstance(env_vars, dict):
            env_vars = [f"{k}={v}" for k, v in env_vars.items()]

        for env in env_vars:
            if "=" in env:
                key, value = env.split("=", 1)
                # Extract service names from URLs like http://service_name:port
                matches = re.findall(r"http://([a-z_0-9-]+):\d+", value)
                deps["env_references"].update(matches)

        dependencies[svc_name] = deps

    return dependencies


def detect_air_gaps(
    compose_services: Set[str],
    filesystem_services: Set[str],
    dependencies: Dict[str, Dict]
) -> Dict:
    """
    Detecta air gaps no sistema
    """

    # 1. Serviços implementados mas não declarados
    not_in_compose = filesystem_services - compose_services

    # 2. Serviços declarados mas sem implementação
    not_in_filesystem = compose_services - filesystem_services

    # 3. Infraestrutura (não são gaps)
    infrastructure = {
        "postgres", "redis", "qdrant", "prometheus", "grafana",
        "hcl-postgres", "hcl-kafka", "zookeeper-immunity",
        "kafka-immunity", "postgres-immunity", "kafka-ui-immunity",
        "rabbitmq"
    }

    # Remove infraestrutura dos gaps
    not_in_compose_clean = not_in_compose - infrastructure
    not_in_filesystem_clean = not_in_filesystem - infrastructure

    # 4. Dependências quebradas
    broken_deps = defaultdict(set)
    for svc, deps in dependencies.items():
        all_refs = deps["depends_on"] | deps["env_references"]
        for ref in all_refs:
            if ref not in compose_services:
                broken_deps[svc].add(ref)

    # 5. Serviços órfãos (ninguém depende deles)
    all_referenced = set()
    for deps in dependencies.values():
        all_referenced.update(deps["depends_on"])
        all_referenced.update(deps["env_references"])

    orphans = compose_services - all_referenced - infrastructure
    # Remove api_gateway dos órfãos (é o entry point)
    orphans.discard("api_gateway")
    orphans.discard("offensive_gateway")

    # 6. Serviços duplicados (mesmo propósito)
    duplicates = detect_duplicates(compose_services)

    return {
        "not_in_compose": sorted(not_in_compose_clean),
        "not_in_filesystem": sorted(not_in_filesystem_clean),
        "broken_dependencies": dict(broken_deps),
        "orphans": sorted(orphans),
        "duplicates": duplicates,
        "infrastructure": sorted(infrastructure)
    }


def detect_duplicates(services: Set[str]) -> List[Tuple]:
    """
    Detecta serviços duplicados baseado em padrões de nomes
    """
    duplicates = []

    # Padrões conhecidos
    patterns = {
        "hcl": ["hcl_analyzer_service", "hcl-analyzer"],
        "rte": ["rte_service", "rte-service"],
        "osint": ["osint-service", "osint_service"],
    }

    for category, variants in patterns.items():
        found = [s for s in services if any(v in s for v in variants)]
        if len(found) > 1:
            duplicates.append((category, found))

    return duplicates


def analyze_service_health(compose_data: Dict) -> Dict[str, str]:
    """
    Analisa configurações de healthcheck
    """
    services = compose_data.get("services", {})
    health_status = {}

    for svc_name, svc_config in services.items():
        if "healthcheck" in svc_config:
            health_status[svc_name] = "configured"
        else:
            health_status[svc_name] = "missing"

    return health_status


def generate_connectivity_graph(dependencies: Dict[str, Dict]) -> Dict:
    """
    Gera grafo de conectividade entre serviços
    """
    graph = {
        "nodes": list(dependencies.keys()),
        "edges": []
    }

    for svc, deps in dependencies.items():
        for dep in deps["depends_on"]:
            graph["edges"].append({"from": svc, "to": dep, "type": "depends_on"})
        for ref in deps["env_references"]:
            graph["edges"].append({"from": svc, "to": ref, "type": "env_ref"})

    return graph


def main():
    print("=" * 100)
    print("🔍 AIR GAP DIAGNOSTIC - MAXIMUS Backend Infrastructure")
    print("=" * 100)
    print()

    # Load data
    compose_data = load_docker_compose()
    compose_services = get_compose_services(compose_data)
    filesystem_services = get_filesystem_services()
    dependencies = extract_service_dependencies(compose_data)

    print(f"📊 RESUMO GERAL:")
    print(f"  • Serviços no docker-compose.yml: {len(compose_services)}")
    print(f"  • Serviços no filesystem:         {len(filesystem_services)}")
    print()

    # Detect air gaps
    gaps = detect_air_gaps(compose_services, filesystem_services, dependencies)

    # === AIR GAP #1: Implementados mas não declarados ===
    print("=" * 100)
    print("🔴 AIR GAP #1: SERVIÇOS IMPLEMENTADOS MAS NÃO DECLARADOS NO DOCKER-COMPOSE")
    print("=" * 100)
    print()

    if gaps["not_in_compose"]:
        print(f"⚠️  Encontrados {len(gaps['not_in_compose'])} serviços órfãos:\n")
        for svc in gaps["not_in_compose"]:
            svc_path = SERVICES_DIR / svc
            has_dockerfile = (svc_path / "Dockerfile").exists()
            has_main = (svc_path / "main.py").exists() or (svc_path / "app.py").exists()

            status = "🟢" if has_dockerfile else "🔴"
            print(f"  {status} {svc:45} | Dockerfile: {has_dockerfile:5} | Main: {has_main:5}")
    else:
        print("✅ Nenhum serviço órfão detectado")

    print()

    # === AIR GAP #2: Declarados mas sem implementação ===
    print("=" * 100)
    print("🔴 AIR GAP #2: SERVIÇOS DECLARADOS MAS SEM IMPLEMENTAÇÃO")
    print("=" * 100)
    print()

    if gaps["not_in_filesystem"]:
        print(f"⚠️  Encontrados {len(gaps['not_in_filesystem'])} serviços fantasmas:\n")
        for svc in gaps["not_in_filesystem"]:
            print(f"  🔴 {svc}")
    else:
        print("✅ Todos os serviços declarados têm implementação")

    print()

    # === AIR GAP #3: Dependências quebradas ===
    print("=" * 100)
    print("🔴 AIR GAP #3: DEPENDÊNCIAS QUEBRADAS")
    print("=" * 100)
    print()

    if gaps["broken_dependencies"]:
        print(f"⚠️  Encontrados {len(gaps['broken_dependencies'])} serviços com deps quebradas:\n")
        for svc, broken in gaps["broken_dependencies"].items():
            print(f"  🔴 {svc:45} → {', '.join(broken)}")
    else:
        print("✅ Todas as dependências estão resolvidas")

    print()

    # === AIR GAP #4: Serviços órfãos (ninguém os consome) ===
    print("=" * 100)
    print("🔴 AIR GAP #4: SERVIÇOS ÓRFÃOS (SEM CONSUMIDORES)")
    print("=" * 100)
    print()

    if gaps["orphans"]:
        print(f"⚠️  Encontrados {len(gaps['orphans'])} serviços sem consumidores:\n")
        for svc in gaps["orphans"]:
            print(f"  🟡 {svc}")
    else:
        print("✅ Todos os serviços são consumidos")

    print()

    # === AIR GAP #5: Serviços duplicados ===
    print("=" * 100)
    print("🔴 AIR GAP #5: SERVIÇOS DUPLICADOS")
    print("=" * 100)
    print()

    if gaps["duplicates"]:
        print(f"⚠️  Encontrados {len(gaps['duplicates'])} possíveis duplicações:\n")
        for category, services in gaps["duplicates"]:
            print(f"  🟡 Categoria: {category}")
            for svc in services:
                print(f"      - {svc}")
    else:
        print("✅ Nenhuma duplicação detectada")

    print()

    # === Healthcheck Analysis ===
    print("=" * 100)
    print("🏥 ANÁLISE DE HEALTHCHECKS")
    print("=" * 100)
    print()

    health_status = analyze_service_health(compose_data)
    missing_health = [svc for svc, status in health_status.items() if status == "missing"]

    print(f"Serviços SEM healthcheck: {len(missing_health)}/{len(health_status)}")
    print()

    if missing_health:
        print("Serviços críticos sem healthcheck:")
        critical_services = [
            "api_gateway", "maximus_core_service", "maximus_orchestrator_service",
            "active_immune_core", "reactive_fabric_core"
        ]
        for svc in missing_health:
            if svc in critical_services:
                print(f"  🔴 {svc:45} (CRÍTICO)")
            elif svc not in gaps["infrastructure"]:
                print(f"  🟡 {svc}")

    print()

    # === Connectivity Graph ===
    print("=" * 100)
    print("🌐 GRAFO DE CONECTIVIDADE")
    print("=" * 100)
    print()

    graph = generate_connectivity_graph(dependencies)
    print(f"Nós (serviços):   {len(graph['nodes'])}")
    print(f"Arestas (deps):   {len(graph['edges'])}")
    print()

    # Top 10 serviços mais conectados
    connection_count = defaultdict(int)
    for edge in graph["edges"]:
        connection_count[edge["from"]] += 1

    top_connected = sorted(connection_count.items(), key=lambda x: x[1], reverse=True)[:10]

    print("Top 10 serviços mais conectados:")
    for svc, count in top_connected:
        print(f"  {svc:45} → {count:3} conexões")

    print()

    # === Export para JSON ===
    report_path = BASE_DIR / "docs/backend/diagnosticos/air_gap_report_20251020.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert sets to lists for JSON serialization
    gaps_serializable = {
        "not_in_compose": gaps["not_in_compose"],
        "not_in_filesystem": gaps["not_in_filesystem"],
        "broken_dependencies": {k: list(v) for k, v in gaps["broken_dependencies"].items()},
        "orphans": gaps["orphans"],
        "duplicates": gaps["duplicates"],
        "infrastructure": gaps["infrastructure"]
    }

    report = {
        "timestamp": "2025-10-20T12:00:00Z",
        "summary": {
            "compose_services": len(compose_services),
            "filesystem_services": len(filesystem_services),
            "total_gaps": sum([
                len(gaps["not_in_compose"]),
                len(gaps["not_in_filesystem"]),
                len(gaps["broken_dependencies"]),
                len(gaps["orphans"]),
                len(gaps["duplicates"])
            ])
        },
        "gaps": gaps_serializable,
        "health_status": health_status,
        "connectivity_graph": graph,
        "top_connected": dict(top_connected)
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("=" * 100)
    print(f"📄 Relatório exportado: {report_path}")
    print("=" * 100)


if __name__ == "__main__":
    main()
