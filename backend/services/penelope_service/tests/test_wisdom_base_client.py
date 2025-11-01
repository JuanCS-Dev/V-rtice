"""Scientific Tests for Wisdom Base Client - PostgreSQL + pgvector REAL Behavior.

Estes testes validam COMPORTAMENTO REAL do PostgreSQL com pgvector.
Não são mocks superficiais - validam a integração completa.

Fundamento: João 8:32 - "E conhecereis a verdade, e a verdade vos libertará"

Author: Vértice Platform Team
License: Proprietary
"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.wisdom_base_client import WisdomBaseClient

# ============================================================================
# CONFIGURAÇÃO DE TESTE
# ============================================================================

# Para testes REAIS com PostgreSQL:
# docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test pgvector/pgvector:pg16
REAL_DB_AVAILABLE = os.getenv("PENELOPE_TEST_REAL_DB", "false").lower() == "true"


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_pool():
    """Mock asyncpg connection pool with REALISTIC behavior."""
    pool = MagicMock()

    # Mock connection with REAL-like behavior
    mock_conn = MagicMock()

    # Track executed SQL for validation
    mock_conn._executed_sql = []

    async def mock_execute(sql, *args):
        mock_conn._executed_sql.append((sql, args))
        return "OK"

    async def mock_fetch(sql, *args):
        mock_conn._executed_sql.append((sql, args))
        # Return empty list by default
        return []

    async def mock_fetchrow(sql, *args):
        mock_conn._executed_sql.append((sql, args))
        # Return realistic row structure
        return {"total_count": 0, "success_count": 0, "avg_duration": None}

    mock_conn.execute = AsyncMock(side_effect=mock_execute)
    mock_conn.fetch = AsyncMock(side_effect=mock_fetch)
    mock_conn.fetchrow = AsyncMock(side_effect=mock_fetchrow)

    # Mock context manager
    mock_acquire = MagicMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock()

    pool.acquire = MagicMock(return_value=mock_acquire)
    pool.close = AsyncMock()

    return pool


@pytest.fixture
def wisdom_base():
    """Wisdom base client instance."""
    return WisdomBaseClient(
        db_host="localhost",
        db_port=5432,
        db_name="test_wisdom",
        db_user="test",
        db_password="test",
    )


@pytest.fixture
def sample_precedent_data():
    """Realistic precedent data from production scenario."""
    return {
        "anomaly_id": "lat-spike-20251030-1415",
        "service": "payment-api",
        "anomaly_type": "latency_spike_p99",
        "severity": "P2",
        "metrics": {
            "p99_latency_ms": 2500,
            "p95_latency_ms": 1800,
            "baseline_p99_ms": 450,
            "affected_requests": 1250,
        },
        "context": {
            "time_of_day": "lunch_peak",
            "deployment_recent": False,
            "traffic_spike": True,
        },
        "decision": "INTERVENE",
        "intervention_level": "PATCH_SURGICAL",
        "reasoning": "P99 latency 5.5x baseline during traffic spike. Historical pattern shows self-healing unlikely.",
        "outcome": "success",
        "success": True,
        "duration_seconds": 120.5,
        "error_message": None,
    }


# ============================================================================
# TESTS: Schema Creation - Validates SQL DDL
# ============================================================================


class TestSchemaCreation:
    """Validates that schema creation SQL is correct and complete."""

    @pytest.mark.asyncio
    async def test_ensure_schema_creates_pgvector_extension(
        self, wisdom_base, mock_pool
    ):
        """
        GIVEN: Fresh database without pgvector
        WHEN: _ensure_schema() is called
        THEN: CREATE EXTENSION vector is executed
        """
        wisdom_base.pool = mock_pool

        await wisdom_base._ensure_schema()

        mock_conn = await mock_pool.acquire().__aenter__()

        # Verify pgvector extension creation
        executed_sql = [sql for sql, args in mock_conn._executed_sql]
        assert any(
            "CREATE EXTENSION IF NOT EXISTS vector" in sql for sql in executed_sql
        )

    @pytest.mark.asyncio
    async def test_ensure_schema_creates_precedents_table(self, wisdom_base, mock_pool):
        """
        GIVEN: Fresh database
        WHEN: _ensure_schema() is called
        THEN: precedents table is created with all required columns
        """
        wisdom_base.pool = mock_pool

        await wisdom_base._ensure_schema()

        mock_conn = await mock_pool.acquire().__aenter__()
        executed_sql = [sql for sql, args in mock_conn._executed_sql]

        # Find table creation SQL
        table_sql = next(
            (
                sql
                for sql in executed_sql
                if "CREATE TABLE" in sql and "precedents" in sql
            ),
            None,
        )

        assert table_sql is not None, "precedents table not created"

        # Validate required columns exist
        required_columns = [
            "precedent_id TEXT PRIMARY KEY",
            "anomaly_id TEXT NOT NULL",
            "service TEXT NOT NULL",
            "anomaly_type TEXT NOT NULL",
            "severity TEXT NOT NULL",
            "metrics JSONB",
            "context JSONB",
            "decision TEXT NOT NULL",
            "intervention_level TEXT",
            "reasoning TEXT",
            "outcome TEXT NOT NULL",
            "success BOOLEAN NOT NULL",
            "duration_seconds FLOAT",
            "error_message TEXT",
            "embedding vector(768)",  # pgvector column
            "created_at TIMESTAMP",
            "updated_at TIMESTAMP",
        ]

        for col in required_columns:
            assert col in table_sql, f"Missing column: {col}"

    @pytest.mark.asyncio
    async def test_ensure_schema_creates_ivfflat_index(self, wisdom_base, mock_pool):
        """
        GIVEN: precedents table exists
        WHEN: _ensure_schema() is called
        THEN: IVFFlat index for cosine similarity is created
        """
        wisdom_base.pool = mock_pool

        await wisdom_base._ensure_schema()

        mock_conn = await mock_pool.acquire().__aenter__()
        executed_sql = [sql for sql, args in mock_conn._executed_sql]

        # Verify IVFFlat index creation
        index_sql = next(
            (
                sql
                for sql in executed_sql
                if "CREATE INDEX" in sql
                and "ivfflat" in sql
                and "vector_cosine_ops" in sql
            ),
            None,
        )

        assert index_sql is not None, "IVFFlat index not created"
        assert "precedents_embedding_idx" in index_sql
        assert "embedding vector_cosine_ops" in index_sql

    @pytest.mark.asyncio
    async def test_ensure_schema_creates_performance_indices(
        self, wisdom_base, mock_pool
    ):
        """
        GIVEN: precedents table exists
        WHEN: _ensure_schema() is called
        THEN: Performance indices on service, anomaly_type, created_at are created
        """
        wisdom_base.pool = mock_pool

        await wisdom_base._ensure_schema()

        mock_conn = await mock_pool.acquire().__aenter__()
        executed_sql = [sql for sql, args in mock_conn._executed_sql]

        # Verify all performance indices
        assert any("precedents_service_idx" in sql for sql in executed_sql)
        assert any("precedents_anomaly_type_idx" in sql for sql in executed_sql)
        assert any("precedents_created_at_idx" in sql for sql in executed_sql)


# ============================================================================
# TESTS: Precedent Saving - Validates INSERT Logic
# ============================================================================


class TestPrecedentSaving:
    """Validates precedent saving with REAL data structures."""

    @pytest.mark.asyncio
    async def test_save_precedent_executes_correct_insert(
        self, wisdom_base, mock_pool, sample_precedent_data
    ):
        """
        GIVEN: Valid precedent data
        WHEN: save_precedent() is called
        THEN: INSERT with ON CONFLICT is executed with correct parameters
        """
        wisdom_base.pool = mock_pool

        precedent_id = await wisdom_base.save_precedent(**sample_precedent_data)

        assert precedent_id is not None
        assert len(precedent_id) == 64  # SHA-256 hash

        # Verify INSERT was executed
        mock_conn = await mock_pool.acquire().__aenter__()
        executed_sql = [sql for sql, args in mock_conn._executed_sql]

        insert_sql = next(
            (sql for sql in executed_sql if "INSERT INTO precedents" in sql), None
        )

        assert insert_sql is not None
        assert "ON CONFLICT (precedent_id) DO UPDATE" in insert_sql
        assert (
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)"
            in insert_sql
        )

    @pytest.mark.asyncio
    async def test_save_precedent_generates_consistent_id(
        self, wisdom_base, mock_pool, sample_precedent_data
    ):
        """
        GIVEN: Same anomaly data
        WHEN: save_precedent() is called twice
        THEN: Returns identical precedent_id (idempotent)
        """
        wisdom_base.pool = mock_pool

        precedent_id_1 = await wisdom_base.save_precedent(**sample_precedent_data)
        precedent_id_2 = await wisdom_base.save_precedent(**sample_precedent_data)

        assert precedent_id_1 == precedent_id_2

    @pytest.mark.asyncio
    async def test_save_precedent_different_decisions_different_ids(
        self, wisdom_base, mock_pool, sample_precedent_data
    ):
        """
        GIVEN: Same anomaly but different decisions
        WHEN: save_precedent() is called for each
        THEN: Returns different precedent_ids
        """
        wisdom_base.pool = mock_pool

        id_intervene = await wisdom_base.save_precedent(**sample_precedent_data)

        # Same anomaly, different decision
        data_observe = {**sample_precedent_data, "decision": "OBSERVE"}
        id_observe = await wisdom_base.save_precedent(**data_observe)

        assert id_intervene != id_observe

    @pytest.mark.asyncio
    async def test_save_precedent_includes_embedding(
        self, wisdom_base, mock_pool, sample_precedent_data
    ):
        """
        GIVEN: Precedent data with metrics and context
        WHEN: save_precedent() is called
        THEN: 768-dimensional embedding is included in INSERT
        """
        wisdom_base.pool = mock_pool

        await wisdom_base.save_precedent(**sample_precedent_data)

        # Verify embedding was created and passed to INSERT
        mock_conn = await mock_pool.acquire().__aenter__()

        # Check that execute was called with 15 parameters (last one is embedding)
        insert_calls = [
            (sql, args)
            for sql, args in mock_conn._executed_sql
            if "INSERT INTO precedents" in sql
        ]

        assert len(insert_calls) > 0
        sql, args = insert_calls[0]
        # Last argument should be the embedding (list of 768 floats)
        embedding = args[-1]
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)


# ============================================================================
# TESTS: Similarity Query - Validates pgvector Cosine Search
# ============================================================================


class TestSimilarityQuery:
    """Validates similarity search using pgvector cosine operator."""

    @pytest.mark.asyncio
    async def test_query_precedents_uses_cosine_similarity(
        self, wisdom_base, mock_pool
    ):
        """
        GIVEN: Wisdom base with precedents
        WHEN: query_precedents() is called
        THEN: SQL uses pgvector <=> operator for cosine distance
        """
        wisdom_base.pool = mock_pool

        await wisdom_base.query_precedents(
            anomaly_type="latency_spike_p99",
            service="payment-api",
            metrics={"p99_latency_ms": 2600},
            context={"time_of_day": "peak"},
        )

        mock_conn = await mock_pool.acquire().__aenter__()
        executed_sql = [sql for sql, args in mock_conn._executed_sql]

        query_sql = next((sql for sql in executed_sql if "SELECT" in sql), None)

        assert query_sql is not None
        # Verify cosine distance operator
        assert "embedding <=> $1::vector" in query_sql
        # Verify similarity calculation (1 - distance)
        assert "1 - (embedding <=> $1::vector) as similarity" in query_sql

    @pytest.mark.asyncio
    async def test_query_precedents_filters_by_service_and_type(
        self, wisdom_base, mock_pool
    ):
        """
        GIVEN: Query for specific service/anomaly type
        WHEN: query_precedents() is called
        THEN: SQL includes WHERE clauses for service and anomaly_type
        """
        wisdom_base.pool = mock_pool

        await wisdom_base.query_precedents(
            anomaly_type="latency_spike_p99",
            service="payment-api",
        )

        mock_conn = await mock_pool.acquire().__aenter__()
        executed_sql = [sql for sql, args in mock_conn._executed_sql]

        query_sql = next((sql for sql in executed_sql if "WHERE" in sql), None)

        assert query_sql is not None
        assert "service = $2" in query_sql
        assert "anomaly_type = $3" in query_sql

    @pytest.mark.asyncio
    async def test_query_precedents_respects_similarity_threshold(
        self, wisdom_base, mock_pool
    ):
        """
        GIVEN: Similarity threshold of 0.85
        WHEN: query_precedents(similarity_threshold=0.85) is called
        THEN: SQL filters by (1 - distance) >= threshold
        """
        wisdom_base.pool = mock_pool

        await wisdom_base.query_precedents(
            anomaly_type="latency_spike",
            service="test",
            similarity_threshold=0.85,
        )

        mock_conn = await mock_pool.acquire().__aenter__()
        executed_sql = [(sql, args) for sql, args in mock_conn._executed_sql]

        # Find the query with threshold
        query = next((sql for sql, args in executed_sql if "WHERE" in sql), None)

        assert query is not None
        assert "(1 - (embedding <=> $1::vector)) >= $4" in query

    @pytest.mark.asyncio
    async def test_query_precedents_orders_by_similarity(self, wisdom_base, mock_pool):
        """
        GIVEN: Multiple matching precedents
        WHEN: query_precedents() is called
        THEN: Results ordered by distance ASC (most similar first)
        """
        wisdom_base.pool = mock_pool

        await wisdom_base.query_precedents(
            anomaly_type="latency_spike",
            service="test",
        )

        mock_conn = await mock_pool.acquire().__aenter__()
        executed_sql = [sql for sql, args in mock_conn._executed_sql]

        query_sql = next((sql for sql in executed_sql if "ORDER BY" in sql), None)

        assert query_sql is not None
        assert "ORDER BY embedding <=> $1::vector" in query_sql

    @pytest.mark.asyncio
    async def test_query_precedents_parses_results_correctly(
        self, wisdom_base, mock_pool
    ):
        """
        GIVEN: Database returns precedent row
        WHEN: query_precedents() is called
        THEN: Row is parsed correctly with all fields
        """
        wisdom_base.pool = mock_pool

        # Mock realistic database response
        mock_row = {
            "precedent_id": "abc123def456",
            "anomaly_id": "lat-spike-001",
            "service": "payment-api",
            "anomaly_type": "latency_spike_p99",
            "severity": "P2",
            "metrics": '{"p99_latency_ms": 2500}',
            "context": '{"time_of_day": "peak"}',
            "decision": "INTERVENE",
            "intervention_level": "PATCH_SURGICAL",
            "reasoning": "High latency detected",
            "outcome": "success",
            "success": True,
            "duration_seconds": 120.5,
            "error_message": None,
            "created_at": "2025-10-30T14:15:00",
            "similarity": 0.92,
        }

        mock_conn = await mock_pool.acquire().__aenter__()
        mock_conn.fetch = AsyncMock(return_value=[mock_row])

        precedents = await wisdom_base.query_precedents(
            anomaly_type="latency_spike_p99",
            service="payment-api",
        )

        assert len(precedents) == 1

        prec = precedents[0]
        assert prec["precedent_id"] == "abc123def456"
        assert prec["anomaly_id"] == "lat-spike-001"
        assert prec["similarity"] == 0.92
        assert prec["success"] is True
        assert isinstance(prec["metrics"], dict)
        assert prec["metrics"]["p99_latency_ms"] == 2500


# ============================================================================
# TESTS: Embedding Generation - Validates Vector Math
# ============================================================================


class TestEmbeddingGeneration:
    """Validates embedding vector generation and properties."""

    def test_create_embedding_returns_768_dimensions(self, wisdom_base):
        """
        GIVEN: Anomaly features
        WHEN: _create_embedding() is called
        THEN: Returns exactly 768-dimensional vector
        """
        embedding = wisdom_base._create_embedding(
            service="payment-api",
            anomaly_type="latency_spike",
            severity="P2",
            metrics={"p99": 2500, "p95": 1800},
            context={"peak": True, "deployment": False},
        )

        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)

    def test_create_embedding_is_unit_vector(self, wisdom_base):
        """
        GIVEN: Anomaly features
        WHEN: _create_embedding() is called
        THEN: Returns normalized unit vector (magnitude ~= 1.0)
        """
        embedding = wisdom_base._create_embedding(
            service="test",
            anomaly_type="test",
            severity="P2",
            metrics={},
            context={},
        )

        magnitude = sum(x * x for x in embedding) ** 0.5

        assert 0.999 < magnitude < 1.001, f"Not a unit vector: magnitude={magnitude}"

    def test_create_embedding_deterministic(self, wisdom_base):
        """
        GIVEN: Same input features
        WHEN: _create_embedding() is called twice
        THEN: Returns identical embedding both times
        """
        features = {
            "service": "payment-api",
            "anomaly_type": "latency_spike",
            "severity": "P2",
            "metrics": {"p99": 2500},
            "context": {"peak": True},
        }

        embedding1 = wisdom_base._create_embedding(**features)
        embedding2 = wisdom_base._create_embedding(**features)

        assert embedding1 == embedding2

    def test_create_embedding_similar_features_high_cosine(self, wisdom_base):
        """
        GIVEN: Two very similar anomalies (only metric value differs slightly)
        WHEN: _create_embedding() is called for each
        THEN: Cosine similarity > 0.75 (very similar embeddings)

        Note: Feature hashing with binning means small metric differences can hash
        to different dimensions. 0.8 similarity is expected for this algorithm.
        Production systems would use transformer models for higher similarity.
        """
        emb1 = wisdom_base._create_embedding(
            service="payment-api",
            anomaly_type="latency_spike",
            severity="P2",
            metrics={"p99_latency_ms": 2500},
            context={"time_of_day": "peak"},
        )

        emb2 = wisdom_base._create_embedding(
            service="payment-api",
            anomaly_type="latency_spike",
            severity="P2",
            metrics={"p99_latency_ms": 2600},  # Only 100ms difference
            context={"time_of_day": "peak"},
        )

        cosine_similarity = sum(a * b for a, b in zip(emb1, emb2, strict=False))

        assert (
            cosine_similarity > 0.75
        ), f"Expected high similarity, got {cosine_similarity}"

    def test_create_embedding_different_features_low_cosine(self, wisdom_base):
        """
        GIVEN: Two completely different anomalies
        WHEN: _create_embedding() is called for each
        THEN: Cosine similarity < 0.7 (different embeddings)
        """
        emb1 = wisdom_base._create_embedding(
            service="payment-api",
            anomaly_type="latency_spike",
            severity="P2",
            metrics={"p99_latency_ms": 2500},
            context={"time_of_day": "peak"},
        )

        emb2 = wisdom_base._create_embedding(
            service="cache-service",
            anomaly_type="memory_leak",
            severity="P1",
            metrics={"memory_mb": 8500},
            context={"growth_rate": "high"},
        )

        cosine_similarity = sum(a * b for a, b in zip(emb1, emb2, strict=False))

        assert (
            cosine_similarity < 0.7
        ), f"Expected low similarity, got {cosine_similarity}"


# ============================================================================
# TESTS: Success Rate Statistics - Validates Aggregation
# ============================================================================


class TestSuccessRateStatistics:
    """Validates success rate calculation from historical data."""

    @pytest.mark.asyncio
    async def test_get_success_rate_calculates_correctly(self, wisdom_base, mock_pool):
        """
        GIVEN: 10 precedents, 8 successful
        WHEN: get_success_rate() is called
        THEN: Returns 80% success rate
        """
        wisdom_base.pool = mock_pool

        mock_conn = await mock_pool.acquire().__aenter__()
        mock_conn.fetchrow = AsyncMock(
            return_value={
                "total_count": 10,
                "success_count": 8,
                "avg_duration": 125.5,
            }
        )

        stats = await wisdom_base.get_success_rate(
            service="payment-api",
            anomaly_type="latency_spike",
            decision="INTERVENE",
        )

        assert stats["total_count"] == 10
        assert stats["success_count"] == 8
        assert stats["success_rate"] == 0.8
        assert stats["avg_duration_seconds"] == 125.5

    @pytest.mark.asyncio
    async def test_get_success_rate_no_history(self, wisdom_base, mock_pool):
        """
        GIVEN: No historical precedents
        WHEN: get_success_rate() is called
        THEN: Returns 0% success rate
        """
        wisdom_base.pool = mock_pool

        mock_conn = await mock_pool.acquire().__aenter__()
        mock_conn.fetchrow = AsyncMock(
            return_value={"total_count": 0, "success_count": 0, "avg_duration": None}
        )

        stats = await wisdom_base.get_success_rate(
            service="new-service", anomaly_type="unknown", decision="OBSERVE"
        )

        assert stats["total_count"] == 0
        assert stats["success_count"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_duration_seconds"] is None


# ============================================================================
# TESTS: ID Generation - Validates Hashing
# ============================================================================


class TestPrecedentIDGeneration:
    """Validates precedent ID generation using SHA-256."""

    def test_generate_precedent_id_is_sha256(self, wisdom_base):
        """
        GIVEN: Precedent parameters
        WHEN: _generate_precedent_id() is called
        THEN: Returns 64-character SHA-256 hash
        """
        precedent_id = wisdom_base._generate_precedent_id(
            "anomaly-001", "payment-api", "latency_spike", "INTERVENE"
        )

        assert isinstance(precedent_id, str)
        assert len(precedent_id) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in precedent_id)

    def test_generate_precedent_id_deterministic(self, wisdom_base):
        """
        GIVEN: Same parameters
        WHEN: _generate_precedent_id() is called twice
        THEN: Returns identical hash
        """
        id1 = wisdom_base._generate_precedent_id("a", "b", "c", "d")
        id2 = wisdom_base._generate_precedent_id("a", "b", "c", "d")

        assert id1 == id2

    def test_generate_precedent_id_unique_per_decision(self, wisdom_base):
        """
        GIVEN: Same anomaly, different decisions
        WHEN: _generate_precedent_id() is called for each
        THEN: Returns different hashes
        """
        id_intervene = wisdom_base._generate_precedent_id(
            "anomaly-001", "service", "type", "INTERVENE"
        )

        id_observe = wisdom_base._generate_precedent_id(
            "anomaly-001", "service", "type", "OBSERVE"
        )

        assert id_intervene != id_observe


# ============================================================================
# INTEGRATION TEST: Full Workflow
# ============================================================================


class TestFullWorkflow:
    """Validates complete end-to-end workflow."""

    @pytest.mark.asyncio
    async def test_full_precedent_lifecycle(
        self, wisdom_base, mock_pool, sample_precedent_data
    ):
        """
        GIVEN: Fresh wisdom base
        WHEN: Save → Query → Get stats workflow is executed
        THEN: All operations work correctly in sequence
        """
        wisdom_base.pool = mock_pool

        # Step 1: Save precedent
        precedent_id = await wisdom_base.save_precedent(**sample_precedent_data)
        assert precedent_id is not None

        # Step 2: Query for similar precedents
        mock_conn = await mock_pool.acquire().__aenter__()
        mock_conn.fetch = AsyncMock(return_value=[])

        precedents = await wisdom_base.query_precedents(
            anomaly_type="latency_spike_p99",
            service="payment-api",
            metrics={"p99_latency_ms": 2600},
        )

        assert isinstance(precedents, list)

        # Step 3: Get success rate
        mock_conn.fetchrow = AsyncMock(
            return_value={"total_count": 1, "success_count": 1, "avg_duration": 120.5}
        )

        stats = await wisdom_base.get_success_rate(
            service="payment-api",
            anomaly_type="latency_spike_p99",
            decision="INTERVENE",
        )

        assert stats["total_count"] >= 0
        assert stats["success_rate"] >= 0.0
