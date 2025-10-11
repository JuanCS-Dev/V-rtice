# Secrets Management with HashiCorp Vault 🔒

**Version**: 1.0.0  
**Last Updated**: 2025-01-11  
**Owner**: Security Team  
**Issue**: #35

---

## 🎯 Overview

HashiCorp Vault provides centralized secrets management for the Vértice Platform, replacing hardcoded credentials and environment variables with a secure, audited, and versioned secrets store.

---

## 🚀 Quick Start

### 1. Start Vault

```bash
# Start Vault container
docker-compose -f docker-compose.secrets.yml up -d

# Wait for Vault to be ready
docker logs vertice-vault -f
```

### 2. Initialize Vault

```bash
# Run initialization script
./scripts/secrets/vault-init.sh

# Save the output (root token, role ID, secret ID)
```

### 3. Access Vault UI

Open browser: http://localhost:8200/ui

Login with root token: `vertice-dev-root-token`

### 4. Use in Python

```python
from backend.shared.vault_client import get_api_key

# Get API key
shodan_key = get_api_key("shodan", fallback_env="SHODAN_API_KEY")

# Use in service
response = requests.get(
    "https://api.shodan.io/search",
    params={"key": shodan_key, "query": "apache"}
)
```

---

## 📂 Secrets Structure

```
vertice/
├── api-keys/
│   ├── virustotal
│   ├── shodan
│   ├── abuseipdb
│   ├── greynoise
│   ├── alienvault-otx
│   └── censys
├── database/
│   ├── postgres
│   ├── redis
│   └── mongodb
├── app/
│   ├── jwt
│   ├── encryption
│   └── session
└── oauth/
    ├── google
    ├── github
    └── microsoft
```

---

## 🔧 Usage Examples

### Python Service

```python
from backend.shared.vault_client import VaultClient

# Initialize client
vault = VaultClient()

# Get API key
vt_key = vault.get_secret("api-keys/virustotal", "api_key")

# Get full secret
db_config = vault.get_secret("database/postgres")
# Returns: {"host": "...", "port": "...", "username": "...", ...}

# With fallback to env var
api_key = vault.get_secret(
    "api-keys/shodan",
    "api_key",
    fallback_env="SHODAN_API_KEY"
)

# Store new secret
vault.set_secret("api-keys/new-service", {
    "api_key": "secret_key_here",
    "url": "https://api.example.com"
})

# List secrets
secrets = vault.list_secrets("api-keys")
print(secrets)  # ['virustotal', 'shodan', ...]
```

### Vault CLI

```bash
# Set environment
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=vertice-dev-root-token

# List secrets
vault kv list vertice/api-keys

# Read secret
vault kv get vertice/api-keys/virustotal

# Write secret
vault kv put vertice/api-keys/new-service \
    api_key="YOUR_KEY" \
    url="https://api.example.com"

# Delete secret
vault kv delete vertice/api-keys/old-service

# Get secret history
vault kv metadata get vertice/api-keys/virustotal
```

---

## 🔐 Authentication

### AppRole (Services)

Recommended for services and applications:

```python
from backend.shared.vault_client import VaultClient

# Environment variables
# VAULT_ADDR=http://localhost:8200
# VAULT_ROLE_ID=<from vault-init.sh>
# VAULT_SECRET_ID=<from vault-init.sh>

vault = VaultClient()
secret = vault.get_secret("api-keys/shodan", "api_key")
```

### Token (Development)

For development and testing:

```python
vault = VaultClient(token="vertice-dev-root-token")
```

### Root Token (Admin)

Only for administrative tasks:

```bash
export VAULT_TOKEN=vertice-dev-root-token
vault kv put vertice/api-keys/admin-key api_key="secret"
```

---

## 🔄 Secret Rotation

### Manual Rotation

```bash
# Update secret
vault kv put vertice/api-keys/virustotal \
    api_key="NEW_KEY_HERE" \
    url="https://www.virustotal.com/api/v3"

# Services will get new key on next request (cached for 5 min)
```

### Automatic Rotation

For database credentials:

```bash
# Configure database secrets engine
vault secrets enable database

vault write database/config/postgres \
    plugin_name=postgresql-database-plugin \
    allowed_roles="vertice-readonly,vertice-readwrite" \
    connection_url="postgresql://{{username}}:{{password}}@localhost:5432/vertice" \
    username="vault" \
    password="vault-password"

# Create role with TTL
vault write database/roles/vertice-readonly \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"

# Get dynamic credentials
vault read database/creds/vertice-readonly
```

