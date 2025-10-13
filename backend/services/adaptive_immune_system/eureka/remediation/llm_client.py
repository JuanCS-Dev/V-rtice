"""
LLM Client - Integration with Claude and GPT-4 for code generation.

Provides unified interface for multiple LLM providers with:
- Token usage tracking
- Cost estimation
- Rate limiting
- Retry logic
- Response validation
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LLMRequest(BaseModel):
    """LLM request model."""

    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.2  # Low temperature for deterministic code generation
    model: str = "claude-3-5-sonnet-20241022"


class LLMResponse(BaseModel):
    """LLM response model."""

    content: str
    model: str
    tokens_used: int
    cost_usd: float
    finish_reason: str


class LLMClient:
    """
    Unified LLM client for code generation.

    Supports:
    - Anthropic Claude (Claude 3.5 Sonnet, Claude 3 Opus)
    - OpenAI GPT (GPT-4, GPT-4 Turbo)

    Features:
    - Automatic provider selection
    - Token usage tracking
    - Cost estimation
    - Rate limiting
    - Retry with exponential backoff
    """

    # Cost per 1M tokens (input/output)
    COSTS = {
        "claude-3-5-sonnet-20241022": (3.00, 15.00),  # $3/$15 per 1M tokens
        "claude-3-opus-20240229": (15.00, 75.00),
        "gpt-4-turbo-2024-04-09": (10.00, 30.00),
        "gpt-4": (30.00, 60.00),
    }

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        default_model: str = "claude-3-5-sonnet-20241022",
    ):
        """
        Initialize LLM client.

        Args:
            anthropic_api_key: Anthropic API key (or use ANTHROPIC_API_KEY env)
            openai_api_key: OpenAI API key (or use OPENAI_API_KEY env)
            default_model: Default model to use
        """
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.default_model = default_model

        if not self.anthropic_api_key and not self.openai_api_key:
            logger.warning(
                "No LLM API keys configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )

        logger.info(
            f"LLMClient initialized: "
            f"anthropic={'configured' if self.anthropic_api_key else 'missing'}, "
            f"openai={'configured' if self.openai_api_key else 'missing'}"
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.2,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate code using LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            model: Model to use (defaults to default_model)

        Returns:
            LLMResponse with generated content

        Raises:
            RuntimeError: If LLM request fails
        """
        model = model or self.default_model

        logger.info(f"Generating code with {model}...")

        if model.startswith("claude"):
            response = await self._generate_anthropic(
                prompt, system_prompt, max_tokens, temperature, model
            )
        elif model.startswith("gpt"):
            response = await self._generate_openai(
                prompt, system_prompt, max_tokens, temperature, model
            )
        else:
            raise ValueError(f"Unsupported model: {model}")

        logger.info(
            f"Generated {len(response.content)} chars using {response.tokens_used} tokens "
            f"(cost: ${response.cost_usd:.4f})"
        )

        return response

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        model: str,
    ) -> LLMResponse:
        """Generate using Anthropic Claude API."""
        if not self.anthropic_api_key:
            raise RuntimeError("Anthropic API key not configured")

        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            payload["system"] = system_prompt

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(
                            f"Anthropic API error {response.status}: {error_text}"
                        )

                    data = await response.json()

                    content = data["content"][0]["text"]
                    tokens_used = data["usage"]["input_tokens"] + data["usage"]["output_tokens"]

                    # Calculate cost
                    input_cost, output_cost = self.COSTS.get(model, (3.00, 15.00))
                    cost = (
                        data["usage"]["input_tokens"] / 1_000_000 * input_cost
                        + data["usage"]["output_tokens"] / 1_000_000 * output_cost
                    )

                    return LLMResponse(
                        content=content,
                        model=model,
                        tokens_used=tokens_used,
                        cost_usd=cost,
                        finish_reason=data.get("stop_reason", "end_turn"),
                    )

            except asyncio.TimeoutError:
                raise RuntimeError("Anthropic API request timed out after 120s")

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        model: str,
    ) -> LLMResponse:
        """Generate using OpenAI GPT API."""
        if not self.openai_api_key:
            raise RuntimeError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(
                            f"OpenAI API error {response.status}: {error_text}"
                        )

                    data = await response.json()

                    content = data["choices"][0]["message"]["content"]
                    tokens_used = data["usage"]["total_tokens"]

                    # Calculate cost
                    input_cost, output_cost = self.COSTS.get(model, (10.00, 30.00))
                    cost = (
                        data["usage"]["prompt_tokens"] / 1_000_000 * input_cost
                        + data["usage"]["completion_tokens"] / 1_000_000 * output_cost
                    )

                    return LLMResponse(
                        content=content,
                        model=model,
                        tokens_used=tokens_used,
                        cost_usd=cost,
                        finish_reason=data["choices"][0]["finish_reason"],
                    )

            except asyncio.TimeoutError:
                raise RuntimeError("OpenAI API request timed out after 120s")

    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.2,
        model: Optional[str] = None,
        max_retries: int = 3,
    ) -> LLMResponse:
        """
        Generate with retry logic.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            model: Model to use
            max_retries: Maximum retry attempts

        Returns:
            LLMResponse

        Raises:
            RuntimeError: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                return await self.generate(
                    prompt, system_prompt, max_tokens, temperature, model
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"LLM generation failed after {max_retries} retries: {e}")

                backoff = 2 ** attempt
                logger.warning(
                    f"LLM generation failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {backoff}s..."
                )
                await asyncio.sleep(backoff)

        raise RuntimeError("Should not reach here")

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Rough approximation: 1 token ≈ 4 characters

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Estimate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name

        Returns:
            Estimated cost in USD
        """
        input_cost, output_cost = self.COSTS.get(model, (3.00, 15.00))

        return (
            input_tokens / 1_000_000 * input_cost
            + output_tokens / 1_000_000 * output_cost
        )
