"""
Maximus 2.0 Integrated System - The Complete AI Brain
====================================================

Integração completa de todos os sistemas cognitivos:

1. RAG System - Retrieval-Augmented Generation
2. Chain-of-Thought - Explicit Reasoning
3. Confidence Scoring - Trustworthy AI
4. Memory System - Multi-layer Memory
5. Self-Reflection - Quality Assurance

Este módulo orquestra TODOS os sistemas para criar
a experiência Maximus 2.0 completa.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio

# Importar todos os sistemas
from rag_system import RAGSystem, Source, SourceType, RAGResult
from chain_of_thought import ChainOfThoughtEngine, ReasoningType, ReasoningChain
from confidence_scoring import ConfidenceScoringSystem, ConfidenceScore
from memory_system import MemorySystem, ConversationContext, MemoryType
from self_reflection import SelfReflectionEngine, QualityAssessment


class ResponseMode(str, Enum):
    """Modos de resposta da Maximus"""
    FAST = "fast"              # Resposta rápida, sem raciocínio profundo
    BALANCED = "balanced"      # Balanceado (padrão)
    DEEP = "deep"             # Raciocínio profundo, máxima qualidade
    VERIFIED = "verified"      # Com verificação factual obrigatória


@dataclass
class MaximusRequest:
    """Request completo para Maximus 2.0"""
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    mode: ResponseMode = ResponseMode.BALANCED
    context: Optional[str] = None
    require_sources: bool = False
    require_reasoning: bool = False
    min_confidence: float = 0.6
    max_thinking_time: int = 30  # segundos


@dataclass
class MaximusResponse:
    """Resposta completa da Maximus 2.0"""
    # Core response
    answer: str
    confidence: ConfidenceScore

    # Optional components
    reasoning_chain: Optional[ReasoningChain] = None
    rag_result: Optional[RAGResult] = None
    quality_assessment: Optional[QualityAssessment] = None

    # Metadata
    mode: ResponseMode = ResponseMode.BALANCED
    thinking_time: float = 0.0
    sources_used: int = 0
    tools_called: List[str] = field(default_factory=list)
    memory_recalled: bool = False

    # Warnings & suggestions
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "reasoning": self.reasoning_chain.to_dict() if self.reasoning_chain else None,
            "rag": self.rag_result.to_dict() if self.rag_result else None,
            "quality": self.quality_assessment.to_dict() if self.quality_assessment else None,
            "metadata": {
                "mode": self.mode,
                "thinking_time": self.thinking_time,
                "sources_used": self.sources_used,
                "tools_called": self.tools_called,
                "memory_recalled": self.memory_recalled
            },
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp
        }


class MaximusIntegratedSystem:
    """
    Sistema Integrado Maximus 2.0

    O CÉREBRO COMPLETO - orquestra todos os subsistemas cognitivos.
    """

    def __init__(
        self,
        llm_client=None,
        enable_rag: bool = True,
        enable_reasoning: bool = True,
        enable_memory: bool = True,
        enable_reflection: bool = True
    ):
        # Initialize all subsystems
        self.rag_system = RAGSystem(llm_client) if enable_rag else None
        self.reasoning_engine = ChainOfThoughtEngine(llm_client) if enable_reasoning else None
        self.confidence_scorer = ConfidenceScoringSystem()
        self.memory_system = MemorySystem() if enable_memory else None
        self.reflection_engine = SelfReflectionEngine(llm_client) if enable_reflection else None

        self.llm_client = llm_client

        # Stats
        self.total_queries = 0
        self.total_thinking_time = 0.0

    async def initialize(self):
        """Initialize async components"""
        if self.memory_system:
            await self.memory_system.initialize()

    async def process(self, request: MaximusRequest) -> MaximusResponse:
        """
        Processa request completo através de TODOS os sistemas.

        Flow:
        1. Memory: Recall context
        2. RAG: Retrieve relevant knowledge (if needed)
        3. Reasoning: Chain-of-Thought (if needed)
        4. Generation: Generate answer
        5. Confidence: Score confidence
        6. Reflection: Assess quality
        7. Memory: Store new memories
        8. Return: Complete response
        """
        start_time = datetime.now()
        self.total_queries += 1

        warnings = []
        suggestions = []
        tools_called = []

        # STEP 1: MEMORY RECALL
        memory_recalled = False
        context = None

        if self.memory_system and request.session_id:
            try:
                context = await self.memory_system.working_memory.get_context(request.session_id)
                memory_recalled = context is not None
            except Exception as e:
                warnings.append(f"Memory recall failed: {str(e)}")

        # STEP 2: RAG (if sources required or verified mode)
        rag_result = None
        sources = []

        if self.rag_system and (request.require_sources or request.mode == ResponseMode.VERIFIED):
            try:
                rag_result = await self.rag_system.query(
                    query=request.query,
                    top_k=5,
                    min_confidence=request.min_confidence
                )
                sources = rag_result.sources

                if rag_result.has_hallucination_risk:
                    warnings.append("⚠️ Hallucination risk detected - verify answer")

            except Exception as e:
                warnings.append(f"RAG failed: {str(e)}")

        # STEP 3: REASONING (if deep mode or reasoning required)
        reasoning_chain = None

        if self.reasoning_engine and (request.require_reasoning or request.mode == ResponseMode.DEEP):
            try:
                reasoning_type = (
                    ReasoningType.SELF_CRITIQUE if request.mode == ResponseMode.DEEP
                    else ReasoningType.LINEAR
                )

                reasoning_chain = await self.reasoning_engine.reason(
                    problem=request.query,
                    reasoning_type=reasoning_type,
                    context=request.context,
                    max_steps=10
                )
            except Exception as e:
                warnings.append(f"Reasoning failed: {str(e)}")

        # STEP 4: GENERATE ANSWER
        # Priority: RAG answer > Reasoning answer > Fallback
        answer = ""

        if rag_result and rag_result.answer:
            answer = rag_result.answer
        elif reasoning_chain and reasoning_chain.final_answer:
            answer = reasoning_chain.final_answer
        else:
            # Fallback: simular resposta
            answer = f"Maximus is processing your query: {request.query}\n\n⚠️ LLM not configured for full capabilities."

        # STEP 5: CONFIDENCE SCORING
        confidence_score = self.confidence_scorer.score(
            answer=answer,
            query=request.query,
            sources=[s.to_dict() for s in sources] if sources else None,
            reasoning_steps=(
                [s.to_dict() for s in reasoning_chain.steps]
                if reasoning_chain else None
            ),
            query_type="general"
        )

        # Add confidence warnings
        if not confidence_score.is_reliable(request.min_confidence):
            warnings.append(f"⚠️ Confidence below threshold: {confidence_score.score:.0%}")

        warnings.extend(confidence_score.warnings)

        # STEP 6: SELF-REFLECTION (quality assessment)
        quality_assessment = None

        if self.reflection_engine:
            try:
                quality_assessment = await self.reflection_engine.assess_quality(
                    query=request.query,
                    answer=answer,
                    sources=[s.to_dict() for s in sources] if sources else None,
                    reasoning_steps=(
                        [s.to_dict() for s in reasoning_chain.steps]
                        if reasoning_chain else None
                    )
                )

                # Add quality suggestions
                if quality_assessment.can_improve:
                    suggestions.extend(quality_assessment.improvement_suggestions)

                # If quality is poor, add warning
                if quality_assessment.overall_score < 0.5:
                    warnings.append("⚠️ Low quality answer detected")

            except Exception as e:
                warnings.append(f"Quality assessment failed: {str(e)}")

        # STEP 7: MEMORY STORAGE
        if self.memory_system and request.session_id:
            try:
                # Update context with new message
                new_message = {
                    "role": "user",
                    "content": request.query,
                    "timestamp": datetime.now().isoformat()
                }

                if context:
                    await self.memory_system.working_memory.update_context(
                        session_id=request.session_id,
                        new_message=new_message
                    )
                else:
                    # Create new context
                    new_context = ConversationContext(
                        session_id=request.session_id,
                        user_id=request.user_id,
                        messages=[new_message]
                    )
                    await self.memory_system.working_memory.store_context(
                        session_id=request.session_id,
                        context=new_context
                    )

                # Store response
                response_message = {
                    "role": "assistant",
                    "content": answer,
                    "confidence": confidence_score.score,
                    "timestamp": datetime.now().isoformat()
                }

                await self.memory_system.working_memory.update_context(
                    session_id=request.session_id,
                    new_message=response_message
                )

            except Exception as e:
                warnings.append(f"Memory storage failed: {str(e)}")

        # STEP 8: BUILD RESPONSE
        thinking_time = (datetime.now() - start_time).total_seconds()
        self.total_thinking_time += thinking_time

        response = MaximusResponse(
            answer=answer,
            confidence=confidence_score,
            reasoning_chain=reasoning_chain,
            rag_result=rag_result,
            quality_assessment=quality_assessment,
            mode=request.mode,
            thinking_time=thinking_time,
            sources_used=len(sources),
            tools_called=tools_called,
            memory_recalled=memory_recalled,
            warnings=warnings,
            suggestions=suggestions
        )

        return response

    async def process_with_tools(
        self,
        request: MaximusRequest,
        available_tools: List[Dict[str, Any]]
    ) -> MaximusResponse:
        """
        Processa com tool calling (para integração com LLM).

        TODO: Integrar com sistema de tool calling existente
        """
        # Por enquanto, usa process normal
        return await self.process(request)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema integrado"""
        stats = {
            "total_queries": self.total_queries,
            "avg_thinking_time": (
                self.total_thinking_time / self.total_queries
                if self.total_queries > 0 else 0
            ),
            "systems_enabled": {
                "rag": self.rag_system is not None,
                "reasoning": self.reasoning_engine is not None,
                "memory": self.memory_system is not None,
                "reflection": self.reflection_engine is not None
            }
        }

        # Add subsystem stats
        if self.rag_system:
            stats["rag_stats"] = self.rag_system.get_stats()

        if self.confidence_scorer:
            stats["confidence_stats"] = self.confidence_scorer.get_stats()

        if self.reflection_engine:
            stats["quality_stats"] = self.reflection_engine.get_stats()

        return stats

    async def shutdown(self):
        """Shutdown all systems"""
        if self.memory_system:
            await self.memory_system.shutdown()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do sistema integrado Maximus 2.0"""

    # Initialize Maximus
    maximus = MaximusIntegratedSystem(
        enable_rag=True,
        enable_reasoning=True,
        enable_memory=True,
        enable_reflection=True
    )

    await maximus.initialize()

    # Exemplo 1: Query rápida (FAST mode)
    print("=== EXAMPLE 1: FAST MODE ===")
    request1 = MaximusRequest(
        query="What is CVE-2024-1234?",
        session_id="user_123",
        mode=ResponseMode.FAST
    )

    response1 = await maximus.process(request1)
    print(f"Answer: {response1.answer[:200]}...")
    print(f"Confidence: {response1.confidence.score:.2%}")
    print(f"Thinking time: {response1.thinking_time:.2f}s")

    # Exemplo 2: Query profunda (DEEP mode com reasoning)
    print("\n=== EXAMPLE 2: DEEP MODE ===")
    request2 = MaximusRequest(
        query="What are the top 3 cyber threats in 2024 and how can I protect against them?",
        session_id="user_123",
        mode=ResponseMode.DEEP,
        require_sources=True,
        require_reasoning=True
    )

    response2 = await maximus.process(request2)
    print(f"Answer: {response2.answer[:200]}...")
    print(f"Confidence: {response2.confidence.score:.2%}")
    print(f"Quality: {response2.quality_assessment.overall_level if response2.quality_assessment else 'N/A'}")
    print(f"Sources: {response2.sources_used}")
    print(f"Reasoning steps: {len(response2.reasoning_chain.steps) if response2.reasoning_chain else 0}")
    print(f"Thinking time: {response2.thinking_time:.2f}s")

    if response2.warnings:
        print(f"Warnings: {response2.warnings}")

    if response2.suggestions:
        print(f"Suggestions: {response2.suggestions}")

    # Exemplo 3: Query verificada (VERIFIED mode - máxima confiança)
    print("\n=== EXAMPLE 3: VERIFIED MODE ===")
    request3 = MaximusRequest(
        query="Is 185.220.101.23 a malicious IP?",
        mode=ResponseMode.VERIFIED,
        min_confidence=0.8
    )

    response3 = await maximus.process(request3)
    print(f"Answer: {response3.answer[:200]}...")
    print(f"Confidence: {response3.confidence.score:.2%}")
    print(f"Hallucination risk: {response3.rag_result.has_hallucination_risk if response3.rag_result else 'N/A'}")

    # Stats
    print("\n=== SYSTEM STATS ===")
    stats = aurora.get_stats()
    print(json.dumps(stats, indent=2, default=str))

    # Cleanup
    await maximus.shutdown()


if __name__ == "__main__":
    asyncio.run(example_usage())
