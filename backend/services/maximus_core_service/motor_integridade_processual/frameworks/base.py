"""
Base interfaces and protocols for ethical frameworks.

Defines the contract that all ethical frameworks must implement
to evaluate ActionPlans within the Motor de Integridade Processual (MIP).

Lei Governante: Constituição Vértice v2.6
"""

from abc import ABC, abstractmethod
from typing import Protocol
from motor_integridade_processual.models.action_plan import ActionPlan
from motor_integridade_processual.models.verdict import FrameworkVerdict


class EthicalFramework(Protocol):
    """
    Protocol defining the interface for ethical evaluation frameworks.
    
    All frameworks (Kantian, Utilitarian, Virtue, Principialism) must implement
    this protocol to be compatible with the MIP resolution engine.
    
    Attributes:
        name: Framework identifier (e.g., "Kantian", "Utilitarian")
        weight: Default weight for aggregation (0.0-1.0)
        can_veto: Whether this framework has absolute veto power
    """
    
    name: str
    weight: float
    can_veto: bool
    
    def evaluate(self, plan: ActionPlan) -> FrameworkVerdict:
        """
        Evaluate an ActionPlan according to this framework's ethical principles.
        
        Args:
            plan: The action plan to evaluate
            
        Returns:
            FrameworkVerdict with decision, reasons, score, and confidence
            
        Raises:
            ValueError: If plan is invalid or cannot be evaluated
        """
        ...
    
    def get_veto_threshold(self) -> float:
        """
        Get the severity threshold for vetoing a plan.
        
        Returns:
            Severity level (0.0-1.0) at which this framework will veto
        """
        ...


class AbstractEthicalFramework(ABC):
    """
    Abstract base class for ethical frameworks.
    
    Provides common functionality and enforces the protocol contract.
    Concrete frameworks should inherit from this class.
    """
    
    def __init__(self, name: str, weight: float = 0.25, can_veto: bool = False):
        """
        Initialize ethical framework.
        
        Args:
            name: Framework identifier
            weight: Default weight for conflict resolution (must sum to 1.0 across all frameworks)
            can_veto: Whether this framework can veto decisions
            
        Raises:
            ValueError: If weight not in [0.0, 1.0]
        """
        if not 0.0 <= weight <= 1.0:
            raise ValueError(f"Weight must be in [0.0, 1.0], got {weight}")
        
        self.name = name
        self.weight = weight
        self.can_veto = can_veto
        self._veto_threshold = 1.0  # Default: only veto on max severity
    
    @abstractmethod
    def evaluate(self, plan: ActionPlan) -> FrameworkVerdict:
        """
        Evaluate action plan. Must be implemented by concrete frameworks.
        
        Args:
            plan: Action plan to evaluate
            
        Returns:
            Framework verdict with decision and reasoning
        """
        pass
    
    def get_veto_threshold(self) -> float:
        """Get veto threshold for this framework."""
        return self._veto_threshold
    
    def set_veto_threshold(self, threshold: float) -> None:
        """
        Set veto threshold.
        
        Args:
            threshold: Severity level (0.0-1.0) for veto
            
        Raises:
            ValueError: If threshold not in [0.0, 1.0]
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be in [0.0, 1.0], got {threshold}")
        self._veto_threshold = threshold
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}', weight={self.weight}, can_veto={self.can_veto})"
