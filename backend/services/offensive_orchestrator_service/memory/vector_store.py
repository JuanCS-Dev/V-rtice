"""
Vector store manager for Qdrant vector database.

Handles:
- Vector collection management
- Campaign embedding storage
- Similarity search
- Vector operations (upsert, delete, search)

Architecture:
- Collection: "campaigns" with 1536 dimensions (Gemini embeddings)
- Metadata: campaign_id, target, action_type, success, timestamp
- Distance: Cosine similarity
- Optimization: HNSW index for fast search
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from ..config import VectorDBConfig, get_config


logger = logging.getLogger(__name__)


class VectorStore:
    """
    Qdrant vector store for campaign similarity search.

    Stores campaign embeddings for semantic search:
    - Find similar past campaigns
    - Retrieve relevant attack patterns
    - Enable experience-based planning
    """

    # Collection configuration
    COLLECTION_NAME = "campaigns"
    VECTOR_SIZE = 1536  # Gemini embedding dimension
    DISTANCE = qdrant_models.Distance.COSINE

    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize vector store.

        Args:
            config: Vector DB configuration (defaults to global config)
        """
        self.config = config or get_config().vector_db

        # Initialize Qdrant client
        self.client = QdrantClient(
            host=self.config.host,
            port=self.config.port,
            api_key=self.config.api_key if self.config.api_key else None,
            timeout=30.0,
        )

        logger.info(
            f"VectorStore initialized: host={self.config.host}, "
            f"port={self.config.port}, collection={self.COLLECTION_NAME}"
        )

    async def init_collection(self, recreate: bool = False):
        """
        Initialize vector collection.

        Creates collection if it doesn't exist.
        Optionally recreates collection (WARNING: deletes all data).

        Args:
            recreate: If True, delete and recreate collection
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(
                col.name == self.COLLECTION_NAME for col in collections
            )

            if collection_exists:
                if recreate:
                    logger.warning(
                        f"Recreating collection '{self.COLLECTION_NAME}' "
                        "(all data will be deleted)"
                    )
                    self.client.delete_collection(collection_name=self.COLLECTION_NAME)
                    collection_exists = False
                else:
                    logger.info(f"Collection '{self.COLLECTION_NAME}' already exists")
                    return

            if not collection_exists:
                # Create collection with optimized configuration
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.VECTOR_SIZE,
                        distance=self.DISTANCE,
                    ),
                    # HNSW index for fast approximate search
                    hnsw_config=qdrant_models.HnswConfigDiff(
                        m=16,  # Number of edges per node
                        ef_construct=100,  # Construction time/quality tradeoff
                        full_scan_threshold=10000,  # Use full scan for small datasets
                    ),
                    # Optimize for search speed
                    optimizers_config=qdrant_models.OptimizersConfigDiff(
                        indexing_threshold=10000,
                    ),
                )

                logger.info(
                    f"Collection '{self.COLLECTION_NAME}' created successfully: "
                    f"size={self.VECTOR_SIZE}, distance={self.DISTANCE}"
                )

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}", exc_info=True)
            raise

    async def store_campaign_embedding(
        self,
        campaign_id: UUID,
        embedding: List[float],
        metadata: Dict[str, Any],
    ) -> str:
        """
        Store campaign embedding in vector database.

        Args:
            campaign_id: Campaign UUID
            embedding: Vector embedding (1536 dimensions)
            metadata: Campaign metadata (target, objectives, etc.)

        Returns:
            str: Vector ID (same as campaign_id)

        Raises:
            ValueError: If embedding dimension is incorrect
        """
        if len(embedding) != self.VECTOR_SIZE:
            raise ValueError(
                f"Embedding size mismatch: expected {self.VECTOR_SIZE}, "
                f"got {len(embedding)}"
            )

        try:
            vector_id = str(campaign_id)

            # Prepare point with metadata
            point = qdrant_models.PointStruct(
                id=vector_id,
                vector=embedding,
                payload={
                    "campaign_id": vector_id,
                    "target": metadata.get("target", ""),
                    "objectives": metadata.get("objectives", []),
                    "action_types": metadata.get("action_types", []),
                    "success": metadata.get("success", False),
                    "timestamp": metadata.get("timestamp", datetime.utcnow().isoformat()),
                    "priority": metadata.get("priority", 5),
                    "techniques": metadata.get("techniques", []),
                },
            )

            # Upsert point (insert or update)
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[point],
                wait=True,  # Wait for indexing
            )

            logger.debug(
                f"Campaign embedding stored: {campaign_id}, "
                f"target={metadata.get('target')}"
            )

            return vector_id

        except Exception as e:
            logger.error(
                f"Failed to store campaign embedding {campaign_id}: {e}",
                exc_info=True,
            )
            raise

    async def search_similar_campaigns(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar campaigns using vector similarity.

        Args:
            query_embedding: Query vector (1536 dimensions)
            limit: Max number of results
            score_threshold: Minimum similarity score (0-1)
            filters: Optional metadata filters (e.g., {"success": True})

        Returns:
            List of tuples: (campaign_id, similarity_score, metadata)
            Sorted by similarity score (highest first)

        Example:
            results = await store.search_similar_campaigns(
                query_embedding=embedding,
                limit=5,
                score_threshold=0.8,
                filters={"success": True}
            )
            for campaign_id, score, metadata in results:
                print(f"Similar: {campaign_id} (score={score:.3f})")
        """
        if len(query_embedding) != self.VECTOR_SIZE:
            raise ValueError(
                f"Query embedding size mismatch: expected {self.VECTOR_SIZE}, "
                f"got {len(query_embedding)}"
            )

        try:
            # Build filter conditions
            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter(filters)

            # Perform similarity search
            search_result = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions,
                with_payload=True,
            )

            # Extract results
            results = []
            for scored_point in search_result:
                campaign_id = scored_point.payload.get("campaign_id", str(scored_point.id))
                similarity_score = scored_point.score
                metadata = scored_point.payload

                results.append((campaign_id, similarity_score, metadata))

            logger.debug(
                f"Similarity search completed: {len(results)} results "
                f"(threshold={score_threshold})"
            )

            return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}", exc_info=True)
            raise

    async def get_campaign_embedding(
        self,
        campaign_id: UUID,
    ) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """
        Retrieve campaign embedding by ID.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Tuple of (embedding, metadata) or None if not found
        """
        try:
            vector_id = str(campaign_id)

            points = self.client.retrieve(
                collection_name=self.COLLECTION_NAME,
                ids=[vector_id],
                with_payload=True,
                with_vectors=True,
            )

            if not points:
                logger.warning(f"Campaign embedding not found: {campaign_id}")
                return None

            point = points[0]
            embedding = point.vector
            metadata = point.payload

            return (embedding, metadata)

        except Exception as e:
            logger.error(
                f"Failed to retrieve campaign embedding {campaign_id}: {e}",
                exc_info=True,
            )
            return None

    async def delete_campaign_embedding(self, campaign_id: UUID) -> bool:
        """
        Delete campaign embedding from vector store.

        Args:
            campaign_id: Campaign UUID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            vector_id = str(campaign_id)

            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=qdrant_models.PointIdsList(
                    points=[vector_id],
                ),
                wait=True,
            )

            logger.info(f"Campaign embedding deleted: {campaign_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to delete campaign embedding {campaign_id}: {e}",
                exc_info=True,
            )
            return False

    def _build_filter(self, filters: Dict[str, Any]) -> qdrant_models.Filter:
        """
        Build Qdrant filter from dictionary.

        Args:
            filters: Filter dictionary (e.g., {"success": True, "priority": 8})

        Returns:
            Qdrant Filter object
        """
        conditions = []

        for key, value in filters.items():
            if isinstance(value, bool):
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=value),
                    )
                )
            elif isinstance(value, (int, float)):
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=value),
                    )
                )
            elif isinstance(value, str):
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=value),
                    )
                )
            elif isinstance(value, list):
                # Match any value in list
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchAny(any=value),
                    )
                )

        return qdrant_models.Filter(must=conditions)

    async def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection statistics and info.

        Returns:
            Dictionary with collection stats
        """
        try:
            collection_info = self.client.get_collection(
                collection_name=self.COLLECTION_NAME
            )

            return {
                "name": self.COLLECTION_NAME,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status,
                "config": {
                    "vector_size": self.VECTOR_SIZE,
                    "distance": str(self.DISTANCE),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}", exc_info=True)
            return {"error": str(e)}

    def close(self):
        """Close vector store connections."""
        # Qdrant client doesn't require explicit closing
        logger.info("VectorStore connections closed")
