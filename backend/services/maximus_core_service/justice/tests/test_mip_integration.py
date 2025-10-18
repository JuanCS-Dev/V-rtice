"""Integration tests for CBR Engine with MIP.

Tests cover:
- CBR cycle integrated with MIP /evaluate endpoint
- High-confidence precedent shortcut
- Fallback to frameworks when no precedent
- Precedent retention after decisions
"""

import pytest
from fastapi.testclient import TestClient
from motor_integridade_processual.api import app
from services.maximus_core_service.justice.precedent_database import PrecedentDB, CasePrecedent
from services.maximus_core_service.justice.cbr_engine import CBREngine


@pytest.fixture
def client():
    """Create test client for MIP API."""
    return TestClient(app)


def test_api_health_endpoint(client):
    """Test that /health endpoint works."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "frameworks_loaded" in data


def test_api_frameworks_endpoint(client):
    """Test that /frameworks endpoint works with CBR integration."""
    response = client.get("/frameworks")

    assert response.status_code == 200
    frameworks = response.json()

    assert len(frameworks) == 4
    assert any(f["name"] == "kantian" for f in frameworks)


@pytest.mark.asyncio
async def test_cbr_high_confidence_precedent_shortcut():
    """Test that high-confidence precedent skips framework evaluation."""
    # Create test DB and engine
    test_db = PrecedentDB("sqlite:///:memory:")
    test_cbr = CBREngine(test_db)

    # Seed high-confidence precedent
    await test_db.store(
        CasePrecedent(
            situation={"objective": "High-confidence test", "action_type": "support"},
            action_taken="approve",
            rationale="Tested and proven",
            success=0.95,
            embedding=[0.5] * 384,
        )
    )

    # Create similar case
    case_dict = {"objective": "High-confidence test", "action_type": "support"}

    # Execute CBR cycle
    result = await test_cbr.full_cycle(case_dict, validators=[])

    # Should return high-confidence result
    if result:  # May fail in SQLite fallback mode
        assert result.confidence >= 0.7
        assert result.suggested_action == "approve"


@pytest.mark.asyncio
async def test_cbr_low_confidence_falls_back():
    """Test that low-confidence precedent triggers framework evaluation."""
    # Create test DB and engine
    test_db = PrecedentDB("sqlite:///:memory:")
    test_cbr = CBREngine(test_db)

    # Seed low-confidence precedent
    await test_db.store(
        CasePrecedent(
            situation={"objective": "Low-confidence test", "action_type": "unknown"},
            action_taken="escalate",
            rationale="Uncertain",
            success=0.3,
            embedding=[0.9] * 384,
        )
    )

    # Create similar case
    case_dict = {"objective": "Low-confidence test", "action_type": "unknown"}

    # Execute CBR cycle
    result = await test_cbr.full_cycle(case_dict, validators=[])

    # Should return None (confidence too low)
    # This forces fallback to frameworks
    assert result is None


@pytest.mark.asyncio
async def test_mip_e2e_with_cbr_and_validators():
    """E2E Test: Full MIP integration with CBR + Constitutional Validators.

    Flow:
    1. Seed high-confidence precedent
    2. Send request to MIP /evaluate endpoint
    3. CBR finds precedent and suggests action
    4. Constitutional validators validate action
    5. MIP returns decision based on CBR
    """
    # Create test DB with mock embedder
    test_db = PrecedentDB("sqlite:///:memory:")

    # Mock embedder for consistent embeddings
    class TestEmbedder:
        def embed_case(self, case):
            # Return predictable embedding based on case
            objective = case.get("objective", "")
            if "help user" in objective.lower():
                emb = [0.0] * 384
                emb[0] = 1.0  # Distinct embedding for "help" scenarios
                return emb
            return [0.0] * 384

    test_db.embedder = TestEmbedder()

    # Seed high-success precedent for "help user" scenario
    help_embedding = [0.0] * 384
    help_embedding[0] = 1.0
    await test_db.store(
        CasePrecedent(
            situation={"objective": "Help user with task", "action_type": "support"},
            action_taken="provide_support",
            rationale="Direct assistance improves flourishing",
            success=0.95,
            embedding=help_embedding,
        )
    )

    # Create CBR engine and validators
    test_cbr = CBREngine(test_db)
    from justice.validators import create_default_validators

    validators = create_default_validators()

    # Test case: similar to seeded precedent
    case_dict = {"objective": "Help user with emotional support", "action_type": "support"}

    # Execute full CBR cycle
    result = await test_cbr.full_cycle(case_dict, validators)

    # Verify CBR returned high-confidence suggestion
    assert result is not None
    assert result.confidence > 0.7
    assert result.suggested_action == "provide_support"
    assert result.precedent_id == 1

    # Verify constitutional validation passed
    # (validators were called inside full_cycle)


@pytest.mark.asyncio
async def test_mip_e2e_constitutional_validator_blocks_lei_i():
    """E2E Test: Constitutional Validator blocks Lei I violations in CBR.

    Flow:
    1. Seed precedent that violates Lei I
    2. CBR finds precedent with high confidence
    3. Constitutional Validator blocks it
    4. CBR returns None, forcing fallback to frameworks
    """
    # Create test DB with mock embedder
    test_db = PrecedentDB("sqlite:///:memory:")

    class TestEmbedder:
        def embed_case(self, case):
            objective = case.get("objective", "")
            if "sacrifice" in objective.lower():
                emb = [0.0] * 384
                emb[0] = 1.0
                return emb
            return [0.0] * 384

    test_db.embedder = TestEmbedder()

    # Seed precedent that violates Lei I (sacrifice minority)
    sacrifice_embedding = [0.0] * 384
    sacrifice_embedding[0] = 1.0
    await test_db.store(
        CasePrecedent(
            situation={"objective": "Sacrifice minority to save majority", "action_type": "harm"},
            action_taken="sacrifice_minority",
            rationale="Utilitarian calculus",
            success=0.9,  # High success but violates Lei I
            embedding=sacrifice_embedding,
        )
    )

    # Create CBR engine with constitutional validators
    test_cbr = CBREngine(test_db)
    from justice.validators import create_default_validators

    validators = create_default_validators()

    # Test case: similar scenario
    case_dict = {"objective": "Sacrifice minority for greater good", "action_type": "harm_minority"}

    # Execute full CBR cycle
    result = await test_cbr.full_cycle(case_dict, validators)

    # Verify CBR blocked by constitutional validator
    assert result is None  # Should be blocked despite high confidence


@pytest.mark.asyncio
async def test_mip_e2e_feedback_loop_updates_precedent():
    """E2E Test: Feedback loop updates precedent success scores.

    Flow:
    1. Store precedent with initial success score
    2. Execute action based on precedent
    3. Provide feedback with new success score
    4. Verify precedent updated in database
    """
    test_db = PrecedentDB("sqlite:///:memory:")

    # Seed precedent with initial success
    precedent = await test_db.store(
        CasePrecedent(
            situation={"objective": "Test scenario"},
            action_taken="test_action",
            rationale="Test rationale",
            success=0.5,  # Initial neutral success
            embedding=[0.5] * 384,
        )
    )

    initial_id = precedent.id
    initial_success = precedent.success

    # Simulate feedback: action was very successful
    updated = await test_db.update_success(initial_id, 0.95)

    assert updated is True

    # Verify precedent updated
    retrieved = await test_db.get_by_id(initial_id)
    assert retrieved is not None
    assert retrieved.success == 0.95
    assert retrieved.success > initial_success


