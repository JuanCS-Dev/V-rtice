"""Agent Factory - Dynamic immune cell creation and management

The Agent Factory implements:
1. Dynamic agent creation (on-demand spawning)
2. Clonal selection (specialized clones)
3. Somatic hypermutation (evolutionary improvement)
4. Agent lifecycle management (tracking, shutdown)

Inspired by biological clonal selection:
- Antigen stimulation triggers cloning
- High-affinity clones proliferate
- Low-affinity clones undergo apoptosis

PRODUCTION-READY: No mocks, type hints, error handling, graceful degradation.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from .base import AgenteImunologicoBase
from .macrofago import MacrofagoDigital
from .models import AgentType
from .neutrofilo import NeutrofiloDigital
from .nk_cell import CelulaNKDigital

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating and managing immune agents.

    Capabilities:
    - Create agents of any type (Macrophage, NK Cell, Neutrophil)
    - Clone agents (clonal selection)
    - Mutate clones (somatic hypermutation)
    - Track active agents
    - Graceful shutdown

    Usage:
        factory = AgentFactory()
        macrofago = await factory.create_agent(AgentType.MACROFAGO, area_patrulha="subnet_10_0_1_0")
        clone = await factory.clone_agent(macrofago, mutate=True)
    """

    def __init__(
        self,
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        rte_service_url: str = "http://localhost:8002",
        ethical_ai_url: str = "http://localhost:8100",
    ):
        """
        Initialize Agent Factory.

        Args:
            kafka_bootstrap: Kafka broker for cytokines
            redis_url: Redis URL for hormones
            rte_service_url: RTE Service URL
            ethical_ai_url: Ethical AI service URL
        """
        self.kafka_bootstrap = kafka_bootstrap
        self.redis_url = redis_url
        self.rte_service_url = rte_service_url
        self.ethical_ai_url = ethical_ai_url

        # Agent registry (track all created agents)
        self._agents: Dict[str, AgenteImunologicoBase] = {}

        # Agent type mapping
        self._agent_classes: Dict[AgentType, Type[AgenteImunologicoBase]] = {
            AgentType.MACROFAGO: MacrofagoDigital,
            AgentType.NK_CELL: CelulaNKDigital,
            AgentType.NEUTROFILO: NeutrofiloDigital,
        }

        # Statistics
        self.agents_created_total: int = 0
        self.agents_cloned_total: int = 0
        self.agents_destroyed_total: int = 0

        logger.info("AgentFactory initialized")

    # ==================== AGENT CREATION ====================

    async def create_agent(
        self,
        tipo: AgentType,
        area_patrulha: str,
        **kwargs,
    ) -> AgenteImunologicoBase:
        """
        Create a new immune agent.

        Args:
            tipo: Agent type (MACROFAGO, NK_CELL, NEUTROFILO)
            area_patrulha: Network zone to patrol
            **kwargs: Additional agent-specific parameters

        Returns:
            Created agent instance

        Raises:
            ValueError: If agent type not supported
        """
        if tipo not in self._agent_classes:
            raise ValueError(
                f"Unsupported agent type: {tipo}. "
                f"Supported types: {list(self._agent_classes.keys())}"
            )

        agent_class = self._agent_classes[tipo]

        logger.info(f"Creating agent: {tipo} (area={area_patrulha})")

        # Create agent with factory defaults + custom kwargs
        agent = agent_class(
            area_patrulha=area_patrulha,
            kafka_bootstrap=self.kafka_bootstrap,
            redis_url=self.redis_url,
            rte_service_url=self.rte_service_url,
            ethical_ai_url=self.ethical_ai_url,
            **kwargs,
        )

        # Register agent
        self._agents[agent.state.id] = agent
        self.agents_created_total += 1

        logger.info(
            f"Agent created: {agent.state.id[:8]} (type={tipo}, total={len(self._agents)})"
        )

        return agent

    async def clone_agent(
        self,
        original: AgenteImunologicoBase,
        mutate: bool = False,
        mutation_rate: float = 0.1,
    ) -> AgenteImunologicoBase:
        """
        Clone an existing agent (clonal selection).

        Biological clonal selection:
        - High-affinity B/T cells proliferate upon antigen encounter
        - Clones inherit parent's specificity
        - Somatic hypermutation introduces diversity

        Args:
            original: Agent to clone
            mutate: Whether to apply somatic hypermutation
            mutation_rate: Mutation rate (0-1) for parameter perturbation

        Returns:
            Cloned agent
        """
        logger.info(
            f"Cloning agent: {original.state.id[:8]} (type={original.state.tipo}, mutate={mutate})"
        )

        # Create clone with same parameters
        clone = await self.create_agent(
            tipo=original.state.tipo,
            area_patrulha=original.state.area_patrulha,
        )

        # Copy specialized parameters
        if hasattr(original, "baseline_behavior"):
            # NK Cell baseline
            clone.baseline_behavior = original.baseline_behavior.copy()

        if hasattr(original, "fagocitados"):
            # Macrophage memory (empty for clone)
            clone.fagocitados = []

        # Apply somatic hypermutation (parameter perturbation)
        if mutate:
            self._apply_somatic_hypermutation(clone, mutation_rate)

        # Mark as cloned
        clone.state.especializacao = f"clone_of_{original.state.id[:8]}"

        # Track statistics
        self.agents_cloned_total += 1

        logger.info(
            f"Agent cloned: {clone.state.id[:8]} "
            f"(parent={original.state.id[:8]}, mutated={mutate})"
        )

        return clone

    def _apply_somatic_hypermutation(
        self,
        agent: AgenteImunologicoBase,
        mutation_rate: float,
    ) -> None:
        """
        Apply somatic hypermutation (parameter perturbation).

        Mutates:
        - Aggressiveness (+/- mutation_rate)
        - Sensitivity (+/- mutation_rate)

        In production, this would use:
        - Genetic algorithms
        - Neuroevolution (NEAT)
        - Bayesian optimization

        Args:
            agent: Agent to mutate
            mutation_rate: Mutation magnitude (0-1)
        """
        import random

        logger.debug(f"Applying somatic hypermutation to {agent.state.id[:8]}")

        # Mutate aggressiveness
        delta_aggression = random.uniform(-mutation_rate, mutation_rate)
        agent.state.nivel_agressividade = max(
            0.0, min(1.0, agent.state.nivel_agressividade + delta_aggression)
        )

        # Mutate sensitivity
        delta_sensitivity = random.uniform(-mutation_rate, mutation_rate)
        agent.state.sensibilidade = max(
            0.0, min(1.0, agent.state.sensibilidade + delta_sensitivity)
        )

        logger.debug(
            f"Mutation applied: aggression={agent.state.nivel_agressividade:.2f}, "
            f"sensitivity={agent.state.sensibilidade:.2f}"
        )

    # ==================== CLONAL EXPANSION ====================

    async def clonal_expansion(
        self,
        original: AgenteImunologicoBase,
        num_clones: int = 5,
        mutate: bool = True,
    ) -> List[AgenteImunologicoBase]:
        """
        Create multiple clones (clonal expansion).

        Triggered when:
        - High-affinity detection (specialized clone needed)
        - Overwhelming threat (need more agents)

        Args:
            original: Agent to clone
            num_clones: Number of clones to create
            mutate: Whether to apply somatic hypermutation

        Returns:
            List of cloned agents
        """
        logger.info(
            f"Clonal expansion: {num_clones} clones of {original.state.id[:8]}"
        )

        clones = []

        for i in range(num_clones):
            clone = await self.clone_agent(original, mutate=mutate)
            clones.append(clone)

        logger.info(
            f"Clonal expansion complete: {num_clones} clones created "
            f"(total agents={len(self._agents)})"
        )

        return clones

    # ==================== AGENT MANAGEMENT ====================

    def get_agent(self, agent_id: str) -> Optional[AgenteImunologicoBase]:
        """
        Get agent by ID.

        Args:
            agent_id: Agent UUID

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_id)

    def get_agents_by_type(self, tipo: AgentType) -> List[AgenteImunologicoBase]:
        """
        Get all agents of a specific type.

        Args:
            tipo: Agent type

        Returns:
            List of agents
        """
        return [agent for agent in self._agents.values() if agent.state.tipo == tipo]

    def get_active_agents(self) -> List[AgenteImunologicoBase]:
        """
        Get all active (running) agents.

        Returns:
            List of active agents
        """
        return [agent for agent in self._agents.values() if agent.state.ativo]

    def get_all_agents(self) -> List[AgenteImunologicoBase]:
        """
        Get all agents.

        Returns:
            List of all agents
        """
        return list(self._agents.values())

    async def destroy_agent(self, agent_id: str) -> bool:
        """
        Destroy (remove) an agent.

        Args:
            agent_id: Agent UUID

        Returns:
            True if destroyed, False if not found
        """
        agent = self._agents.get(agent_id)

        if not agent:
            logger.warning(f"Agent not found: {agent_id}")
            return False

        logger.info(f"Destroying agent: {agent_id[:8]} (type={agent.state.tipo})")

        # Stop agent if running
        if agent._running:
            await agent.parar()

        # Remove from registry
        del self._agents[agent_id]
        self.agents_destroyed_total += 1

        logger.info(
            f"Agent destroyed: {agent_id[:8]} (total agents={len(self._agents)})"
        )

        return True

    async def shutdown_all(self) -> None:
        """
        Shutdown all agents gracefully.

        Stops all running agents and clears registry.
        """
        logger.info(f"Shutting down all agents (total={len(self._agents)})")

        # Stop all running agents
        for agent in self._agents.values():
            if agent._running:
                try:
                    await agent.parar()
                except Exception as e:
                    logger.error(f"Error stopping agent {agent.state.id[:8]}: {e}")

        # Clear registry
        num_agents = len(self._agents)
        self._agents.clear()

        logger.info(f"All agents shutdown: {num_agents} agents stopped")

    # ==================== METRICS ====================

    def get_factory_metrics(self) -> Dict[str, Any]:
        """
        Get factory statistics.

        Returns:
            Dict with factory metrics
        """
        agents_by_type = {
            agent_type: len(self.get_agents_by_type(agent_type))
            for agent_type in [AgentType.MACROFAGO, AgentType.NK_CELL, AgentType.NEUTROFILO]
        }

        return {
            "agents_total": len(self._agents),
            "agents_active": len(self.get_active_agents()),
            "agents_by_type": agents_by_type,
            "agents_created_total": self.agents_created_total,
            "agents_cloned_total": self.agents_cloned_total,
            "agents_destroyed_total": self.agents_destroyed_total,
            "cloning_rate": (
                self.agents_cloned_total / self.agents_created_total
                if self.agents_created_total > 0
                else 0.0
            ),
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"AgentFactory(agents={len(self._agents)}, "
            f"active={len(self.get_active_agents())}, "
            f"created={self.agents_created_total}, "
            f"cloned={self.agents_cloned_total})"
        )
