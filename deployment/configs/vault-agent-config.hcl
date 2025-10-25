# Vault Agent Configuration
# VÉRTICE Platform - FASE 3
#
# Auto-authentication for services using AppRole

vault {
  address = "http://vault:8200"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path = "/vault/data/role-id"
      secret_id_file_path = "/vault/data/secret-id"
      remove_secret_id_file_after_reading = false
    }
  }

  sink "file" {
    config = {
      path = "/vault/data/token"
    }
  }
}

cache {
  use_auto_auth_token = true
}

listener "tcp" {
  address = "127.0.0.1:8100"
  tls_disable = true
}
