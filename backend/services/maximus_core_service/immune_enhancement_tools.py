"""Immune Enhancement Tools - FASE 9 Integration

Tools for false positive suppression, memory consolidation,
and adaptive immunity capabilities.

NO MOCKS - Production-ready immune enhancement.
"""

from typing import Dict, Any, List, Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)


class ImmuneEnhancementTools:
    """Immune Enhancement Tools for MAXIMUS AI.

    Integrates FASE 9 services:
    - Regulatory T-Cells Service (port 8018)
    - Memory Consolidation Service (port 8019)
    - Adaptive Immunity Service (port 8020)
    """

    def __init__(self, gemini_client: Any):
        """Initialize Immune Enhancement Tools.

        Args:
            gemini_client: Gemini client instance
        """
        self.gemini_client = gemini_client
        self.treg_url = "http://localhost:8018"
        self.memory_url = "http://localhost:8019"
        self.adaptive_url = "http://localhost:8020"

    async def suppress_false_positives(
        self,
        alerts: List[Dict[str, Any]],
        suppression_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """Suppress false positive alerts using Regulatory T-Cells.

        Args:
            alerts: List of alerts to evaluate
            suppression_threshold: Tolerance threshold for suppression (0-1)

        Returns:
            Evaluation results with suppressed alerts
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.treg_url}/alert/evaluate_batch",
                    json={
                        "alerts": alerts,
                        "suppression_threshold": suppression_threshold
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"FP suppression failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in suppress_false_positives: {e}")
            return {"error": str(e)}

    async def get_tolerance_profile(
        self,
        entity_id: str,
        entity_type: str = "ip"
    ) -> Dict[str, Any]:
        """Get immune tolerance profile for entity.

        Args:
            entity_id: Entity identifier (IP, user, domain)
            entity_type: Entity type (ip, user, domain, service)

        Returns:
            Tolerance profile with behavioral fingerprint and FP stats
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.treg_url}/tolerance/profile/{entity_id}",
                    params={"entity_type": entity_type},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Get tolerance profile failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in get_tolerance_profile: {e}")
            return {"error": str(e)}

    async def consolidate_memory(
        self,
        trigger_manual: bool = False,
        importance_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """Trigger memory consolidation cycle (STM → LTM).

        Args:
            trigger_manual: Trigger manual consolidation (bypass circadian rhythm)
            importance_threshold: Minimum importance for consolidation (0-1)

        Returns:
            Consolidation results with patterns extracted and memories created
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.memory_url}/consolidation/trigger",
                    json={
                        "importance_threshold": importance_threshold,
                        "manual_trigger": trigger_manual
                    },
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Memory consolidation failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in consolidate_memory: {e}")
            return {"error": str(e)}

    async def query_long_term_memory(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.5
    ) -> Dict[str, Any]:
        """Query long-term immunological memory.

        Args:
            query: Search query
            limit: Maximum results to return
            min_importance: Minimum importance threshold (0-1)

        Returns:
            Long-term memories matching query
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.memory_url}/memory/long_term",
                    params={
                        "query": query,
                        "limit": limit,
                        "min_importance": min_importance
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"LTM query failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in query_long_term_memory: {e}")
            return {"error": str(e)}

    async def diversify_antibodies(
        self,
        threat_samples: List[Dict[str, Any]],
        repertoire_size: int = 100
    ) -> Dict[str, Any]:
        """Initialize antibody repertoire from threat samples.

        Args:
            threat_samples: Threat samples for training (V(D)J recombination)
            repertoire_size: Size of initial antibody repertoire

        Returns:
            Initialization results with antibody pool stats
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.adaptive_url}/repertoire/initialize",
                    json={
                        "samples": threat_samples,
                        "repertoire_size": repertoire_size
                    },
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Antibody diversification failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in diversify_antibodies: {e}")
            return {"error": str(e)}

    async def run_affinity_maturation(
        self,
        feedback_data: Dict[str, Dict[str, bool]]
    ) -> Dict[str, Any]:
        """Run affinity maturation cycle (somatic hypermutation).

        Args:
            feedback_data: Antibody feedback (antibody_id -> {sample_id -> was_correct})

        Returns:
            Maturation results with new antibodies created
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.adaptive_url}/learning/run_maturation",
                    json=feedback_data,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Affinity maturation failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in run_affinity_maturation: {e}")
            return {"error": str(e)}

    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available Immune Enhancement tools.

        Returns:
            List of tool metadata
        """
        return [
            {
                "name": "suppress_false_positives",
                "method_name": "suppress_false_positives",
                "description": "Suppress false positive alerts using Regulatory T-Cells tolerance learning",
                "parameters": {
                    "alerts": "List of alerts to evaluate",
                    "suppression_threshold": "Tolerance threshold for suppression 0-1"
                }
            },
            {
                "name": "get_tolerance_profile",
                "method_name": "get_tolerance_profile",
                "description": "Get immune tolerance profile for entity with behavioral fingerprint",
                "parameters": {
                    "entity_id": "Entity identifier (IP, user, domain)",
                    "entity_type": "Entity type (ip, user, domain, service)"
                }
            },
            {
                "name": "consolidate_memory",
                "method_name": "consolidate_memory",
                "description": "Trigger memory consolidation cycle (STM → LTM) with pattern extraction",
                "parameters": {
                    "trigger_manual": "Trigger manual consolidation (bool)",
                    "importance_threshold": "Minimum importance for consolidation 0-1"
                }
            },
            {
                "name": "query_long_term_memory",
                "method_name": "query_long_term_memory",
                "description": "Query long-term immunological memory for patterns and attack chains",
                "parameters": {
                    "query": "Search query",
                    "limit": "Maximum results to return",
                    "min_importance": "Minimum importance threshold 0-1"
                }
            },
            {
                "name": "diversify_antibodies",
                "method_name": "diversify_antibodies",
                "description": "Initialize antibody repertoire from threat samples (V(D)J recombination)",
                "parameters": {
                    "threat_samples": "Threat samples for training",
                    "repertoire_size": "Size of initial antibody repertoire"
                }
            },
            {
                "name": "run_affinity_maturation",
                "method_name": "run_affinity_maturation",
                "description": "Run affinity maturation cycle with somatic hypermutation",
                "parameters": {
                    "feedback_data": "Antibody feedback (antibody_id -> sample detections)"
                }
            }
        ]
