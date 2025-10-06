"""Ethics module for VÉRTICE MAXIMUS.

This module implements a comprehensive multi-framework ethical decision-making system
for autonomous cybersecurity operations.

Frameworks:
- Kantian Deontology: Categorical imperative and humanity formula (veto power)
- Consequentialism: Utilitarian hedonic calculus
- Virtue Ethics: Aristotelian golden mean and character virtues
- Principialism: Beneficence, non-maleficence, autonomy, justice

Usage:
    from ethics import EthicalIntegrationEngine, ActionContext

    engine = EthicalIntegrationEngine(config)
    action_context = ActionContext(
        action_type="offensive_action",
        action_description="Block malicious IP 192.168.1.100",
        system_component="immunis_neutrophil",
        threat_data={...}
    )

    decision = await engine.evaluate(action_context)
    print(f"Decision: {decision.final_decision}")
    print(f"Explanation: {decision.explanation}")
"""

from .base import (
    ActionContext,
    EthicalCache,
    EthicalException,
    EthicalFramework,
    EthicalFrameworkResult,
    EthicalVerdict,
    VetoException,
)
from .consequentialist_engine import ConsequentialistEngine
from .integration_engine import EthicalIntegrationEngine, IntegratedEthicalDecision
from .kantian_checker import KantianImperativeChecker
from .principialism import PrinciplismFramework
from .virtue_ethics import VirtueEthicsAssessment

__all__ = [
    # Base classes
    "EthicalFramework",
    "EthicalFrameworkResult",
    "EthicalVerdict",
    "ActionContext",
    "EthicalCache",
    "EthicalException",
    "VetoException",
    # Frameworks
    "KantianImperativeChecker",
    "ConsequentialistEngine",
    "VirtueEthicsAssessment",
    "PrinciplismFramework",
    # Integration
    "EthicalIntegrationEngine",
    "IntegratedEthicalDecision",
]

__version__ = "1.0.0"
