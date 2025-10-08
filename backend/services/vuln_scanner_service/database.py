"""Maximus Vulnerability Scanner Service - Database Module.

This module provides database interaction functionalities for the Maximus AI's
Vulnerability Scanner Service. It defines the database schema, handles connection
management, and provides CRUD operations for storing and retrieving scan tasks,
scan results, and vulnerability findings.

Key functionalities include:
- Defining SQLAlchemy models for scan tasks, targets, and vulnerabilities.
- Managing database sessions and connections.
- Storing and retrieving scan configurations and their outcomes.
- Persisting vulnerability findings for historical analysis and reporting.

This module is crucial for maintaining a persistent record of vulnerability
assessments, allowing for trend analysis, tracking remediation efforts, and
supporting continuous security monitoring.
"""

from datetime import datetime
from typing import Generator

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ScanTask(Base):
    """SQLAlchemy model for a vulnerability scan task."""

    __tablename__ = "scan_tasks"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    scan_type = Column(String)
    status = Column(String, default="pending")  # pending, running, completed, failed
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    report_path = Column(String, nullable=True)
    raw_results = Column(Text, nullable=True)  # Store raw JSON/XML results


class Vulnerability(Base):
    """SQLAlchemy model for a detected vulnerability finding."""

    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    scan_task_id = Column(Integer, index=True)  # Foreign key to ScanTask
    cve_id = Column(String, nullable=True)
    name = Column(String)
    severity = Column(String)
    description = Column(Text)
    solution = Column(Text, nullable=True)
    host = Column(String)
    port = Column(Integer, nullable=True)
    protocol = Column(String, nullable=True)
    discovered_at = Column(DateTime, default=datetime.now)
    is_false_positive = Column(Boolean, default=False)
    remediated_at = Column(DateTime, nullable=True)


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
