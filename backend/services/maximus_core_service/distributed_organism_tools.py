"""Distributed Organism Tools - FASE 10 Integration

Tools for edge agent management, cloud coordination,
and distributed operations.

NO MOCKS - Production-ready distributed organism.
"""

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class DistributedOrganismTools:
    """Distributed Organism Tools for MAXIMUS AI.

    Integrates FASE 10 services:
    - Edge Agent Service (port 8021)
    - Cloud Coordinator Service (port 8022)
    """

    def __init__(self, gemini_client: Any):
        """Initialize Distributed Organism Tools.

        Args:
            gemini_client: Gemini client instance
        """
        self.gemini_client = gemini_client
        self.edge_url = "http://localhost:8021"
        self.coordinator_url = "http://localhost:8022"

    async def get_edge_status(self, agent_id: str | None = None) -> dict[str, Any]:
        """Get edge agent status and metrics.

        Args:
            agent_id: Specific agent ID (None for all agents)

        Returns:
            Edge agent status, buffer utilization, metrics
        """
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(f"{self.edge_url}/status", timeout=aiohttp.ClientTimeout(total=30)) as response,
            ):
                if response.status == 200:
                    return await response.json()
                error_text = await response.text()
                logger.error(f"Get edge status failed: {error_text}")
                return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in get_edge_status: {e}")
            return {"error": str(e)}

    async def coordinate_multi_edge_scan(
        self,
        targets: list[str],
        scan_type: str = "comprehensive",
        distribute_load: bool = True,
    ) -> dict[str, Any]:
        """Coordinate scan across multiple edge agents.

        Args:
            targets: List of scan targets (IPs, networks, domains)
            scan_type: Scan type (comprehensive, quick, deep)
            distribute_load: Enable load distribution across edges

        Returns:
            Coordination results with task distribution and aggregated findings
        """
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    f"{self.coordinator_url}/coordinate/scan",
                    json={
                        "targets": targets,
                        "scan_type": scan_type,
                        "distribute_load": distribute_load,
                    },
                    timeout=aiohttp.ClientTimeout(total=180),
                ) as response,
            ):
                if response.status == 200:
                    return await response.json()
                error_text = await response.text()
                logger.error(f"Multi-edge scan failed: {error_text}")
                return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in coordinate_multi_edge_scan: {e}")
            return {"error": str(e)}

    async def get_global_metrics(self, time_range_minutes: int = 60) -> dict[str, Any]:
        """Get aggregated global metrics from all edge agents.

        Args:
            time_range_minutes: Time range for metrics aggregation

        Returns:
            Global metrics (events/s, compression ratios, latencies)
        """
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{self.coordinator_url}/metrics/global",
                    params={"time_range_minutes": time_range_minutes},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response,
            ):
                if response.status == 200:
                    return await response.json()
                error_text = await response.text()
                logger.error(f"Get global metrics failed: {error_text}")
                return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in get_global_metrics: {e}")
            return {"error": str(e)}

    async def get_topology(self) -> dict[str, Any]:
        """Get distributed organism topology.

        Returns:
            Network topology with edge agents, health, connections
        """
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{self.coordinator_url}/topology",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response,
            ):
                if response.status == 200:
                    return await response.json()
                error_text = await response.text()
                logger.error(f"Get topology failed: {error_text}")
                return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in get_topology: {e}")
            return {"error": str(e)}

    def list_available_tools(self) -> list[dict[str, Any]]:
        """List all available Distributed Organism tools.

        Returns:
            List of tool metadata
        """
        return [
            {
                "name": "get_edge_status",
                "method_name": "get_edge_status",
                "description": "Get edge agent status and metrics (buffer, batching, compression)",
                "parameters": {"agent_id": "Specific agent ID (None for all agents)"},
            },
            {
                "name": "coordinate_multi_edge_scan",
                "method_name": "coordinate_multi_edge_scan",
                "description": "Coordinate scan across multiple edge agents with load distribution",
                "parameters": {
                    "targets": "List of scan targets (IPs, networks, domains)",
                    "scan_type": "Scan type (comprehensive, quick, deep)",
                    "distribute_load": "Enable load distribution across edges (bool)",
                },
            },
            {
                "name": "get_global_metrics",
                "method_name": "get_global_metrics",
                "description": "Get aggregated global metrics from all edge agents",
                "parameters": {"time_range_minutes": "Time range for metrics aggregation"},
            },
            {
                "name": "get_topology",
                "method_name": "get_topology",
                "description": "Get distributed organism topology with edge agents and connections",
                "parameters": {},
            },
        ]
