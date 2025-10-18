"""Lymphnode Metrics - Metrics Collection and Reporting

Extracted from LinfonodoDigital as part of FASE 3 Desacoplamento.

This module implements metrics collection including threat detection counters,
neutralization tracking, clonal expansion statistics, and comprehensive
lymphnode state reporting.

Responsibilities:
- Threat detection counting (atomic)
- Neutralization tracking (atomic)
- Clonal expansion statistics (created/destroyed)
- Metrics aggregation and reporting
- Statistics snapshot generation

Biological Inspiration:
-----------------------
In biological systems, the immune system tracks various metrics:
- Pathogen encounter count (threat detection)
- Successful neutralizations (adaptive immunity effectiveness)
- Lymphocyte proliferation (clonal expansion)
- System resource utilization

This digital implementation mirrors these biological tracking mechanisms,
providing observability into immune system performance.

NO MOCK, NO PLACEHOLDER, NO TODO - Production ready.
DOUTRINA VERTICE compliant: Quality-first, production-ready code.

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

import logging
from typing import Any, Dict

from active_immune_core.coordination.thread_safe_structures import AtomicCounter

logger = logging.getLogger(__name__)


class LymphnodeMetrics:
    """Collects and reports lymphnode operational metrics.

    This class implements metrics collection logic extracted from
    LinfonodoDigital, tracking threats, neutralizations, and clonal
    expansion statistics.

    Attributes:
        lymphnode_id: Lymphnode identifier
        total_ameacas_detectadas: Atomic counter for threats detected
        total_neutralizacoes: Atomic counter for neutralizations
        total_clones_criados: Atomic counter for clones created
        total_clones_destruidos: Atomic counter for clones destroyed

    Example:
        >>> metrics = LymphnodeMetrics(lymphnode_id="lymph-1")
        >>> await metrics.increment_threats_detected()
        >>> await metrics.increment_neutralizations()
        >>> stats = await metrics.get_stats()
        >>> assert stats["total_threats_detected"] == 1
    """

    def __init__(self, lymphnode_id: str):
        """Initialize LymphnodeMetrics.

        Args:
            lymphnode_id: Unique lymphnode identifier
        """
        self.lymphnode_id = lymphnode_id

        # Atomic counters (thread-safe)
        self.total_ameacas_detectadas = AtomicCounter()
        self.total_neutralizacoes = AtomicCounter()
        self.total_clones_criados = AtomicCounter()
        self.total_clones_destruidos = AtomicCounter()

        logger.info(f"LymphnodeMetrics initialized: lymphnode={lymphnode_id}")

    async def increment_threats_detected(self, count: int = 1) -> int:
        """Increment threats detected counter.

        EXTRACTED from lymphnode.py (line 628)

        Args:
            count: Number to increment (default 1)

        Returns:
            New total count
        """
        for _ in range(count):
            await self.total_ameacas_detectadas.increment()
        return await self.total_ameacas_detectadas.get()

    async def increment_neutralizations(self, count: int = 1) -> int:
        """Increment neutralizations counter.

        EXTRACTED from lymphnode.py (line 637)

        Args:
            count: Number to increment (default 1)

        Returns:
            New total count
        """
        for _ in range(count):
            await self.total_neutralizacoes.increment()
        return await self.total_neutralizacoes.get()

    async def increment_clones_created(self, count: int = 1) -> int:
        """Increment clones created counter.

        EXTRACTED from lymphnode.py (line 488)

        Args:
            count: Number to increment (default 1)

        Returns:
            New total count
        """
        for _ in range(count):
            await self.total_clones_criados.increment()
        return await self.total_clones_criados.get()

    async def increment_clones_destroyed(self, count: int = 1) -> int:
        """Increment clones destroyed counter.

        EXTRACTED from lymphnode.py (line 512)

        Args:
            count: Number to increment (default 1)

        Returns:
            New total count
        """
        for _ in range(count):
            await self.total_clones_destruidos.increment()
        return await self.total_clones_destruidos.get()

    async def get_threats_detected(self) -> int:
        """Get total threats detected.

        Returns:
            Total threats detected
        """
        return await self.total_ameacas_detectadas.get()

    async def get_neutralizations(self) -> int:
        """Get total neutralizations.

        Returns:
            Total neutralizations
        """
        return await self.total_neutralizacoes.get()

    async def get_clones_created(self) -> int:
        """Get total clones created.

        Returns:
            Total clones created
        """
        return await self.total_clones_criados.get()

    async def get_clones_destroyed(self) -> int:
        """Get total clones destroyed.

        Returns:
            Total clones destroyed
        """
        return await self.total_clones_destruidos.get()

    async def get_net_clones(self) -> int:
        """Get net clones (created - destroyed).

        Returns:
            Net clone count
        """
        created = await self.total_clones_criados.get()
        destroyed = await self.total_clones_destruidos.get()
        return created - destroyed

    async def get_neutralization_rate(self) -> float:
        """Calculate neutralization rate (neutralizations / threats).

        Returns:
            Neutralization rate (0.0-1.0+)
        """
        threats = await self.total_ameacas_detectadas.get()
        neutralizations = await self.total_neutralizacoes.get()

        if threats == 0:
            return 0.0

        return neutralizations / threats

    async def reset_all(self) -> None:
        """Reset all counters to zero.

        WARNING: Use with caution, typically only for testing.
        """
        await self.total_ameacas_detectadas.set(0)
        await self.total_neutralizacoes.set(0)
        await self.total_clones_criados.set(0)
        await self.total_clones_destruidos.set(0)

        logger.warning(f"Lymphnode {self.lymphnode_id} metrics reset to zero")

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive metrics statistics.

        EXTRACTED from lymphnode.py:get_metrics() (lines 946-966)

        Returns:
            Dict with all metrics
        """
        threats = await self.total_ameacas_detectadas.get()
        neutralizations = await self.total_neutralizacoes.get()
        clones_created = await self.total_clones_criados.get()
        clones_destroyed = await self.total_clones_destruidos.get()

        return {
            "lymphnode_id": self.lymphnode_id,
            "total_threats_detected": threats,
            "total_neutralizations": neutralizations,
            "total_clones_created": clones_created,
            "total_clones_destroyed": clones_destroyed,
            "net_clones": clones_created - clones_destroyed,
            "neutralization_rate": (neutralizations / threats if threats > 0 else 0.0),
        }

    def __repr__(self) -> str:
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                metrics_str = "metrics=?"
            else:
                threats = loop.run_until_complete(self.total_ameacas_detectadas.get())
                neutralizations = loop.run_until_complete(self.total_neutralizacoes.get())
                metrics_str = f"threats={threats}, neutralizations={neutralizations}"
        except Exception:
            metrics_str = "metrics=?"

        return f"LymphnodeMetrics(lymphnode={self.lymphnode_id}, {metrics_str})"
