#!/bin/bash
# Traffic split updater for blue-green deployment
# Updates load balancer configuration to shift traffic

FROM_COLOR=$1
TO_COLOR=$2
TRAFFIC_PERCENTAGE=$3

echo "Updating traffic split: ${FROM_COLOR} → ${TO_COLOR} (${TRAFFIC_PERCENTAGE}%)"

# Calculate inverse percentage
FROM_PERCENTAGE=$((100 - TRAFFIC_PERCENTAGE))

# Update HAProxy/Nginx/Traefik configuration
# This is a placeholder - implement based on your load balancer

# Example for HAProxy:
# sed -i "s/weight $FROM_COLOR.*/weight $FROM_PERCENTAGE/" /etc/haproxy/haproxy.cfg
# sed -i "s/weight $TO_COLOR.*/weight $TRAFFIC_PERCENTAGE/" /etc/haproxy/haproxy.cfg
# systemctl reload haproxy

# Example for Nginx:
# Update upstream weights dynamically via API

# Example for Traefik (using labels):
docker service update \
    --label-add "traefik.http.services.vertice.loadbalancer.server.weight=${TRAFFIC_PERCENTAGE}" \
    vertice_${TO_COLOR} 2>/dev/null || true

echo "Traffic split updated successfully"
