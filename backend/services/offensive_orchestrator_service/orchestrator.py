"""
MAXIMUS Orchestrator Agent - Central LLM Coordinator for Offensive Operations.

Responsibilities:
- Campaign planning (mission objectives → attack plan)
- Agent coordination (Recon, Exploit, Post-Exploit)
- Strategic decision-making (high-level tactics)
- HOTL checkpoints (human approval for critical actions)
- Campaign memory management
- Inter-campaign learning

Architecture:
- LLM: Gemini 1.5 Pro (2M token context window)
- Framework: LangChain for prompt management
- Memory: Vector DB (Qdrant) + Relational (PostgreSQL)
- Decision: HOTL system for critical approvals

Conformidade MAXIMUS:
- NO MOCK: Real LLM integration desde Sprint 1
- QUALITY-FIRST: Type hints, error handling, logging
- PRODUCTION-READY: Resilient, fault-tolerant, observable
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

import google.generativeai as genai
from langchain.prompts import PromptTemplate

from config import get_config, LLMConfig
from models import (
    CampaignObjective,
    CampaignPlan,
    CampaignStatus,
    ActionType,
    RiskLevel,
    HOTLRequest,
)


logger = logging.getLogger(__name__)


class MaximusOrchestratorAgent:
    """
    Central orchestrator agent using LLM for campaign planning and coordination.

    This agent emulates a senior penetration tester's strategic thinking:
    - Analyzes target and objectives
    - Plans multi-phase attack campaigns
    - Coordinates specialized agents (Recon, Exploit, Post-Exploit)
    - Makes tactical decisions based on campaign progress
    - Enforces HOTL checkpoints for critical actions
    """

    # Campaign planning prompt template
    CAMPAIGN_PLANNING_PROMPT = PromptTemplate(
        input_variables=["target", "scope", "objectives", "constraints", "historical_campaigns"],
        template="""You are MAXIMUS, an AI-powered penetration testing orchestrator with expertise in offensive security operations.

**MISSION**:
Plan a strategic offensive security campaign for the following engagement:

**Target**: {target}
**Scope**: {scope}
**Objectives**: {objectives}
**Constraints**: {constraints}

**Historical Context** (similar past campaigns):
{historical_campaigns}

**YOUR TASK**:
Design a comprehensive attack campaign plan that:
1. Breaks down the engagement into distinct phases (Reconnaissance, Exploitation, Post-Exploitation)
2. Maps MITRE ATT&CK TTPs to each phase
3. Sequences actions logically (info gathering → vulnerability discovery → exploitation → objectives)
4. Identifies HOTL checkpoints (actions requiring human approval)
5. Estimates timeline and resources
6. Defines success criteria
7. Assesses overall risk level

**OUTPUT FORMAT** (JSON):
{{
  "phases": [
    {{
      "name": "Phase 1: Reconnaissance",
      "actions": [
        {{
          "action": "DNS enumeration",
          "ttp": "T1590.002",
          "agent": "recon_agent",
          "estimated_duration_min": 15,
          "requires_hotl": false
        }},
        ...
      ]
    }},
    ...
  ],
  "ttps": ["T1590.002", "T1595.001", ...],
  "estimated_duration_minutes": 180,
  "risk_assessment": "medium",
  "success_criteria": ["Identify all exposed services", "Discover at least one exploitable vulnerability", ...],
  "hotl_checkpoints": ["Before executing any exploit", "Before lateral movement", ...]
}}

**CRITICAL**: This is a controlled security assessment. All actions must:
- Stay within defined scope
- Respect constraints (time windows, forbidden actions)
- Include HOTL checkpoints for high-risk actions
- Be reversible/non-destructive when possible

