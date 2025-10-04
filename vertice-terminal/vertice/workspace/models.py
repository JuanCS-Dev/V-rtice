"""
SQLAlchemy Models for Vértice Workspace
========================================

Database schema for persistent state management.

Tables:
- projects: Top-level container for engagements
- hosts: Discovered target systems
- ports: Open/closed ports on hosts
- vulnerabilities: CVEs, misconfigurations, weaknesses
- credentials: Captured/cracked credentials
- notes: Free-form analyst notes
- evidence: Files (screenshots, pcaps, logs)
- events: Audit trail + triggerable events
- suggestions: AI-generated next steps
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    ForeignKey, DateTime, JSON, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Project(Base):
    """
    Top-level container for security engagement.

    A project represents a penetration test, security assessment,
    or bug bounty program with defined scope and timeline.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    scope = Column(JSON)  # List of target CIDRs/domains
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(
        String,
        CheckConstraint("status IN ('active', 'completed', 'archived')"),
        default="active"
    )

    # Relationships
    hosts = relationship("Host", back_populates="project", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="project", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="project", cascade="all, delete-orphan")
    suggestions = relationship("Suggestion", back_populates="project", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(name='{self.name}', status='{self.status}')>"


class Host(Base):
    """
    Discovered target system (IP address).

    Represents a single host discovered during reconnaissance.
    Contains OS information, hostname, and state.
    """
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    ip_address = Column(String, nullable=False, index=True)
    hostname = Column(String)
    mac_address = Column(String)
    os_family = Column(String)  # Linux, Windows, etc.
    os_version = Column(String)
    state = Column(
        String,
        CheckConstraint("state IN ('up', 'down', 'unknown')"),
        default="unknown"
    )
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="hosts")
    ports = relationship("Port", back_populates="host", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="host", cascade="all, delete-orphan")
    credentials = relationship("Credential", back_populates="host", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Host(ip='{self.ip_address}', hostname='{self.hostname}')>"


class Port(Base):
    """
    Open/closed port on a host.

    Represents a single port discovered during scanning.
    Includes service detection and version information.
    """
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False, index=True)
    port = Column(Integer, nullable=False)
    protocol = Column(
        String,
        CheckConstraint("protocol IN ('tcp', 'udp', 'sctp')"),
        default="tcp"
    )
    state = Column(
        String,
        CheckConstraint("state IN ('open', 'closed', 'filtered')"),
        default="open"
    )
    service = Column(String)  # http, ssh, mysql, etc.
    version = Column(String)  # Apache 2.4.41, OpenSSH 7.4, etc.
    banner = Column(Text)  # Raw banner grab
    discovered_by = Column(String)  # Tool that discovered it (nmap, masscan, etc.)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    host = relationship("Host", back_populates="ports")

    def __repr__(self):
        return f"<Port(port={self.port}/{self.protocol}, service='{self.service}')>"


class Vulnerability(Base):
    """
    Security vulnerability (CVE, misconfiguration, weakness).

    Represents a discovered vulnerability with severity,
    exploitability, and remediation information.
    """
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), index=True)
    port_id = Column(Integer, ForeignKey("ports.id"))
    cve_id = Column(String, index=True)  # CVE-2021-44228, etc.
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(
        String,
        CheckConstraint("severity IN ('critical', 'high', 'medium', 'low', 'info')"),
        index=True
    )
    cvss_score = Column(Float)
    exploitable = Column(Boolean, default=False)
    exploit_available = Column(Text)  # Metasploit module, ExploitDB ID, etc.
    remediation = Column(Text)
    discovered_by = Column(String)  # Tool/method
    discovered_at = Column(DateTime, default=datetime.utcnow)
    validated = Column(Boolean, default=False)  # Manually confirmed?

    # Relationships
    host = relationship("Host", back_populates="vulnerabilities")

    def __repr__(self):
        return f"<Vulnerability(cve='{self.cve_id}', severity='{self.severity}')>"


class Credential(Base):
    """
    Captured or cracked credential.

    Stores usernames, passwords, and hashes discovered
    during penetration testing.
    """
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), index=True)
    username = Column(String)
    password = Column(String)
    hash = Column(String)
    hash_type = Column(String)  # NTLM, bcrypt, MD5, etc.
    service = Column(String)  # SSH, RDP, SMB, HTTP, etc.
    validated = Column(Boolean, default=False)  # Tested and confirmed working?
    discovered_by = Column(String)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    host = relationship("Host", back_populates="credentials")

    def __repr__(self):
        return f"<Credential(username='{self.username}', service='{self.service}')>"


class Note(Base):
    """
    Free-form analyst note.

    Allows analysts to add comments/observations to projects,
    hosts, ports, or vulnerabilities.
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    target_type = Column(String)  # 'project', 'host', 'port', 'vuln'
    target_id = Column(Integer)  # ID of the target object
    content = Column(Text, nullable=False)
    author = Column(String)  # Username of analyst
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="notes")

    def __repr__(self):
        return f"<Note(target_type='{self.target_type}', author='{self.author}')>"


class Evidence(Base):
    """
    Evidence file (screenshot, pcap, log).

    Metadata for files stored in evidence/ directory.
    """
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    file_path = Column(String, nullable=False)  # Relative path from project root
    file_type = Column(String)  # 'pcap', 'screenshot', 'log', 'exploit'
    description = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="evidence")

    def __repr__(self):
        return f"<Evidence(file_type='{self.file_type}', path='{self.file_path}')>"


class Event(Base):
    """
    Audit trail event / triggerable event.

    Records all significant actions for audit purposes.
    Also used to trigger AI analysis and notifications.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)  # 'host_discovered', 'vuln_found', etc.
    payload = Column(JSON)  # Event data (flexible)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    project = relationship("Project", back_populates="events")

    def __repr__(self):
        return f"<Event(type='{self.event_type}', timestamp='{self.timestamp}')>"


class Suggestion(Base):
    """
    AI-generated suggestion for next steps.

    Maximus AI analyzes workspace state and recommends
    logical next actions to the analyst.
    """
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    suggestion_text = Column(Text, nullable=False)
    reasoning = Column(Text)  # Why this suggestion?
    priority = Column(
        String,
        CheckConstraint("priority IN ('high', 'medium', 'low')"),
        default="medium"
    )
    status = Column(
        String,
        CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'completed')"),
        default="pending"
    )
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="suggestions")

    def __repr__(self):
        return f"<Suggestion(priority='{self.priority}', status='{self.status}')>"
