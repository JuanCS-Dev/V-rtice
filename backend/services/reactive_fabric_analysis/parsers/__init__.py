"""
Forensic Capture Parsers
Extract structured data from honeypot logs and network captures.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real implementation
"""

from .base import ForensicParser
from .cowrie_parser import CowrieJSONParser

__all__ = [
    "ForensicParser",
    "CowrieJSONParser",
]
