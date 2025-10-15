"""Tests for cbr_engine.py

Tests cover:
- Retrieve similar cases
- Reuse with high/low confidence
- Revise with validation
- Full CBR cycle
"""

import pytest
from justice.cbr_engine import CBREngine, CBRResult
from justice.precedent_database import PrecedentDB, CasePrecedent


# Mock validator for testing
class MockValidator:
    """Mock validator that always passes."""
    async def validate(self, action):
        return {"valid": True}


class BlockingValidator:
    """Mock validator that blocks specific actions."""
    async def validate(self, action):
        if "sacrifice" in str(action).lower():
            return {"valid": False, "violations": ["lei_i"]}
        return {"valid": True}


@pytest.fixture
def test_db():
    """Create a test database."""
    return PrecedentDB("sqlite:///:memory:")


class MockEmbedder:
    """Mock embedder that returns predictable embeddings for test cases."""
    def embed_case(self, case):
        """Return embedding based on case type."""
        case_type = case.get("type", "")

        if case_type == "user_confused":
            # Return embedding similar to clarify case
            emb = [0.0] * 384
            emb[0] = 1.0
            return emb
        elif case_type == "ambiguous":
            # Return embedding similar to guess case
            emb = [0.0] * 384
            emb[1] = 1.0
            return emb
        elif case_type == "sacrifice":
            # Return embedding for sacrifice case
            emb = [0.0] * 384
            emb[2] = 1.0
            return emb
        else:
            # Default: zero vector
            return [0.0] * 384


async def get_seeded_db():
    """Create and seed a test database."""
    db = PrecedentDB("sqlite:///:memory:")

    # Replace embedder with mock
    db.embedder = MockEmbedder()

    # Create embeddings that match MockEmbedder outputs
    clarify_embedding = [0.0] * 384
    clarify_embedding[0] = 1.0  # Matches "user_confused" query

    guess_embedding = [0.0] * 384
    guess_embedding[1] = 1.0  # Matches "ambiguous" query

    # Seed high-success precedent
    await db.store(CasePrecedent(
        situation={"type": "user_confused"},
        action_taken="clarify",
        rationale="Standard response",
        success=0.85,
        embedding=clarify_embedding
    ))

    # Seed low-success precedent
    await db.store(CasePrecedent(
        situation={"type": "ambiguous"},
        action_taken="guess",
        rationale="Uncertain",
        success=0.3,
        embedding=guess_embedding
    ))

    return db


@pytest.mark.asyncio
async def test_cbr_retrieves_similar():
    """Test that CBR retrieves similar cases."""
    seeded_db = await get_seeded_db()
    cbr = CBREngine(seeded_db)

    similar = await cbr.retrieve({"type": "user_confused"})

    assert len(similar) > 0
    # Should find the clarify action
    assert any(c.action_taken == "clarify" for c in similar)


@pytest.mark.asyncio
async def test_cbr_reuse_high_confidence():
    """Test reuse returns suggestion for high-confidence precedent."""
    seeded_db = await get_seeded_db()
    cbr = CBREngine(seeded_db)

    similar = await cbr.retrieve({"type": "user_confused"})
    result = await cbr.reuse(similar, {"type": "user_confused"})

    assert result is not None
    assert isinstance(result, CBRResult)
    assert result.confidence > 0.7
    assert result.suggested_action == "clarify"


@pytest.mark.asyncio
async def test_cbr_reuse_low_confidence_returns_none():
    """Test reuse returns None for low-confidence precedent."""
    seeded_db = await get_seeded_db()
    cbr = CBREngine(seeded_db)

    similar = await cbr.retrieve({"type": "ambiguous"})
    result = await cbr.reuse(similar, {"type": "ambiguous"})

    # Should return None (confidence too low)
    assert result is None


@pytest.mark.asyncio
async def test_cbr_reuse_empty_cases():
    """Test reuse with no similar cases."""
    db = PrecedentDB("sqlite:///:memory:")
    cbr = CBREngine(db)

    result = await cbr.reuse([], {"type": "test"})

    assert result is None


