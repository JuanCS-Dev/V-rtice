#!/bin/bash
cd /home/juan/vertice-dev/backend/services
echo "=== REMAINING SERVICES WITH DOCKERFILES ==="
for svc in $(comm -23 /tmp/all_services_with_dockerfiles.txt /tmp/deployed_services.txt); do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  fi
done
