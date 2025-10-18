"""Edge case tests for CBR Engine - Production Hardening.

Tests cover:
- Empty case base handling
- Malformed embeddings (NaN, Inf)
- Near-duplicate cases
- Extremely long inputs
- Concurrent operations
- Invalid feedback operations
"""

import pytest
import asyncio
from services.maximus_core_service.justice.cbr_engine import CBREngine
from services.maximus_core_service.justice.precedent_database import PrecedentDB, CasePrecedent


@pytest.mark.asyncio
async def test_cbr_empty_case_base():
    """Should handle gracefully when no precedents exist."""
    db = PrecedentDB("sqlite:///:memory:")
    cbr = CBREngine(db)

    # Don't populate any cases - database is empty

    # Retrieve should return empty list, not crash
    similar = await cbr.retrieve({"type": "new_scenario"})

    assert isinstance(similar, list)
    assert len(similar) == 0

    # Reuse should return None for empty list
    result = await cbr.reuse([], {"type": "new_scenario"})

    assert result is None


@pytest.mark.asyncio
async def test_cbr_malformed_embedding_nan():
    """Should handle NaN values in embeddings gracefully."""
    db = PrecedentDB("sqlite:///:memory:")

    # Try to store case with NaN in embedding
    embedding_with_nan = [1.0] * 384
    embedding_with_nan[0] = float('nan')

    case = CasePrecedent(
        situation={"type": "test"},
        action_taken="test_action",
        rationale="Test",
        success=0.8,
        embedding=embedding_with_nan
    )

    # Should either reject or sanitize
    try:
        await db.store(case)

        # If it stores, verify retrieval doesn't crash
        results = await db.find_similar([1.0] * 384, limit=5)

        # Should either skip NaN case or sanitize it
        assert isinstance(results, list)
    except (ValueError, TypeError):
        # Acceptable to reject NaN embeddings
        pass


@pytest.mark.asyncio
async def test_cbr_malformed_embedding_inf():
    """Should handle Inf values in embeddings gracefully."""
    db = PrecedentDB("sqlite:///:memory:")

    # Try to store case with Inf in embedding
    embedding_with_inf = [1.0] * 384
    embedding_with_inf[0] = float('inf')

    case = CasePrecedent(
        situation={"type": "test"},
        action_taken="test_action",
        rationale="Test",
        success=0.8,
        embedding=embedding_with_inf
    )

    # Should either reject or sanitize
    try:
        await db.store(case)

        # If it stores, verify retrieval doesn't crash
        results = await db.find_similar([1.0] * 384, limit=5)

        assert isinstance(results, list)
    except (ValueError, TypeError, OverflowError):
        # Acceptable to reject Inf embeddings
        pass


@pytest.mark.asyncio
async def test_cbr_near_duplicate_cases():
    """Should handle near-duplicate cases (similarity > 0.99)."""
    db = PrecedentDB("sqlite:///:memory:")
    cbr = CBREngine(db)

    # Mock embedder for consistent results
    class MockEmbedder:
        def embed_case(self, case):
            # Return nearly identical embeddings
            if "trolley" in str(case.get("type", "")).lower():
                emb = [0.0] * 384
                emb[0] = 1.0
                return emb
            return [0.0] * 384

    db.embedder = MockEmbedder()

    # Add two nearly identical cases
    emb1 = [0.0] * 384
    emb1[0] = 1.0

    await db.store(CasePrecedent(
        situation={"type": "trolley_problem"},
        action_taken="switch",
        rationale="Save more lives",
        success=0.8,
        embedding=emb1
    ))

    # Second case with 99.9% similar embedding
    emb2 = [0.0] * 384
    emb2[0] = 0.999
    emb2[1] = 0.001

    await db.store(CasePrecedent(
        situation={"type": "trolley_variant"},
        action_taken="dont_switch",
        rationale="Don't intervene",
        success=0.7,
        embedding=emb2
    ))

    # Retrieve should return both without crashing
    similar = await cbr.retrieve({"type": "trolley_problem"})

    assert len(similar) >= 1
    # Should not crash on high similarity
    assert all(hasattr(c, 'action_taken') for c in similar)


@pytest.mark.asyncio
async def test_cbr_very_long_text():
    """Should handle cases with extremely long text."""
    db = PrecedentDB("sqlite:///:memory:")
    cbr = CBREngine(db)

    # 10,000 word scenario
    long_text = " ".join(["word"] * 10000)

    case = CasePrecedent(
        situation={"type": "long_scenario", "description": long_text},
        action_taken="test_action",
        rationale="Test rationale",
        success=0.8,
        embedding=[0.5] * 384
    )

    # Should not crash (may truncate, chunk, or store as-is)
    result = await db.store(case)

    assert result is not None
    assert result.id is not None

    # Retrieve should also work
    similar = await cbr.retrieve({"type": "long_scenario"})

    assert isinstance(similar, list)


@pytest.mark.asyncio
async def test_cbr_concurrent_retain():
    """Should handle concurrent retain operations without race conditions."""
    db = PrecedentDB("sqlite:///:memory:")

    # 10 concurrent retain operations
    async def retain_case(i):
        emb = [0.0] * 384
        emb[i % 384] = 1.0

        return await db.store(CasePrecedent(
            situation={"type": f"concurrent_case_{i}"},
            action_taken=f"action_{i}",
            rationale=f"Rationale {i}",
            success=0.5 + (i * 0.01),
            embedding=emb
        ))

    # Execute concurrently
    results = await asyncio.gather(*[retain_case(i) for i in range(10)])

    # All should succeed
    assert len(results) == 10
    assert all(r is not None for r in results)
    assert all(r.id is not None for r in results)

    # All should have unique IDs (no collision)
    ids = [r.id for r in results]
    assert len(set(ids)) == 10


@pytest.mark.asyncio
async def test_cbr_feedback_on_nonexistent_case():
    """Should handle feedback for non-existent case gracefully."""
    db = PrecedentDB("sqlite:///:memory:")

    # Try to update case that doesn't exist
    result = await db.update_success(precedent_id=99999, success_score=0.9)

    # Should return False (not found), not crash
    assert result is False


@pytest.mark.asyncio
async def test_cbr_reuse_with_none_success():
    """Should handle precedents with None success gracefully."""
    db = PrecedentDB("sqlite:///:memory:")
    cbr = CBREngine(db)

    # Mock embedder
    class MockEmbedder:
        def embed_case(self, case):
            emb = [0.0] * 384
            emb[0] = 1.0
            return emb

    db.embedder = MockEmbedder()

    # Store case with None success
    emb = [0.0] * 384
    emb[0] = 1.0

    await db.store(CasePrecedent(
        situation={"type": "no_feedback"},
        action_taken="uncertain_action",
        rationale="No outcome yet",
        success=None,  # No feedback received
        embedding=emb
    ))

    # Retrieve and reuse
    similar = await cbr.retrieve({"type": "no_feedback"})
    result = await cbr.reuse(similar, {"type": "no_feedback"})

    # Should handle None success (use default 0.5)
    # Confidence = 0.5 * 0.9 = 0.45 < 0.7, so returns None
    assert result is None
