"""Tatacá Ingestion - Neo4j Loader.

Loads entities and relationships into Neo4j knowledge graph via Seriema Graph
service for relationship analysis and graph queries.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx

from models import EntityType, EntityRelationship, LoadResult
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Neo4jLoader:
    """
    Loads entities and relationships into Neo4j graph database.

    Communicates with Seriema Graph service to create nodes and relationships
    for knowledge graph construction and analysis.
    """

    def __init__(self, seriema_url: Optional[str] = None):
        """
        Initialize Neo4j loader.

        Args:
            seriema_url: Seriema Graph service URL (defaults to settings)
        """
        self.seriema_url = seriema_url or settings.SERIEMA_GRAPH_URL
        self.timeout = 30.0
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize HTTP client for Seriema Graph service."""
        try:
            logger.info("Initializing Neo4j loader (via Seriema Graph)...")

            self._client = httpx.AsyncClient(
                base_url=self.seriema_url,
                timeout=self.timeout
            )

            # Health check
            is_healthy = await self.health_check()
            if is_healthy:
                logger.info("✅ Neo4j loader initialized successfully")
            else:
                logger.warning("⚠️ Seriema Graph service not available - graph features limited")

        except Exception as e:
            logger.error(f"Failed to initialize Neo4j loader: {e}", exc_info=True)
            raise

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.info("Neo4j loader closed")

    async def load_entity(
        self,
        entity_type: EntityType,
        entity_data: Dict[str, Any]
    ) -> LoadResult:
        """
        Load a single entity as a node in Neo4j.

        Args:
            entity_type: Type of entity
            entity_data: Entity data dictionary

        Returns:
            LoadResult with success status
        """
        try:
            if not self._client:
                raise RuntimeError("Neo4j loader not initialized")

            # Build entity ID
            entity_id = self._get_entity_id(entity_type, entity_data)

            # Create node via Seriema Graph API
            node_data = {
                "type": entity_type.value,
                "id": entity_id,
                "properties": entity_data
            }

            response = await self._client.post("/nodes", json=node_data)
            response.raise_for_status()

            logger.info(f"Loaded {entity_type} node: {entity_id}")

            return LoadResult(
                success=True,
                entity_type=entity_type,
                entity_id=entity_id,
                neo4j_loaded=True
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Seriema Graph endpoint not implemented yet - graceful degradation
                logger.warning(f"Seriema Graph /nodes endpoint not available: {e}")
                return LoadResult(
                    success=True,  # Don't fail the whole job
                    entity_type=entity_type,
                    entity_id=self._get_entity_id(entity_type, entity_data),
                    neo4j_loaded=False,
                    error_message="Neo4j loading skipped (service not ready)"
                )
            else:
                logger.error(f"HTTP error loading node: {e}")
                return LoadResult(
                    success=False,
                    entity_type=entity_type,
                    entity_id=self._get_entity_id(entity_type, entity_data),
                    neo4j_loaded=False,
                    error_message=str(e)
                )

        except Exception as e:
            logger.error(f"Error loading entity to Neo4j: {e}", exc_info=True)
            return LoadResult(
                success=False,
                entity_type=entity_type,
                entity_id=self._get_entity_id(entity_type, entity_data),
                neo4j_loaded=False,
                error_message=str(e)
            )

    async def load_relationship(
        self,
        relationship: EntityRelationship
    ) -> bool:
        """
        Load a relationship as an edge in Neo4j.

        Args:
            relationship: EntityRelationship object

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._client:
                raise RuntimeError("Neo4j loader not initialized")

            # Create edge via Seriema Graph API
            edge_data = {
                "source_type": relationship.source_type.value,
                "source_id": relationship.source_id,
                "target_type": relationship.target_type.value,
                "target_id": relationship.target_id,
                "relation_type": relationship.relation_type.value,
                "properties": relationship.properties
            }

            response = await self._client.post("/edges", json=edge_data)
            response.raise_for_status()

            logger.info(
                f"Loaded relationship: {relationship.source_id} "
                f"-[{relationship.relation_type}]-> {relationship.target_id}"
            )

            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Seriema Graph endpoint not implemented yet - graceful degradation
                logger.warning(f"Seriema Graph /edges endpoint not available: {e}")
                return False  # Don't fail, just skip
            else:
                logger.error(f"HTTP error loading relationship: {e}")
                return False

        except Exception as e:
            logger.error(f"Error loading relationship to Neo4j: {e}", exc_info=True)
            return False

    async def load_batch(
        self,
        entity_type: EntityType,
        entities: List[Dict[str, Any]]
    ) -> List[LoadResult]:
        """
        Load multiple entities in batch.

        Args:
            entity_type: Type of entities
            entities: List of entity data dictionaries

        Returns:
            List of LoadResult objects
        """
        results = []

        for entity_data in entities:
            result = await self.load_entity(entity_type, entity_data)
            results.append(result)

        success_count = sum(1 for r in results if r.success and r.neo4j_loaded)
        logger.info(f"Batch loaded {success_count}/{len(entities)} {entity_type} nodes to Neo4j")

        return results

    async def load_relationships_batch(
        self,
        relationships: List[EntityRelationship]
    ) -> int:
        """
        Load multiple relationships in batch.

        Args:
            relationships: List of EntityRelationship objects

        Returns:
            Number of successfully loaded relationships
        """
        success_count = 0

        for relationship in relationships:
            success = await self.load_relationship(relationship)
            if success:
                success_count += 1

        logger.info(f"Batch loaded {success_count}/{len(relationships)} relationships to Neo4j")

        return success_count

    async def query_graph(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a Cypher query via Seriema Graph service.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            Query results
        """
        try:
            if not self._client:
                raise RuntimeError("Neo4j loader not initialized")

            request_data = {
                "query": query,
                "params": params or {}
            }

            response = await self._client.post("/query", json=request_data)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Seriema Graph /query endpoint not available")
                return {"results": [], "error": "Query endpoint not implemented"}
            else:
                logger.error(f"HTTP error executing query: {e}")
                raise

        except Exception as e:
            logger.error(f"Error executing graph query: {e}", exc_info=True)
            raise

    async def get_entity_neighbors(
        self,
        entity_type: EntityType,
        entity_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get neighboring entities in the graph.

        Args:
            entity_type: Type of central entity
            entity_id: Entity identifier
            max_depth: Maximum traversal depth

        Returns:
            Subgraph of neighbors
        """
        try:
            query_params = {
                "entity_type": entity_type.value,
                "entity_id": entity_id,
                "max_depth": max_depth
            }

            response = await self._client.get("/neighbors", params=query_params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Seriema Graph /neighbors endpoint not available")
                return {"nodes": [], "edges": []}
            else:
                logger.error(f"HTTP error getting neighbors: {e}")
                return {"nodes": [], "edges": []}

        except Exception as e:
            logger.error(f"Error getting entity neighbors: {e}", exc_info=True)
            return {"nodes": [], "edges": []}

    async def find_path(
        self,
        source_type: EntityType,
        source_id: str,
        target_type: EntityType,
        target_id: str,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Find shortest path between two entities.

        Args:
            source_type: Source entity type
            source_id: Source entity ID
            target_type: Target entity type
            target_id: Target entity ID
            max_depth: Maximum path length

        Returns:
            Path information or empty if no path found
        """
        try:
            path_query = {
                "source_type": source_type.value,
                "source_id": source_id,
                "target_type": target_type.value,
                "target_id": target_id,
                "max_depth": max_depth
            }

            response = await self._client.post("/paths", json=path_query)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Seriema Graph /paths endpoint not available")
                return {"paths": []}
            else:
                logger.error(f"HTTP error finding path: {e}")
                return {"paths": []}

        except Exception as e:
            logger.error(f"Error finding path: {e}", exc_info=True)
            return {"paths": []}

    async def health_check(self) -> bool:
        """
        Check Seriema Graph service health.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if not self._client:
                return False

            response = await self._client.get("/health")
            return response.status_code == 200

        except Exception as e:
            logger.debug(f"Seriema Graph health check failed: {e}")
            return False

    def _get_entity_id(self, entity_type: EntityType, entity_data: Dict[str, Any]) -> str:
        """
        Extract entity identifier from data.

        Args:
            entity_type: Type of entity
            entity_data: Entity data dictionary

        Returns:
            Entity identifier string
        """
        if entity_type == EntityType.PESSOA:
            return entity_data.get("cpf") or entity_data.get("nome", "unknown")
        elif entity_type == EntityType.VEICULO:
            return entity_data.get("placa", "unknown")
        elif entity_type == EntityType.OCORRENCIA:
            return entity_data.get("numero_bo", "unknown")
        elif entity_type == EntityType.ENDERECO:
            # Build composite ID
            return entity_data.get("id") or f"{entity_data.get('logradouro', '')}-{entity_data.get('cidade', '')}"
        else:
            return "unknown"
