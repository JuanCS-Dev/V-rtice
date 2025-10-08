"""FASE 9: Memory Consolidation Service

Long-term immunological memory and circadian rhythm consolidation.
Bio-inspired memory transfer from short-term to long-term storage.

NO MOCKS - Production-ready memory consolidation.
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Team"

from .consolidation_core import (
    ConsolidationCycle,
    ConsolidationStatus,
    ImportanceScorer,
    LongTermMemory,
    MemoryConsolidator,
    MemoryImportance,
    PatternExtractor,
    SecurityEvent,
    ShortTermMemory,
)

__all__ = [
    "MemoryImportance",
    "ConsolidationStatus",
    "SecurityEvent",
    "ShortTermMemory",
    "LongTermMemory",
    "ConsolidationCycle",
    "ImportanceScorer",
    "PatternExtractor",
    "MemoryConsolidator",
]
