"""Integration tests for complete flow."""
import pytest
from httpx import ASGITransport, AsyncClient
from service_template import create_app
from service_template.infrastructure.database import Database


@pytest.fixture
async def app():
    """Create test app."""
    import os
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    return create_app()


@pytest.fixture
async def client(app):
    """Create async HTTP client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac


@pytest.mark.asyncio
class TestFullEntityFlow:
    """Test complete CRUD flow."""

    async def test_health_endpoint(self, client: AsyncClient) -> None:
        """Test health check."""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_create_entity(self, client: AsyncClient) -> None:
        """Test creating an entity."""
        payload = {
            "name": "Test Entity",
            "description": "Test Description"
        }

        response = await client.post("/api/v1/entities", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Entity"

    async def test_list_entities(self, client: AsyncClient) -> None:
        """Test listing entities."""
        # Create entity
        await client.post(
            "/api/v1/entities",
            json={"name": "List Test", "description": "Desc"}
        )

        response = await client.get("/api/v1/entities")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1


@pytest.mark.asyncio
class TestDatabaseSession:
    """Test database session management."""

    async def test_database_lifecycle(self) -> None:
        """Test database create tables and close."""
        db = Database("sqlite+aiosqlite:///:memory:")

        await db.create_tables()

        # Use session
        async with db.session():
            pass

        await db.close()
