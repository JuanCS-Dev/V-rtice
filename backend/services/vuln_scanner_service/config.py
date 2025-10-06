"""Maximus Vulnerability Scanner Service - Configuration Module.

This module handles the configuration settings for the Vulnerability Scanner
Service. It provides a centralized place to define and manage parameters such
as API keys for integrated scanning tools (e.g., Nessus, OpenVAS), scan timeouts,
logging levels, and other operational settings.

By externalizing configuration, this module allows for flexible deployment and
management of the Vulnerability Scanner Service without requiring code changes.
It supports loading configurations from environment variables, files, or other
sources, ensuring adaptability across different environments.
"""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Maximus Vulnerability Scanner Service.

    Settings are loaded from environment variables or a .env file.
    """

    app_name: str = "Maximus Vulnerability Scanner Service"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./vuln_scanner.db")
    nmap_path: str = os.getenv("NMAP_PATH", "/usr/bin/nmap")
    nessus_api_key: str = os.getenv("NESSUS_API_KEY", "your_nessus_api_key")
    openvas_api_url: str = os.getenv("OPENVAS_API_URL", "http://localhost:9392")
    scan_timeout_seconds: int = os.getenv("SCAN_TIMEOUT_SECONDS", 1800)  # 30 minutes
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        """Configuração para carregar variáveis de ambiente de um arquivo .env."""

        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Returns a singleton instance of the Settings.

    Returns:
        Settings: The configuration settings for the Vulnerability Scanner service.
    """
    return Settings()
