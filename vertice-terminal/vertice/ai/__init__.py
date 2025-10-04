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

Advanced AI Features (Phase 2.2):
- CoTReasoner: Chain-of-Thought reasoning with backtracking
- SelfReflector: Self-reflection and continuous improvement
- MultiAgentOrchestrator: Multi-agent collaboration and orchestration
- ToolLearner: Tool performance tracking and adaptive selection
- ExplainableAI: Decision explainability and transparency
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

# Advanced AI Features
from .reasoning import CoTReasoner, ReasoningStrategy, ReasoningResult, ReasoningStep, StepType
from .self_reflection import (
    SelfReflector,
    ActionRecord,
    Reflection,
    LearningInsight,
    OutcomeType,
    ReflectionType
)
from .multi_agent import (
    MultiAgentOrchestrator,
    Agent,
    Task,
    CollaborationResult,
    AgentRole,
    TaskPriority,
    TaskStatus
)
from .tool_learning import (
    ToolLearner,
    ToolUsage,
    ToolRecommendation,
    ToolPerformanceProfile,
    ToolCategory
)
from .explainability import (
    ExplainableAI,
    DecisionExplanation,
    ConfidenceFactor,
    ExplanationType,
    DecisionType
)

__all__ = [
    # Core AI
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
    # Advanced AI Features
    "CoTReasoner",
    "ReasoningStrategy",
    "ReasoningResult",
    "ReasoningStep",
    "StepType",
    "SelfReflector",
    "ActionRecord",
    "Reflection",
    "LearningInsight",
    "OutcomeType",
    "ReflectionType",
    "MultiAgentOrchestrator",
    "Agent",
    "Task",
    "CollaborationResult",
    "AgentRole",
    "TaskPriority",
    "TaskStatus",
    "ToolLearner",
    "ToolUsage",
    "ToolRecommendation",
    "ToolPerformanceProfile",
    "ToolCategory",
    "ExplainableAI",
    "DecisionExplanation",
    "ConfidenceFactor",
    "ExplanationType",
    "DecisionType",
]
