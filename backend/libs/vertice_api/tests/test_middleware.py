"""Tests for vertice_api.middleware module."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from vertice_core import NotFoundError

from vertice_api.middleware import ErrorHandlingMiddleware


class TestErrorHandlingMiddleware:
    """Tests for ErrorHandlingMiddleware."""

    def test_converts_vertice_exception(self) -> None:
        """Test that VerticeException is converted to JSON."""
        app = FastAPI()
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/test")
        def test_endpoint() -> None:
            raise NotFoundError("User", 123)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "NotFoundError"
        assert "User not found" in data["message"]

    def test_converts_generic_exception(self) -> None:
        """Test that generic Exception is converted to 500."""
        app = FastAPI()
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/test")
        def test_endpoint() -> None:
            raise RuntimeError("Something broke")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "InternalServerError"
