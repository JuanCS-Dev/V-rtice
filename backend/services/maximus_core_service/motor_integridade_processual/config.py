"""
Configuração do Motor de Integridade Processual.

Este módulo define todas as configurações necessárias para operação do MIP,
incluindo thresholds éticos, pesos de frameworks, e configurações de infraestrutura.

Lei Governante: Constituição Vértice v2.6
"""

from typing import Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class MIPSettings(BaseSettings):
    """
    Configurações do Motor de Integridade Processual.
    
    Attributes:
        neo4j_uri: URI de conexão com Neo4j para Knowledge Base
        neo4j_user: Usuário Neo4j
        neo4j_password: Senha Neo4j
        kantian_weight: Peso do framework Kantiano (0.0-1.0)
        utilitarian_weight: Peso do framework Utilitarista (0.0-1.0)
        virtue_weight: Peso da Ética das Virtudes (0.0-1.0)
        principialism_weight: Peso do Principialismo (0.0-1.0)
        approval_threshold: Score mínimo para aprovação (0.0-1.0)
        escalation_threshold: Score máximo para escalar para HITL (0.0-1.0)
        enable_hitl: Se deve escalar casos ambíguos para humano
        audit_retention_days: Dias para manter audit trail
    """
    
    # Infrastructure
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="maximus2025", env="NEO4J_PASSWORD")
    
    # Framework Weights (devem somar 1.0)
    kantian_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    utilitarian_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    virtue_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    principialism_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    
    # Decision Thresholds
    approval_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Score mínimo para aprovação automática"
    )
    escalation_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Score abaixo disso escala para HITL"
    )
    
    # HITL Configuration
    enable_hitl: bool = Field(default=True, description="Habilita escalação HITL")
    hitl_timeout_seconds: int = Field(default=3600, description="Timeout para resposta humana")
    
    # Audit Trail
    audit_retention_days: int = Field(default=365, description="Dias para reter audit trail")
    
    # Metrics
    prometheus_enabled: bool = Field(default=True, description="Habilita métricas Prometheus")
    prometheus_port: int = Field(default=9090, description="Porta Prometheus")
    
    # API
    api_host: str = Field(default="0.0.0.0", description="Host da API")
    api_port: int = Field(default=8000, description="Porta da API")
    api_reload: bool = Field(default=False, description="Hot reload (dev only)")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def validate_weights(self) -> None:
        """
        Valida que os pesos dos frameworks somam 1.0.
        
        Raises:
            ValueError: Se a soma dos pesos não for 1.0 (com tolerância de 0.01)
        """
        total = (
            self.kantian_weight
            + self.utilitarian_weight
            + self.virtue_weight
            + self.principialism_weight
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Framework weights must sum to 1.0, got {total}. "
                f"Adjust: Kant={self.kantian_weight}, Mill={self.utilitarian_weight}, "
                f"Virtue={self.virtue_weight}, Principialism={self.principialism_weight}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário."""
        return self.model_dump()


# Singleton instance
settings = MIPSettings()
settings.validate_weights()
