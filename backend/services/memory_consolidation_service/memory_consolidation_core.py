"""Maximus Memory Consolidation Service - Memory Consolidation Core.

This module implements the core logic for the Maximus AI's Memory Consolidation
Service. Inspired by biological memory consolidation processes, this core is
responsible for transforming short-term, transient memories into stable,
long-term knowledge.

Key functionalities include:
- Ingesting raw experiences and short-term memories from various Maximus AI services.
- Filtering, organizing, and integrating new information with existing knowledge.
- Identifying redundant or conflicting memories and resolving inconsistencies.
- Storing consolidated knowledge in the long-term memory system (e.g., vector database).
- Ensuring the continuous growth, coherence, and efficiency of Maximus AI's knowledge base,
  allowing for more robust reasoning and decision-making over time.

Performance Optimizations:
- Memory importance scoring for prioritization
- Batch processing for vector DB operations
- Automatic memory pruning based on importance threshold
- Memory health metrics and monitoring
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Assuming a client for the long-term memory (e.g., VectorDBClient) exists
class MockLongTermMemoryClient:
    """Um mock para um cliente de banco de dados de vetor de longo prazo.

    Simula o armazenamento e recuperação de conhecimento para fins de teste.
    Otimizado para batch operations e cache.
    """

    def __init__(self):
        """Initialize mock LTM client with cache."""
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps: Dict[str, datetime] = {}

    async def store_knowledge_batch(
        self, 
        items: List[Tuple[str, Dict[str, Any]]]
    ) -> List[str]:
        """Store multiple knowledge items in a single batch operation.

        Args:
            items: List of (content, metadata) tuples.

        Returns:
            List[str]: IDs of stored items.
        """
        logger.info(f"[MockLTM] Storing {len(items)} items in batch")
        await asyncio.sleep(0.01)  # Simulate batch write
        return [f"ltm_id_{i}_{len(content)}" for i, (content, _) in enumerate(items)]

    async def store_knowledge(self, content: str, metadata: Dict[str, Any]) -> str:
        """Simula o armazenamento de um item de conhecimento no banco de dados de longo prazo.

        Args:
            content (str): O conteúdo textual do conhecimento a ser armazenado.
            metadata (Dict[str, Any]): Metadados associados ao conhecimento.

        Returns:
            str: Um ID simulado para o conhecimento armazenado.
        """
        logger.debug(f"[MockLTM] Storing knowledge: {content[:50]}...")
        await asyncio.sleep(0.01)
        return f"ltm_id_{len(content)}"

    async def retrieve_similar_knowledge(
        self, 
        query: str, 
        top_k: int = 1,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Simula a recuperação de conhecimento similar do banco de dados de longo prazo.

        Args:
            query (str): A consulta para buscar conhecimento similar.
            top_k (int): O número de resultados mais relevantes a serem retornados.
            use_cache (bool): Whether to use cache for repeated queries.

        Returns:
            List[Dict[str, Any]]: Uma lista vazia simulando a ausência de resultados.
        """
        # Check cache
        if use_cache and query in self._cache:
            cache_time = self._cache_timestamps.get(query)
            if cache_time and (datetime.now() - cache_time).seconds < self._cache_ttl:
                logger.debug(f"[MockLTM] Cache hit for: {query[:50]}...")
                return self._cache[query]

        logger.debug(f"[MockLTM] Retrieving similar knowledge for: {query[:50]}...")
        await asyncio.sleep(0.01)
        
        result = []  # Always return empty for simplicity
        
        # Update cache
        if use_cache:
            self._cache[query] = result
            self._cache_timestamps[query] = datetime.now()
        
        return result
    
    def clear_cache(self) -> int:
        """Clear expired cache entries.

        Returns:
            int: Number of entries cleared.
        """
        now = datetime.now()
        expired = [
            k for k, v in self._cache_timestamps.items()
            if (now - v).seconds >= self._cache_ttl
        ]
        
        for key in expired:
            del self._cache[key]
            del self._cache_timestamps[key]
        
        if expired:
            logger.info(f"[MockLTM] Cleared {len(expired)} expired cache entries")
        
        return len(expired)


