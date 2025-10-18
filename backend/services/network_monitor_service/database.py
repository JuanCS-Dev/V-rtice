"""Database models for Network Monitor Service."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class NetworkEvent(Base):
    """Network event model."""
    
    __tablename__ = "network_events"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    source_ip = Column(String, nullable=False, index=True)
    destination_ip = Column(String, nullable=True)
    protocol = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    severity = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    ml_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Database connection
DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/vertice_network_monitor"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
