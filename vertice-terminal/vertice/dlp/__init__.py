"""
🔒 Data Loss Prevention (DLP) System
Prevenção de perda de dados com classificação automática e políticas

Componentes:
- ContentInspector: Inspeção profunda de conteúdo
- DataClassifier: Classificação automática de dados sensíveis
- PolicyEngine: Engine de políticas DLP
- AlertSystem: Sistema de alertas e resposta
"""

from .content_inspector import (
    ContentInspector,
    InspectionResult,
    SensitiveDataType,
)
from .data_classifier import (
    DataClassifier,
    DataClassification,
    ClassificationLevel,
)
from .policy_engine import (
    PolicyEngine,
    DLPPolicy,
    PolicyAction,
    PolicyCondition,
)
from .alert_system import (
    AlertSystem,
    DLPAlert,
    AlertSeverity,
)

__all__ = [
    "ContentInspector",
    "InspectionResult",
    "SensitiveDataType",
    "DataClassifier",
    "DataClassification",
    "ClassificationLevel",
    "PolicyEngine",
    "DLPPolicy",
    "PolicyAction",
    "PolicyCondition",
    "AlertSystem",
    "DLPAlert",
    "AlertSeverity",
]
