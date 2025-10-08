"""Tests for Analytics domain endpoints (Timeline & Risk Heatmap).

Tests analytics endpoints for time-series and risk distribution analysis
following PAGANI Standard (no internal mocking).

Endpoints tested:
- GET /audit/analytics/timeline
- GET /audit/analytics/risk-heatmap
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

# ============================================================================
# TIMELINE ANALYTICS TESTS
# ============================================================================


@pytest.mark.asyncio
class TestDecisionTimeline:
    """Test time-series analytics endpoint."""

    async def test_get_timeline_success(self, authenticated_client, mock_db):
        """Test successful timeline retrieval with default parameters."""
        # Mock timeline data
        now = datetime.utcnow()
        mock_timeline_data = [
            {
                "bucket": now - timedelta(hours=2),
                "total_decisions": 25,
                "avg_confidence": 0.85,
                "avg_latency": 250.0,
                "approved": 20,
                "rejected": 4,
                "escalated": 1,
            },
            {
                "bucket": now - timedelta(hours=1),
                "total_decisions": 30,
                "avg_confidence": 0.82,
                "avg_latency": 245.0,
                "approved": 25,
                "rejected": 3,
                "escalated": 2,
            },
        ]

        # Set up mock to return timeline data
        mock_db.pool.connection._timeline_data = mock_timeline_data

        response = await authenticated_client.get("/audit/analytics/timeline")

        assert response.status_code == 200
        data = response.json()

        assert data["hours_analyzed"] == 24  # Default
        assert data["bucket_minutes"] == 60  # Default
        assert data["data_points"] == 2
        assert len(data["timeline"]) == 2

        # Verify first bucket
        bucket = data["timeline"][0]
        assert bucket["total_decisions"] == 25
        assert bucket["avg_confidence"] == 0.85
        assert bucket["approved"] == 20
        assert bucket["rejected"] == 4
        assert bucket["escalated"] == 1

    async def test_get_timeline_custom_hours(self, authenticated_client, mock_db):
        """Test timeline with custom hours parameter."""
        mock_db.pool.connection._timeline_data = []

        response = await authenticated_client.get("/audit/analytics/timeline?hours=48&bucket_minutes=120")

        assert response.status_code == 200
        data = response.json()

        assert data["hours_analyzed"] == 48
        assert data["bucket_minutes"] == 120
        assert data["data_points"] == 0

    async def test_get_timeline_invalid_hours(self, authenticated_client):
        """Test timeline rejects invalid hours parameter."""
        # Hours must be >= 1 and <= 720
        response = await authenticated_client.get("/audit/analytics/timeline?hours=0")
        assert response.status_code == 422

        response = await authenticated_client.get("/audit/analytics/timeline?hours=1000")
        assert response.status_code == 422

    async def test_get_timeline_invalid_bucket(self, authenticated_client):
        """Test timeline rejects invalid bucket_minutes parameter."""
        # Bucket must be >= 5 and <= 1440
        response = await authenticated_client.get("/audit/analytics/timeline?bucket_minutes=1")
        assert response.status_code == 422

        response = await authenticated_client.get("/audit/analytics/timeline?bucket_minutes=2000")
        assert response.status_code == 422


# ============================================================================
# RISK HEATMAP TESTS
# ============================================================================


@pytest.mark.asyncio
class TestRiskHeatmap:
    """Test risk distribution heatmap endpoint."""

    async def test_get_heatmap_success(self, authenticated_client, mock_db):
        """Test successful heatmap retrieval."""
        # Mock heatmap data
        mock_heatmap_data = [
            {
                "decision_type": "offensive_action",
                "risk_level": "high",
                "count": 15,
                "avg_confidence": 0.88,
            },
            {
                "decision_type": "offensive_action",
                "risk_level": "medium",
                "count": 30,
                "avg_confidence": 0.85,
            },
            {
                "decision_type": "data_access",
                "risk_level": "low",
                "count": 50,
                "avg_confidence": 0.92,
            },
        ]

        # Set up mock to return heatmap data
        mock_db.pool.connection._heatmap_data = mock_heatmap_data

        response = await authenticated_client.get("/audit/analytics/risk-heatmap")

        assert response.status_code == 200
        data = response.json()

        assert data["hours_analyzed"] == 24  # Default
        assert len(data["heatmap"]) == 3

        # Verify first heatmap cell
        cell = data["heatmap"][0]
        assert cell["decision_type"] == "offensive_action"
        assert cell["risk_level"] == "high"
        assert cell["count"] == 15
        assert cell["avg_confidence"] == 0.88

    async def test_get_heatmap_custom_hours(self, authenticated_client, mock_db):
        """Test heatmap with custom hours parameter."""
        mock_db.pool.connection._heatmap_data = []

        response = await authenticated_client.get("/audit/analytics/risk-heatmap?hours=72")

        assert response.status_code == 200
        data = response.json()

        assert data["hours_analyzed"] == 72
        assert len(data["heatmap"]) == 0

    async def test_get_heatmap_invalid_hours(self, authenticated_client):
        """Test heatmap rejects invalid hours parameter."""
        response = await authenticated_client.get("/audit/analytics/risk-heatmap?hours=-1")
        assert response.status_code == 422

        response = await authenticated_client.get("/audit/analytics/risk-heatmap?hours=800")
        assert response.status_code == 422

    async def test_get_heatmap_role_based_access(self, client, mock_db, mock_auditor_user):
        """Test heatmap allows auditor role."""
        import api

        original_db = api.db
        api.db = mock_db

        # Override auth with auditor user
        api.app.dependency_overrides[api.get_current_user] = lambda: mock_auditor_user

        from httpx import ASGITransport

        transport = ASGITransport(app=api.app)
        async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
            mock_db.pool.connection._heatmap_data = []
            response = await ac.get("/audit/analytics/risk-heatmap")

            assert response.status_code == 200

        # Cleanup
        api.app.dependency_overrides.clear()
        api.db = original_db
