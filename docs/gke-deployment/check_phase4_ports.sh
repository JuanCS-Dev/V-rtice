#!/bin/bash
cd /home/juan/vertice-dev/backend/services
echo "=== COGNITION SERVICES (4) ==="
for svc in prefrontal_cortex_service digital_thalamus_service memory_consolidation_service neuromodulation_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
echo ""
echo "=== SENSORY SERVICES (6) ==="
for svc in auditory_cortex_service visual_cortex_service somatosensory_service chemical_sensing_service vestibular_service tegumentar_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
