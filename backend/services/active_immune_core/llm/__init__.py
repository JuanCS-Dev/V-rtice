"""LLM Client Abstraction Layer.

Provides unified interface to multiple LLM providers (OpenAI, Anthropic).
Enables Sentinel detection, Fusion narrative, and Honeypot interaction.

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

from llm.llm_client import BaseLLMClient, OpenAIClient, AnthropicClient, LLMError

__all__ = [
    "BaseLLMClient",
    "OpenAIClient",
    "AnthropicClient",
    "LLMError",
]
