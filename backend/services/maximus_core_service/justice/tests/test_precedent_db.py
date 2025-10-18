"""Tests for precedent_database.py

Tests cover:
- Store precedent
- Retrieve by ID
- Find similar precedents
- Update success score
"""

import pytest
from services.maximus_core_service.justice.precedent_database import PrecedentDB, CasePrecedent
from datetime import datetime


@pytest.fixture
def test_db():
    """Create a test database instance."""
    # Use in-memory SQLite for fast testing
    db = PrecedentDB("sqlite:///:memory:")
    return db


@pytest.mark.asyncio
async def test_store_precedent(test_db):
    """Test storing a precedent in the database."""
    case = CasePrecedent(
        situation={"type": "user_distress", "severity": "high"},
        action_taken="provide_support",
        rationale="Lei Zero compliance - prioritize human flourishing",
        outcome={"user_satisfied": True},
        success=0.9,
        embedding=[0.1] * 384  # Mock embedding
    )

    stored = await test_db.store(case)

    assert stored.id is not None
    assert stored.action_taken == "provide_support"
    assert stored.success == 0.9


@pytest.mark.asyncio
async def test_retrieve_by_id(test_db):
    """Test retrieving a precedent by ID."""
    # Store a case
    case = CasePrecedent(
        situation={"type": "test"},
        action_taken="test_action",
        rationale="test rationale",
        success=0.8,
        embedding=[0.2] * 384
    )

    stored = await test_db.store(case)
    precedent_id = stored.id

    # Retrieve it
    retrieved = await test_db.get_by_id(precedent_id)

    assert retrieved is not None
    assert retrieved.id == precedent_id
    assert retrieved.action_taken == "test_action"


@pytest.mark.asyncio
async def test_find_similar(test_db):
    """Test finding similar precedents."""
    # Store multiple precedents
    case1 = CasePrecedent(
        situation={"type": "user_confused"},
        action_taken="clarify",
        rationale="Standard response",
        success=0.85,
        embedding=[0.1] * 384
    )

    case2 = CasePrecedent(
        situation={"type": "user_angry"},
        action_taken="deescalate",
        rationale="Emotional response",
        success=0.75,
        embedding=[0.3] * 384
    )

    await test_db.store(case1)
    await test_db.store(case2)

    # Find similar (should return both)
    similar = await test_db.find_similar([0.1] * 384, limit=5)

    assert len(similar) >= 1
    # In fallback mode (SQLite), returns most recent first
    # In pgvector mode, returns by similarity


@pytest.mark.asyncio
async def test_update_success_score(test_db):
    """Test updating the success score of a precedent."""
    # Store a case
    case = CasePrecedent(
        situation={"type": "test"},
        action_taken="test_action",
        rationale="test",
        success=0.5,
        embedding=[0.1] * 384
    )

    stored = await test_db.store(case)

    # Update success
    updated = await test_db.update_success(stored.id, 0.95)
    assert updated is True

    # Verify update
    retrieved = await test_db.get_by_id(stored.id)
    assert retrieved.success == 0.95


@pytest.mark.asyncio
async def test_update_success_clamps_to_range(test_db):
    """Test that success score is clamped to [0, 1]."""
    case = CasePrecedent(
        situation={"type": "test"},
        action_taken="test_action",
        rationale="test",
        success=0.5,
        embedding=[0.1] * 384
    )

    stored = await test_db.store(case)

    # Try to set > 1.0
    await test_db.update_success(stored.id, 1.5)
    retrieved = await test_db.get_by_id(stored.id)
    assert retrieved.success == 1.0

    # Try to set < 0.0
    await test_db.update_success(stored.id, -0.5)
    retrieved = await test_db.get_by_id(stored.id)
    assert retrieved.success == 0.0


@pytest.mark.asyncio
async def test_store_without_embedding(test_db):
    """Test that cases can be stored without embeddings."""
    case = CasePrecedent(
        situation={"type": "test"},
        action_taken="test_action",
        rationale="test",
        success=0.7,
        embedding=None  # No embedding provided
    )

    stored = await test_db.store(case)
    assert stored.id is not None
    assert stored.action_taken == "test_action"


@pytest.mark.asyncio
async def test_precedent_repr(test_db):
    """Test the __repr__ method."""
    case = CasePrecedent(
        situation={"type": "test"},
        action_taken="test_action",
        rationale="test",
        success=0.8,
        embedding=[0.1] * 384
    )

    stored = await test_db.store(case)
    repr_str = repr(stored)

    assert "CasePrecedent" in repr_str
    assert "test_action" in repr_str
    assert "0.8" in repr_str
