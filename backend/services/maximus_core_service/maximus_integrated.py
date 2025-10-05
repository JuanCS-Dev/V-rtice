"""Maximus Core Service - Maximus Integrated.

This module serves as the primary integration point for the entire Maximus AI
system, bringing together all core components into a cohesive and functional
unit. It orchestrates the flow of information and control between the autonomic
core, reasoning engine, memory system, tool orchestrator, and other specialized
modules.

This integrated module is responsible for the overall operation and coordination
of Maximus, ensuring that all parts work in harmony to achieve intelligent
behavior and respond effectively to complex tasks and dynamic environments.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from autonomic_core.homeostatic_control import HomeostaticControlLoop
from autonomic_core.system_monitor import SystemMonitor
from autonomic_core.resource_analyzer import ResourceAnalyzer
from autonomic_core.resource_planner import ResourcePlanner
from autonomic_core.resource_executor import ResourceExecutor

from reasoning_engine import ReasoningEngine
from memory_system import MemorySystem
from tool_orchestrator import ToolOrchestrator
from self_reflection import SelfReflection
from confidence_scoring import ConfidenceScoring
from chain_of_thought import ChainOfThought
from rag_system import RAGSystem
from agent_templates import AgentTemplates
from gemini_client import GeminiClient, GeminiConfig
from vector_db_client import VectorDBClient
from all_services_tools import AllServicesTools
import os


class MaximusIntegrated:
    """Integrates and orchestrates all core components of the Maximus AI system.

    This class provides a unified interface to the entire Maximus AI, managing
    the interactions between its autonomic core, reasoning capabilities, memory,
    and tool-use functionalities.
    """

    def __init__(self):
        """Initializes all Maximus AI components and sets up their interconnections."""
        # Initialize core clients/dependencies
        gemini_config = GeminiConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model="gemini-1.5-flash",
            temperature=0.7,
            max_tokens=4096,
            timeout=60
        )
        self.gemini_client = GeminiClient(gemini_config)
        self.vector_db_client = VectorDBClient()

        # Initialize Autonomic Core components
        self.system_monitor = SystemMonitor()
        self.resource_analyzer = ResourceAnalyzer()
        self.resource_planner = ResourcePlanner()
        self.resource_executor = ResourceExecutor()
        self.hcl = HomeostaticControlLoop(
            monitor=self.system_monitor,
            analyzer=self.resource_analyzer,
            planner=self.resource_planner,
            executor=self.resource_executor
        )

        # Initialize other core components
        self.memory_system = MemorySystem(vector_db_client=self.vector_db_client)
        self.rag_system = RAGSystem(vector_db_client=self.vector_db_client)
        self.agent_templates = AgentTemplates()
        self.all_services_tools = AllServicesTools(gemini_client=self.gemini_client)
        self.tool_orchestrator = ToolOrchestrator(gemini_client=self.gemini_client)
        self.chain_of_thought = ChainOfThought(gemini_client=self.gemini_client)
        self.reasoning_engine = ReasoningEngine(gemini_client=self.gemini_client)
        self.self_reflection = SelfReflection()
        self.confidence_scoring = ConfidenceScoring()

    async def start_autonomic_core(self):
        """Starts the Homeostatic Control Loop (HCL) for autonomic management."""
        await self.hcl.start()

    async def stop_autonomic_core(self):
        """Stops the Homeostatic Control Loop (HCL)."""
        await self.hcl.stop()

    async def process_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processes a natural language query through the integrated Maximus AI pipeline.

        Args:
            query (str): The natural language query from the user.
            user_context (Optional[Dict[str, Any]]): Additional context provided by the user.

        Returns:
            Dict[str, Any]: A comprehensive response from Maximus, including reasoning, actions, and confidence.
        """
        print(f"[MaximusIntegrated] Processing query: {query}")
        start_time = datetime.now()

        # 1. Retrieve relevant information (RAG)
        retrieved_docs = await self.rag_system.retrieve(query)
        context = {"query": query, "user_context": user_context, "retrieved_docs": retrieved_docs}

        # 2. Generate Chain of Thought
        cot_response = await self.chain_of_thought.generate_thought(query, context)
        context["cot_response"] = cot_response

        # 3. Reasoning Engine to formulate initial response and potential tool calls
        reasoning_output = await self.reasoning_engine.reason(query, context)
        initial_response = reasoning_output.get("response", "")
        tool_calls = reasoning_output.get("tool_calls", [])

        # 4. Execute tools if any
        tool_results = []
        if tool_calls:
            tool_results = await self.tool_orchestrator.execute_tools(tool_calls)
            context["tool_results"] = tool_results
            # Re-reason with tool results if necessary
            if tool_results:
                re_reason_prompt = f"Based on the initial query: {query}, and tool results: {tool_results}, refine the response."
                reasoning_output = await self.reasoning_engine.reason(re_reason_prompt, context)
                initial_response = reasoning_output.get("response", initial_response)

        # 5. Self-reflection and refinement
        reflection_output = await self.self_reflection.reflect_and_refine(
            {"output": initial_response, "tool_results": tool_results}, context
        )
        final_response = reflection_output.get("output", initial_response)

        # 6. Confidence Scoring
        confidence_score = await self.confidence_scoring.score(final_response, context)

        # 7. Store interaction in memory
        await self.memory_system.store_interaction(query, final_response, confidence_score)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "final_response": final_response,
            "confidence_score": confidence_score,
            "processing_time_seconds": duration,
            "timestamp": end_time.isoformat(),
            "raw_reasoning_output": reasoning_output,
            "tool_execution_results": tool_results,
            "reflection_notes": reflection_output.get("reflection_notes")
        }

    async def get_system_status(self) -> Dict[str, Any]:
        """Retrieves the current status of the integrated Maximus AI system."""
        hcl_status = await self.hcl.get_status()
        return {
            "status": "online",
            "autonomic_core_status": hcl_status,
            "memory_system_status": "operational", # Placeholder
            "tool_orchestrator_status": "operational", # Placeholder
            "last_update": datetime.now().isoformat()
        }