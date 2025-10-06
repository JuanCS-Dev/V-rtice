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
from datetime import datetime
import os
from typing import Any, Dict, Optional

from agent_templates import AgentTemplates
from all_services_tools import AllServicesTools
from autonomic_core.homeostatic_control import HomeostaticControlLoop
from autonomic_core.resource_analyzer import ResourceAnalyzer
from autonomic_core.resource_executor import ResourceExecutor
from autonomic_core.resource_planner import ResourcePlanner
from autonomic_core.system_monitor import SystemMonitor
from chain_of_thought import ChainOfThought
from confidence_scoring import ConfidenceScoring
from ethical_guardian import EthicalGuardian
from ethical_tool_wrapper import EthicalToolWrapper
from gemini_client import GeminiClient, GeminiConfig
from governance import GovernanceConfig
from memory_system import MemorySystem
from rag_system import RAGSystem
from reasoning_engine import ReasoningEngine
from self_reflection import SelfReflection
from tool_orchestrator import ToolOrchestrator
from vector_db_client import VectorDBClient


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
            timeout=60,
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
            executor=self.resource_executor,
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

        # Initialize Ethical AI Stack
        self.governance_config = GovernanceConfig()
        self.ethical_guardian = EthicalGuardian(
            governance_config=self.governance_config,
            enable_governance=True,
            enable_ethics=True,
            enable_xai=True,
            enable_compliance=True,
        )
        self.ethical_wrapper = EthicalToolWrapper(
            ethical_guardian=self.ethical_guardian,
            enable_pre_check=True,
            enable_post_check=True,
            enable_audit=True,
        )

        # Inject ethical wrapper into tool orchestrator
        self.tool_orchestrator.set_ethical_wrapper(self.ethical_wrapper)

    async def start_autonomic_core(self):
        """Starts the Homeostatic Control Loop (HCL) for autonomic management."""
        await self.hcl.start()

    async def stop_autonomic_core(self):
        """Stops the Homeostatic Control Loop (HCL)."""
        await self.hcl.stop()

    async def process_query(
        self, query: str, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
        context = {
            "query": query,
            "user_context": user_context,
            "retrieved_docs": retrieved_docs,
        }

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
                reasoning_output = await self.reasoning_engine.reason(
                    re_reason_prompt, context
                )
                initial_response = reasoning_output.get("response", initial_response)

        # 5. Self-reflection and refinement
        reflection_output = await self.self_reflection.reflect_and_refine(
            {"output": initial_response, "tool_results": tool_results}, context
        )
        final_response = reflection_output.get("output", initial_response)

        # 6. Confidence Scoring
        confidence_score = await self.confidence_scoring.score(final_response, context)

        # 7. Store interaction in memory
        await self.memory_system.store_interaction(
            query, final_response, confidence_score
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "final_response": final_response,
            "confidence_score": confidence_score,
            "processing_time_seconds": duration,
            "timestamp": end_time.isoformat(),
            "raw_reasoning_output": reasoning_output,
            "tool_execution_results": tool_results,
            "reflection_notes": reflection_output.get("reflection_notes"),
        }

    async def get_system_status(self) -> Dict[str, Any]:
        """Retrieves the current status of the integrated Maximus AI system."""
        hcl_status = await self.hcl.get_status()

        # Get ethical AI statistics
        ethical_stats = self.ethical_guardian.get_statistics()
        wrapper_stats = self.ethical_wrapper.get_statistics()

        return {
            "status": "online",
            "autonomic_core_status": hcl_status,
            "memory_system_status": "operational",  # Placeholder
            "tool_orchestrator_status": "operational",  # Placeholder
            "ethical_ai_status": {
                "guardian": ethical_stats,
                "wrapper": wrapper_stats,
                "average_overhead_ms": wrapper_stats.get("avg_overhead_ms", 0.0),
                "total_validations": ethical_stats.get("total_validations", 0),
                "approval_rate": ethical_stats.get("approval_rate", 0.0),
            },
            "last_update": datetime.now().isoformat(),
        }

    async def get_ethical_statistics(self) -> Dict[str, Any]:
        """Get detailed ethical AI statistics."""
        return {
            "guardian": self.ethical_guardian.get_statistics(),
            "wrapper": self.ethical_wrapper.get_statistics(),
            "timestamp": datetime.now().isoformat(),
        }
