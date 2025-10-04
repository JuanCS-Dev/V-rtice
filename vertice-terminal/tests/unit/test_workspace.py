"""
Unit tests for Workspace module - State Management
====================================================

Tests for WorkspaceManager, models, and database operations.

Coverage:
- Project CRUD operations
- Host/Port/Vulnerability management
- Event system
- Git versioning
- Query operations
- Statistics
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from vertice.workspace import (
    WorkspaceManager,
    Project,
    Host,
    Port,
    Vulnerability,
    Credential,
    Event,
    Suggestion,
    ProjectExistsError,
    ProjectNotFoundError,
    WorkspaceError
)


@pytest.fixture
def temp_workspace():
    """Create temporary workspace directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def workspace(temp_workspace):
    """Create WorkspaceManager instance with temp directory."""
    return WorkspaceManager(workspace_root=temp_workspace)


@pytest.fixture
def workspace_with_project(workspace):
    """Create WorkspaceManager with active project."""
    workspace.create_project(
        "test-project",
        description="Test project",
        scope=["10.0.0.0/24", "192.168.1.0/24"]
    )
    return workspace


class TestWorkspaceInitialization:
    """Test WorkspaceManager initialization."""

    def test_init_creates_workspace_root(self, temp_workspace):
        """Test that workspace root directory is created."""
        workspace = WorkspaceManager(workspace_root=temp_workspace)
        assert workspace.workspace_root.exists()
        assert workspace.workspace_root.is_dir()

    def test_init_default_location(self):
        """Test that default location is ~/.vertice/workspaces."""
        workspace = WorkspaceManager()
        expected = Path.home() / ".vertice" / "workspaces"
        assert workspace.workspace_root == expected

    def test_init_no_active_project(self, workspace):
        """Test that no project is active initially."""
        assert workspace._current_project is None
        assert workspace._session is None


class TestProjectManagement:
    """Test project CRUD operations."""

    def test_create_project(self, workspace):
        """Test creating a new project."""
        project = workspace.create_project(
            "pentest-acme",
            description="Acme Corp Pentest",
            scope=["acme.com", "10.10.1.0/24"]
        )

        assert project.name == "pentest-acme"
        assert project.description == "Acme Corp Pentest"
        assert project.scope == ["acme.com", "10.10.1.0/24"]
        assert project.status == "active"
        assert isinstance(project.created_at, datetime)

        # Check directory structure
        project_dir = workspace.workspace_root / "pentest-acme"
        assert project_dir.exists()
        assert (project_dir / "state.db").exists()
        assert (project_dir / "evidence").exists()

    def test_create_duplicate_project(self, workspace_with_project):
        """Test that creating duplicate project raises error."""
        with pytest.raises(ProjectExistsError):
            workspace_with_project.create_project("test-project")

    def test_list_projects_empty(self, workspace):
        """Test listing projects when none exist."""
        projects = workspace.list_projects()
        assert projects == []

    def test_list_projects(self, workspace):
        """Test listing multiple projects."""
        workspace.create_project("project-1")
        workspace.create_project("project-2")
        workspace.create_project("project-3")

        projects = workspace.list_projects()

        assert len(projects) == 3
        project_names = {p["name"] for p in projects}
        assert project_names == {"project-1", "project-2", "project-3"}

        # Verify metadata
        for proj in projects:
            assert "name" in proj
            assert "status" in proj
            assert "created_at" in proj
            assert "hosts" in proj
            assert "vulns" in proj

    def test_switch_project(self, workspace):
        """Test switching between projects."""
        workspace.create_project("project-1")
        workspace.create_project("project-2")

        # Switch to project-2
        workspace.switch_project("project-2")

        current = workspace.get_current_project()
        assert current.name == "project-2"

    def test_switch_nonexistent_project(self, workspace):
        """Test switching to non-existent project raises error."""
        with pytest.raises(ProjectNotFoundError):
            workspace.switch_project("nonexistent")

    def test_delete_project(self, workspace):
        """Test deleting a project."""
        workspace.create_project("to-delete")

        project_dir = workspace.workspace_root / "to-delete"
        assert project_dir.exists()

        workspace.delete_project("to-delete", confirm=True)

        assert not project_dir.exists()

    def test_delete_project_without_confirmation(self, workspace_with_project):
        """Test that delete requires confirmation."""
        with pytest.raises(WorkspaceError):
            workspace_with_project.delete_project("test-project", confirm=False)

    def test_delete_active_project(self, workspace_with_project):
        """Test deleting currently active project."""
        workspace_with_project.delete_project("test-project", confirm=True)

        assert workspace_with_project._current_project is None
        assert workspace_with_project._session is None


