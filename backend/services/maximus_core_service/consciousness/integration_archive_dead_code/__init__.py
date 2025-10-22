"""
Consciousness-Immune Integration Clients

HTTP clients for integrating consciousness components (MMEI/MCEA/ESGT)
with Active Immune Core.
"""

from .esgt_subscriber import ESGTSubscriber
from .mea_bridge import MEABridge, MEAContextSnapshot
from .mcea_client import MCEAClient
from .mmei_client import MMEIClient

__all__ = [
    "MMEIClient",
    "MCEAClient",
    "ESGTSubscriber",
    "MEABridge",
    "MEAContextSnapshot",
]
