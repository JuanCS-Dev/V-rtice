"""Tests for vertice_api.health module."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from vertice_api.health import create_health_router


class TestHealthRouter:
    """Tests for health check router."""

    def test_health_endpoint_returns_200(self) -> None:
        """Test /health endpoint returns 200 when healthy."""
        app = FastAPI()
        router = create_health_router("test_service", "1.0.0")
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "test_service"
        assert data["version"] == "1.0.0"

    def test_health_with_healthy_dependencies(self) -> None:
        """Test health check with all dependencies healthy."""
        app = FastAPI()
        router = create_health_router(
            "test",
            "1.0.0",
            dependency_checks={"db": lambda: True, "cache": lambda: True},
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["dependencies"]["db"] == "healthy"
        assert data["dependencies"]["cache"] == "healthy"

    def test_health_with_unhealthy_dependency(self) -> None:
        """Test health check with unhealthy dependency."""
        app = FastAPI()
        router = create_health_router(
            "test",
            "1.0.0",
            dependency_checks={"db": lambda: False},
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["dependencies"]["db"] == "unhealthy"

    def test_health_with_failing_check(self) -> None:
        """Test health check when dependency check raises exception."""
        def failing_check() -> bool:
            raise RuntimeError("Connection failed")

        app = FastAPI()
        router = create_health_router(
            "test",
            "1.0.0",
            dependency_checks={"db": failing_check},
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["dependencies"]["db"] == "error"

    def test_readiness_endpoint(self) -> None:
        """Test /health/ready endpoint."""
        app = FastAPI()
        router = create_health_router(
            "test",
            "1.0.0",
            dependency_checks={"db": lambda: True},
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health/ready")

        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_readiness_not_ready(self) -> None:
        """Test /health/ready returns 503 when not ready."""
        app = FastAPI()
        router = create_health_router(
            "test",
            "1.0.0",
            dependency_checks={"db": lambda: False},
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health/ready")

        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"

    def test_liveness_endpoint(self) -> None:
        """Test /health/live endpoint."""
        app = FastAPI()
        router = create_health_router("test", "1.0.0")
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health/live")

        assert response.status_code == 200
        assert response.json()["status"] == "alive"
