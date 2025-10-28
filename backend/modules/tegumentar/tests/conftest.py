"""
Configuração de fixtures compartilhadas para testes do Tegumentar.

Seguindo Padrão Pagani (Constituição Vértice v2.5 - Artigo II):
- Zero mocks desnecessários
- Fixtures reusáveis e bem documentadas
- Isolamento completo entre testes
"""
import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# ASYNCIO EVENT LOOP
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Cria event loop para testes async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# MOCK EXTERNAL SERVICES
# ============================================================================


@pytest.fixture
def mock_redis() -> MagicMock:
    """Mock do Redis para rate limiting."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.keys = AsyncMock(return_value=[])
    return redis


@pytest.fixture
def mock_kafka_producer() -> MagicMock:
    """Mock do Kafka Producer."""
    producer = MagicMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    producer.send = AsyncMock()
    producer.send_and_wait = AsyncMock(return_value=MagicMock(offset=0))
    return producer


@pytest.fixture
def mock_postgresql() -> MagicMock:
    """Mock do PostgreSQL connection pool."""
    pool = MagicMock()

    # Mock connection context manager
    conn = MagicMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=None)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=None)

    pool.acquire = MagicMock(return_value=conn)
    pool.close = AsyncMock()

    return pool


@pytest.fixture
def mock_nftables_command() -> Generator[MagicMock, None, None]:
    """Mock de comandos nftables (subprocess)."""
    with patch("asyncio.create_subprocess_exec") as mock_proc:
        # Mock process
        process = MagicMock()
        process.communicate = AsyncMock(return_value=(b"", b""))
        process.returncode = 0

        mock_proc.return_value = process
        yield mock_proc


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Mock do httpx.AsyncClient para integrações HTTP."""
    client = MagicMock()

    # Mock response
    response = MagicMock()
    response.status_code = 200
    response.json = MagicMock(return_value={"status": "ok"})
    response.text = "OK"
    response.raise_for_status = MagicMock()

    client.post = AsyncMock(return_value=response)
    client.get = AsyncMock(return_value=response)
    client.put = AsyncMock(return_value=response)
    client.delete = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    return client


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture
def temp_config_file() -> Generator[str, None, None]:
    """Cria arquivo de configuração temporário."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            """
epiderme:
  nftables_table: "filter"
  nftables_chain: "tegumentar_input"
  reputation_feeds:
    - "https://example.com/blocklist.txt"
  rate_limit:
    default_limit: 100
    default_window: 60

derme:
  enabled: false
  postgresql_dsn: "postgresql://test:test@localhost:5432/tegumentar_test"
  kafka_bootstrap_servers: "localhost:9092"

hipoderme:
  mmei_url: "http://localhost:8600"
  lymphnode_url: "http://localhost:8021"
"""
        )
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_tegumentar_settings() -> MagicMock:
    """Mock das configurações do Tegumentar."""
    from backend.modules.tegumentar.config import TegumentarSettings

    settings = MagicMock(spec=TegumentarSettings)
    settings.EPIDERME_NFTABLES_TABLE = "filter"
    settings.EPIDERME_NFTABLES_CHAIN = "tegumentar_input"
    settings.EPIDERME_RATE_LIMIT_DEFAULT = 100
    settings.EPIDERME_RATE_LIMIT_WINDOW = 60
    settings.EPIDERME_REPUTATION_FEEDS = ["https://example.com/blocklist.txt"]

    settings.DERME_ENABLED = False
    settings.DERME_POSTGRESQL_DSN = "postgresql://test:test@localhost:5432/test"
    settings.DERME_KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    settings.DERME_KAFKA_TOPIC_LANGERHANS = "tegumentar.langerhans"

    settings.HIPODERME_MMEI_URL = "http://localhost:8600"
    settings.HIPODERME_LYMPHNODE_URL = "http://localhost:8021"

    settings.REDIS_URL = "redis://localhost:6379/0"

    return settings


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_ip_packet() -> dict:
    """Pacote IP de exemplo para testes."""
    return {
        "src_ip": "192.168.1.100",
        "dst_ip": "10.0.0.1",
        "src_port": 54321,
        "dst_port": 80,
        "protocol": "TCP",
        "payload": b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n",
        "timestamp": 1698765432.123,
    }


@pytest.fixture
def sample_threat_signature() -> dict:
    """Assinatura de ameaça de exemplo."""
    return {
        "id": "SIG-001",
        "name": "SQL Injection Attempt",
        "pattern": r"(?i)(union.*select|select.*from|insert.*into|drop.*table)",
        "severity": "HIGH",
        "category": "injection",
        "cve_ids": ["CVE-2023-12345"],
    }


@pytest.fixture
def sample_langerhans_antigen() -> dict:
    """Antígeno capturado por Langerhans cell."""
    return {
        "id": "ant-12345",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.1",
        "protocol": "TCP",
        "port": 443,
        "payload_hash": "a1b2c3d4e5f6",
        "signatures_matched": ["SIG-001", "SIG-042"],
        "ml_anomaly_score": 0.87,
        "captured_at": "2025-10-28T10:30:00Z",
    }


@pytest.fixture
def sample_wound_healing_playbook() -> dict:
    """Playbook SOAR de exemplo."""
    return {
        "id": "playbook-block-ip",
        "name": "Block Malicious IP",
        "trigger": "high_severity_threat",
        "actions": [
            {"type": "firewall", "action": "block_ip", "duration": 3600},
            {"type": "alert", "channels": ["slack", "email"]},
            {"type": "log", "destination": "siem"},
        ],
    }


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================


@pytest.fixture
async def real_redis_client() -> AsyncGenerator:
    """
    Cliente Redis REAL para testes de integração.

    Requer Redis rodando em localhost:6379 ou REDIS_TEST_URL configurado.
    """
    import redis.asyncio as aioredis

    redis_url = os.getenv("REDIS_TEST_URL", "redis://localhost:6379/15")

    try:
        client = await aioredis.from_url(redis_url, decode_responses=True)
        await client.ping()

        yield client

        # Cleanup: flush test database
        await client.flushdb()
        await client.close()
    except Exception as e:
        pytest.skip(f"Redis não disponível: {e}")


@pytest.fixture
async def real_postgresql_pool() -> AsyncGenerator:
    """
    Connection pool PostgreSQL REAL para testes de integração.

    Requer PostgreSQL rodando ou POSTGRESQL_TEST_DSN configurado.
    """
    import asyncpg

    dsn = os.getenv(
        "POSTGRESQL_TEST_DSN",
        "postgresql://postgres:postgres@localhost:5432/tegumentar_test",
    )

    try:
        pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)

        # Setup: criar schema de teste
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS antigens (
                    id UUID PRIMARY KEY,
                    source_ip INET NOT NULL,
                    payload_hash TEXT NOT NULL,
                    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """
            )

        yield pool

        # Cleanup: dropar tabelas
        async with pool.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS antigens CASCADE")

        await pool.close()
    except Exception as e:
        pytest.skip(f"PostgreSQL não disponível: {e}")


# ============================================================================
# MARKERS
# ============================================================================

# Markers para categorizar testes
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.requires_root = pytest.mark.requires_root
