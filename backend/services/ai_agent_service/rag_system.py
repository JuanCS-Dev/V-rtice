"""
Aurora RAG System - Retrieval-Augmented Generation
===================================================

Sistema RAG (Retrieval-Augmented Generation) para reduzir alucinações
e melhorar precisão factual através de:

1. Busca vetorial em bases de conhecimento
2. Verificação de factos em tempo real
3. Citação de fontes
4. Confidence scoring baseado em evidências

Resolve o problema #1 do Manifesto:
- "66% dos profissionais frustrados com respostas 'quase certas'"
- "Alucinações ocorrem em 15-38% dos outputs"

Inspiração: Perplexity, You.com, Claude com Citations
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
import asyncio


class SourceType(str, Enum):
    """Tipos de fontes de conhecimento"""
    THREAT_INTEL = "threat_intel"  # CVE, NVD, etc
    OSINT = "osint"  # Dados OSINT coletados
    MALWARE_DB = "malware_db"  # Base de malware
    DOCUMENTATION = "documentation"  # Docs técnicos
    MEMORY = "memory"  # Memória da Aurora
    WEB = "web"  # Busca web
    FILE = "file"  # Arquivos locais


class RelevanceLevel(str, Enum):
    """Nível de relevância do documento recuperado"""
    VERY_HIGH = "very_high"  # > 0.9 similarity
    HIGH = "high"  # 0.7-0.9
    MEDIUM = "medium"  # 0.5-0.7
    LOW = "low"  # 0.3-0.5
    VERY_LOW = "very_low"  # < 0.3


@dataclass
class Source:
    """Representa uma fonte de informação"""
    source_id: str
    source_type: SourceType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    url: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    relevance_score: float = 0.0  # 0-1
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.source_id,
            "type": self.source_type,
            "content": self.content,
            "metadata": self.metadata,
            "url": self.url,
            "timestamp": self.timestamp,
            "relevance": self.relevance_score
        }


@dataclass
class Citation:
    """Citação de uma fonte no texto gerado"""
    citation_id: str
    source: Source
    quoted_text: str
    relevance: RelevanceLevel
    confidence: float  # 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.citation_id,
            "source": self.source.to_dict(),
            "text": self.quoted_text,
            "relevance": self.relevance,
            "confidence": self.confidence
        }


@dataclass
class RAGResult:
    """Resultado de uma query RAG"""
    query: str
    answer: str
    sources: List[Source] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.0  # 0-1
    has_hallucination_risk: bool = False
    reasoning: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "sources": [s.to_dict() for s in self.sources],
            "citations": [c.to_dict() for c in self.citations],
            "confidence": self.confidence,
            "hallucination_risk": self.has_hallucination_risk,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp
        }


class VectorStore:
    """
    Interface abstrata para vector stores.
    Pode usar: Qdrant, Chroma, FAISS, Pinecone, etc.
    """

    def __init__(self, collection_name: str = "aurora_knowledge"):
        self.collection_name = collection_name
        self.documents: List[Source] = []  # In-memory fallback
        self.embeddings_cache: Dict[str, List[float]] = {}

    async def add_documents(self, sources: List[Source]):
        """Adiciona documentos ao vector store"""
        # TODO: Integrar com Qdrant ou Chroma real
        self.documents.extend(sources)

    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Source]:
        """
        Busca por similaridade vetorial.

        Args:
            query: Query string
            top_k: Quantos documentos retornar
            min_score: Score mínimo de similaridade (0-1)
            filters: Filtros adicionais (tipo, data, etc)

        Returns:
            Lista de fontes ordenadas por relevância
        """
        # TODO: Implementar busca vetorial real
        # Por enquanto, retorna busca simples
        results = []
        query_lower = query.lower()

        for doc in self.documents:
            # Busca keyword simples (placeholder)
            if any(word in doc.content.lower() for word in query_lower.split()):
                # Score fake baseado em quantas palavras match
                words_matched = sum(
                    1 for word in query_lower.split()
                    if word in doc.content.lower()
                )
                doc.relevance_score = words_matched / len(query_lower.split())

                if doc.relevance_score >= min_score:
                    results.append(doc)

        # Ordena por relevância
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]

    async def get_embedding(self, text: str) -> List[float]:
        """Gera embedding para texto"""
        # TODO: Integrar com modelo de embedding real (OpenAI, Cohere, local)
        # Por enquanto retorna hash fake
        text_hash = hashlib.md5(text.encode()).hexdigest()
        # Converte hash em vetor fake de 384 dimensões
        fake_embedding = [float(int(c, 16)) / 15.0 for c in text_hash[:384]]
        return fake_embedding


class FactChecker:
    """
    Sistema de verificação factual para detectar alucinações.
    """

    def __init__(self):
        self.hallucination_patterns = [
            "I don't have access to",
            "I cannot verify",
            "based on my training data",
            "as of my knowledge cutoff",
            "I'm not sure",
            "this may not be accurate"
        ]

    async def check_factual_consistency(
        self,
        answer: str,
        sources: List[Source]
    ) -> Tuple[bool, float, List[str]]:
        """
        Verifica consistência factual da resposta contra fontes.

        Returns:
            (is_consistent, confidence, issues)
        """
        issues = []

        # 1. Verifica se resposta contém patterns de incerteza
        uncertainty_found = any(
            pattern.lower() in answer.lower()
            for pattern in self.hallucination_patterns
        )

        if uncertainty_found:
            issues.append("Response contains uncertainty markers")

        # 2. Verifica se temos fontes suficientes
        if len(sources) == 0:
            issues.append("No sources provided to verify answer")
            return False, 0.0, issues

        if len(sources) < 2:
            issues.append("Only one source - low confidence")

        # 3. Verifica se fontes são relevantes
        avg_relevance = sum(s.relevance_score for s in sources) / len(sources)
        if avg_relevance < 0.5:
            issues.append(f"Low average relevance: {avg_relevance:.2f}")

        # 4. Calcula confidence
        confidence = avg_relevance * (1.0 if len(sources) >= 2 else 0.7)
        confidence *= (0.8 if uncertainty_found else 1.0)

        is_consistent = confidence >= 0.6 and len(issues) == 0

        return is_consistent, confidence, issues

    async def detect_hallucination_risk(
        self,
        query: str,
        answer: str,
        sources: List[Source]
    ) -> Tuple[bool, float, str]:
        """
        Detecta risco de alucinação.

        Returns:
            (has_risk, risk_score, explanation)
        """
        risk_factors = []
        risk_score = 0.0

        # 1. Sem fontes = alto risco
        if len(sources) == 0:
            risk_factors.append("No sources available")
            risk_score += 0.5

        # 2. Fontes pouco relevantes = médio risco
        elif all(s.relevance_score < 0.5 for s in sources):
            risk_factors.append("All sources have low relevance")
            risk_score += 0.3

        # 3. Resposta muito longa sem fontes proporcionais
        words_per_source = len(answer.split()) / max(len(sources), 1)
        if words_per_source > 100:
            risk_factors.append(f"High word-to-source ratio: {words_per_source:.0f}")
            risk_score += 0.2

        # 4. Query muito específica com fontes genéricas
        if len(query.split()) > 10 and len(sources) < 3:
            risk_factors.append("Complex query with few sources")
            risk_score += 0.2

        has_risk = risk_score > 0.3
        explanation = "; ".join(risk_factors) if risk_factors else "Low risk"

        return has_risk, min(risk_score, 1.0), explanation


class RAGSystem:
    """
    Sistema RAG completo - Coordena retrieval, generation e verification.
    """

    def __init__(self, llm_client=None):
        self.vector_store = VectorStore()
        self.fact_checker = FactChecker()
        self.llm_client = llm_client  # Cliente LLM (OpenAI, Anthropic, etc)
        self.query_count = 0
        self.cache: Dict[str, RAGResult] = {}

    async def index_knowledge(self, sources: List[Source]):
        """Indexa conhecimento no vector store"""
        await self.vector_store.add_documents(sources)
        return len(sources)

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3,
        source_types: Optional[List[SourceType]] = None
    ) -> List[Source]:
        """
        Retrieval: Busca documentos relevantes.

        Args:
            query: Query do usuário
            top_k: Quantos docs retornar
            min_score: Score mínimo
            source_types: Filtrar por tipos de fonte

        Returns:
            Lista de fontes relevantes
        """
        filters = {}
        if source_types:
            filters["source_type"] = source_types

        sources = await self.vector_store.similarity_search(
            query=query,
            top_k=top_k,
            min_score=min_score,
            filters=filters
        )

        return sources

    async def generate_with_sources(
        self,
        query: str,
        sources: List[Source],
        system_prompt: Optional[str] = None
    ) -> Tuple[str, List[Citation]]:
        """
        Generation: Gera resposta usando fontes como contexto.

        Args:
            query: Query do usuário
            sources: Fontes recuperadas
            system_prompt: System prompt customizado

        Returns:
            (answer, citations)
        """
        # Monta contexto com fontes
        context = "\n\n".join([
            f"[SOURCE {i+1}] ({s.source_type}):\n{s.content}"
            for i, s in enumerate(sources)
        ])

        # System prompt padrão
        if not system_prompt:
            system_prompt = """You are Aurora, an elite AI cyber intelligence analyst.

