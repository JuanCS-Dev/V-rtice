"""
Infrastructure Layer - SQLAlchemy Models

Database models using SQLAlchemy ORM.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class ExampleModel(Base):
    """SQLAlchemy model for ExampleEntity."""

    __tablename__ = "examples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ExampleModel(id={self.id}, name={self.name}, status={self.status})>"
