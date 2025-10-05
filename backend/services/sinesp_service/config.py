"""Maximus Sinesp Service - Configuration Module.

This module handles the configuration settings for the Sinesp Service.
It provides a centralized place to define and manage parameters such as API keys
for the Sinesp Cidadão API, rate limits, logging levels, and other operational
settings.

By externalizing configuration, this module allows for flexible deployment and
management of the Sinesp Service without requiring code changes. It supports
loading configurations from environment variables, files, or other sources,
ensuring adaptability across different environments.
"""

import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Maximus Sinesp Service.

    Settings are loaded from environment variables or a .env file.
    """
    app_name: str = "Maximus Sinesp Service"
    sinesp_api_key: str = os.getenv("SINESP_API_KEY", "your_sinesp_api_key")
    sinesp_api_url: str = os.getenv("SINESP_API_URL", "https://api.sinespcidadao.com")
    rate_limit_per_minute: int = os.getenv("SINESP_RATE_LIMIT_PER_MINUTE", 10)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        """Configuração para carregar variáveis de ambiente de um arquivo .env."""
        env_file = ".env"
        env_file_encoding = 'utf-8'


def get_settings() -> Settings:
    """Returns a singleton instance of the Settings.

    Returns:
        Settings: The configuration settings for the Sinesp service.
    """
    return Settings()