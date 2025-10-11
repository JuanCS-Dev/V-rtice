"""
Remediation Strategies Module - MAXIMUS Eureka.

Provides strategy pattern implementation for automated vulnerability remediation.

Strategy Types:
    - DependencyUpgradeStrategy: Automated dependency version bumps
    - CodePatchLLMStrategy: LLM-guided code patching
    - CoagulationWAFStrategy: WAF rule generation (future)
    - ManualReviewStrategy: Human review fallback (future)

Author: MAXIMUS Team
Date: 2025-01-10
"""

from strategies.base_strategy import (
    BaseStrategy,
    StrategyError,
    StrategyFailedError,
    StrategyNotApplicableError,
)
from strategies.strategy_selector import StrategySelector, NoStrategyAvailableError
from strategies.dependency_upgrade import DependencyUpgradeStrategy
from strategies.code_patch_llm import CodePatchLLMStrategy

__all__ = [
    "BaseStrategy",
    "StrategyError",
    "StrategyFailedError",
    "StrategyNotApplicableError",
    "StrategySelector",
    "NoStrategyAvailableError",
    "DependencyUpgradeStrategy",
    "CodePatchLLMStrategy",
]