class MemoryConsolidationCore:
    """Transforms short-term, transient memories into stable, long-term knowledge.

    Ingests raw experiences and short-term memories, filters, organizes, and
    integrates new information with existing knowledge, and stores consolidated
    knowledge in the long-term memory system.
    
    Performance optimizations:
    - Memory importance scoring
    - Batch vector DB operations
    - Automatic pruning of low-importance memories
    - Health metrics tracking
    """

    def __init__(
        self, 
        consolidation_interval_seconds: int = 60,
        importance_threshold: float = 0.3,
        max_buffer_size: int = 1000,
        batch_size: int = 50
    ):
        """Initializes the MemoryConsolidationCore with optimization parameters.

        Args:
            consolidation_interval_seconds (int): The interval in seconds for running consolidation cycles.
            importance_threshold (float): Minimum importance score for memory retention (0.0-1.0).
            max_buffer_size (int): Maximum short-term memories before forced consolidation.
            batch_size (int): Number of memories to process in each batch.
        """
        self.consolidation_interval = consolidation_interval_seconds
        self.importance_threshold = importance_threshold
        self.max_buffer_size = max_buffer_size
        self.batch_size = batch_size
        
        self.is_running = False
        self.short_term_memories: List[Dict[str, Any]] = []
        self.long_term_memory_client = MockLongTermMemoryClient()
        self.last_consolidation_time: Optional[datetime] = None
        self.consolidation_cycles_run: int = 0
        self.current_status: str = "idle"
        
        # Performance metrics
        self.metrics = {
            "total_memories_ingested": 0,
            "total_memories_consolidated": 0,
            "total_memories_pruned": 0,
            "avg_consolidation_time_ms": 0.0,
            "memory_buffer_peak": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    async def start_consolidation_loop(self):
        """Starts the continuous memory consolidation loop."""
        if self.is_running:
            return
        self.is_running = True
        logger.info("🧠 [MemoryConsolidationCore] Starting consolidation loop.")
        asyncio.create_task(self._consolidation_cycle_loop())

    async def stop_consolidation_loop(self):
        """Stops the continuous memory consolidation loop."""
        self.is_running = False
        logger.info("🧠 [MemoryConsolidationCore] Stopping consolidation loop.")

    async def _consolidation_cycle_loop(self):
        """The main loop for memory consolidation with cache management."""
        while self.is_running:
            await asyncio.sleep(self.consolidation_interval)
            
            # Clear expired cache entries periodically
            self.long_term_memory_client.clear_cache()
            
            # Consolidate memories
            await self.consolidate_memories()
            
            # Force consolidation if buffer too large
            if len(self.short_term_memories) >= self.max_buffer_size:
                logger.warning(f"[MemoryConsolidationCore] Buffer full ({len(self.short_term_memories)}), forcing consolidation")
                await self.consolidate_memories()

    async def ingest_short_term_memory(
        self,
        source_service: str,
        memory_type: str,
        payload: Dict[str, Any],
        timestamp: str,
    ):
        """Ingests a short-term memory into the temporary buffer.

        Args:
            source_service (str): The service that generated the memory.
            memory_type (str): The type of memory.
            payload (Dict[str, Any]): The actual memory content.
            timestamp (str): ISO formatted timestamp of when the memory was created.
        """
        memory_entry = {
            "source_service": source_service,
            "memory_type": memory_type,
            "payload": payload,
            "timestamp": timestamp,
            "ingested_at": datetime.now().isoformat(),
            "importance_score": self._calculate_importance(source_service, memory_type, payload)
        }
        self.short_term_memories.append(memory_entry)
        self.metrics["total_memories_ingested"] += 1
        self.metrics["memory_buffer_peak"] = max(
            self.metrics["memory_buffer_peak"],
            len(self.short_term_memories)
        )
        
        logger.debug(
            f"[MemoryConsolidationCore] Ingested memory from {source_service} "
            f"({memory_type}) - Importance: {memory_entry['importance_score']:.2f}"
        )
        
        # Auto-consolidate if buffer full
        if len(self.short_term_memories) >= self.max_buffer_size:
            logger.warning("[MemoryConsolidationCore] Buffer full, triggering consolidation")
            asyncio.create_task(self.consolidate_memories())
    
    def _calculate_importance(
        self,
        source_service: str,
        memory_type: str,
        payload: Dict[str, Any]
    ) -> float:
        """Calculate importance score for memory prioritization.

        Args:
            source_service: Origin service.
            memory_type: Type of memory.
            payload: Memory content.

        Returns:
            float: Importance score (0.0-1.0).
        """
        score = 0.5  # Base score
        
        # Service-based weighting
        high_priority_services = {"maximus_core", "ethical_ai", "consciousness"}
        if any(svc in source_service.lower() for svc in high_priority_services):
            score += 0.2
        
        # Type-based weighting
        high_priority_types = {"decision", "learning", "error", "security"}
        if any(t in memory_type.lower() for t in high_priority_types):
            score += 0.2
        
        # Content-based weighting (payload size and complexity)
        if isinstance(payload, dict):
            if len(payload) > 5:  # Rich payload
                score += 0.1
        
        return min(1.0, score)  # Cap at 1.0

    async def consolidate_memories(self):
        """Processes short-term memories and consolidates them into long-term knowledge with optimizations."""
        if not self.short_term_memories:
            logger.debug("[MemoryConsolidationCore] No short-term memories to consolidate.")
            return

        start_time = datetime.now()
        self.current_status = "consolidating"
        self.consolidation_cycles_run += 1
        
        logger.info(
            f"🧠 [MemoryConsolidationCore] Starting consolidation cycle #{self.consolidation_cycles_run} "
            f"with {len(self.short_term_memories)} memories."
        )

        # Take snapshot and clear buffer
        memories_to_process = list(self.short_term_memories)
        self.short_term_memories.clear()

        # Step 1: Prune low-importance memories
        pruned, memories_to_process = self._prune_memories(memories_to_process)
        self.metrics["total_memories_pruned"] += pruned
        
        if pruned > 0:
            logger.info(f"[MemoryConsolidationCore] Pruned {pruned} low-importance memories")

        # Step 2: Batch process remaining memories
        consolidated_count = 0
        for i in range(0, len(memories_to_process), self.batch_size):
            batch = memories_to_process[i:i + self.batch_size]
            consolidated_count += await self._process_batch(batch)

        self.metrics["total_memories_consolidated"] += consolidated_count
        
        # Update timing metrics
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics["avg_consolidation_time_ms"] = (
            (self.metrics["avg_consolidation_time_ms"] * (self.consolidation_cycles_run - 1) + elapsed_ms)
            / self.consolidation_cycles_run
        )

        self.last_consolidation_time = datetime.now()
        self.current_status = "idle"
        
        logger.info(
            f"🧠 [MemoryConsolidationCore] Consolidation cycle completed. "
            f"Consolidated: {consolidated_count}, Pruned: {pruned}, Time: {elapsed_ms:.0f}ms"
        )

    def _prune_memories(
        self, 
        memories: List[Dict[str, Any]]
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Prune low-importance memories based on threshold.

        Args:
            memories: List of memory entries to prune.

        Returns:
            Tuple of (pruned_count, filtered_memories).
        """
        filtered = [
            m for m in memories
            if m.get("importance_score", 0.0) >= self.importance_threshold
        ]
        pruned = len(memories) - len(filtered)
        return pruned, filtered

    async def _process_batch(self, batch: List[Dict[str, Any]]) -> int:
        """Process a batch of memories using batch vector DB operations.

        Args:
            batch: List of memory entries to process.

        Returns:
            int: Number of memories successfully consolidated.
        """
        try:
            # Prepare batch items
            batch_items = []
            for memory in batch:
                processed_content = self._process_memory(memory)
                metadata = {
                    "source_service": memory["source_service"],
                    "memory_type": memory["memory_type"],
                    "original_timestamp": memory["timestamp"],
                    "importance_score": memory.get("importance_score", 0.0)
                }
                batch_items.append((processed_content, metadata))

            # Batch store to vector DB
            await self.long_term_memory_client.store_knowledge_batch(batch_items)
            
            logger.debug(f"[MemoryConsolidationCore] Batch processed {len(batch)} memories")
            return len(batch)
            
        except Exception as e:
            logger.error(f"[MemoryConsolidationCore] Batch processing error: {e}")
            # Fallback to individual processing
            count = 0
            for memory in batch:
                try:
                    processed_content = self._process_memory(memory)
                    metadata = {
                        "source_service": memory["source_service"],
                        "memory_type": memory["memory_type"],
                        "original_timestamp": memory["timestamp"],
                    }
                    await self.long_term_memory_client.store_knowledge(processed_content, metadata)
                    count += 1
                except Exception as inner_e:
                    logger.error(f"[MemoryConsolidationCore] Failed to process memory: {inner_e}")
            return count

    def _process_memory(self, memory: Dict[str, Any]) -> str:
        """Simulates processing a short-term memory for long-term storage.

        Args:
            memory (Dict[str, Any]): The short-term memory entry.

        Returns:
            str: The processed content suitable for long-term storage.
        """
        # In a real system, this would involve:
        # - NLP for extracting key entities/relationships
        # - Deduplication against existing LTM
        # - Semantic embedding generation
        # - Knowledge graph integration
        importance = memory.get("importance_score", 0.0)
        return (
            f"Consolidated memory from {memory['source_service']} about {memory['memory_type']}: "
            f"{memory['payload']} [importance: {importance:.2f}]"
        )

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Memory Consolidation Core.

        Returns:
            Dict[str, Any]: A dictionary summarizing the core's status and health metrics.
        """
        return {
            "status": self.current_status,
            "consolidation_loop_running": self.is_running,
            "short_term_memories_count": len(self.short_term_memories),
            "consolidation_cycles_run": self.consolidation_cycles_run,
            "last_consolidation": (
                self.last_consolidation_time.isoformat() 
                if self.last_consolidation_time 
                else "N/A"
            ),
            "configuration": {
                "importance_threshold": self.importance_threshold,
                "max_buffer_size": self.max_buffer_size,
                "batch_size": self.batch_size,
                "consolidation_interval_s": self.consolidation_interval
            },
            "metrics": self.metrics,
            "health": self._calculate_health()
        }
    
    def _calculate_health(self) -> Dict[str, Any]:
        """Calculate memory system health indicators.

        Returns:
            Dict[str, Any]: Health metrics and status.
        """
        buffer_utilization = (
            len(self.short_term_memories) / self.max_buffer_size 
            if self.max_buffer_size > 0 
            else 0.0
        )
        
        prune_ratio = (
            self.metrics["total_memories_pruned"] / self.metrics["total_memories_ingested"]
            if self.metrics["total_memories_ingested"] > 0
            else 0.0
        )
        
        health_status = "healthy"
        if buffer_utilization > 0.9:
            health_status = "critical"
        elif buffer_utilization > 0.7:
            health_status = "warning"
        
        return {
            "status": health_status,
            "buffer_utilization": round(buffer_utilization, 2),
            "prune_ratio": round(prune_ratio, 2),
            "avg_consolidation_time_ms": round(self.metrics["avg_consolidation_time_ms"], 2),
            "recommendations": self._generate_recommendations(buffer_utilization, prune_ratio)
        }
    
    def _generate_recommendations(
        self, 
        buffer_utilization: float,
        prune_ratio: float
    ) -> List[str]:
        """Generate operational recommendations based on metrics.

        Args:
            buffer_utilization: Current buffer usage ratio.
            prune_ratio: Ratio of pruned to total memories.

        Returns:
            List[str]: List of recommendations.
        """
        recommendations = []
        
        if buffer_utilization > 0.8:
            recommendations.append("Consider increasing consolidation frequency or buffer size")
        
        if prune_ratio > 0.5:
            recommendations.append("High prune ratio - consider lowering importance threshold")
        
        if prune_ratio < 0.1 and self.metrics["total_memories_ingested"] > 100:
            recommendations.append("Low prune ratio - consider raising importance threshold")
        
        if self.metrics["avg_consolidation_time_ms"] > 5000:
            recommendations.append("High consolidation time - consider reducing batch size")
        
        return recommendations if recommendations else ["System operating optimally"]
