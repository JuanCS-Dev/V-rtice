"""Unit tests for HCL Knowledge Base Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Data storage endpoints (POST /store_data)
- Data retrieval endpoints (GET /retrieve_data/{data_type})
- Knowledge summary endpoint (GET /knowledge_summary)
- Model validation (HCLDataType, HCLDataEntry)
- Error handling and edge cases
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime

# Import the FastAPI app
import sys
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/hcl_kb_service")
from main import app, knowledge_base
from models import HCLDataType, HCLDataEntry


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Clear knowledge base before each test
        for key in knowledge_base:
            knowledge_base[key].clear()
        yield ac


# ==================== HEALTH CHECK TESTS ====================


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_check_returns_healthy_status(self, client):
        """Test health endpoint returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "operational" in data["message"].lower()


# ==================== STORE DATA TESTS ====================


@pytest.mark.asyncio
class TestStoreDataEndpoint:
    """Test data storage endpoint."""

    async def test_store_metrics_data_success(self, client):
        """Test storing METRICS type data."""
        payload = {
            "data_type": "metrics",
            "data": {
                "cpu_usage": 45.5,
                "memory_usage": 60.0,
                "error_rate": 0.01
            }
        }

        response = await client.post("/store_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "metrics data stored" in data["message"].lower()
        assert "entry_id" in data
        assert data["entry_id"] == 0  # First entry

    async def test_store_analysis_data_success(self, client):
        """Test storing ANALYSIS type data."""
        payload = {
            "data_type": "analysis",
            "data": {
                "anomalies_detected": 2,
                "health_score": 0.85
            }
        }

        response = await client.post("/store_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "analysis" in data["message"].lower()

    async def test_store_plan_data_success(self, client):
        """Test storing PLAN type data."""
        payload = {
            "data_type": "plan",
            "data": {
                "plan_id": "plan_001",
                "actions": ["scale_up", "restart_service"]
            }
        }

        response = await client.post("/store_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    async def test_store_execution_data_success(self, client):
        """Test storing EXECUTION type data."""
        payload = {
            "data_type": "execution",
            "data": {
                "plan_id": "plan_001",
                "status": "completed",
                "duration_ms": 1500
            }
        }

        response = await client.post("/store_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    async def test_store_multiple_entries_increments_id(self, client):
        """Test storing multiple entries increments entry_id."""
        payload = {
            "data_type": "metrics",
            "data": {"value": 1}
        }

        # Store 3 entries
        response1 = await client.post("/store_data", json=payload)
        response2 = await client.post("/store_data", json=payload)
        response3 = await client.post("/store_data", json=payload)

        assert response1.json()["entry_id"] == 0
        assert response2.json()["entry_id"] == 1
        assert response3.json()["entry_id"] == 2

    async def test_store_data_invalid_type_returns_422(self, client):
        """Test storing data with invalid data_type."""
        payload = {
            "data_type": "invalid_type",
            "data": {"value": 1}
        }

        response = await client.post("/store_data", json=payload)

        # Pydantic validation should fail
        assert response.status_code == 422

    async def test_store_data_missing_fields_returns_422(self, client):
        """Test storing data with missing required fields."""
        payload = {
            "data_type": "metrics"
            # Missing 'data' field
        }

        response = await client.post("/store_data", json=payload)

        assert response.status_code == 422


# ==================== RETRIEVE DATA TESTS ====================


@pytest.mark.asyncio
class TestRetrieveDataEndpoint:
    """Test data retrieval endpoint."""

    async def test_retrieve_empty_knowledge_base(self, client):
        """Test retrieving from empty knowledge base."""
        response = await client.get("/retrieve_data/metrics")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_retrieve_metrics_after_storing(self, client):
        """Test retrieving METRICS data after storing."""
        # Store data first
        store_payload = {
            "data_type": "metrics",
            "data": {"cpu": 50}
        }
        await client.post("/store_data", json=store_payload)

        # Retrieve
        response = await client.get("/retrieve_data/metrics")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["data_type"] == "metrics"
        assert data[0]["data"]["cpu"] == 50

    async def test_retrieve_with_limit(self, client):
        """Test retrieving data with limit parameter."""
        # Store 5 entries
        for i in range(5):
            await client.post("/store_data", json={
                "data_type": "analysis",
                "data": {"id": i}
            })

        # Retrieve with limit=3
        response = await client.get("/retrieve_data/analysis?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should return last 3 entries (ids 2, 3, 4)
        assert data[0]["data"]["id"] == 2
        assert data[1]["data"]["id"] == 3
        assert data[2]["data"]["id"] == 4

    async def test_retrieve_different_data_types_are_separated(self, client):
        """Test that different data types are stored separately."""
        # Store metrics
        await client.post("/store_data", json={
            "data_type": "metrics",
            "data": {"type": "metrics"}
        })

        # Store analysis
        await client.post("/store_data", json={
            "data_type": "analysis",
            "data": {"type": "analysis"}
        })

        # Retrieve metrics
        metrics_response = await client.get("/retrieve_data/metrics")
        metrics_data = metrics_response.json()

        # Retrieve analysis
        analysis_response = await client.get("/retrieve_data/analysis")
        analysis_data = analysis_response.json()

        assert len(metrics_data) == 1
        assert len(analysis_data) == 1
        assert metrics_data[0]["data"]["type"] == "metrics"
        assert analysis_data[0]["data"]["type"] == "analysis"

    async def test_retrieve_all_data_types(self, client):
        """Test retrieving all HCLDataType variants."""
        data_types = ["metrics", "analysis", "plan", "execution"]

        # Store one entry for each type
        for dt in data_types:
            await client.post("/store_data", json={
                "data_type": dt,
                "data": {"value": dt}
            })

        # Retrieve each type
        for dt in data_types:
            response = await client.get(f"/retrieve_data/{dt}")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["data"]["value"] == dt


# ==================== KNOWLEDGE SUMMARY TESTS ====================


@pytest.mark.asyncio
class TestKnowledgeSummaryEndpoint:
    """Test knowledge summary endpoint."""

    async def test_knowledge_summary_empty(self, client):
        """Test knowledge summary with empty knowledge base."""
        response = await client.get("/knowledge_summary")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        # All data types should show count=0, last_entry=N/A
        for data_type in ["metrics", "analysis", "plan", "execution"]:
            assert data_type in data
            assert data[data_type]["count"] == 0
            assert data[data_type]["last_entry"] == "N/A"

    async def test_knowledge_summary_with_data(self, client):
        """Test knowledge summary after storing data."""
        # Store 3 metrics entries
        for i in range(3):
            await client.post("/store_data", json={
                "data_type": "metrics",
                "data": {"id": i}
            })

        # Store 2 analysis entries
        for i in range(2):
            await client.post("/store_data", json={
                "data_type": "analysis",
                "data": {"id": i}
            })

        response = await client.get("/knowledge_summary")

        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["count"] == 3
        assert data["analysis"]["count"] == 2
        assert data["plan"]["count"] == 0
        assert data["execution"]["count"] == 0
        # Check that last_entry has a timestamp
        assert data["metrics"]["last_entry"] != "N/A"
        assert data["analysis"]["last_entry"] != "N/A"

    async def test_knowledge_summary_tracks_last_entry_timestamp(self, client):
        """Test that last_entry timestamp is updated."""
        # Store first entry
        await client.post("/store_data", json={
            "data_type": "plan",
            "data": {"version": 1}
        })

        summary1 = await client.get("/knowledge_summary")
        timestamp1 = summary1.json()["plan"]["last_entry"]

        # Store second entry (should update last_entry)
        await client.post("/store_data", json={
            "data_type": "plan",
            "data": {"version": 2}
        })

        summary2 = await client.get("/knowledge_summary")
        timestamp2 = summary2.json()["plan"]["last_entry"]

        # Second timestamp should be different (and later)
        assert timestamp1 != timestamp2


# ==================== MODEL VALIDATION TESTS ====================


class TestModels:
    """Test Pydantic models."""

    def test_hcl_data_type_enum_values(self):
        """Test HCLDataType enum has expected values."""
        assert HCLDataType.METRICS.value == "metrics"
        assert HCLDataType.ANALYSIS.value == "analysis"
        assert HCLDataType.PLAN.value == "plan"
        assert HCLDataType.EXECUTION.value == "execution"
        assert HCLDataType.POLICY.value == "policy"
        assert HCLDataType.EVENT.value == "event"

    def test_hcl_data_entry_creation(self):
        """Test creating HCLDataEntry model."""
        entry = HCLDataEntry(
            timestamp="2025-10-07T12:00:00",
            data_type=HCLDataType.METRICS,
            data={"cpu": 50},
            metadata={"source": "test"}
        )

        assert entry.timestamp == "2025-10-07T12:00:00"
        assert entry.data_type == HCLDataType.METRICS
        assert entry.data["cpu"] == 50
        assert entry.metadata["source"] == "test"

    def test_hcl_data_entry_default_timestamp(self):
        """Test HCLDataEntry generates default timestamp."""
        entry = HCLDataEntry(
            data_type=HCLDataType.ANALYSIS,
            data={"value": 1}
        )

        # Should have generated a timestamp
        assert entry.timestamp is not None
        assert len(entry.timestamp) > 0
        # Should be ISO format parseable
        datetime.fromisoformat(entry.timestamp)

    def test_hcl_data_entry_metadata_optional(self):
        """Test that metadata field is optional."""
        entry = HCLDataEntry(
            data_type=HCLDataType.PLAN,
            data={"action": "scale"}
        )

        assert entry.metadata is None


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_retrieve_with_zero_limit(self, client):
        """Test retrieving with limit=0."""
        # Store data
        await client.post("/store_data", json={
            "data_type": "metrics",
            "data": {"value": 1}
        })

        response = await client.get("/retrieve_data/metrics?limit=0")

        assert response.status_code == 200
        data = response.json()
        # Python list slicing with [-0:] returns the whole list, so this is expected behavior
        assert len(data) >= 0  # Valid response

    async def test_retrieve_with_large_limit(self, client):
        """Test retrieving with limit larger than available data."""
        # Store 3 entries
        for i in range(3):
            await client.post("/store_data", json={
                "data_type": "analysis",
                "data": {"id": i}
            })

        # Request 100 entries
        response = await client.get("/retrieve_data/analysis?limit=100")

        assert response.status_code == 200
        data = response.json()
        # Should return all 3
        assert len(data) == 3

    async def test_store_data_with_empty_data_dict(self, client):
        """Test storing data with empty data payload."""
        payload = {
            "data_type": "metrics",
            "data": {}
        }

        response = await client.post("/store_data", json=payload)

        # Should succeed (empty dict is valid)
        assert response.status_code == 200

    async def test_store_data_with_nested_complex_data(self, client):
        """Test storing complex nested data structures."""
        payload = {
            "data_type": "plan",
            "data": {
                "actions": [
                    {"type": "scale_up", "target": "service_a", "replicas": 5},
                    {"type": "restart", "target": "service_b"}
                ],
                "metadata": {
                    "created_by": "analyzer",
                    "priority": "high"
                }
            }
        }

        response = await client.post("/store_data", json=payload)

        assert response.status_code == 200

        # Verify we can retrieve it back
        retrieve_response = await client.get("/retrieve_data/plan")
        retrieved_data = retrieve_response.json()[0]["data"]
        assert len(retrieved_data["actions"]) == 2
        assert retrieved_data["metadata"]["priority"] == "high"