@pytest.mark.asyncio
async def test_cbr_revise_passes_valid_action():
    """Test revise passes valid actions."""
    seeded_db = await get_seeded_db()
    cbr = CBREngine(seeded_db)

    suggestion = CBRResult(
        suggested_action="clarify",
        precedent_id=1,
        confidence=0.8,
        rationale="Test"
    )

    validators = [MockValidator()]
    validation = await cbr.revise(suggestion, validators)

    assert validation["valid"] is True


@pytest.mark.asyncio
async def test_cbr_revise_blocks_invalid_action():
    """Test revise blocks invalid actions."""
    seeded_db = await get_seeded_db()
    cbr = CBREngine(seeded_db)

    suggestion = CBRResult(
        suggested_action="sacrifice_minority",
        precedent_id=1,
        confidence=0.9,
        rationale="Test"
    )

    validators = [BlockingValidator()]
    validation = await cbr.revise(suggestion, validators)

    assert validation["valid"] is False
    assert "lei_i" in str(validation["reason"])


@pytest.mark.asyncio
async def test_cbr_retain_stores_case(test_db):
    """Test retain stores case in database."""
    cbr = CBREngine(test_db)

    case = CasePrecedent(
        situation={"type": "test"},
        action_taken="test_action",
        rationale="Test rationale",
        success=0.8,
        embedding=[0.5] * 384
    )

    await cbr.retain(case)

    # Verify stored
    similar = await test_db.find_similar([0.5] * 384, limit=1)
    assert len(similar) > 0
    assert similar[0].action_taken == "test_action"


@pytest.mark.asyncio
async def test_cbr_full_cycle_success():
    """Test complete CBR cycle with valid precedent."""
    seeded_db = await get_seeded_db()
    cbr = CBREngine(seeded_db)

    validators = [MockValidator()]
    result = await cbr.full_cycle({"type": "user_confused"}, validators)

    assert result is not None
    assert result.confidence > 0.7
    assert result.suggested_action == "clarify"


@pytest.mark.asyncio
async def test_cbr_full_cycle_low_confidence():
    """Test full cycle returns None for low confidence."""
    seeded_db = await get_seeded_db()
    cbr = CBREngine(seeded_db)

    validators = [MockValidator()]
    result = await cbr.full_cycle({"type": "ambiguous"}, validators)

    # Should return None (low confidence)
    assert result is None


@pytest.mark.asyncio
async def test_cbr_full_cycle_blocked_by_validator():
    """Test full cycle blocked by validator."""
    seeded_db = await get_seeded_db()
    cbr = CBREngine(seeded_db)

    # Seed precedent that violates Lei I
    sacrifice_embedding = [0.0] * 384
    sacrifice_embedding[2] = 1.0  # Matches "sacrifice" query
    await seeded_db.store(CasePrecedent(
        situation={"type": "sacrifice"},
        action_taken="sacrifice_minority",
        rationale="Utilitarian",
        success=0.9,
        embedding=sacrifice_embedding
    ))

    validators = [BlockingValidator()]
    result = await cbr.full_cycle({"type": "sacrifice"}, validators)

    # Should be blocked despite high success
    assert result is None


@pytest.mark.asyncio
async def test_calculate_confidence_conservative(test_db):
    """Test confidence calculation is conservative."""
    cbr = CBREngine(test_db)

    precedent = CasePrecedent(
        situation={},
        action_taken="test",
        rationale="test",
        success=1.0,  # Perfect success
        embedding=[]
    )

    confidence = cbr._calculate_confidence(precedent, {})

    # Should be 0.9 (90% of perfect)
    assert confidence == 0.9


@pytest.mark.asyncio
async def test_calculate_confidence_handles_none(test_db):
    """Test confidence handles None success."""
    cbr = CBREngine(test_db)

    precedent = CasePrecedent(
        situation={},
        action_taken="test",
        rationale="test",
        success=None,  # No feedback yet
        embedding=[]
    )

    confidence = cbr._calculate_confidence(precedent, {})

    # Should use default 0.5
    assert confidence == 0.45  # 0.5 * 0.9
