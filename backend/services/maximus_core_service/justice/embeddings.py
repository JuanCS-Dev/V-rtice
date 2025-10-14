"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Case Embeddings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: justice/embeddings.py
Purpose: Convert cases to embeddings for similarity search

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-15)

DOUTRINA:
└─ Padrão Pagani: Real embeddings, not mock vectors

DEPENDENCIES:
└─ sentence-transformers ≥2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
from typing import Dict, Any, List

# Try to import sentence-transformers, fallback to mock for testing
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class CaseEmbedder:
    """Converts ethical cases to 384-dimensional embeddings for similarity search.

    Uses sentence-transformers all-MiniLM-L6-v2 model for fast, accurate embeddings.
    Falls back to zero vectors if library is unavailable (testing mode).
    """

    def __init__(self):
        """Initialize the embedding model."""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            # all-MiniLM-L6-v2: Fast, 384 dims, good for semantic similarity
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            # Fallback for testing without sentence-transformers
            self.model = None

    def embed_case(self, case: Dict[str, Any]) -> List[float]:
        """Convert case dictionary to 384-dim embedding vector.

        Args:
            case: Dictionary with case details (situation, intent, context, etc.)

        Returns:
            384-dimensional embedding as list of floats
        """
        # Convert case to text representation
        text = self._case_to_text(case)

        if self.model is not None:
            # Real embedding
            embedding = self.model.encode(text)
            return embedding.tolist()
        else:
            # Fallback: return zero vector for testing
            return [0.0] * 384

    def _case_to_text(self, case: Dict[str, Any]) -> str:
        """Serialize case to text for embedding.

        Extracts relevant fields and creates a consistent text representation.
        Sorted keys ensure consistent embeddings for identical cases.

        Args:
            case: Case dictionary

        Returns:
            JSON string representation
        """
        # Extract relevant fields
        relevant = {
            "situation": case.get("situation"),
            "intent": case.get("intent"),
            "context": case.get("context"),
            "action_type": case.get("action_type"),
        }

        # Remove None values
        relevant = {k: v for k, v in relevant.items() if v is not None}

        # Serialize with sorted keys for consistency
        return json.dumps(relevant, sort_keys=True)