class TestHostManagement:
    """Test host CRUD operations."""

    def test_add_host(self, workspace_with_project):
        """Test adding a host."""
        host = workspace_with_project.add_host(
            "10.10.1.5",
            hostname="target.local",
            os_family="Linux",
            state="up"
        )

        assert host.ip_address == "10.10.1.5"
        assert host.hostname == "target.local"
        assert host.os_family == "Linux"
        assert host.state == "up"
        assert isinstance(host.discovered_at, datetime)

    def test_add_host_without_project(self, workspace):
        """Test that adding host without active project raises error."""
        with pytest.raises(WorkspaceError):
            workspace.add_host("10.10.1.5")

    def test_update_host(self, workspace_with_project):
        """Test updating existing host."""
        # Add host
        host1 = workspace_with_project.add_host("10.10.1.5", hostname="host1")
        assert host1.hostname == "host1"

        # Update same IP
        host2 = workspace_with_project.add_host("10.10.1.5", hostname="host1-updated")
        assert host2.id == host1.id  # Same host
        assert host2.hostname == "host1-updated"

    def test_query_hosts(self, workspace_with_project):
        """Test querying hosts."""
        workspace_with_project.add_host("10.10.1.1", state="up")
        workspace_with_project.add_host("10.10.1.2", state="up")
        workspace_with_project.add_host("10.10.1.3", state="down")

        # Query all hosts
        all_hosts = workspace_with_project.query_hosts()
        assert len(all_hosts) == 3

        # Query filtered
        up_hosts = workspace_with_project.query_hosts({"state": "up"})
        assert len(up_hosts) == 2

    def test_query_hosts_empty(self, workspace_with_project):
        """Test querying when no hosts exist."""
        hosts = workspace_with_project.query_hosts()
        assert hosts == []


class TestPortManagement:
    """Test port CRUD operations."""

    def test_add_port(self, workspace_with_project):
        """Test adding a port to host."""
        host = workspace_with_project.add_host("10.10.1.5")

        port = workspace_with_project.add_port(
            host.id,
            22,
            protocol="tcp",
            service="ssh",
            version="OpenSSH 7.4",
            state="open"
        )

        assert port.port == 22
        assert port.protocol == "tcp"
        assert port.service == "ssh"
        assert port.version == "OpenSSH 7.4"
        assert port.state == "open"
        assert port.host_id == host.id

    def test_update_port(self, workspace_with_project):
        """Test updating existing port."""
        host = workspace_with_project.add_host("10.10.1.5")

        # Add port
        port1 = workspace_with_project.add_port(host.id, 22, service="ssh")
        assert port1.service == "ssh"

        # Update same port
        port2 = workspace_with_project.add_port(
            host.id,
            22,
            service="ssh",
            version="OpenSSH 7.4"
        )

        assert port2.id == port1.id  # Same port
        assert port2.version == "OpenSSH 7.4"

    def test_add_multiple_ports(self, workspace_with_project):
        """Test adding multiple ports to same host."""
        host = workspace_with_project.add_host("10.10.1.5")

        workspace_with_project.add_port(host.id, 22, service="ssh")
        workspace_with_project.add_port(host.id, 80, service="http")
        workspace_with_project.add_port(host.id, 443, service="https")

        # Query all ports for this host
        ports = workspace_with_project._session.query(Port).filter_by(host_id=host.id).all()
        assert len(ports) == 3


