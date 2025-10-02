
import datetime
from sqlalchemy import (Column, String, Integer, DateTime, Text, JSON, ForeignKey, Enum as SQLAlchemyEnum)
from sqlalchemy.orm import relationship
from database import Base
import enum

class ScanStatus(enum.Enum):
    QUEUED = "queued"
    SCANNING = "scanning"
    COMPLETED = "completed"
    FAILED = "failed"

class Severity(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, index=True)
    target = Column(String, index=True)
    scan_type = Column(String)
    status = Column(SQLAlchemyEnum(ScanStatus), default=ScanStatus.QUEUED)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scans.id"))
    host = Column(String)
    port = Column(Integer)
    service = Column(String)
    cve_id = Column(String, nullable=True, index=True)
    severity = Column(String, default="info")  # Changed from Enum to String to avoid migration issues
    description = Column(Text)
    recommendation = Column(Text)
    exploit_available = Column(String, nullable=True)

    scan = relationship("Scan", back_populates="vulnerabilities")

class CommonExploit(Base):
    __tablename__ = "common_exploits"

    cve_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    severity = Column(String)  # Changed from Enum to String
    metasploit_module = Column(String, nullable=True)
