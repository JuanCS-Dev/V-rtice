"""
LLM Module - Language Model clients for patch generation.

Provides LLM integration for AI-assisted vulnerability patching.

Clients:
    - ClaudeClient: Anthropic Claude models
    - GPT4Client: OpenAI GPT-4 models (future)
    - LocalClient: Local LLMs via Ollama (future)

Author: MAXIMUS Team
Date: 2025-01-10
"""

from llm.base_client import (
    BaseLLMClient,
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMInvalidRequestError,
)

from llm.claude_client import ClaudeClient

from llm.prompt_templates import (
    SYSTEM_PROMPT,
    generate_patch_prompt,
    generate_validation_prompt,
    generate_complexity_assessment_prompt,
    format_patch_explanation,
)

__all__ = [
    # Base classes
    "BaseLLMClient",
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    # Exceptions
    "LLMError",
    "LLMRateLimitError",
    "LLMAuthenticationError",
    "LLMInvalidRequestError",
    # Clients
    "ClaudeClient",
    # Prompts
    "SYSTEM_PROMPT",
    "generate_patch_prompt",
    "generate_validation_prompt",
    "generate_complexity_assessment_prompt",
    "format_patch_explanation",
]
