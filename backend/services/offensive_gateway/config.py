"""Maximus Offensive Gateway Service - Configuration Module.

This module handles the configuration settings for the Offensive Gateway Service.
It provides a centralized place to define and manage parameters such as API keys
for integrated offensive tools (e.g., Metasploit, Cobalt Strike), connection
details, logging levels, and other operational settings.

By externalizing configuration, this module allows for flexible deployment and
management of the Offensive Gateway Service without requiring code changes.
It supports loading configurations from environment variables, files, or other
sources, ensuring adaptability across different environments.
"""

import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Maximus Offensive Gateway Service.

    Settings are loaded from environment variables or a .env file.
    """

    app_name: str = "Maximus Offensive Gateway Service"
    metasploit_rpc_host: str = os.getenv("METASPLOIT_RPC_HOST", "localhost")
    metasploit_rpc_port: int = os.getenv("METASPLOIT_RPC_PORT", 55553)
    metasploit_rpc_user: str = os.getenv("METASPLOIT_RPC_USER", "msf")
    metasploit_rpc_pass: str = os.getenv("METASPLOIT_RPC_PASS", "random")

    cobalt_strike_host: str = os.getenv("COBALT_STRIKE_HOST", "localhost")
    cobalt_strike_port: int = os.getenv("COBALT_STRIKE_PORT", 50050)
    cobalt_strike_pass: str = os.getenv("COBALT_STRIKE_PASS", "password")

    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        """Configuração para carregar variáveis de ambiente de um arquivo .env."""

        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Returns a singleton instance of the Settings.

    Returns:
        Settings: The configuration settings for the Offensive Gateway service.
    """
    return Settings()
