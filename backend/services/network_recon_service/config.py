"""Maximus Network Reconnaissance Service - Configuration Module.

This module handles the configuration settings for the Network Reconnaissance
Service. It provides a centralized place to define and manage parameters such
as API keys for external reconnaissance tools, scan timeouts, logging levels,
and other operational settings.

By externalizing configuration, this module allows for flexible deployment and
management of the Network Reconnaissance Service without requiring code changes.
It supports loading configurations from environment variables, files, or other
sources, ensuring adaptability across different environments.
"""

import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Maximus Network Reconnaissance Service.

    Settings are loaded from environment variables or a .env file.
    """
    app_name: str = "Maximus Network Reconnaissance Service"
    nmap_path: str = os.getenv("NMAP_PATH", "/usr/bin/nmap")
    masscan_path: str = os.getenv("MASSCAN_PATH", "/usr/bin/masscan")
    scan_timeout_seconds: int = os.getenv("SCAN_TIMEOUT_SECONDS", 300)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        """Configuração para carregar variáveis de ambiente de um arquivo .env."""
        env_file = ".env"
        env_file_encoding = 'utf-8'


def get_settings() -> Settings:
    """Returns a singleton instance of the Settings.

    Returns:
        Settings: The configuration settings for the Network Reconnaissance service.
    """
    return Settings()