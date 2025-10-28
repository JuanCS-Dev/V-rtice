#!/bin/bash
cd /home/juan/vertice-dev/backend/services
for svc in immunis_bcell_service immunis_cytotoxic_t_service immunis_dendritic_service immunis_helper_t_service immunis_macrophage_service immunis_neutrophil_service immunis_nk_cell_service immunis_treg_service adaptive_immunity_service adaptive_immunity_db; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
