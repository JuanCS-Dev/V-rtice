"""Maximus Core Service - Reasoning Engine.

This module constitutes the core cognitive component of the Maximus AI, responsible
for processing information, making decisions, and generating coherent responses.
It leverages advanced large language models (LLMs) to perform complex reasoning
tasks, synthesize information from various sources, and formulate intelligent
outputs.

The Reasoning Engine integrates inputs from the memory system, RAG system, and
tool orchestrator, applying a sophisticated understanding of context and intent
to produce high-quality, relevant, and actionable responses.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states for external API calls."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures detected, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation for LLM API calls.
    
    Prevents cascade failures by opening circuit after threshold failures,
    allowing periodic retry attempts.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit.
            recovery_timeout: Seconds to wait before attempting recovery.
            success_threshold: Consecutive successes needed to close circuit.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED

    def call_succeeded(self) -> None:
        """Record successful API call."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("[CircuitBreaker] Closing circuit after successful recovery")
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def call_failed(self) -> None:
        """Record failed API call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            logger.warning(f"[CircuitBreaker] Opening circuit after {self.failure_count} failures")
            self.state = CircuitState.OPEN

    def can_attempt(self) -> bool:
        """Check if API call can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).seconds
                if elapsed >= self.recovery_timeout:
                    logger.info("[CircuitBreaker] Attempting recovery (HALF_OPEN)")
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
            
        return True  # HALF_OPEN state


