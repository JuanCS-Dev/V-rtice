# 🗄️ WORKSPACE ARCHITECTURE: Persistent State Management
## The "Brain" of Vértice - Single Source of Truth for Security Operations

> **Objective**: Design a persistent, queryable, versioned state management system that stores all findings, context, and intelligence for security engagements.

---

## 📊 EXECUTIVE SUMMARY

### The Problem: Context Loss
Current security workflows suffer from **ephemeral state**:
- Nmap scan → XML file → manually imported to Metasploit
- Findings scattered across files, terminals, notes
- No queryable history
- No correlation across tools
- Context switching nightmare

### The Solution: Persistent Workspace
**Vértice Workspace** = SQLite-based, Git-versioned,

 queryable database for entire engagement:
- **Single source of truth** for all findings
- **Queryable via SQL or NL** ("show SSH servers with weak auth")
- **Versioned via Git** (audit trail, rollback, collaboration)
- **Event-driven** (triggers AI analysis, notifications)

---

## 🏗️ ARCHITECTURE

### Database Schema (SQLite)

```sql
-- Projects: Top-level container for engagements
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    scope TEXT,  -- JSON array of target CIDRs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('active', 'completed', 'archived')) DEFAULT 'active'
);

-- Hosts: Discovered target systems
CREATE TABLE hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    hostname TEXT,
    mac_address TEXT,
    os_family TEXT,
    os_version TEXT,
    state TEXT CHECK(state IN ('up', 'down', 'unknown')) DEFAULT 'unknown',
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, ip_address)
);

-- Ports: Open/closed ports on hosts
CREATE TABLE ports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT CHECK(protocol IN ('tcp', 'udp', 'sctp')) DEFAULT 'tcp',
    state TEXT CHECK(state IN ('open', 'closed', 'filtered')) DEFAULT 'open',
    service TEXT,
    version TEXT,
    banner TEXT,
    discovered_by TEXT,  -- Tool that discovered it (nmap, masscan, etc.)
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
    UNIQUE(host_id, port, protocol)
);

-- Vulnerabilities: CVEs, misconfigurations, weaknesses
CREATE TABLE vulnerabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER,
    port_id INTEGER,
    cve_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low', 'info')),
    cvss_score REAL,
    exploitable BOOLEAN DEFAULT 0,
    exploit_available TEXT,  -- Metasploit module, ExploitDB ID, etc.
    remediation TEXT,
    discovered_by TEXT,  -- Tool/method
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated BOOLEAN DEFAULT 0,  -- Manually confirmed?
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
    FOREIGN KEY (port_id) REFERENCES ports(id) ON DELETE SET NULL
);

-- Credentials: Captured/cracked credentials
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER,
    username TEXT,
    password TEXT,
    hash TEXT,
    hash_type TEXT,  -- NTLM, bcrypt, etc.
    service TEXT,    -- SSH, RDP, SMB, HTTP, etc.
    validated BOOLEAN DEFAULT 0,
    discovered_by TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE
);

-- Notes: Free-form analyst notes
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    target_type TEXT,  -- 'project', 'host', 'port', 'vuln'
    target_id INTEGER,
    content TEXT NOT NULL,
    author TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Evidence: Files (screenshots, packet captures, logs)
CREATE TABLE evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,  -- 'pcap', 'screenshot', 'log', 'exploit'
    description TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Events: Audit trail + triggerable events
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,  -- 'host_discovered', 'vuln_found', 'scan_completed', etc.
    payload JSON,  -- Event data
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Suggestions: AI-generated next steps
CREATE TABLE suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    suggestion_text TEXT NOT NULL,
    reasoning TEXT,  -- Why this suggestion?
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('pending', 'accepted', 'rejected', 'completed')) DEFAULT 'pending',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

---

## 🔧 WORKSPACE MANAGER API

### File: `vertice/workspace/manager.py`

```python
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, Project, Host, Port, Vulnerability, Credential
import git