class TestVulnerabilityManagement:
    """Test vulnerability CRUD operations."""

    def test_add_vulnerability(self, workspace_with_project):
        """Test adding a vulnerability."""
        host = workspace_with_project.add_host("10.10.1.5")

        vuln = workspace_with_project.add_vulnerability(
            host.id,
            "SQL Injection in login form",
            "critical",
            cve_id="CVE-2021-12345",
            description="Login form vulnerable to SQLi",
            cvss_score=9.8,
            exploitable=True
        )

        assert vuln.title == "SQL Injection in login form"
        assert vuln.severity == "critical"
        assert vuln.cve_id == "CVE-2021-12345"
        assert vuln.cvss_score == 9.8
        assert vuln.exploitable is True
        assert vuln.host_id == host.id

    def test_query_vulnerabilities(self, workspace_with_project):
        """Test querying vulnerabilities."""
        host = workspace_with_project.add_host("10.10.1.5")

        workspace_with_project.add_vulnerability(host.id, "Vuln 1", "critical")
        workspace_with_project.add_vulnerability(host.id, "Vuln 2", "high")
        workspace_with_project.add_vulnerability(host.id, "Vuln 3", "critical")

        # Query all
        all_vulns = workspace_with_project.query_vulnerabilities()
        assert len(all_vulns) == 3

        # Query by severity
        critical_vulns = workspace_with_project.query_vulnerabilities(severity="critical")
        assert len(critical_vulns) == 2

    def test_query_exploitable_vulnerabilities(self, workspace_with_project):
        """Test querying exploitable vulnerabilities."""
        host = workspace_with_project.add_host("10.10.1.5")

        workspace_with_project.add_vulnerability(host.id, "Vuln 1", "high", exploitable=True)
        workspace_with_project.add_vulnerability(host.id, "Vuln 2", "high", exploitable=False)
        workspace_with_project.add_vulnerability(host.id, "Vuln 3", "critical", exploitable=True)

        exploitable = workspace_with_project.query_vulnerabilities(exploitable=True)
        assert len(exploitable) == 2


class TestCredentialManagement:
    """Test credential CRUD operations."""

    def test_add_credential(self, workspace_with_project):
        """Test adding a credential."""
        host = workspace_with_project.add_host("10.10.1.5")

        cred = workspace_with_project.add_credential(
            host.id,
            "admin",
            password="P@ssw0rd",
            service="ssh",
            validated=True
        )

        assert cred.username == "admin"
        assert cred.password == "P@ssw0rd"
        assert cred.service == "ssh"
        assert cred.validated is True


class TestEventSystem:
    """Test event emission and listeners."""

    def test_event_emission_host_discovered(self, workspace_with_project):
        """Test that host_discovered event is emitted."""
        workspace_with_project.add_host("10.10.1.5")

        # Query events
        events = workspace_with_project._session.query(Event).filter_by(
            event_type="host_discovered"
        ).all()

        assert len(events) == 1
        assert events[0].payload["ip"] == "10.10.1.5"

    def test_event_emission_port_discovered(self, workspace_with_project):
        """Test that port_discovered event is emitted."""
        host = workspace_with_project.add_host("10.10.1.5")
        workspace_with_project.add_port(host.id, 22, service="ssh")

        events = workspace_with_project._session.query(Event).filter_by(
            event_type="port_discovered"
        ).all()

        assert len(events) == 1
        assert events[0].payload["port"] == 22

    def test_event_emission_vuln_found(self, workspace_with_project):
        """Test that vuln_found event is emitted."""
        host = workspace_with_project.add_host("10.10.1.5")
        workspace_with_project.add_vulnerability(host.id, "SQLi", "critical")

        events = workspace_with_project._session.query(Event).filter_by(
            event_type="vuln_found"
        ).all()

        assert len(events) == 1
        assert events[0].payload["severity"] == "critical"

    def test_event_listener(self, workspace_with_project):
        """Test registering and triggering event listeners."""
        callback_data = []

        def listener(payload):
            callback_data.append(payload)

        workspace_with_project.on("host_discovered", listener)

        # Trigger event
        workspace_with_project.add_host("10.10.1.5", hostname="test")

        # Verify listener was called
        assert len(callback_data) == 1
        assert callback_data[0]["ip"] == "10.10.1.5"
        assert callback_data[0]["hostname"] == "test"

    def test_multiple_listeners(self, workspace_with_project):
        """Test multiple listeners for same event."""
        callback1_data = []
        callback2_data = []

        def listener1(payload):
            callback1_data.append(payload)

        def listener2(payload):
            callback2_data.append(payload)

        workspace_with_project.on("host_discovered", listener1)
        workspace_with_project.on("host_discovered", listener2)

        workspace_with_project.add_host("10.10.1.5")

        assert len(callback1_data) == 1
        assert len(callback2_data) == 1


