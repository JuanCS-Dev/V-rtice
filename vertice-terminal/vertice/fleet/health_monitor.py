"""
💓 Health Monitor - Monitora saúde dos endpoints do fleet

Responsável por:
- Heartbeat tracking (ping/pong)
- Status updates automáticos
- Detecção de endpoints offline
"""

import asyncio
from typing import List, Optional, Callable
from datetime import datetime, timedelta
from .registry import EndpointRegistry, EndpointStatus


class HealthMonitor:
    """
    Monitor de saúde do fleet
    Verifica periodicamente se endpoints estão online/offline
    """

    def __init__(
        self,
        registry: EndpointRegistry,
        check_interval: int = 30,
        offline_threshold: int = 90,
    ):
        """
        Args:
            registry: Registry de endpoints
            check_interval: Intervalo entre checks (segundos)
            offline_threshold: Tempo sem heartbeat pra marcar offline (segundos)
        """
        self.registry = registry
        self.check_interval = check_interval
        self.offline_threshold = offline_threshold
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Inicia monitoring loop"""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Para monitoring loop"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self) -> None:
        """Loop principal de monitoramento"""
        while self._running:
            try:
                await self._check_all_endpoints()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_all_endpoints(self) -> None:
        """Verifica saúde de todos os endpoints"""
        endpoints = self.registry.list()
        threshold = datetime.now() - timedelta(seconds=self.offline_threshold)

        for endpoint in endpoints:
            # Se last_seen é muito antigo, marca como offline
            if endpoint.last_seen < threshold and endpoint.status == EndpointStatus.ONLINE:
                self.registry.update_status(endpoint.id, EndpointStatus.OFFLINE)
                print(f"⚠️  Endpoint {endpoint.hostname} marked as OFFLINE")

    async def heartbeat(self, endpoint_id: str) -> None:
        """
        Recebe heartbeat de um endpoint

        Args:
            endpoint_id: ID do endpoint
        """
        endpoint = self.registry.get(endpoint_id)
        if endpoint:
            # Atualiza last_seen e marca como online
            self.registry.update_status(endpoint_id, EndpointStatus.ONLINE)

    def get_health_summary(self) -> dict:
        """
        Retorna resumo de saúde do fleet

        Returns:
            Dicionário com estatísticas de saúde
        """
        stats = self.registry.get_stats()

        online = stats["by_status"].get("online", 0)
        offline = stats["by_status"].get("offline", 0)
        total = stats["total"]

        health_percentage = (online / total * 100) if total > 0 else 0

        return {
            "total": total,
            "online": online,
            "offline": offline,
            "unknown": stats["by_status"].get("unknown", 0),
            "maintenance": stats["by_status"].get("maintenance", 0),
            "health_percentage": round(health_percentage, 2),
        }
