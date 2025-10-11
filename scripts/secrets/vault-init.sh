#!/bin/bash
#
# Vault Initialization Script
# ============================
#
# Purpose: Initialize HashiCorp Vault and create secrets structure
# Issue: #35 - Secrets management (Vault)
#
# Usage:
#   ./vault-init.sh [--reset]
#
# What it does:
# 1. Checks if Vault is running
# 2. Initializes Vault (if needed)
# 3. Creates secrets engines
# 4. Stores initial secrets
# 5. Outputs access information
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
ROOT_TOKEN="vertice-dev-root-token"  # Dev mode token
SECRETS_FILE="$HOME/.vertice-vault-secrets"

# Parse arguments
RESET=false
if [ "$1" = "--reset" ]; then
    RESET=true
fi

echo -e "${BLUE}🔒 Vault Initialization Script${NC}"
echo "================================"
echo ""

# ============================================================================
# Check if Vault is running
# ============================================================================

echo -e "${YELLOW}Checking Vault status...${NC}"

if ! curl -s "$VAULT_ADDR/v1/sys/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Vault is not running!${NC}"
    echo ""
    echo "Start Vault with:"
    echo "  docker-compose -f docker-compose.secrets.yml up -d"
    exit 1
fi

echo -e "${GREEN}✅ Vault is running${NC}"
echo ""

# Set vault CLI environment
export VAULT_ADDR
export VAULT_TOKEN="$ROOT_TOKEN"

# ============================================================================
# Initialize Vault (if not initialized)
# ============================================================================

if [ "$RESET" = true ]; then
    echo -e "${YELLOW}Resetting Vault (dev mode - auto-restart)...${NC}"
    # In dev mode, just restart the container
    docker restart vertice-vault
    sleep 5
    echo -e "${GREEN}✅ Vault reset${NC}"
    echo ""
fi

# ============================================================================
# Enable Audit Logging
# ============================================================================

echo -e "${YELLOW}Enabling audit logging...${NC}"

# Check if audit device exists
if vault audit list 2>/dev/null | grep -q "file/"; then
    echo -e "${GREEN}✅ Audit logging already enabled${NC}"
else
    # Enable file audit device
    vault audit enable file file_path=/vault/logs/audit.log || echo "Audit already enabled"
    echo -e "${GREEN}✅ Audit logging enabled${NC}"
fi
echo ""

# ============================================================================
# Create Secrets Engines
# ============================================================================

echo -e "${YELLOW}Creating secrets engines...${NC}"

# KV Secrets Engine v2 (versioned secrets)
if vault secrets list 2>/dev/null | grep -q "vertice/"; then
    echo -e "${GREEN}✅ KV secrets engine already exists${NC}"
else
    vault secrets enable -path=vertice kv-v2
    echo -e "${GREEN}✅ KV secrets engine created${NC}"
fi

# Database secrets engine (dynamic credentials)
if vault secrets list 2>/dev/null | grep -q "database/"; then
    echo -e "${GREEN}✅ Database secrets engine already exists${NC}"
else
    vault secrets enable database
    echo -e "${GREEN}✅ Database secrets engine created${NC}"
fi

echo ""

# ============================================================================
# Store Initial Secrets
# ============================================================================

echo -e "${YELLOW}Storing initial secrets...${NC}"

# API Keys
vault kv put vertice/api-keys/virustotal \
    api_key="YOUR_VIRUSTOTAL_API_KEY_REPLACE_IN_PRODUCTION" \
    url="https://www.virustotal.com/api/v3"

vault kv put vertice/api-keys/shodan \
    api_key="YOUR_SHODAN_API_KEY_REPLACE_IN_PRODUCTION" \
    url="https://api.shodan.io"

vault kv put vertice/api-keys/abuseipdb \
    api_key="YOUR_ABUSEIPDB_API_KEY_REPLACE_IN_PRODUCTION" \
    url="https://api.abuseipdb.com/api/v2"

vault kv put vertice/api-keys/greynoise \
    api_key="YOUR_GREYNOISE_API_KEY_REPLACE_IN_PRODUCTION" \
    url="https://api.greynoise.io/v3"

# Database credentials
vault kv put vertice/database/postgres \
    host="localhost" \
    port="5432" \
    username="vertice" \
    password="CHANGE_ME_IN_PRODUCTION" \
    database="vertice"

