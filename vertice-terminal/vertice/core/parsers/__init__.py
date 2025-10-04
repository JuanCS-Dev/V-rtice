"""
Tool Output Parsers
====================

Parsers convert tool-specific output formats into unified data structures.

Available Parsers:
- NmapParser: XML → structured host/port data
- NucleiParser: JSONL → vulnerability data
- NiktoParser: Text → web vulnerability data (TODO)
"""

from .nmap_parser import NmapParser
from .nuclei_parser import NucleiParser

__all__ = ["NmapParser", "NucleiParser"]
