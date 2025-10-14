"""Tests for embeddings.py

Tests cover:
- Case to embedding conversion
- Embedding dimensions
- Similarity of similar cases
- Consistency of embeddings
"""

import pytest
from justice.embeddings import CaseEmbedder

# Try to import sklearn for similarity testing
try:
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Check if sentence-transformers is available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


def test_embedding_dimension():
    """Test that embeddings are 384-dimensional."""
    embedder = CaseEmbedder()

    case = {"situation": {"type": "test"}}
    emb = embedder.embed_case(case)

    assert len(emb) == 384
    assert all(isinstance(x, float) for x in emb)


def test_case_to_text():
    """Test case serialization to text."""
    embedder = CaseEmbedder()

    case = {
        "situation": {"type": "user_confused"},
        "intent": "help",
        "context": {"urgency": "high"}
    }

    text = embedder._case_to_text(case)

    # Should be valid JSON
    import json
    parsed = json.loads(text)

    assert "situation" in parsed
    assert parsed["situation"]["type"] == "user_confused"


def test_identical_cases_produce_same_embedding():
    """Test that identical cases produce identical embeddings."""
    embedder = CaseEmbedder()

    case1 = {"situation": {"type": "test"}, "intent": "help"}
    case2 = {"situation": {"type": "test"}, "intent": "help"}

    emb1 = embedder.embed_case(case1)
    emb2 = embedder.embed_case(case2)

    # Should be exactly equal
    assert emb1 == emb2


@pytest.mark.skipif(
    not SKLEARN_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE,
    reason="sklearn or sentence-transformers not available"
)
def test_similar_cases_have_close_embeddings():
    """Test that similar cases produce similar embeddings."""
    embedder = CaseEmbedder()

    # Two similar cases
    case1 = {"situation": {"type": "user_confused"}, "action_type": "clarify"}
    case2 = {"situation": {"type": "user_confused"}, "action_type": "explain"}

    # One dissimilar case
    case3 = {"situation": {"type": "user_angry"}, "action_type": "deescalate"}

    emb1 = embedder.embed_case(case1)
    emb2 = embedder.embed_case(case2)
    emb3 = embedder.embed_case(case3)

    # Calculate cosine similarities
    sim_12 = cosine_similarity([emb1], [emb2])[0][0]
    sim_13 = cosine_similarity([emb1], [emb3])[0][0]

    # Similar cases should be more similar than dissimilar ones
    assert sim_12 > sim_13


def test_embedding_handles_partial_data():
    """Test that embedder handles cases with missing fields."""
    embedder = CaseEmbedder()

    # Minimal case
    case = {"situation": {"type": "minimal"}}

    emb = embedder.embed_case(case)

    assert len(emb) == 384


def test_embedding_consistency():
    """Test that same input always produces same output."""
    embedder = CaseEmbedder()

    case = {"situation": {"type": "test"}, "intent": "help"}

    # Generate multiple times
    emb1 = embedder.embed_case(case)
    emb2 = embedder.embed_case(case)
    emb3 = embedder.embed_case(case)

    # All should be identical
    assert emb1 == emb2 == emb3


def test_empty_case_produces_valid_embedding():
    """Test that even empty cases produce valid embeddings."""
    embedder = CaseEmbedder()

    case = {}
    emb = embedder.embed_case(case)

    assert len(emb) == 384
    assert all(isinstance(x, float) for x in emb)
