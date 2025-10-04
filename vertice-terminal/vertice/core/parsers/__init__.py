"""
Tool Output Parsers
====================

Parsers convert tool-specific output formats into unified data structures.

Available Parsers:
- NmapParser: XML → structured host/port data
- NucleiParser: JSON → vulnerability data (TODO)
- NiktoParser: Text → web vulnerability data (TODO)
"""

from .nmap_parser import NmapParser

__all__ = ["NmapParser"]