class WorkspaceManager:
    """
    Manages Vértice workspaces (projects).

    A workspace consists of:
    - SQLite database (state.db)
    - Git repository (for versioning)
    - Evidence directory (for files)
    """

    def __init__(self, workspace_root: Path = Path.home() / ".vertice" / "workspaces"):
        self.workspace_root = workspace_root
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self._current_project: Optional[str] = None
        self._session: Optional[Session] = None

    def create_project(self, name: str, description: str = "", scope: List[str] = None) -> Project:
        """
        Create new project workspace.

        Directory structure:
        ~/.vertice/workspaces/<project_name>/
        ├── state.db              # SQLite database
        ├── evidence/             # Files (pcaps, screenshots, etc.)
        └── .git/                 # Git repo for versioning
        """
        project_dir = self.workspace_root / name
        if project_dir.exists():
            raise ValueError(f"Project '{name}' already exists")

        project_dir.mkdir()
        (project_dir / "evidence").mkdir()

        # Initialize SQLite
        db_path = project_dir / "state.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        # Create project record
        project = Project(
            name=name,
            description=description,
            scope=json.dumps(scope) if scope else "[]"
        )
        session.add(project)
        session.commit()

        # Initialize Git
        repo = git.Repo.init(project_dir)
        repo.index.add(["state.db"])
        repo.index.commit("Initial commit: Project created")

        self._current_project = name
        self._session = session

        return project

    def switch_project(self, name: str):
        """Switch active project"""
        project_dir = self.workspace_root / name
        if not project_dir.exists():
            raise ValueError(f"Project '{name}' not found")

        db_path = project_dir / "state.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        self._session = Session()
        self._current_project = name

    def list_projects(self) -> List[Project]:
        """List all projects"""
        projects = []
        for project_dir in self.workspace_root.iterdir():
            if project_dir.is_dir() and (project_dir / "state.db").exists():
                # Quick load
                engine = create_engine(f"sqlite:///{project_dir / 'state.db'}")
                Session = sessionmaker(bind=engine)
                session = Session()
                project = session.query(Project).first()
                if project:
                    projects.append(project)
        return projects

    def get_current_project(self) -> Optional[Project]:
        """Get currently active project"""
        if not self._session:
            return None
        return self._session.query(Project).first()

    # ===== CRUD Operations =====

    def add_host(self, ip_address: str, hostname: str = None, **kwargs) -> Host:
        """Add/update host"""
        project = self.get_current_project()
        if not project:
            raise RuntimeError("No active project")

        # Check if host exists
        host = self._session.query(Host).filter_by(
            project_id=project.id,
            ip_address=ip_address
        ).first()

        if host:
            # Update existing
            host.hostname = hostname or host.hostname
            host.last_seen = func.now()
            for key, value in kwargs.items():
                setattr(host, key, value)
        else:
            # Create new
            host = Host(
                project_id=project.id,
                ip_address=ip_address,
                hostname=hostname,
                **kwargs
            )
            self._session.add(host)

        self._session.commit()

        # Emit event
        self._emit_event("host_discovered", {"host_id": host.id, "ip": ip_address})

        return host

    def add_port(self, host_id: int, port: int, protocol: str = "tcp", **kwargs) -> Port:
        """Add/update port"""
        existing = self._session.query(Port).filter_by(
            host_id=host_id,
            port=port,
            protocol=protocol
        ).first()

        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            port_obj = existing
        else:
            port_obj = Port(host_id=host_id, port=port, protocol=protocol, **kwargs)
            self._session.add(port_obj)

        self._session.commit()
        self._emit_event("port_discovered", {"port_id": port_obj.id, "port": port})
        return port_obj

    def add_vulnerability(self, host_id: int, title: str, severity: str, **kwargs) -> Vulnerability:
        """Add vulnerability"""
        vuln = Vulnerability(
            host_id=host_id,
            title=title,
            severity=severity,
            **kwargs
        )
        self._session.add(vuln)
        self._session.commit()

        self._emit_event("vuln_found", {"vuln_id": vuln.id, "severity": severity})
        return vuln

    # ===== Query Interface =====

    def query_hosts(self, filters: Dict[str, Any] = None) -> List[Host]:
        """Query hosts with filters"""
        query = self._session.query(Host)
        if filters:
            for key, value in filters.items():
                query = query.filter(getattr(Host, key) == value)
        return query.all()

    def query_nl(self, question: str) -> Dict[str, Any]:
        """
        Natural language query → SQL.

        Examples:
            "show all SSH servers" → SELECT ... WHERE port = 22
            "find critical vulns" → SELECT ... WHERE severity = 'critical'
        """
        from vertice.ai.assistant import MaximusAssistant
        assistant = MaximusAssistant()
        return assistant.query_workspace(question, session=self._session)

    # ===== Event System =====

    def _emit_event(self, event_type: str, payload: Dict[str, Any]):
        """Emit event (triggers listeners, e.g., AI Assistant)"""
        project = self.get_current_project()
        event = Event(
            project_id=project.id,
            event_type=event_type,
            payload=json.dumps(payload)
        )
        self._session.add(event)
        self._session.commit()

        # Trigger listeners
        self._trigger_listeners(event_type, payload)

    def _trigger_listeners(self, event_type: str, payload: Dict):
        """Trigger registered event listeners"""
        # Hook for Maximus AI, notifications, etc.
        pass

    # ===== Git Versioning =====

    def commit(self, message: str):
        """Commit current state to Git"""
        project_dir = self.workspace_root / self._current_project
        repo = git.Repo(project_dir)
        repo.index.add(["state.db"])
        repo.index.commit(message)

    def rollback(self, commit_hash: str):
        """Rollback to previous state"""
        project_dir = self.workspace_root / self._current_project
        repo = git.Repo(project_dir)
        repo.git.checkout(commit_hash, "state.db")
