"""
Aurora Memory System - NSA-Grade Multi-Layer Memory
====================================================

Sistema de memória cognitiva inspirado na neurociência humana:

1. WORKING MEMORY (Redis) - Memória de curto prazo
   - Contexto da conversa atual
   - Estado temporário (segundos/minutos)
   - Ultra-rápida (sub-ms latency)

2. EPISODIC MEMORY (PostgreSQL) - Memória de eventos
   - Histórico completo de conversas
   - Investigações realizadas
   - Resultados de tools
   - Timeline de eventos

3. SEMANTIC MEMORY (Qdrant Vector DB) - Memória de conhecimento
   - Conhecimento sobre ameaças
   - Padrões identificados
   - TTPs (Tactics, Techniques, Procedures)
   - Relações entre entidades

Inspiração: Memória humana + sistemas de elite (NSA, GCHQ)
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
import hashlib

# Redis para working memory
import redis.asyncio as redis

# PostgreSQL para episodic memory
import asyncpg

# Qdrant para semantic memory (vector DB)
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("qdrant-client not available. Install with: pip install qdrant-client")


class MemoryType(str, Enum):
    """Tipos de memória"""
    WORKING = "working"      # Contexto atual (Redis)
    EPISODIC = "episodic"    # Histórico de eventos (PostgreSQL)
    SEMANTIC = "semantic"    # Conhecimento (Vector DB)


class MemoryPriority(str, Enum):
    """Prioridade de retenção"""
    CRITICAL = "critical"    # Nunca esquecer
    HIGH = "high"           # Lembrar por muito tempo
    MEDIUM = "medium"       # Lembrar moderadamente
    LOW = "low"            # Pode esquecer depois de um tempo


@dataclass
class Memory:
    """Representa uma memória"""
    memory_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: MemoryPriority = MemoryPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None  # Para semantic memory
    ttl: Optional[int] = None  # Time-to-live em segundos (para working memory)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "priority": self.priority,
            "metadata": self.metadata,
            "ttl": self.ttl
        }


@dataclass
class ConversationContext:
    """Contexto de uma conversa em andamento"""
    session_id: str
    user_id: Optional[str]
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_chains: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())


class WorkingMemory:
    """
    WORKING MEMORY - Memória de curto prazo (Redis)

    Armazena o contexto ATUAL da conversa.
    Ultra-rápida, mas temporária (TTL: minutos a horas).
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 3600  # 1 hora

    async def connect(self):
        """Conecta ao Redis"""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        """Desconecta do Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def store_context(
        self,
        session_id: str,
        context: ConversationContext,
        ttl: Optional[int] = None
    ):
        """Armazena contexto de conversa"""
        if not self.redis_client:
            await self.connect()

        key = f"context:{session_id}"
        value = json.dumps(context.__dict__, default=str)
        ttl = ttl or self.default_ttl

        await self.redis_client.setex(key, ttl, value)

    async def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Recupera contexto de conversa"""
        if not self.redis_client:
            await self.connect()

        key = f"context:{session_id}"
        value = await self.redis_client.get(key)

        if value:
            data = json.loads(value)
            return ConversationContext(**data)
        return None

    async def update_context(
        self,
        session_id: str,
        new_message: Optional[Dict] = None,
        new_tool_use: Optional[Dict] = None,
        new_reasoning: Optional[Dict] = None
    ):
        """Atualiza contexto existente"""
        context = await self.get_context(session_id)
        if not context:
            return False

        if new_message:
            context.messages.append(new_message)
        if new_tool_use:
            context.tools_used.append(new_tool_use)
        if new_reasoning:
            context.reasoning_chains.append(new_reasoning)

        context.last_activity = datetime.now().isoformat()

        await self.store_context(session_id, context)
        return True

    async def delete_context(self, session_id: str):
        """Deleta contexto (esquece conversa)"""
        if not self.redis_client:
            await self.connect()

        key = f"context:{session_id}"
        await self.redis_client.delete(key)

    async def get_recent_contexts(self, limit: int = 10) -> List[str]:
        """Lista sessões recentes"""
        if not self.redis_client:
            await self.connect()

        pattern = "context:*"
        keys = []
        async for key in self.redis_client.scan_iter(match=pattern):
            keys.append(key.replace("context:", ""))
            if len(keys) >= limit:
                break

        return keys


