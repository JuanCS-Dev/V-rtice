"""Tests for Atlas Service main application."""

import pytest
from datetime import datetime
import httpx
from main import app, EnvironmentUpdateRequest, QueryEnvironmentRequest, environmental_state


@pytest.fixture
async def client():
    """Async test client fixture using httpx."""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Atlas Service is operational" in data["message"]


@pytest.mark.asyncio
async def test_map_status(client):
    """Test map status endpoint."""
    response = await client.get("/map_status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "last_update" in data
    assert data["coverage_percentage"] == 95.5
    assert data["model_complexity"] == "high"


@pytest.mark.asyncio
async def test_update_environment_basic(client):
    """Test basic environment update."""
    payload = {
        "sensor_data": {"temperature": 25.5, "pressure": 1013.25},
        "data_source": "sensor-001",
        "timestamp": datetime.now().isoformat()
    }

    response = await client.post("/update_environment", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["new_features_integrated"] == 2
    assert "timestamp" in data
    assert "environmental_model_version" in data


@pytest.mark.asyncio
async def test_update_environment_multiple_features(client):
    """Test environment update with multiple sensor features."""
    payload = {
        "sensor_data": {
            "temperature": 25.5,
            "pressure": 1013.25,
            "humidity": 60,
            "wind_speed": 10,
            "visibility": 10000
        },
        "data_source": "weather-station-alpha",
        "timestamp": datetime.now().isoformat()
    }

    response = await client.post("/update_environment", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["new_features_integrated"] == 5


@pytest.mark.asyncio
async def test_update_environment_default_timestamp(client):
    """Test environment update with default timestamp."""
    payload = {
        "sensor_data": {"radar_signal": "strong"},
        "data_source": "radar-001"
    }

    response = await client.post("/update_environment", json=payload)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_query_environment_threats(client):
    """Test environment query for threats."""
    payload = {
        "query": "identify threats in sector 7",
        "context": {"current_location": "sector 6"}
    }

    response = await client.post("/query_environment", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "query_result" in data
    assert "situational_awareness_level" in data

    result = data["query_result"]
    assert "threats" in result["answer"].lower()
    assert result["threat_level"] == "high"


@pytest.mark.asyncio
async def test_query_environment_exit(client):
    """Test environment query for nearest exit."""
    payload = {
        "query": "find nearest exit",
        "context": {"current_position": {"x": 100, "y": 200}}
    }

    response = await client.post("/query_environment", json=payload)

    assert response.status_code == 200
    data = response.json()

    result = data["query_result"]
    assert "exit" in result["answer"].lower()
    assert "path" in result


@pytest.mark.asyncio
async def test_query_environment_generic(client):
    """Test environment query with generic question."""
    payload = {
        "query": "what is the current situation?"
    }

    response = await client.post("/query_environment", json=payload)

    assert response.status_code == 200
    data = response.json()

    result = data["query_result"]
    assert "being processed" in result["answer"]
    assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_query_environment_no_context(client):
    """Test environment query without context."""
    payload = {
        "query": "general status query"
    }

    response = await client.post("/query_environment", json=payload)

    assert response.status_code == 200


def test_environment_update_request_model():
    """Test EnvironmentUpdateRequest model validation."""
    request = EnvironmentUpdateRequest(
        sensor_data={"temp": 20},
        data_source="test-sensor"
    )

    assert request.sensor_data == {"temp": 20}
    assert request.data_source == "test-sensor"
    assert request.timestamp is not None


def test_query_environment_request_model():
    """Test QueryEnvironmentRequest model validation."""
    request = QueryEnvironmentRequest(
        query="test query",
        context={"location": "test"}
    )

    assert request.query == "test query"
    assert request.context == {"location": "test"}


def test_query_environment_request_no_context():
    """Test QueryEnvironmentRequest without context."""
    request = QueryEnvironmentRequest(query="test")

    assert request.query == "test"
    assert request.context is None


def test_app_metadata():
    """Test FastAPI app metadata."""
    assert app.title == "Maximus Atlas Service"
    assert app.version == "1.0.0"


@pytest.mark.asyncio
async def test_environment_update_invalid_payload(client):
    """Test environment update with invalid payload."""
    payload = {
        "data_source": "sensor-001"
        # Missing required 'sensor_data' field
    }

    response = await client.post("/update_environment", json=payload)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_query_environment_invalid_payload(client):
    """Test query environment with invalid payload."""
    payload = {
        "context": {"location": "test"}
        # Missing required 'query' field
    }

    response = await client.post("/query_environment", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_check_structure(client):
    """Test health check response structure."""
    response = await client.get("/health")
    data = response.json()

    # Verify all expected keys are present
    assert "status" in data
    assert "message" in data
    assert len(data) == 2


@pytest.mark.asyncio
async def test_map_status_structure(client):
    """Test map status response structure."""
    response = await client.get("/map_status")
    data = response.json()

    # Verify all expected keys
    assert "status" in data
    assert "last_update" in data
    assert "coverage_percentage" in data
    assert "model_complexity" in data


@pytest.mark.asyncio
async def test_update_environment_response_structure(client):
    """Test environment update response structure."""
    payload = {
        "sensor_data": {"test": "data"},
        "data_source": "test"
    }

    response = await client.post("/update_environment", json=payload)
    data = response.json()

    assert "timestamp" in data
    assert "status" in data
    assert "new_features_integrated" in data
    assert "environmental_model_version" in data


@pytest.mark.asyncio
async def test_query_environment_response_structure(client):
    """Test query environment response structure."""
    payload = {"query": "test query"}

    response = await client.post("/query_environment", json=payload)
    data = response.json()

    assert "timestamp" in data
    assert "query_result" in data
    assert "situational_awareness_level" in data


@pytest.mark.asyncio
async def test_situational_awareness_levels(client):
    """Test that situational awareness level is calculated."""
    payload = {"query": "status check"}

    response = await client.post("/query_environment", json=payload)
    data = response.json()

    # Should return one of the defined awareness levels
    awareness = data["situational_awareness_level"]
    assert awareness in ["high", "medium", "low", "minimal"]


@pytest.mark.asyncio
async def test_query_threats_case_insensitive(client):
    """Test threat query is case-insensitive."""
    payload = {"query": "THREATS in area"}

    response = await client.post("/query_environment", json=payload)
    data = response.json()

    assert "threats" in data["query_result"]["answer"].lower()


@pytest.mark.asyncio
async def test_query_exit_case_insensitive(client):
    """Test exit query is case-insensitive."""
    payload = {"query": "EXIT location"}

    response = await client.post("/query_environment", json=payload)
    data = response.json()

    assert "exit" in data["query_result"]["answer"].lower()


@pytest.mark.asyncio
async def test_concurrent_updates(client):
    """Test multiple concurrent environment updates."""
    payloads = [
        {"sensor_data": {"sensor_1": "data"}, "data_source": "s1"},
        {"sensor_data": {"sensor_2": "data"}, "data_source": "s2"},
        {"sensor_data": {"sensor_3": "data"}, "data_source": "s3"},
    ]

    responses = [await client.post("/update_environment", json=p) for p in payloads]

    assert all(r.status_code == 200 for r in responses)


@pytest.mark.asyncio
async def test_concurrent_queries(client):
    """Test multiple concurrent environment queries."""
    queries = [
        {"query": "threats"},
        {"query": "exit"},
        {"query": "general status"}
    ]

    responses = [await client.post("/query_environment", json=q) for q in queries]

    assert all(r.status_code == 200 for r in responses)


def test_environmental_state_structure():
    """Test environmental_state global variable structure."""
    assert "model_version" in environmental_state
    assert "last_update" in environmental_state
    assert "feature_count" in environmental_state
    assert "data_sources" in environmental_state
    assert "sensor_readings" in environmental_state


def test_environmental_state_defaults():
    """Test environmental_state default values."""
    assert environmental_state["model_version"] == "1.0.0"
    assert environmental_state["feature_count"] == 0
    assert isinstance(environmental_state["data_sources"], set)


@pytest.mark.asyncio
async def test_awareness_level_high(client):
    """Test 'high' situational awareness level."""
    # Set up environmental state for 'high' awareness
    from datetime import datetime
    environmental_state["data_sources"] = {"source1", "source2", "source3"}
    environmental_state["feature_count"] = 15
    environmental_state["last_update"] = datetime.now().isoformat()

    payload = {"query": "test"}
    response = await client.post("/query_environment", json=payload)
    data = response.json()

    assert data["situational_awareness_level"] == "high"


@pytest.mark.asyncio
async def test_awareness_level_medium(client):
    """Test 'medium' situational awareness level."""
    from datetime import datetime, timedelta
    environmental_state["data_sources"] = {"source1", "source2"}
    environmental_state["feature_count"] = 7
    environmental_state["last_update"] = (datetime.now() - timedelta(seconds=400)).isoformat()

    payload = {"query": "test"}
    response = await client.post("/query_environment", json=payload)
    data = response.json()

    assert data["situational_awareness_level"] == "medium"


@pytest.mark.asyncio
async def test_awareness_level_low(client):
    """Test 'low' situational awareness level."""
    from datetime import datetime, timedelta
    environmental_state["data_sources"] = {"source1"}
    environmental_state["feature_count"] = 3
    environmental_state["last_update"] = (datetime.now() - timedelta(seconds=1000)).isoformat()

    payload = {"query": "test"}
    response = await client.post("/query_environment", json=payload)
    data = response.json()

    assert data["situational_awareness_level"] == "low"
