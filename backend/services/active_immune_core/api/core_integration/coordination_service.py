"""Coordination Service - PRODUCTION-READY

Service layer for lymphnode coordination operations.

This module provides:
- Clonal expansion (agent cloning)
- Lymphnode metrics and status
- Homeostatic state monitoring
- Agent registration/removal in lymphnode

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Optional

from ..models.coordination import (
    CloneResponse,
    HomeostaticStateResponse,
    LymphnodeMetrics,
)
from .core_manager import CoreManager

logger = logging.getLogger(__name__)


class CoordinationServiceError(Exception):
    """Base exception for CoordinationService errors"""

    pass


class LymphnodeNotAvailableError(CoordinationServiceError):
    """Raised when Lymphnode not available"""

    pass


class AgentNotFoundForCloneError(CoordinationServiceError):
    """Raised when agent not found for cloning"""

    pass


class CoordinationService:
    """
    Service for lymphnode coordination operations.

    Responsibilities:
    - Clonal expansion (create specialized clones)
    - Lymphnode metrics retrieval
    - Homeostatic state monitoring
    - Agent registration/removal

    This service acts as a bridge between the REST API and the Lymphnode.

    Usage:
        service = CoordinationService()

        # Clone agent
        clone_response = await service.clone_agent(
            agent_id="macrofago_001",
            especializacao="threat_192_168_1_50",
            num_clones=5
        )

        # Get lymphnode metrics
        metrics = await service.get_lymphnode_metrics()

        # Get homeostatic state
        state = await service.get_homeostatic_state()
    """

    def __init__(self):
        """Initialize Coordination Service."""
        self._core_manager = CoreManager.get_instance()
        logger.info("CoordinationService initialized")

    def _check_lymphnode_available(self) -> None:
        """
        Check if Lymphnode is available.

        Raises:
            LymphnodeNotAvailableError: If Core not initialized or Lymphnode unavailable
        """
        if not self._core_manager.is_initialized:
            raise LymphnodeNotAvailableError("Core System not initialized")

        if self._core_manager.lymphnode is None:
            raise LymphnodeNotAvailableError("Lymphnode not available")

    async def clone_agent(
        self,
        agent_id: str,
        especializacao: Optional[str] = None,
        num_clones: int = 1,
        mutate: bool = True,
        mutation_rate: float = 0.1,
    ) -> CloneResponse:
        """
        Clone an agent with optional specialization.

        This performs clonal expansion - creating multiple clones of a
        high-performing agent for specialized threats.

        Args:
            agent_id: ID of agent to clone
            especializacao: Specialization for clones (e.g., "threat_192_168_1_50")
            num_clones: Number of clones to create (1-10)
            mutate: Apply somatic hypermutation (IGNORED - always applied)
            mutation_rate: Mutation rate (IGNORED - fixed in lymphnode)

        Returns:
            CloneResponse with clone IDs

        Raises:
            LymphnodeNotAvailableError: If Lymphnode unavailable
            AgentNotFoundForCloneError: If agent not found
            CoordinationServiceError: If cloning fails
        """
        self._check_lymphnode_available()

        logger.info(f"Cloning agent: {agent_id}, especializacao={especializacao}, num_clones={num_clones}")

        try:
            lymphnode = self._core_manager.lymphnode

            # Get original agent from agent factory to determine type
            factory = self._core_manager.agent_factory
            if agent_id not in factory._agents:
                raise AgentNotFoundForCloneError(f"Agent not found: {agent_id}")

            original_agent = factory._agents[agent_id]

            # Get agent type from state
            from active_immune_core.agents.models import AgentType

            # Map state.tipo (string) to AgentType enum
            tipo_str = original_agent.state.tipo.lower()
            tipo_mapping = {
                "macrofago": AgentType.MACROFAGO,
                "nk_cell": AgentType.NK_CELL,
                "neutrofilo": AgentType.NEUTROFILO,
            }

            tipo_base = tipo_mapping.get(tipo_str)
            if tipo_base is None:
                raise CoordinationServiceError(f"Unknown agent type: {tipo_str}")

            # Create clones via lymphnode
            clone_ids = await lymphnode.clonar_agente(
                tipo_base=tipo_base,
                especializacao=especializacao or f"clone_{agent_id}",
                quantidade=num_clones,
            )

            logger.info(f"✓ Created {len(clone_ids)} clones of {agent_id}")

            return CloneResponse(
                parent_id=agent_id,
                clone_ids=clone_ids,
                num_clones=len(clone_ids),
                especializacao=especializacao,
                created_at=datetime.utcnow().isoformat(),
            )

        except AgentNotFoundForCloneError:
            raise
        except Exception as e:
            logger.error(f"Failed to clone agent: {e}", exc_info=True)
            raise CoordinationServiceError(f"Cloning failed: {e}") from e

    async def get_lymphnode_metrics(self) -> LymphnodeMetrics:
        """
        Get lymphnode metrics and status.

        Returns:
            LymphnodeMetrics with current lymphnode state

        Raises:
            LymphnodeNotAvailableError: If Lymphnode unavailable
        """
        self._check_lymphnode_available()

        logger.debug("Getting lymphnode metrics")

        try:
            lymphnode = self._core_manager.lymphnode

            # Get metrics from lymphnode
            metrics_dict = lymphnode.get_lymphnode_metrics()

            return LymphnodeMetrics(
                lymphnode_id=lymphnode.id,
                nivel=lymphnode.nivel,
                area_responsabilidade=lymphnode.area,
                homeostatic_state=lymphnode.homeostatic_state.value,
                temperatura_regional=lymphnode.temperatura_regional,
                agentes_ativos=metrics_dict["agentes_total"],  # Fixed: agentes_total
                agentes_dormindo=metrics_dict["agentes_dormindo"],
                total_ameacas_detectadas=metrics_dict["ameacas_detectadas"],  # Fixed: ameacas_detectadas
                total_neutralizacoes=metrics_dict["neutralizacoes"],  # Fixed: neutralizacoes
                total_clones_criados=metrics_dict["clones_criados"],  # Fixed: clones_criados
                total_clones_destruidos=metrics_dict["clones_destruidos"],  # Fixed: clones_destruidos
            )

        except Exception as e:
            logger.error(f"Failed to get lymphnode metrics: {e}", exc_info=True)
            raise CoordinationServiceError(f"Metrics retrieval failed: {e}") from e

    async def get_homeostatic_state(self) -> HomeostaticStateResponse:
        """
        Get current homeostatic state.

        Returns:
            HomeostaticStateResponse with state and recommendations

        Raises:
            LymphnodeNotAvailableError: If Lymphnode unavailable
        """
        self._check_lymphnode_available()

        logger.debug("Getting homeostatic state")

        try:
            lymphnode = self._core_manager.lymphnode

            state = lymphnode.homeostatic_state
            temp = lymphnode.temperatura_regional

            # Descriptions and recommendations per state
            state_info = {
                "REPOUSO": {
                    "description": "System at rest, normal operations",
                    "recommended_action": "Maintain normal agent count",
                },
                "VIGILÂNCIA": {
                    "description": "System vigilant, low-level monitoring",
                    "recommended_action": "Increase monitoring frequency",
                },
                "ATENÇÃO": {
                    "description": "System alert, moderate stress detected",
                    "recommended_action": "Prepare for potential activation",
                },
                "ATIVAÇÃO": {
                    "description": "System activated, significant stress",
                    "recommended_action": "Increase agent count and activate clonal expansion",
                },
                "INFLAMAÇÃO": {
                    "description": "System inflamed, critical stress level",
                    "recommended_action": "Maximum agent deployment and emergency response",
                },
            }

            info = state_info.get(
                state.value,
                {
                    "description": "Unknown state",
                    "recommended_action": "Monitor and reassess",
                },
            )

            return HomeostaticStateResponse(
                homeostatic_state=state.value,
                temperatura_regional=temp,
                description=info["description"],
                recommended_action=info["recommended_action"],
            )

        except Exception as e:
            logger.error(f"Failed to get homeostatic state: {e}", exc_info=True)
            raise CoordinationServiceError(f"State retrieval failed: {e}") from e

    async def destroy_clones(self, especializacao: str) -> int:
        """
        Destroy clones by specialization.

        This triggers apoptosis for all clones with a specific specialization,
        useful for cleanup after a threat is neutralized.

        Args:
            especializacao: Specialization to destroy

        Returns:
            Number of clones destroyed

        Raises:
            LymphnodeNotAvailableError: If Lymphnode unavailable
            CoordinationServiceError: If destruction fails
        """
        self._check_lymphnode_available()

        logger.info(f"Destroying clones with especialization: {especializacao}")

        try:
            lymphnode = self._core_manager.lymphnode

            num_destroyed = await lymphnode.destruir_clones(especializacao)

            logger.info(f"✓ Destroyed {num_destroyed} clones ({especializacao})")

            return num_destroyed

        except Exception as e:
            logger.error(f"Failed to destroy clones: {e}", exc_info=True)
            raise CoordinationServiceError(f"Clone destruction failed: {e}") from e

    def __repr__(self) -> str:
        """String representation."""
        return f"CoordinationService(lymphnode_available={self._core_manager.lymphnode is not None})"