class EpisodicMemory:
    """
    EPISODIC MEMORY - Memória de eventos (PostgreSQL)

    Armazena HISTÓRICO COMPLETO de:
    - Todas as conversas
    - Todas as investigações
    - Todos os resultados de tools
    - Timeline de eventos

    Permanente. Permite Aurora aprender com o passado.
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Conecta ao PostgreSQL"""
        self.pool = await asyncpg.create_pool(self.db_url)

    async def disconnect(self):
        """Desconecta do PostgreSQL"""
        if self.pool:
            await self.pool.close()

    async def init_schema(self):
        """Inicializa schema do banco"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            # Tabela de conversas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id VARCHAR(255),
                    started_at TIMESTAMP NOT NULL,
                    ended_at TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    tool_count INTEGER DEFAULT 0,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Tabela de mensagens
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Tabela de investigações
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS investigations (
                    id SERIAL PRIMARY KEY,
                    investigation_id VARCHAR(255) UNIQUE NOT NULL,
                    session_id VARCHAR(255),
                    target VARCHAR(500) NOT NULL,
                    target_type VARCHAR(100),
                    status VARCHAR(50),
                    confidence_score FLOAT,
                    findings JSONB,
                    tools_used JSONB,
                    reasoning_trace JSONB,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Tabela de tool executions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id SERIAL PRIMARY KEY,
                    execution_id VARCHAR(255) UNIQUE NOT NULL,
                    session_id VARCHAR(255),
                    investigation_id VARCHAR(255),
                    tool_name VARCHAR(255) NOT NULL,
                    tool_input JSONB NOT NULL,
                    tool_output JSONB,
                    success BOOLEAN,
                    error_message TEXT,
                    execution_time_ms INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Índices para performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_investigations_target ON investigations(target)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_executions_tool ON tool_executions(tool_name)")

    async def store_conversation(
        self,
        session_id: str,
        user_id: Optional[str],
        metadata: Optional[Dict] = None
    ):
        """Inicia registro de nova conversa"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversations (session_id, user_id, started_at, metadata)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (session_id) DO NOTHING
            """, session_id, user_id, datetime.now(), json.dumps(metadata or {}))

    async def store_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Armazena mensagem"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO messages (session_id, role, content, timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5)
            """, session_id, role, content, datetime.now(), json.dumps(metadata or {}))

            # Atualiza contador
            await conn.execute("""
                UPDATE conversations
                SET message_count = message_count + 1,
                    ended_at = $2
                WHERE session_id = $1
            """, session_id, datetime.now())

    async def store_investigation(
        self,
        investigation_id: str,
        session_id: str,
        target: str,
        target_type: str,
        findings: Dict,
        tools_used: List[Dict],
        reasoning_trace: Optional[Dict] = None,
        confidence_score: Optional[float] = None
    ):
        """Armazena investigação completa"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO investigations (
                    investigation_id, session_id, target, target_type,
                    status, confidence_score, findings, tools_used,
                    reasoning_trace, started_at, completed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                investigation_id, session_id, target, target_type,
                "completed", confidence_score,
                json.dumps(findings), json.dumps(tools_used),
                json.dumps(reasoning_trace or {}),
                datetime.now(), datetime.now()
            )

    async def store_tool_execution(
        self,
        execution_id: str,
        session_id: str,
        tool_name: str,
        tool_input: Dict,
        tool_output: Optional[Dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        investigation_id: Optional[str] = None
    ):
        """Armazena execução de tool"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tool_executions (
                    execution_id, session_id, investigation_id,
                    tool_name, tool_input, tool_output,
                    success, error_message, execution_time_ms, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                execution_id, session_id, investigation_id,
                tool_name, json.dumps(tool_input), json.dumps(tool_output or {}),
                success, error_message, execution_time_ms, datetime.now()
            )

    async def get_conversation_history(
        self,
        session_id: str
    ) -> List[Dict]:
        """Recupera histórico de conversa"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT role, content, timestamp, metadata
                FROM messages
                WHERE session_id = $1
                ORDER BY timestamp ASC
            """, session_id)

            return [dict(row) for row in rows]

    async def get_similar_investigations(
        self,
        target: str,
        limit: int = 5
    ) -> List[Dict]:
        """Busca investigações similares ao target"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    investigation_id, target, target_type,
                    confidence_score, findings, tools_used,
                    completed_at
                FROM investigations
                WHERE target ILIKE $1
                ORDER BY completed_at DESC
                LIMIT $2
            """, f"%{target}%", limit)

            return [dict(row) for row in rows]

    async def get_tool_success_rate(
        self,
        tool_name: str,
        last_n_days: int = 30
    ) -> Dict[str, Any]:
        """Calcula taxa de sucesso de uma tool"""
        if not self.pool:
            await self.connect()

        since = datetime.now() - timedelta(days=last_n_days)

        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                    AVG(execution_time_ms) as avg_time_ms
                FROM tool_executions
                WHERE tool_name = $1 AND timestamp > $2
            """, tool_name, since)

            total = result['total']
            successes = result['successes'] or 0

            return {
                "tool_name": tool_name,
                "total_executions": total,
                "successes": successes,
                "failures": total - successes,
                "success_rate": (successes / total * 100) if total > 0 else 0,
                "avg_execution_time_ms": result['avg_time_ms']
            }


class SemanticMemory:
    """
    SEMANTIC MEMORY - Memória de conhecimento (Qdrant Vector DB)

    Armazena CONHECIMENTO SEMÂNTICO:
    - Ameaças conhecidas e seus padrões
    - TTPs (Tactics, Techniques, Procedures)
    - Relações entre entidades
    - Embeddings de textos importantes

    Permite busca semântica: "encontre investigações similares a X"
    """

    def __init__(
        self,
        collection_name: str = "aurora_knowledge",
        qdrant_url: str = "http://localhost:6333",
        vector_size: int = 384  # all-MiniLM-L6-v2 default
    ):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = None
        self.enabled = QDRANT_AVAILABLE

        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(url=qdrant_url)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"✅ Qdrant client initialized: {qdrant_url}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ Qdrant connection failed: {e}")
                self.enabled = False
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("⚠️ Qdrant client not available - semantic memory disabled")

    async def init_collection(self):
        """Inicializa coleção no Qdrant com schema para conhecimento"""
        if not self.enabled or not self.client:
            return False

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)

            if not collection_exists:
                # Create collection with vector config
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE  # Cosine similarity for semantic search
                    )
                )

                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"✅ Created Qdrant collection: {self.collection_name}")

            # Create payload indexes for faster filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="pattern_type",
                field_schema="keyword"
            )

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="timestamp",
                field_schema="datetime"
            )

            return True

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to initialize Qdrant collection: {e}")
            return False

    async def store_knowledge(
        self,
        knowledge_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ):
        """
        Armazena conhecimento com embedding no Qdrant

        Args:
            knowledge_id: ID único do conhecimento
            text: Texto original
            embedding: Vetor de embedding
            metadata: Metadados adicionais
        """
        if not self.enabled or not self.client:
            return False

        try:
            # Prepare point
            point = PointStruct(
                id=hashlib.md5(knowledge_id.encode()).hexdigest(),  # Convert to numeric-like hash
                vector=embedding,
                payload={
                    "knowledge_id": knowledge_id,
                    "text": text,
                    "timestamp": datetime.now().isoformat(),
                    **metadata
                }
            )

            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            return True

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to store knowledge in Qdrant: {e}")
            return False

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Busca conhecimento semanticamente similar

        Args:
            query_embedding: Vetor de busca
            limit: Número máximo de resultados
            score_threshold: Score mínimo de similaridade (0-1)
            filter_conditions: Filtros adicionais (ex: {"pattern_type": "malware"})

        Returns:
            Lista de conhecimentos similares com scores
        """
        if not self.enabled or not self.client:
            return []

        try:
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                must_conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filter_conditions.items()
                ]
                query_filter = Filter(must=must_conditions)

            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            )

            # Format results
            similar_knowledge = []
            for hit in results:
                similar_knowledge.append({
                    "knowledge_id": hit.payload.get("knowledge_id"),
                    "text": hit.payload.get("text"),
                    "score": hit.score,
                    "metadata": {
                        k: v for k, v in hit.payload.items()
                        if k not in ["knowledge_id", "text"]
                    }
                })

            return similar_knowledge

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Qdrant search failed: {e}")
            return []

    async def store_threat_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        description: str,
        indicators: List[str],
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ):
        """
        Armazena padrão de ameaça com embedding automático

        Args:
            pattern_id: ID único do padrão
            pattern_type: Tipo (malware, exploit, phishing, etc)
            description: Descrição textual
            indicators: Lista de IoCs
            metadata: Metadados adicionais
            embedding: Embedding pré-computado (opcional)
        """
        if not self.enabled or not self.client:
            return False

        try:
            # Generate embedding if not provided
            if embedding is None:
                embedding = await self._generate_embedding(description)

            # Combine description with indicators for better semantic search
            full_text = f"{description}\nIndicators: {', '.join(indicators[:10])}"

            # Store with metadata
            await self.store_knowledge(
                knowledge_id=pattern_id,
                text=full_text,
                embedding=embedding,
                metadata={
                    "pattern_type": pattern_type,
                    "description": description,
                    "indicators": indicators,
                    "indicator_count": len(indicators),
                    **metadata
                }
            )

            return True

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to store threat pattern: {e}")
            return False

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding usando modelo local (sentence-transformers)

        Falls back to simple hash-based embedding if model not available
        """
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text).tolist()
            return embedding

        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("⚠️ sentence-transformers not available, using hash-based embedding")

            # Fallback: simple hash-based embedding (not semantic, but functional)
            hash_val = hashlib.sha256(text.encode()).hexdigest()
            # Convert hex to normalized float vector
            embedding = [
                (int(hash_val[i:i+2], 16) - 128) / 128.0
                for i in range(0, min(len(hash_val), self.vector_size * 2), 2)
            ]

            # Pad to vector_size if needed
            while len(embedding) < self.vector_size:
                embedding.append(0.0)

            return embedding[:self.vector_size]

    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da semantic memory"""
        if not self.enabled or not self.client:
            return {
                "enabled": False,
                "reason": "Qdrant not available or not configured"
            }

        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                "enabled": True,
                "collection_name": self.collection_name,
                "total_vectors": collection_info.points_count,
                "vector_size": self.vector_size,
                "distance_metric": "cosine",
                "status": collection_info.status
            }

        except Exception as e:
            return {
                "enabled": False,
                "error": str(e)
            }