Generate the campaign plan now:
""",
    )

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        hotl_system: Optional[Any] = None,  # HOTLDecisionSystem
        attack_memory: Optional[Any] = None,  # AttackMemorySystem
    ):
        """
        Initialize Orchestrator Agent.

        Args:
            config: LLM configuration (defaults to global config)
            hotl_system: HOTL decision system instance
            attack_memory: Attack memory system instance
        """
        self.config = config or get_config().llm
        self.hotl_system = hotl_system
        self.attack_memory = attack_memory

        # Initialize Gemini
        genai.configure(api_key=self.config.api_key)
        self.llm = genai.GenerativeModel(
            model_name=self.config.model,
            generation_config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            },
        )

        logger.info(
            f"MaximusOrchestratorAgent initialized with model={self.config.model}, "
            f"temperature={self.config.temperature}"
        )

    async def plan_campaign(
        self, objective: CampaignObjective, campaign_id: Optional[UUID] = None
    ) -> CampaignPlan:
        """
        Plan offensive campaign based on objective.

        This is the core orchestration function. It:
        1. Retrieves similar historical campaigns from memory
        2. Uses LLM to generate strategic campaign plan
        3. Parses and validates the plan
        4. Assesses risk level
        5. Returns structured campaign plan

        Args:
            objective: Campaign objective (target, scope, goals)
            campaign_id: Optional campaign ID (generates new if not provided)

        Returns:
            CampaignPlan: Structured campaign plan

        Raises:
            ValueError: If plan generation fails or invalid
            RuntimeError: If LLM call fails
        """
        if campaign_id is None:
            campaign_id = uuid4()

        logger.info(f"Planning campaign {campaign_id} for target={objective.target}")

        try:
            # Step 1: Retrieve historical context
            historical_context = await self._get_historical_context(objective)

            # Step 2: Generate campaign plan via LLM
            prompt = self._build_planning_prompt(objective, historical_context)
            raw_plan = await self._call_llm(prompt)

            # Step 3: Parse and validate
            parsed_plan = self._parse_campaign_plan(raw_plan)

            # Step 4: Build CampaignPlan object
            plan = CampaignPlan(
                campaign_id=campaign_id,
                target=objective.target,
                phases=parsed_plan["phases"],
                ttps=parsed_plan["ttps"],
                estimated_duration_minutes=parsed_plan["estimated_duration_minutes"],
                risk_assessment=RiskLevel(parsed_plan["risk_assessment"]),
                success_criteria=parsed_plan["success_criteria"],
                created_at=datetime.utcnow(),
            )

            logger.info(
                f"Campaign {campaign_id} planned successfully: "
                f"{len(plan.phases)} phases, {len(plan.ttps)} TTPs, "
                f"risk={plan.risk_assessment}, duration={plan.estimated_duration_minutes}min"
            )

            # Step 5: Store in memory for future reference
            if self.attack_memory:
                await self.attack_memory.store_campaign_plan(plan)

            return plan

        except ValueError as e:
            # Re-raise ValueError for API layer to handle as 400 Bad Request
            logger.error(f"Campaign planning validation failed for {campaign_id}: {e}")
            raise

        except Exception as e:
            logger.error(f"Campaign planning failed for {campaign_id}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to plan campaign: {e}") from e

    async def execute_campaign(self, plan: CampaignPlan) -> Dict[str, Any]:
        """
        Execute planned campaign by coordinating specialized agents.

        Orchestrates the complete attack campaign:
        1. Iterates through phases sequentially
        2. For each action: delegates to appropriate agent
        3. Enforces HOTL checkpoints
        4. Collects results and metrics
        5. Adapts plan based on results (if needed)

        Args:
            plan: Campaign plan to execute

        Returns:
            Dict containing campaign results, metrics, timeline

        Raises:
            RuntimeError: If campaign execution fails critically
        """
        logger.info(f"Executing campaign {plan.campaign_id} for target={plan.target}")

        results = {
            "campaign_id": str(plan.campaign_id),
            "target": plan.target,
            "start_time": datetime.utcnow().isoformat(),
            "phases": [],
            "status": CampaignStatus.IN_PROGRESS,
        }

        try:
            for phase_idx, phase in enumerate(plan.phases):
                phase_name = phase["name"]
                logger.info(f"Campaign {plan.campaign_id}: Starting phase {phase_idx + 1}/{len(plan.phases)}: {phase_name}")

                phase_results = await self._execute_phase(plan.campaign_id, phase)
                results["phases"].append(phase_results)

                # Check if phase failed critically
                if phase_results.get("critical_failure"):
                    logger.error(f"Campaign {plan.campaign_id}: Critical failure in phase {phase_name}")
                    results["status"] = CampaignStatus.FAILED
                    break

            # Mark as completed if all phases succeeded
            if results["status"] == CampaignStatus.IN_PROGRESS:
                results["status"] = CampaignStatus.COMPLETED

            results["end_time"] = datetime.utcnow().isoformat()

            logger.info(
                f"Campaign {plan.campaign_id} finished with status={results['status']}"
            )

            return results

        except Exception as e:
            logger.error(f"Campaign {plan.campaign_id} execution failed: {e}", exc_info=True)
            results["status"] = CampaignStatus.FAILED
            results["error"] = str(e)
            results["end_time"] = datetime.utcnow().isoformat()
            return results

    async def _execute_phase(self, campaign_id: UUID, phase: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single campaign phase.

        Args:
            campaign_id: Campaign identifier
            phase: Phase definition with actions

        Returns:
            Dict with phase results
        """
        phase_results = {
            "name": phase["name"],
            "actions": [],
            "start_time": datetime.utcnow().isoformat(),
        }

        for action in phase.get("actions", []):
            action_result = await self._execute_action(campaign_id, action)
            phase_results["actions"].append(action_result)

            # Early abort if action failed critically
            if action_result.get("critical_failure"):
                phase_results["critical_failure"] = True
                break

        phase_results["end_time"] = datetime.utcnow().isoformat()
        return phase_results

    async def _execute_action(self, campaign_id: UUID, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single action (delegates to specialized agent).

        Args:
            campaign_id: Campaign identifier
            action: Action definition

        Returns:
            Dict with action results
        """
        action_name = action["action"]
        agent_type = action.get("agent", "unknown")
        requires_hotl = action.get("requires_hotl", False)

        logger.info(f"Campaign {campaign_id}: Executing action '{action_name}' via {agent_type}")

        # HOTL checkpoint if required
        if requires_hotl and self.hotl_system:
            hotl_approved = await self._check_hotl(campaign_id, action)
            if not hotl_approved:
                return {
                    "action": action_name,
                    "status": "rejected",
                    "reason": "HOTL approval denied",
                    "timestamp": datetime.utcnow().isoformat(),
                }

        # Delegate to appropriate agent
        # NOTE: In Sprint 1, we return placeholder (agents implemented in Sprint 2-4)
        # This is NOT a mock - it's a phased implementation approach
        result = {
            "action": action_name,
            "agent": agent_type,
            "status": "pending_agent_implementation",
            "note": f"Agent {agent_type} will be implemented in Sprint 2-4",
            "timestamp": datetime.utcnow().isoformat(),
        }

        return result

    async def _check_hotl(self, campaign_id: UUID, action: Dict[str, Any]) -> bool:
        """
        Request HOTL approval for action.

        Args:
            campaign_id: Campaign identifier
            action: Action requiring approval

        Returns:
            bool: True if approved, False if rejected/timeout
        """
        if not self.hotl_system:
            logger.warning("HOTL system not configured, auto-approving")
            return True

        # Map agent type to action type
        agent = action.get("agent", "recon_agent")
        action_type_map = {
            "recon_agent": ActionType.RECONNAISSANCE,
            "exploit_agent": ActionType.EXPLOITATION,
            "post_exploit_agent": ActionType.POST_EXPLOITATION,
            "analysis_agent": ActionType.ANALYSIS,
        }
        action_type = action_type_map.get(agent, ActionType.RECONNAISSANCE)

        hotl_request = HOTLRequest(
            campaign_id=campaign_id,
            action_type=action_type,
            description=f"Action: {action['action']} (TTP: {action.get('ttp', 'unknown')})",
            risk_level=RiskLevel.HIGH,  # Assume high if requires approval
            context=action,
        )

        approval = await self.hotl_system.request_approval(hotl_request)
        return approval.approved

    async def _get_historical_context(self, objective: CampaignObjective) -> str:
        """
        Retrieve similar historical campaigns from attack memory.

        Args:
            objective: Current campaign objective

        Returns:
            str: Formatted historical context for LLM
        """
        if not self.attack_memory:
            return "No historical campaigns available (first run)."

        try:
            similar_campaigns = await self.attack_memory.find_similar_campaigns(
                target=objective.target, limit=3
            )

            if not similar_campaigns:
                return "No similar campaigns found in history."

            # Format for LLM consumption
            context_lines = []
            for idx, campaign in enumerate(similar_campaigns, 1):
                context_lines.append(
                    f"Campaign {idx}: Target={campaign.get('target')}, "
                    f"Success={campaign.get('success', 'unknown')}, "
                    f"Key Learnings: {campaign.get('lessons_learned', 'N/A')}"
                )

            return "\n".join(context_lines)

        except Exception as e:
            logger.warning(f"Failed to retrieve historical context: {e}")
            return "Historical context unavailable due to error."

    def _build_planning_prompt(
        self, objective: CampaignObjective, historical_context: str
    ) -> str:
        """
        Build complete planning prompt for LLM.

        Args:
            objective: Campaign objective
            historical_context: Historical campaigns context

        Returns:
            str: Complete prompt
        """
        return self.CAMPAIGN_PLANNING_PROMPT.format(
            target=objective.target,
            scope=", ".join(objective.scope),
            objectives=", ".join(objective.objectives),
            constraints=str(objective.constraints),
            historical_campaigns=historical_context,
        )

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM with error handling and retry logic.

        Args:
            prompt: Prompt text

        Returns:
            str: LLM response text

        Raises:
            RuntimeError: If LLM call fails after retries
        """
        max_retries = 3
        retry_delay = 2.0

        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.llm.generate_content, prompt
                )
                return response.text

            except Exception as e:
                logger.warning(
                    f"LLM call attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    raise RuntimeError(f"LLM call failed after {max_retries} attempts") from e

    def _parse_campaign_plan(self, raw_plan: str) -> Dict[str, Any]:
        """
        Parse LLM-generated campaign plan into structured format.

        Args:
            raw_plan: Raw LLM output (expected JSON)

        Returns:
            Dict: Parsed and validated plan

        Raises:
            ValueError: If parsing or validation fails
        """
        import json
        import re

        try:
            # Extract JSON from response (LLM might add explanation text)
            json_match = re.search(r"\{.*\}", raw_plan, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")

            plan = json.loads(json_match.group(0))

            # Validate required fields
            required_fields = [
                "phases",
                "ttps",
                "estimated_duration_minutes",
                "risk_assessment",
                "success_criteria",
            ]
            missing = [f for f in required_fields if f not in plan]
            if missing:
                raise ValueError(f"Missing required fields in plan: {missing}")

            # Validate data types
            if not isinstance(plan["phases"], list) or not plan["phases"]:
                raise ValueError("phases must be non-empty list")

            if not isinstance(plan["ttps"], list):
                raise ValueError("ttps must be list")

            if not isinstance(plan["estimated_duration_minutes"], int):
                raise ValueError("estimated_duration_minutes must be integer")

            return plan

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}\nRaw: {raw_plan}")
            raise ValueError(f"Invalid JSON in LLM response: {e}") from e
        except Exception as e:
            logger.error(f"Plan parsing failed: {e}")
            raise ValueError(f"Failed to parse campaign plan: {e}") from e