```

---

## 📋 MODELS (SQLAlchemy)

### File: `vertice/workspace/models.py`

```python
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    scope = Column(JSON)  # List of target CIDRs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="active")

    # Relationships
    hosts = relationship("Host", back_populates="project", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="project", cascade="all, delete-orphan")

class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    ip_address = Column(String, nullable=False)
    hostname = Column(String)
    mac_address = Column(String)
    os_family = Column(String)
    os_version = Column(String)
    state = Column(String, default="unknown")
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="hosts")
    ports = relationship("Port", back_populates="host", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="host", cascade="all, delete-orphan")

class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False)
    port = Column(Integer, nullable=False)
    protocol = Column(String, default="tcp")
    state = Column(String, default="open")
    service = Column(String)
    version = Column(String)
    banner = Column(Text)
    discovered_by = Column(String)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    host = relationship("Host", back_populates="ports")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    port_id = Column(Integer, ForeignKey("ports.id"))
    cve_id = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(String)
    cvss_score = Column(Float)
    exploitable = Column(Boolean, default=False)
    exploit_available = Column(Text)
    remediation = Column(Text)
    discovered_by = Column(String)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    validated = Column(Boolean, default=False)

    # Relationships
    host = relationship("Host", back_populates="vulnerabilities")
```

---

## 🎯 USAGE EXAMPLES

### CLI Commands

```bash
# Create new project
$ vcli project create pentest-acme --scope "10.10.1.0/24,192.168.1.0/24"
✅ Project 'pentest-acme' created

# List projects
$ vcli project list
┌────────────────┬──────────┬────────────────┐
│ Name           │ Hosts    │ Status         │
├────────────────┼──────────┼────────────────┤
│ pentest-acme   │ 0        │ active         │
│ old-pentest    │ 45       │ completed      │
└────────────────┴──────────┴────────────────┘

# Switch project
$ vcli project switch pentest-acme
✅ Switched to 'pentest-acme'

# Status
$ vcli project status
📊 Project: pentest-acme
   Created: 2025-01-15 10:30:00
   Hosts: 12
   Ports: 48
   Vulns: 3 (1 critical, 2 high)
   Last activity: 5 minutes ago

# Export report
$ vcli project export --format pdf --output report.pdf
✅ Report generated: report.pdf
```

### Programmatic API

```python
from vertice.workspace import WorkspaceManager

workspace = WorkspaceManager()
workspace.switch_project("pentest-acme")

# Add host
host = workspace.add_host(
    ip_address="10.10.1.5",
    hostname="target.local",
    os_family="Linux"
)

# Add port
port = workspace.add_port(
    host_id=host.id,
    port=22,
    protocol="tcp",
    service="ssh",
    version="OpenSSH 7.4"
)

# Add vulnerability
vuln = workspace.add_vulnerability(
    host_id=host.id,
    port_id=port.id,
    cve_id="CVE-2018-15473",
    title="OpenSSH User Enumeration",
    severity="medium",
    exploitable=True
)

# Query
all_ssh_hosts = workspace.query_hosts({"ports.port": 22})

# Natural language query
results = workspace.query_nl("show all critical vulnerabilities")
```

---

## 📚 NEXT STEPS

1. ✅ Implement SQLAlchemy models
2. ✅ Implement WorkspaceManager class
3. ⏳ Add CLI commands (`vcli project ...`)
4. ⏳ Integrate with orchestrator (auto-store scan results)
5. ⏳ Event system + AI listener
6. ⏳ Export/reporting (PDF, HTML, JSON)
7. ⏳ Multi-user collaboration (shared workspaces)

---

**Document Version**: 1.0
**Last Updated**: January 2025
**Status**: 📋 Design Complete