class MemorySystem:
    """
    Sistema de memória integrado da Aurora

    Coordena as 3 camadas de memória:
    - Working Memory (Redis)
    - Episodic Memory (PostgreSQL)
    - Semantic Memory (Qdrant)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        postgres_url: str = "postgresql://user:pass@localhost/aurora",
        enable_semantic: bool = False
    ):
        self.working = WorkingMemory(redis_url)
        self.episodic = EpisodicMemory(postgres_url)
        self.semantic = SemanticMemory() if enable_semantic else None
        self.initialized = False

    async def initialize(self):
        """Inicializa todas as camadas de memória"""
        await self.working.connect()
        await self.episodic.connect()
        await self.episodic.init_schema()

        if self.semantic:
            await self.semantic.init_collection()

        self.initialized = True

    async def shutdown(self):
        """Desliga sistema de memória"""
        await self.working.disconnect()
        await self.episodic.disconnect()

    async def remember_conversation(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[ConversationContext]:
        """
        Tenta lembrar de uma conversa.

        1. Primeiro tenta working memory (rápido)
        2. Se não encontrar, busca episodic memory (completo)
        """
        # Tenta working memory primeiro
        context = await self.working.get_context(session_id)
        if context:
            return context

        # Busca em episodic memory
        history = await self.episodic.get_conversation_history(session_id)
        if history:
            # Reconstrói contexto
            context = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                messages=history
            )
            # Carrega de volta para working memory
            await self.working.store_context(session_id, context)
            return context

        return None

    async def learn_from_investigation(
        self,
        investigation_id: str,
        session_id: str,
        target: str,
        findings: Dict,
        tools_used: List[Dict],
        reasoning_trace: Optional[Dict] = None
    ):
        """
        Aprende com uma investigação.

        Armazena em episodic memory para referência futura.
        """
        target_type = self._detect_target_type(target)
        confidence = reasoning_trace.get("confidence", 0.0) if reasoning_trace else 0.0

        await self.episodic.store_investigation(
            investigation_id=investigation_id,
            session_id=session_id,
            target=target,
            target_type=target_type,
            findings=findings,
            tools_used=tools_used,
            reasoning_trace=reasoning_trace,
            confidence_score=confidence
        )

    def _detect_target_type(self, target: str) -> str:
        """Detecta tipo do target"""
        import re

        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
            return "ip"
        elif re.match(r'^[a-fA-F0-9]{32,64}$', target):
            return "hash"
        elif re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', target):
            return "domain"
        elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', target):
            return "email"
        else:
            return "unknown"

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de memória"""
        stats = {
            "initialized": self.initialized,
            "working_memory": "connected" if self.working.redis_client else "disconnected",
            "episodic_memory": "connected" if self.episodic.pool else "disconnected",
            "semantic_memory": "enabled" if self.semantic else "disabled"
        }

        if self.episodic.pool:
            async with self.episodic.pool.acquire() as conn:
                conv_count = await conn.fetchval("SELECT COUNT(*) FROM conversations")
                msg_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
                inv_count = await conn.fetchval("SELECT COUNT(*) FROM investigations")
                tool_count = await conn.fetchval("SELECT COUNT(*) FROM tool_executions")

                stats["episodic_stats"] = {
                    "conversations": conv_count,
                    "messages": msg_count,
                    "investigations": inv_count,
                    "tool_executions": tool_count
                }

        return stats