"""Agent Orchestrator - Agent Lifecycle Management

Extracted from LinfonodoDigital as part of FASE 3 Desacoplamento.

This module implements agent orchestration logic including registration,
clonal expansion, clone destruction, and apoptosis signaling.

Responsibilities:
- Agent registration and removal
- Clonal expansion (specialized agent cloning)
- Clone destruction (apoptosis)
- Rate limiting via ClonalExpansionRateLimiter
- Somatic hypermutation (clone variation)
- Apoptosis signal broadcasting

Biological Inspiration:
-----------------------
In biological systems, lymph nodes orchestrate immune cell responses:
- B/T cell registration (lymph node migration)
- Clonal expansion (proliferation upon antigen recognition)
- Somatic hypermutation (antibody affinity maturation)
- Apoptosis (programmed cell death for homeostasis)
- Resource constraints (limited lymph node capacity)

This digital implementation mirrors these biological mechanisms, orchestrating
agent lifecycle to respond to threats while maintaining homeostatic balance.

NO MOCK, NO PLACEHOLDER, NO TODO - Production ready.
DOUTRINA VERTICE compliant: Quality-first, production-ready code.

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from agents.agent_factory import AgentFactory
from agents.models import AgenteState, AgentType
from coordination.exceptions import (
    AgentOrchestrationError,
    LymphnodeRateLimitError,
    LymphnodeResourceExhaustedError,
)
from coordination.rate_limiter import ClonalExpansionRateLimiter
from coordination.thread_safe_structures import AtomicCounter

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates agent lifecycle and clonal expansion.

    This class implements agent management logic extracted from
    LinfonodoDigital, including registration, clonal expansion with
    rate limiting, clone destruction, and apoptosis signaling.

    Attributes:
        lymphnode_id: Lymphnode identifier
        area: Network area (subnet, zone, datacenter)
        factory: AgentFactory for creating new agents
        rate_limiter: ClonalExpansionRateLimiter for controlling expansion
        redis_client: Redis client for apoptosis signals (optional)

    Example:
        >>> orchestrator = AgentOrchestrator(
        ...     lymphnode_id="lymph-1",
        ...     area="network-zone-1",
        ...     factory=agent_factory,
        ... )
        >>> clone_ids = await orchestrator.create_clones(
        ...     tipo_base=AgentType.NEUTROPHIL,
        ...     especializacao="malware-x",
        ...     quantidade=5,
        ... )
    """

    def __init__(
        self,
        lymphnode_id: str,
        area: str,
        factory: AgentFactory,
        rate_limiter: Optional[ClonalExpansionRateLimiter] = None,
        redis_client: Optional[Any] = None,
    ):
        """Initialize AgentOrchestrator.

        Args:
            lymphnode_id: Unique lymphnode identifier
            area: Network area (subnet, zone, datacenter)
            factory: AgentFactory instance for creating agents
            rate_limiter: Rate limiter (creates default if None)
            redis_client: Redis client for apoptosis signals (optional)
        """
        self.lymphnode_id = lymphnode_id
        self.area = area
        self.factory = factory
        self.redis_client = redis_client

        # Rate limiter (default or injected)
        self.rate_limiter = rate_limiter or ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=10,
            max_total_agents=100,
        )

        # Agent registry
        self.agentes_ativos: Dict[str, AgenteState] = {}
        self.agentes_dormindo: Set[str] = set()

        # Statistics (ATOMIC COUNTERS)
        self._total_clones_criados = AtomicCounter()
        self._total_clones_destruidos = AtomicCounter()

        logger.info(f"AgentOrchestrator initialized: lymphnode={lymphnode_id}, area={area}")

    async def register_agent(self, agente_state: AgenteState) -> None:
        """Register agent with orchestrator.

        EXTRACTED from lymphnode.py:registrar_agente() (lines 423-439)

        Args:
            agente_state: Agent state snapshot
        """
        self.agentes_ativos[agente_state.id] = agente_state

        logger.info(f"Agent {agente_state.id[:8]} ({agente_state.tipo}) registered with lymphnode {self.lymphnode_id}")

    async def remove_agent(self, agente_id: str) -> None:
        """Remove agent from orchestrator (apoptosis/migration).

        EXTRACTED from lymphnode.py:remover_agente() (lines 441-455)

        Args:
            agente_id: Agent UUID
        """
        if agente_id in self.agentes_ativos:
            agente_state = self.agentes_ativos[agente_id]
            del self.agentes_ativos[agente_id]

            logger.info(f"Agent {agente_id[:8]} ({agente_state.tipo}) removed from lymphnode {self.lymphnode_id}")

    async def create_clones(
        self,
        tipo_base: AgentType,
        especializacao: str,
        quantidade: int = 5,
    ) -> List[str]:
        """Create specialized agent clones (clonal expansion) WITH RATE LIMITING.

        EXTRACTED from lymphnode.py:clonar_agente() (lines 457-547)

        Triggered by:
        - Persistent threat (pattern detection)
        - High cytokine concentration (inflammation)
        - MAXIMUS directive (manual intervention)

        Args:
            tipo_base: Base agent type to clone
            especializacao: Specialization marker
            quantidade: Number of clones to create

        Returns:
            List of clone IDs

        Raises:
            LymphnodeRateLimitError: If rate limit exceeded
            LymphnodeResourceExhaustedError: If resource limit exceeded
            AgentOrchestrationError: If clone creation fails
        """
        # RATE LIMITING: Check before creating clones
        try:
            await self.rate_limiter.check_clonal_expansion(
                especializacao=especializacao,
                quantidade=quantidade,
                current_total_agents=len(self.agentes_ativos),
            )
        except (LymphnodeRateLimitError, LymphnodeResourceExhaustedError) as e:
            logger.warning(f"Lymphnode {self.lymphnode_id} clonal expansion BLOCKED: {e}")
            raise

        logger.info(
            f"Lymphnode {self.lymphnode_id} initiating clonal expansion: "
            f"{quantidade} {tipo_base} agents (specialization={especializacao})"
        )

        clone_ids = []
        failures = 0

        for i in range(quantidade):
            try:
                # Create agent via factory
                agente = await self.factory.create_agent(
                    tipo=tipo_base,
                    area_patrulha=self.area,
                )

                # Set specialization
                agente.state.especializacao = especializacao

                # Apply somatic hypermutation (variation in sensitivity/aggressiveness)
                mutation = (i * 0.04) - 0.1  # Range: -10% to +10%
                agente.state.sensibilidade = max(0.0, min(1.0, agente.state.sensibilidade + mutation))

                # Start agent
                await agente.iniciar()

                # Register with orchestrator
                await self.register_agent(agente.state)

                clone_ids.append(agente.state.id)

                # ATOMIC INCREMENT
                await self._total_clones_criados.increment()

            except Exception as e:
                logger.error(f"Failed to create clone {i}: {e}")
                failures += 1

        # If too many failures, raise error
        if failures > quantidade // 2:
            raise AgentOrchestrationError(f"Clonal expansion failed: {failures}/{quantidade} clones failed to create")

        logger.info(f"Clonal expansion complete: {len(clone_ids)}/{quantidade} clones created")

        return clone_ids

    async def destroy_clones(self, especializacao: str) -> int:
        """Destroy clones with specific specialization (apoptosis).

        EXTRACTED from lymphnode.py:destruir_clones() (lines 549-585)

        Triggered by:
        - Threat eliminated
        - Resource constraints
        - Homeostatic regulation (too many agents)

        Args:
            especializacao: Specialization marker

        Returns:
            Number of clones destroyed
        """
        destruidos = 0

        for agente_id, state in list(self.agentes_ativos.items()):
            if state.especializacao == especializacao:
                # Send apoptosis signal via hormone (graceful shutdown)
                await self.send_apoptosis_signal(agente_id)

                # Remove from registry
                await self.remove_agent(agente_id)

                destruidos += 1
                # ATOMIC INCREMENT
                await self._total_clones_destruidos.increment()

        # Release from rate limiter
        await self.rate_limiter.release_clones(especializacao, destruidos)

        logger.info(f"Lymphnode {self.lymphnode_id} destroyed {destruidos} clones ({especializacao})")

        return destruidos

    async def send_apoptosis_signal(self, agente_id: str) -> None:
        """Send apoptosis signal to agent via Redis.

        EXTRACTED from lymphnode.py:_send_apoptosis_signal() (lines 587-613)

        Args:
            agente_id: Agent UUID
        """
        if not self.redis_client:
            logger.debug("Redis client not available for apoptosis signal")
            return

        try:
            await self.redis_client.publish(
                f"agent:{agente_id}:apoptosis",
                json.dumps(
                    {
                        "lymphnode_id": self.lymphnode_id,
                        "reason": "lymphnode_directive",
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            )

            logger.debug(f"Apoptosis signal sent to agent {agente_id[:8]}")

        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Apoptosis signal failed (Redis unavailable): {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending apoptosis signal: {e}")

    def get_active_agents(self) -> Dict[str, AgenteState]:
        """Get all active agents.

        Returns:
            Dict mapping agent_id → AgenteState
        """
        return self.agentes_ativos.copy()

    def get_agents_by_specialization(self, especializacao: str) -> List[AgenteState]:
        """Get all agents with specific specialization.

        Args:
            especializacao: Specialization marker

        Returns:
            List of AgenteState for matching agents
        """
        return [state for state in self.agentes_ativos.values() if state.especializacao == especializacao]

    def get_agent_count(self) -> int:
        """Get total number of active agents.

        Returns:
            Number of active agents
        """
        return len(self.agentes_ativos)

    async def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics.

        Returns:
            Dict with orchestration stats
        """
        return {
            "lymphnode_id": self.lymphnode_id,
            "area": self.area,
            "active_agents": len(self.agentes_ativos),
            "sleeping_agents": len(self.agentes_dormindo),
            "total_clones_created": await self._total_clones_criados.get(),
            "total_clones_destroyed": await self._total_clones_destruidos.get(),
            "rate_limiter_stats": self.rate_limiter.get_stats(),
        }

    def __repr__(self) -> str:
        return (
            f"AgentOrchestrator("
            f"lymphnode={self.lymphnode_id}, "
            f"area={self.area}, "
            f"active_agents={len(self.agentes_ativos)})"
        )
