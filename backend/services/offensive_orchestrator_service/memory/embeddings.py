"""
Embedding generator for semantic representation of campaigns.

Handles:
- Campaign text serialization
- Embedding generation via Gemini
- Caching for efficiency
- Batch operations
- Error handling with retries

Architecture:
- Model: text-embedding-004 (1536 dimensions)
- Input: Campaign metadata (target, objectives, techniques)
- Output: Vector embedding for similarity search
- Cache: In-memory LRU cache (Sprint 2: Upgrade to Redis for distributed systems)
"""

import logging
import hashlib
import json
from typing import Optional, List, Dict, Any
from functools import lru_cache
from uuid import UUID

import google.generativeai as genai
from google.api_core import retry
from google.api_core import exceptions as google_exceptions

from config import LLMConfig, get_config
from models import CampaignPlan, CampaignObjective


logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings for campaigns using Gemini.

    Converts campaign metadata into vector embeddings for:
    - Similarity search
    - Campaign clustering
    - Pattern recognition
    - Historical context retrieval
    """

    # Embedding model configuration
    EMBEDDING_MODEL = "models/text-embedding-004"
    EMBEDDING_DIMENSION = 1536
    TASK_TYPE = "RETRIEVAL_DOCUMENT"  # Document to be retrieved
    MAX_INPUT_TOKENS = 2048

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize embedding generator.

        Args:
            config: LLM configuration (defaults to global config)

        Raises:
            ValueError: If API key is missing
        """
        self.config = config or get_config().llm

        if not self.config.api_key:
            raise ValueError("Gemini API key is required for embedding generation")

        # Configure Gemini
        genai.configure(api_key=self.config.api_key)

        # Cache for embeddings (in-memory for Sprint 1)
        # Sprint 2: Will upgrade to Redis for distributed caching
        self._embedding_cache: Dict[str, List[float]] = {}

        logger.info(
            f"EmbeddingGenerator initialized: model={self.EMBEDDING_MODEL}, "
            f"dimension={self.EMBEDDING_DIMENSION}"
        )

    async def generate_campaign_embedding(
        self,
        campaign: CampaignPlan,
        use_cache: bool = True,
    ) -> List[float]:
        """
        Generate embedding for a campaign plan.

        Args:
            campaign: Campaign plan to embed
            use_cache: Use cached embedding if available

        Returns:
            List[float]: Embedding vector (1536 dimensions)

        Raises:
            ValueError: If campaign cannot be serialized
            Exception: If embedding generation fails after retries
        """
        # Serialize campaign to text
        campaign_text = self._serialize_campaign(campaign)

        # Generate embedding
        embedding = await self.generate_embedding(
            text=campaign_text,
            use_cache=use_cache,
        )

        logger.debug(
            f"Campaign embedding generated: {campaign.campaign_id}, "
            f"dimension={len(embedding)}"
        )

        return embedding

    async def generate_objective_embedding(
        self,
        objective: CampaignObjective,
        use_cache: bool = True,
    ) -> List[float]:
        """
        Generate embedding for a campaign objective (used for similarity search).

        Args:
            objective: Campaign objective to embed
            use_cache: Use cached embedding if available

        Returns:
            List[float]: Embedding vector (1536 dimensions)
        """
        # Serialize objective to text
        objective_text = self._serialize_objective(objective)

        # Generate embedding
        embedding = await self.generate_embedding(
            text=objective_text,
            use_cache=use_cache,
        )

        logger.debug(f"Objective embedding generated: dimension={len(embedding)}")

        return embedding

    async def generate_embedding(
        self,
        text: str,
        use_cache: bool = True,
    ) -> List[float]:
        """
        Generate embedding for arbitrary text.

        Args:
            text: Text to embed
            use_cache: Use cached embedding if available

        Returns:
            List[float]: Embedding vector (1536 dimensions)

        Raises:
            ValueError: If text is empty or too long
            Exception: If generation fails after retries
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Truncate if too long
        if len(text) > self.MAX_INPUT_TOKENS * 4:  # Rough estimate (4 chars/token)
            logger.warning(f"Text too long ({len(text)} chars), truncating")
            text = text[: self.MAX_INPUT_TOKENS * 4]

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                logger.debug("Embedding cache hit")
                return self._embedding_cache[cache_key]

        # Generate embedding with retries
        try:
            embedding = await self._generate_with_retry(text)

            # Cache result
            if use_cache:
                cache_key = self._get_cache_key(text)
                self._embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}", exc_info=True)
            raise

    @retry.Retry(
        predicate=retry.if_exception_type(
            google_exceptions.ResourceExhausted,
            google_exceptions.ServiceUnavailable,
            google_exceptions.DeadlineExceeded,
        ),
        initial=1.0,
        maximum=10.0,
        multiplier=2.0,
        timeout=60.0,
    )
    async def _generate_with_retry(self, text: str) -> List[float]:
        """
        Generate embedding with automatic retries.

        Args:
            text: Text to embed

        Returns:
            List[float]: Embedding vector

        Raises:
            Exception: If all retries fail
        """
        try:
            # Call Gemini embedding API
            result = genai.embed_content(
                model=self.EMBEDDING_MODEL,
                content=text,
                task_type=self.TASK_TYPE,
            )

            embedding = result["embedding"]

            # Validate dimension
            if len(embedding) != self.EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Unexpected embedding dimension: expected {self.EMBEDDING_DIMENSION}, "
                    f"got {len(embedding)}"
                )

            logger.debug(f"Embedding generated: {len(embedding)} dimensions")

            return embedding

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Embedding generation error: {e}", exc_info=True)
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        use_cache: bool = True,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch operation).

        Args:
            texts: List of texts to embed
            use_cache: Use cached embeddings if available

        Returns:
            List of embedding vectors

        Note:
            Currently processes texts sequentially.
            Sprint 2: Will implement parallel batch processing for performance
        """
        embeddings = []

        for text in texts:
            try:
                embedding = await self.generate_embedding(text, use_cache=use_cache)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to generate embedding in batch: {e}")
                # Use zero vector as fallback
                embeddings.append([0.0] * self.EMBEDDING_DIMENSION)

        logger.info(
            f"Batch embeddings generated: {len(embeddings)} embeddings "
            f"({len([e for e in embeddings if sum(e) != 0])} successful)"
        )

        return embeddings

    def _serialize_campaign(self, campaign: CampaignPlan) -> str:
        """
        Serialize campaign plan to text for embedding.

        Args:
            campaign: Campaign plan

        Returns:
            str: Serialized campaign text

        Format:
            Target: <target>
            Objectives: <objectives>
            Phases: <phase descriptions>
            Techniques: <techniques>
            Priority: <priority>
        """
        parts = []

        # Target
        parts.append(f"Target: {campaign.target}")

        # Success Criteria (objectives for the campaign)
        if campaign.success_criteria:
            objectives_str = ", ".join(campaign.success_criteria)
            parts.append(f"Success Criteria: {objectives_str}")

        # TTPs (MITRE ATT&CK techniques)
        if campaign.ttps:
            ttps_str = ", ".join(campaign.ttps)
            parts.append(f"TTPs: {ttps_str}")

        # Phases (are dicts with keys: name, actions)
        if campaign.phases:
            phase_descriptions = []
            for phase in campaign.phases:
                phase_name = phase.get("name", "Unknown Phase")
                phase_desc = phase_name

                if "actions" in phase and phase["actions"]:
                    # Actions are also dicts
                    actions = phase["actions"]
                    if isinstance(actions, list) and len(actions) > 0:
                        # Just count or show first few action names
                        action_count = len(actions)
                        phase_desc += f" ({action_count} actions)"

                phase_descriptions.append(phase_desc)

            phases_str = " → ".join(phase_descriptions)
            parts.append(f"Phases: {phases_str}")

        # Risk Assessment
        if hasattr(campaign, 'risk_assessment'):
            parts.append(f"Risk: {campaign.risk_assessment.value}")

        # Duration
        if hasattr(campaign, 'estimated_duration_minutes'):
            parts.append(f"Duration: {campaign.estimated_duration_minutes}min")

        # Combine all parts
        campaign_text = "\n".join(parts)

        return campaign_text

    def _serialize_objective(self, objective: CampaignObjective) -> str:
        """
        Serialize campaign objective to text for embedding.

        Args:
            objective: Campaign objective

        Returns:
            str: Serialized objective text
        """
        parts = []

        # Target
        parts.append(f"Target: {objective.target}")

        # Scope
        if objective.scope:
            scope_str = ", ".join(objective.scope)
            parts.append(f"Scope: {scope_str}")

        # Objectives
        if objective.objectives:
            objectives_str = ", ".join(objective.objectives)
            parts.append(f"Objectives: {objectives_str}")

        # Constraints
        if objective.constraints:
            constraints_items = []
            for key, value in objective.constraints.items():
                constraints_items.append(f"{key}={value}")
            constraints_str = ", ".join(constraints_items)
            parts.append(f"Constraints: {constraints_str}")

        # Priority
        if objective.priority:
            parts.append(f"Priority: {objective.priority}")

        objective_text = "\n".join(parts)

        return objective_text

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.

        Args:
            text: Input text

        Returns:
            str: Cache key (SHA256 hash)
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def clear_cache(self):
        """Clear embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            "cache_size": len(self._embedding_cache),
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            "model": self.EMBEDDING_MODEL,
        }
