"""Maximus Core Service - Apply Maximus.

This module provides the core functionality for applying Maximus AI's
intelligence to various tasks. It acts as an orchestrator, integrating
different Maximus components (e.g., reasoning engine, memory system, tool
orchestrator) to process requests and generate intelligent responses.

It handles the overall flow of information, from receiving a prompt to
delivering a refined output, leveraging the full capabilities of the Maximus
architecture.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

# Assuming these modules exist and are correctly structured within Maximus
from reasoning_engine import ReasoningEngine
from memory_system import MemorySystem
from tool_orchestrator import ToolOrchestrator
from self_reflection import SelfReflection
from confidence_scoring import ConfidenceScoring
from chain_of_thought import ChainOfThought
from rag_system import RAGSystem
from agent_templates import AgentTemplates
from gemini_client import GeminiClient
from vector_db_client import VectorDBClient


class ApplyMaximus:
    """Orchestrates Maximus AI components to process requests and generate intelligent responses.

    This class integrates the reasoning engine, memory system, tool orchestrator,
    self-reflection, and other core components to provide a comprehensive AI solution.
    """

    def __init__(self):
        """Initializes the ApplyMaximus orchestrator with instances of core components."""
        self.reasoning_engine = ReasoningEngine()
        self.memory_system = MemorySystem()
        self.tool_orchestrator = ToolOrchestrator()
        self.self_reflection = SelfReflection()
        self.confidence_scoring = ConfidenceScoring()
        self.chain_of_thought = ChainOfThought()
        self.rag_system = RAGSystem()
        self.agent_templates = AgentTemplates()
        self.gemini_client = GeminiClient()
        self.vector_db_client = VectorDBClient()

    async def process_request(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processes a user request using the full Maximus AI pipeline.

        Args:
            prompt (str): The user's input prompt.
            context (Optional[Dict[str, Any]]): Additional context for the request.

        Returns:
            Dict[str, Any]: A dictionary containing the generated response and other relevant information.
        """
        print(f"[ApplyMaximus] Processing request: {prompt}")
        start_time = datetime.now()

        # 1. Retrieve relevant information from memory/RAG
        retrieved_info = await self.rag_system.retrieve(prompt)
        full_context = {**context, "retrieved_info": retrieved_info} if context else {"retrieved_info": retrieved_info}

        # 2. Generate initial thought/plan using Chain of Thought
        initial_thought = await self.chain_of_thought.generate_thought(prompt, full_context)

        # 3. Reason and generate a response
        reasoned_response = await self.reasoning_engine.reason(initial_thought, full_context)

        # 4. Orchestrate tools if necessary
        tool_output = await self.tool_orchestrator.execute_tools(reasoned_response.get("tool_calls", []))
        if tool_output: # Integrate tool output back into context for further reasoning
            full_context["tool_output"] = tool_output
            reasoned_response = await self.reasoning_engine.reason("Refine response with tool output.", full_context)

        # 5. Self-reflect and refine
        refined_response = await self.self_reflection.reflect_and_refine(reasoned_response, full_context)

        # 6. Score confidence
        confidence_score = await self.confidence_scoring.score(refined_response, full_context)

        # 7. Store interaction in memory
        await self.memory_system.store_interaction(prompt, refined_response, confidence_score)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"[ApplyMaximus] Request processed in {duration:.2f} seconds.")

        return {
            "response": refined_response,
            "confidence": confidence_score,
            "duration_seconds": duration,
            "timestamp": end_time.isoformat()
        }

    async def get_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the ApplyMaximus orchestrator."""
        return {
            "status": "operational",
            "last_request_time": datetime.now().isoformat(),
            "active_components": [
                "ReasoningEngine", "MemorySystem", "ToolOrchestrator",
                "SelfReflection", "ConfidenceScoring", "ChainOfThought",
                "RAGSystem", "AgentTemplates", "GeminiClient", "VectorDBClient"
            ]
        }
