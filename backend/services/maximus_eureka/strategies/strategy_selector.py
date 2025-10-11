"""
Strategy Selector - Choose appropriate remediation strategy for APV.

Implements strategy selection logic based on APV characteristics and
confirmation results. Evaluates strategies in priority order.

Theoretical Foundation:
    Strategy selection is informed by:
    1. Determinism: Dependency upgrades are deterministic, preferred
    2. Safety: Automated > LLM > WAF > Manual
    3. Effectiveness: Fix > Mitigation > Review
    
    Selection algorithm:
    - Iterate strategies in priority order
    - Return first strategy where can_handle() returns True
    - Fallback to MANUAL_REVIEW if none applicable

Author: MAXIMUS Team
Date: 2025-01-10
"""

from typing import List, Optional
import logging

# Import APV from Oráculo
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "maximus_oraculo"))
from models.apv import APV

from eureka_models.confirmation.confirmation_result import ConfirmationResult
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class NoStrategyAvailableError(Exception):
    """Raised when no strategy can handle APV."""

    pass


class StrategySelector:
    """
    Selects remediation strategy based on APV characteristics.
    
    Selection Logic:
        1. Check each strategy's can_handle() in priority order
        2. Return first strategy that can handle
        3. Raise NoStrategyAvailableError if none applicable
    
    Priority Order (injected via constructor):
        Typically: DependencyUpgrade → CodePatchLLM → CoagulationWAF → ManualReview
    
    Usage:
        >>> strategies = [
        ...     DependencyUpgradeStrategy(),
        ...     CodePatchLLMStrategy(llm_client),
        ...     ManualReviewStrategy(),
        ... ]
        >>> selector = StrategySelector(strategies)
        >>> strategy = await selector.select_strategy(apv, confirmation)
        >>> patch = await strategy.apply_strategy(apv, confirmation)
    """
    
    def __init__(self, strategies: List[BaseStrategy]):
        """
        Initialize strategy selector.
        
        Args:
            strategies: List of strategies in priority order
        """
        self.strategies = strategies
        logger.info(
            f"StrategySelector initialized with {len(strategies)} strategies: "
            f"{[s.strategy_type.value for s in strategies]}"
        )
    
    async def select_strategy(
        self, apv: APV, confirmation: ConfirmationResult
    ) -> BaseStrategy:
        """
        Select best strategy for APV.
        
        Evaluates strategies sequentially in priority order.
        Returns first strategy where can_handle() returns True.
        
        Args:
            apv: APV to remediate
            confirmation: Vulnerability confirmation result
            
        Returns:
            Selected strategy ready to apply
            
        Raises:
            NoStrategyAvailableError: If no strategy can handle APV
        """
        logger.info(
            f"Selecting strategy for {apv.cve_id} "
            f"(priority={apv.priority}, complexity={apv.remediation_complexity})"
        )
        
        for strategy in self.strategies:
            try:
                if await strategy.can_handle(apv, confirmation):
                    logger.info(
                        f"✅ Selected {strategy.strategy_type.value} for {apv.cve_id}"
                    )
                    return strategy
            except Exception as e:
                logger.warning(
                    f"⚠️ Strategy {strategy.strategy_type.value} "
                    f"failed can_handle() check: {e}",
                    exc_info=True,
                )
                continue
        
        # No strategy available
        available_strategies = [s.strategy_type.value for s in self.strategies]
        error_msg = (
            f"No strategy available for {apv.cve_id}. "
            f"Tried: {available_strategies}"
        )
        logger.error(error_msg)
        raise NoStrategyAvailableError(error_msg)
    
    def get_strategies(self) -> List[BaseStrategy]:
        """
        Get list of registered strategies.
        
        Returns:
            List of strategies in priority order
        """
        return self.strategies.copy()
