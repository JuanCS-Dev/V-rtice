#!/bin/sh
# ═══════════════════════════════════════════════════════════════════════════
# Vértice Frontend - Docker Entrypoint for Cloud Run
# ═══════════════════════════════════════════════════════════════════════════
# This script:
# 1. Substitutes environment variables in nginx config template
# 2. Starts nginx

set -e

echo "🚀 Vértice Frontend - Starting..."
echo "📍 PORT: ${PORT:-8080}"

# Substitute environment variables in nginx config template
# This allows nginx to use ${PORT} from environment
envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "✅ Nginx configuration ready"
echo "🌐 Starting nginx on port ${PORT}..."

# Execute the CMD from Dockerfile (nginx)
exec "$@"
