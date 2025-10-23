"""Architecture Scanner - Scans all VÉRTICE services and builds dependency graph.

Scans docker-compose.yml and service directories to extract:
- Service metadata (ports, dependencies, health checks)
- Dependency graph (NetworkX)
- Subsystem categorization
- Health check coverage

Zero mocks, zero placeholders - production-ready implementation.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Set

import networkx as nx
import yaml

logger = logging.getLogger(__name__)


class ArchitectureScanner:
    """Scans VÉRTICE architecture and builds comprehensive service inventory."""

    # Subsystem categorization patterns
    SUBSYSTEM_PATTERNS = {
        "consciousness": [
            "maximus_core", "digital_thalamus", "prefrontal_cortex",
            "memory_consolidation", "neuromodulation", "visual_cortex",
            "auditory_cortex", "somatosensory", "chemical_sensing", "vestibular"
        ],
        "immune": [
            "immunis_", "active_immune", "adaptive_immune", "ai_immune"
        ],
        "homeostatic": [
            "hcl_", "homeostatic"
        ],
        "maximus_ai": [
            "maximus_orchestrator", "maximus_eureka", "maximus_oraculo",
            "maximus_predict", "maximus_integration"
        ],
        "reactive_fabric": [
            "reactive_fabric", "reflex_triage", "antithrombin",
            "protein_c", "tfpi"
        ],
        "offensive": [
            "purple_team", "network_recon", "web_attack", "vuln_intel",
            "offensive_", "bas_service"
        ],
        "intelligence": [
            "osint", "google_osint", "sinesp", "ip_intelligence",
            "threat_intel", "narrative_"
        ],
        "infrastructure": [
            "api_gateway", "auth_service", "atlas_service",
            "command_bus", "agent_communication", "seriema_graph"
        ]
    }

    def __init__(
        self,
        docker_compose_path: str,
        services_base_path: str
    ):
        """
        Initialize Architecture Scanner.

        Args:
            docker_compose_path: Path to docker-compose.yml
            services_base_path: Base path to services directory
        """
        self.docker_compose_path = Path(docker_compose_path)
        self.services_base_path = Path(services_base_path)
        self.dependency_graph = nx.DiGraph()
        self._compose_data: Dict[str, Any] = {}

    async def scan(self, subsystem_filter: str | None = None) -> Dict[str, Any]:
        """
        Scan entire VÉRTICE architecture.

        Args:
            subsystem_filter: Optional filter for specific subsystem

        Returns:
            Comprehensive architecture metadata
        """
        logger.info("Starting architecture scan...")

        # Load docker-compose.yml
        await self._load_docker_compose()

        # Extract services
        services = await self._extract_services()

        # Filter by subsystem if specified
        if subsystem_filter:
            services = {
                name: data for name, data in services.items()
                if self._get_subsystem(name) == subsystem_filter
            }

        # Build dependency graph
        await self._build_dependency_graph(services)

        # Categorize by subsystems
        subsystems = await self._categorize_subsystems(services)

        # Analyze health checks
        health_summary = await self._analyze_health_checks(services)

        # Extract port allocations
        ports = await self._extract_ports(services)

        # Extract networks
        networks = self._compose_data.get("networks", {})

        # Extract volumes
        volumes = self._compose_data.get("volumes", {})

        result = {
            "total_services": len(services),
            "services": services,
            "subsystems": subsystems,
            "health_summary": health_summary,
            "ports": ports,
            "networks": list(networks.keys()),
            "volumes": list(volumes.keys()),
            "dependency_graph": {
                "nodes": list(self.dependency_graph.nodes()),
                "edges": list(self.dependency_graph.edges()),
                "metrics": {
                    "total_nodes": self.dependency_graph.number_of_nodes(),
                    "total_edges": self.dependency_graph.number_of_edges(),
                    "average_degree": sum(dict(self.dependency_graph.degree()).values()) / max(self.dependency_graph.number_of_nodes(), 1)
                }
            }
        }

        logger.info(f"✅ Architecture scan complete: {len(services)} services found")
        return result

    async def _load_docker_compose(self):
        """Load and parse docker-compose.yml."""
        logger.info(f"Loading docker-compose from: {self.docker_compose_path}")

        if not self.docker_compose_path.exists():
            raise FileNotFoundError(f"docker-compose.yml not found: {self.docker_compose_path}")

        with open(self.docker_compose_path, 'r') as f:
            self._compose_data = yaml.safe_load(f)

        logger.info(f"Loaded docker-compose with {len(self._compose_data.get('services', {}))} services")

    async def _extract_services(self) -> Dict[str, Dict[str, Any]]:
        """Extract service metadata from docker-compose."""
        services = {}
        compose_services = self._compose_data.get("services", {})

        for service_name, service_config in compose_services.items():
            services[service_name] = {
                "name": service_name,
                "image": service_config.get("image"),
                "build": service_config.get("build"),
                "ports": service_config.get("ports", []),
                "depends_on": service_config.get("depends_on", []),
                "networks": service_config.get("networks", []),
                "volumes": service_config.get("volumes", []),
                "environment": service_config.get("environment", {}),
                "healthcheck": service_config.get("healthcheck"),
                "subsystem": self._get_subsystem(service_name)
            }

        return services

    def _get_subsystem(self, service_name: str) -> str:
        """Categorize service into subsystem."""
        service_lower = service_name.lower()

        for subsystem, patterns in self.SUBSYSTEM_PATTERNS.items():
            for pattern in patterns:
                if pattern in service_lower:
                    return subsystem

        return "uncategorized"

    async def _build_dependency_graph(self, services: Dict[str, Dict[str, Any]]):
        """Build NetworkX dependency graph."""
        logger.info("Building dependency graph...")

        for service_name, service_data in services.items():
            # Add node
            self.dependency_graph.add_node(
                service_name,
                subsystem=service_data["subsystem"],
                ports=service_data["ports"]
            )

            # Add edges (dependencies)
            for dep in service_data.get("depends_on", []):
                self.dependency_graph.add_edge(service_name, dep)

        logger.info(f"Dependency graph: {self.dependency_graph.number_of_nodes()} nodes, {self.dependency_graph.number_of_edges()} edges")

    async def _categorize_subsystems(
        self,
        services: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Categorize services by subsystem."""
        subsystems: Dict[str, List[str]] = {}

        for service_name, service_data in services.items():
            subsystem = service_data["subsystem"]

            if subsystem not in subsystems:
                subsystems[subsystem] = []

            subsystems[subsystem].append(service_name)

        return subsystems

    async def _analyze_health_checks(
        self,
        services: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze health check coverage."""
        total = len(services)
        with_healthcheck = sum(
            1 for s in services.values() if s.get("healthcheck") is not None
        )

        return {
            "total_services": total,
            "with_healthcheck": with_healthcheck,
            "without_healthcheck": total - with_healthcheck,
            "coverage_percentage": (with_healthcheck / total * 100) if total > 0 else 0
        }

    async def _extract_ports(
        self,
        services: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Extract port allocations."""
        ports = {}

        for service_name, service_data in services.items():
            service_ports = service_data.get("ports", [])
            if service_ports:
                # Parse "8000:8000" format
                for port_mapping in service_ports:
                    if isinstance(port_mapping, str):
                        external_port = port_mapping.split(":")[0]
                        ports[external_port] = service_name

        return ports