CRITICAL INSTRUCTIONS:
1. Base your answer ONLY on the provided sources
2. Cite sources explicitly: [SOURCE 1], [SOURCE 2], etc
3. If sources don't contain the answer, say "I don't have enough information"
4. Never make up facts or hallucinate
5. Be precise and factual

Sources are provided below. Use them to answer the question."""

        # Monta prompt completo
        full_prompt = f"""{system_prompt}

SOURCES:
{context}

QUESTION: {query}

ANSWER (with citations):"""

        # TODO: Chamar LLM real (OpenAI, Anthropic, etc)
        # Por enquanto, resposta simples baseada nas fontes
        answer = self._generate_fallback_answer(query, sources)

        # Extrai citações
        citations = self._extract_citations(answer, sources)

        return answer, citations

    def _generate_fallback_answer(self, query: str, sources: List[Source]) -> str:
        """Gera resposta simples sem LLM (fallback)"""
        if not sources:
            return "I don't have enough information to answer this question accurately."

        # Resposta simples concatenando fontes
        answer_parts = [f"Based on {len(sources)} source(s):"]

        for i, source in enumerate(sources[:3], 1):
            # Pega primeiras 200 chars da fonte
            snippet = source.content[:200].strip()
            answer_parts.append(f"\n[SOURCE {i}]: {snippet}...")

        return "\n".join(answer_parts)

    def _extract_citations(
        self,
        answer: str,
        sources: List[Source]
    ) -> List[Citation]:
        """Extrai citações da resposta"""
        citations = []

        # Busca padrões [SOURCE N]
        import re
        citation_pattern = r'\[SOURCE (\d+)\]'
        matches = re.finditer(citation_pattern, answer)

        for match in matches:
            source_num = int(match.group(1))
            if source_num <= len(sources):
                source = sources[source_num - 1]

                # Pega texto ao redor da citação
                start = max(0, match.start() - 50)
                end = min(len(answer), match.end() + 50)
                quoted_text = answer[start:end]

                relevance = self._score_to_relevance(source.relevance_score)

                citation = Citation(
                    citation_id=f"cite_{len(citations)+1}",
                    source=source,
                    quoted_text=quoted_text,
                    relevance=relevance,
                    confidence=source.relevance_score
                )
                citations.append(citation)

        return citations

    def _score_to_relevance(self, score: float) -> RelevanceLevel:
        """Converte score numérico em nível categórico"""
        if score >= 0.9:
            return RelevanceLevel.VERY_HIGH
        elif score >= 0.7:
            return RelevanceLevel.HIGH
        elif score >= 0.5:
            return RelevanceLevel.MEDIUM
        elif score >= 0.3:
            return RelevanceLevel.LOW
        else:
            return RelevanceLevel.VERY_LOW

    async def query(
        self,
        query: str,
        top_k: int = 5,
        min_confidence: float = 0.6,
        source_types: Optional[List[SourceType]] = None
    ) -> RAGResult:
        """
        Query completo RAG: Retrieve → Generate → Verify

        Args:
            query: Query do usuário
            top_k: Quantas fontes buscar
            min_confidence: Confiança mínima aceitável
            source_types: Tipos de fonte para buscar

        Returns:
            RAGResult com resposta, fontes e métricas
        """
        self.query_count += 1

        # 1. RETRIEVE: Busca fontes relevantes
        sources = await self.retrieve(
            query=query,
            top_k=top_k,
            source_types=source_types
        )

        # 2. GENERATE: Gera resposta com citações
        answer, citations = await self.generate_with_sources(
            query=query,
            sources=sources
        )

        # 3. VERIFY: Verifica factualidade
        is_consistent, confidence, issues = await self.fact_checker.check_factual_consistency(
            answer=answer,
            sources=sources
        )

        # 4. CHECK HALLUCINATION: Detecta riscos
        has_risk, risk_score, risk_explanation = await self.fact_checker.detect_hallucination_risk(
            query=query,
            answer=answer,
            sources=sources
        )

        # 5. Monta reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Retrieved {len(sources)} relevant source(s)")
        reasoning_parts.append(f"Generated answer with {len(citations)} citation(s)")
        reasoning_parts.append(f"Confidence: {confidence:.2%}")

        if has_risk:
            reasoning_parts.append(f"⚠️ Hallucination risk detected: {risk_explanation}")

        if issues:
            reasoning_parts.append(f"Issues: {', '.join(issues)}")

        reasoning = " | ".join(reasoning_parts)

        # 6. Monta resultado
        result = RAGResult(
            query=query,
            answer=answer,
            sources=sources,
            citations=citations,
            confidence=confidence,
            has_hallucination_risk=has_risk,
            reasoning=reasoning
        )

        return result

    async def verify_statement(
        self,
        statement: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifica se uma afirmação é factualmente correta.

        Returns:
            {
                "verified": bool,
                "confidence": float,
                "supporting_sources": List[Source],
                "contradicting_sources": List[Source],
                "explanation": str
            }
        """
        # Busca fontes relevantes para a afirmação
        sources = await self.retrieve(query=statement, top_k=10)

        supporting = []
        contradicting = []
        neutral = []

        # TODO: Usar LLM para classificar se fonte suporta/contradiz
        # Por enquanto, classificação simples baseada em keywords
        for source in sources:
            if source.relevance_score > 0.7:
                supporting.append(source)
            elif source.relevance_score < 0.3:
                contradicting.append(source)
            else:
                neutral.append(source)

        verified = len(supporting) > len(contradicting)
        confidence = len(supporting) / max(len(sources), 1)

        explanation = (
            f"Found {len(supporting)} supporting source(s), "
            f"{len(contradicting)} contradicting, "
            f"{len(neutral)} neutral"
        )

        return {
            "verified": verified,
            "confidence": confidence,
            "supporting_sources": [s.to_dict() for s in supporting],
            "contradicting_sources": [s.to_dict() for s in contradicting],
            "explanation": explanation
        }

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema RAG"""
        return {
            "total_queries": self.query_count,
            "documents_indexed": len(self.vector_store.documents),
            "cache_size": len(self.cache),
            "collections": self.vector_store.collection_name
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do sistema RAG"""

    # 1. Inicializa sistema
    rag = RAGSystem()

    # 2. Indexa conhecimento
    sources = [
        Source(
            source_id="cve_001",
            source_type=SourceType.THREAT_INTEL,
            content="CVE-2024-1234: Remote code execution vulnerability in Apache Log4j allows attackers to execute arbitrary code via crafted LDAP queries.",
            metadata={"cve_id": "CVE-2024-1234", "severity": "CRITICAL"},
            url="https://nvd.nist.gov/vuln/detail/CVE-2024-1234"
        ),
        Source(
            source_id="cve_002",
            source_type=SourceType.THREAT_INTEL,
            content="CVE-2024-5678: SQL injection in WordPress plugin allows authentication bypass.",
            metadata={"cve_id": "CVE-2024-5678", "severity": "HIGH"},
            url="https://nvd.nist.gov/vuln/detail/CVE-2024-5678"
        )
    ]

    await rag.index_knowledge(sources)

    # 3. Faz query
    result = await rag.query(
        query="What are the critical vulnerabilities in Log4j?",
        top_k=5,
        min_confidence=0.6,
        source_types=[SourceType.THREAT_INTEL]
    )

    # 4. Usa resultado
    print("ANSWER:", result.answer)
    print("CONFIDENCE:", f"{result.confidence:.2%}")
    print("SOURCES:", len(result.sources))
    print("CITATIONS:", len(result.citations))
    print("HALLUCINATION RISK:", result.has_hallucination_risk)
    print("REASONING:", result.reasoning)

    # 5. Verifica statement
    verification = await rag.verify_statement(
        statement="Log4j has a critical RCE vulnerability",
        context="Security assessment report"
    )
    print("\nVERIFICATION:", verification)


if __name__ == "__main__":
    asyncio.run(example_usage())
