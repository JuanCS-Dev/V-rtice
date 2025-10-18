"""
Attack Memory System - High-level coordinator for persistent learning.

Integrates:
- PostgreSQL: Structured campaign data
- Qdrant: Vector similarity search
- Embeddings: Semantic representation

Provides:
- Campaign storage and retrieval
- Similarity-based search
- Historical context for planning
- Learning from past operations

Architecture:
- Hybrid storage: Relational + Vector
- Automatic embedding generation
- Intelligent retrieval strategies
- Performance optimization
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from ..models import CampaignPlan, CampaignObjective, CampaignDB, CampaignStatus
from .database import DatabaseManager
from .vector_store import VectorStore
from .embeddings import EmbeddingGenerator


logger = logging.getLogger(__name__)


class AttackMemorySystem:
    """
    High-level attack memory system.

    Manages persistent storage and retrieval of offensive campaigns:
    - Stores campaigns in PostgreSQL (structured data)
    - Generates and stores embeddings in Qdrant (semantic search)
    - Retrieves similar past campaigns for planning
    - Tracks success patterns and lessons learned
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        vector_store: Optional[VectorStore] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
    ):
        """
        Initialize attack memory system.

        Args:
            db_manager: Database manager (defaults to new instance)
            vector_store: Vector store (defaults to new instance)
            embedding_generator: Embedding generator (defaults to new instance)
        """
        self.db = db_manager or DatabaseManager()
        self.vector_store = vector_store or VectorStore()
        self.embeddings = embedding_generator or EmbeddingGenerator()

        logger.info("AttackMemorySystem initialized")

    async def initialize(self):
        """
        Initialize all components.

        Call this on service startup.
        Creates database schema and vector collection.
        """
        try:
            # Initialize database schema
            self.db.init_db()
            logger.info("Database schema initialized")

            # Initialize vector collection
            await self.vector_store.init_collection(recreate=False)
            logger.info("Vector collection initialized")

            logger.info("✅ AttackMemorySystem initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize AttackMemorySystem: {e}", exc_info=True)
            raise

    async def store_campaign(
        self,
        campaign: CampaignPlan,
        status: CampaignStatus = CampaignStatus.PLANNED,
    ) -> UUID:
        """
        Store campaign in memory system.

        Stores both structured data (PostgreSQL) and embedding (Qdrant).

        Args:
            campaign: Campaign plan to store
            status: Initial campaign status

        Returns:
            UUID: Campaign ID

        Raises:
            Exception: If storage fails
        """
        try:
            # 1. Store in PostgreSQL
            # Extract data from campaign plan (campaigns don't have scope/objectives directly)
            # These would come from the original objective that created the plan
            campaign_db = await self.db.create_campaign(
                target=campaign.target,
                scope=[],  # CampaignPlan doesn't have scope
                objectives=campaign.success_criteria or [],  # Use success criteria as objectives
                constraints={},  # CampaignPlan doesn't have constraints
                priority=5,  # Default priority
                created_by=getattr(campaign, 'created_by', None),
            )

            campaign_id = campaign_db.id

            # Update campaign with ID
            campaign.campaign_id = campaign_id

            # 2. Generate embedding
            logger.debug(f"Generating embedding for campaign {campaign_id}")
            embedding = await self.embeddings.generate_campaign_embedding(campaign)

            # 3. Store embedding with metadata
            metadata = {
                "target": campaign.target,
                "objectives": campaign.success_criteria or [],
                "action_types": self._extract_action_types(campaign),
                "techniques": self._extract_techniques(campaign),
                "priority": 5,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,  # Will be updated when campaign completes
            }

            await self.vector_store.store_campaign_embedding(
                campaign_id=campaign_id,
                embedding=embedding,
                metadata=metadata,
            )

            logger.info(
                f"Campaign stored successfully: {campaign_id}, target={campaign.target}"
            )

            return campaign_id

        except Exception as e:
            logger.error(f"Failed to store campaign: {e}", exc_info=True)
            raise

    async def get_campaign(self, campaign_id: UUID) -> Optional[CampaignDB]:
        """
        Retrieve campaign by ID.

        Args:
            campaign_id: Campaign UUID

        Returns:
            CampaignDB or None if not found
        """
        return await self.db.get_campaign(campaign_id)

    async def update_campaign_status(
        self,
        campaign_id: UUID,
        status: CampaignStatus,
        results: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update campaign status.

        Args:
            campaign_id: Campaign UUID
            status: New status
            results: Optional results data

        Returns:
            bool: True if updated successfully
        """
        success = await self.db.update_campaign_status(
            campaign_id=campaign_id,
            status=status,
            results=results,
        )

        # Update vector metadata if completed/failed
        if success and (status == CampaignStatus.COMPLETED or status == CampaignStatus.FAILED):
            try:
                # Get existing embedding
                result = await self.vector_store.get_campaign_embedding(campaign_id)
                if result:
                    embedding, metadata = result
                    # Update success flag
                    metadata["success"] = (status == CampaignStatus.COMPLETED)
                    # Re-store with updated metadata
                    await self.vector_store.store_campaign_embedding(
                        campaign_id=campaign_id,
                        embedding=embedding,
                        metadata=metadata,
                    )
                    logger.debug(f"Vector metadata updated for campaign {campaign_id}")
            except Exception as e:
                logger.warning(f"Failed to update vector metadata: {e}")

        return success

    async def find_similar_campaigns(
        self,
        objective: CampaignObjective,
        limit: int = 5,
        score_threshold: float = 0.7,
        success_only: bool = False,
    ) -> List[Tuple[CampaignDB, float]]:
        """
        Find similar past campaigns using semantic search.

        Args:
            objective: Campaign objective to compare
            limit: Max number of results
            score_threshold: Minimum similarity score (0-1)
            success_only: Only return successful campaigns

        Returns:
            List of tuples: (CampaignDB, similarity_score)
            Sorted by similarity (highest first)

        Example:
            similar = await memory.find_similar_campaigns(
                objective=objective,
                limit=5,
                score_threshold=0.8,
                success_only=True
            )
            for campaign, score in similar:
                print(f"Similar: {campaign.target} (score={score:.3f})")
        """
        try:
            # 1. Generate query embedding
            query_embedding = await self.embeddings.generate_objective_embedding(objective)

            # 2. Build filters
            filters = {}
            if success_only:
                filters["success"] = True

            # 3. Search vector store
            vector_results = await self.vector_store.search_similar_campaigns(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters,
            )

            # 4. Retrieve full campaign data from PostgreSQL
            results = []
            for campaign_id_str, similarity_score, metadata in vector_results:
                campaign_id = UUID(campaign_id_str)
                campaign_db = await self.db.get_campaign(campaign_id)

                if campaign_db:
                    results.append((campaign_db, similarity_score))
                else:
                    logger.warning(
                        f"Campaign {campaign_id} found in vector store but not in database"
                    )

            logger.info(
                f"Similarity search completed: {len(results)} campaigns found "
                f"(threshold={score_threshold})"
            )

            return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}", exc_info=True)
            return []

    async def get_historical_context(
        self,
        objective: CampaignObjective,
        max_campaigns: int = 3,
    ) -> str:
        """
        Get historical context for campaign planning.

        Retrieves similar past campaigns and formats them as context
        for the orchestrator LLM.

        Args:
            objective: Campaign objective
            max_campaigns: Maximum number of campaigns to include

        Returns:
            str: Formatted historical context
        """
        try:
            # Find similar successful campaigns
            similar_campaigns = await self.find_similar_campaigns(
                objective=objective,
                limit=max_campaigns,
                score_threshold=0.6,
                success_only=True,
            )

            if not similar_campaigns:
                return "No similar past campaigns found."

            # Format context
            context_parts = [
                f"Found {len(similar_campaigns)} similar past campaigns:",
                "",
            ]

            for idx, (campaign, similarity_score) in enumerate(similar_campaigns, 1):
                context_parts.append(f"Campaign {idx} (similarity: {similarity_score:.2f}):")
                context_parts.append(f"  Target: {campaign.target}")
                context_parts.append(f"  Objectives: {', '.join(campaign.objectives)}")
                context_parts.append(f"  Status: {campaign.status}")

                if campaign.results:
                    # Extract key results
                    results_summary = self._summarize_results(campaign.results)
                    context_parts.append(f"  Results: {results_summary}")

                context_parts.append("")

            historical_context = "\n".join(context_parts)

            logger.debug(
                f"Historical context generated: {len(similar_campaigns)} campaigns"
            )

            return historical_context

        except Exception as e:
            logger.error(f"Failed to get historical context: {e}", exc_info=True)
            return "Error retrieving historical context."

    async def store_attack_memory(
        self,
        campaign_id: UUID,
        action_type: str,
        target: str,
        technique: str,
        success: bool,
        result: Dict[str, Any],
        lessons_learned: Optional[str] = None,
    ) -> UUID:
        """
        Store individual attack memory entry.

        Args:
            campaign_id: Campaign UUID
            action_type: Action type
            target: Target identifier
            technique: Technique used
            success: Whether action succeeded
            result: Result data
            lessons_learned: Optional lessons

        Returns:
            UUID: Memory entry ID
        """
        memory_entry = await self.db.store_attack_memory(
            campaign_id=campaign_id,
            action_type=action_type,
            target=target,
            technique=technique,
            success=success,
            result=result,
            lessons_learned=lessons_learned,
        )

        logger.info(
            f"Attack memory stored: {memory_entry.id}, "
            f"action={action_type}, success={success}"
        )

        return memory_entry.id

    async def search_attack_memory(
        self,
        target: Optional[str] = None,
        technique: Optional[str] = None,
        success_only: bool = False,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search attack memory entries.

        Args:
            target: Optional target filter
            technique: Optional technique filter
            success_only: Only successful attacks
            limit: Max results

        Returns:
            List of memory entries
        """
        memories = await self.db.search_attack_memory(
            target=target,
            technique=technique,
            success_only=success_only,
            limit=limit,
        )

        # Convert to dictionaries
        results = []
        for memory in memories:
            results.append({
                "id": str(memory.id),
                "campaign_id": str(memory.campaign_id),
                "action_type": memory.action_type,
                "target": memory.target,
                "technique": memory.technique,
                "success": memory.success,
                "result": memory.result,
                "lessons_learned": memory.lessons_learned,
                "timestamp": memory.timestamp.isoformat(),
            })

        logger.info(f"Attack memory search: {len(results)} entries found")

        return results

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory system statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            # Database stats
            total_campaigns = len(await self.db.list_campaigns(limit=10000))
            active_campaigns = len(
                await self.db.list_campaigns(status=CampaignStatus.IN_PROGRESS, limit=10000)
            )
            completed_campaigns = len(
                await self.db.list_campaigns(status=CampaignStatus.COMPLETED, limit=10000)
            )

            # Vector store stats
            vector_info = await self.vector_store.get_collection_info()

            # Embedding cache stats
            cache_stats = self.embeddings.get_cache_stats()

            return {
                "database": {
                    "total_campaigns": total_campaigns,
                    "active_campaigns": active_campaigns,
                    "completed_campaigns": completed_campaigns,
                },
                "vector_store": vector_info,
                "embeddings": cache_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {"error": str(e)}

    def _extract_action_types(self, campaign: CampaignPlan) -> List[str]:
        """Extract all action types from campaign."""
        action_types = set()
        if campaign.phases:
            for phase in campaign.phases:
                # phase is a dict with 'actions' key
                if isinstance(phase, dict) and "actions" in phase and phase["actions"]:
                    for action in phase["actions"]:
                        # action is also a dict
                        if isinstance(action, dict) and "action" in action:
                            action_types.add(action.get("action", "unknown"))
        return list(action_types)

    def _extract_techniques(self, campaign: CampaignPlan) -> List[str]:
        """Extract all techniques from campaign."""
        techniques = set()
        if campaign.phases:
            for phase in campaign.phases:
                # phase is a dict with 'actions' key
                if isinstance(phase, dict) and "actions" in phase and phase["actions"]:
                    for action in phase["actions"]:
                        # action is also a dict
                        if isinstance(action, dict) and "ttp" in action:
                            techniques.add(action["ttp"])
        return list(techniques)

    def _summarize_results(self, results: Dict[str, Any]) -> str:
        """Summarize campaign results."""
        summary_parts = []

        if "success_rate" in results:
            summary_parts.append(f"success_rate={results['success_rate']}")

        if "phases_completed" in results:
            summary_parts.append(f"phases={results['phases_completed']}")

        if "findings" in results and isinstance(results["findings"], list):
            summary_parts.append(f"findings={len(results['findings'])}")

        return ", ".join(summary_parts) if summary_parts else "No summary available"

    def close(self):
        """Close all connections."""
        self.db.close()
        self.vector_store.close()
        logger.info("AttackMemorySystem connections closed")
