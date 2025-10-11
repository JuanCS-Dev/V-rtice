"""
Base LLM Client - Abstract interface for LLM providers.

Provides common interface for different LLM providers (Claude, GPT-4, etc).
Enables swapping LLM backends without changing strategy code.

Theoretical Foundation:
    LLM clients abstract provider-specific APIs behind common interface.
    This enables:
    - Provider agnosticism in strategies
    - Easy A/B testing between models
    - Fallback to different providers
    - Consistent error handling and retry logic
    
    Interface design influenced by:
    - Anthropic SDK patterns
    - OpenAI API conventions
    - Langchain abstractions

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - Source of all intelligence
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    CLAUDE = "claude"
    GPT4 = "gpt4"
    LOCAL = "local"


@dataclass
class LLMMessage:
    """
    Single message in conversation.
    
    Attributes:
        role: Message role (user, assistant, system)
        content: Message text content
    """
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class LLMResponse:
    """
    LLM completion response.
    
    Attributes:
        content: Generated text
        model: Model used (e.g., "claude-3-5-sonnet-20241022")
        tokens_used: Total tokens (input + output)
        finish_reason: Completion reason (stop, length, etc)
        raw_response: Original provider response for debugging
    """
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    raw_response: Optional[Dict[str, Any]] = None


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class LLMAuthenticationError(LLMError):
    """Authentication failed."""
    pass


class LLMInvalidRequestError(LLMError):
    """Invalid request parameters."""
    pass


class BaseLLMClient(ABC):
    """
    Abstract base for LLM clients.
    
    Subclasses implement provider-specific logic while maintaining
    consistent interface for strategies.
    
    Common features provided:
    - Retry logic with exponential backoff
    - Rate limiting
    - Token counting
    - Error handling
    
    Usage:
        >>> client = ClaudeClient(api_key="...")
        >>> response = await client.complete(
        ...     messages=[LLMMessage(role="user", content="Fix this code...")],
        ...     temperature=0.7,
        ... )
        >>> print(response.content)
    """
    
    def __init__(
        self,
        api_key: str,
        model: str,
        max_retries: int = 3,
        timeout_seconds: int = 120,
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: Provider API key
            model: Model identifier
            max_retries: Max retry attempts on failure
            timeout_seconds: Request timeout
        """
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
    
    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Return provider enum."""
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate completion from messages.
        
        Args:
            messages: Conversation messages
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Max output tokens
            system_prompt: System prompt (if supported)
            **kwargs: Provider-specific parameters
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            LLMError: On API errors
            LLMRateLimitError: On rate limit
            LLMAuthenticationError: On auth failure
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Uses provider-specific tokenizer for accurate counts.
        
        Args:
            text: Text to count
            
        Returns:
            Number of tokens
        """
        pass
    
    def estimate_cost(
        self, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Estimate cost in USD for token usage.
        
        Default implementation returns 0.0. Override with provider pricing.
        
        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Estimated cost in USD
        """
        return 0.0
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__} provider={self.provider.value} model={self.model}>"
