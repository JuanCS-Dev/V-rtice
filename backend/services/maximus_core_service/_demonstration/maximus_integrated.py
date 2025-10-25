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
from _demonstration.all_services_tools import AllServicesTools
from attention_system.attention_core import AttentionSystem
from autonomic_core.homeostatic_control import HomeostaticControlLoop
from autonomic_core.resource_analyzer import ResourceAnalyzer
from autonomic_core.resource_executor import ResourceExecutor
from autonomic_core.resource_planner import ResourcePlanner
from autonomic_core.system_monitor import SystemMonitor
from _demonstration.chain_of_thought import ChainOfThought
from confidence_scoring import ConfidenceScoring
from ethical_guardian import EthicalGuardian
from ethical_tool_wrapper import EthicalToolWrapper
from gemini_client import GeminiClient, GeminiConfig
from governance import GovernanceConfig
from memory_system import MemorySystem
from neuromodulation import NeuromodulationController
from _demonstration.rag_system import RAGSystem
from _demonstration.reasoning_engine import ReasoningEngine
from self_reflection import SelfReflection
from tool_orchestrator import ToolOrchestrator
from _demonstration.vector_db_client import VectorDBClient


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

        # Initialize Neuromodulation System (FASE 5)
        # Must be initialized BEFORE other components that depend on it
        self.neuromodulation = NeuromodulationController()

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

        # Initialize Attention System (FASE 0)
        # Modulated by Acetylcholine (salience threshold) and Norepinephrine (arousal)
        base_foveal_threshold = 0.6
        self.attention_system = AttentionSystem(
            foveal_threshold=base_foveal_threshold,
            scan_interval=1.0
        )

        # Initialize Predictive Coding Network (FASE 3)
        # Requires torch - gracefully handle if not available
        self.hpc_network = None
        self.predictive_coding_available = False
        try:
            from predictive_coding import HierarchicalPredictiveCodingNetwork
            self.hpc_network = HierarchicalPredictiveCodingNetwork(
                latent_dim=64,
                device="cpu"
            )
            self.predictive_coding_available = True
            print("🧠 [MAXIMUS] Predictive Coding Network initialized (FASE 3)")
        except ImportError as e:
            print(f"ℹ️  [MAXIMUS] Predictive Coding not available (torch required): {e}")
            print("ℹ️  [MAXIMUS] Install torch/torch_geometric for Free Energy Minimization")

        # Initialize Skill Learning System (FASE 6)
        # Client to HSAS service - gracefully handle if service not available
        self.skill_learning = None
        self.skill_learning_available = False
        try:
            from skill_learning import SkillLearningController
            self.skill_learning = SkillLearningController(
                hsas_url=os.getenv("HSAS_SERVICE_URL", "http://localhost:8023"),
                timeout=30.0
            )
            self.skill_learning_available = True
            print("🎓 [MAXIMUS] Skill Learning System initialized (FASE 6)")
        except Exception as e:
            print(f"ℹ️  [MAXIMUS] Skill Learning not available (HSAS service required): {e}")
            print("ℹ️  [MAXIMUS] Start HSAS service for skill acquisition capabilities")

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
            enable_fairness=True,  # Phase 3: Fairness & Bias Mitigation
            enable_xai=True,
            enable_privacy=True,  # Phase 4.1: Differential Privacy
            enable_fl=False,  # Phase 4.2: FL (disabled by default - optional)
            enable_hitl=True,  # Phase 5: HITL (Human-in-the-Loop)
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

        # Get neuromodulation state
        neuromod_state = self.get_neuromodulation_state()

        # Get attention system performance
        attention_stats = self.attention_system.get_performance_stats()

        return {
            "status": "online",
            "autonomic_core_status": hcl_status,
            "memory_system_status": "operational",
            "tool_orchestrator_status": "operational",
            "ethical_ai_status": {
                "guardian": ethical_stats,
                "wrapper": wrapper_stats,
                "average_overhead_ms": wrapper_stats.get("avg_overhead_ms", 0.0),
                "total_validations": ethical_stats.get("total_validations", 0),
                "approval_rate": ethical_stats.get("approval_rate", 0.0),
            },
            "neuromodulation_status": {
                "global_state": neuromod_state["global_state"],
                "modulated_parameters": neuromod_state["modulated_parameters"],
            },
            "attention_system_status": {
                "peripheral_detections": attention_stats["peripheral"]["detections_total"],
                "foveal_analyses": attention_stats["foveal"]["analyses_total"],
                "avg_analysis_time_ms": attention_stats["foveal"]["avg_analysis_time_ms"],
            },
            "predictive_coding_status": self.get_predictive_coding_state(),
            "skill_learning_status": self.get_skill_learning_state(),
            "last_update": datetime.now().isoformat(),
        }

    async def get_ethical_statistics(self) -> Dict[str, Any]:
        """Get detailed ethical AI statistics."""
        return {
            "guardian": self.ethical_guardian.get_statistics(),
            "wrapper": self.ethical_wrapper.get_statistics(),
            "timestamp": datetime.now().isoformat(),
        }

    # ============================================================================
    # NEUROMODULATION INTEGRATION (FASE 5)
    # ============================================================================

    def get_neuromodulated_parameters(self) -> Dict[str, Any]:
        """Get all neuromodulated parameters for adaptive behavior.

        Returns modulation values for:
        - Learning rate (Dopamine): for HCL/RL agent
        - Attention threshold (Acetylcholine): for AttentionSystem salience
        - Arousal gain (Norepinephrine): for threat response amplification
        - Exploration temperature (Serotonin): for ReasoningEngine
        """
        # Base parameters
        base_learning_rate = 0.01
        base_foveal_threshold = 0.6
        base_temperature = 0.7

        # Get modulated values
        modulated_lr = self.neuromodulation.get_modulated_learning_rate(base_learning_rate)
        exploration_rate = self.neuromodulation.serotonin.get_exploration_rate()
        attention_gain = self.neuromodulation.norepinephrine.get_attention_gain()
        salience_threshold = self.neuromodulation.acetylcholine.get_salience_threshold()

        # Convert exploration rate to temperature (inverse relationship)
        # High exploration → high temperature (more randomness)
        # Serotonin exploration_rate is in [0.05, 0.3]
        # Map to temperature [0.3, 1.0]
        modulated_temperature = 0.3 + (exploration_rate / 0.3) * 0.7

        # Adjust attention threshold based on ACh salience threshold
        # High ACh → lower threshold (attend to more)
        # salience_threshold is typically [0.3, 0.7]
        # Map to foveal_threshold [0.4, 0.8] (inverted)
        modulated_attention_threshold = 0.8 - (salience_threshold - 0.3) * (0.4 / 0.4)

        return {
            "learning_rate": modulated_lr,
            "attention_threshold": modulated_attention_threshold,
            "arousal_gain": attention_gain,
            "temperature": modulated_temperature,
            "raw_neuromodulation": {
                "dopamine_level": self.neuromodulation.dopamine.level,
                "serotonin_level": self.neuromodulation.serotonin.level,
                "norepinephrine_level": self.neuromodulation.norepinephrine.level,
                "acetylcholine_level": self.neuromodulation.acetylcholine.level,
                "exploration_rate": exploration_rate,
                "salience_threshold": salience_threshold,
            },
        }

    async def process_outcome(
        self, expected_reward: float, actual_reward: float, success: bool
    ) -> Dict[str, Any]:
        """Process task outcome through neuromodulation system.

        Updates dopamine (RPE) and serotonin (mood) based on results.

        Args:
            expected_reward: Expected reward/quality (0-1)
            actual_reward: Actual reward/quality (0-1)
            success: Whether the task succeeded

        Returns:
            Dict with RPE, motivation, and updated neuromodulation state
        """
        result = self.neuromodulation.process_reward(
            expected_reward=expected_reward,
            actual_reward=actual_reward,
            success=success,
        )

        # Get updated parameters after processing outcome
        updated_params = self.get_neuromodulated_parameters()
        result["updated_parameters"] = updated_params

        return result

    async def respond_to_threat(
        self, threat_severity: float, threat_type: str = "unknown"
    ) -> Dict[str, Any]:
        """Respond to detected threats through neuromodulation.

        Activates norepinephrine system to increase arousal and attention.

        Args:
            threat_severity: Severity of threat (0-1)
            threat_type: Type of threat (e.g., 'intrusion', 'anomaly')

        Returns:
            Dict with arousal level and attention gain
        """
        # Activate norepinephrine response
        self.neuromodulation.respond_to_threat(threat_severity)

        # Get updated arousal and attention
        arousal_level = self.neuromodulation.norepinephrine.get_arousal_level()
        attention_gain = self.neuromodulation.norepinephrine.get_attention_gain()

        # Update attention system threshold based on arousal
        updated_params = self.get_neuromodulated_parameters()
        self.attention_system.salience_scorer.foveal_threshold = updated_params[
            "attention_threshold"
        ]

        return {
            "threat_severity": threat_severity,
            "threat_type": threat_type,
            "arousal_level": arousal_level,
            "attention_gain": attention_gain,
            "updated_attention_threshold": updated_params["attention_threshold"],
        }

    def get_neuromodulation_state(self) -> Dict[str, Any]:
        """Get current neuromodulation state and global modulation parameters."""
        global_state = self.neuromodulation.get_global_state()
        modulated_params = self.get_neuromodulated_parameters()

        return {
            "global_state": {
                "dopamine": global_state.dopamine,
                "serotonin": global_state.serotonin,
                "norepinephrine": global_state.norepinephrine,
                "acetylcholine": global_state.acetylcholine,
                "overall_mood": global_state.overall_mood,
                "cognitive_load": global_state.cognitive_load,
            },
            "modulated_parameters": modulated_params,
            "timestamp": datetime.now().isoformat(),
        }

    # ============================================================================
    # PREDICTIVE CODING INTEGRATION (FASE 3)
    # ============================================================================

    def predict_with_hpc_network(
        self, raw_event: Any, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform hierarchical prediction using HPC Network.

        Implements Free Energy Minimization principle:
        - Layer 1 (Sensory): Compresses raw event (VAE)
        - Layer 2 (Behavioral): Predicts process patterns (GNN)
        - Layer 3 (Operational): Predicts threats (TCN)
        - Layer 4 (Tactical): Predicts campaigns (LSTM)
        - Layer 5 (Strategic): Predicts threat landscape (Transformer)

        Args:
            raw_event: Raw event vector (numpy array or tensor)
            context: Additional context (event graphs, sequences)

        Returns:
            Dict with predictions from all layers + free energy

        Note: Requires torch. Returns gracefully if not available.
        """
        if not self.predictive_coding_available:
            return {
                "available": False,
                "message": "Predictive Coding requires torch/torch_geometric",
                "predictions": None,
                "free_energy": None,
            }

        try:
            # Extract context
            event_graph = context.get("event_graph") if context else None
            l2_sequence = context.get("l2_sequence") if context else None
            l3_sequence = context.get("l3_sequence") if context else None
            l4_sequence = context.get("l4_sequence") if context else None

            # Hierarchical inference through all layers
            predictions = self.hpc_network.hierarchical_inference(
                raw_event=raw_event,
                event_graph=event_graph,
                l2_sequence=l2_sequence,
                l3_sequence=l3_sequence,
                l4_sequence=l4_sequence,
            )

            # Compute Free Energy (prediction error)
            ground_truth = context.get("ground_truth") if context else None
            free_energy = self.hpc_network.compute_free_energy(
                predictions=predictions,
                ground_truth=ground_truth
            )

            return {
                "available": True,
                "predictions": predictions,
                "free_energy": free_energy,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "error": str(e),
                "predictions": None,
                "free_energy": None,
            }

    async def process_prediction_error(
        self, prediction_error: float, layer: str = "l1"
    ) -> Dict[str, Any]:
        """Process prediction error from Predictive Coding Network.

        Connects Free Energy Minimization with:
        - Neuromodulation: High prediction error → dopamine RPE → learning rate ↑
        - Attention: Unexpected events → salience ↑
        - HCL: Prediction errors guide action selection

        Args:
            prediction_error: Free Energy value (0-1, higher = more surprise)
            layer: Which layer generated the error (l1-l5)

        Returns:
            Dict with updated system state
        """
        # Map prediction error to RPE (treat as negative surprise)
        # High prediction error = unexpected = high surprise
        rpe = prediction_error  # Positive values indicate surprise

        # Update dopamine based on prediction error magnitude
        # This increases learning rate for surprising events
        modulated_lr = self.neuromodulation.dopamine.modulate_learning_rate(
            base_learning_rate=0.01,
            rpe=rpe
        )

        # If prediction error is high, increase attention
        if prediction_error > 0.5:  # High surprise
            # Increase acetylcholine (important event)
            self.neuromodulation.acetylcholine.modulate_attention(
                importance=prediction_error
            )

            # Update attention threshold
            updated_params = self.get_neuromodulated_parameters()
            self.attention_system.salience_scorer.foveal_threshold = updated_params[
                "attention_threshold"
            ]

        return {
            "prediction_error": prediction_error,
            "layer": layer,
            "rpe_signal": rpe,
            "modulated_learning_rate": modulated_lr,
            "attention_updated": prediction_error > 0.5,
            "timestamp": datetime.now().isoformat(),
        }

    def get_predictive_coding_state(self) -> Dict[str, Any]:
        """Get current Predictive Coding Network state.

        Returns:
            Dict with HPC network status and prediction buffers
        """
        if not self.predictive_coding_available:
            return {
                "available": False,
                "message": "Predictive Coding requires torch/torch_geometric",
            }

        try:
            # Get prediction error history from HPC network
            prediction_errors = self.hpc_network.prediction_errors

            return {
                "available": True,
                "latent_dim": self.hpc_network.latent_dim,
                "device": self.hpc_network.device,
                "prediction_errors": {
                    "l1": len(prediction_errors.get("l1", [])),
                    "l2": len(prediction_errors.get("l2", [])),
                    "l3": len(prediction_errors.get("l3", [])),
                    "l4": len(prediction_errors.get("l4", [])),
                    "l5": len(prediction_errors.get("l5", [])),
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "error": str(e),
            }

    # ========================================================================
    # SKILL LEARNING INTEGRATION (FASE 6)
    # ========================================================================

    async def execute_learned_skill(
        self,
        skill_name: str,
        context: Dict[str, Any],
        mode: str = "hybrid",
    ) -> Dict[str, Any]:
        """Execute a learned skill via HSAS service.

        Args:
            skill_name: Name of skill to execute
            context: Execution context (state, parameters)
            mode: Execution mode (model_free/model_based/hybrid)

        Returns:
            Execution result with success, reward, and neuromodulation updates

        Integration Points:
        - Dopamine: Skill reward → RPE → Learning rate modulation
        - Predictive Coding: Skill outcome vs prediction → Free Energy
        - HCL: Skill execution affects system state
        """
        if not self.skill_learning_available:
            return {
                "available": False,
                "message": "Skill Learning requires HSAS service (port 8023)",
                "success": False,
            }

        try:
            # Execute skill via HSAS service
            result = await self.skill_learning.execute_skill(
                skill_name=skill_name,
                context=context,
                mode=mode
            )

            # Compute RPE from skill execution
            # Positive reward = positive RPE (better than expected)
            # Negative reward = negative RPE (worse than expected)
            rpe = result.total_reward

            # Update dopamine based on skill execution reward
            modulated_lr = self.neuromodulation.dopamine.modulate_learning_rate(
                base_learning_rate=0.01,
                rpe=rpe
            )

            # If skill failed, increase norepinephrine (error signal)
            if not result.success:
                self.neuromodulation.norepinephrine.process_error_signal(
                    error_magnitude=abs(rpe),
                    requires_vigilance=True
                )

            # Connect to Predictive Coding if available
            if self.predictive_coding_available and "outcome" in context:
                # Skill outcome can be compared to prediction
                prediction_error = abs(result.total_reward - context.get("expected_reward", 0.0))

                # Process via Predictive Coding
                await self.process_prediction_error(
                    prediction_error=prediction_error,
                    layer="l4"  # Tactical layer (skill execution timescale)
                )

            return {
                "available": True,
                "skill_name": skill_name,
                "success": result.success,
                "steps_executed": result.steps_executed,
                "total_reward": result.total_reward,
                "execution_time": result.execution_time,
                "errors": result.errors,
                "neuromodulation": {
                    "rpe": rpe,
                    "modulated_learning_rate": modulated_lr,
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "success": False,
                "error": str(e),
            }

    async def learn_skill_from_demonstration(
        self,
        skill_name: str,
        demonstration: list,
        expert_name: str = "human"
    ) -> Dict[str, Any]:
        """Learn new skill from expert demonstration (imitation learning).

        Args:
            skill_name: Name for new skill
            demonstration: List of (state, action) pairs
            expert_name: Name of expert demonstrator

        Returns:
            Learning result

        Implements:
        - Imitation Learning via HSAS service
        - Dopamine boost for successful learning (intrinsic reward)
        - Memory consolidation of new skill
        """
        if not self.skill_learning_available:
            return {
                "available": False,
                "message": "Skill Learning requires HSAS service (port 8023)",
                "success": False,
            }

        try:
            # Learn from demonstration via HSAS
            success = await self.skill_learning.learn_from_demonstration(
                skill_name=skill_name,
                demonstration=demonstration,
                expert_name=expert_name
            )

            if success:
                # Intrinsic reward for learning new skill (dopamine boost)
                intrinsic_reward = 1.0
                self.neuromodulation.dopamine.modulate_learning_rate(
                    base_learning_rate=0.01,
                    rpe=intrinsic_reward  # Positive RPE for learning
                )

                # Store skill in memory system
                await self.memory_system.store_memory(
                    memory_type="skill",
                    content=f"Learned skill: {skill_name} from {expert_name}",
                    metadata={
                        "skill_name": skill_name,
                        "expert": expert_name,
                        "demonstration_steps": len(demonstration),
                    }
                )

            return {
                "available": True,
                "success": success,
                "skill_name": skill_name,
                "expert": expert_name,
                "demonstration_steps": len(demonstration),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "success": False,
                "error": str(e),
            }

    async def compose_skill_from_primitives(
        self,
        skill_name: str,
        primitive_sequence: list,
        description: str = ""
    ) -> Dict[str, Any]:
        """Compose new skill from sequence of primitives.

        Args:
            skill_name: Name for composed skill
            primitive_sequence: List of primitive skill names
            description: Skill description

        Returns:
            Composition result

        Implements:
        - Hierarchical skill composition
        - Creativity bonus (serotonin for novel compositions)
        - Memory consolidation of composed skill
        """
        if not self.skill_learning_available:
            return {
                "available": False,
                "message": "Skill Learning requires HSAS service (port 8023)",
                "success": False,
            }

        try:
            # Compose skill via HSAS
            success = await self.skill_learning.compose_skill(
                skill_name=skill_name,
                primitive_sequence=primitive_sequence,
                description=description
            )

            if success:
                # Creativity bonus (serotonin for novel behavior)
                # More primitives = more creative composition
                creativity_score = min(len(primitive_sequence) / 10.0, 1.0)
                self.neuromodulation.serotonin.process_system_stability(
                    stability_metrics={
                        "creativity": creativity_score,
                        "novel_composition": True
                    }
                )

                # Store composed skill in memory
                await self.memory_system.store_memory(
                    memory_type="skill",
                    content=f"Composed skill: {skill_name}",
                    metadata={
                        "skill_name": skill_name,
                        "primitives": primitive_sequence,
                        "description": description,
                    }
                )

            return {
                "available": True,
                "success": success,
                "skill_name": skill_name,
                "primitives": primitive_sequence,
                "creativity_score": creativity_score if success else 0.0,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "success": False,
                "error": str(e),
            }

    def get_skill_learning_state(self) -> Dict[str, Any]:
        """Get current Skill Learning system state.

        Returns:
            Dict with skill library, statistics, and HSAS service status
        """
        if not self.skill_learning_available:
            return {
                "available": False,
                "message": "Skill Learning requires HSAS service (port 8023)",
            }

        try:
            # Get state from controller
            state = self.skill_learning.export_state()

            return {
                "available": True,
                "hsas_service_url": state["hsas_url"],
                "learned_skills_count": state["learned_skills_count"],
                "cached_skills": state["cached_skills"],
                "skill_statistics": state["skill_stats"],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "error": str(e),
            }
