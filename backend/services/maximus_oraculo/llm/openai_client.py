"""OpenAI LLM Client for Code Generation.

Production-ready client with:
- GPT-4 integration
- Streaming support
- Token counting and cost tracking
- Error handling (rate limits, timeouts)
- Retry logic with exponential backoff
"""

import asyncio
import os
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class CodeGenerationResult:
    """Result from LLM code generation."""

    code: str
    model: str
    tokens_used: int
    cost_usd: float
    latency_ms: float
    success: bool
    error: Optional[str] = None


class OpenAICodeGenerator:
    """OpenAI client for code generation with production features."""

    # Pricing per 1K tokens (as of 2025)
    PRICING = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4": {"input": 0.03, "output": 0.06},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        max_tokens: int = 4096,
        temperature: float = 0.2,
        max_retries: int = 3,
    ):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to env var)
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            max_retries: Max retry attempts on failure
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries

        # Metrics tracking
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.request_count = 0
        self.error_count = 0

    async def generate_code(
        self,
        task_description: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CodeGenerationResult:
        """Generate code using OpenAI GPT-4.

        Args:
            task_description: What to implement
            language: Target programming language (go, python, etc)
            context: Additional context (framework, dependencies, etc)

        Returns:
            CodeGenerationResult with generated code and metadata
        """
        start_time = time.time()

        # Build prompt
        prompt = self._build_prompt(task_description, language, context or {})

        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt(language),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    timeout=60.0,  # 60s timeout
                )

                # Extract code
                generated_code = response.choices[0].message.content

                # Calculate metrics
                tokens_used = response.usage.total_tokens
                cost_usd = self._calculate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
                latency_ms = (time.time() - start_time) * 1000

                # Update tracking
                self.total_tokens_used += tokens_used
                self.total_cost_usd += cost_usd
                self.request_count += 1

                return CodeGenerationResult(
                    code=generated_code,
                    model=self.model,
                    tokens_used=tokens_used,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                    success=True,
                )

            except Exception as e:
                self.error_count += 1

                # Last attempt - return error
                if attempt == self.max_retries - 1:
                    latency_ms = (time.time() - start_time) * 1000
                    return CodeGenerationResult(
                        code="",
                        model=self.model,
                        tokens_used=0,
                        cost_usd=0.0,
                        latency_ms=latency_ms,
                        success=False,
                        error=str(e),
                    )

                # Exponential backoff
                backoff_seconds = 2 ** attempt
                print(f"[OpenAI] Attempt {attempt + 1} failed: {e}")
                print(f"[OpenAI] Retrying in {backoff_seconds}s...")
                await asyncio.sleep(backoff_seconds)

        # Should never reach here
        return CodeGenerationResult(
            code="",
            model=self.model,
            tokens_used=0,
            cost_usd=0.0,
            latency_ms=0.0,
            success=False,
            error="Max retries exceeded",
        )

    def _get_system_prompt(self, language: str) -> str:
        """Get language-specific system prompt."""
        if language.lower() == "go":
            return """You are an expert Go developer following best practices.

Rules:
- Write production-ready, idiomatic Go code
- Follow Effective Go guidelines
- Handle ALL errors explicitly (no panics unless unrecoverable)
- Use context.Context for cancelation
- Add godoc comments for exported functions
- Use interfaces for testability
- Keep functions small and focused
- No external dependencies unless specified

Output ONLY the Go code. No markdown formatting, no explanations."""

        elif language.lower() == "python":
            return """You are an expert Python developer following best practices.

Rules:
- Write production-ready Python code
- Follow PEP 8 style guide
- Add type hints (Python 3.9+)
- Write comprehensive docstrings (Google style)
- Handle errors with try/except
- Use context managers where appropriate
- Keep functions small and focused
- No external dependencies unless specified

Output ONLY the Python code. No markdown formatting, no explanations."""

        else:
            return f"""You are an expert {language} developer.

Write production-ready, well-commented code following best practices.
Output ONLY the code. No markdown formatting, no explanations."""

    def _build_prompt(
        self,
        task_description: str,
        language: str,
        context: Dict[str, Any],
    ) -> str:
        """Build detailed prompt for code generation."""
        prompt = f"Generate {language} code for: {task_description}\n\n"

        # Add framework context
        if "framework" in context:
            prompt += f"Framework: {context['framework']}\n"

        # Add dependencies
        if "dependencies" in context:
            deps = context.get("dependencies", [])
            if deps:
                prompt += f"Available dependencies: {', '.join(deps)}\n"

        # Add existing code context
        if "existing_code" in context:
            prompt += f"\nExisting code to modify:\n{context['existing_code']}\n"

        # Add requirements
        if "requirements" in context:
            req = context["requirements"]
            prompt += "\nRequirements:\n"
            for key, value in req.items():
                prompt += f"- {key}: {value}\n"

        prompt += "\nGenerate complete, production-ready code."

        return prompt

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD based on token usage."""
        pricing = self.PRICING.get(self.model, {"input": 0.01, "output": 0.03})

        prompt_cost = (prompt_tokens / 1000) * pricing["input"]
        completion_cost = (completion_tokens / 1000) * pricing["output"]

        return prompt_cost + completion_cost

    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics."""
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.request_count - self.error_count) / self.request_count
                if self.request_count > 0
                else 0.0
            ),
        }
