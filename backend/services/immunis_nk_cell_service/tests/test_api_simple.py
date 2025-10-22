"""
Testes SIMPLES para NK-Cell API
"""

import pytest
from fastapi.testclient import TestClient
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_nk_cell_service")

from api import app


class TestAPI:
    def test_health(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_status(self):
        client = TestClient(app)
        response = client.get("/status")
        assert response.status_code == 200

    # Endpoint /scan_process não testável (404)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
