"""Maximus Social Engineering Service - Database Module.

This module provides database interaction functionalities for the Maximus AI's
Social Engineering Service. It defines the database schema, handles connection
management, and provides CRUD operations for storing and retrieving social
engineering campaign data, simulated human profiles, and interaction logs.

Key functionalities include:
- Defining SQLAlchemy models for campaigns, targets, and interactions.
- Managing database sessions and connections.
- Storing and retrieving campaign configurations and results.
- Tracking simulated human responses and vulnerabilities.

This module is crucial for persisting social engineering simulation data,
allowing for historical analysis, learning from past campaigns, and improving
the effectiveness of simulated attacks and countermeasures.
"""

from datetime import datetime
from typing import Generator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from services.social_eng_service.config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Campaign(Base):
    """SQLAlchemy model for a social engineering campaign."""

    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="created")  # created, running, completed, cancelled
    scenario = Column(Text)
    target_group = Column(Text)

    interactions = relationship("Interaction", back_populates="campaign")


class Target(Base):
    """SQLAlchemy model for a simulated human target."""

    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    vulnerabilities = Column(Text)  # JSON string of vulnerabilities
    phishing_susceptibility = Column(Integer)  # 0-100

    interactions = relationship("Interaction", back_populates="target")


class Interaction(Base):
    """SQLAlchemy model for a simulated interaction with a target."""

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    target_id = Column(Integer, ForeignKey("targets.id"))
    timestamp = Column(DateTime, default=datetime.now)
    action = Column(String)  # e.g., email_sent, link_clicked, credential_entered
    details = Column(Text)  # JSON string of interaction details
    successful = Column(Boolean)

    campaign = relationship("Campaign", back_populates="interactions")
    target = relationship("Target", back_populates="interactions")


def create_db_and_tables():
    """Creates the database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    """Dependency that provides a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
