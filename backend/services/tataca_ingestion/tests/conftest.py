"""Shared test fixtures for Tatacá Ingestion Service tests.

Following PAGANI Standard:
- Mock external dependencies (JobScheduler, PostgreSQL, Neo4j)
- DO NOT mock internal business logic
"""

import uuid
from datetime import datetime
from typing import Dict, List

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ============================================================================
# MOCK JOBSCHEDULER
# ============================================================================


class MockJobScheduler:
    """Mock JobScheduler for testing (mocks external ETL infrastructure)."""

    def __init__(self):
        self.jobs: Dict[str, "IngestJobStatus"] = {}
        self.running_jobs: set = set()
        self.initialized = False
        self.postgres_healthy = True
        self.neo4j_healthy = True

        # Mock loaders (checked by health endpoint)
        self.postgres_loader = MockPostgresLoader()
        self.neo4j_loader = MockNeo4jLoader()

    async def initialize(self):
        """Mock initialize."""
        self.initialized = True

    async def shutdown(self):
        """Mock shutdown."""
        self.initialized = False


class MockPostgresLoader:
    """Mock PostgresLoader."""

    async def check_health(self) -> bool:
        return True


class MockNeo4jLoader:
    """Mock Neo4jLoader."""

    async def check_health(self) -> bool:
        return True

    async def shutdown(self):
        """Mock shutdown."""
        self.initialized = False

    async def create_job(self, job_request: "IngestJobRequest") -> "IngestJobResponse":
        """Mock job creation."""
        from models import IngestJobResponse, IngestJobStatus, JobStatus

        job_id = str(uuid.uuid4())

        # Create job status
        job_status = IngestJobStatus(
            job_id=job_id,
            status=JobStatus.PENDING,
            data_source=job_request.data_source,
            entity_type=job_request.entity_type,
            created_at=datetime.utcnow(),
            progress=0,
        )

        self.jobs[job_id] = job_status

        return IngestJobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Job created successfully",
        )

    async def get_job_status(self, job_id: str) -> "IngestJobStatus":
        """Mock get job status."""
        if job_id not in self.jobs:
            return None
        return self.jobs[job_id]

    async def list_jobs(self, limit: int = 100, status: str = None) -> List["IngestJobStatus"]:
        """Mock list jobs."""
        jobs = list(self.jobs.values())

        # Filter by status if provided
        if status:
            from models import JobStatus

            try:
                status_enum = JobStatus(status)
                jobs = [j for j in jobs if j.status == status_enum]
            except ValueError:
                pass

        return jobs[:limit]

    async def delete_job(self, job_id: str) -> bool:
        """Mock delete job."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False

    async def check_health(self) -> Dict[str, bool]:
        """Mock health check."""
        return {
            "postgres_healthy": self.postgres_healthy,
            "neo4j_healthy": self.neo4j_healthy,
        }


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def client():
    """Provides an async HTTP client with mocked JobScheduler."""
    import api

    # Replace scheduler with mock
    mock_scheduler = MockJobScheduler()
    await mock_scheduler.initialize()

    original_scheduler = api.scheduler
    api.scheduler = mock_scheduler

    transport = ASGITransport(app=api.app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac

    # Cleanup
    api.scheduler = original_scheduler


# ============================================================================
# TEST DATA FACTORIES
# ============================================================================


@pytest.fixture
def create_job_request():
    """Factory for creating IngestJobRequest payloads."""

    def _create(
        data_source: str = "sinesp",
        entity_type: str = "vehicle",
        query_params: dict = None,
    ):
        """Create an IngestJobRequest payload."""

        return {
            "data_source": data_source,
            "entity_type": entity_type,
            "query_params": query_params or {"plate": "ABC1234"},
            "priority": "normal",
        }

    return _create
