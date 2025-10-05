"""
Distributed Connector - Distributed Organism Services
======================================================

Conector para serviços de organismo distribuído (Edge + Cloud).

Serviços integrados:

FASE 10 (Distributed Organism):
    - Edge Agent Service (local collection, batching, compression)
    - Cloud Coordinator Service (aggregation, load balancing, multi-tenant)
    - Federation Protocol (cross-organization threat sharing)

Author: Vértice Team
Version: 1.0.0
"""

from typing import Dict, Any, Optional
from .base import BaseConnector


class DistributedConnector(BaseConnector):
    """
    Conector para serviços de organismo distribuído.

    Integra edge agents e cloud coordinator para operações distribuídas
    em escala global.
    """

    def __init__(self):
        """Inicializa DistributedConnector via Maximus AI Core."""
        super().__init__(
            service_name="Distributed Organism Services (via Maximus)",
            base_url="http://localhost:8001",
            timeout=180  # Operações distribuídas podem demorar
        )

    async def health_check(self) -> bool:
        """Verifica saúde do Maximus AI Core."""
        try:
            data = await self._get("/health")
            return data is not None and data.get("status") == "healthy"
        except Exception:
            return False

    async def get_edge_status(
        self,
        agent_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém status e métricas de edge agent.

        Args:
            agent_id: ID do agent específico (None para todos os agents)

        Returns:
            Status do edge agent, utilização de buffer, métricas

        Examples:
            >>> status = await connector.get_edge_status()
            >>> print(f"Active agents: {len(status['agents'])}")

            >>> agent_status = await connector.get_edge_status(agent_id="edge-001")
            >>> print(f"Buffer usage: {agent_status['buffer_utilization']}%")
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "get_edge_status",
                "params": {
                    "agent_id": agent_id
                }
            }
        )

    async def coordinate_multi_edge_scan(
        self,
        targets: list,
        scan_type: str = "comprehensive",
        distribute_load: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Coordena scan através de múltiplos edge agents.

        Args:
            targets: Lista de alvos de scan (IPs, networks, domains)
            scan_type: Tipo de scan (comprehensive, quick, deep)
            distribute_load: Habilita distribuição de carga entre edges

        Returns:
            Resultados de coordenação com distribuição de tarefas e findings agregados

        Examples:
            >>> results = await connector.coordinate_multi_edge_scan(
            ...     targets=["192.168.1.0/24", "10.0.0.0/16", "example.com"],
            ...     scan_type="comprehensive",
            ...     distribute_load=True
            ... )
            >>> print(f"Total findings: {results['total_findings']}")
            >>> print(f"Agents used: {len(results['agent_distribution'])}")
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "coordinate_multi_edge_scan",
                "params": {
                    "targets": targets,
                    "scan_type": scan_type,
                    "distribute_load": distribute_load
                }
            }
        )

    async def get_global_metrics(
        self,
        time_range_minutes: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém métricas globais agregadas de todos os edge agents.

        Args:
            time_range_minutes: Intervalo de tempo para agregação de métricas

        Returns:
            Métricas globais (events/s, compression ratios, latencies)

        Examples:
            >>> metrics = await connector.get_global_metrics(time_range_minutes=30)
            >>> print(f"Global throughput: {metrics['events_per_second']}")
            >>> print(f"Avg compression: {metrics['avg_compression_ratio']}")
            >>> print(f"P95 latency: {metrics['p95_latency_ms']}ms")
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "get_global_metrics",
                "params": {
                    "time_range_minutes": time_range_minutes
                }
            }
        )

    async def get_topology(self) -> Optional[Dict[str, Any]]:
        """
        Obtém topologia do organismo distribuído.

        Returns:
            Topologia de rede com edge agents, saúde, conexões

        Examples:
            >>> topology = await connector.get_topology()
            >>> print(f"Total agents: {topology['agent_count']}")
            >>> print(f"Healthy: {topology['healthy_count']}")
            >>> print(f"Regions: {topology['regions']}")
            >>>
            >>> for agent in topology['agents']:
            ...     print(f"{agent['id']}: {agent['health']} - {agent['location']}")
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "get_topology",
                "params": {}
            }
        )

    async def close(self):
        """Fecha o cliente HTTP."""
        await self.client.aclose()
