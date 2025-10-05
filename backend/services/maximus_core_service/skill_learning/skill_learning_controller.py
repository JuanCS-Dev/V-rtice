"""Skill Learning Controller - Integration with HSAS Service.

This controller provides a lightweight interface to the full HSAS (Hybrid Skill
Acquisition System) service, enabling skill learning within Maximus Core.

Production-ready implementation with real HSAS integration.
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SkillExecutionResult:
    """Result of skill execution."""
    skill_name: str
    success: bool
    steps_executed: int
    total_reward: float
    execution_time: float
    errors: List[str]
    timestamp: datetime


class SkillLearningController:
    """Controller for skill learning via HSAS service integration.

    Provides:
    - Execute learned skills
    - Learn new skills from demonstrations
    - Compose skills from primitives
    - Track skill performance
    - Integration with neuromodulation (dopamine for RPE)

    This is a lightweight proxy to the full HSAS service (port 8023).
    """

    def __init__(
        self,
        hsas_url: str = "http://localhost:8023",
        timeout: float = 30.0
    ):
        """Initialize skill learning controller.

        Args:
            hsas_url: URL of HSAS service
            timeout: HTTP timeout in seconds
        """
        self.hsas_url = hsas_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

        # Local cache
        self.learned_skills: Dict[str, Any] = {}
        self.skill_stats: Dict[str, Dict] = {}

        logger.info(f"Skill learning controller initialized (HSAS: {hsas_url})")

    async def execute_skill(
        self,
        skill_name: str,
        context: Dict[str, Any],
        mode: str = "hybrid"  # model_free, model_based, hybrid
    ) -> SkillExecutionResult:
        """Execute a learned skill.

        Args:
            skill_name: Name of skill to execute
            context: Execution context (state, parameters)
            mode: Execution mode (model_free/model_based/hybrid)

        Returns:
            Execution result
        """
        start_time = datetime.utcnow()

        try:
            # Call HSAS service
            response = await self.client.post(
                f"{self.hsas_url}/api/execute_skill",
                json={
                    "skill_name": skill_name,
                    "context": context,
                    "mode": mode
                }
            )
            response.raise_for_status()

            result_data = response.json()

            # Track statistics
            self._update_skill_stats(skill_name, success=result_data.get("success", False))

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = SkillExecutionResult(
                skill_name=skill_name,
                success=result_data.get("success", False),
                steps_executed=result_data.get("steps", 0),
                total_reward=result_data.get("reward", 0.0),
                execution_time=execution_time,
                errors=result_data.get("errors", []),
                timestamp=datetime.utcnow()
            )

            logger.info(f"Skill executed: {skill_name}, success={result.success}, "
                       f"reward={result.total_reward:.2f}, time={execution_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"Skill execution failed: {skill_name}, error={str(e)}")

            return SkillExecutionResult(
                skill_name=skill_name,
                success=False,
                steps_executed=0,
                total_reward=0.0,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                errors=[str(e)],
                timestamp=datetime.utcnow()
            )

    async def learn_from_demonstration(
        self,
        skill_name: str,
        demonstration: List[Dict],
        expert_name: str = "human"
    ) -> bool:
        """Learn skill from expert demonstration (imitation learning).

        Args:
            skill_name: Name for new skill
            demonstration: List of (state, action) pairs
            expert_name: Name of expert

        Returns:
            True if learning succeeded
        """
        try:
            response = await self.client.post(
                f"{self.hsas_url}/api/learn_from_demo",
                json={
                    "skill_name": skill_name,
                    "demonstration": demonstration,
                    "expert": expert_name
                }
            )
            response.raise_for_status()

            logger.info(f"Skill learned from demonstration: {skill_name} (expert: {expert_name})")

            # Cache locally
            self.learned_skills[skill_name] = {
                "source": "demonstration",
                "expert": expert_name,
                "learned_at": datetime.utcnow().isoformat()
            }

            return True

        except Exception as e:
            logger.error(f"Learning from demonstration failed: {str(e)}")
            return False

    async def compose_skill(
        self,
        skill_name: str,
        primitive_sequence: List[str],
        description: str = ""
    ) -> bool:
        """Compose new skill from sequence of primitives.

        Args:
            skill_name: Name for composed skill
            primitive_sequence: List of primitive names
            description: Skill description

        Returns:
            True if composition succeeded
        """
        try:
            response = await self.client.post(
                f"{self.hsas_url}/api/compose_skill",
                json={
                    "skill_name": skill_name,
                    "primitives": primitive_sequence,
                    "description": description
                }
            )
            response.raise_for_status()

            logger.info(f"Skill composed: {skill_name} from {len(primitive_sequence)} primitives")

            # Cache locally
            self.learned_skills[skill_name] = {
                "source": "composition",
                "primitives": primitive_sequence,
                "created_at": datetime.utcnow().isoformat()
            }

            return True

        except Exception as e:
            logger.error(f"Skill composition failed: {str(e)}")
            return False

    async def get_skill_library(self) -> Dict[str, Any]:
        """Get list of all learned skills.

        Returns:
            Dictionary of skill_name -> skill_info
        """
        try:
            response = await self.client.get(f"{self.hsas_url}/api/skills")
            response.raise_for_status()

            skills = response.json()

            # Update local cache
            self.learned_skills.update(skills)

            logger.debug(f"Retrieved {len(skills)} skills from library")

            return skills

        except Exception as e:
            logger.error(f"Failed to retrieve skill library: {str(e)}")
            return self.learned_skills  # Return cached

    async def get_primitive_library(self) -> List[str]:
        """Get list of available skill primitives.

        Returns:
            List of primitive names
        """
        try:
            response = await self.client.get(f"{self.hsas_url}/api/primitives")
            response.raise_for_status()

            primitives = response.json()

            logger.debug(f"Retrieved {len(primitives)} primitives")

            return primitives

        except Exception as e:
            logger.error(f"Failed to retrieve primitives: {str(e)}")
            return []

    def _update_skill_stats(self, skill_name: str, success: bool):
        """Update local skill statistics.

        Args:
            skill_name: Skill name
            success: Whether execution succeeded
        """
        if skill_name not in self.skill_stats:
            self.skill_stats[skill_name] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "success_rate": 0.0
            }

        stats = self.skill_stats[skill_name]
        stats["executions"] += 1

        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1

        stats["success_rate"] = stats["successes"] / stats["executions"]

    def get_skill_stats(self, skill_name: str) -> Optional[Dict]:
        """Get statistics for a specific skill.

        Args:
            skill_name: Skill name

        Returns:
            Statistics dict or None if not found
        """
        return self.skill_stats.get(skill_name)

    def export_state(self) -> Dict[str, Any]:
        """Export controller state for monitoring.

        Returns:
            State dictionary
        """
        return {
            "hsas_url": self.hsas_url,
            "learned_skills_count": len(self.learned_skills),
            "skill_stats": self.skill_stats,
            "cached_skills": list(self.learned_skills.keys())
        }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
        logger.info("Skill learning controller closed")


# Placeholder classes for completeness (actual implementations in HSAS service)

class SkillPrimitive:
    """Placeholder - Real implementation in HSAS service."""
    pass


class PrimitiveLibrary:
    """Placeholder - Real implementation in HSAS service."""
    pass


class ModelFreeAgent:
    """Placeholder - Real implementation in HSAS service."""
    pass


class ModelBasedAgent:
    """Placeholder - Real implementation in HSAS service."""
    pass


class SkillComposer:
    """Placeholder - Real implementation in HSAS service."""
    pass
