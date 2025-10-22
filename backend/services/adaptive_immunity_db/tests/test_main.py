"""
Testes para adaptive_immunity_db

OBJETIVO: 100% cobertura
ESTRATÉGIA: Service mínimo (57 lines) - testar todos os endpoints + lifespan
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestAdaptiveImmunityDB:
    """Testa adaptive_immunity_db endpoints."""

    def test_health(self):
        """Testa /health endpoint."""
        with TestClient(app) as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "adaptive_immunity_db"

    def test_root(self):
        """Testa / (root) endpoint."""
        with TestClient(app) as client:
            response = client.get("/")

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "adaptive_immunity_db"
            assert data["version"] == "0.1.0"
            assert data["status"] == "running"

    def test_lifespan_startup_shutdown(self, caplog):
        """Testa lifespan startup/shutdown (lines 15-19)."""
        import logging

        caplog.set_level(logging.INFO)

        # TestClient com context manager triggera lifespan
        with TestClient(app) as client:
            # Startup deve ter executado
            response = client.get("/health")
            assert response.status_code == 200

        # Verifica logs de startup/shutdown
        log_messages = [record.message for record in caplog.records]
        assert any("Starting adaptive_immunity_db" in msg for msg in log_messages)
        assert any("Shutting down adaptive_immunity_db" in msg for msg in log_messages)

    def test_cors_headers(self):
        """Testa CORS middleware (lines 28-35)."""
        with TestClient(app) as client:
            # OPTIONS preflight request
            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

            # CORS deve permitir
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
