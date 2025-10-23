#!/bin/bash
# Vault Initialization Script (using curl)
# VÉRTICE Platform - FASE 3

set -e

VAULT_ADDR="http://localhost:8201"
VAULT_TOKEN="vertice-dev-root-token"

echo "===================================="
echo "VÉRTICE Vault Initialization"
echo "===================================="
echo ""

# Wait for Vault to be ready
echo "[1/7] Waiting for Vault to be ready..."
until curl -s ${VAULT_ADDR}/v1/sys/health >/dev/null 2>&1; do
    echo "  Waiting for Vault..."
    sleep 2
done
echo "  ✅ Vault is ready!"
echo ""

# Enable KV v2 secrets engine
echo "[2/7] Enabling KV v2 secrets engine..."
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{"type":"kv-v2"}' \
    ${VAULT_ADDR}/v1/sys/mounts/secret || echo "  Already enabled"
echo "  ✅ KV v2 enabled at secret/"
echo ""

# Enable AppRole authentication
echo "[3/7] Enabling AppRole authentication..."
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{"type":"approle"}' \
    ${VAULT_ADDR}/v1/sys/auth/approle || echo "  Already enabled"
echo "  ✅ AppRole enabled"
echo ""

# Create policies
echo "[4/7] Creating Vault policies..."

# maximus-ai policy
curl -s -X PUT -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{
      "policy": "path \"secret/data/maximus_ai/*\" { capabilities = [\"read\", \"list\"] }\npath \"secret/data/postgres/*\" { capabilities = [\"read\", \"list\"] }\npath \"secret/data/redis/*\" { capabilities = [\"read\", \"list\"] }\npath \"secret/data/kafka/*\" { capabilities = [\"read\", \"list\"] }"
    }' \
    ${VAULT_ADDR}/v1/sys/policies/acl/maximus-ai >/dev/null
echo "  ✅ maximus-ai policy created"

# immune-system policy
curl -s -X PUT -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{
      "policy": "path \"secret/data/immune/*\" { capabilities = [\"read\", \"list\"] }\npath \"secret/data/postgres/*\" { capabilities = [\"read\", \"list\"] }\npath \"secret/data/kafka/*\" { capabilities = [\"read\", \"list\"] }"
    }' \
    ${VAULT_ADDR}/v1/sys/policies/acl/immune-system >/dev/null
echo "  ✅ immune-system policy created"

# infrastructure policy
curl -s -X PUT -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{
      "policy": "path \"secret/data/*\" { capabilities = [\"read\", \"list\"] }"
    }' \
    ${VAULT_ADDR}/v1/sys/policies/acl/infrastructure >/dev/null
echo "  ✅ infrastructure policy created"
echo ""

# Create AppRoles
echo "[5/7] Creating AppRoles..."
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{"token_policies":["maximus-ai"],"token_ttl":"1h","token_max_ttl":"4h"}' \
    ${VAULT_ADDR}/v1/auth/approle/role/maximus-ai >/dev/null
echo "  ✅ maximus-ai role created"

curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{"token_policies":["immune-system"],"token_ttl":"1h","token_max_ttl":"4h"}' \
    ${VAULT_ADDR}/v1/auth/approle/role/immune-system >/dev/null
echo "  ✅ immune-system role created"

curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d '{"token_policies":["infrastructure"],"token_ttl":"1h","token_max_ttl":"4h"}' \
    ${VAULT_ADDR}/v1/auth/approle/role/infrastructure >/dev/null
echo "  ✅ infrastructure role created"
echo ""

# Migrate initial secrets
echo "[6/7] Migrating initial secrets..."

# MAXIMUS AI secrets
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-placeholder_anthropic_key}"
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d "{\"data\":{\"api_key\":\"${ANTHROPIC_API_KEY}\",\"model\":\"claude-3-7-sonnet-20250219\"}}" \
    ${VAULT_ADDR}/v1/secret/data/maximus_ai/anthropic >/dev/null
echo "  ✅ MAXIMUS AI secrets migrated"

# PostgreSQL secrets
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d "{\"data\":{\"username\":\"postgres\",\"password\":\"${POSTGRES_PASSWORD}\",\"host\":\"postgres\",\"port\":\"5432\",\"database\":\"vertice\"}}" \
    ${VAULT_ADDR}/v1/secret/data/postgres/main >/dev/null
echo "  ✅ PostgreSQL secrets migrated"

# Redis secrets
REDIS_PASSWORD="${REDIS_PASSWORD:-maximus_redis}"
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d "{\"data\":{\"password\":\"${REDIS_PASSWORD}\",\"host\":\"redis-master\",\"port\":\"6379\"}}" \
    ${VAULT_ADDR}/v1/secret/data/redis/main >/dev/null
echo "  ✅ Redis secrets migrated"

# Kafka secrets
KAFKA_SASL_PASSWORD="${KAFKA_SASL_PASSWORD:-kafka_password}"
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d "{\"data\":{\"sasl_username\":\"kafka\",\"sasl_password\":\"${KAFKA_SASL_PASSWORD}\",\"bootstrap_servers\":\"kafka:9092\"}}" \
    ${VAULT_ADDR}/v1/secret/data/kafka/main >/dev/null
echo "  ✅ Kafka secrets migrated"

# Immune System secrets
curl -s -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" \
    -d "{\"data\":{\"username\":\"postgres\",\"password\":\"${POSTGRES_PASSWORD}\",\"host\":\"postgres-immunity\",\"port\":\"5432\",\"database\":\"adaptive_immunity\"}}" \
    ${VAULT_ADDR}/v1/secret/data/immune/postgres >/dev/null
echo "  ✅ Immune System secrets migrated"
echo ""

# Test secret retrieval
echo "[7/7] Testing secret retrieval..."
RESULT=$(curl -s -H "X-Vault-Token: ${VAULT_TOKEN}" ${VAULT_ADDR}/v1/secret/data/postgres/main | grep -o '"username"' || echo "")
if [ -n "$RESULT" ]; then
    echo "  ✅ Secrets retrieval working!"
else
    echo "  ❌ Failed to retrieve secrets"
    exit 1
fi
echo ""

echo "===================================="
echo "✅ Vault initialization complete!"
echo "===================================="
echo ""
echo "Vault UI: http://localhost:8201"
echo "Root Token: vertice-dev-root-token"
echo ""
echo "Test commands:"
echo "  curl -H 'X-Vault-Token: vertice-dev-root-token' http://localhost:8201/v1/secret/data/postgres/main"
echo ""
