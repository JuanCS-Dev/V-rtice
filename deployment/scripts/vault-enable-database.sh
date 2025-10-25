#!/bin/bash
# Vault Database Dynamic Secrets Setup
# VÉRTICE Platform - FASE 3.2
#
# This script enables PostgreSQL dynamic credentials with:
# - Automated credential rotation
# - Least-privilege access (readonly vs readwrite)
# - TTL-based expiration

set -e

VAULT_ADDR="http://localhost:8201"
VAULT_TOKEN="vertice-dev-root-token"

echo "===================================="
echo "Vault Dynamic Database Secrets Setup"
echo "===================================="
echo ""

# Enable database secrets engine
echo "[1/5] Enabling database secrets engine..."
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{"type":"database"}' \
    ${VAULT_ADDR}/v1/sys/mounts/database >/dev/null 2>&1 || echo "  Already enabled"
echo "  ✅ Database secrets engine enabled"
echo ""

# Configure PostgreSQL connection (main database)
echo "[2/5] Configuring PostgreSQL connection (main)..."
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d "{
      \"plugin_name\": \"postgresql-database-plugin\",
      \"allowed_roles\": \"vertice-readonly,vertice-readwrite,vertice-admin\",
      \"connection_url\": \"postgresql://{{username}}:{{password}}@postgres:5432/vertice?sslmode=disable\",
      \"username\": \"postgres\",
      \"password\": \"${POSTGRES_PASSWORD}\"
    }" \
    ${VAULT_ADDR}/v1/database/config/postgres-main >/dev/null
echo "  ✅ PostgreSQL main connection configured"

# Configure PostgreSQL connection (immunity database)
echo "[3/5] Configuring PostgreSQL connection (immunity)..."
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d "{
      \"plugin_name\": \"postgresql-database-plugin\",
      \"allowed_roles\": \"immune-readonly,immune-readwrite\",
      \"connection_url\": \"postgresql://{{username}}:{{password}}@postgres-immunity:5432/adaptive_immunity?sslmode=disable\",
      \"username\": \"postgres\",
      \"password\": \"${POSTGRES_PASSWORD}\"
    }" \
    ${VAULT_ADDR}/v1/database/config/postgres-immunity >/dev/null
echo "  ✅ PostgreSQL immunity connection configured"
echo ""

# Create readonly role (main database)
echo "[4/5] Creating database roles (main)..."
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{
      "db_name": "postgres-main",
      "creation_statements": [
        "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '\''{{password}}'\'' VALID UNTIL '\''{{expiration}}'\'';",
        "GRANT CONNECT ON DATABASE vertice TO \"{{name}}\";",
        "GRANT USAGE ON SCHEMA public TO \"{{name}}\";",
        "GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO \"{{name}}\";"
      ],
      "default_ttl": "1h",
      "max_ttl": "24h"
    }' \
    ${VAULT_ADDR}/v1/database/roles/vertice-readonly >/dev/null
echo "  ✅ vertice-readonly role created (1h TTL)"

# Create readwrite role (main database)
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{
      "db_name": "postgres-main",
      "creation_statements": [
        "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '\''{{password}}'\'' VALID UNTIL '\''{{expiration}}'\'';",
        "GRANT CONNECT ON DATABASE vertice TO \"{{name}}\";",
        "GRANT USAGE ON SCHEMA public TO \"{{name}}\";",
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO \"{{name}}\";",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO \"{{name}}\";"
      ],
      "default_ttl": "2h",
      "max_ttl": "8h"
    }' \
    ${VAULT_ADDR}/v1/database/roles/vertice-readwrite >/dev/null
echo "  ✅ vertice-readwrite role created (2h TTL)"

# Create admin role (main database)
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{
      "db_name": "postgres-main",
      "creation_statements": [
        "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '\''{{password}}'\'' VALID UNTIL '\''{{expiration}}'\'' CREATEDB;",
        "GRANT ALL PRIVILEGES ON DATABASE vertice TO \"{{name}}\";",
        "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
        "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO \"{{name}}\";",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO \"{{name}}\";"
      ],
      "default_ttl": "4h",
      "max_ttl": "12h"
    }' \
    ${VAULT_ADDR}/v1/database/roles/vertice-admin >/dev/null
echo "  ✅ vertice-admin role created (4h TTL)"
echo ""

# Create roles for immunity database
echo "[5/5] Creating database roles (immunity)..."
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{
      "db_name": "postgres-immunity",
      "creation_statements": [
        "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '\''{{password}}'\'' VALID UNTIL '\''{{expiration}}'\'';",
        "GRANT CONNECT ON DATABASE adaptive_immunity TO \"{{name}}\";",
        "GRANT USAGE ON SCHEMA public TO \"{{name}}\";",
        "GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO \"{{name}}\";"
      ],
      "default_ttl": "1h",
      "max_ttl": "24h"
    }' \
    ${VAULT_ADDR}/v1/database/roles/immune-readonly >/dev/null
echo "  ✅ immune-readonly role created (1h TTL)"

curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{
      "db_name": "postgres-immunity",
      "creation_statements": [
        "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '\''{{password}}'\'' VALID UNTIL '\''{{expiration}}'\'';",
        "GRANT CONNECT ON DATABASE adaptive_immunity TO \"{{name}}\";",
        "GRANT USAGE ON SCHEMA public TO \"{{name}}\";",
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO \"{{name}}\";",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO \"{{name}}\";"
      ],
      "default_ttl": "2h",
      "max_ttl": "8h"
    }' \
    ${VAULT_ADDR}/v1/database/roles/immune-readwrite >/dev/null
echo "  ✅ immune-readwrite role created (2h TTL)"
echo ""

# Test dynamic credential generation
echo "[TEST] Generating test credentials..."
CREDS=$(curl -s -H "X-Vault-Token: ${VAULT_TOKEN}" ${VAULT_ADDR}/v1/database/creds/vertice-readonly)
USERNAME=$(echo $CREDS | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['username'])" 2>/dev/null || echo "")
PASSWORD=$(echo $CREDS | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['password'])" 2>/dev/null || echo "")

if [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
    echo "  ✅ Dynamic credentials generated successfully!"
    echo "  Username: $USERNAME"
    echo "  Password: ${PASSWORD:0:8}... (redacted)"
    echo "  Lease TTL: 1h"
else
    echo "  ❌ Failed to generate credentials"
    exit 1
fi
echo ""

echo "===================================="
echo "✅ Dynamic Database Secrets Complete!"
echo "===================================="
echo ""
echo "Available Roles:"
echo "  - vertice-readonly   (1h TTL, SELECT only)"
echo "  - vertice-readwrite  (2h TTL, SELECT/INSERT/UPDATE/DELETE)"
echo "  - vertice-admin      (4h TTL, ALL PRIVILEGES)"
echo "  - immune-readonly    (1h TTL, SELECT only)"
echo "  - immune-readwrite   (2h TTL, SELECT/INSERT/UPDATE/DELETE)"
echo ""
echo "Get credentials:"
echo "  curl -H 'X-Vault-Token: vertice-dev-root-token' http://localhost:8201/v1/database/creds/vertice-readonly"
echo ""
