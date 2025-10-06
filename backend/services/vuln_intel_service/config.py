"""Maximus Vulnerability Intelligence Service - Configuration Module.

This module handles the configuration settings for the Vulnerability Intelligence
Service. It provides a centralized place to define and manage parameters such
as API keys for external vulnerability databases (e.g., NVD, Exploit-DB),
data refresh intervals, logging levels, and other operational settings.

By externalizing configuration, this module allows for flexible deployment and
management of the Vulnerability Intelligence Service without requiring code changes.
It supports loading configurations from environment variables, files, or other
sources, ensuring adaptability across different environments.
"""

import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Maximus Vulnerability Intelligence Service.

    Settings are loaded from environment variables or a .env file.
    """

    app_name: str = "Maximus Vulnerability Intelligence Service"
    nvd_api_key: str = os.getenv("NVD_API_KEY", "your_nvd_api_key")
    exploitdb_api_key: str = os.getenv("EXPLOITDB_API_KEY", "your_exploitdb_api_key")
    data_refresh_interval_hours: int = os.getenv("DATA_REFRESH_INTERVAL_HOURS", 24)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        """Configuração para carregar variáveis de ambiente de um arquivo .env."""

        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Returns a singleton instance of the Settings.

    Returns:
        Settings: The configuration settings for the Vulnerability Intelligence service.
    """
    return Settings()
