"""
Claude LLM Client - Anthropic Claude API integration.

Implements BaseLLMClient for Claude models via Anthropic SDK.

Model Recommendations (2025-01):
    - claude-3-5-sonnet-20241022: Best balance (200K context, $3/$15 per MTok)
    - claude-3-opus-20240229: Highest quality (200K context, $15/$75 per MTok)
    - claude-3-haiku-20240307: Fastest/cheapest (200K context, $0.25/$1.25 per MTok)

Pricing (as of 2025-01):
    - Sonnet: $3/MTok input, $15/MTok output
    - Opus: $15/MTok input, $75/MTok output
    - Haiku: $0.25/MTok input, $1.25/MTok output

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - Giver of wisdom
"""

import asyncio
import logging
from typing import List, Optional, Any

try:
    from anthropic import Anthropic, AsyncAnthropic
    from anthropic import (
        RateLimitError,
        AuthenticationError,
        BadRequestError,
    )
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    # Define stubs for type checking
    Anthropic = Any
    AsyncAnthropic = Any
    RateLimitError = Exception
    AuthenticationError = Exception
    BadRequestError = Exception

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

logger = logging.getLogger(__name__)


class ClaudeClient(BaseLLMClient):
    """
    Claude LLM client using Anthropic SDK.
    
    Features:
    - Async API calls with retry logic
    - Exponential backoff on rate limits
    - Token counting via Claude tokenizer
    - Cost estimation
    - Error handling and logging
    
    Usage:
        >>> client = ClaudeClient(
        ...     api_key=os.environ["ANTHROPIC_API_KEY"],
        ...     model="claude-3-5-sonnet-20241022",
        ... )
        >>> response = await client.complete(
        ...     messages=[LLMMessage(role="user", content="Hello!")],
        ...     temperature=0.7,
        ... )
        >>> print(response.content)
    """
    
    # Pricing per 1M tokens (MTok) in USD
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_retries: int = 3,
        timeout_seconds: int = 120,
    ):
        """
        Initialize Claude client.
        
        Args:
            api_key: Anthropic API key
            model: Claude model identifier
            max_retries: Max retry attempts
            timeout_seconds: Request timeout
            
        Raises:
            ImportError: If anthropic package not installed
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )
        
        super().__init__(api_key, model, max_retries, timeout_seconds)
        
        # Initialize Anthropic client
        self._client = AsyncAnthropic(
            api_key=api_key,
            timeout=timeout_seconds,
        )
        
        logger.info(f"ClaudeClient initialized with model {model}")
    
    @property
    def provider(self) -> LLMProvider:
        """Return provider enum."""
        return LLMProvider.CLAUDE
    
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
        
        Implements retry logic with exponential backoff.
        Converts LLMMessage to Anthropic format.
        
        Args:
            messages: Conversation messages
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Max output tokens
            system_prompt: System prompt (Claude supports this natively)
            **kwargs: Additional Anthropic parameters
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            LLMRateLimitError: On rate limit (after retries)
            LLMAuthenticationError: On auth failure
            LLMInvalidRequestError: On invalid request
            LLMError: On other errors
        """
        # Convert messages to Anthropic format
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Retry loop
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling Claude API (attempt {attempt + 1}/{self.max_retries})"
                )
                
                # Build request params
                request_params = {
                    "model": self.model,
                    "messages": anthropic_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs,
                }
                
                # Add system prompt if provided
                if system_prompt:
                    request_params["system"] = system_prompt
                
                # Call API
                response = await self._client.messages.create(**request_params)
                
                # Extract content (Claude returns list of content blocks)
                content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        content += block.text
                
                # Calculate total tokens
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                
                logger.info(
                    f"✅ Claude API success: {tokens_used} tokens "
                    f"({response.usage.input_tokens} in, {response.usage.output_tokens} out)"
                )
                
                return LLMResponse(
                    content=content,
                    model=response.model,
                    tokens_used=tokens_used,
                    finish_reason=response.stop_reason or "stop",
                    raw_response={
                        "id": response.id,
                        "usage": {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
                        },
                        "stop_reason": response.stop_reason,
                    },
                )
                
            except RateLimitError as e:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    f"⚠️ Rate limit hit (attempt {attempt + 1}), "
                    f"waiting {wait_time}s..."
                )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise LLMRateLimitError(
                        f"Rate limit exceeded after {self.max_retries} attempts"
                    ) from e
                    
            except AuthenticationError as e:
                logger.error("❌ Claude authentication failed")
                raise LLMAuthenticationError(
                    "Invalid API key or authentication failed"
                ) from e
                
            except BadRequestError as e:
                logger.error(f"❌ Invalid request to Claude API: {e}")
                raise LLMInvalidRequestError(f"Invalid request: {e}") from e
                
            except Exception as e:
                logger.error(
                    f"❌ Claude API error (attempt {attempt + 1}): {e}",
                    exc_info=True,
                )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise LLMError(f"Claude API failed: {e}") from e
        
        # Should never reach here
        raise LLMError("Unexpected: retry loop exited without return")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Claude tokenizer.
        
        Uses Anthropic's token counting API for accurate counts.
        Falls back to rough estimate (chars/4) if API unavailable.
        
        Args:
            text: Text to count
            
        Returns:
            Number of tokens
        """
        try:
            # Use Anthropic's count_tokens method
            result = self._client.count_tokens(text)
            return result
        except Exception as e:
            logger.warning(f"Token counting failed, using estimate: {e}")
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4
    
    def estimate_cost(
        self, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Estimate cost for token usage.
        
        Uses current Claude pricing (2025-01).
        
        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(self.model)
        if not pricing:
            logger.warning(f"Unknown model {self.model}, cannot estimate cost")
            return 0.0
        
        # Convert from per-MTok to per-token
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
