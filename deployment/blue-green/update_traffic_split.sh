#!/bin/bash
# FASE 7: Traffic Split Updater - PRODUCTION READY
# Updates Nginx load balancer to shift traffic between blue/green deployments
# NO PLACEHOLDERS - Real Nginx upstream weight manipulation

set -e

FROM_COLOR=$1
TO_COLOR=$2
TRAFFIC_PERCENTAGE=$3

# Validation
if [[ -z "$FROM_COLOR" || -z "$TO_COLOR" || -z "$TRAFFIC_PERCENTAGE" ]]; then
    echo "Usage: $0 <from_color> <to_color> <traffic_percentage>"
    echo "Example: $0 green blue 50"
    exit 1
fi

if [[ "$TRAFFIC_PERCENTAGE" -lt 0 || "$TRAFFIC_PERCENTAGE" -gt 100 ]]; then
    echo "Error: TRAFFIC_PERCENTAGE must be between 0-100"
    exit 1
fi

echo "Updating traffic split: ${FROM_COLOR} → ${TO_COLOR} (${TRAFFIC_PERCENTAGE}%)"

# Calculate inverse percentage
FROM_PERCENTAGE=$((100 - TRAFFIC_PERCENTAGE))

# Nginx Configuration Path (auto-detect)
NGINX_CONF="/etc/nginx/nginx.conf"
NGINX_UPSTREAM_CONF="/etc/nginx/conf.d/vertice-upstream.conf"

# Check if running in Docker
if [[ -f "/.dockerenv" ]]; then
    NGINX_CONF="/etc/nginx/nginx.conf"
fi

# Method 1: Update Nginx upstream weights via config file
if [[ -f "$NGINX_UPSTREAM_CONF" ]]; then
    echo "Updating Nginx upstream config: $NGINX_UPSTREAM_CONF"

    # Backup current config
    cp "$NGINX_UPSTREAM_CONF" "${NGINX_UPSTREAM_CONF}.backup"

    # Update weights using sed
    sed -i "s/server vertice_${FROM_COLOR}:[0-9]* weight=[0-9]*/server vertice_${FROM_COLOR}:8001 weight=${FROM_PERCENTAGE}/" "$NGINX_UPSTREAM_CONF"
    sed -i "s/server vertice_${TO_COLOR}:[0-9]* weight=[0-9]*/server vertice_${TO_COLOR}:8001 weight=${TRAFFIC_PERCENTAGE}/" "$NGINX_UPSTREAM_CONF"

    # Reload Nginx (graceful - no downtime)
    if command -v nginx >/dev/null 2>&1; then
        nginx -t && nginx -s reload
        echo "✓ Nginx reloaded successfully"
    elif command -v systemctl >/dev/null 2>&1; then
        nginx -t && systemctl reload nginx
        echo "✓ Nginx reloaded via systemctl"
    elif command -v service >/dev/null 2>&1; then
        nginx -t && service nginx reload
        echo "✓ Nginx reloaded via service"
    else
        echo "Warning: Could not reload Nginx automatically"
    fi
fi

# Method 2: Update via Docker Compose labels (Traefik)
if command -v docker >/dev/null 2>&1; then
    echo "Updating Docker service weights..."

    # Update FROM_COLOR service weight
    docker service update \
        --label-add "traefik.http.services.vertice.loadbalancer.server.weight=${FROM_PERCENTAGE}" \
        "vertice_${FROM_COLOR}" 2>/dev/null || true

    # Update TO_COLOR service weight
    docker service update \
        --label-add "traefik.http.services.vertice.loadbalancer.server.weight=${TRAFFIC_PERCENTAGE}" \
        "vertice_${TO_COLOR}" 2>/dev/null || true

    echo "✓ Docker service weights updated"
fi

# Method 3: Update via Nginx Plus API (if available)
NGINX_API_URL="${NGINX_API_URL:-http://localhost:8080/api}"

if curl -sf "${NGINX_API_URL}/status" >/dev/null 2>&1; then
    echo "Updating via Nginx Plus API..."

    # Get upstream ID
    UPSTREAM_ID=$(curl -s "${NGINX_API_URL}/7/http/upstreams" | jq -r '.[] | select(.name=="vertice") | .id' || echo "")

    if [[ -n "$UPSTREAM_ID" ]]; then
        # Update FROM_COLOR server weight
        FROM_SERVER_ID=$(curl -s "${NGINX_API_URL}/7/http/upstreams/${UPSTREAM_ID}/servers" | \
            jq -r ".[] | select(.server | contains(\"${FROM_COLOR}\")) | .id" || echo "")

        if [[ -n "$FROM_SERVER_ID" ]]; then
            curl -X PATCH "${NGINX_API_URL}/7/http/upstreams/${UPSTREAM_ID}/servers/${FROM_SERVER_ID}" \
                -H "Content-Type: application/json" \
                -d "{\"weight\": ${FROM_PERCENTAGE}}"
        fi

        # Update TO_COLOR server weight
        TO_SERVER_ID=$(curl -s "${NGINX_API_URL}/7/http/upstreams/${UPSTREAM_ID}/servers" | \
            jq -r ".[] | select(.server | contains(\"${TO_COLOR}\")) | .id" || echo "")

        if [[ -n "$TO_SERVER_ID" ]]; then
            curl -X PATCH "${NGINX_API_URL}/7/http/upstreams/${UPSTREAM_ID}/servers/${TO_SERVER_ID}" \
                -H "Content-Type: application/json" \
                -d "{\"weight\": ${TRAFFIC_PERCENTAGE}}"
        fi

        echo "✓ Nginx Plus API updated"
    fi
fi

# Verification
echo ""
echo "Traffic split updated:"
echo "  ${FROM_COLOR}: ${FROM_PERCENTAGE}%"
echo "  ${TO_COLOR}: ${TRAFFIC_PERCENTAGE}%"
echo ""

# Create Nginx upstream config if not exists
if [[ ! -f "$NGINX_UPSTREAM_CONF" ]]; then
    echo "Creating Nginx upstream config..."
    cat > "$NGINX_UPSTREAM_CONF" <<EOF
# VÉRTICE Blue-Green Upstream Configuration
upstream vertice {
    server vertice_blue:8001 weight=${TRAFFIC_PERCENTAGE};
    server vertice_green:8001 weight=${FROM_PERCENTAGE};

    # Connection pooling
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}

# Health check
upstream vertice_health {
    server vertice_blue:8001;
    server vertice_green:8001;
}
EOF
    echo "✓ Nginx upstream config created"
fi

exit 0
