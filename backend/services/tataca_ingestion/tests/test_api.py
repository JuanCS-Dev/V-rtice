"""Tests for Tatacá Ingestion Service API endpoints.

Tests all 9 API endpoints with mocked external dependencies (PAGANI Standard).

Endpoints tested:
- GET /health
- POST /jobs (create job)
- GET /jobs/{job_id} (get job status)
- GET /jobs (list jobs)
- POST /ingest/trigger (quick trigger)
- GET /sources (list data sources)
- GET /entities (list entities)
- GET /stats (statistics)
- DELETE /jobs/{job_id} (delete job)
"""

import pytest

# ============================================================================
# HEALTH ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_check_all_healthy(self, client):
        """Test health check when all dependencies are healthy."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "Tatacá Ingestion Service"
        assert data["postgres_healthy"] is True
        assert data["neo4j_healthy"] is True
        assert "active_jobs" in data

    async def test_health_check_includes_version(self, client):
        """Test health check includes version."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "version" in data


# ============================================================================
# JOB CREATION ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestJobCreation:
    """Test job creation endpoint."""

    async def test_create_job_success(self, client, create_job_request):
        """Test successful job creation."""
        payload = create_job_request()

        response = await client.post("/jobs", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert data["status"] == "pending"
        assert "message" in data

    async def test_create_job_with_different_sources(self, client, create_job_request):
        """Test job creation with different data sources."""
        # Test SINESP source
        payload = create_job_request(data_source="sinesp")
        response = await client.post("/jobs", json=payload)
        assert response.status_code == 200

    async def test_create_job_with_different_entities(self, client, create_job_request):
        """Test job creation with different entity types."""
        # Test vehicle entity
        payload = create_job_request(entity_type="vehicle")
        response = await client.post("/jobs", json=payload)
        assert response.status_code == 200

        # Test person entity
        payload = create_job_request(entity_type="person")
        response = await client.post("/jobs", json=payload)
        assert response.status_code == 200

    async def test_create_job_missing_required_fields(self, client):
        """Test job creation with missing required fields."""
        response = await client.post("/jobs", json={})

        assert response.status_code == 422  # Pydantic validation error


# ============================================================================
# JOB STATUS ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestJobStatus:
    """Test job status retrieval endpoint."""

    async def test_get_job_status_success(self, client, create_job_request):
        """Test retrieving job status."""
        # Create a job first
        payload = create_job_request()
        create_response = await client.post("/jobs", json=payload)
        job_id = create_response.json()["job_id"]

        # Get job status
        response = await client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == job_id
        assert "status" in data
        assert "created_at" in data
        assert "progress" in data

    async def test_get_job_status_not_found(self, client):
        """Test getting status for non-existent job."""
        fake_job_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/jobs/{fake_job_id}")

        assert response.status_code == 404


# ============================================================================
# JOB LISTING ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestJobListing:
    """Test job listing endpoint."""

    async def test_list_jobs_empty(self, client):
        """Test listing jobs when no jobs exist."""
        response = await client.get("/jobs")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_jobs_with_jobs(self, client, create_job_request):
        """Test listing jobs when jobs exist."""
        # Create multiple jobs
        for i in range(3):
            payload = create_job_request()
            await client.post("/jobs", json=payload)

        # List jobs
        response = await client.get("/jobs")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 3

    async def test_list_jobs_with_limit(self, client, create_job_request):
        """Test listing jobs with limit parameter."""
        # Create 5 jobs
        for i in range(5):
            payload = create_job_request()
            await client.post("/jobs", json=payload)

        # List with limit=2
        response = await client.get("/jobs?limit=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2

    async def test_list_jobs_with_status_filter(self, client, create_job_request):
        """Test listing jobs with status filter."""
        # Create a job
        payload = create_job_request()
        await client.post("/jobs", json=payload)

        # List pending jobs
        response = await client.get("/jobs?status=pending")

        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1
        for job in data:
            assert job["status"] == "pending"


# ============================================================================
# QUICK TRIGGER ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestQuickTrigger:
    """Test quick ingestion trigger endpoint."""

    async def test_trigger_ingest_success(self, client):
        """Test quick trigger ingestion."""
        payload = {
            "data_source": "sinesp",
            "entity_type": "vehicle",
            "query_params": {"plate": "XYZ5678"},
        }

        response = await client.post("/ingest/trigger", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert data["status"] == "pending"


# ============================================================================
# DATA SOURCES ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestDataSources:
    """Test data sources listing endpoint."""

    async def test_list_sources(self, client):
        """Test listing available data sources."""
        response = await client.get("/sources")

        assert response.status_code == 200
        data = response.json()

        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0

    async def test_sources_have_required_fields(self, client):
        """Test that sources have required fields."""
        response = await client.get("/sources")
        data = response.json()

        for source in data["sources"]:
            assert "name" in source
            assert "description" in source
            assert "available" in source


# ============================================================================
# ENTITIES ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestEntities:
    """Test entities listing endpoint."""

    async def test_list_entities(self, client):
        """Test listing available entity types."""
        response = await client.get("/entities")

        assert response.status_code == 200
        data = response.json()

        assert "entities" in data
        assert isinstance(data["entities"], list)
        assert len(data["entities"]) > 0

    async def test_entities_have_required_fields(self, client):
        """Test that entities have required fields."""
        response = await client.get("/entities")
        data = response.json()

        for entity in data["entities"]:
            assert "name" in entity
            assert "description" in entity
            assert "fields" in entity


# ============================================================================
# STATISTICS ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestStatistics:
    """Test statistics endpoint."""

    async def test_get_stats(self, client):
        """Test getting ingestion statistics."""
        response = await client.get("/stats")

        assert response.status_code == 200
        data = response.json()

        assert "total_jobs" in data
        assert "active_jobs" in data
        assert "completed_jobs" in data
        assert "failed_jobs" in data

    async def test_stats_after_job_creation(self, client, create_job_request):
        """Test stats update after creating jobs."""
        # Get initial stats
        initial_response = await client.get("/stats")
        initial_total = initial_response.json()["total_jobs"]

        # Create a job
        payload = create_job_request()
        await client.post("/jobs", json=payload)

        # Get updated stats
        updated_response = await client.get("/stats")
        updated_total = updated_response.json()["total_jobs"]

        assert updated_total == initial_total + 1


# ============================================================================
# JOB DELETION ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestJobDeletion:
    """Test job deletion endpoint."""

    async def test_delete_job_success(self, client, create_job_request):
        """Test successful job deletion."""
        # Create a job
        payload = create_job_request()
        create_response = await client.post("/jobs", json=payload)
        job_id = create_response.json()["job_id"]

        # Delete the job
        response = await client.delete(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data

        # Verify job no longer exists
        get_response = await client.get(f"/jobs/{job_id}")
        assert get_response.status_code == 404

    async def test_delete_job_not_found(self, client):
        """Test deleting non-existent job."""
        fake_job_id = "00000000-0000-0000-0000-000000000000"

        response = await client.delete(f"/jobs/{fake_job_id}")

        assert response.status_code == 404


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error handling."""

    async def test_invalid_job_id_format(self, client):
        """Test invalid job ID format."""
        response = await client.get("/jobs/invalid-uuid-format")

        # Should return 422 (validation error) or 404
        assert response.status_code in [404, 422]

    async def test_invalid_limit_parameter(self, client):
        """Test invalid limit parameter."""
        response = await client.get("/jobs?limit=-1")

        assert response.status_code == 422

    async def test_invalid_status_parameter(self, client):
        """Test invalid status filter."""
        # Should handle gracefully (return empty or all jobs)
        response = await client.get("/jobs?status=invalid_status")

        assert response.status_code == 200
