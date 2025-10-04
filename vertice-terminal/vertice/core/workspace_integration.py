"""
Workspace Integration - Auto-populate findings
===============================================

Automatically populate workspace from tool execution results.

Workflow:
1. Execute tool (Nmap, Nuclei, etc.)
2. Parse output
3. Auto-populate workspace
4. Emit events for AI integration

Example:
    from vertice.core import NmapExecutor, NmapParser
    from vertice.core.workspace_integration import populate_from_nmap
    from vertice.workspace import WorkspaceManager

    # Execute & parse
    executor = NmapExecutor()
    result = executor.execute(target="10.10.1.0/24", scan_type="full")

    parser = NmapParser()
    data = parser.parse(result.stdout)

    # Auto-populate workspace
    workspace = WorkspaceManager()
    workspace.switch_project("pentest-acme")

    stats = populate_from_nmap(workspace, data)
    # → Adds hosts, ports to workspace
    # → Emits events for AI
    # → Returns stats (hosts_added, ports_added, etc.)
"""

from typing import Dict, Any
from ..workspace import WorkspaceManager
import logging

logger = logging.getLogger(__name__)


def populate_from_nmap(workspace: WorkspaceManager, nmap_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Populate workspace from parsed Nmap data.

    Args:
        workspace: Active WorkspaceManager instance
        nmap_data: Parsed Nmap data (from NmapParser)

    Returns:
        Statistics dict:
        {
            "hosts_added": 5,
            "hosts_updated": 2,
            "ports_added": 15,
            "ports_updated": 3
        }

    Raises:
        WorkspaceError: If no active project
    """
    stats = {
        "hosts_added": 0,
        "hosts_updated": 0,
        "ports_added": 0,
        "ports_updated": 0
    }

    for host_data in nmap_data.get("hosts", []):
        # Check if host already exists
        existing_hosts = workspace.query_hosts({"ip_address": host_data["ip"]})

        if existing_hosts:
            # Update existing host
            host = workspace.add_host(
                host_data["ip"],
                hostname=host_data.get("hostname"),
                os_family=host_data.get("os_family"),
                os_version=host_data.get("os_version"),
                state=host_data.get("state", "up")
            )
            stats["hosts_updated"] += 1
            logger.debug(f"Updated host: {host_data['ip']}")
        else:
            # Add new host
            host = workspace.add_host(
                host_data["ip"],
                hostname=host_data.get("hostname"),
                os_family=host_data.get("os_family"),
                os_version=host_data.get("os_version"),
                state=host_data.get("state", "up")
            )
            stats["hosts_added"] += 1
            logger.info(f"Added host: {host_data['ip']}")

        # Add ports
        for port_data in host_data.get("ports", []):
            # Only add open ports
            if port_data.get("state") != "open":
                continue

            # add_port handles upsert logic automatically
            port = workspace.add_port(
                host.id,
                port_data["port"],
                protocol=port_data.get("protocol", "tcp"),
                service=port_data.get("service"),
                version=port_data.get("version"),
                banner=port_data.get("banner"),
                state=port_data.get("state", "open"),
                discovered_by="nmap"
            )

            # Track whether it was new or updated
            # (WorkspaceManager.add_port doesn't tell us, so we count all as "added" for now)
            stats["ports_added"] += 1
            logger.info(f"Added/updated port: {host_data['ip']}:{port_data['port']}/{port_data.get('service', 'unknown')}")

    logger.info(
        f"Workspace population complete: "
        f"{stats['hosts_added']} hosts added, {stats['hosts_updated']} updated, "
        f"{stats['ports_added']} ports added, {stats['ports_updated']} updated"
    )

    return stats


def populate_from_nuclei(workspace: WorkspaceManager, nuclei_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Populate workspace from parsed Nuclei data.

    TODO: Implement when NucleiParser is ready

    Args:
        workspace: Active WorkspaceManager instance
        nuclei_data: Parsed Nuclei data

    Returns:
        Statistics dict
    """
    raise NotImplementedError("Nuclei integration coming in Phase 1.1 completion")


def populate_from_nikto(workspace: WorkspaceManager, nikto_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Populate workspace from parsed Nikto data.

    TODO: Implement when NiktoParser is ready

    Args:
        workspace: Active WorkspaceManager instance
        nikto_data: Parsed Nikto data

    Returns:
        Statistics dict
    """
    raise NotImplementedError("Nikto integration coming in Phase 1.1 completion")