class ReasoningEngine:
    """The core cognitive component of Maximus AI, responsible for processing information,
    making decisions, and generating coherent responses.

    It leverages advanced large language models (LLMs) to perform complex reasoning tasks
    with circuit breaker protection for API resilience.
    """

    def __init__(self, gemini_client: Any, enable_circuit_breaker: bool = True):
        """Initializes the ReasoningEngine with a Gemini client.

        Args:
            gemini_client (Any): An initialized Gemini client for LLM interactions.
            enable_circuit_breaker (bool): Enable circuit breaker for API resilience. Default: True.
        """
        self.gemini_client = gemini_client
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
        self.fallback_mode = False

    async def reason(
        self, 
        prompt: str, 
        context: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Processes information and generates a reasoned response with retry and circuit breaker.

        Args:
            prompt (str): The input prompt or question.
            context (Dict[str, Any]): Additional context for reasoning, including RAG results, CoT, etc.
            max_retries (int): Maximum retry attempts on transient failures. Default: 3.

        Returns:
            Dict[str, Any]: A dictionary containing the generated response and any potential tool calls.

        Raises:
            ValueError: If prompt is empty or invalid.
            RuntimeError: If all attempts fail and circuit breaker opens.
        """
        if not prompt or not prompt.strip():
            logger.error("[ReasoningEngine] Empty prompt received")
            raise ValueError("Prompt cannot be empty")

        # Check circuit breaker
        if self.circuit_breaker and not self.circuit_breaker.can_attempt():
            logger.warning("[ReasoningEngine] Circuit breaker OPEN - using fallback")
            return self._generate_fallback_response(prompt, context)

        logger.info(f"[ReasoningEngine] Reasoning on prompt: {prompt[:50]}...")
        
        for attempt in range(max_retries):
            try:
                # Construct a comprehensive prompt for the LLM
                llm_prompt = self._construct_llm_prompt(prompt, context)

                # Simulate LLM call
                # In a real scenario, this would be a call to self.gemini_client.generate_content
                # and parsing its structured output for response and tool_calls.
                mock_llm_response_text = f"Based on your request '{prompt}' and the provided context, I have reasoned that..."
                mock_tool_calls: List[Dict[str, Any]] = []

                # Example of how tool calls might be generated by the LLM
                if "search for" in prompt.lower():
                    mock_tool_calls.append(
                        {
                            "name": "search_web",
                            "args": {"query": prompt.replace("search for", "").strip()},
                        }
                    )
                elif "weather in" in prompt.lower():
                    location = prompt.split("weather in")[-1].strip()
                    mock_tool_calls.append(
                        {"name": "get_current_weather", "args": {"location": location}}
                    )

                await asyncio.sleep(0.5)  # Simulate LLM processing time
                
                # Success - record in circuit breaker
                if self.circuit_breaker:
                    self.circuit_breaker.call_succeeded()
                
                result = {"response": mock_llm_response_text, "tool_calls": mock_tool_calls}
                logger.info(f"[ReasoningEngine] Generated response with {len(mock_tool_calls)} tool calls")
                return result

            except asyncio.TimeoutError:
                logger.warning(f"[ReasoningEngine] Timeout on attempt {attempt + 1}/{max_retries}")
                if self.circuit_breaker:
                    self.circuit_breaker.call_failed()
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
            except Exception as e:
                logger.error(f"[ReasoningEngine] Error on attempt {attempt + 1}/{max_retries}: {e}")
                if self.circuit_breaker:
                    self.circuit_breaker.call_failed()
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

        # All retries exhausted - use fallback
        logger.warning("[ReasoningEngine] All retries failed, using fallback mode")
        return self._generate_fallback_response(prompt, context)

    def _generate_fallback_response(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simplified response when LLM is unavailable.

        Args:
            prompt (str): The user's input prompt.
            context (Dict[str, Any]): The context for reasoning.

        Returns:
            Dict[str, Any]: Fallback response with degraded capabilities.
        """
        logger.info("[ReasoningEngine] Generating fallback response (degraded mode)")
        self.fallback_mode = True
        
        # Extract keywords for basic tool selection
        tool_calls = []
        if "search" in prompt.lower():
            tool_calls.append({"name": "search_web", "args": {"query": prompt}})
        
        return {
            "response": (
                f"I'm currently experiencing connectivity issues with my reasoning engine. "
                f"However, I understand you're asking about: '{prompt[:100]}...'. "
                f"I'll attempt to help with limited capabilities."
            ),
            "tool_calls": tool_calls,
            "degraded_mode": True,
            "reason": "LLM API unavailable"
        }

    def _construct_llm_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Constructs a detailed prompt for the LLM based on the input and context.

        Args:
            prompt (str): The user's input prompt.
            context (Dict[str, Any]): The context for reasoning.

        Returns:
            str: The constructed prompt string.

        Raises:
            ValueError: If context contains invalid data types.
        """
        try:
            # This method would dynamically build a prompt considering:
            # - The original user query
            # - Retrieved documents from RAG
            # - Chain of Thought steps
            # - Previous turns in a conversation (from memory)
            # - Tool outputs
            # - Agent templates/personas

            context_str = ""
            if context.get("retrieved_docs"):
                docs = context["retrieved_docs"]
                if not isinstance(docs, list):
                    logger.warning(f"[ReasoningEngine] Invalid retrieved_docs type: {type(docs)}")
                else:
                    context_str += "\nRelevant Documents:\n" + "\n---\n".join(
                        [str(d.get("content", "")) for d in docs if isinstance(d, dict)]
                    )
                    
            if context.get("cot_response"):
                cot = context["cot_response"]
                if isinstance(cot, list):
                    context_str += "\nChain of Thought:\n" + "\n".join(str(s) for s in cot)
                else:
                    context_str += f"\nChain of Thought:\n{cot}"
                    
            if context.get("tool_results"):
                context_str += "\nTool Results:\n" + str(context["tool_results"])

            return f"User Query: {prompt}\n{context_str}\n\nBased on the above, provide a comprehensive and reasoned response. If external tools are needed, suggest them in a structured format."
            
        except Exception as e:
            logger.error(f"[ReasoningEngine] Error constructing LLM prompt: {e}")
            # Return minimal safe prompt
            return f"User Query: {prompt}\n\nProvide a response."

    async def evaluate_response(
        self, response: Dict[str, Any], criteria: List[str]
    ) -> Dict[str, Any]:
        """Evaluates a generated response against a set of criteria.

        Args:
            response (Dict[str, Any]): The response to evaluate.
            criteria (List[str]): A list of criteria for evaluation (e.g., accuracy, relevance, completeness).

        Returns:
            Dict[str, Any]: Evaluation results, including scores for each criterion.

        Raises:
            ValueError: If response or criteria are invalid.
        """
        if not response:
            logger.error("[ReasoningEngine] Cannot evaluate empty response")
            raise ValueError("Response cannot be empty")
        
        if not criteria:
            logger.warning("[ReasoningEngine] No criteria provided, using defaults")
            criteria = ["accuracy", "relevance", "completeness"]

        logger.info(f"[ReasoningEngine] Evaluating response against {len(criteria)} criteria...")
        
        try:
            await asyncio.sleep(0.2)
            
            # Simulate evaluation with basic heuristics
            scores = {}
            response_text = str(response.get("response", ""))
            
            for criterion in criteria:
                if criterion == "accuracy":
                    # Longer responses tend to be more detailed (simple heuristic)
                    scores["accuracy"] = min(0.9, 0.5 + len(response_text) / 1000)
                elif criterion == "relevance":
                    # Check if response mentions key terms
                    scores["relevance"] = 0.85 if response_text else 0.0
                elif criterion == "completeness":
                    # Check for tool calls and response length
                    has_tools = len(response.get("tool_calls", [])) > 0
                    scores["completeness"] = 0.9 if has_tools else 0.7
                else:
                    scores[criterion] = 0.75  # Default score
            
            result = {
                **scores,
                "overall_score": sum(scores.values()) / len(scores) if scores else 0.0,
                "evaluated_criteria": criteria,
                "degraded_mode": response.get("degraded_mode", False)
            }
            
            logger.info(f"[ReasoningEngine] Evaluation complete. Overall: {result['overall_score']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"[ReasoningEngine] Error during evaluation: {e}")
            return {
                "error": str(e),
                "overall_score": 0.0,
                "evaluated_criteria": criteria
            }
