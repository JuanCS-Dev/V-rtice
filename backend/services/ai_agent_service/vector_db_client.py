"""
Aurora Vector Database Client - Semantic Search Infrastructure
===============================================================

Cliente unificado para vector databases, suportando múltiplos backends:

1. QDRANT - Production-grade vector search
2. CHROMA - Lightweight, easy to use
3. FAISS - Local, high-performance
4. IN-MEMORY - Fallback simples

Usado por:
- RAG System (busca de conhecimento)
- Semantic Memory (memória de longo prazo)
- Similarity Search (investigações)

Inspiração: LangChain VectorStores, LlamaIndex, Pinecone
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
import asyncio
from abc import ABC, abstractmethod


class VectorDBType(str, Enum):
    """Tipos de vector database suportados"""
    QDRANT = "qdrant"
    CHROMA = "chroma"
    FAISS = "faiss"
    IN_MEMORY = "in_memory"


class DistanceMetric(str, Enum):
    """Métricas de distância/similaridade"""
    COSINE = "cosine"  # Cosine similarity (mais comum)
    EUCLIDEAN = "euclidean"  # L2 distance
    DOT_PRODUCT = "dot"  # Dot product


@dataclass
class VectorDocument:
    """Documento com embedding vetorial"""
    doc_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.doc_id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class SearchResult:
    """Resultado de busca vetorial"""
    document: VectorDocument
    score: float  # Similarity score (0-1, maior = mais similar)
    rank: int  # Position in results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "rank": self.rank
        }


class VectorDBBackend(ABC):
    """Interface abstrata para backends de vector DB"""

    @abstractmethod
    async def initialize(self):
        """Inicializa conexão com DB"""
        pass

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        distance_metric: DistanceMetric
    ):
        """Cria coleção/índice"""
        pass

    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        documents: List[VectorDocument]
    ):
        """Insere documentos"""
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """Busca por similaridade"""
        pass

    @abstractmethod
    async def delete(
        self,
        collection_name: str,
        doc_ids: List[str]
    ):
        """Deleta documentos"""
        pass

    @abstractmethod
    async def count(self, collection_name: str) -> int:
        """Conta documentos na coleção"""
        pass


class InMemoryBackend(VectorDBBackend):
    """
    Backend in-memory simples (fallback).
    Usa busca linear - OK para < 10k docs.
    """

    def __init__(self):
        self.collections: Dict[str, Dict[str, VectorDocument]] = {}
        self.collection_configs: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Já inicializado"""
        pass

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        distance_metric: DistanceMetric
    ):
        """Cria coleção in-memory"""
        if collection_name not in self.collections:
            self.collections[collection_name] = {}
            self.collection_configs[collection_name] = {
                "dimension": dimension,
                "distance_metric": distance_metric
            }

    async def insert(
        self,
        collection_name: str,
        documents: List[VectorDocument]
    ):
        """Insere documentos"""
        if collection_name not in self.collections:
            # Auto-create collection
            if documents:
                dimension = len(documents[0].embedding)
                await self.create_collection(
                    collection_name, dimension, DistanceMetric.COSINE
                )

        for doc in documents:
            self.collections[collection_name][doc.doc_id] = doc

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Busca linear por similaridade"""
        if collection_name not in self.collections:
            return []

        collection = self.collections[collection_name]
        config = self.collection_configs.get(collection_name, {})
        distance_metric = config.get("distance_metric", DistanceMetric.COSINE)

        # Calcula similaridade para todos docs
        scores = []
        for doc in collection.values():
            # Aplica filtros
            if filters:
                if not self._matches_filters(doc, filters):
                    continue

            # Calcula similaridade
            score = self._calculate_similarity(
                query_vector, doc.embedding, distance_metric
            )
            scores.append((doc, score))

        # Ordena por score (descendente)
        scores.sort(key=lambda x: x[1], reverse=True)

        # Retorna top_k
        results = []
        for rank, (doc, score) in enumerate(scores[:top_k], 1):
            results.append(SearchResult(
                document=doc,
                score=score,
                rank=rank
            ))

        return results

    async def delete(
        self,
        collection_name: str,
        doc_ids: List[str]
    ):
        """Deleta documentos"""
        if collection_name in self.collections:
            for doc_id in doc_ids:
                self.collections[collection_name].pop(doc_id, None)

    async def count(self, collection_name: str) -> int:
        """Conta documentos"""
        if collection_name not in self.collections:
            return 0
        return len(self.collections[collection_name])

    def _matches_filters(
        self,
        doc: VectorDocument,
        filters: Dict[str, Any]
    ) -> bool:
        """Verifica se documento match filtros"""
        for key, value in filters.items():
            doc_value = doc.metadata.get(key)
            if doc_value != value:
                return False
        return True

    def _calculate_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
        metric: DistanceMetric
    ) -> float:
        """Calcula similaridade entre vetores"""
        if len(vec1) != len(vec2):
            return 0.0

        if metric == DistanceMetric.COSINE:
            # Cosine similarity
            dot = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot / (norm1 * norm2)

        elif metric == DistanceMetric.DOT_PRODUCT:
            # Dot product
            return sum(a * b for a, b in zip(vec1, vec2))

        elif metric == DistanceMetric.EUCLIDEAN:
            # L2 distance (inverso normalizado)
            distance = sum((a - b) ** 2 for a, b in zip(vec1, vec2)) ** 0.5
            # Normaliza para 0-1 (maior = mais similar)
            max_distance = (len(vec1) ** 0.5) * 2  # Max possível
            return 1.0 - (distance / max_distance)

        return 0.0


class QdrantBackend(VectorDBBackend):
    """
    Backend para Qdrant (production-grade).

    Requires: pip install qdrant-client
    """

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.host = host
        self.port = port
        self.client = None

    async def initialize(self):
        """Inicializa cliente Qdrant"""
        try:
            from qdrant_client import QdrantClient
            self.client = QdrantClient(host=self.host, port=self.port)
        except ImportError:
            raise ImportError(
                "Qdrant client not installed. "
                "Install with: pip install qdrant-client"
            )

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        distance_metric: DistanceMetric
    ):
        """Cria coleção Qdrant"""
        from qdrant_client.models import Distance, VectorParams

        # Map distance metric
        distance_map = {
            DistanceMetric.COSINE: Distance.COSINE,
            DistanceMetric.EUCLIDEAN: Distance.EUCLID,
            DistanceMetric.DOT_PRODUCT: Distance.DOT
        }

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=dimension,
                distance=distance_map[distance_metric]
            )
        )

    async def insert(
        self,
        collection_name: str,
        documents: List[VectorDocument]
    ):
        """Insere documentos no Qdrant"""
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=doc.doc_id,
                vector=doc.embedding,
                payload={
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "timestamp": doc.timestamp
                }
            )
            for doc in documents
        ]

        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Busca no Qdrant"""
        # TODO: Implementar filtros Qdrant
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k
        )

        search_results = []
        for rank, hit in enumerate(results, 1):
            doc = VectorDocument(
                doc_id=str(hit.id),
                content=hit.payload["content"],
                embedding=hit.vector,
                metadata=hit.payload.get("metadata", {}),
                timestamp=hit.payload.get("timestamp", "")
            )
            search_results.append(SearchResult(
                document=doc,
                score=hit.score,
                rank=rank
            ))

        return search_results

    async def delete(
        self,
        collection_name: str,
        doc_ids: List[str]
    ):
        """Deleta documentos"""
        self.client.delete(
            collection_name=collection_name,
            points_selector=doc_ids
        )

    async def count(self, collection_name: str) -> int:
        """Conta documentos"""
        info = self.client.get_collection(collection_name)
        return info.points_count


