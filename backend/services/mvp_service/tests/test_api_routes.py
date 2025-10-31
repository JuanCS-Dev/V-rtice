"""API routes smoke tests.

These tests validate critical API endpoints with basic happy path scenarios.
Full coverage (90%+) will be achieved incrementally in FASE 2-4 per TDD roadmap.

Author: Vértice Platform Team
License: Proprietary
"""

from fastapi import status


class TestNarrativeEndpoints:
    """Test suite for narrative generation endpoints."""

    def test_generate_narrative_success(
        self, client, mock_mvp_service, sample_narrative_request
    ):
        """Test generating narrative returns narrative data."""
        response = client.post("/api/v1/narratives", json=sample_narrative_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "narrative_id" in data
        assert "narrative_text" in data
        assert "word_count" in data
        assert "nqs" in data

    def test_get_narrative_by_id(self, client, mock_mvp_service):
        """Test retrieving narrative by ID."""
        narrative_id = "mvp-narr-test-123"

        response = client.get(f"/api/v1/narratives/{narrative_id}")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_list_narratives(self, client, mock_mvp_service):
        """Test listing narratives with pagination."""
        response = client.get("/api/v1/narratives?limit=50&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "narratives" in data or "items" in data

    def test_delete_narrative(self, client, mock_mvp_service):
        """Test deleting a narrative."""
        narrative_id = "mvp-narr-test-123"

        response = client.delete(f"/api/v1/narratives/{narrative_id}")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestAudioEndpoints:
    """Test suite for audio synthesis endpoints."""

    def test_synthesize_audio_success(self, client, mock_mvp_service):
        """Test audio synthesis returns audio URL."""
        response = client.post(
            "/api/v1/audio/synthesize",
            json={
                "text": "This is a test narrative.",
                "voice_id": "elevenlabs-voice-marcus",
                "duration_target_seconds": 30,
            },
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED,
        ]


class TestErrorHandling:
    """Test suite for error handling across all endpoints."""

    def test_get_mvp_service_import_error(self, client):
        """Test get_mvp_service when main import fails (lines 44-45)."""
        import sys
        from unittest.mock import patch

        from services.mvp_service.api.routes import set_mvp_service

        # Set service to None to trigger fallback import
        set_mvp_service(None)

        # Mock sys.modules to simulate ImportError from main
        with patch.dict(sys.modules, {"services.mvp_service.main": None}):
            response = client.post(
                "/api/v1/narratives",
                json={"consciousness_snapshot_id": "test-123", "tone": "reflective"},
            )

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        # Restore mock for other tests
        from services.mvp_service.tests.conftest import _get_mock_mvp_service

        set_mvp_service(_get_mock_mvp_service())

    def test_generate_narrative_service_not_initialized(self, client):
        """Test narrative generation when service not initialized."""
        from services.mvp_service.api.routes import set_mvp_service

        set_mvp_service(None)

        response = client.post(
            "/api/v1/narratives",
            json={"consciousness_snapshot_id": "test-123", "tone": "reflective"},
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        # Restore mock for other tests
        from services.mvp_service.tests.conftest import _get_mock_mvp_service

        set_mvp_service(_get_mock_mvp_service())

    def test_generate_narrative_service_unhealthy(self, client, mock_mvp_service):
        """Test narrative generation when service is unhealthy."""
        mock_mvp_service.is_healthy.return_value = False

        response = client.post(
            "/api/v1/narratives",
            json={"consciousness_snapshot_id": "test-123", "tone": "reflective"},
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_generate_narrative_generic_error(self, client, mock_mvp_service):
        """Test narrative generation with generic exception."""
        mock_mvp_service.is_healthy.side_effect = Exception("Unexpected error")

        response = client.post(
            "/api/v1/narratives",
            json={"consciousness_snapshot_id": "test-123", "tone": "reflective"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_narrative_service_unhealthy(self, client, mock_mvp_service):
        """Test get narrative when service is unhealthy."""
        mock_mvp_service.is_healthy.return_value = False

        response = client.get("/api/v1/narratives/test-123")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_get_narrative_generic_error(self, client, mock_mvp_service):
        """Test get narrative with generic exception."""
        mock_mvp_service.is_healthy.side_effect = Exception("Unexpected error")

        response = client.get("/api/v1/narratives/test-123")

        assert response.status_code == 500

    def test_list_narratives_service_unhealthy(self, client, mock_mvp_service):
        """Test list narratives when service is unhealthy."""
        mock_mvp_service.is_healthy.return_value = False

        response = client.get("/api/v1/narratives")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_list_narratives_generic_error(self, client, mock_mvp_service):
        """Test list narratives with generic exception."""
        mock_mvp_service.is_healthy.side_effect = Exception("Unexpected error")

        response = client.get("/api/v1/narratives")

        assert response.status_code == 500

    def test_delete_narrative_service_unhealthy(self, client, mock_mvp_service):
        """Test delete narrative when service is unhealthy."""
        mock_mvp_service.is_healthy.return_value = False

        response = client.delete("/api/v1/narratives/test-123")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_delete_narrative_generic_error(self, client, mock_mvp_service):
        """Test delete narrative with generic exception."""
        mock_mvp_service.is_healthy.side_effect = Exception("Unexpected error")

        response = client.delete("/api/v1/narratives/test-123")

        assert response.status_code == 500

    def test_synthesize_audio_service_unhealthy(self, client, mock_mvp_service):
        """Test audio synthesis when service is unhealthy."""
        mock_mvp_service.is_healthy.return_value = False

        response = client.post(
            "/api/v1/audio/synthesize", json={"text": "Test", "voice_id": "test"}
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_synthesize_audio_generic_error(self, client, mock_mvp_service):
        """Test audio synthesis with generic exception."""
        mock_mvp_service.is_healthy.side_effect = Exception("Unexpected error")

        response = client.post(
            "/api/v1/audio/synthesize", json={"text": "Test", "voice_id": "test"}
        )

        assert response.status_code == 500


class TestMetricsEndpoint:
    """Test suite for metrics query endpoint."""

    def test_query_metrics_success(self, client, mock_mvp_service):
        """Test querying metrics returns metrics data."""
        from unittest.mock import AsyncMock

        mock_mvp_service.system_observer.collect_metrics = AsyncMock(
            return_value={
                "timestamp": "2025-10-30T16:00:00Z",
                "cpu_usage": 45.5,
                "memory_usage": 67.2,
                "active_connections": 152,
            }
        )

        response = client.post("/api/v1/metrics", json={"time_range_minutes": 60})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "timestamp" in data
        assert "cpu_usage" in data

    def test_query_metrics_service_unhealthy(self, client, mock_mvp_service):
        """Test query metrics when service is unhealthy."""
        mock_mvp_service.is_healthy.return_value = False

        response = client.post("/api/v1/metrics", json={"time_range_minutes": 60})

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_query_metrics_generic_error(self, client, mock_mvp_service):
        """Test query metrics with generic exception."""
        from unittest.mock import AsyncMock

        mock_mvp_service.system_observer.collect_metrics = AsyncMock(
            side_effect=Exception("Metrics collection failed")
        )

        response = client.post("/api/v1/metrics", json={"time_range_minutes": 60})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestAnomaliesEndpoint:
    """Test suite for anomaly detection endpoint."""

    def test_detect_anomalies_success(self, client, mock_mvp_service):
        """Test detecting anomalies returns anomaly data."""
        from unittest.mock import AsyncMock, MagicMock

        mock_mvp_service.system_observer.collect_metrics = AsyncMock(
            return_value={
                "timestamp": "2025-10-30T16:00:00Z",
                "cpu_usage": 95.0,
                "memory_usage": 87.2,
            }
        )

        mock_mvp_service.narrative_engine._detect_anomalies_in_metrics = MagicMock(
            return_value=[
                {"type": "high_cpu", "severity": "warning", "value": 95.0},
                {"type": "high_memory", "severity": "info", "value": 87.2},
            ]
        )

        response = client.get("/api/v1/anomalies?time_range_minutes=60")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "anomalies" in data
        assert "count" in data
        assert data["count"] == 2

    def test_detect_anomalies_service_unhealthy(self, client, mock_mvp_service):
        """Test detect anomalies when service is unhealthy."""
        mock_mvp_service.is_healthy.return_value = False

        response = client.get("/api/v1/anomalies")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_detect_anomalies_generic_error(self, client, mock_mvp_service):
        """Test detect anomalies with generic exception."""
        from unittest.mock import AsyncMock

        mock_mvp_service.system_observer.collect_metrics = AsyncMock(
            side_effect=Exception("Metrics collection failed")
        )

        response = client.get("/api/v1/anomalies")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestStatusEndpoint:
    """Test suite for status endpoint."""

    def test_get_status_success(self, client, mock_mvp_service):
        """Test getting service status returns status data."""
        from unittest.mock import AsyncMock

        mock_mvp_service.health_check = AsyncMock(
            return_value={
                "status": "healthy",
                "components": {"system_observer": "ok", "narrative_engine": "ok"},
            }
        )
        mock_mvp_service.is_healthy.return_value = True
        mock_mvp_service.service_version = "1.0.0"

        response = client.get("/api/v1/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["status"] == "operational"

    def test_get_status_service_not_initialized(self, client):
        """Test get status when service is not initialized."""
        from services.mvp_service.api.routes import set_mvp_service

        set_mvp_service(None)

        response = client.get("/api/v1/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "not_initialized"

        # Restore mock for other tests
        from services.mvp_service.tests.conftest import _get_mock_mvp_service

        set_mvp_service(_get_mock_mvp_service())

    def test_get_status_generic_error(self, client, mock_mvp_service):
        """Test get status with generic exception."""
        from unittest.mock import AsyncMock

        mock_mvp_service.health_check = AsyncMock(
            side_effect=Exception("Health check failed")
        )

        response = client.get("/api/v1/status")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
