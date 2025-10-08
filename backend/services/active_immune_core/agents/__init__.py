"""Immune Agents Module

Autonomous agents that patrol the network and neutralize threats.
"""

from .agent_factory import AgentFactory
from .b_cell import LinfocitoBDigital
from .base import AgenteImunologicoBase
from .dendritic_cell import CelulaDendritica
from .distributed_coordinator import DistributedCoordinator
from .helper_t_cell import LinfocitoTAuxiliar
from .macrofago import MacrofagoDigital
from .models import AgenteState, AgentStatus, AgentType
from .neutrofilo import NeutrofiloDigital
from .nk_cell import CelulaNKDigital
from .regulatory_t_cell import LinfocitoTRegulador
from .swarm_coordinator import SwarmCoordinator

__all__ = [
    "AgentFactory",
    "AgenteImunologicoBase",
    "AgentStatus",
    "AgentType",
    "AgenteState",
    "MacrofagoDigital",
    "CelulaNKDigital",
    "NeutrofiloDigital",
    "LinfocitoBDigital",
    "LinfocitoTAuxiliar",
    "CelulaDendritica",
    "LinfocitoTRegulador",
    "SwarmCoordinator",
    "DistributedCoordinator",
]
