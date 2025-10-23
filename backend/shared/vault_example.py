"""
Vault Client Integration Examples
VÉRTICE Platform - FASE 3

Examples of how to integrate Vault secrets into your services.

Author: MAXIMUS Team
Glory to YHWH - Keeper of Secrets
"""

import os
import psycopg2
from redis import Redis
from anthropic import Anthropic

# Import Vault client
from vault_client import get_vault_client


def example_1_get_api_key():
    """Example 1: Get API key from Vault"""
    vault = get_vault_client()

    # Get Anthropic API key
    api_key = vault.get_secret("maximus_ai/anthropic", key="api_key")

    # Use with Anthropic client
    client = Anthropic(api_key=api_key)

    print("✅ Anthropic client initialized with Vault API key")
    return client


def example_2_get_database_connection():
    """Example 2: Get PostgreSQL credentials from Vault"""
    vault = get_vault_client()

    # Get static credentials
    postgres_creds = vault.get_secret("postgres/main")

    # Connect to database
    conn = psycopg2.connect(
        host=postgres_creds["host"],
        port=postgres_creds["port"],
        database=postgres_creds["database"],
        user=postgres_creds["username"],
        password=postgres_creds["password"]
    )

    print("✅ PostgreSQL connected with Vault credentials")
    return conn


def example_3_get_dynamic_database_credentials():
    """Example 3: Get dynamic PostgreSQL credentials (recommended)"""
    vault = get_vault_client()

    # Get dynamic credentials (auto-expires after 1h)
    creds = vault.get_database_creds("vertice-readonly")

    # Connect to database
    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        database="vertice",
        user=creds["username"],
        password=creds["password"]
    )

    print(f"✅ PostgreSQL connected with dynamic credentials")
    print(f"  Username: {creds['username']}")
    print(f"  Lease: {creds['lease_duration']}s")

    return conn


def example_4_get_redis_connection():
    """Example 4: Get Redis credentials from Vault"""
    vault = get_vault_client()

    # Get Redis credentials
    redis_creds = vault.get_secret("redis/main")

    # Connect to Redis
    redis_client = Redis(
        host=redis_creds["host"],
        port=int(redis_creds["port"]),
        password=redis_creds["password"],
        decode_responses=True
    )

    # Test connection
    redis_client.ping()

    print("✅ Redis connected with Vault credentials")
    return redis_client


def example_5_fastapi_dependency():
    """Example 5: Use Vault in FastAPI dependency injection"""
    from fastapi import FastAPI, Depends
    from vault_client import VaultClient, get_vault_client

    app = FastAPI()

    @app.get("/secrets/test")
    def test_vault(vault: VaultClient = Depends(get_vault_client)):
        """Endpoint that uses Vault"""
        try:
            # Get secret
            api_key = vault.get_secret("maximus_ai/anthropic", key="api_key")

            return {
                "status": "ok",
                "vault_connected": True,
                "api_key_length": len(api_key)
            }
        except Exception as e:
            return {
                "status": "error",
                "vault_connected": False,
                "error": str(e)
            }

    print("✅ FastAPI app with Vault dependency configured")
    return app


def example_6_service_configuration():
    """Example 6: Complete service configuration from Vault"""
    vault = get_vault_client()

    class Config:
        """Service configuration loaded from Vault"""

        def __init__(self):
            # API Keys
            anthropic_secret = vault.get_secret("maximus_ai/anthropic")
            self.ANTHROPIC_API_KEY = anthropic_secret["api_key"]
            self.ANTHROPIC_MODEL = anthropic_secret["model"]

            # Database
            postgres = vault.get_secret("postgres/main")
            self.DATABASE_URL = f"postgresql://{postgres['username']}:{postgres['password']}@{postgres['host']}:{postgres['port']}/{postgres['database']}"

            # Redis
            redis = vault.get_secret("redis/main")
            self.REDIS_URL = f"redis://:{redis['password']}@{redis['host']}:{redis['port']}"

            # Kafka
            kafka = vault.get_secret("kafka/main")
            self.KAFKA_BOOTSTRAP_SERVERS = kafka["bootstrap_servers"]
            self.KAFKA_SASL_USERNAME = kafka["sasl_username"]
            self.KAFKA_SASL_PASSWORD = kafka["sasl_password"]

    config = Config()
    print("✅ Service configuration loaded from Vault")
    print(f"  Database: {config.DATABASE_URL[:30]}...")
    print(f"  Redis: {config.REDIS_URL[:30]}...")
    print(f"  Model: {config.ANTHROPIC_MODEL}")

    return config


def example_7_vault_health_check():
    """Example 7: Vault health check for monitoring"""
    vault = get_vault_client()

    if vault.health_check():
        print("✅ Vault is HEALTHY")
        return True
    else:
        print("❌ Vault is DOWN")
        return False


def example_8_circuit_breaker_demo():
    """Example 8: Circuit breaker pattern demo"""
    vault = get_vault_client()

    print("Testing circuit breaker...")

    # Simulate failures
    for i in range(10):
        try:
            # This will fail if circuit is open
            vault.get_secret("nonexistent/path")
        except Exception as e:
            print(f"  Attempt {i+1}: {type(e).__name__}")

            # Circuit should open after 5 failures
            if i >= 5:
                print("  ⚠️  Circuit breaker should be OPEN now")
                break


if __name__ == "__main__":
    print("=" * 60)
    print("Vault Client Integration Examples")
    print("=" * 60)
    print()

    # Run examples
    try:
        print("[1] API Key Example")
        # example_1_get_api_key()
        print("  (Skipped - requires Anthropic import)")
        print()

        print("[2] Database Connection Example")
        # example_2_get_database_connection()
        print("  (Skipped - requires PostgreSQL running)")
        print()

        print("[3] Dynamic Database Credentials Example")
        # example_3_get_dynamic_database_credentials()
        print("  (Skipped - requires PostgreSQL running)")
        print()

        print("[4] Redis Connection Example")
        # example_4_get_redis_connection()
        print("  (Skipped - requires Redis running)")
        print()

        print("[5] FastAPI Dependency Example")
        app = example_5_fastapi_dependency()
        print()

        print("[6] Service Configuration Example")
        # config = example_6_service_configuration()
        print("  (Skipped - requires all secrets configured)")
        print()

        print("[7] Vault Health Check Example")
        example_7_vault_health_check()
        print()

        print("[8] Circuit Breaker Demo")
        # example_8_circuit_breaker_demo()
        print("  (Skipped - causes intentional failures)")
        print()

    except Exception as e:
        print(f"❌ Example failed: {e}")

    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)
