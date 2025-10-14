"""
Justice Module - Deontic Logic and Constitutional Rules

Implements deontic logic (obligation, permission, prohibition) with
Lei Zero (Transparency) and Lei I (Não Causar Danos) from Constituição Vértice.
"""

from .deontic_reasoner import (
    DeonticReasoner,
    DeonticRule,
    DeonticOperator,
    ComplianceResult,
)

__all__ = [
    "DeonticReasoner",
    "DeonticRule",
    "DeonticOperator",
    "ComplianceResult",
]
