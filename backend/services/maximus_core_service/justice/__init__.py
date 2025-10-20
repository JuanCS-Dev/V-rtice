"""Justice module - Ethical reasoning and precedent management for Maximus AI."""

from .precedent_database import PrecedentDB, CasePrecedent
from .embeddings import CaseEmbedder
from .constitutional_validator import (
    ConstitutionalValidator,
    ViolationLevel,
    ViolationType,
    ViolationReport,
    ConstitutionalViolation,
)
from .emergency_circuit_breaker import EmergencyCircuitBreaker

__all__ = [
    "PrecedentDB",
    "CasePrecedent",
    "CaseEmbedder",
    "ConstitutionalValidator",
    "ViolationLevel",
    "ViolationType",
    "ViolationReport",
    "ConstitutionalViolation",
    "EmergencyCircuitBreaker",
]
