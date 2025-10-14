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
try:
    from pgvector.sqlalchemy import Vector
    from sqlalchemy.dialects.postgresql import ARRAY
    PGVECTOR_AVAILABLE = True
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
        if db_url is None:
            db_url = os.getenv("DATABASE_URL", "postgresql://maximus:password@localhost/maximus")

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Initialize embedder
        from justice.embeddings import CaseEmbedder
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
            from justice.embeddings import CaseEmbedder
            if isinstance(self.embedder, CaseEmbedder):
                case.embedding = self.embedder.embed_case(case.situation)

        session = self.Session()
        try:
            session.add(case)
            session.commit()
            session.refresh(case)
            return case
        finally:
            session.close()

    async def find_similar(self, query_embedding: List[float], limit: int = 5) -> List[CasePrecedent]:
        """Find similar cases using vector similarity search.

        Uses pgvector cosine distance if available, otherwise falls back to
        simple retrieval for testing.

        Args:
            query_embedding: 384-dim embedding vector
            limit: Maximum number of results

        Returns:
            List of similar CasePrecedent objects, ordered by similarity
        """
        session = self.Session()
        try:
            if PGVECTOR_AVAILABLE:
                # Use pgvector for real similarity search
                results = session.query(CasePrecedent).order_by(
                    CasePrecedent.embedding.cosine_distance(query_embedding)
                ).limit(limit).all()
            else:
                # Fallback: just return most recent cases for testing
                results = session.query(CasePrecedent).order_by(
                    CasePrecedent.created_at.desc()
                ).limit(limit).all()

            return results
        finally:
            session.close()

    async def get_by_id(self, precedent_id: int) -> Optional[CasePrecedent]:
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

    async def update_success(self, precedent_id: int, success_score: float) -> bool:
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
