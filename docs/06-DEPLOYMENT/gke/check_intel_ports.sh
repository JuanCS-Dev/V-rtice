#!/bin/bash
cd /home/juan/vertice-dev/backend/services
for svc in osint_service threat_intel_service google_osint_service network_recon_service domain_service ip_intelligence_service vuln_intel_service cyber_service network_monitor_service ssl_monitor_service nmap_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
