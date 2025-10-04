"""
🚨 Incident Response & Orchestration
Gerenciamento completo de incidentes de segurança

Componentes:
- IncidentManager: Gerenciamento de incidentes
- PlaybookEngine: Automação de resposta via playbooks
- CaseManager: Investigações e case management
- TimelineBuilder: Reconstrução de timeline de ataques
- EvidenceCollector: Coleta e preservação de evidências
"""

from .incident_manager import (
    IncidentManager,
    Incident,
    IncidentStatus,
    IncidentSeverity,
    IncidentCategory,
)
from .playbook_engine import PlaybookEngine, Playbook, PlaybookStep, StepStatus
from .case_manager import CaseManager, Case, CaseStatus, Finding
from .timeline import TimelineBuilder, TimelineEvent, EventType
from .evidence import EvidenceCollector, Evidence, EvidenceType, ChainOfCustody

__all__ = [
    "IncidentManager",
    "Incident",
    "IncidentStatus",
    "IncidentSeverity",
    "IncidentCategory",
    "PlaybookEngine",
    "Playbook",
    "PlaybookStep",
    "StepStatus",
    "CaseManager",
    "Case",
    "CaseStatus",
    "Finding",
    "TimelineBuilder",
    "TimelineEvent",
    "EventType",
    "EvidenceCollector",
    "Evidence",
    "EvidenceType",
    "ChainOfCustody",
]
