"""Maximus Web Attack Service - Configuration Module.

This module handles the configuration settings for the Web Attack Service.
It provides a centralized place to define and manage parameters such as API keys
for integrated web scanning tools (e.g., Burp Suite, OWASP ZAP), AI configuration,
ASA integration details, logging levels, and other operational settings.

By externalizing configuration, this module allows for flexible deployment and
management of the Web Attack Service without requiring code changes.
It supports loading configurations from environment variables, files, or other
sources, ensuring adaptability across different environments.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Service configuration"""

    # Service
    SERVICE_NAME: str = "web_application_attack"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8034
    LOG_LEVEL: str = "INFO"

    # AI Configuration (Hybrid Gemini/Anthropic)
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "auto"  # auto, gemini, anthropic
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 2000

    # Burp Suite
    BURP_API_URL: Optional[str] = "http://localhost:1337"
    BURP_API_KEY: Optional[str] = None

    # OWASP ZAP
    ZAP_API_URL: Optional[str] = "http://localhost:8080"
    ZAP_API_KEY: Optional[str] = None

    # ASA Integration
    ENABLE_ASA_INTEGRATION: bool = True
    PREFRONTAL_CORTEX_URL: Optional[str] = "http://prefrontal_cortex_service:8011"
    AUDITORY_CORTEX_URL: Optional[str] = "http://auditory_cortex_service:8007"
    SOMATOSENSORY_URL: Optional[str] = "http://somatosensory_service:8008"

    # Metrics
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9034

    class Config:
        """Configuração para carregar variáveis de ambiente de um arquivo .env."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retorna uma instância singleton das configurações do serviço.

    As configurações são carregadas uma única vez e armazenadas em cache.

    Returns:
        Settings: A instância de configurações do serviço.
    """
    return Settings()
