#!/usr/bin/env python3
"""
Healthcheck Fix - httpx → curl (Best Practice)
Baseado em OSINT research: curl é mais confiável para Docker healthchecks
"""
import re
from pathlib import Path

# Mapeamento completo: serviço → porta interna
SERVICES_PORTS = {
    "autonomous_investigation_service": 8007,
    "bas_service": 8008,
    "c2_orchestration_service": 8009,
    "network_monitor_service": 8044,
    "maximus_predict": 8040,
    "narrative_analysis_service": 8042,
    "predictive_threat_hunting_service": 8050,
    "rte_service": 8053,
    "atlas_service": 8004,
    "cloud_coordinator_service": 8011,
    "cyber_service": 8012,
    "domain_service": 8014,
    "edge_agent_service": 8015,
    "google_osint_service": 8016,
    "hcl_analyzer_service": 8017,
    "hcl_executor_service": 8018,
    "hcl_kb_service": 8019,
    "hcl_monitor_service": 8020,
    "hcl_planner_service": 8021,
    "hsas_service": 8024,
    "malware_analysis_service": 8035,
    "nmap_service": 8047,
    "osint_service": 8049,
    "osint-service": 8049,
    "reflex_triage_engine": 8052,
    "rte-service": 8053,
    "seriema_graph": 8300,
    "ssl_monitor_service": 8057,
    "threat_intel_service": 8059,
    "vuln_intel_service": 8062,
    "vuln_scanner_service": 8063,
    "hcl-kb-service": 8019,
}

def fix_healthcheck(dockerfile_path, port):
    """Fix healthcheck: httpx → curl"""
    try:
        content = dockerfile_path.read_text()
        
        # Pattern: HEALTHCHECK com python httpx (multi-line)
        old_pattern = r'HEALTHCHECK\s+--interval=\S+\s+--timeout=\S+\s+--start-period=\S+\s+--retries=\S+\s+\\\s*\n\s*CMD python -c "import httpx;.*?" \|\| exit 1'
        
        # Novo healthcheck canônico (OSINT validated)
        new_healthcheck = (
            f'HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\\n'
            f'  CMD curl -f http://localhost:{port}/health || exit 1'
        )
        
        # Substituir
        fixed = re.sub(old_pattern, new_healthcheck, content, flags=re.DOTALL)
        
        if fixed != content:
            dockerfile_path.write_text(fixed)
            return True, "fixed"
        
        return False, "already_curl_or_different_pattern"
    
    except Exception as e:
        return False, str(e)

# Executar
base_path = Path("/home/juan/vertice-dev/backend/services")
results = {"success": [], "skipped": [], "failed": []}

for service, port in sorted(SERVICES_PORTS.items()):
    service_dir = service.replace("-", "_")
    dockerfile = base_path / service_dir / "Dockerfile"
    
    if not dockerfile.exists():
        results["skipped"].append(f"{service} (Dockerfile not found)")
        continue
    
    success, msg = fix_healthcheck(dockerfile, port)
    
    if success:
        results["success"].append(f"{service}:{port}")
    elif "already" in msg:
        results["skipped"].append(f"{service} ({msg})")
    else:
        results["failed"].append(f"{service} ({msg})")

# Report
print("=" * 80)
print("HEALTHCHECK FIX AUTOMATION - httpx → curl")
print("=" * 80)
print(f"\n✅ FIXED ({len(results['success'])}):")
for item in results['success']:
    print(f"  {item}")

print(f"\n⏭️  SKIPPED ({len(results['skipped'])}):")
for item in results['skipped'][:10]:
    print(f"  {item}")
if len(results['skipped']) > 10:
    print(f"  ... +{len(results['skipped']) - 10} more")

print(f"\n❌ FAILED ({len(results['failed'])}):")
for item in results['failed']:
    print(f"  {item}")

print(f"\n{'='*80}")
print(f"TOTAL: {len(SERVICES_PORTS)} serviços processados")
print(f"FIXED: {len(results['success'])}")
print(f"SUCCESS RATE: {len(results['success']) * 100 // len(SERVICES_PORTS)}%")
print("=" * 80)

# Salvar lista de serviços fixados para rebuild
output_file = Path("/home/juan/vertice-dev/docs/auditorias/services_to_rebuild.txt")
with output_file.open("w") as f:
    for svc_port in results['success']:
        svc = svc_port.split(':')[0]
        f.write(f"{svc}\n")

print(f"\n✅ Lista de serviços para rebuild salva em: {output_file}")
