"""
Motor de Integridade Processual (MIP) - MAXIMUS Core Component
Version: 1.0.0
Constituição Vértice v2.6 Compliant

Este módulo implementa o sistema de validação ética que governa todas as ações
do MAXIMUS, garantindo conformidade com os princípios fundamentais de integridade processual.
"""

from .core import ProcessIntegrityEngine
from .models import (
    ActionPlan,
    ActionStep,
    EthicalVerdict,
    VerdictStatus,
    Stakeholder,
    StakeholderType,
    ActionCategory,
    Effect,
    Precondition,
    FrameworkScore,
    AuditTrailEntry
)
from .frameworks import (
    KantianDeontology,
    UtilitarianCalculus,
    VirtueEthics,
    Principialism
)
from .resolver import ConflictResolver

__version__ = "1.0.0"
__all__ = [
    "ProcessIntegrityEngine",
    "ActionPlan",
    "ActionStep", 
    "EthicalVerdict",
    "VerdictStatus",
    "Stakeholder",
    "StakeholderType",
    "ActionCategory",
    "Effect",
    "Precondition",
    "FrameworkScore",
    "AuditTrailEntry",
    "KantianDeontology",
    "UtilitarianCalculus",
    "VirtueEthics",
    "Principialism",
    "ConflictResolver"
]
