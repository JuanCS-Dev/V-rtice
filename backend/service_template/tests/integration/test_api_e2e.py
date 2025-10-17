"""End-to-end API tests with real database."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from service_template.infrastructure.config import Settings
from service_template.infrastructure.database import Database
from service_template.main import app
from service_template.presentation.dependencies import get_database


@pytest.fixture
async def test_db() -> Database:
    """Create test database."""
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",

    )
    database = Database(settings.database_url)
    await database.create_tables()
    yield database
    await database.close()


@pytest.fixture
async def client(test_db: Database) -> AsyncClient:
    """Create test client with database override."""
    app.dependency_overrides[get_database] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.integration
class TestEntityAPIE2E:
    """End-to-end tests for entity API."""

    async def test_full_crud_lifecycle(self, client: AsyncClient) -> None:
        """Test complete CRUD lifecycle."""
        # CREATE
        create_response = await client.post(
            "/api/v1/entities/",
            json={"name": "E2E Test Entity", "description": "E2E Description"},
        )
        assert create_response.status_code == 201
        entity = create_response.json()
        entity_id = entity["id"]
        assert entity["name"] == "E2E Test Entity"

        # READ
        get_response = await client.get(f"/api/v1/entities/{entity_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["id"] == entity_id
        assert retrieved["name"] == "E2E Test Entity"

        # UPDATE
        update_response = await client.put(
            f"/api/v1/entities/{entity_id}",
            json={"name": "Updated Name", "description": "Updated Description"},
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Updated Name"
        assert updated["description"] == "Updated Description"

        # LIST
        list_response = await client.get("/api/v1/entities/")
        assert list_response.status_code == 200
        entities_list = list_response.json()
        assert entities_list["total"] >= 1
        assert any(e["id"] == entity_id for e in entities_list["items"])

        # DELETE
        delete_response = await client.delete(f"/api/v1/entities/{entity_id}")
        assert delete_response.status_code == 204

        # VERIFY DELETED
        get_deleted_response = await client.get(f"/api/v1/entities/{entity_id}")
        assert get_deleted_response.status_code == 404

    async def test_create_duplicate_name_fails(self, client: AsyncClient) -> None:
        """Test that creating duplicate names fails."""
        await client.post(
            "/api/v1/entities/",
            json={"name": "Unique Name", "description": "First"},
        )

        duplicate_response = await client.post(
            "/api/v1/entities/",
            json={"name": "Unique Name", "description": "Second"},
        )
        assert duplicate_response.status_code == 409

    async def test_pagination_works(self, client: AsyncClient) -> None:
        """Test pagination."""
        for i in range(15):
            await client.post(
                "/api/v1/entities/",
                json={"name": f"Entity {i}", "description": f"Desc {i}"},
            )

        page1_response = await client.get("/api/v1/entities/?limit=5&offset=0")
        page1 = page1_response.json()
        assert len(page1["items"]) == 5
        assert page1["limit"] == 5
        assert page1["offset"] == 0

        page2_response = await client.get("/api/v1/entities/?limit=5&offset=5")
        page2 = page2_response.json()
        assert len(page2["items"]) == 5
        assert page2["offset"] == 5

        page1_ids = {e["id"] for e in page1["items"]}
        page2_ids = {e["id"] for e in page2["items"]}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_get_nonexistent_entity_404(self, client: AsyncClient) -> None:
        """Test 404 for non-existent entity."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/entities/{fake_id}")
        assert response.status_code == 404

    async def test_update_nonexistent_entity_404(self, client: AsyncClient) -> None:
        """Test 404 when updating non-existent entity."""
        fake_id = str(uuid4())
        response = await client.put(
            f"/api/v1/entities/{fake_id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 404

    async def test_delete_nonexistent_entity_404(self, client: AsyncClient) -> None:
        """Test 404 when deleting non-existent entity."""
        fake_id = str(uuid4())
        response = await client.delete(f"/api/v1/entities/{fake_id}")
        assert response.status_code == 404

    async def test_validation_errors(self, client: AsyncClient) -> None:
        """Test validation errors."""
        # Name too short
        response = await client.post(
            "/api/v1/entities/",
            json={"name": "AB", "description": "Test"},
        )
        assert response.status_code == 422

        # Name too long
        response = await client.post(
            "/api/v1/entities/",
            json={"name": "A" * 101, "description": "Test"},
        )
        assert response.status_code == 422
