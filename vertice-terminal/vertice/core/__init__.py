"""
Vértice Core - Tool Orchestration Engine
=========================================

The Core module provides the orchestration layer for external security tools.
Instead of replacing tools, we WRAP them - execute, parse, and integrate results.

Components:
- base.py: Base classes (ToolExecutor, ToolParser, ExecutionResult)
- executor.py: Tool execution engine
- parsers/: Output parsers for various tools (Nmap, Nuclei, Nikto, etc.)

Philosophy:
- Don't reinvent the wheel (Nmap, Metasploit, etc. are best-in-class)
- Provide intelligent orchestration layer
- Parse outputs into unified format
- Auto-populate workspace
- Enable AI-powered workflows

Example Usage:
    from vertice.core import NmapExecutor, NmapParser
    from vertice.workspace import WorkspaceManager

    # Execute Nmap
    executor = NmapExecutor()
    result = executor.execute(target="10.10.1.0/24", scan_type="full")

    # Parse output
    parser = NmapParser()
    structured = parser.parse(result.stdout)

    # Auto-populate workspace
    workspace = WorkspaceManager()
    for host in structured.hosts:
        workspace.add_host(host.ip, hostname=host.hostname, os_family=host.os)
        for port in host.ports:
            workspace.add_port(host.id, port.number, service=port.service)
"""

from .base import (
    ExecutionResult,
    ToolExecutor,
    ToolParser,
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolTimeoutError
)
from .nmap_executor import NmapExecutor
from .parsers import NmapParser

__all__ = [
    "ExecutionResult",
    "ToolExecutor",
    "ToolParser",
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolTimeoutError",
    "NmapExecutor",
    "NmapParser"
]
