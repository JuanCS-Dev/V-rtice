"""
Vértice Workspace - Persistent State Management
===============================================

The Workspace module provides persistent, queryable, versioned state
management for security operations.

A workspace consists of:
- SQLite database (state.db) - stores all findings
- Git repository - version control & audit trail
- Evidence directory - files (pcaps, screenshots, logs)

Key Components:
- models.py: SQLAlchemy models (Project, Host, Port, Vulnerability, etc.)
- manager.py: WorkspaceManager class (CRUD operations, queries)
- queries.py: Helper functions for common queries

Example Usage:
    from vertice.workspace import WorkspaceManager

    workspace = WorkspaceManager()
    workspace.create_project("pentest-acme", scope=["10.10.1.0/24"])

    # Add findings
    host = workspace.add_host("10.10.1.5", hostname="target.local")
    port = workspace.add_port(host.id, 22, service="ssh", version="OpenSSH 7.4")

    # Query
    all_hosts = workspace.query_hosts()
    ssh_servers = workspace.query_nl("show all SSH servers")
"""

from .manager import (
    WorkspaceManager,
    WorkspaceError,
    ProjectNotFoundError,
    ProjectExistsError
)
from .models import (
    Base,
    Project,
    Host,
    Port,
    Vulnerability,
    Credential,
    Note,
    Evidence,
    Event,
    Suggestion
)

__all__ = [
    "WorkspaceManager",
    "WorkspaceError",
    "ProjectNotFoundError",
    "ProjectExistsError",
    "Base",
    "Project",
    "Host",
    "Port",
    "Vulnerability",
    "Credential",
    "Note",
    "Evidence",
    "Event",
    "Suggestion"
]
