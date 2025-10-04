"""
WorkspaceManager - Core State Management
=========================================

Manages Vértice workspaces (projects) with SQLite + Git versioning.

Features:
- Project CRUD operations
- Host/Port/Vulnerability management
- Event system for AI integration
- Git versioning for audit trail
- Natural language queries (via Maximus)

Example:
    workspace = WorkspaceManager()
    workspace.create_project("pentest-acme", scope=["10.10.1.0/24"])

    host = workspace.add_host("10.10.1.5", hostname="target.local")
    port = workspace.add_port(host.id, 22, service="ssh", version="OpenSSH 7.4")

    all_hosts = workspace.query_hosts()
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import logging

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

from .models import (
    Base, Project, Host, Port, Vulnerability,
    Credential, Note, Evidence, Event, Suggestion
)

logger = logging.getLogger(__name__)


class WorkspaceError(Exception):
    """Base exception for workspace operations"""
    pass


class ProjectNotFoundError(WorkspaceError):
    """Raised when project doesn't exist"""
    pass


class ProjectExistsError(WorkspaceError):
    """Raised when trying to create existing project"""
    pass


class WorkspaceManager:
    """
    Manages Vértice workspaces (projects).

    A workspace consists of:
    - SQLite database (state.db)
    - Git repository (for versioning)
    - Evidence directory (for files)
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize WorkspaceManager.

        Args:
            workspace_root: Root directory for all workspaces.
                          Defaults to ~/.vertice/workspaces
        """
        if workspace_root is None:
            workspace_root = Path.home() / ".vertice" / "workspaces"

        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        self._current_project: Optional[str] = None
        self._session: Optional[Session] = None
        self._engine = None

        # Event listeners
        self._event_listeners: Dict[str, List[callable]] = {}

        logger.info(f"WorkspaceManager initialized: {self.workspace_root}")

    # ===== PROJECT MANAGEMENT =====

    def create_project(
        self,
        name: str,
        description: str = "",
        scope: Optional[List[str]] = None
    ) -> Project:
        """
        Create new project workspace.

        Creates:
        - Directory: ~/.vertice/workspaces/<project_name>/
        - SQLite database: state.db
        - Evidence directory: evidence/
        - Git repository: .git/

        Args:
            name: Project name (must be unique)
            description: Optional description
            scope: List of target CIDRs/domains

        Returns:
            Project object

        Raises:
            ProjectExistsError: If project already exists
        """
        project_dir = self.workspace_root / name

        if project_dir.exists():
            raise ProjectExistsError(f"Project '{name}' already exists")

        logger.info(f"Creating project: {name}")

        # Create directory structure
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
            scope=scope or []
        )
        session.add(project)
        session.commit()

        # Initialize Git (if available)
        if GIT_AVAILABLE:
            try:
                repo = git.Repo.init(project_dir)
                repo.index.add(["state.db"])
                repo.index.commit("Initial commit: Project created")
                logger.info(f"Git repository initialized for {name}")
            except Exception as e:
                logger.warning(f"Git init failed: {e}")

        # Switch to new project
        self._current_project = name
        self._session = session
        self._engine = engine

        logger.info(f"Project '{name}' created successfully")
        return project

    def switch_project(self, name: str):
        """
        Switch active project.

        Args:
            name: Project name

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project_dir = self.workspace_root / name

        if not project_dir.exists():
            raise ProjectNotFoundError(f"Project '{name}' not found")

        db_path = project_dir / "state.db"

        if not db_path.exists():
            raise ProjectNotFoundError(f"Project '{name}' has no database")

        # Close existing session
        if self._session:
            self._session.close()

        # Open new session
        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        self._session = Session()
        self._engine = engine
        self._current_project = name

        logger.info(f"Switched to project: {name}")

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.

        Returns:
            List of project metadata dicts
        """
        projects = []

        for project_dir in self.workspace_root.iterdir():
            if not project_dir.is_dir():
                continue

            db_path = project_dir / "state.db"
            if not db_path.exists():
                continue

            # Quick metadata load
            engine = create_engine(f"sqlite:///{db_path}")
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                project = session.query(Project).first()
                if project:
                    # Get stats
                    host_count = session.query(Host).filter_by(project_id=project.id).count()
                    vuln_count = session.query(Vulnerability).filter_by(host_id=Host.id).count()

                    projects.append({
                        "name": project.name,
                        "description": project.description,
                        "status": project.status,
                        "created_at": project.created_at,
                        "hosts": host_count,
                        "vulns": vuln_count
                    })
            finally:
                session.close()

        return sorted(projects, key=lambda p: p["created_at"], reverse=True)

    def get_current_project(self) -> Optional[Project]:
        """
        Get currently active project.

        Returns:
            Project object or None
        """
        if not self._session:
            return None

        return self._session.query(Project).first()

    def delete_project(self, name: str, confirm: bool = False):
        """
        Delete project (requires confirmation).

        Args:
            name: Project name
            confirm: Must be True to proceed

        Raises:
            WorkspaceError: If confirmation not provided
        """
        if not confirm:
            raise WorkspaceError("Must confirm=True to delete project")

        project_dir = self.workspace_root / name

        if not project_dir.exists():
            raise ProjectNotFoundError(f"Project '{name}' not found")

        # Close session if this is active project
        if self._current_project == name and self._session:
            self._session.close()
            self._session = None
            self._current_project = None

        # Delete directory
        import shutil
        shutil.rmtree(project_dir)

        logger.info(f"Project '{name}' deleted")

    # ===== CRUD OPERATIONS =====

    def add_host(
        self,
        ip_address: str,
        hostname: Optional[str] = None,
        **kwargs
    ) -> Host:
        """
        Add or update host.

        Args:
            ip_address: IP address (required)
            hostname: Hostname (optional)
            **kwargs: Additional fields (os_family, os_version, state, etc.)

        Returns:
            Host object

        Raises:
            WorkspaceError: If no active project
        """
        project = self.get_current_project()
        if not project:
            raise WorkspaceError("No active project. Use switch_project() first.")

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
                if hasattr(host, key):
                    setattr(host, key, value)
            logger.debug(f"Updated host: {ip_address}")
        else:
            # Create new
            host = Host(
                project_id=project.id,
                ip_address=ip_address,
                hostname=hostname,
                **kwargs
            )
            self._session.add(host)
            logger.info(f"Added host: {ip_address}")

        self._session.commit()

        # Emit event
        self._emit_event("host_discovered", {
            "host_id": host.id,
            "ip": ip_address,
            "hostname": hostname
        })

        return host

    def add_port(
        self,
        host_id: int,
        port: int,
        protocol: str = "tcp",
        **kwargs
    ) -> Port:
        """
        Add or update port.

        Args:
            host_id: Host ID
            port: Port number
            protocol: Protocol (tcp, udp, sctp)
            **kwargs: Additional fields (service, version, banner, etc.)

        Returns:
            Port object
        """
        existing = self._session.query(Port).filter_by(
            host_id=host_id,
            port=port,
            protocol=protocol
        ).first()

        if existing:
            # Update
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            port_obj = existing
            logger.debug(f"Updated port: {port}/{protocol}")
        else:
            # Create
            port_obj = Port(
                host_id=host_id,
                port=port,
                protocol=protocol,
                **kwargs
            )
            self._session.add(port_obj)
            logger.info(f"Added port: {port}/{protocol}")

        self._session.commit()

        # Emit event
        self._emit_event("port_discovered", {
            "port_id": port_obj.id,
            "host_id": host_id,
            "port": port,
            "service": kwargs.get("service")
        })

        return port_obj

    def add_vulnerability(
        self,
        host_id: int,
        title: str,
        severity: str,
        **kwargs
    ) -> Vulnerability:
        """
        Add vulnerability.

        Args:
            host_id: Host ID
            title: Vulnerability title
            severity: Severity (critical, high, medium, low, info)
            **kwargs: Additional fields (cve_id, description, etc.)

        Returns:
            Vulnerability object
        """
        vuln = Vulnerability(
            host_id=host_id,
            title=title,
            severity=severity,
            **kwargs
        )
        self._session.add(vuln)
        self._session.commit()

        logger.info(f"Added vulnerability: {title} ({severity})")

        # Emit event
        self._emit_event("vuln_found", {
            "vuln_id": vuln.id,
            "host_id": host_id,
            "severity": severity,
            "cve_id": kwargs.get("cve_id")
        })

        return vuln

    def add_credential(
        self,
        host_id: int,
        username: str,
        **kwargs
    ) -> Credential:
        """
        Add credential.

        Args:
            host_id: Host ID
            username: Username
            **kwargs: Additional fields (password, hash, service, etc.)

        Returns:
            Credential object
        """
        cred = Credential(
            host_id=host_id,
            username=username,
            **kwargs
        )
        self._session.add(cred)
        self._session.commit()

        logger.info(f"Added credential: {username}")

        # Emit event
        self._emit_event("cred_found", {
            "cred_id": cred.id,
            "host_id": host_id,
            "username": username,
            "service": kwargs.get("service")
        })

        return cred

    # ===== QUERY INTERFACE =====

    def query_hosts(self, filters: Optional[Dict[str, Any]] = None) -> List[Host]:
        """
        Query hosts with optional filters.

        Args:
            filters: Dict of field:value filters

        Returns:
            List of Host objects
        """
        query = self._session.query(Host)

        if filters:
            for key, value in filters.items():
                if hasattr(Host, key):
                    query = query.filter(getattr(Host, key) == value)

        return query.all()

    def query_vulnerabilities(
        self,
        severity: Optional[str] = None,
        exploitable: Optional[bool] = None
    ) -> List[Vulnerability]:
        """
        Query vulnerabilities.

        Args:
            severity: Filter by severity
            exploitable: Filter by exploitability

        Returns:
            List of Vulnerability objects
        """
        query = self._session.query(Vulnerability)

        if severity:
            query = query.filter_by(severity=severity)

        if exploitable is not None:
            query = query.filter_by(exploitable=exploitable)

        return query.all()

    def query_nl(self, question: str) -> Dict[str, Any]:
        """
        Natural language query (TODO: integrate with Maximus AI).

        Args:
            question: Natural language question

        Returns:
            Query results
        """
        # Placeholder - will integrate with Maximus AI v2
        logger.warning("NL query not yet implemented. Returning empty results.")
        return {"question": question, "results": []}

    # ===== EVENT SYSTEM =====

    def _emit_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Emit event (triggers listeners, e.g., AI Assistant).

        Args:
            event_type: Event type (host_discovered, vuln_found, etc.)
            payload: Event data
        """
        project = self.get_current_project()
        if not project:
            return

        # Store in DB
        event = Event(
            project_id=project.id,
            event_type=event_type,
            payload=payload
        )
        self._session.add(event)
        self._session.commit()

        # Trigger listeners
        for listener in self._event_listeners.get(event_type, []):
            try:
                listener(payload)
            except Exception as e:
                logger.error(f"Event listener failed: {e}")

    def on(self, event_type: str, callback: callable):
        """
        Register event listener.

        Args:
            event_type: Event type to listen for
            callback: Function to call when event fires
        """
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []

        self._event_listeners[event_type].append(callback)
        logger.debug(f"Registered listener for {event_type}")

    # ===== GIT VERSIONING =====

    def commit(self, message: str):
        """
        Commit current state to Git.

        Args:
            message: Commit message
        """
        if not GIT_AVAILABLE:
            logger.warning("Git not available. Skipping commit.")
            return

        if not self._current_project:
            raise WorkspaceError("No active project")

        project_dir = self.workspace_root / self._current_project

        try:
            repo = git.Repo(project_dir)
            repo.index.add(["state.db"])
            repo.index.commit(message)
            logger.info(f"Committed: {message}")
        except Exception as e:
            logger.error(f"Git commit failed: {e}")

    def rollback(self, commit_hash: str):
        """
        Rollback to previous state.

        Args:
            commit_hash: Git commit hash
        """
        if not GIT_AVAILABLE:
            raise WorkspaceError("Git not available")

        if not self._current_project:
            raise WorkspaceError("No active project")

        project_dir = self.workspace_root / self._current_project

        try:
            repo = git.Repo(project_dir)
            repo.git.checkout(commit_hash, "state.db")
            logger.info(f"Rolled back to {commit_hash}")

            # Reload session
            self.switch_project(self._current_project)
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise WorkspaceError(f"Rollback failed: {e}")

    # ===== UTILITY METHODS =====

    def get_stats(self) -> Dict[str, Any]:
        """
        Get workspace statistics.

        Returns:
            Dict with host/port/vuln counts
        """
        project = self.get_current_project()
        if not project:
            return {}

        return {
            "project": project.name,
            "hosts": self._session.query(Host).filter_by(project_id=project.id).count(),
            "ports": self._session.query(Port).join(Host).filter(Host.project_id == project.id).count(),
            "vulns": self._session.query(Vulnerability).join(Host).filter(Host.project_id == project.id).count(),
            "vulns_critical": self._session.query(Vulnerability).join(Host).filter(
                Host.project_id == project.id,
                Vulnerability.severity == "critical"
            ).count(),
            "vulns_high": self._session.query(Vulnerability).join(Host).filter(
                Host.project_id == project.id,
                Vulnerability.severity == "high"
            ).count(),
            "credentials": self._session.query(Credential).join(Host).filter(Host.project_id == project.id).count()
        }

    def close(self):
        """Close current session."""
        if self._session:
            self._session.close()
            self._session = None
            logger.debug("Session closed")
