"""
Frameworks Éticos - Consolidação
Exporta todos os frameworks implementados
"""

from .kantian import KantianDeontology
from .utilitarian import UtilitarianCalculus
from .virtue_ethics import VirtueEthics
from .principialism import Principialism

__all__ = [
    "KantianDeontology",
    "UtilitarianCalculus",
    "VirtueEthics",
    "Principialism"
]
