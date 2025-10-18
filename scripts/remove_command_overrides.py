#!/usr/bin/env python3
"""
Remove unnecessary command overrides from docker-compose.yml
Based on audit results
"""

import re
import sys
from pathlib import Path
from typing import Set

# Services with unnecessary/conflicting overrides (from audit)
SERVICES_TO_FIX = {
    "adaptive_immune_system",
    "adr_core_service",
    "ai_immune_system",
    "api_gateway",
    "atlas_service",
    "auditory_cortex_service",
    "auth_service",
    "chemical_sensing_service",
    "cloud_coordinator_service",
    "cyber_service",
    "digital_thalamus_service",
    "domain_service",
    "edge_agent_service",
    "ethical_audit_service",
    "google_osint_service",
    "hcl_analyzer_service",
    "hcl_executor_service",
    "hcl_kb_service",
    "hcl_monitor_service",
    "hcl_planner_service",
    "homeostatic_regulation",
    "hpc_service",
    "hsas_service",
    "immunis_api_service",
    "immunis_bcell_service",
    "immunis_cytotoxic_t_service",
    "immunis_dendritic_service",
    "immunis_helper_t_service",
    "immunis_macrophage_service",
    "immunis_neutrophil_service",
    "immunis_nk_cell_service",
    "ip_intelligence_service",
    "malware_analysis_service",
    "maximus_core_service",
    "maximus_eureka",
    "maximus_integration_service",
    "maximus_orchestrator_service",
    "maximus_predict",
    "narrative_manipulation_filter",
    "network_monitor_service",
    "network_recon_service",
    "neuromodulation_service",
    "nmap_service",
    "osint_service",
    "prefrontal_cortex_service",
    "reflex_triage_engine",
    "rte_service",
    "seriema_graph",
    "sinesp_service",
    "social_eng_service",
    "somatosensory_service",
    "ssl_monitor_service",
    "strategic_planning_service",
    "tataca_ingestion",
    "threat_intel_service",
    "vestibular_service",
    "visual_cortex_service",
    "vuln_intel_service",
    "vuln_scanner_service",
    "web_attack_service",
}

def remove_command_overrides(dry_run: bool = True) -> int:
    """Remove command lines from specified services."""
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        print("❌ docker-compose.yml not found")
        return 1
    
    content = compose_file.read_text()
    lines = content.split('\n')
    
    new_lines = []
    removed_count = 0
    current_service = None
    skip_next_command = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Track current service
        if re.match(r'^  \w+.*_service:', line) or re.match(r'^  api_gateway:', line):
            match = re.match(r'^  ([^:]+):', line)
            if match:
                service_name = match.group(1).strip()
                current_service = service_name if service_name in SERVICES_TO_FIX else None
        
        # Check if this is a command line we should remove
        if current_service and re.match(r'^\s+command:', line):
            print(f"✅ {current_service}: Removing command override")
            removed_count += 1
            # Skip this line (don't add to new_lines)
        else:
            new_lines.append(line)
        
        i += 1
    
    if removed_count > 0:
        if dry_run:
            print(f"\n📋 DRY RUN: Would remove {removed_count} command overrides")
            print("Run with --apply to actually apply changes")
            return 0
        else:
            # Backup
            backup_file = compose_file.parent / f"{compose_file.name}.backup.remove_commands"
            backup_file.write_text(content)
            print(f"💾 Backup: {backup_file}")
            
            # Write fixed version
            compose_file.write_text('\n'.join(new_lines))
            print(f"✅ Removed {removed_count} command overrides")
            print("ℹ️  Services will now use CMD defined in their Dockerfiles")
            return 0
    else:
        print("✅ No command overrides to remove")
        return 0

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Remove unnecessary command overrides")
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    args = parser.parse_args()
    
    print(f"🔧 Removing command overrides for {len(SERVICES_TO_FIX)} services...")
    return remove_command_overrides(dry_run=not args.apply)

if __name__ == "__main__":
    sys.exit(main())
