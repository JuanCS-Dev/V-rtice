# HashiCorp Vault Configuration
# ==============================
#
# Server configuration for development/testing
# For production, use proper storage backend and seal configuration

# Storage backend (file - for dev only)
storage "file" {
  path = "/vault/file"
}

# HTTP listener
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1  # Disable TLS for dev (ENABLE for production!)
  
  # For production with TLS:
  # tls_disable = 0
  # tls_cert_file = "/vault/certs/vault.crt"
  # tls_key_file  = "/vault/certs/vault.key"
}

# API address
api_addr = "http://0.0.0.0:8200"

# UI (web interface)
ui = true

# Telemetry (Prometheus metrics)
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}

# Logging
log_level = "info"
log_format = "json"

# Default lease TTL
default_lease_ttl = "768h"  # 32 days
max_lease_ttl = "8760h"     # 365 days

# Disable mlock in container (use IPC_LOCK cap instead)
disable_mlock = false

# Seal configuration (auto-unseal for production)
# For AWS KMS:
# seal "awskms" {
#   region     = "us-east-1"
#   kms_key_id = "alias/vault-unseal-key"
# }

# For dev mode, sealing is handled automatically
