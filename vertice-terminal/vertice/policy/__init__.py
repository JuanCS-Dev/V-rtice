"""
📜 Policy-as-Code Engine
Automação de resposta baseada em políticas YAML

Componentes:
- PolicyEngine: Avalia e executa policies
- PolicyParser: Parse de YAML policies
- ActionExecutor: Executa ações automatizadas
"""

from .engine import PolicyEngine, PolicyStatus, PolicyExecution
from .parser import PolicyParser, Policy, Trigger, Condition, Action
from .executor import ActionExecutor, ActionResult, ActionStatus

__all__ = [
    "PolicyEngine",
    "PolicyStatus",
    "PolicyExecution",
    "PolicyParser",
    "Policy",
    "Trigger",
    "Condition",
    "Action",
    "ActionExecutor",
    "ActionResult",
    "ActionStatus",
]
