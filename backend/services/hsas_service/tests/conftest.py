"""Shared test fixtures and configuration for HSAS Service tests.

This module provides reusable fixtures following PAGANI Standard:
- NO external dependencies to mock (service is self-contained!)
- Provide test data factories
- DO NOT mock internal business logic

Since HSAS Service has no database, auth, or external dependencies,
fixtures are minimal and focus on HTTP clients and test data.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def client():
    """Provides an async HTTP client for testing HSAS Service.

    No mocking needed - service is fully self-contained!

    Resets HSASCore state before each test to ensure test isolation.
    """
    import api
    from hsas_core import HSASCore

    # Reset HSASCore to initial state before each test
    api.hsas_core = HSASCore()

    transport = ASGITransport(app=api.app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac


# ============================================================================
# TEST DATA FACTORIES
# ============================================================================


@pytest.fixture
def create_feedback_request():
    """Factory for creating HumanFeedback request payloads."""

    def _create(
        feedback_type: str = "approval",
        context: dict = None,
        feedback_details: str = "Test feedback",
        rating: int = None,
    ):
        """Create a HumanFeedback request payload.

        Args:
            feedback_type: Type of feedback (approval, correction, concern)
            context: Context dict
            feedback_details: Detailed feedback text
            rating: Optional rating (1-5)

        Returns:
            Dict with HumanFeedback payload
        """
        return {
            "feedback_type": feedback_type,
            "context": context or {"decision_id": "test_decision"},
            "feedback_details": feedback_details,
            "rating": rating,
        }

    return _create


@pytest.fixture
def create_explanation_request():
    """Factory for creating ExplanationRequest payloads."""

    def _create(decision_id: str = "test_decision_123", context: dict = None):
        """Create an ExplanationRequest payload.

        Args:
            decision_id: ID of decision to explain
            context: Optional context dict

        Returns:
            Dict with ExplanationRequest payload
        """
        return {
            "decision_id": decision_id,
            "context": context,
        }

    return _create