---

## 📊 Monitoring

### Health Check

```bash
# Vault status
curl http://localhost:8200/v1/sys/health

# Seal status
vault status
```

### Metrics (Prometheus)

```bash
# Enable telemetry
curl http://localhost:8200/v1/sys/metrics

# Add to Prometheus config
scrape_configs:
  - job_name: 'vault'
    metrics_path: '/v1/sys/metrics'
    params:
      format: ['prometheus']
    static_configs:
      - targets: ['localhost:8200']
```

### Audit Logs

```bash
# View audit logs
docker exec vertice-vault cat /vault/logs/audit.log

# Parse with jq
docker exec vertice-vault cat /vault/logs/audit.log | jq '.'
```

---

## 🔒 Security Best Practices

### Development

- ✅ Use dev mode with in-memory storage
- ✅ HTTP is acceptable (localhost only)
- ✅ Root token for convenience
- ❌ Don't commit tokens to git
- ❌ Don't use dev mode in staging/production

### Production

- ✅ Use TLS/HTTPS with valid certificates
- ✅ Consul/etcd storage backend (HA)
- ✅ 5 unseal keys (threshold 3)
- ✅ AppRole or Kubernetes auth
- ✅ Enable audit logging
- ✅ Regular backups
- ✅ Token TTL limits
- ✅ MFA for root token
- ❌ Never expose Vault port publicly
- ❌ Never use root token in services

### Secret Hygiene

1. **Rotation Schedule**:
   - API keys: Quarterly
   - Database passwords: Monthly
   - JWT secrets: Annually
   - Root token: On personnel change

2. **Access Control**:
   - Least privilege principle
   - Role-based policies
   - Regular access reviews

3. **Monitoring**:
   - Alert on failed authentication
   - Alert on secret access patterns
   - Alert on seal status changes

---

## 🚨 Troubleshooting

### Vault Not Starting

```bash
# Check logs
docker logs vertice-vault

# Common issues:
# - Port 8200 already in use
# - Volume permissions
# - IPC_LOCK capability missing
```

### Authentication Failed

```bash
# Check token expiry
vault token lookup

# Renew token
vault token renew

# Re-authenticate with AppRole
./scripts/secrets/vault-init.sh
```

### Secret Not Found

```bash
# List available secrets
vault kv list vertice/api-keys

# Check path format (note: no leading slash)
vault kv get vertice/api-keys/shodan  # ✅ Correct
vault kv get /vertice/api-keys/shodan  # ❌ Wrong
```

---

## 📋 Migration from .env

### Before (insecure)

```bash
# .env
VIRUSTOTAL_API_KEY=secret_key_here
SHODAN_API_KEY=another_secret
DB_PASSWORD=password123
```

```python
import os
api_key = os.getenv("VIRUSTOTAL_API_KEY")
```

### After (secure)

```bash
# .env (only Vault credentials)
VAULT_ADDR=http://localhost:8200
VAULT_ROLE_ID=<role-id>
VAULT_SECRET_ID=<secret-id>
```

```python
from backend.shared.vault_client import get_api_key
api_key = get_api_key("virustotal")
```

### Migration Script

```bash
#!/bin/bash
# migrate-secrets-to-vault.sh

# Read .env
source .env

# Store in Vault
vault kv put vertice/api-keys/virustotal api_key="$VIRUSTOTAL_API_KEY"
vault kv put vertice/api-keys/shodan api_key="$SHODAN_API_KEY"
vault kv put vertice/database/postgres password="$DB_PASSWORD"

# Remove from .env (BACKUP FIRST!)
# sed -i.bak '/VIRUSTOTAL_API_KEY/d' .env
```

---

## 🔗 References

- [HashiCorp Vault Docs](https://www.vaultproject.io/docs)
- [Vault API Reference](https://www.vaultproject.io/api-docs)
- [hvac Python Client](https://github.com/hvac/hvac)
- [Vault Production Hardening](https://learn.hashicorp.com/tutorials/vault/production-hardening)

---

## ✅ Completion Checklist

- [x] Docker Compose configuration
- [x] Vault initialization script
- [x] Python client library
- [x] Documentation
- [ ] Migrate 5 critical secrets
- [ ] Test in 3 services
- [ ] Production deployment guide
- [ ] Backup/restore procedures

---

**Status**: ✅ **INFRASTRUCTURE COMPLETE**  
**Next**: Migrate secrets from .env to Vault

**Issue #35** | Day 68+ | Secrets Management 🔒
