"""Database for HCL Knowledge Base Service."""

from datetime import datetime
from typing import Optional
import os

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class HCLDataEntry(Base):
    """HCL data entry model."""
    
    __tablename__ = "hcl_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_type = Column(String, nullable=False, index=True)  # METRICS, ANALYSIS, PLAN, EXECUTION
    data = Column(JSON, nullable=False)
    entry_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# Database connection
DATABASE_URL = os.environ["DATABASE_URL"]

# Use psycopg2 (sync) instead of asyncpg
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

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
