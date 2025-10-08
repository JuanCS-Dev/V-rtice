"""
Memory Consolidation Service client.

Integrates with VÉRTICE Memory Consolidation Service
for long-term immune memory storage and recall.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_client import BaseExternalClient

logger = logging.getLogger(__name__)


class MemoryClient(BaseExternalClient):
    """
    Client for Memory Consolidation Service.

    Provides:
    - Memory consolidation (threat signatures → long-term storage)
    - Memory recall (retrieve similar past threats)
    - Memory search (similarity-based queries)
    - Memory management (forget for privacy/compliance)

    Graceful degradation:
    - Falls back to local PostgreSQL memory only
    - Uses internal MemoryFormation module
    - No cross-service memory sharing in degraded mode
    """

    def __init__(self, base_url: str = "http://localhost:8019", **kwargs):
        """
        Initialize Memory client.

        Args:
            base_url: Memory Service base URL
            **kwargs: Additional BaseExternalClient arguments
        """
        super().__init__(base_url=base_url, **kwargs)

        # Local memory cache (for degraded mode)
        self._local_memory_cache: List[Dict[str, Any]] = []
        self._local_memory_max_size = 1000

    async def consolidate_memory(
        self,
        threat_signature: str,
        threat_type: str,
        response_success: bool,
        antibody_profile: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Consolidate new memory to long-term storage.

        Args:
            threat_signature: Unique threat signature (hash)
            threat_type: Type of threat (malware, network_attack, etc.)
            response_success: Whether immune response was successful
            antibody_profile: Antibody configuration that worked
            metadata: Additional metadata

        Returns:
            Consolidation result with memory_id
        """
        return await self.request(
            "POST",
            "/api/v1/memory/consolidate",
            json={
                "threat_signature": threat_signature,
                "threat_type": threat_type,
                "response_success": response_success,
                "antibody_profile": antibody_profile,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def recall_memory(self, threat_signature: str, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Recall memory for similar threat.

        Args:
            threat_signature: Threat signature to match
            similarity_threshold: Minimum similarity (0.0-1.0)

        Returns:
            Matching memories and antibody profiles
        """
        return await self.request(
            "GET", f"/api/v1/memory/recall/{threat_signature}", params={"similarity_threshold": similarity_threshold}
        )

    async def search_memories(
        self, query: str, threat_type: Optional[str] = None, success_only: bool = False, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search memories by criteria.

        Args:
            query: Search query (threat signature pattern)
            threat_type: Filter by threat type
            success_only: Only return successful responses
            limit: Maximum results

        Returns:
            Matching memories
        """
        params = {
            "query": query,
            "limit": limit,
        }

        if threat_type:
            params["threat_type"] = threat_type

        if success_only:
            params["success_only"] = "true"

        return await self.request("GET", "/api/v1/memory/search", params=params)

    async def forget_memory(self, memory_id: str, reason: str = "privacy_compliance") -> Dict[str, Any]:
        """
        Forget (delete) a memory.

        For privacy/compliance requirements (GDPR, etc.).

        Args:
            memory_id: Memory ID to forget
            reason: Reason for forgetting

        Returns:
            Deletion result
        """
        return await self.request("DELETE", f"/api/v1/memory/{memory_id}", json={"reason": reason})

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get memory service metrics.

        Returns:
            Metrics including total memories, recall accuracy, etc.
        """
        return await self.request("GET", "/api/v1/memory/metrics")

    async def degraded_fallback(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fallback to local memory cache.

        When Memory service is unavailable:
        - Use local in-memory cache (limited size)
        - No persistence across restarts
        - No cross-service memory sharing
        - Limited similarity search

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Request kwargs

        Returns:
            Synthetic degraded response
        """
        logger.warning(f"MemoryClient: Operating in degraded mode for {method} {endpoint}")

        # Parse endpoint
        if endpoint == "/api/v1/memory/consolidate":
            # Store in local cache
            json_data = kwargs.get("json", {})

            memory_entry = {
                "memory_id": f"local_{len(self._local_memory_cache)}",
                "threat_signature": json_data.get("threat_signature"),
                "threat_type": json_data.get("threat_type"),
                "response_success": json_data.get("response_success"),
                "antibody_profile": json_data.get("antibody_profile"),
                "metadata": json_data.get("metadata"),
                "timestamp": datetime.now().isoformat(),
                "degraded_mode": True,
            }

            # Add to cache (FIFO if full)
            if len(self._local_memory_cache) >= self._local_memory_max_size:
                self._local_memory_cache.pop(0)

            self._local_memory_cache.append(memory_entry)

            return {
                "status": "degraded",
                "memory_id": memory_entry["memory_id"],
                "message": "stored_in_local_cache",
                "persistence": "transient",
                "degraded_mode": True,
            }

        elif endpoint.startswith("/api/v1/memory/recall/"):
            # Simple local recall (exact match only)
            threat_signature = endpoint.split("/")[-1]

            matching = [m for m in self._local_memory_cache if m.get("threat_signature") == threat_signature]

            return {
                "status": "degraded",
                "matches": matching,
                "count": len(matching),
                "similarity_method": "exact_match_only",
                "degraded_mode": True,
            }

        elif endpoint == "/api/v1/memory/search":
            # Simple local search
            params = kwargs.get("params", {})
            query = params.get("query", "")
            threat_type = params.get("threat_type")
            limit = int(params.get("limit", 10))

            # Filter by threat_type if specified
            results = self._local_memory_cache

            if threat_type:
                results = [m for m in results if m.get("threat_type") == threat_type]

            # Simple substring search
            if query:
                results = [m for m in results if query in m.get("threat_signature", "")]

            return {
                "status": "degraded",
                "results": results[:limit],
                "total": len(results),
                "search_method": "substring_match",
                "degraded_mode": True,
            }

        elif endpoint.startswith("/api/v1/memory/") and method == "DELETE":
            # Remove from local cache
            memory_id = endpoint.split("/")[-1]

            self._local_memory_cache = [m for m in self._local_memory_cache if m.get("memory_id") != memory_id]

            return {
                "status": "degraded",
                "deleted": True,
                "persistence": "transient",
                "degraded_mode": True,
            }

        elif endpoint == "/api/v1/memory/metrics":
            # Local cache metrics
            return {
                "status": "degraded",
                "total_memories": len(self._local_memory_cache),
                "cache_size": self._local_memory_max_size,
                "cache_usage": len(self._local_memory_cache) / self._local_memory_max_size,
                "persistence": "transient",
                "degraded_mode": True,
            }

        else:
            return {
                "status": "degraded",
                "error": f"unknown_endpoint_{endpoint}",
                "degraded_mode": True,
            }
