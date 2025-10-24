"""
Tests for vuln_scanner_service - API Endpoints

OBJETIVO: 100% COBERTURA ABSOLUTA da API
- Testa todos os endpoints HTTP
- Testa CRUD operations para scans
- Testa background scan execution
- ZERO MOCKS desnecessários

Padrão Pagani Absoluto: Cada endpoint, cada response code testado.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestHealthEndpoint:
    """Testes do endpoint /health."""

    async def test_health_endpoint(self, client):
        """Testa /health retorna informações básicas."""
        response = await client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "Vulnerability Scanner" in data["message"]


class TestCreateScanTask:
    """Testes do endpoint POST /scans/."""

    async def test_create_scan_task_success(self, client):
        """Testa criação de scan task com dados válidos."""
        scan_request = {
            "target": "192.168.1.1",
            "scan_type": "nmap_network",
            "parameters": {"ports": [80, 443]}
        }

        with patch("main.asyncio.create_task") as mock_task:
            response = await client.post("/scans/", json=scan_request)

            assert response.status_code == 200

            data = response.json()
            assert data["target"] == "192.168.1.1"
            assert data["scan_type"] == "nmap_network"
            assert data["status"] == "pending"
            assert "id" in data
            assert "start_time" in data

            # Verify background task was created
            mock_task.assert_called_once()

    async def test_create_scan_task_web_application(self, client):
        """Testa criação de scan task web application."""
        scan_request = {
            "target": "https://example.com",
            "scan_type": "web_application",
            "parameters": {"depth": 2}
        }

        with patch("main.asyncio.create_task"):
            response = await client.post("/scans/", json=scan_request)

            assert response.status_code == 200
            data = response.json()
            assert data["scan_type"] == "web_application"

    async def test_create_scan_task_invalid_data(self, client):
        """Testa criação de scan task com dados inválidos."""
        # Missing required fields
        response = await client.post("/scans/", json={})

        assert response.status_code == 422  # Unprocessable Entity


class TestReadScanTasks:
    """Testes do endpoint GET /scans/."""

    async def test_read_scan_tasks_empty(self, client):
        """Testa listagem de scans quando não há nenhum."""
        response = await client.get("/scans/")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_read_scan_tasks_with_scans(self, client):
        """Testa listagem de scans após criar alguns."""
        # Create two scan tasks
        scan1 = {"target": "192.168.1.1", "scan_type": "nmap_network", "parameters": {}}
        scan2 = {"target": "192.168.1.2", "scan_type": "nmap_network", "parameters": {}}

        with patch("main.asyncio.create_task"):
            await client.post("/scans/", json=scan1)
            await client.post("/scans/", json=scan2)

        response = await client.get("/scans/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["target"] == "192.168.1.1"
        assert data[1]["target"] == "192.168.1.2"

    async def test_read_scan_tasks_pagination(self, client):
        """Testa paginação de scan tasks."""
        # Create multiple scans
        with patch("main.asyncio.create_task"):
            for i in range(5):
                scan = {"target": f"192.168.1.{i}", "scan_type": "nmap_network", "parameters": {}}
                await client.post("/scans/", json=scan)

        # Test skip and limit
        response = await client.get("/scans/?skip=2&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestReadScanTask:
    """Testes do endpoint GET /scans/{scan_id}."""

    async def test_read_scan_task_success(self, client):
        """Testa busca de scan task por ID."""
        # Create a scan first
        scan_request = {"target": "192.168.1.1", "scan_type": "nmap_network", "parameters": {}}

        with patch("main.asyncio.create_task"):
            create_response = await client.post("/scans/", json=scan_request)
            scan_id = create_response.json()["id"]

        # Fetch the scan by ID
        response = await client.get(f"/scans/{scan_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == scan_id
        assert data["target"] == "192.168.1.1"

    async def test_read_scan_task_not_found(self, client):
        """Testa busca de scan task inexistente."""
        response = await client.get("/scans/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestReadScanVulnerabilities:
    """Testes do endpoint GET /scans/{scan_id}/vulnerabilities."""

    async def test_read_vulnerabilities_empty(self, client):
        """Testa listagem de vulnerabilities quando não há nenhuma."""
        # Create a scan first
        scan_request = {"target": "192.168.1.1", "scan_type": "nmap_network", "parameters": {}}

        with patch("main.asyncio.create_task"):
            create_response = await client.post("/scans/", json=scan_request)
            scan_id = create_response.json()["id"]

        # Fetch vulnerabilities
        response = await client.get(f"/scans/{scan_id}/vulnerabilities")

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestRunScanBackgroundTask:
    """Testes da função run_scan (background task)."""

    async def test_run_scan_nmap_success(self, client):
        """Testa execução de scan nmap com sucesso."""
        scan_request = {"target": "192.168.1.1", "scan_type": "nmap_network", "parameters": {"ports": [80]}}

        # Mock the scanner to return fake vulnerabilities
        mock_scan_result = {
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2021-1234",
                    "name": "Test Vulnerability",
                    "severity": "high",
                    "description": "Test description",
                    "solution": "Patch system",
                    "host": "192.168.1.1",
                    "port": 80,
                    "protocol": "tcp"
                }
            ]
        }

        with patch("main.nmap_scanner.scan_network", new_callable=AsyncMock, return_value=mock_scan_result):
            with patch("main.asyncio.create_task") as mock_create_task:
                # Create scan - this should trigger run_scan in background
                create_response = await client.post("/scans/", json=scan_request)
                scan_id = create_response.json()["id"]

                # Get the actual run_scan coroutine that was passed to create_task
                run_scan_coro = mock_create_task.call_args[0][0]

                # Execute it directly to test
                await run_scan_coro

        # Verify scan was updated to completed
        scan_response = await client.get(f"/scans/{scan_id}")
        scan_data = scan_response.json()
        assert scan_data["status"] == "completed"
        assert scan_data["end_time"] is not None

        # Verify vulnerability was stored
        vuln_response = await client.get(f"/scans/{scan_id}/vulnerabilities")
        vulns = vuln_response.json()
        assert len(vulns) == 1
        assert vulns[0]["cve_id"] == "CVE-2021-1234"

    async def test_run_scan_web_application_success(self, client):
        """Testa execução de scan web application com sucesso."""
        scan_request = {"target": "https://example.com", "scan_type": "web_application", "parameters": {"depth": 1}}

        mock_scan_result = {"vulnerabilities": []}

        with patch("main.web_scanner.scan_web_application", new_callable=AsyncMock, return_value=mock_scan_result):
            with patch("main.asyncio.create_task") as mock_create_task:
                create_response = await client.post("/scans/", json=scan_request)
                run_scan_coro = mock_create_task.call_args[0][0]
                await run_scan_coro

                scan_id = create_response.json()["id"]

        # Verify scan completed
        scan_response = await client.get(f"/scans/{scan_id}")
        assert scan_response.json()["status"] == "completed"

    async def test_run_scan_unsupported_type(self, client):
        """Testa execução de scan com tipo não suportado."""
        scan_request = {"target": "192.168.1.1", "scan_type": "unsupported_type", "parameters": {}}

        with patch("main.asyncio.create_task") as mock_create_task:
            create_response = await client.post("/scans/", json=scan_request)
            scan_id = create_response.json()["id"]

            run_scan_coro = mock_create_task.call_args[0][0]
            await run_scan_coro

        # Verify scan failed
        scan_response = await client.get(f"/scans/{scan_id}")
        scan_data = scan_response.json()
        assert scan_data["status"] == "failed"
        assert "Unsupported scan type" in scan_data["raw_results"]

    async def test_run_scan_scanner_exception(self, client):
        """Testa exceção durante execução do scanner."""
        scan_request = {"target": "192.168.1.1", "scan_type": "nmap_network", "parameters": {}}

        with patch("main.nmap_scanner.scan_network", new_callable=AsyncMock, side_effect=RuntimeError("Scanner failed")):
            with patch("main.asyncio.create_task") as mock_create_task:
                create_response = await client.post("/scans/", json=scan_request)
                scan_id = create_response.json()["id"]

                run_scan_coro = mock_create_task.call_args[0][0]
                await run_scan_coro

        # Verify scan failed with error
        scan_response = await client.get(f"/scans/{scan_id}")
        scan_data = scan_response.json()
        assert scan_data["status"] == "failed"
        assert "Scanner failed" in scan_data["raw_results"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
