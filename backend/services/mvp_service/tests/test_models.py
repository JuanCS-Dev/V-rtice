"""Tests for MVP Pydantic models and MVPService.

Author: Vértice Platform Team
License: Proprietary
"""

import pytest
from services.mvp_service.models import (
    MVPService,
    NarrativeRequest,
    NarrativeResponse,
    NarrativeType,
)


class TestNarrativeType:
    """Test NarrativeType enum."""

    def test_narrative_type_values(self):
        """Test all narrative type enum values."""
        assert NarrativeType.REALTIME == "realtime"
        assert NarrativeType.SUMMARY == "summary"
        assert NarrativeType.ALERT == "alert"
        assert NarrativeType.BRIEFING == "briefing"


class TestNarrativeRequest:
    """Test NarrativeRequest model."""

    def test_valid_narrative_request(self):
        """Test creating valid narrative request."""
        req = NarrativeRequest(
            narrative_type=NarrativeType.REALTIME,
            time_range_minutes=120,
            focus_areas=["cpu", "memory"],
        )
        assert req.narrative_type == NarrativeType.REALTIME
        assert req.time_range_minutes == 120
        assert req.focus_areas == ["cpu", "memory"]

    def test_default_values(self):
        """Test default values are applied."""
        req = NarrativeRequest(narrative_type=NarrativeType.SUMMARY)
        assert req.time_range_minutes == 60
        assert req.focus_areas is None


class TestNarrativeResponse:
    """Test NarrativeResponse model."""

    def test_valid_narrative_response(self):
        """Test creating valid narrative response."""
        resp = NarrativeResponse(
            narrative="System is operating normally",
            metrics_analyzed=150,
            anomalies_detected=3,
        )
        assert resp.narrative == "System is operating normally"
        assert resp.metrics_analyzed == 150
        assert resp.anomalies_detected == 3
        assert resp.timestamp is not None

    def test_default_anomalies(self):
        """Test default anomalies value."""
        resp = NarrativeResponse(
            narrative="All systems operational", metrics_analyzed=200
        )
        assert resp.anomalies_detected == 0


class TestMVPService:
    """Test MVPService class initialization and methods."""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test MVP service initialization."""
        service = MVPService(
            service_name="MVP",
            service_version="1.0.0",
            maximus_endpoint="http://localhost:8000",
        )

        assert service.service_name == "MVP"
        assert service.service_version == "1.0.0"
        assert service.narrative_engine is None
        assert service.system_observer is None

    @pytest.mark.asyncio
    async def test_service_without_endpoint(self):
        """Test service initialization without maximus endpoint."""
        service = MVPService(service_name="MVP", service_version="1.0.0")

        assert service.service_name == "MVP"
        assert service.narrative_engine is None
        assert service.system_observer is None

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful service initialization."""
        from unittest.mock import AsyncMock, MagicMock, patch

        service = MVPService(service_name="MVP", service_version="1.0.0")

        with (
            patch("services.mvp_service.models.NarrativeEngine") as mock_engine_cls,
            patch("services.mvp_service.models.SystemObserver") as mock_observer_cls,
        ):

            # Mock NarrativeEngine
            mock_engine = MagicMock()
            mock_engine.initialize = AsyncMock(return_value=None)
            mock_engine_cls.return_value = mock_engine

            # Mock SystemObserver
            mock_observer = MagicMock()
            mock_observer.initialize = AsyncMock(return_value=None)
            mock_observer_cls.return_value = mock_observer

            # Mock register_tools_with_maximus
            service.register_tools_with_maximus = AsyncMock(return_value=None)

            result = await service.initialize()

            assert result is True
            assert service.narrative_engine is not None
            assert service.system_observer is not None

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test service initialization failure."""
        from unittest.mock import patch

        service = MVPService(service_name="MVP", service_version="1.0.0")

        with patch("services.mvp_service.models.NarrativeEngine") as mock_engine_cls:
            # Mock NarrativeEngine to raise exception
            mock_engine_cls.side_effect = Exception("Engine init failed")

            result = await service.initialize()

            assert result is False

    @pytest.mark.asyncio
    async def test_shutdown_with_components(self):
        """Test service shutdown with components initialized."""
        from unittest.mock import AsyncMock, MagicMock

        service = MVPService(service_name="MVP", service_version="1.0.0")

        # Mock components
        service.narrative_engine = MagicMock()
        service.narrative_engine.shutdown = AsyncMock(return_value=None)

        service.system_observer = MagicMock()
        service.system_observer.shutdown = AsyncMock(return_value=None)

        await service.shutdown()

        service.narrative_engine.shutdown.assert_called_once()
        service.system_observer.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_with_error(self):
        """Test service shutdown with error."""
        from unittest.mock import AsyncMock, MagicMock

        service = MVPService(service_name="MVP", service_version="1.0.0")

        # Mock component that raises exception
        service.narrative_engine = MagicMock()
        service.narrative_engine.shutdown = AsyncMock(
            side_effect=Exception("Shutdown failed")
        )

        # Should not raise exception
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_health_check_with_components(self):
        """Test health check with components initialized."""
        from unittest.mock import AsyncMock, MagicMock

        service = MVPService(service_name="MVP", service_version="1.0.0")

        # Mock get_base_health_info
        service.get_base_health_info = AsyncMock(
            return_value={"status": "healthy", "service": "MVP"}
        )

        # Mock narrative engine
        service.narrative_engine = MagicMock()
        service.narrative_engine.health_check = AsyncMock(
            return_value={"status": "ok", "model": "claude-sonnet-4.5-20250929"}
        )

        # Mock system observer
        service.system_observer = MagicMock()
        service.system_observer.health_check = AsyncMock(
            return_value={"status": "ok", "metrics_sources": 2}
        )

        health = await service.health_check()

        assert "components" in health
        assert "narrative_engine" in health["components"]
        assert "system_observer" in health["components"]
        assert health["components"]["narrative_engine"]["status"] == "ok"
        assert health["components"]["system_observer"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_check_without_components(self):
        """Test health check without components initialized."""
        from unittest.mock import AsyncMock

        service = MVPService(service_name="MVP", service_version="1.0.0")

        # Mock get_base_health_info
        service.get_base_health_info = AsyncMock(
            return_value={"status": "healthy", "service": "MVP"}
        )

        health = await service.health_check()

        assert "components" in health
        assert health["components"]["narrative_engine"]["status"] == "not_initialized"
        assert health["components"]["system_observer"]["status"] == "not_initialized"

    def test_get_tool_manifest(self):
        """Test tool manifest generation."""
        service = MVPService(service_name="MVP", service_version="1.0.0")

        tools = service._get_tool_manifest()

        assert isinstance(tools, list)
        assert len(tools) == 2

        # Check first tool (generate_narrative)
        generate_tool = tools[0]
        assert generate_tool["name"] == "generate_narrative"
        assert generate_tool["category"] == "vision"
        assert "narrative_type" in generate_tool["parameters"]

        # Check second tool (detect_anomalies)
        anomaly_tool = tools[1]
        assert anomaly_tool["name"] == "detect_anomalies"
        assert anomaly_tool["category"] == "analysis"
        assert "time_range_minutes" in anomaly_tool["parameters"]
