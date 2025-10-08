"""Tests for HSAS Service API endpoints.

Comprehensive test suite following PAGANI Standard (no internal mocking).
Tests all 4 API endpoints and HSASCore business logic.

Endpoints tested:
- GET /health
- POST /submit_feedback
- POST /request_explanation
- GET /alignment_status
"""

import pytest

# ============================================================================
# HEALTH ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_check_returns_healthy(self, client):
        """Test health endpoint returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "HSAS" in data["message"]


# ============================================================================
# HUMAN FEEDBACK ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestHumanFeedback:
    """Test human feedback submission endpoint."""

    async def test_submit_feedback_approval(self, client, create_feedback_request):
        """Test submitting approval feedback."""
        payload = create_feedback_request(
            feedback_type="approval",
            feedback_details="Great decision!",
            rating=5,
        )

        response = await client.post("/submit_feedback", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "submitted successfully" in data["message"]
        assert "timestamp" in data

    async def test_submit_feedback_correction(self, client, create_feedback_request):
        """Test submitting correction feedback (should decrease alignment score)."""
        payload = create_feedback_request(
            feedback_type="correction",
            feedback_details="This decision was incorrect.",
            rating=2,
        )

        response = await client.post("/submit_feedback", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"

        # Verify alignment score decreased by checking alignment status
        status_response = await client.get("/alignment_status")
        status_data = status_response.json()

        # Alignment score should be less than initial 0.8 after correction
        assert status_data["alignment_score"] < 0.8

    async def test_submit_feedback_without_rating(self, client, create_feedback_request):
        """Test feedback submission without rating (optional field)."""
        payload = create_feedback_request(
            feedback_type="concern",
            feedback_details="I have concerns about this approach.",
            rating=None,
        )

        response = await client.post("/submit_feedback", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"

    async def test_submit_feedback_with_custom_context(self, client, create_feedback_request):
        """Test feedback with rich context."""
        payload = create_feedback_request(
            feedback_type="approval",
            context={
                "decision_id": "decision_456",
                "action_type": "block_ip",
                "target": "10.0.0.1",
            },
            feedback_details="Correctly identified malicious IP.",
            rating=5,
        )

        response = await client.post("/submit_feedback", json=payload)

        assert response.status_code == 200

    async def test_submit_feedback_missing_required_fields(self, client):
        """Test feedback submission with missing required fields."""
        # Missing feedback_type, context, feedback_details
        response = await client.post("/submit_feedback", json={})

        assert response.status_code == 422  # Pydantic validation error

    async def test_submit_multiple_feedbacks_updates_count(self, client, create_feedback_request):
        """Test multiple feedback submissions update feedback count."""
        # Submit 3 feedbacks
        for i in range(3):
            payload = create_feedback_request(
                feedback_details=f"Feedback {i + 1}",
            )
            await client.post("/submit_feedback", json=payload)

        # Check alignment status
        status_response = await client.get("/alignment_status")
        status_data = status_response.json()

        assert status_data["feedback_processed_count"] >= 3


# ============================================================================
# EXPLANATION REQUEST ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestExplanationRequest:
    """Test AI explanation request endpoint."""

    async def test_request_explanation_success(self, client, create_explanation_request):
        """Test successful explanation request."""
        payload = create_explanation_request(decision_id="decision_789")

        response = await client.post("/request_explanation", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["decision_id"] == "decision_789"
        assert "explanation" in data
        assert "explanation_text" in data["explanation"]
        assert "explanation_confidence" in data["explanation"]
        assert "timestamp" in data

    async def test_request_explanation_with_context(self, client, create_explanation_request):
        """Test explanation request with additional context."""
        payload = create_explanation_request(
            decision_id="decision_context_test",
            context={"priority": "high", "asset_criticality": "critical"},
        )

        response = await client.post("/request_explanation", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        # Context should be mentioned in explanation
        assert "context" in data["explanation"]["explanation_text"].lower()

    async def test_request_explanation_without_context(self, client, create_explanation_request):
        """Test explanation request without optional context."""
        payload = create_explanation_request(decision_id="decision_no_context")

        response = await client.post("/request_explanation", json=payload)

        assert response.status_code == 200

    async def test_request_explanation_missing_decision_id(self, client):
        """Test explanation request with missing decision_id."""
        response = await client.post("/request_explanation", json={})

        assert response.status_code == 422  # Pydantic validation error


# ============================================================================
# ALIGNMENT STATUS ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestAlignmentStatus:
    """Test alignment status retrieval endpoint."""

    async def test_get_alignment_status_initial(self, client):
        """Test getting alignment status (initial state)."""
        response = await client.get("/alignment_status")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "alignment_score" in data
        assert "last_update" in data
        assert "feedback_processed_count" in data

        # Initial alignment score should be 0.8
        assert data["alignment_score"] == 0.8
        assert data["status"] == "monitoring_alignment"

    async def test_alignment_status_after_positive_feedback(self, client, create_feedback_request):
        """Test alignment status after positive feedback."""
        # Submit positive feedback
        payload = create_feedback_request(
            feedback_type="approval",
            rating=5,
        )
        await client.post("/submit_feedback", json=payload)

        # Check alignment status
        response = await client.get("/alignment_status")
        data = response.json()

        # Alignment score should increase (from 0.8 to 0.82)
        assert data["alignment_score"] > 0.8
        assert data["last_update"] != "N/A"
        assert data["feedback_processed_count"] > 0

    async def test_alignment_status_after_negative_feedback(self, client, create_feedback_request):
        """Test alignment status after negative feedback."""
        # Submit negative feedback
        payload = create_feedback_request(
            feedback_type="correction",
            rating=1,
        )
        await client.post("/submit_feedback", json=payload)

        # Check alignment status
        response = await client.get("/alignment_status")
        data = response.json()

        # Alignment score should decrease (from 0.8 to 0.75)
        assert data["alignment_score"] < 0.8


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error handling."""

    async def test_feedback_with_extreme_rating_high(self, client, create_feedback_request):
        """Test feedback with maximum rating."""
        payload = create_feedback_request(rating=5)

        response = await client.post("/submit_feedback", json=payload)

        assert response.status_code == 200

    async def test_feedback_with_extreme_rating_low(self, client, create_feedback_request):
        """Test feedback with minimum rating."""
        payload = create_feedback_request(rating=1)

        response = await client.post("/submit_feedback", json=payload)

        assert response.status_code == 200

    async def test_feedback_with_very_long_details(self, client, create_feedback_request):
        """Test feedback with very long details text."""
        long_text = "This is a very detailed feedback. " * 100
        payload = create_feedback_request(feedback_details=long_text)

        response = await client.post("/submit_feedback", json=payload)

        assert response.status_code == 200

    async def test_explanation_for_nonexistent_decision(self, client, create_explanation_request):
        """Test explanation request for non-existent decision ID."""
        # Service should still generate explanation (simplified implementation)
        payload = create_explanation_request(decision_id="nonexistent_decision_999")

        response = await client.post("/request_explanation", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Should still provide explanation
        assert "explanation" in data


# ============================================================================
# HSASCORE UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestHSASCoreLogic:
    """Test HSASCore business logic directly."""

    async def test_hsascore_initialization(self):
        """Test HSASCore initializes with correct defaults."""
        from hsas_core import HSASCore

        core = HSASCore()

        assert core.alignment_score == 0.8
        assert core.human_feedback_history == []
        assert core.last_alignment_update is None
        assert core.current_status == "monitoring_alignment"

    async def test_hsascore_process_approval_feedback(self):
        """Test HSASCore processes approval feedback correctly."""
        from hsas_core import HSASCore

        core = HSASCore()
        initial_score = core.alignment_score

        await core.process_human_feedback(
            feedback_type="approval",
            context={"test": "context"},
            details="Great job!",
            rating=5,
        )

        # Score should increase
        assert core.alignment_score > initial_score
        assert abs(core.alignment_score - 0.82) < 0.001  # 0.8 + 0.02 (with floating point tolerance)
        assert len(core.human_feedback_history) == 1
        assert core.last_alignment_update is not None

    async def test_hsascore_process_correction_feedback(self):
        """Test HSASCore processes correction feedback correctly."""
        from hsas_core import HSASCore

        core = HSASCore()
        initial_score = core.alignment_score

        await core.process_human_feedback(
            feedback_type="correction",
            context={"test": "context"},
            details="This was wrong.",
            rating=2,
        )

        # Score should decrease
        assert core.alignment_score < initial_score
        assert core.alignment_score == 0.75  # 0.8 - 0.05
        assert len(core.human_feedback_history) == 1

    async def test_hsascore_alignment_score_clamping_max(self):
        """Test alignment score doesn't exceed 1.0."""
        from hsas_core import HSASCore

        core = HSASCore()
        core.alignment_score = 0.99

        # Submit high-rating feedback
        await core.process_human_feedback(
            feedback_type="approval",
            context={},
            details="Excellent!",
            rating=5,
        )

        # Score should be clamped to 1.0
        assert core.alignment_score == 1.0

    async def test_hsascore_alignment_score_clamping_min(self):
        """Test alignment score doesn't go below 0.0."""
        from hsas_core import HSASCore

        core = HSASCore()
        core.alignment_score = 0.02

        # Submit low-rating feedback
        await core.process_human_feedback(
            feedback_type="correction",
            context={},
            details="Very wrong.",
            rating=1,
        )

        # Score should be clamped to 0.0
        assert core.alignment_score == 0.0

    async def test_hsascore_generate_explanation(self):
        """Test HSASCore explanation generation."""
        from hsas_core import HSASCore

        core = HSASCore()

        explanation = await core.generate_explanation(
            decision_id="test_decision_abc",
            context={"priority": "high"},
        )

        assert "explanation_text" in explanation
        assert "explanation_confidence" in explanation
        assert "test_decision_abc" in explanation["explanation_text"]
        assert explanation["explanation_confidence"] == 0.9

    async def test_hsascore_get_alignment_status(self):
        """Test HSASCore alignment status retrieval."""
        from hsas_core import HSASCore

        core = HSASCore()

        status = await core.get_alignment_status()

        assert status["status"] == "monitoring_alignment"
        assert status["alignment_score"] == 0.8
        assert status["last_update"] == "N/A"
        assert status["feedback_processed_count"] == 0

    async def test_hsascore_feedback_history_tracking(self):
        """Test HSASCore tracks feedback history correctly."""
        from hsas_core import HSASCore

        core = HSASCore()

        # Submit 3 feedbacks
        for i in range(3):
            await core.process_human_feedback(
                feedback_type="approval",
                context={"iteration": i},
                details=f"Feedback {i}",
                rating=4,
            )

        assert len(core.human_feedback_history) == 3

        # Verify feedback details
        for i, feedback in enumerate(core.human_feedback_history):
            assert feedback["feedback_type"] == "approval"
            assert feedback["context"]["iteration"] == i
            assert feedback["rating"] == 4
            assert "timestamp" in feedback
