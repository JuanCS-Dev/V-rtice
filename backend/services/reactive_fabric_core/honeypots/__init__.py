"""
Honeypot Infrastructure for Reactive Fabric
High-interaction honeypots to capture attacker behavior
"""

from .base_honeypot import BaseHoneypot, HoneypotType, AttackCapture
from .cowrie_ssh import CowrieSSHHoneypot
from .dvwa_web import DVWAWebHoneypot
from .postgres_honeypot import PostgreSQLHoneypot
from .honeypot_manager import HoneypotManager

__all__ = [
    'BaseHoneypot',
    'HoneypotType',
    'AttackCapture',
    'CowrieSSHHoneypot',
    'DVWAWebHoneypot',
    'PostgreSQLHoneypot',
    'HoneypotManager'
]