class VectorDBClient:
    """
    Cliente unificado para vector databases.

    Suporta múltiplos backends de forma transparente.
    """

    def __init__(
        self,
        backend_type: VectorDBType = VectorDBType.IN_MEMORY,
        **backend_config
    ):
        self.backend_type = backend_type
        self.backend = self._create_backend(backend_type, backend_config)
        self.initialized = False
        self.embedding_function: Optional[Callable] = None

    def _create_backend(
        self,
        backend_type: VectorDBType,
        config: Dict[str, Any]
    ) -> VectorDBBackend:
        """Factory para criar backend"""
        if backend_type == VectorDBType.IN_MEMORY:
            return InMemoryBackend()

        elif backend_type == VectorDBType.QDRANT:
            host = config.get("host", "localhost")
            port = config.get("port", 6333)
            return QdrantBackend(host, port)

        # TODO: Implementar Chroma, FAISS
        else:
            raise ValueError(f"Unsupported backend: {backend_type}")

    async def initialize(self):
        """Inicializa backend"""
        if not self.initialized:
            await self.backend.initialize()
            self.initialized = True

    def set_embedding_function(self, func: Callable[[str], List[float]]):
        """
        Define função para gerar embeddings.

        Example:
            def my_embed(text):
                # Call OpenAI, Cohere, local model, etc
                return [0.1, 0.2, ...]

            client.set_embedding_function(my_embed)
        """
        self.embedding_function = func

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE
    ):
        """Cria coleção"""
        await self._ensure_initialized()
        await self.backend.create_collection(
            collection_name, dimension, distance_metric
        )

    async def add_documents(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Adiciona documentos à coleção.

        Args:
            collection_name: Nome da coleção
            texts: Textos dos documentos
            metadatas: Metadados opcionais
            embeddings: Embeddings pré-computados (se None, usa embedding_function)

        Returns:
            Lista de IDs dos documentos inseridos
        """
        await self._ensure_initialized()

        # Gera embeddings se necessário
        if embeddings is None:
            if self.embedding_function is None:
                raise ValueError(
                    "No embeddings provided and no embedding_function set. "
                    "Call set_embedding_function() first."
                )
            embeddings = [self.embedding_function(text) for text in texts]

        # Gera metadatas se não fornecidos
        if metadatas is None:
            metadatas = [{} for _ in texts]

        # Cria documentos
        documents = []
        doc_ids = []

        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            doc_id = self._generate_doc_id(text)
            doc_ids.append(doc_id)

            doc = VectorDocument(
                doc_id=doc_id,
                content=text,
                embedding=embedding,
                metadata=metadata
            )
            documents.append(doc)

        # Insere
        await self.backend.insert(collection_name, documents)

        return doc_ids

    async def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        query_embedding: Optional[List[float]] = None
    ) -> List[SearchResult]:
        """
        Busca documentos similares.

        Args:
            collection_name: Nome da coleção
            query: Query text (se query_embedding não fornecido)
            top_k: Quantos resultados retornar
            filters: Filtros de metadata
            query_embedding: Embedding pré-computado da query

        Returns:
            Lista de resultados ordenados por similaridade
        """
        await self._ensure_initialized()

        # Gera embedding da query se necessário
        if query_embedding is None:
            if self.embedding_function is None:
                raise ValueError(
                    "No query_embedding provided and no embedding_function set."
                )
            query_embedding = self.embedding_function(query)

        # Busca
        results = await self.backend.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            top_k=top_k,
            filters=filters
        )

        return results

    async def delete_documents(
        self,
        collection_name: str,
        doc_ids: List[str]
    ):
        """Deleta documentos"""
        await self._ensure_initialized()
        await self.backend.delete(collection_name, doc_ids)

    async def count(self, collection_name: str) -> int:
        """Conta documentos na coleção"""
        await self._ensure_initialized()
        return await self.backend.count(collection_name)

    async def _ensure_initialized(self):
        """Garante que backend está inicializado"""
        if not self.initialized:
            await self.initialize()

    def _generate_doc_id(self, text: str) -> str:
        """Gera ID único para documento"""
        # Hash do conteúdo + timestamp para garantir unicidade
        content_hash = hashlib.md5(text.encode()).hexdigest()
        timestamp = datetime.now().timestamp()
        return f"doc_{content_hash[:8]}_{int(timestamp)}"


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do vector DB client"""

    # 1. Cria cliente (in-memory para exemplo)
    client = VectorDBClient(backend_type=VectorDBType.IN_MEMORY)
    await client.initialize()

    # 2. Define função de embedding (fake para exemplo)
    def fake_embed(text: str) -> List[float]:
        """Embedding fake baseado em hash do texto"""
        # Em produção: usar OpenAI, Cohere, sentence-transformers, etc
        text_hash = hashlib.md5(text.encode()).hexdigest()
        # Converte hash em vetor de 384 dimensões
        embedding = []
        for i in range(0, 96, 2):  # 48 chunks de 2 chars = 48 floats
            chunk = text_hash[i:i+2]
            embedding.append(float(int(chunk, 16)) / 255.0)

        # Preenche até 384 dims
        while len(embedding) < 384:
            embedding.append(0.0)

        return embedding[:384]

    client.set_embedding_function(fake_embed)

    # 3. Cria coleção
    await client.create_collection(
        collection_name="cyber_knowledge",
        dimension=384,
        distance_metric=DistanceMetric.COSINE
    )

    # 4. Adiciona documentos
    texts = [
        "CVE-2024-1234 is a critical remote code execution vulnerability in Apache Log4j",
        "SQL injection allows attackers to manipulate database queries",
        "Cross-site scripting (XSS) enables injection of malicious scripts",
        "Ransomware encrypts files and demands payment for decryption",
        "Zero-day vulnerabilities are unknown to software vendors"
    ]

    metadatas = [
        {"category": "vulnerability", "severity": "critical"},
        {"category": "vulnerability", "severity": "high"},
        {"category": "vulnerability", "severity": "medium"},
        {"category": "malware", "severity": "critical"},
        {"category": "vulnerability", "severity": "critical"}
    ]

    doc_ids = await client.add_documents(
        collection_name="cyber_knowledge",
        texts=texts,
        metadatas=metadatas
    )

    print(f"Inserted {len(doc_ids)} documents")

    # 5. Busca
    query = "What are code execution vulnerabilities?"
    results = await client.search(
        collection_name="cyber_knowledge",
        query=query,
        top_k=3
    )

    print(f"\nSearch results for: '{query}'")
    for result in results:
        print(f"[{result.rank}] Score: {result.score:.3f}")
        print(f"    Content: {result.document.content[:80]}...")
        print(f"    Metadata: {result.document.metadata}")

    # 6. Busca com filtro
    print("\n\nSearch with filter (critical only):")
    results_filtered = await client.search(
        collection_name="cyber_knowledge",
        query=query,
        top_k=3,
        filters={"severity": "critical"}
    )

    for result in results_filtered:
        print(f"[{result.rank}] Score: {result.score:.3f}")
        print(f"    Content: {result.document.content[:80]}...")

    # 7. Count
    count = await client.count("cyber_knowledge")
    print(f"\nTotal documents: {count}")


if __name__ == "__main__":
    asyncio.run(example_usage())
