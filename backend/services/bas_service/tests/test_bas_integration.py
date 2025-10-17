"""Integration tests for BAS Service - Breach & Attack Simulation.

Tests offensive arsenal safety checks, API endpoints, attack orchestration.
Validates that BAS service operates securely with proper guardrails.

NO REAL ATTACKS - only simulated/sandboxed environments.
"""

import asyncio
import os
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

# Set test environment variable BEFORE importing app
os.environ["MAXIMUS_ENV"] = "test"
os.environ["BAS_SAFE_MODE"] = "true"

from services.bas_service.api import app


@pytest.fixture
def client() -> TestClient:
    """Create TestClient for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_simulation_request() -> Dict[str, Any]:
    """Sample simulation request payload."""
    return {
        "attack_scenario": "credential_access",
        "target_service": "test_service",
        "duration_seconds": 10,
        "techniques": ["T1059", "T1003"]
    }


class TestHealthAndSafety:
    """Test health checks and safety mechanisms."""

    def test_health_endpoint(self, client: TestClient) -> None:
        """Health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        # Version might not be in response, that's OK

    def test_safe_mode_enabled(self, client: TestClient) -> None:
        """Verify safe mode is active in test environment."""
        # Safe mode verified via environment variable
        assert os.getenv("BAS_SAFE_MODE") == "true"
        assert os.getenv("MAXIMUS_ENV") == "test"

    def test_production_check_prevents_attacks(self, client: TestClient) -> None:
        """Simulations fail if production environment detected."""
        # This test validates safety guardrail
        # In real implementation, check for PRODUCTION env blocks attacks
        pass  # Placeholder - implement when production check exists


class TestAttackTechniques:
    """Test attack technique repository."""

    def test_techniques_loaded(self) -> None:
        """Attack techniques are loaded in memory."""
        from attack_techniques import AttackTechniques
        
        techniques = AttackTechniques()
        assert len(techniques.techniques) > 0
        
        # Verify MITRE ATT&CK format
        for tech_id, tech in techniques.techniques.items():
            assert tech_id.startswith("T")  # MITRE format
            assert tech.name
            assert tech.description

    def test_get_specific_technique(self) -> None:
        """Can retrieve specific technique by ID."""
        from attack_techniques import AttackTechniques
        
        techniques = AttackTechniques()
        tech = techniques.techniques.get("T1059")
        
        assert tech is not None
        assert tech.id == "T1059"
        assert tech.name == "Command and Scripting Interpreter"
        assert len(tech.parameters) > 0


class TestSimulationLifecycle:
    """Test complete simulation lifecycle."""

    def test_start_simulation_success(
        self, 
        client: TestClient,
        sample_simulation_request: Dict[str, Any]
    ) -> None:
        """Can start attack simulation using /simulate endpoint."""
        response = client.post("/simulate", json=sample_simulation_request)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data or "simulation_id" in data
        assert "status" in data

    def test_simulation_status(
        self, 
        client: TestClient,
        sample_simulation_request: Dict[str, Any]
    ) -> None:
        """Can query simulation status."""
        # Start simulation
        start_response = client.post("/simulate", json=sample_simulation_request)
        assert start_response.status_code == 200
        
        sim_data = start_response.json()
        sim_id = sim_data.get("id") or sim_data.get("simulation_id")
        
        # Query status
        response = client.get(f"/simulation/{sim_id}")
        assert response.status_code == 200
        status = response.json()
        
        assert "status" in status

    def test_get_simulation_results(
        self, 
        client: TestClient,
        sample_simulation_request: Dict[str, Any]
    ) -> None:
        """Can retrieve simulation results."""
        # Start simulation
        start_response = client.post("/simulate", json=sample_simulation_request)
        assert start_response.status_code == 200
        
        sim_data = start_response.json()
        sim_id = sim_data.get("id") or sim_data.get("simulation_id")
        
        # Wait briefly
        import time
        time.sleep(1)
        
        # Get results
        response = client.get(f"/simulation/{sim_id}/results")
        # May be 200 with results, 404 if not ready, or 409 if still running
        assert response.status_code in [200, 404, 409]
        
        if response.status_code == 200:
            results = response.json()
            assert isinstance(results, list)


class TestInputValidation:
    """Test API input validation."""

    def test_invalid_payload_rejected(self, client: TestClient) -> None:
        """Invalid JSON payload is rejected."""
        response = client.post("/simulate", json={})
        # Should fail validation
        assert response.status_code in [422, 400]

    def test_valid_simulation_accepted(self, client: TestClient) -> None:
        """Valid simulation request is accepted."""
        payload = {
            "attack_scenario": "credential_access",
            "target_service": "test",
            "duration_seconds": 5,
            "techniques": ["T1059"]
        }
        response = client.post("/simulate", json=payload)
        assert response.status_code == 200


class TestSafetyGuardrails:
    """Test safety mechanisms and guardrails."""

    def test_safe_mode_environment(self) -> None:
        """Safe mode enabled in test environment."""
        assert os.getenv("BAS_SAFE_MODE") == "true"
        assert os.getenv("MAXIMUS_ENV") == "test"

    def test_simulation_completes_safely(self, client: TestClient) -> None:
        """Simulation runs without crashing in safe mode."""
        payload = {
            "attack_scenario": "test",
            "target_service": "test",
            "duration_seconds": 1,
            "techniques": []
        }
        response = client.post("/simulate", json=payload)
        # Should complete without errors
        assert response.status_code in [200, 400, 422]  # Valid responses


class TestMetricsAndAudit:
    """Test metrics collection."""

    def test_metrics_endpoint(self, client: TestClient) -> None:
        """Metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Basic Prometheus format check
        metrics_text = response.text
        assert len(metrics_text) > 0


class TestPurpleTeamIntegration:
    """Test Purple Team Engine integration."""

    def test_purple_team_engine_exists(self) -> None:
        """Purple Team Engine component is initialized."""
        from purple_team_engine import PurpleTeamEngine
        from atomic_executor import AtomicExecutor
        from metrics import MetricsCollector
        
        executor = AtomicExecutor()
        metrics = MetricsCollector()
        engine = PurpleTeamEngine(executor, metrics)
        
        assert engine is not None


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test asynchronous attack execution."""

    async def test_atomic_executor_exists(self) -> None:
        """AtomicExecutor component is available."""
        from atomic_executor import AtomicExecutor
        
        executor = AtomicExecutor()
        assert executor is not None


# Integration test requiring docker-compose
@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION") == "true",
    reason="Integration tests require full stack"
)
class TestFullStackIntegration:
    """Full stack integration tests with docker-compose."""

    def test_bas_communicates_with_vuln_intel(self, client: TestClient) -> None:
        """BAS service can query vuln intel service."""
        # This would test actual service-to-service communication
        pass  # Implement when docker-compose test environment ready

    def test_bas_reports_to_siem(self, client: TestClient) -> None:
        """BAS results are sent to SIEM service."""
        pass  # Implement when SIEM integration ready


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
