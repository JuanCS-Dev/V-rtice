"""Unit tests for Maximus Digital Thalamus Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Lifecycle events (startup/shutdown)
- Sensory data ingestion (with gating, filtering, routing)
- Sensory gating logic (allow/block decisions)
- Signal filtering (type-specific transformations)
- Attention control (prioritization and routing)
- Component validation
- Edge cases

Note: NO production logic mocking (PAGANI compliant).
All component logic is REAL. Only external dependencies would be mocked if present.
"""

import asyncio

# Import the FastAPI app and components
import sys
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/digital_thalamus_service")
from api import app
from attention_control import AttentionControl
from sensory_gating import SensoryGating
from signal_filtering import SignalFiltering

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sensory_gating_instance():
    """Create fresh SensoryGating instance for testing."""
    return SensoryGating()


@pytest.fixture
def signal_filtering_instance():
    """Create fresh SignalFiltering instance for testing."""
    return SignalFiltering()


@pytest.fixture
def attention_control_instance():
    """Create fresh AttentionControl instance for testing."""
    return AttentionControl()


def create_sensory_data_request(sensor_id="sensor_001", sensor_type="visual", data=None, priority=5):
    """Helper to create SensoryDataIngest payload."""
    if data is None:
        data = {"noise_level": 0.3, "signal_strength": 0.8}
    return {
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "priority": priority,
    }


