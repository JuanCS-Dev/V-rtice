"""
Forensic Capture Parsers
Extract structured data from honeypot logs and network captures.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real implementation
"""

from backend.services.reactive_fabric_analysis.parsers.base import ForensicParser
from backend.services.reactive_fabric_analysis.parsers.cowrie_parser import CowrieJSONParser

__all__ = [
    "ForensicParser",
    "CowrieJSONParser",
]
