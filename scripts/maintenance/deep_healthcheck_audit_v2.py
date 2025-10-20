#!/usr/bin/env python3
"""Deep Healthcheck Audit V2 - Investigação dos 23 unhealthy"""
import json
import subprocess
import yaml
from pathlib import Path

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
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={service}", "--format", "{{{{.Names}}}}"],
            capture_output=True, text=True, timeout=5
        )
        names = [n for n in result.stdout.strip().split('\n') if n]
        return names[0] if names else None
    except:
        return None

def get_healthcheck_logs(container_name):
    try:
        result = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{json .State.Health}}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            health_data = json.loads(result.stdout)
            if health_data and 'Log' in health_data and health_data['Log']:
                last_log = health_data['Log'][-1]
                return {
                    'exit_code': last_log.get('ExitCode'),
                    'output': last_log.get('Output', '').strip()[-200:]
                }
        return None
    except:
        return None

def get_dockerfile_port(service):
    service_dir = service.replace("-", "_")
    dockerfile = Path(f"/home/juan/vertice-dev/backend/services/{service_dir}/Dockerfile")
    
    if not dockerfile.exists():
        return None
    
    try:
        content = dockerfile.read_text()
        for line in content.split('\n'):
            if line.strip().startswith('EXPOSE'):
                port = line.split()[1]
                return int(port)
    except:
        pass
    return None

def get_compose_config(service):
    compose_file = Path("/home/juan/vertice-dev/docker-compose.yml")
    try:
        with compose_file.open() as f:
            compose_data = yaml.safe_load(f)
        
        if service in compose_data.get("services", {}):
            service_config = compose_data["services"][service]
            
            # Port mapping
            ports = service_config.get("ports", [])
            port_info = None
            if ports:
                port_mapping = ports[0] if isinstance(ports, list) else ports
                internal_port = int(port_mapping.split(":")[-1])
                port_info = {'mapping': port_mapping, 'internal': internal_port}
            
            # Healthcheck override
            healthcheck = service_config.get("healthcheck")
            
            return {'port': port_info, 'healthcheck': healthcheck}
        return None
    except:
        return None

# Execute
results = []

for service in UNHEALTHY_SERVICES:
    container_name = get_container_name(service)
    dockerfile_port = get_dockerfile_port(service)
    compose_config = get_compose_config(service)
    
    data = {
        'service': service,
        'container': container_name,
        'dockerfile_port': dockerfile_port,
        'compose_config': compose_config,
        'healthcheck_logs': None,
        'issues': []
    }
    
    if not container_name:
        data['issues'].append('NO_CONTAINER')
        results.append(data)
        continue
    
    healthcheck_logs = get_healthcheck_logs(container_name)
    data['healthcheck_logs'] = healthcheck_logs
    
    # Analyze issues
    if compose_config and compose_config.get('port') and dockerfile_port:
        compose_internal = compose_config['port']['internal']
        if dockerfile_port != compose_internal:
            data['issues'].append(f'PORT_MISMATCH: Dockerfile={dockerfile_port} vs Compose={compose_internal}')
    
    if compose_config and compose_config.get('healthcheck'):
        hc = compose_config['healthcheck']
        test_cmd = hc.get('test', [])
        if isinstance(test_cmd, list):
            test_cmd = ' '.join(test_cmd)
        data['issues'].append(f'HEALTHCHECK_OVERRIDE: {test_cmd}')
    
    if healthcheck_logs:
        exit_code = healthcheck_logs['exit_code']
        output = healthcheck_logs['output']
        
        if exit_code == 7:
            data['issues'].append('CURL_CONNECT_FAILED')
            import re
            port_match = re.search(r'port (\d+)', output)
            if port_match:
                data['issues'].append(f'TRIED_PORT={port_match.group(1)}')
        elif exit_code == 22:
            data['issues'].append('HTTP_ERROR_22')
    
    results.append(data)

# Categorize
categorized = {
    'port_mismatch': [],
    'healthcheck_override': [],
    'curl_failed': [],
    'no_container': [],
    'unknown': []
}

for r in results:
    if 'NO_CONTAINER' in r['issues']:
        categorized['no_container'].append(r)
    elif any('PORT_MISMATCH' in i for i in r['issues']):
        categorized['port_mismatch'].append(r)
    elif any('HEALTHCHECK_OVERRIDE' in i for i in r['issues']):
        categorized['healthcheck_override'].append(r)
    elif any('CURL' in i for i in r['issues']):
        categorized['curl_failed'].append(r)
    else:
        categorized['unknown'].append(r)

# Report
print("=" * 100)
print("DEEP HEALTHCHECK AUDIT - 23 UNHEALTHY SERVICES")
print("=" * 100)

print(f"\n📊 CATEGORIZAÇÃO:")
print(f"  ❌ PORT_MISMATCH: {len(categorized['port_mismatch'])}")
print(f"  ⚠️  HEALTHCHECK_OVERRIDE: {len(categorized['healthcheck_override'])}")
print(f"  🔌 CURL_FAILED: {len(categorized['curl_failed'])}")
print(f"  📦 NO_CONTAINER: {len(categorized['no_container'])}")
print(f"  ❓ UNKNOWN: {len(categorized['unknown'])}")

for category, items in categorized.items():
    if items:
        print(f"\n{'=' * 100}")
        print(f"{category.upper()} ({len(items)} services):")
        print('=' * 100)
        
        for r in items:
            print(f"\n{r['service']}:")
            print(f"  Container: {r['container']}")
            print(f"  Dockerfile port: {r['dockerfile_port']}")
            if r['compose_config'] and r['compose_config'].get('port'):
                print(f"  Compose port: {r['compose_config']['port']}")
            print(f"  Issues: {', '.join(r['issues']) if r['issues'] else 'None detected'}")
            if r['healthcheck_logs']:
                print(f"  Exit code: {r['healthcheck_logs']['exit_code']}")
                print(f"  Output: {r['healthcheck_logs']['output'][:120]}...")

# Save
output_file = Path("/home/juan/vertice-dev/docs/auditorias/deep_healthcheck_audit.json")
with output_file.open('w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 100}")
print(f"✅ Audit salvo em: {output_file}")
print('=' * 100)
