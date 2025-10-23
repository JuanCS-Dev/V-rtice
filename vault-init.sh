#!/bin/bash
# Vault Initialization Script
# VÉRTICE Platform - FASE 3
#
# This script initializes Vault with:
# - KV v2 secrets engine
# - Database secrets engine for PostgreSQL
# - AppRole authentication
# - Initial secrets migration

set -e

export VAULT_ADDR='http://localhost:8201'
export VAULT_TOKEN='vertice-dev-root-token'

echo "===================================="
echo "VÉRTICE Vault Initialization"
echo "===================================="
echo ""

# Wait for Vault to be ready
echo "[1/7] Waiting for Vault to be ready..."
until docker compose -f docker-compose.vault.yml exec -T vault vault status >/dev/null 2>&1; do
    echo "  Waiting for Vault..."
    sleep 2
done
echo "  ✅ Vault is ready!"
echo ""

# Enable KV v2 secrets engine
echo "[2/7] Enabling KV v2 secrets engine..."
docker compose -f docker-compose.vault.yml exec -T -e VAULT_ADDR='http://127.0.0.1:8200' vault vault secrets enable -path=secret kv-v2 || echo "  Already enabled"
echo "  ✅ KV v2 enabled at secret/"
echo ""

# Enable AppRole authentication
echo "[3/7] Enabling AppRole authentication..."
docker compose -f docker-compose.vault.yml exec -T vault vault auth enable approle || echo "  Already enabled"
echo "  ✅ AppRole enabled"
echo ""

# Create policies
echo "[4/7] Creating Vault policies..."

# Policy for MAXIMUS AI services
docker compose -f docker-compose.vault.yml exec -T vault vault policy write maximus-ai - <<EOF
path "secret/data/maximus_ai/*" {
  capabilities = ["read", "list"]
}
path "secret/data/postgres/*" {
  capabilities = ["read", "list"]
}
path "secret/data/redis/*" {
  capabilities = ["read", "list"]
}
path "secret/data/kafka/*" {
  capabilities = ["read", "list"]
}
EOF
echo "  ✅ maximus-ai policy created"

# Policy for Immune System services
docker compose -f docker-compose.vault.yml exec -T vault vault policy write immune-system - <<EOF
path "secret/data/immune/*" {
  capabilities = ["read", "list"]
}
path "secret/data/postgres/*" {
  capabilities = ["read", "list"]
}
path "secret/data/kafka/*" {
  capabilities = ["read", "list"]
}
EOF
echo "  ✅ immune-system policy created"

# Policy for Infrastructure services
docker compose -f docker-compose.vault.yml exec -T vault vault policy write infrastructure - <<EOF
path "secret/data/*" {
  capabilities = ["read", "list"]
}
EOF
echo "  ✅ infrastructure policy created"
echo ""

# Create AppRoles
echo "[5/7] Creating AppRoles..."
docker compose -f docker-compose.vault.yml exec -T vault vault write auth/approle/role/maximus-ai \
    token_policies="maximus-ai" \
    token_ttl=1h \
    token_max_ttl=4h
echo "  ✅ maximus-ai role created"

docker compose -f docker-compose.vault.yml exec -T vault vault write auth/approle/role/immune-system \
    token_policies="immune-system" \
    token_ttl=1h \
    token_max_ttl=4h
echo "  ✅ immune-system role created"

docker compose -f docker-compose.vault.yml exec -T vault vault write auth/approle/role/infrastructure \
    token_policies="infrastructure" \
    token_ttl=1h \
    token_max_ttl=4h
echo "  ✅ infrastructure role created"
echo ""

# Migrate initial secrets
echo "[6/7] Migrating initial secrets..."

# MAXIMUS AI secrets (from .env or defaults)
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-placeholder_anthropic_key}"
docker compose -f docker-compose.vault.yml exec -T vault vault kv put secret/maximus_ai/anthropic \
    api_key="${ANTHROPIC_API_KEY}" \
    model="claude-3-7-sonnet-20250219"
echo "  ✅ MAXIMUS AI secrets migrated"

# PostgreSQL secrets
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
docker compose -f docker-compose.vault.yml exec -T vault vault kv put secret/postgres/main \
    username="postgres" \
    password="${POSTGRES_PASSWORD}" \
    host="postgres" \
    port="5432" \
    database="vertice"
echo "  ✅ PostgreSQL secrets migrated"

# Redis secrets
REDIS_PASSWORD="${REDIS_PASSWORD:-maximus_redis}"
docker compose -f docker-compose.vault.yml exec -T vault vault kv put secret/redis/main \
    password="${REDIS_PASSWORD}" \
    host="redis-master" \
    port="6379"
echo "  ✅ Redis secrets migrated"

# Kafka secrets
KAFKA_SASL_PASSWORD="${KAFKA_SASL_PASSWORD:-kafka_password}"
docker compose -f docker-compose.vault.yml exec -T vault vault kv put secret/kafka/main \
    sasl_username="kafka" \
    sasl_password="${KAFKA_SASL_PASSWORD}" \
    bootstrap_servers="kafka:9092"
echo "  ✅ Kafka secrets migrated"

# Immune System secrets
docker compose -f docker-compose.vault.yml exec -T vault vault kv put secret/immune/postgres \
    username="postgres" \
    password="${POSTGRES_PASSWORD}" \
    host="postgres-immunity" \
    port="5432" \
    database="adaptive_immunity"
echo "  ✅ Immune System secrets migrated"
echo ""

# Enable Database secrets engine (for dynamic credentials)
echo "[7/7] Enabling Database secrets engine for PostgreSQL..."
docker compose -f docker-compose.vault.yml exec -T vault vault secrets enable database || echo "  Already enabled"

# Configure PostgreSQL connection
docker compose -f docker-compose.vault.yml exec -T vault vault write database/config/postgres \
    plugin_name=postgresql-database-plugin \
    allowed_roles="maximus-readonly,maximus-readwrite" \
    connection_url="postgresql://{{username}}:{{password}}@postgres:5432/vertice?sslmode=disable" \
    username="postgres" \
    password="${POSTGRES_PASSWORD}"
echo "  ✅ PostgreSQL connection configured"

# Create readonly role
docker compose -f docker-compose.vault.yml exec -T vault vault write database/roles/maximus-readonly \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"
echo "  ✅ maximus-readonly role created"

# Create readwrite role
docker compose -f docker-compose.vault.yml exec -T vault vault write database/roles/maximus-readwrite \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"
echo "  ✅ maximus-readwrite role created"
echo ""

echo "===================================="
echo "✅ Vault initialization complete!"
echo "===================================="
echo ""
echo "Vault UI: http://localhost:8200"
echo "Root Token: vertice-dev-root-token"
echo ""
echo "Test commands:"
echo "  docker compose -f docker-compose.vault.yml exec vault vault kv list secret/"
echo "  docker compose -f docker-compose.vault.yml exec vault vault kv get secret/maximus_ai/anthropic"
echo "  docker compose -f docker-compose.vault.yml exec vault vault read database/creds/maximus-readonly"
echo ""
