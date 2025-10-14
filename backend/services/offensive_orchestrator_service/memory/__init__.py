"""
Attack Memory System - Persistent storage and retrieval for offensive operations.

Components:
- PostgreSQL: Structured campaign data (relational)
- Qdrant: Vector embeddings for similarity search
- Embeddings: Semantic representation of campaigns

Architecture:
- Hybrid storage: Relational + Vector
- Similarity search: Find similar past campaigns
- Learning: Extract patterns and lessons
"""

from memory.attack_memory import AttackMemorySystem
from memory.database import DatabaseManager
from memory.vector_store import VectorStore
from memory.embeddings import EmbeddingGenerator


__all__ = [
    "AttackMemorySystem",
    "DatabaseManager",
    "VectorStore",
    "EmbeddingGenerator",
]
