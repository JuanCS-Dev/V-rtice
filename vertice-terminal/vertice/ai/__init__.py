"""
🤖 VÉRTICE AI ENGINE
Motor de IA conversacional para threat hunting

Componentes:
- AIInterpreter: Traduz linguagem natural para VeQL
- ConversationEngine: Investigações multi-turn
- ToolCaller: Executa comandos Vértice via AI
- SafetyGuard: Valida e protege comandos perigosos
- AutopilotEngine: Execução autônoma de workflows multi-fase
- ExecutionPlanner: Geração de planos de execução
- MaximusAssistant: NL queries, CVE correlation, suggestions, reports
"""

from .interpreter import AIInterpreter
from .conversation import ConversationEngine, Investigation
from .tools import ToolCaller, ToolRegistry
from .safety import SafetyGuard
from .autopilot import AutopilotEngine
from .planner import ExecutionPlanner
from .assistant import (
    MaximusAssistant,
    NaturalLanguageQueryParser,
    CVECorrelator,
    SuggestionEngine,
    ReportGenerator
)
from .models import (
    ExecutionPlan,
    ExecutionPhase,
    ExecutionStep,
    ObjectiveType,
    RiskLevel,
    PhaseStatus,
    StepStatus,
    PlanResult
)

__all__ = [
    "AIInterpreter",
    "ConversationEngine",
    "Investigation",
    "ToolCaller",
    "ToolRegistry",
    "SafetyGuard",
    "AutopilotEngine",
    "ExecutionPlanner",
    "MaximusAssistant",
    "NaturalLanguageQueryParser",
    "CVECorrelator",
    "SuggestionEngine",
    "ReportGenerator",
    "ExecutionPlan",
    "ExecutionPhase",
    "ExecutionStep",
    "ObjectiveType",
    "RiskLevel",
    "PhaseStatus",
    "StepStatus",
    "PlanResult",
]
