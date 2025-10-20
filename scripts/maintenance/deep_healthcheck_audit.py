#!/usr/bin/env python3
"""
Deep Healthcheck Audit - Investigação sistemática dos 23 unhealthy
Captura: logs, config, port mapping, Dockerfile vs compose
"""
import json
import subprocess
import yaml
from pathlib import Path

# Lista dos 23 unhealthy (do relatório)
UNHEALTHY_SERVICES = [
    "hcl-kb-service", "narrative_analysis_service", "predictive_threat_hunting_service",
    "rte-service", "domain_service", "edge_agent_service", "google_osint_service",
    "hcl_analyzer_service", "hcl_executor_service", "hcl_kb_service",
    "hcl_monitor_service", "hcl_planner_service", "hsas_service",
    "malware_analysis_service", "nmap_service", "osint-service",
    "reflex_triage_engine", "seriema_graph", "ssl_monitor_service",
    "threat_intel_service", "vuln_intel_service", "vuln_scanner_service",
    "cloud_coordinator_service"
]

def get_container_name(service):
    """Get container name from docker ps"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={service}", "--format", "{{{{.Names}}}}"],
            capture_output=True, text=True, timeout=5
        )
        names = result.stdout.strip().split('\n')
        return names[0] if names and names[0] else None
    except:
        return None

def get_healthcheck_logs(container_name):
    """Get last healthcheck log from container"""
    try:
        result = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{json .State.Health}}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            health_data = json.loads(result.stdout)
            if health_data and 'Log' in health_data and health_data['Log']:
                last_log = health_data['Log'][-1]
                return {
                    'exit_code': last_log.get('ExitCode'),
                    'output': last_log.get('Output', '').strip()[-300:]  # Last 300 chars
                }
        return None
    except:
        return None

def get_dockerfile_port(service):
    """Get EXPOSE port from Dockerfile"""
    service_dir = service.replace("-", "_")
    dockerfile = Path(f"/home/juan/vertice-dev/backend/services/{service_dir}/Dockerfile")
    
    if not dockerfile.exists():
        return None
    
    try:
        content = dockerfile.read_text()
        # Find EXPOSE line
        for line in content.split('\n'):
            if line.strip().startswith('EXPOSE'):
                port = line.split()[1]
                return int(port)
    except:
        pass
    return None

def get_compose_port(service):
    """Get port mapping from docker-compose.yml"""
    compose_file = Path("/home/juan/vertice-dev/docker-compose.yml")
    try:
        with compose_file.open() as f:
            compose_data = yaml.safe_load(f)
        
        if service in compose_data.get("services", {}):
            service_config = compose_data["services"][service]
            ports = service_config.get("ports", [])
            
            if ports:
                port_mapping = ports[0] if isinstance(ports, list) else ports
                # Extract internal port (right side)
                internal_port = int(port_mapping.split(":")[-1])
                return {
                    'mapping': port_mapping,
                    'internal': internal_port
                }
        return None
    except:
        return None

def get_compose_healthcheck(service):
    """Get healthcheck override from docker-compose.yml"""
    compose_file = Path("/home/juan/vertice-dev/docker-compose.yml")
    try:
        with compose_file.open() as f:
            compose_data = yaml.safe_load(f)
        
        if service in compose_data.get("services", {}):
            service_config = compose_data["services"][service]
            return service_config.get("healthcheck")
        return None
    except:
        return None

# Execute audit
results = []

for service in UNHEALTHY_SERVICES:
    container_name = get_container_name(service)
    
    if not container_name:
        results.append({
            'service': service,
            'status': 'CONTAINER_NOT_FOUND',
            'container': None
        })
        continue
    
    healthcheck_logs = get_healthcheck_logs(container_name)
    dockerfile_port = get_dockerfile_port(service)
    compose_port = get_compose_port(service)
    compose_healthcheck = get_compose_healthcheck(service)
    
    # Analyze
    issues = []
    
    if dockerfile_port and compose_port:
        if dockerfile_port != compose_port['internal']:
            issues.append(f"PORT_MISMATCH: Dockerfile={dockerfile_port} vs Compose={compose_port['internal']}")
    
    if compose_healthcheck:
        issues.append(f"HEALTHCHECK_OVERRIDE: {compose_healthcheck.get('test', 'N/A')}")
    
    if healthcheck_logs:
        exit_code = healthcheck_logs.get('exit_code')
        output = healthcheck_logs.get('output', '')
        
        if exit_code == 7:
            issues.append("CURL_CONNECTION_REFUSED (exit 7)")
        elif exit_code == 22:
            issues.append("CURL_HTTP_ERROR (exit 22)")
        
        # Extract port from error
        if "port" in output:
            import re
            port_match = re.search(r'port (\d+)', output)
            if port_match:
                tried_port = int(port_match.group(1))
                issues.append(f"TRIED_PORT={tried_port}")
    
    results.append({
        'service': service,
        'container': container_name,
        'dockerfile_port': dockerfile_port,
        'compose_port': compose_port,
        'compose_healthcheck': bool(compose_healthcheck),
        'healthcheck_logs': healthcheck_logs,
        'issues': issues
    })

# Report
print("=" * 100)
print("DEEP HEALTHCHECK AUDIT - 23 UNHEALTHY SERVICES")
print("=" * 100)

# Group by issue type
port_mismatches = []
healthcheck_overrides = []
connection_refused = []
unknown = []

for r in results:
    service = r['service']
    issues = r.get('issues', [])
    
    has_port_mismatch = any('PORT_MISMATCH' in i for i in issues)
    has_override = any('HEALTHCHECK_OVERRIDE' in i for i in issues)
    has_conn_refused = any('CONNECTION_REFUSED' in i for i in issues)
    
    if has_port_mismatch:
        port_mismatches.append(r)
    elif has_override:
        healthcheck_overrides.append(r)
    elif has_conn_refused:
        connection_refused.append(r)
    else:
        unknown.append(r)

print(f"\n📊 CATEGORIZAÇÃO:\n")
print(f"❌ PORT_MISMATCH: {len(port_mismatches)} serviços")
print(f"⚠️  HEALTHCHECK_OVERRIDE: {len(healthcheck_overrides)} serviços")
print(f"🔌 CONNECTION_REFUSED: {len(connection_refused)} serviços")
print(f"❓ UNKNOWN: {len(unknown)} serviços")

print("\n" + "=" * 100)
print("DETALHES POR CATEGORIA")
print("=" * 100)

if port_mismatches:
    print("\n❌ PORT_MISMATCH:\n")
    for r in port_mismatches:
        print(f"  {r['service']}:")
        print(f"    Dockerfile: {r['dockerfile_port']}")
        print(f"    Compose: {r['compose_port']}")
        print(f"    Issues: {', '.join(r['issues'])}")
        print()

if healthcheck_overrides:
    print("\n⚠️  HEALTHCHECK_OVERRIDE:\n")
    for r in healthcheck_overrides:
        print(f"  {r['service']}:")
        print(f"    Issues: {', '.join(r['issues'])}")
        if r['healthcheck_logs']:
            print(f"    Last error: {r['healthcheck_logs'].get('output', 'N/A')[:150]}")
        print()

if connection_refused:
    print("\n🔌 CONNECTION_REFUSED:\n")
    for r in connection_refused:
        print(f"  {r['service']}:")
        print(f"    Issues: {', '.join(r['issues'])}")
        print()

if unknown:
    print("\n❓ UNKNOWN:\n")
    for r in unknown:
        print(f"  {r['service']}:")
        print(f"    Container: {r['container']}")
        print(f"    Dockerfile port: {r['dockerfile_port']}")
        print(f"    Compose port: {r['compose_port']}")
        print(f"    Healthcheck override: {r['compose_healthcheck']}")
        if r['healthcheck_logs']:
            print(f"    Exit code: {r['healthcheck_logs'].get('exit_code')}")
            print(f"    Output: {r['healthcheck_logs'].get('output', 'N/A')[:150]}")
        print()

# Save to JSON
output_file = Path("/home/juan/vertice-dev/docs/auditorias/deep_healthcheck_audit.json")
with output_file.open('w') as f:
    json.dump(results, f, indent=2)

print("=" * 100)
print(f"✅ Audit completo salvo em: {output_file}")
print("=" * 100)
