"""
🔍 Detection Engine
Real-time threat detection com YARA e Sigma rules

Componentes:
- DetectionEngine: Engine principal de detecção
- YARAScanner: Scanner de arquivos com regras YARA
- SigmaParser: Parser de regras Sigma para logs
- AlertManager: Gerenciamento e correlação de alertas
"""

from .engine import DetectionEngine, Detection, DetectionSeverity
from .yara_scanner import YARAScanner, YARAMatch
from .sigma_parser import SigmaParser, SigmaRule
from .alert_manager import AlertManager, Alert, AlertStatus

__all__ = [
    "DetectionEngine",
    "Detection",
    "DetectionSeverity",
    "YARAScanner",
    "YARAMatch",
    "SigmaParser",
    "SigmaRule",
    "AlertManager",
    "Alert",
    "AlertStatus",
]
