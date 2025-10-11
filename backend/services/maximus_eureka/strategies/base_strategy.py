"""
Base Strategy - Abstract class for remediation strategies.

All remediation strategies inherit from BaseStrategy and implement:
- can_handle(): Strategy selection logic based on APV characteristics
- apply_strategy(): Patch generation logic specific to strategy type
- estimate_complexity(): Complexity assessment for MTTR estimation

Theoretical Foundation:
    Strategy Pattern enables polymorphic remediation approaches. Each strategy
    encapsulates specific remediation technique (dependency upgrade, LLM patch,
    WAF rule, etc.) with common interface for orchestrator.
    
    Strategy Selection Order (evaluated sequentially):
    1. DEPENDENCY_UPGRADE (if fix_available=True) - Deterministic, safest
    2. CODE_PATCH (if ast_grep_pattern exists) - LLM-guided, requires validation
    3. COAGULATION_WAF (zero-day without pattern) - Temporary mitigation
    4. MANUAL_REVIEW (high complexity fallback) - Human intervention required
    
    This order prioritizes determinism and safety: automated fixes first,
    LLM-assisted next, temporary mitigations, then human review.

Performance Targets:
    - Dependency upgrade: < 30s
    - LLM code patch: < 2min
    - WAF rule generation: < 10s
    
Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - The Architect of all strategies
"""

from abc import ABC, abstractmethod
from typing import Optional

# Import APV and related enums from Oráculo
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "maximus_oraculo"))
from models.apv import APV, RemediationStrategy, RemediationComplexity

# Import Eureka models
from eureka_models.confirmation.confirmation_result import ConfirmationResult
from eureka_models.patch import Patch


class StrategyError(Exception):
    """Base exception for strategy errors."""

    pass


class StrategyFailedError(StrategyError):
    """Raised when strategy fails to generate valid patch."""

    pass


class StrategyNotApplicableError(StrategyError):
    """Raised when strategy cannot handle given APV."""

    pass


class BaseStrategy(ABC):
    """
    Abstract base for all remediation strategies.
    
    Implements Template Method pattern where subclasses override specific steps
    while base class orchestrates overall flow and provides common utilities.
    
    Subclass Responsibilities:
        - Implement strategy_type property
        - Implement can_handle() logic
        - Implement apply_strategy() patch generation
        - Optionally override estimate_complexity()
    
    Usage:
        >>> strategy = DependencyUpgradeStrategy()
        >>> if await strategy.can_handle(apv, confirmation):
        ...     patch = await strategy.apply_strategy(apv, confirmation)
        ...     print(f"Generated patch: {patch.patch_id}")
    """
    
    @property
    @abstractmethod
    def strategy_type(self) -> RemediationStrategy:
        """
        Return strategy type enum.
        
        Returns:
            RemediationStrategy enum value
        """
        pass
    
    @abstractmethod
    async def can_handle(
        self, apv: APV, confirmation: ConfirmationResult
    ) -> bool:
        """
        Determine if strategy can handle this APV.
        
        Strategy selection logic based on APV characteristics:
        - Dependency upgrade: requires fix_available=True
        - Code patch: requires ast_grep_pattern
        - WAF: zero-day without pattern
        - Manual review: high complexity fallback
        
        Args:
            apv: APV to evaluate
            confirmation: Vulnerability confirmation result
            
        Returns:
            True if strategy is applicable to this APV
        """
        pass
    
    @abstractmethod
    async def apply_strategy(
        self, apv: APV, confirmation: ConfirmationResult
    ) -> Patch:
        """
        Apply remediation strategy and generate patch.
        
        Core strategy logic. Generates Patch object with:
        - Unified diff (git format)
        - Confidence score
        - Validation status
        
        Args:
            apv: APV with vulnerability details
            confirmation: Confirmed vulnerable locations
            
        Returns:
            Patch object with diff and metadata
            
        Raises:
            StrategyFailedError: If strategy cannot generate valid patch
            StrategyNotApplicableError: If strategy not applicable
        """
        pass
    
    def estimate_complexity(self, apv: APV) -> RemediationComplexity:
        """
        Estimate remediation complexity.
        
        Default implementation uses APV.remediation_complexity which is
        calculated during Oráculo processing based on:
        - Number of affected packages
        - Availability of fixes
        - ast-grep pattern complexity
        
        Subclasses can override for strategy-specific logic.
        
        Args:
            apv: APV to assess
            
        Returns:
            RemediationComplexity enum
        """
        return apv.remediation_complexity
    
    def _generate_patch_id(self, cve_id: str) -> str:
        """
        Generate unique patch identifier.
        
        Format: patch-{cve_id}-{timestamp}
        Example: patch-CVE-2024-99999-20250110-143022
        
        Args:
            cve_id: CVE identifier
            
        Returns:
            Unique patch ID
        """
        from datetime import datetime
        
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        return f"patch-{cve_id}-{timestamp}"
    
    def _generate_branch_name(self, cve_id: str) -> str:
        """
        Generate Git branch name for patch.
        
        Format: security/fix-{cve_id}-{timestamp}
        Example: security/fix-CVE-2024-99999-20250110
        
        Args:
            cve_id: CVE identifier
            
        Returns:
            Branch name
        """
        from datetime import datetime
        
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        return f"security/fix-{cve_id}-{timestamp}"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__} strategy={self.strategy_type.value}>"
