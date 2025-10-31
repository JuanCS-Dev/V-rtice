"""PENELOPE Core Modules.

Core components implementing the 7 Biblical Articles of Governance.

Author: Vértice Platform Team
License: Proprietary
"""

from .praotes_validator import PraotesValidator
from .sophia_engine import SophiaEngine
from .tapeinophrosyne_monitor import TapeinophrosyneMonitor

__all__ = [
    "SophiaEngine",
    "PraotesValidator",
    "TapeinophrosyneMonitor",
]
