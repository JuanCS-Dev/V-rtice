"""LLM Client Implementation - Multi-provider Support.

Provides unified async interface to OpenAI GPT-4o and Anthropic Claude.
Handles retries, error handling, and token management.

Biological Inspiration:
- Neural plasticity: Multiple pathways to same goal
- Redundancy: Fallback providers ensure resilience
- Adaptation: Choose best provider for task

IIT Integration:
- Φ maximization: LLM provides integrated understanding
- Information integration: Combines detection signals into narrative
- Conscious analysis: LLM emulates human SOC analyst reasoning

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from prometheus_client import Counter, Histogram

try:
    import openai
except ImportError:
    openai = None

try:
    from anthropic import Anthropic, AsyncAnthropic
except ImportError:
    Anthropic = None
    AsyncAnthropic = None

logger = logging.getLogger(__name__)


# Metrics
LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "status"]
)

LLM_LATENCY = Histogram(
    "llm_latency_seconds",
    "LLM API call latency",
    ["provider"]
)

LLM_TOKENS_USED = Counter(
    "llm_tokens_used_total",
    "Total tokens consumed",
    ["provider", "type"]
)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMProviderUnavailable(LLMError):
    """Raised when LLM provider is not available."""
    pass


class LLMAPIError(LLMError):
    """Raised when LLM API returns an error."""
    pass


@dataclass
class LLMResponse:
    """LLM generation response with metadata.
    
    Attributes:
        content: Generated text content
        provider: LLM provider used
        model: Model name
        tokens_used: Total tokens consumed
        prompt_tokens: Tokens in prompt
        completion_tokens: Tokens in completion
        latency_ms: Generation latency in milliseconds
    """
    content: str
    provider: str
    model: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class BaseLLMClient(ABC):
    """Base abstract interface for LLM providers.
    
    All LLM clients must implement this interface to ensure
    consistent behavior across providers.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate completion from prompt.
        
        Args:
            prompt: User prompt/question
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            system_prompt: Optional system instructions
        
        Returns:
            LLMResponse with generated content and metadata
        
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available.
        
        Returns:
            True if provider can be used
        """
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT-4o client with async support.
    
    Provides access to OpenAI's GPT-4o model for high-quality
    threat analysis and narrative generation.
    
    Attributes:
        api_key: OpenAI API key
        model: Model name (default: gpt-4o)
        organization: OpenAI organization ID (optional)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        organization: Optional[str] = None
    ):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env)
            model: Model name
            organization: OpenAI org ID (optional)
        
        Raises:
            LLMProviderUnavailable: If openai package not installed
        """
        if openai is None:
            raise LLMProviderUnavailable(
                "openai package not installed. "
                "Install with: pip install openai"
            )
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMProviderUnavailable(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )
        
        self.model = model
        self.organization = organization
        
        # Configure client
        openai.api_key = self.api_key
        if self.organization:
            openai.organization = self.organization
        
        logger.info(f"OpenAI client initialized with model: {self.model}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate completion using GPT-4o.
        
        Args:
            prompt: User prompt
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            system_prompt: System instructions
        
        Returns:
            LLMResponse with generated content
        
        Raises:
            LLMAPIError: If OpenAI API call fails
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            import time
            start_time = time.time()
            
            with LLM_LATENCY.labels(provider="openai").time():
                response = await openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract response data
            content = response.choices[0].message.content
            usage = response.usage
            
            # Record metrics
            LLM_REQUESTS_TOTAL.labels(provider="openai", status="success").inc()
            LLM_TOKENS_USED.labels(provider="openai", type="prompt").inc(
                usage.prompt_tokens
            )
            LLM_TOKENS_USED.labels(provider="openai", type="completion").inc(
                usage.completion_tokens
            )
            
            return LLMResponse(
                content=content,
                provider="openai",
                model=self.model,
                tokens_used=usage.total_tokens,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                latency_ms=latency_ms
            )
        
        except Exception as e:
            LLM_REQUESTS_TOTAL.labels(provider="openai", status="error").inc()
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise LLMAPIError(f"OpenAI generation failed: {e}")
    
    async def is_available(self) -> bool:
        """Check if OpenAI is available.
        
        Returns:
            True if API key is configured
        """
        return bool(self.api_key)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client with async support.
    
    Provides access to Anthropic's Claude model as alternative
    to OpenAI. Known for high-quality reasoning and safety.
    
    Attributes:
        api_key: Anthropic API key
        model: Model name (default: claude-3-5-sonnet-20241022)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        """Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env)
            model: Model name
        
        Raises:
            LLMProviderUnavailable: If anthropic package not installed
        """
        if AsyncAnthropic is None:
            raise LLMProviderUnavailable(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMProviderUnavailable(
                "Anthropic API key not found. "
                "Set ANTHROPIC_API_KEY environment variable."
            )
        
        self.model = model
        self.client = AsyncAnthropic(api_key=self.api_key)
        
        logger.info(f"Anthropic client initialized with model: {self.model}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate completion using Claude.
        
        Args:
            prompt: User prompt
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            system_prompt: System instructions
        
        Returns:
            LLMResponse with generated content
        
        Raises:
            LLMAPIError: If Anthropic API call fails
        """
        try:
            import time
            start_time = time.time()
            
            with LLM_LATENCY.labels(provider="anthropic").time():
                kwargs = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                if system_prompt:
                    kwargs["system"] = system_prompt
                
                message = await self.client.messages.create(**kwargs)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract response data
            content = message.content[0].text
            
            # Record metrics
            LLM_REQUESTS_TOTAL.labels(provider="anthropic", status="success").inc()
            LLM_TOKENS_USED.labels(provider="anthropic", type="prompt").inc(
                message.usage.input_tokens
            )
            LLM_TOKENS_USED.labels(provider="anthropic", type="completion").inc(
                message.usage.output_tokens
            )
            
            return LLMResponse(
                content=content,
                provider="anthropic",
                model=self.model,
                tokens_used=message.usage.input_tokens + message.usage.output_tokens,
                prompt_tokens=message.usage.input_tokens,
                completion_tokens=message.usage.output_tokens,
                latency_ms=latency_ms
            )
        
        except Exception as e:
            LLM_REQUESTS_TOTAL.labels(provider="anthropic", status="error").inc()
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            raise LLMAPIError(f"Anthropic generation failed: {e}")
    
    async def is_available(self) -> bool:
        """Check if Anthropic is available.
        
        Returns:
            True if API key is configured
        """
        return bool(self.api_key)


class FallbackLLMClient(BaseLLMClient):
    """LLM client with fallback support.
    
    Tries primary provider first, falls back to secondary if primary fails.
    Ensures defense operations continue even if one provider is down.
    
    Biological Inspiration:
    - Neural redundancy: Multiple pathways for critical functions
    - Resilience: System continues functioning despite component failure
    
    Attributes:
        primary: Primary LLM client
        fallback: Fallback LLM client (optional)
    """
    
    def __init__(
        self,
        primary: BaseLLMClient,
        fallback: Optional[BaseLLMClient] = None
    ):
        """Initialize fallback client.
        
        Args:
            primary: Primary LLM client
            fallback: Fallback client (optional)
        """
        self.primary = primary
        self.fallback = fallback
        
        logger.info(
            f"Fallback LLM client initialized. "
            f"Primary available: {self.primary.__class__.__name__}"
        )
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate with fallback support.
        
        Tries primary first, falls back to secondary on failure.
        
        Args:
            prompt: User prompt
            max_tokens: Max tokens
            temperature: Sampling temperature
            system_prompt: System instructions
        
        Returns:
            LLMResponse from successful provider
        
        Raises:
            LLMAPIError: If all providers fail
        """
        # Try primary
        try:
            if await self.primary.is_available():
                return await self.primary.generate(
                    prompt, max_tokens, temperature, system_prompt
                )
        except LLMAPIError as e:
            logger.warning(f"Primary LLM failed: {e}")
        
        # Try fallback
        if self.fallback:
            try:
                if await self.fallback.is_available():
                    logger.info("Falling back to secondary LLM provider")
                    return await self.fallback.generate(
                        prompt, max_tokens, temperature, system_prompt
                    )
            except LLMAPIError as e:
                logger.error(f"Fallback LLM also failed: {e}")
        
        raise LLMAPIError("All LLM providers failed")
    
    async def is_available(self) -> bool:
        """Check if any provider is available.
        
        Returns:
            True if primary or fallback is available
        """
        primary_available = await self.primary.is_available()
        if primary_available:
            return True
        
        if self.fallback:
            return await self.fallback.is_available()
        
        return False
