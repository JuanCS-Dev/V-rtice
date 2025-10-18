"""
Base Framework - Interface comum para todos os frameworks éticos
"""

from abc import ABC, abstractmethod
from .models import ActionPlan, FrameworkScore


class EthicalFramework(ABC):
    """
    Interface base para todos os frameworks éticos do MIP.
    
    Cada framework implementa uma teoria ética específica e avalia
    ActionPlans de acordo com seus princípios.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do framework."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Versão da implementação."""
        pass
    
    @abstractmethod
    def evaluate(self, plan: ActionPlan) -> FrameworkScore:
        """
        Avalia um plano de ação segundo este framework ético.
        
        Args:
            plan: ActionPlan a ser avaliado
            
        Returns:
            FrameworkScore com resultado da avaliação
        """
        pass
    
    @abstractmethod
    def can_veto(self) -> bool:
        """
        Indica se este framework tem poder de veto absoluto.
        
        Returns:
            True se pode vetar incondicionalmente
        """
        pass
    
    def validate_plan(self, plan: ActionPlan) -> None:
        """
        Valida estrutura básica do plano antes de avaliar.
        
        Raises:
            ValueError: se plano inválido
        """
        if not plan.steps:
            raise ValueError("ActionPlan deve ter pelo menos um step")
        if not plan.description:
            raise ValueError("ActionPlan deve ter descrição")