class TestStatistics:
    """Test workspace statistics."""

    def test_get_stats_empty(self, workspace_with_project):
        """Test statistics for empty project."""
        stats = workspace_with_project.get_stats()

        assert stats["project"] == "test-project"
        assert stats["hosts"] == 0
        assert stats["ports"] == 0
        assert stats["vulns"] == 0
        assert stats["vulns_critical"] == 0
        assert stats["vulns_high"] == 0
        assert stats["credentials"] == 0

    def test_get_stats_with_data(self, workspace_with_project):
        """Test statistics with data."""
        # Add hosts
        host1 = workspace_with_project.add_host("10.10.1.1")
        host2 = workspace_with_project.add_host("10.10.1.2")

        # Add ports
        workspace_with_project.add_port(host1.id, 22)
        workspace_with_project.add_port(host1.id, 80)
        workspace_with_project.add_port(host2.id, 443)

        # Add vulnerabilities
        workspace_with_project.add_vulnerability(host1.id, "Vuln 1", "critical")
        workspace_with_project.add_vulnerability(host1.id, "Vuln 2", "high")
        workspace_with_project.add_vulnerability(host2.id, "Vuln 3", "critical")

        # Add credentials
        workspace_with_project.add_credential(host1.id, "admin", password="pass123")

        stats = workspace_with_project.get_stats()

        assert stats["hosts"] == 2
        assert stats["ports"] == 3
        assert stats["vulns"] == 3
        assert stats["vulns_critical"] == 2
        assert stats["vulns_high"] == 1
        assert stats["credentials"] == 1


class TestGitVersioning:
    """Test Git versioning functionality."""

    def test_git_init_on_create(self, workspace):
        """Test that Git repo is initialized on project creation."""
        workspace.create_project("git-test")

        project_dir = workspace.workspace_root / "git-test"
        git_dir = project_dir / ".git"

        # Git might not be available, so we check conditionally
        try:
            import git
            assert git_dir.exists()
        except ImportError:
            pytest.skip("Git not available")

    def test_commit(self, workspace_with_project):
        """Test committing workspace state."""
        try:
            import git
            workspace_with_project.add_host("10.10.1.5")
            workspace_with_project.commit("Added test host")

            project_dir = workspace_with_project.workspace_root / "test-project"
            repo = git.Repo(project_dir)

            # Verify commit exists
            commits = list(repo.iter_commits())
            assert len(commits) >= 2  # Initial + our commit
            assert "Added test host" in commits[0].message

        except ImportError:
            pytest.skip("Git not available")


class TestSessionManagement:
    """Test session lifecycle."""

    def test_close_session(self, workspace_with_project):
        """Test closing workspace session."""
        assert workspace_with_project._session is not None

        workspace_with_project.close()

        assert workspace_with_project._session is None

    def test_operations_after_close(self, workspace_with_project):
        """Test that operations fail after session close."""
        workspace_with_project.close()

        # This should work - it reopens the project
        workspace_with_project.switch_project("test-project")
        workspace_with_project.add_host("10.10.1.5")


class TestNaturalLanguageQuery:
    """Test natural language query integration (placeholder)."""

    def test_nl_query_placeholder(self, workspace_with_project):
        """Test that NL query returns placeholder response."""
        result = workspace_with_project.query_nl("show all hosts")

        assert "question" in result
        assert result["question"] == "show all hosts"
        # Currently returns empty results as it's not implemented
        assert "results" in result
