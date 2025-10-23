"""Configuration module for MAXIMUS Oráculo Service.

Handles feature flags, environment variables, and graceful degradation.
"""

import os
from typing import Dict, Any


class OraculoConfig:
    """Configuration manager for Oráculo service."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Feature flags
        self.enable_kafka = os.getenv("ENABLE_KAFKA", "true").lower() == "true"
        self.enable_websocket = os.getenv("ENABLE_WEBSOCKET", "true").lower() == "true"
        self.enable_llm_codegen = os.getenv("ENABLE_LLM_CODEGEN", "true").lower() == "true"

        # Kafka settings
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
        self.kafka_topic = os.getenv("KAFKA_TOPIC", "maximus.adaptive-immunity.apv")

        # OpenAI settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

        # Service settings
        self.service_name = "maximus_oraculo"
        self.service_version = "2.0.0"

        # Degradation tracking
        self.degradations: list[str] = []

    def check_kafka_availability(self) -> bool:
        """Check if Kafka should be enabled."""
        return self.enable_kafka

    def check_llm_availability(self) -> bool:
        """Check if LLM code generation should be enabled."""
        return self.enable_llm_codegen and bool(self.openai_api_key)

    def get_capabilities(self) -> Dict[str, bool]:
        """Get current service capabilities."""
        return {
            "code_generation": True,  # Always available (with templates fallback)
            "llm_generation": self.check_llm_availability(),
            "kafka_integration": self.enable_kafka and not ("kafka_unavailable" in self.degradations),
            "websocket_streaming": self.enable_websocket and not ("kafka_unavailable" in self.degradations),
        }

    def add_degradation(self, degradation: str):
        """Track a service degradation."""
        if degradation not in self.degradations:
            self.degradations.append(degradation)

    def get_health_status(self) -> Dict[str, Any]:
        """Get health check response."""
        capabilities = self.get_capabilities()
        status = "healthy" if not self.degradations else "degraded"

        return {
            "status": status,
            "service": self.service_name,
            "version": self.service_version,
            "features": capabilities,
            "degradations": self.degradations if self.degradations else None,
        }


# Global configuration instance
config = OraculoConfig()
