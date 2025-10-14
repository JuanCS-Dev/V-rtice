"""
MIP Configuration Management

Gerencia configurações do Motor de Integridade Processual.
Suporta variáveis de ambiente e valores padrão.

Autor: Juan Carlos de Souza
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configurações do MIP Service.
    
    Lê de variáveis de ambiente ou usa defaults.
    """
    
    # Service
    service_name: str = "mip"
    service_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8100
    log_level: str = "INFO"
    
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j123"
    neo4j_database: str = "neo4j"
    neo4j_max_pool_size: int = 50
    
    # API
    api_title: str = "MIP - Motor de Integridade Processual"
    api_description: str = "Sistema de supervisão ética para MAXIMUS"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    
    # Performance
    request_timeout: float = 30.0
    evaluation_timeout: float = 10.0
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 8101
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna singleton de Settings.
    
    Cached para performance.
    """
    return Settings()
