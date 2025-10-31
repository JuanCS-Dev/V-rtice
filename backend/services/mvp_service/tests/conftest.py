"""Pytest configuration and fixtures for MVP tests.

Author: Vértice Platform Team
License: Proprietary
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routes import set_mvp_service
from main import app


@pytest.fixture
def mock_mvp_service():
    """Create a mock MVP service for testing."""
    service = MagicMock()

    # Mock narrative generator
    service.narrative_generator = MagicMock()
    service.narrative_generator.generate = AsyncMock(
        return_value={
            "narrative_id": "mvp-narr-test-123",
            "narrative_text": "Today I observed 127 service interactions...",
            "word_count": 67,
            "tone": "reflective",
            "nqs": 87,
        }
    )

    # Mock audio synthesizer
    service.audio_synthesizer = MagicMock()
    service.audio_synthesizer.synthesize = AsyncMock(
        return_value={
            "audio_url": "/audio/test-123.mp3",
            "duration_seconds": 28.5,
            "aqs": 93,
        }
    )

    # Mock knowledge graph client
    service.knowledge_graph_client = MagicMock()
    service.knowledge_graph_client.get_consciousness_snapshot = AsyncMock(
        return_value={
            "snapshot_id": "cs-test-2025-10-30",
            "event_count": 150,
            "eci": 0.958,
        }
    )

    # Mock system observer
    service.system_observer = MagicMock()
    service.system_observer.collect_metrics = AsyncMock(
        return_value={
            "timestamp": "2025-10-30T16:00:00Z",
            "cpu_usage": 45.5,
            "memory_usage": 67.2,
            "active_connections": 152,
        }
    )

    # Mock narrative engine
    service.narrative_engine = MagicMock()
    service.narrative_engine._detect_anomalies_in_metrics = MagicMock(return_value=[])

    # Mock service attributes
    service.service_version = "1.0.0"

    # Mock health check
    service.is_healthy = MagicMock(return_value=True)
    service.health_check = AsyncMock(
        return_value={
            "status": "healthy",
            "components": {
                "narrative_generator": "ok",
                "audio_synthesizer": "ok",
                "knowledge_graph": "ok",
                "system_observer": "ok",
                "narrative_engine": "ok",
            },
        }
    )

    return service


def _get_mock_mvp_service():
    """Helper function to get a fresh mock MVP service for test restoration."""
    service = MagicMock()

    # Mock narrative generator
    service.narrative_generator = MagicMock()
    service.narrative_generator.generate = AsyncMock(
        return_value={
            "narrative_id": "mvp-narr-test-123",
            "narrative_text": "Today I observed 127 service interactions...",
            "word_count": 67,
            "tone": "reflective",
            "nqs": 87,
        }
    )

    # Mock system observer
    service.system_observer = MagicMock()
    service.system_observer.collect_metrics = AsyncMock(
        return_value={
            "timestamp": "2025-10-30T16:00:00Z",
            "cpu_usage": 45.5,
            "memory_usage": 67.2,
            "active_connections": 152,
        }
    )

    # Mock narrative engine
    service.narrative_engine = MagicMock()
    service.narrative_engine._detect_anomalies_in_metrics = MagicMock(return_value=[])

    # Mock service attributes
    service.service_version = "1.0.0"

    # Mock health check
    service.is_healthy = MagicMock(return_value=True)
    service.health_check = AsyncMock(
        return_value={
            "status": "healthy",
            "components": {
                "narrative_generator": "ok",
                "system_observer": "ok",
                "narrative_engine": "ok",
            },
        }
    )

    return service


@pytest.fixture
def client(mock_mvp_service):
    """Create a test client with mocked MVP service."""
    set_mvp_service(mock_mvp_service)
    return TestClient(app)


@pytest.fixture
def sample_narrative_request():
    """Sample narrative generation request data."""
    return {
        "consciousness_snapshot_id": "cs-2025-10-30-14-23-45",
        "narrative_type": "daily_summary",
        "tone": "reflective",
        "duration_target_seconds": 30,
        "include_audio": True,
    }
