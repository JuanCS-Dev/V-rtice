"""
Consciousness-Immune Integration Clients

HTTP clients for integrating consciousness components (MMEI/MCEA/ESGT)
with Active Immune Core.
"""

from .mmei_client import MMEIClient
from .mcea_client import MCEAClient
from .esgt_subscriber import ESGTSubscriber

__all__ = [
    "MMEIClient",
    "MCEAClient",
    "ESGTSubscriber",
]