# ==================== HEALTH CHECK TESTS ====================


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_check_returns_healthy_status(self, client):
        """Test health endpoint returns operational status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "operational" in data["message"].lower()


# ==================== LIFECYCLE EVENT TESTS ====================


@pytest.mark.asyncio
class TestLifecycleEvents:
    """Test FastAPI lifecycle events."""

    async def test_startup_event_executes(self):
        """Test startup event executes without errors."""
        from api import startup_event

        await startup_event()
        # If no exception, test passes

    async def test_shutdown_event_executes(self):
        """Test shutdown event executes without errors."""
        from api import shutdown_event

        await shutdown_event()
        # If no exception, test passes


# ==================== INGEST SENSORY DATA TESTS ====================


@pytest.mark.asyncio
class TestIngestSensoryData:
    """Test sensory data ingestion endpoint - REAL gating/filtering/routing logic."""

    async def test_ingest_visual_data_high_priority_success(self, client):
        """Test ingesting high-priority visual data successfully processes."""
        payload = create_sensory_data_request(
            sensor_type="visual",
            priority=10,  # High intensity/priority
            data={"noise_level": 0.2, "signal_strength": 0.95},
        )

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed_and_routed"
        assert data["sensor_type"] == "visual"
        assert "processed_payload_summary" in data

    async def test_ingest_auditory_data_success(self, client):
        """Test ingesting auditory data processes successfully."""
        payload = create_sensory_data_request(
            sensor_type="auditory", priority=7, data={"background_noise": 0.6, "speech_signal": 0.8}
        )

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed_and_routed"
        assert data["sensor_type"] == "auditory"

    async def test_ingest_chemical_data_success(self, client):
        """Test ingesting chemical sensor data."""
        payload = create_sensory_data_request(
            sensor_type="chemical", priority=6, data={"concentration": 0.75, "ph_level": 7.2}
        )

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed_and_routed"
        assert data["sensor_type"] == "chemical"

    async def test_ingest_somatosensory_data_success(self, client):
        """Test ingesting somatosensory data."""
        payload = create_sensory_data_request(
            sensor_type="somatosensory", priority=4, data={"pressure": 0.5, "temperature": 36.5}
        )

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed_and_routed"

    async def test_ingest_low_priority_data_rejected_by_gating(self, client):
        """Test that low-priority data is rejected by sensory gating - REAL gating logic."""
        payload = create_sensory_data_request(
            sensor_type="visual",
            priority=1,  # Low priority (0.1 intensity when normalized)
            data={"noise_level": 0.9, "signal_strength": 0.1},
        )

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should be rejected by gating
        assert data["status"] == "rejected"
        assert "gating" in data["reason"].lower()

    async def test_ingest_different_sensor_ids(self, client):
        """Test that different sensor IDs are handled correctly."""
        payloads = [
            create_sensory_data_request(sensor_id="visual_cam_01", priority=8),
            create_sensory_data_request(sensor_id="audio_mic_02", sensor_type="auditory", priority=7),
        ]

        for payload in payloads:
            response = await client.post("/ingest_sensory_data", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["sensor_id"] == payload["sensor_id"]

    async def test_ingest_preserves_timestamp(self, client):
        """Test that timestamp is preserved in response."""
        payload = create_sensory_data_request(priority=6)

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        # Validate it's a valid ISO timestamp
        datetime.fromisoformat(data["timestamp"])

    async def test_ingest_returns_processed_payload_summary(self, client):
        """Test that response includes processed payload summary."""
        payload = create_sensory_data_request(priority=7, data={"key1": "value1", "key2": "value2", "key3": "value3"})

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "processed_payload_summary" in data
        assert "keys" in data["processed_payload_summary"]
        assert "size" in data["processed_payload_summary"]
        assert len(data["processed_payload_summary"]["keys"]) > 0


# ==================== SENSORY GATING TESTS ====================


@pytest.mark.asyncio
class TestSensoryGating:
    """Test SensoryGating component - REAL gating logic without mocks."""

    def test_allow_data_visual_above_threshold(self, sensory_gating_instance):
        """Test visual data above threshold is allowed - REAL threshold check."""
        # Visual threshold is 0.4 by default
        result = sensory_gating_instance.allow_data("visual", 0.5)

        assert result is True
        assert sensory_gating_instance.blocked_data_count == 0

    def test_allow_data_visual_below_threshold(self, sensory_gating_instance):
        """Test visual data below threshold is blocked."""
        # Visual threshold is 0.4
        result = sensory_gating_instance.allow_data("visual", 0.3)

        assert result is False
        assert sensory_gating_instance.blocked_data_count == 1

    def test_allow_data_auditory_exact_threshold(self, sensory_gating_instance):
        """Test auditory data exactly at threshold is allowed."""
        # Auditory threshold is 0.3
        result = sensory_gating_instance.allow_data("auditory", 0.3)

        assert result is True  # >= threshold

    def test_allow_data_chemical_high_intensity(self, sensory_gating_instance):
        """Test chemical data with high intensity passes gating."""
        # Chemical threshold is 0.5
        result = sensory_gating_instance.allow_data("chemical", 0.9)

        assert result is True

    def test_allow_data_somatosensory_low_threshold(self, sensory_gating_instance):
        """Test somatosensory has lowest threshold (0.2)."""
        # Somatosensory threshold is 0.2
        result = sensory_gating_instance.allow_data("somatosensory", 0.25)

        assert result is True

    def test_allow_data_unknown_type_uses_default_threshold(self, sensory_gating_instance):
        """Test unknown sensor type uses default threshold (0.3)."""
        result = sensory_gating_instance.allow_data("unknown_sensor", 0.4)

        assert result is True  # 0.4 >= 0.3 (default)

    def test_blocked_data_count_increments(self, sensory_gating_instance):
        """Test that blocked data count increments correctly."""
        sensory_gating_instance.allow_data("visual", 0.1)  # Blocked
        sensory_gating_instance.allow_data("auditory", 0.1)  # Blocked
        sensory_gating_instance.allow_data("visual", 0.9)  # Allowed

        assert sensory_gating_instance.blocked_data_count == 2

    async def test_get_status_returns_configuration(self, sensory_gating_instance):
        """Test get_status returns current gating configuration."""
        status = await sensory_gating_instance.get_status()

        assert status["status"] == "active"
        assert status["default_threshold"] == 0.3
        assert "gating_rules" in status
        assert status["gating_rules"]["visual"] == 0.4
        assert "blocked_data_count_since_startup" in status

    def test_set_gating_threshold_valid(self, sensory_gating_instance):
        """Test setting valid gating threshold."""
        sensory_gating_instance.set_gating_threshold("visual", 0.6)

        assert sensory_gating_instance.gating_rules["visual"] == 0.6

    def test_set_gating_threshold_invalid_high(self, sensory_gating_instance):
        """Test setting threshold above 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            sensory_gating_instance.set_gating_threshold("visual", 1.5)

    def test_set_gating_threshold_invalid_low(self, sensory_gating_instance):
        """Test setting threshold below 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            sensory_gating_instance.set_gating_threshold("auditory", -0.1)


# ==================== SIGNAL FILTERING TESTS ====================


@pytest.mark.asyncio
class TestSignalFiltering:
    """Test SignalFiltering component - REAL filtering logic without mocks."""

    def test_apply_filters_visual_adds_noise_reduction(self, signal_filtering_instance):
        """Test visual filtering adds noise reduction - REAL transformation."""
        raw_data = {"noise_level": 0.8, "raw_pixels": [1, 2, 3]}

        filtered = signal_filtering_instance.apply_filters(raw_data, "visual")

        assert "visual_noise_reduced" in filtered
        assert filtered["visual_noise_reduced"] == 0.8 * 0.5  # 50% reduction
        assert filtered["visual_edges_enhanced"] is True
        assert "raw_pixels" in filtered  # Original data preserved

    def test_apply_filters_auditory_suppresses_noise(self, signal_filtering_instance):
        """Test auditory filtering suppresses background noise."""
        raw_data = {"background_noise": 0.7, "speech_waveform": [0.1, 0.2]}

        filtered = signal_filtering_instance.apply_filters(raw_data, "auditory")

        assert "auditory_noise_suppressed" in filtered
        assert filtered["auditory_noise_suppressed"] == 0.7 * 0.3  # 70% suppression
        assert filtered["speech_clarity_enhanced"] is True

    def test_apply_filters_chemical_baseline_correction(self, signal_filtering_instance):
        """Test chemical filtering applies baseline correction."""
        raw_data = {"concentration": 0.65, "compound_id": "C2H5OH"}

        filtered = signal_filtering_instance.apply_filters(raw_data, "chemical")

        assert "chemical_baseline_corrected" in filtered
        assert filtered["chemical_baseline_corrected"] is True
        assert filtered["compound_id"] == "C2H5OH"

    def test_apply_filters_somatosensory_smoothing(self, signal_filtering_instance):
        """Test somatosensory filtering applies smoothing."""
        raw_data = {"pressure": 0.5, "temperature": 36.5}

        filtered = signal_filtering_instance.apply_filters(raw_data, "somatosensory")

        assert "somatosensory_smoothed" in filtered
        assert filtered["somatosensory_smoothed"] is True
        assert filtered["pressure"] == 0.5

    def test_apply_filters_unknown_type_preserves_data(self, signal_filtering_instance):
        """Test unknown sensor type still processes (copies) data."""
        raw_data = {"custom_metric": 0.75, "device_id": "XYZ"}

        filtered = signal_filtering_instance.apply_filters(raw_data, "unknown")

        # Should be a copy with no specific filtering
        assert filtered["custom_metric"] == 0.75
        assert filtered["device_id"] == "XYZ"
        # No type-specific keys added
        assert "visual_noise_reduced" not in filtered

    def test_processed_data_count_increments(self, signal_filtering_instance):
        """Test that processed data counter increments."""
        signal_filtering_instance.apply_filters({}, "visual")
        signal_filtering_instance.apply_filters({}, "auditory")
        signal_filtering_instance.apply_filters({}, "chemical")

        assert signal_filtering_instance.processed_data_count == 3

    async def test_get_status_returns_processing_stats(self, signal_filtering_instance):
        """Test get_status returns processing statistics."""
        signal_filtering_instance.apply_filters({}, "visual")

        status = await signal_filtering_instance.get_status()

        assert status["status"] == "idle"
        assert status["total_data_processed"] == 1
        assert "last_filter" in status


# ==================== ATTENTION CONTROL TESTS ====================


@pytest.mark.asyncio
class TestAttentionControl:
    """Test AttentionControl component - REAL prioritization/routing logic."""

    async def test_prioritize_and_route_high_priority_to_prefrontal(self, attention_control_instance):
        """Test high effective priority routes to Prefrontal Cortex - REAL routing decision."""
        sensory_data = {"signal": "important_visual_data"}
        # priority=10 * visual_weight=0.8 = 8.0 effective (> 6.0 threshold)

        result = await attention_control_instance.prioritize_and_route(sensory_data, "visual", priority=10)

        assert result["effective_priority"] == 10 * 0.8  # 8.0
        assert result["routing_destination"] == "Prefrontal_Cortex_Service"
        assert "attention_notes" in result

    async def test_prioritize_and_route_low_priority_to_core(self, attention_control_instance):
        """Test low effective priority routes to Maximus Core."""
        sensory_data = {"signal": "routine_data"}
        # priority=5 * somatosensory_weight=0.5 = 2.5 effective (<= 6.0 threshold)

        result = await attention_control_instance.prioritize_and_route(sensory_data, "somatosensory", priority=5)

        assert result["effective_priority"] == 5 * 0.5  # 2.5
        assert result["routing_destination"] == "Maximus_Core_Service"

    async def test_prioritize_and_route_exact_threshold(self, attention_control_instance):
        """Test priority exactly at threshold (6.0) routes to Core."""
        sensory_data = {"signal": "boundary_case"}
        # Need effective_priority = 6.0: priority=10 * chemical_weight=0.6 = 6.0

        result = await attention_control_instance.prioritize_and_route(sensory_data, "chemical", priority=10)

        assert result["effective_priority"] == 6.0
        # Exactly 6.0 is NOT > 6.0, so routes to Core
        assert result["routing_destination"] == "Maximus_Core_Service"

    async def test_prioritize_and_route_auditory_medium_priority(self, attention_control_instance):
        """Test auditory data with medium priority."""
        sensory_data = {"audio_stream": "data"}
        # priority=9 * auditory_weight=0.7 = 6.3 effective (> 6.0)

        result = await attention_control_instance.prioritize_and_route(sensory_data, "auditory", priority=9)

        assert result["effective_priority"] == 9 * 0.7  # 6.3
        assert result["routing_destination"] == "Prefrontal_Cortex_Service"

    async def test_prioritize_and_route_unknown_type_uses_default_weight(self, attention_control_instance):
        """Test unknown sensor type uses default weight (0.5)."""
        sensory_data = {"unknown_signal": "test"}

        result = await attention_control_instance.prioritize_and_route(sensory_data, "unknown_sensor", priority=8)

        assert result["effective_priority"] == 8 * 0.5  # 4.0 (default weight)
        assert result["routing_destination"] == "Maximus_Core_Service"

    async def test_prioritize_and_route_updates_focus(self, attention_control_instance):
        """Test that prioritization updates current focus."""
        await attention_control_instance.prioritize_and_route({}, "visual", 7)

        assert attention_control_instance.current_focus == "visual"

    async def test_get_status_returns_attention_state(self, attention_control_instance):
        """Test get_status returns attention control state."""
        await attention_control_instance.prioritize_and_route({}, "auditory", 5)

        status = await attention_control_instance.get_status()

        assert status["status"] == "monitoring_attention"
        assert status["current_focus"] == "auditory"
        assert "priority_weights" in status
        assert status["priority_weights"]["visual"] == 0.8

    def test_set_priority_weight_valid(self, attention_control_instance):
        """Test setting valid priority weight."""
        attention_control_instance.set_priority_weight("visual", 0.9)

        assert attention_control_instance.priority_weights["visual"] == 0.9

    def test_set_priority_weight_invalid_high(self, attention_control_instance):
        """Test setting weight above 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            attention_control_instance.set_priority_weight("auditory", 1.2)

    def test_set_priority_weight_invalid_low(self, attention_control_instance):
        """Test setting weight below 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            attention_control_instance.set_priority_weight("chemical", -0.3)


# ==================== GATING/ATTENTION STATUS ENDPOINTS ====================


@pytest.mark.asyncio
class TestStatusEndpoints:
    """Test gating and attention status endpoints."""

    async def test_get_gating_status_returns_configuration(self, client):
        """Test /gating_status endpoint returns gating configuration."""
        response = await client.get("/gating_status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "gating_rules" in data
        assert "default_threshold" in data

    async def test_get_attention_status_returns_state(self, client):
        """Test /attention_status endpoint returns attention state."""
        response = await client.get("/attention_status")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "priority_weights" in data


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_ingest_empty_data_payload(self, client):
        """Test ingesting with empty data dict."""
        payload = create_sensory_data_request(data={}, priority=7)

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        # Should still process, just with no keys in data

    async def test_ingest_minimum_priority(self, client):
        """Test ingesting with minimum priority (1)."""
        payload = create_sensory_data_request(priority=1)

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        # May be rejected by gating depending on type/intensity

    async def test_ingest_maximum_priority(self, client):
        """Test ingesting with maximum priority (10)."""
        payload = create_sensory_data_request(priority=10)

        response = await client.post("/ingest_sensory_data", json=payload)

        assert response.status_code == 200
        data = response.json()
        # High priority should be processed
        assert data["status"] == "processed_and_routed"

    async def test_ingest_concurrent_requests(self, client):
        """Test handling concurrent sensory data ingestion."""
        payloads = [create_sensory_data_request(sensor_id=f"sensor_{i}", priority=5 + i) for i in range(5)]

        # Send concurrent requests
        tasks = [client.post("/ingest_sensory_data", json=p) for p in payloads]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    def test_sensory_gating_boundary_values(self, sensory_gating_instance):
        """Test gating with boundary intensity values."""
        # Exactly 0.0
        assert sensory_gating_instance.allow_data("visual", 0.0) is False

        # Exactly 1.0
        assert sensory_gating_instance.allow_data("visual", 1.0) is True

    async def test_attention_control_minimum_priority(self, attention_control_instance):
        """Test attention control with minimum priority."""
        result = await attention_control_instance.prioritize_and_route({}, "visual", 1)

        assert result["effective_priority"] == 1 * 0.8  # 0.8
        assert result["routing_destination"] == "Maximus_Core_Service"

    async def test_attention_control_maximum_priority(self, attention_control_instance):
        """Test attention control with maximum priority."""
        result = await attention_control_instance.prioritize_and_route({}, "visual", 10)

        assert result["effective_priority"] == 10 * 0.8  # 8.0
        assert result["routing_destination"] == "Prefrontal_Cortex_Service"
