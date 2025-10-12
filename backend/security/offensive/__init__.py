"""
MAXIMUS Offensive Security Framework
=====================================

World-class AI-driven offensive security tools for autonomous penetration testing.
Implements reconnaissance, exploitation, post-exploitation, and intelligence gathering.

Architecture:
    - reconnaissance/: Target discovery and enumeration
    - exploitation/: Vulnerability exploitation engines
    - post_exploitation/: Payload delivery and persistence
    - intelligence/: OSINT and threat intelligence

Philosophy:
    "Attack is the best teacher of defense."
    Every offensive capability strengthens defensive posture.
"""

__version__ = "1.0.0"
__author__ = "MAXIMUS Team"

from typing import List

__all__: List[str] = [
    "reconnaissance",
    "exploitation", 
    "post_exploitation",
    "intelligence"
]
