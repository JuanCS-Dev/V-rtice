"""Justice module - Ethical reasoning and precedent management for Maximus AI."""

from justice.precedent_database import PrecedentDB, CasePrecedent
from justice.embeddings import CaseEmbedder
from justice.constitutional_validator import (
    ConstitutionalValidator,
    ViolationLevel,
    ViolationType,
    ViolationReport,
    ConstitutionalViolation,
)
from justice.emergency_circuit_breaker import EmergencyCircuitBreaker

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
