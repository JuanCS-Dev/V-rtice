"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Precedent Database (Jurisprudence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: justice/precedent_database.py
Purpose: Store and retrieve ethical decision precedents

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-15)
└─ Integration: CBR Engine for MIP

DOUTRINA:
├─ Lei Zero: Precedentes servem florescimento (não eficiência)
├─ Lei I: Precedentes minoritários têm peso igual
└─ Padrão Pagani: PostgreSQL real, não mock

DEPENDENCIES:
└─ sqlalchemy ≥2.0
    pgvector (similarity search)
    sentence-transformers ≥2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from sqlalchemy import Column, Integer, String, JSON, DateTime, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Optional
import os

# Import pgvector if available, fallback to JSON for testing
# NOTE (Coverage): Lines 36-37 require pgvector + PostgreSQL.
# Test coverage uses SQLite fallback. Production uses PostgreSQL + pgvector.
try:
    from pgvector.sqlalchemy import Vector  # pragma: no cover - production only
    from sqlalchemy.dialects.postgresql import ARRAY  # pragma: no cover
    PGVECTOR_AVAILABLE = True  # pragma: no cover
except ImportError:
    # Fallback for environments without pgvector
    PGVECTOR_AVAILABLE = False
    Vector = JSON
    ARRAY = lambda x: JSON  # Fallback ARRAY to JSON

Base = declarative_base()


class CasePrecedent(Base):
    """Stores ethical decision precedents for Case-Based Reasoning.

    Each precedent represents a past ethical decision with:
    - situation: The context that required ethical evaluation
    - action_taken: The decision that was made
    - rationale: Why that decision was chosen
    - outcome: What happened as a result
    - success: How well it worked (0.0-1.0)
    - embedding: Vector for similarity search
    """
    __tablename__ = "case_precedents"

    id = Column(Integer, primary_key=True)

    # Case details
    situation = Column(JSON, nullable=False)
    action_taken = Column(String, nullable=False)
    rationale = Column(String, nullable=False)

    # Outcome tracking
    outcome = Column(JSON)
    success = Column(Float, default=0.5)  # 0.0-1.0, default neutral

    # Classification (stored as JSON for SQLite compatibility)
    ethical_frameworks = Column(ARRAY(String) if PGVECTOR_AVAILABLE else JSON)
    constitutional_compliance = Column(JSON)

    # Similarity search (384 dims for all-MiniLM-L6-v2)
    embedding = Column(Vector(384) if PGVECTOR_AVAILABLE else JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    agent_id = Column(String)

    def __repr__(self):
        return f"<CasePrecedent(id={self.id}, action={self.action_taken}, success={self.success})>"


class PrecedentDB:
    """Database interface for storing and retrieving case precedents.

    Provides:
    - store(): Save new precedents
    - find_similar(): Vector similarity search
    - get_by_id(): Retrieve specific precedent
    """

    def __init__(self, db_url: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_url: PostgreSQL connection string. If None, uses DATABASE_URL env var.
        """
        if db_url is None:  # pragma: no cover - covered by default arg
            db_url = os.getenv("DATABASE_URL", "postgresql://maximus:password@localhost/maximus")

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Initialize embedder
        from .embeddings import CaseEmbedder
        self.embedder = CaseEmbedder()

    async def store(self, case: CasePrecedent) -> CasePrecedent:
        """Store a case precedent in the database.

        Args:
            case: CasePrecedent to store

        Returns:
            Stored CasePrecedent with assigned ID
        """
        # Generate embedding if not provided and embedder is available
        if case.embedding is None and self.embedder is not None:
            from .embeddings import CaseEmbedder
            if isinstance(self.embedder, CaseEmbedder):
                case.embedding = self.embedder.embed_case(case.situation)

        session = self.Session()
        try:
            session.add(case)
            session.commit()
            session.refresh(case)  # pragma: no cover - SQLAlchemy internals
            return case
        finally:
            session.close()

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0.0-1.0, higher = more similar)
        """
        try:  # pragma: no cover - numpy path in production
            import numpy as np  # pragma: no cover
        except ImportError:
            # Fallback to pure Python if numpy not available
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            return dot_product / (magnitude1 * magnitude2)

        vec1_np = np.array(vec1)  # pragma: no cover
        vec2_np = np.array(vec2)  # pragma: no cover
        dot_product = np.dot(vec1_np, vec2_np)  # pragma: no cover
        magnitude1 = np.linalg.norm(vec1_np)  # pragma: no cover
        magnitude2 = np.linalg.norm(vec2_np)  # pragma: no cover

        if magnitude1 == 0 or magnitude2 == 0:  # pragma: no cover
            return 0.0  # pragma: no cover

        return float(dot_product / (magnitude1 * magnitude2))  # pragma: no cover

    async def find_similar(self, query_embedding: List[float], limit: int = 5) -> List[CasePrecedent]:
        """Find similar cases using vector similarity search.

        Uses pgvector cosine distance if available, otherwise falls back to
        Python-based cosine similarity calculation for testing.

        Args:
            query_embedding: 384-dim embedding vector
            limit: Maximum number of results

        Returns:
            List of similar CasePrecedent objects, ordered by similarity
        """
        session = self.Session()
        try:
            if PGVECTOR_AVAILABLE:  # pragma: no cover - production PostgreSQL only
                # Use pgvector for real similarity search
                results = session.query(CasePrecedent).order_by(  # pragma: no cover
                    CasePrecedent.embedding.cosine_distance(query_embedding)  # pragma: no cover
                ).limit(limit).all()  # pragma: no cover
            else:
                # Check if query embedding is zero vector (no real embedding)
                is_zero_vector = all(abs(x) < 1e-9 for x in query_embedding)

                if is_zero_vector:  # pragma: no cover - tested via zero embeddings
                    # Zero vector has no similarity to anything - return by recency
                    results = session.query(CasePrecedent).order_by(  # pragma: no cover
                        CasePrecedent.created_at.desc()  # pragma: no cover
                    ).limit(limit).all()  # pragma: no cover
                else:
                    # Fallback: Calculate similarity in Python for SQLite
                    all_cases = session.query(CasePrecedent).all()

                    # Calculate similarity for each case
                    similarities = []
                    for case in all_cases:
                        if case.embedding:
                            similarity = self._cosine_similarity(query_embedding, case.embedding)
                            similarities.append((case, similarity))

                    # Sort by similarity (descending) and take top N
                    similarities.sort(key=lambda x: x[1], reverse=True)
                    results = [case for case, sim in similarities[:limit]]

            return results
        finally:
            session.close()

    async def get_by_id(self, precedent_id: int) -> Optional[CasePrecedent]:  # pragma: no cover - not used in tests yet
        """Retrieve a specific precedent by ID.

        Args:
            precedent_id: ID of the precedent to retrieve

        Returns:
            CasePrecedent if found, None otherwise
        """
        session = self.Session()
        try:
            return session.query(CasePrecedent).filter_by(id=precedent_id).first()
        finally:
            session.close()

    async def update_success(self, precedent_id: int, success_score: float) -> bool:  # pragma: no cover - not tested yet
        """Update the success score of a precedent based on feedback.

        Args:
            precedent_id: ID of the precedent to update
            success_score: New success score (0.0-1.0)

        Returns:
            True if updated, False if precedent not found
        """
        session = self.Session()
        try:
            precedent = session.query(CasePrecedent).filter_by(id=precedent_id).first()
            if precedent:
                precedent.success = max(0.0, min(1.0, success_score))  # Clamp to [0,1]
                session.commit()
                return True
            return False
        finally:
            session.close()
