"""PENELOPE Health Endpoint Tests.

Tests for PENELOPE health check and root endpoints.
"""

from unittest.mock import MagicMock, patch


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_health_check_success(self, test_client):
        """Test health check with all components initialized."""
        with (
            patch("main.sophia_engine", MagicMock()),
            patch("main.praotes_validator", MagicMock()),
            patch("main.tapeinophrosyne_monitor", MagicMock()),
            patch("main.wisdom_base", MagicMock()),
            patch("main.observability_client", MagicMock()),
        ):

            response = test_client.get("/health")

            assert response.status_code == 200
            data = response.json()

            assert "status" in data
            assert data["status"] == "healthy"
            assert "components" in data
            assert "virtues_status" in data
            assert "sabbath_mode" in data
            assert "timestamp" in data

    def test_health_check_degraded(self, test_client):
        """Test health check with missing components."""
        with (
            patch("main.sophia_engine", None),
            patch("main.praotes_validator", None),
            patch("main.tapeinophrosyne_monitor", MagicMock()),
            patch("main.wisdom_base", MagicMock()),
            patch("main.observability_client", MagicMock()),
        ):

            response = test_client.get("/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "degraded"
            assert data["components"]["sophia_engine"] == "not_initialized"
            assert data["components"]["praotes_validator"] == "not_initialized"

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns service information."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "PENELOPE - Christian Autonomous Healing Service"
        assert "version" in data
        assert data["governance"] == "7_biblical_articles"
        assert "sabbath_mode" in data
        assert "virtues" in data
        assert len(data["virtues"]) == 7  # 7 Biblical Articles
        assert "endpoints" in data

    @patch("main.is_sabbath")
    def test_sabbath_mode_active(self, mock_is_sabbath, test_client):
        """Test health check shows sabbath mode when active."""
        mock_is_sabbath.return_value = True

        with (
            patch("main.sophia_engine", MagicMock()),
            patch("main.praotes_validator", MagicMock()),
            patch("main.tapeinophrosyne_monitor", MagicMock()),
            patch("main.wisdom_base", MagicMock()),
            patch("main.observability_client", MagicMock()),
        ):

            response = test_client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["sabbath_mode"] is True

    @patch("main.is_sabbath")
    def test_sabbath_mode_inactive(self, mock_is_sabbath, test_client):
        """Test health check shows sabbath mode when inactive."""
        mock_is_sabbath.return_value = False

        with (
            patch("main.sophia_engine", MagicMock()),
            patch("main.praotes_validator", MagicMock()),
            patch("main.tapeinophrosyne_monitor", MagicMock()),
            patch("main.wisdom_base", MagicMock()),
            patch("main.observability_client", MagicMock()),
        ):

            response = test_client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["sabbath_mode"] is False

    def test_virtues_status_in_health(self, test_client):
        """Test health check includes virtues status."""
        with (
            patch("main.sophia_engine", MagicMock()),
            patch("main.praotes_validator", MagicMock()),
            patch("main.tapeinophrosyne_monitor", MagicMock()),
            patch("main.wisdom_base", MagicMock()),
            patch("main.observability_client", MagicMock()),
        ):

            response = test_client.get("/health")

            assert response.status_code == 200
            data = response.json()

            virtues = data["virtues_status"]
            assert "sophia" in virtues
            assert "praotes" in virtues
            assert "tapeinophrosyne" in virtues
            assert virtues["sophia"] == "ok"
            assert virtues["praotes"] == "ok"
            assert virtues["tapeinophrosyne"] == "ok"