vault kv put vertice/database/redis \
    host="localhost" \
    port="6379" \
    password="CHANGE_ME_IN_PRODUCTION"

# Application secrets
vault kv put vertice/app/jwt \
    secret_key="CHANGE_ME_IN_PRODUCTION_USE_256_BIT_KEY" \
    algorithm="HS256" \
    expiration_minutes="30"

vault kv put vertice/app/encryption \
    key="CHANGE_ME_IN_PRODUCTION_USE_AES_256_KEY" \
    algorithm="AES-256-GCM"

# OAuth credentials
vault kv put vertice/oauth/google \
    client_id="YOUR_GOOGLE_CLIENT_ID" \
    client_secret="YOUR_GOOGLE_CLIENT_SECRET" \
    redirect_uri="http://localhost:3000/auth/callback/google"

echo -e "${GREEN}✅ Initial secrets stored${NC}"
echo ""

# ============================================================================
# Create Policies
# ============================================================================

echo -e "${YELLOW}Creating access policies...${NC}"

# Read-only policy for services
vault policy write vertice-readonly - <<EOF
# Read access to API keys
path "vertice/data/api-keys/*" {
  capabilities = ["read"]
}

# Read access to database credentials
path "vertice/data/database/*" {
  capabilities = ["read"]
}

# Read access to app secrets
path "vertice/data/app/*" {
  capabilities = ["read"]
}
EOF

# Write policy for admins
vault policy write vertice-admin - <<EOF
# Full access to all secrets
path "vertice/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage policies
path "sys/policies/acl/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage auth methods
path "sys/auth/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

echo -e "${GREEN}✅ Policies created${NC}"
echo ""

# ============================================================================
# Create AppRole for Services
# ============================================================================

echo -e "${YELLOW}Creating AppRole for services...${NC}"

# Enable AppRole auth
if vault auth list 2>/dev/null | grep -q "approle/"; then
    echo -e "${GREEN}✅ AppRole already enabled${NC}"
else
    vault auth enable approle
    echo -e "${GREEN}✅ AppRole enabled${NC}"
fi

# Create role for services
vault write auth/approle/role/vertice-services \
    token_ttl=1h \
    token_max_ttl=4h \
    token_policies="vertice-readonly" \
    secret_id_ttl=0

# Get role ID and secret ID
ROLE_ID=$(vault read -field=role_id auth/approle/role/vertice-services/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/vertice-services/secret-id)

echo -e "${GREEN}✅ AppRole created${NC}"
echo ""

# ============================================================================
# Output Access Information
# ============================================================================

echo "================================"
echo -e "${GREEN}✅ Vault initialization complete!${NC}"
echo "================================"
echo ""
echo -e "${BLUE}Access Information:${NC}"
echo "  Vault URL: $VAULT_ADDR"
echo "  Vault UI:  $VAULT_ADDR/ui"
echo "  Root Token: $ROOT_TOKEN"
echo ""
echo -e "${BLUE}AppRole Credentials (for services):${NC}"
echo "  Role ID:   $ROLE_ID"
echo "  Secret ID: $SECRET_ID"
echo ""
echo -e "${YELLOW}Save these to .env:${NC}"
cat << ENV

# Vault Configuration
VAULT_ADDR=$VAULT_ADDR
VAULT_ROLE_ID=$ROLE_ID
VAULT_SECRET_ID=$SECRET_ID

ENV
echo ""
echo -e "${BLUE}Quick Test:${NC}"
echo "  # List secrets"
echo "  vault kv list vertice/api-keys"
echo ""
echo "  # Read secret"
echo "  vault kv get vertice/api-keys/virustotal"
echo ""
echo "  # Update secret"
echo "  vault kv put vertice/api-keys/virustotal api_key=\"YOUR_NEW_KEY\""
echo ""
echo -e "${RED}⚠️  SECURITY REMINDERS:${NC}"
echo "  1. Change all default secrets in production"
echo "  2. Enable TLS/HTTPS for Vault"
echo "  3. Store unseal keys securely (5 different locations)"
echo "  4. Enable MFA for root token"
echo "  5. Rotate secrets regularly"
echo "  6. Monitor audit logs"
echo ""
