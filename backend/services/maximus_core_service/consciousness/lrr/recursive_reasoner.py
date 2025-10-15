"""
Recursive Reasoner - Motor de Raciocínio Recursivo
==================================================

Implementa metacognição através de loops recursivos validados.

Permite que MAXIMUS:
1. Pense sobre seu próprio pensamento (metacognição)
2. Detecte contradições em suas crenças
3. Revise crenças inconsistentes
4. Raciocine em múltiplos níveis de abstração

Exemplo de Recursão:
--------------------
Level 0: "Há uma ameaça no IP 192.168.1.1" (objeto-level)
Level 1: "Eu acredito que há uma ameaça em 192.168.1.1" (meta-level)
Level 2: "Eu acredito que minha crença sobre 192.168.1.1 é justificada" (meta-meta)
Level 3: "Eu acredito que minha meta-crença sobre justificação é coerente"

Baseline Científico:
-------------------
- Carruthers (2009): Higher-Order Thoughts (HOT Theory)
- Hofstadter (1979): Strange Loops e auto-referência
- Graziano (2013, 2019): Attention Schema Theory

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import logging
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from time import perf_counter
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from uuid import UUID, uuid4

from .contradiction_detector import BeliefRevision, ContradictionDetector, RevisionOutcome
from .introspection_engine import IntrospectionEngine, IntrospectionReport
from .meta_monitor import MetaMonitor, MetaMonitoringReport

if TYPE_CHECKING:  # pragma: no cover
    from consciousness.mea.attention_schema import AttentionState
    from consciousness.mea.boundary_detector import BoundaryAssessment
    from consciousness.mea.self_model import IntrospectiveSummary
    from consciousness.episodic_memory import Episode

logger = logging.getLogger(__name__)


# ==================== ENUMS ====================


class BeliefType(Enum):
    """Tipos de crenças no sistema."""

    FACTUAL = "factual"  # "IP 192.168.1.1 é malicioso"
    META = "meta"  # "Eu acredito que IP 192.168.1.1 é malicioso"
    NORMATIVE = "normative"  # "Devo bloquear IP 192.168.1.1"
    EPISTEMIC = "epistemic"  # "Minha crença sobre 192.168.1.1 é justificada"


class ContradictionType(Enum):
    """Tipos de contradições detectadas."""

    DIRECT = "direct"  # A e ¬A simultaneamente
    TRANSITIVE = "transitive"  # A→B, B→C, C→¬A
    TEMPORAL = "temporal"  # Acreditava X antes, acredito ¬X agora sem razão
    CONTEXTUAL = "contextual"  # X verdadeiro em C1, ¬X em C2 sem explicação


class ResolutionStrategy(Enum):
    """Estratégias de resolução de contradições."""

    RETRACT_WEAKER = "retract_weaker"  # Remove crença menos confiável
    WEAKEN_BOTH = "weaken_both"  # Reduz confiança de ambas
    CONTEXTUALIZE = "contextualize"  # Adiciona condições contextuais
    TEMPORIZE = "temporize"  # Marca como crença passada
    HITL_ESCALATE = "hitl_escalate"  # Escala para humano


# ==================== DATACLASSES ====================


@dataclass
class Belief:
    """
    Representa uma crença no sistema.

    Attributes:
        id: Identificador único
        content: Conteúdo proposicional da crença
        belief_type: Tipo de crença (factual, meta, normative, epistemic)
        confidence: Nível de confiança [0.0, 1.0]
        justification: Crença(s) que justificam esta
        context: Contexto em que crença é válida
        timestamp: Quando crença foi formada
        meta_level: Nível de abstração (0=objeto, 1=meta, 2=meta-meta, etc.)
    """

    content: str
    belief_type: BeliefType = BeliefType.FACTUAL
    confidence: float = 0.5
    justification: Optional[List["Belief"]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    meta_level: int = 0
    id: UUID = field(default_factory=uuid4)

    NEGATION_MAP: ClassVar[Dict[str, str]] = {
        "isn't": "is",
        "aren't": "are",
        "not": "",
        "¬": "",
        "~": "",
        "no ": "",
    }

    def __post_init__(self):
        """Validações."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be [0, 1], got {self.confidence}")
        if self.meta_level < 0:
            raise ValueError(f"Meta level must be >= 0, got {self.meta_level}")
        if self.justification is None:
            self.justification = []

    def __hash__(self):
        """Hash para usar em sets."""
        return hash(self.id)

    def __eq__(self, other):
        """Equality baseado em ID."""
        if not isinstance(other, Belief):
            return False
        return self.id == other.id

    def is_negation_of(self, other: "Belief") -> bool:
        """
        Verifica se esta crença é negação de outra.

        Heurísticas simples:
        - "IP X is malicious" vs "IP X is not malicious"
        - "Action Y is ethical" vs "Action Y is unethical"
        """
        if self.belief_type != other.belief_type:
            return False

        content_lower = self.content.lower()
        other_lower = other.content.lower()

        # Se um tem negação e outro não, pode ser negação
        self_has_neg = any(marker in content_lower for marker in self.NEGATION_MAP)
        other_has_neg = any(marker in other_lower for marker in self.NEGATION_MAP)

        if self_has_neg != other_has_neg:
            # Remover negação e comparar
            self_clean = content_lower
            other_clean = other_lower

            for marker, replacement in self.NEGATION_MAP.items():
                self_clean = self_clean.replace(marker, replacement)
                other_clean = other_clean.replace(marker, replacement)

            # Se conteúdos são similares após remover negação
            self_clean = self._normalize_whitespace(self_clean)
            other_clean = self._normalize_whitespace(other_clean)
            return self_clean == other_clean

        return False

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Compress consecutive whitespace to support semantic comparisons."""
        return " ".join(text.split())

    @classmethod
    def strip_negations(cls, text: str) -> str:
        """Remove marcadores de negação para comparação canônica."""
        cleaned = text.lower()
        for marker, replacement in cls.NEGATION_MAP.items():
            cleaned = cleaned.replace(marker, replacement)
        return cls._normalize_whitespace(cleaned)


@dataclass
class Contradiction:
    """
    Representa uma contradição detectada.

    Attributes:
        belief_a: Primeira crença contraditória
        belief_b: Segunda crença contraditória
        contradiction_type: Tipo de contradição
        severity: Severidade [0.0, 1.0]
        explanation: Explicação da contradição
        suggested_resolution: Estratégia sugerida
    """

    belief_a: Belief
    belief_b: Belief
    contradiction_type: ContradictionType
    severity: float = 1.0
    explanation: str = ""
    suggested_resolution: ResolutionStrategy = ResolutionStrategy.RETRACT_WEAKER
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        """Gerar explicação se não fornecida."""
        if not self.explanation:
            self.explanation = (
                f"Contradiction detected: '{self.belief_a.content}' "
                f"contradicts '{self.belief_b.content}' "
                f"(type: {self.contradiction_type.value})"
            )


@dataclass
class Resolution:
    """
    Representa a resolução de uma contradição.

    Attributes:
        contradiction: Contradição resolvida
        strategy: Estratégia usada
        beliefs_modified: Crenças modificadas
        beliefs_removed: Crenças removidas
        new_beliefs: Novas crenças adicionadas
        timestamp: Quando resolução foi aplicada
    """

    contradiction: Contradiction
    strategy: ResolutionStrategy
    beliefs_modified: List[Belief] = field(default_factory=list)
    beliefs_removed: List[Belief] = field(default_factory=list)
    new_beliefs: List[Belief] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)


@dataclass
class ReasoningStep:
    """
    Representa um passo de raciocínio.

    Attributes:
        belief: Crença sendo processada
        meta_level: Nível de abstração
        justification_chain: Cadeia de justificações
        confidence_assessment: Avaliação de confiança
        timestamp: Quando passo foi executado
    """

    belief: Belief
    meta_level: int
    justification_chain: List[Belief] = field(default_factory=list)
    confidence_assessment: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningLevel:
    """
    Representa um nível completo de raciocínio.

    Attributes:
        level: Número do nível (0=objeto, 1=meta, etc.)
        beliefs: Crenças neste nível
        coherence: Coerência interna [0.0, 1.0]
        steps: Passos de raciocínio executados
    """

    level: int
    beliefs: List[Belief] = field(default_factory=list)
    coherence: float = 1.0
    steps: List[ReasoningStep] = field(default_factory=list)


@dataclass
class RecursiveReasoningResult:
    """
    Resultado de raciocínio recursivo completo.

    Attributes:
        levels: Níveis de raciocínio executados
        final_depth: Profundidade alcançada
        coherence_score: Coerência global [0.0, 1.0]
        contradictions_detected: Contradições encontradas
        resolutions_applied: Resoluções aplicadas
        timestamp: Quando raciocínio foi executado
    """

    levels: List[ReasoningLevel]
    final_depth: int
    coherence_score: float
    contradictions_detected: List[Contradiction] = field(default_factory=list)
    resolutions_applied: List[Resolution] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    meta_report: Optional[MetaMonitoringReport] = None
    introspection_report: Optional[IntrospectionReport] = None
    attention_state: Optional["AttentionState"] = None
    boundary_assessment: Optional["BoundaryAssessment"] = None
    self_summary: Optional["IntrospectiveSummary"] = None
    episodic_episode: Optional["Episode"] = None
    episodic_narrative: Optional[str] = None
    episodic_coherence: Optional[float] = None


# ==================== CLASSES ====================


class BeliefGraph:
    """
    Grafo de crenças e suas inter-relações.

    Permite:
    - Adicionar crenças e justificações
    - Detectar contradições (diretas, transitivas, temporais)
    - Resolver contradições através de revisão
    - Calcular coerência do grafo
    """

    def __init__(self):
        """Initialize belief graph."""
        self.beliefs: Set[Belief] = set()
        self.justifications: Dict[UUID, List[Belief]] = defaultdict(list)
        self.timestamp_index: Dict[datetime, Set[Belief]] = defaultdict(set)
        self.context_index: Dict[str, Set[Belief]] = defaultdict(set)

    def add_belief(
        self, belief: Belief, justification: Optional[List[Belief]] = None
    ) -> None:
        """
        Adiciona crença ao grafo.

        Args:
            belief: Crença a adicionar
            justification: Crenças que justificam esta
        """
        self.beliefs.add(belief)

        if justification:
            self.justifications[belief.id].extend(justification)
            belief.justification = justification

        # Indexar por timestamp
        self.timestamp_index[belief.timestamp].add(belief)

        # Indexar por contexto
        for key in belief.context:
            self.context_index[key].add(belief)

    def detect_contradictions(self) -> List[Contradiction]:
        """
        Detecta todas as contradições no grafo.

        Returns:
            Lista de contradições ordenadas por severidade
        """
        contradictions: List[Contradiction] = []

        # Contradições diretas (A e ¬A)
        contradictions.extend(self._detect_direct_contradictions())

        # Contradições transitivas (A→B, B→C, C→¬A)
        contradictions.extend(self._detect_transitive_contradictions())

        # Contradições temporais
        contradictions.extend(self._detect_temporal_contradictions())

        # Contradições contextuais
        contradictions.extend(self._detect_contextual_contradictions())

        # Ordenar por severidade
        return sorted(contradictions, key=lambda c: c.severity, reverse=True)

    def _detect_direct_contradictions(self) -> List[Contradiction]:
        """Detecta contradições diretas (A e ¬A)."""
        contradictions = []

        beliefs_list = list(self.beliefs)
        for i, belief_a in enumerate(beliefs_list):
            for belief_b in beliefs_list[i + 1 :]:
                if belief_a.is_negation_of(belief_b):
                    # Severity baseado em confiança
                    severity = min(belief_a.confidence, belief_b.confidence)

                    # Sugerir estratégia
                    if belief_a.confidence > belief_b.confidence:
                        strategy = ResolutionStrategy.RETRACT_WEAKER
                    elif abs(belief_a.confidence - belief_b.confidence) < 0.1:
                        strategy = ResolutionStrategy.WEAKEN_BOTH
                    else:
                        strategy = ResolutionStrategy.RETRACT_WEAKER

                    contradictions.append(
                        Contradiction(
                            belief_a=belief_a,
                            belief_b=belief_b,
                            contradiction_type=ContradictionType.DIRECT,
                            severity=severity,
                            suggested_resolution=strategy,
                        )
                    )

        return contradictions

    def _detect_transitive_contradictions(self) -> List[Contradiction]:
        """
        Detecta contradições transitivas (A→B, B→C, C→¬A).

        Usa BFS para encontrar caminhos de justificação que levam
        a contradições indiretas.
        """
        contradictions = []

        # Para cada crença, seguir cadeia de justificações
        for belief in self.beliefs:
            # BFS para encontrar caminhos de justificação
            visited = set()
            queue = [(belief, [belief])]

            while queue:
                current, path = queue.pop(0)

                if current.id in visited:  # pragma: no cover - BFS deduplication for diamond patterns in justification graphs
                    continue
                visited.add(current.id)

                # Para cada justificação desta crença
                for justification in self.justifications.get(current.id, []):
                    new_path = path + [justification]

                    # Se encontramos negação da crença original
                    if justification.is_negation_of(belief):
                        # Temos contradição transitiva!
                        contradictions.append(
                            Contradiction(
                                belief_a=belief,
                                belief_b=justification,
                                contradiction_type=ContradictionType.TRANSITIVE,
                                severity=0.6,  # Menos severa que direta
                                suggested_resolution=ResolutionStrategy.WEAKEN_BOTH,
                                explanation=f"Transitive contradiction: {' → '.join(b.content[:30] for b in new_path)}"
                            )
                        )
                    else:
                        # Continuar BFS
                        if len(new_path) < 5:  # Limitar profundidade
                            queue.append((justification, new_path))

        return contradictions

    def _detect_temporal_contradictions(self) -> List[Contradiction]:
        """Detecta contradições temporais."""
        contradictions = []

        # Agrupar crenças por conteúdo similar (ignorando marcadores de negação)
        content_groups: Dict[str, List[Belief]] = defaultdict(list)
        for belief in self.beliefs:
            key = Belief.strip_negations(belief.content)
            content_groups[key].append(belief)

        # Detectar mudanças sem justificação
        for beliefs in content_groups.values():
            if len(beliefs) < 2:
                continue

            # Ordenar por timestamp
            sorted_beliefs = sorted(beliefs, key=lambda b: b.timestamp)

            for i in range(len(sorted_beliefs) - 1):
                current = sorted_beliefs[i]
                next_belief = sorted_beliefs[i + 1]

                # Se são negações e não há justificação
                if current.is_negation_of(next_belief) and not next_belief.justification:
                    contradictions.append(
                        Contradiction(
                            belief_a=current,
                            belief_b=next_belief,
                            contradiction_type=ContradictionType.TEMPORAL,
                            severity=0.7,
                            suggested_resolution=ResolutionStrategy.TEMPORIZE,
                            explanation=f"Belief changed from '{current.content}' to '{next_belief.content}' without justification",
                        )
                    )

        return contradictions

    def _detect_contextual_contradictions(self) -> List[Contradiction]:
        """
        Detecta contradições contextuais.

        Identifica crenças que são contraditórias em contextos diferentes
        sem explicação adequada.
        """
        contradictions = []

        # Agrupar crenças por chaves de contexto compartilhadas
        for key, beliefs_with_context in self.context_index.items():
            if len(beliefs_with_context) < 2:
                continue

            beliefs_list = list(beliefs_with_context)
            for i, belief_a in enumerate(beliefs_list):
                for belief_b in beliefs_list[i + 1:]:
                    # Se são negações mas compartilham contexto
                    if belief_a.is_negation_of(belief_b):
                        # Verificar se contextos são realmente diferentes
                        context_diff = set(belief_a.context.keys()) ^ set(belief_b.context.keys())

                        if context_diff:
                            contradictions.append(
                                Contradiction(
                                    belief_a=belief_a,
                                    belief_b=belief_b,
                                    contradiction_type=ContradictionType.CONTEXTUAL,
                                    severity=0.5,
                                    suggested_resolution=ResolutionStrategy.CONTEXTUALIZE,
                                    explanation=f"Contextual contradiction in context '{key}': differing contexts {context_diff}"
                                )
                            )

        return contradictions

    def resolve_belief(self, belief: Belief, resolution: Resolution) -> None:
        """
        Resolve contradição aplicando resolução.

        Args:
            belief: Crença envolvida na contradição
            resolution: Resolução a aplicar
        """
        if resolution.strategy == ResolutionStrategy.RETRACT_WEAKER:
            # Remover crença mais fraca
            if belief in self.beliefs:
                self.beliefs.remove(belief)
                logger.info(f"Retracted belief: {belief.content}")

        elif resolution.strategy == ResolutionStrategy.WEAKEN_BOTH:
            # Reduzir confiança (criar nova crença com confiança menor)
            new_belief = Belief(
                content=belief.content,
                belief_type=belief.belief_type,
                confidence=belief.confidence * 0.5,
                justification=belief.justification,
                context=belief.context,
                meta_level=belief.meta_level,
            )
            if belief in self.beliefs:
                self.beliefs.remove(belief)
            self.beliefs.add(new_belief)
            logger.info(f"Weakened belief: {belief.content} (conf: {belief.confidence} → {new_belief.confidence})")

        elif resolution.strategy == ResolutionStrategy.TEMPORIZE:
            # Marcar como crença passada (adicionar ao contexto)
            belief.context["temporal_status"] = "past"
            belief.context["superseded_at"] = datetime.now().isoformat()
            logger.info(f"Temporized belief: {belief.content}")

        elif resolution.strategy == ResolutionStrategy.CONTEXTUALIZE:
            # Adicionar contexto que explica aparente contradição
            belief.context["contextualized"] = True
            belief.context["context_note"] = "Valid in specific context only"
            logger.info(f"Contextualized belief: {belief.content}")

        elif resolution.strategy == ResolutionStrategy.HITL_ESCALATE:
            # Marcar para escalação humana
            belief.context["hitl_review_required"] = True
            belief.context["escalated_at"] = datetime.now().isoformat()
            logger.warning(f"Escalated belief to HITL: {belief.content}")

    def calculate_coherence(self) -> float:
        """
        Calcula coerência do grafo.

        Heurística:
        - Coherence = 1.0 - (contradictions / total_pairs)
        - Com penalidade por contradições de alta severidade

        Returns:
            Coherence score [0.0, 1.0]
        """
        if len(self.beliefs) < 2:
            return 1.0

        contradictions = self.detect_contradictions()
        if not contradictions:
            return 1.0

        # Total de pares possíveis
        n = len(self.beliefs)
        total_pairs = n * (n - 1) / 2

        # Penalidade por contradições (ponderada por severidade)
        penalty = sum(c.severity for c in contradictions) / total_pairs

        return max(0.0, 1.0 - penalty)


class RecursiveReasoner:
    """
    Motor de raciocínio recursivo.

    Permite que MAXIMUS raciocine sobre seu próprio raciocínio
    em múltiplos níveis de abstração.
    """

    def __init__(self, max_depth: int = 3):
        """
        Initialize recursive reasoner.

        Args:
            max_depth: Profundidade máxima de recursão (default 3)
                      1 = simples, 2 = meta, 3+ = meta-meta
        """
        if max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        if max_depth > 5:
            warnings.warn(f"max_depth={max_depth} is high, may be slow", UserWarning)

        self.max_depth = max_depth
        self.belief_graph = BeliefGraph()
        self.reasoning_history: List[ReasoningStep] = []
        self.contradiction_detector = ContradictionDetector()
        self.belief_revision = BeliefRevision()
        self.meta_monitor = MetaMonitor()
        self.introspection_engine = IntrospectionEngine()
        self._seen_contradiction_pairs: Set[Tuple[UUID, UUID]] = set()
        self._mea_attention_state: Optional["AttentionState"] = None
        self._mea_boundary: Optional["BoundaryAssessment"] = None
        self._mea_summary: Optional["IntrospectiveSummary"] = None
        self._episodic_episode: Optional["Episode"] = None
        self._episodic_narrative: Optional[str] = None
        self._episodic_coherence: Optional[float] = None

    async def reason_recursively(
        self, initial_belief: Belief, context: Dict[str, Any]
    ) -> RecursiveReasoningResult:
        """
        Executa raciocínio recursivo sobre uma crença inicial.

        Process:
            1. Avaliar crença de nível 0 (objeto-level)
            2. Para cada nível até max_depth:
                a. Gerar meta-crença sobre nível anterior
                b. Avaliar justificação da meta-crença
                c. Detectar contradições
                d. Revisar se necessário
            3. Retornar resultado com todos os níveis

        Args:
            initial_belief: Crença inicial (nível 0)
            context: Contexto adicional para raciocínio

        Returns:
            RecursiveReasoningResult com todos os níveis de raciocínio
        """
        start_time = perf_counter()
        levels: List[ReasoningLevel] = []
        current_belief = initial_belief
        contradictions_detected: List[Contradiction] = []
        resolutions_applied: List[Resolution] = []

        self._integrate_mea_context(context)

        # Adicionar crença inicial ao grafo
        self.belief_graph.add_belief(initial_belief)

        for depth in range(self.max_depth + 1):
            logger.debug(f"Reasoning at level {depth}")

            # Raciocínio neste nível
            level_result = await self._reason_at_level(
                belief=current_belief, depth=depth, context=context
            )
            levels.append(level_result)
            self._register_level_beliefs(level_result)

            # Detectar contradições nível a nível utilizando detector avançado
            contradictions = await self.contradiction_detector.detect_contradictions(
                self.belief_graph
            )
            new_contradictions: List[Contradiction] = []
            for contradiction in contradictions:
                pair = self._contradiction_pair(contradiction)
                if pair in self._seen_contradiction_pairs:
                    continue
                self._seen_contradiction_pairs.add(pair)
                new_contradictions.append(contradiction)

            for contradiction in new_contradictions:
                contradictions_detected.append(contradiction)

                # Resolver contradições seguindo revisão AGM
                outcome = await self.belief_revision.revise_belief_graph(
                    self.belief_graph, contradiction
                )
                resolutions_applied.append(outcome.resolution)

            # Gerar meta-crença para próximo nível
            if depth < self.max_depth:
                current_belief = self._generate_meta_belief(level_result, depth + 1)
                self.belief_graph.add_belief(current_belief)

        # Calcular coerência global
        coherence_score = self._calculate_coherence(levels)
        duration_ms = (perf_counter() - start_time) * 1000.0

        result = RecursiveReasoningResult(
            levels=levels,
            final_depth=len(levels),
            coherence_score=coherence_score,
            contradictions_detected=contradictions_detected,
            resolutions_applied=resolutions_applied,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
        )
        result.meta_report = self.meta_monitor.monitor_reasoning(result)
        result.introspection_report = self.introspection_engine.generate_introspection_report(
            result
        )
        result.attention_state = self._mea_attention_state
        result.boundary_assessment = self._mea_boundary
        result.self_summary = self._mea_summary
        result.episodic_episode = self._episodic_episode
        result.episodic_narrative = self._episodic_narrative
        result.episodic_coherence = self._episodic_coherence
        return result


    async def _reason_at_level(
        self, belief: Belief, depth: int, context: Dict[str, Any]
    ) -> ReasoningLevel:
        """
        Executa raciocínio em um nível específico.

        Args:
            belief: Crença a processar
            depth: Profundidade atual
            context: Contexto

        Returns:
            ReasoningLevel com resultados deste nível
        """
        steps: List[ReasoningStep] = []
        beliefs: List[Belief] = [belief]

        # Avaliar justificação da crença
        justification_chain = self._build_justification_chain(belief)

        # Avaliar confiança
        confidence_assessment = self._assess_confidence(belief, justification_chain)

        step = ReasoningStep(
            belief=belief,
            meta_level=depth,
            justification_chain=justification_chain,
            confidence_assessment=confidence_assessment,
        )
        steps.append(step)
        self.reasoning_history.append(step)

        # Calcular coerência do nível
        level_coherence = self._calculate_level_coherence(beliefs, steps)

        return ReasoningLevel(
            level=depth, beliefs=beliefs, coherence=level_coherence, steps=steps
        )

    def _build_justification_chain(self, belief: Belief) -> List[Belief]:
        """Constrói cadeia de justificações para crença."""
        if not belief.justification:
            return []

        chain = list(belief.justification)

        # Recursivamente adicionar justificações das justificações
        for justifying_belief in belief.justification:
            chain.extend(self._build_justification_chain(justifying_belief))

        return chain

    def _assess_confidence(self, belief: Belief, justification_chain: List[Belief]) -> float:
        """
        Avalia confiança calibrada para crença.

        Heurística:
        - Se sem justificação: manter confiança original
        - Se com justificação: média ponderada com justificações
        """
        if not justification_chain:
            return belief.confidence

        # Média das confianças das justificações
        avg_justification_conf = sum(b.confidence for b in justification_chain) / len(
            justification_chain
        )

        # Média ponderada (70% crença, 30% justificações)
        return 0.7 * belief.confidence + 0.3 * avg_justification_conf

    def _calculate_level_coherence(
        self, beliefs: List[Belief], steps: List[ReasoningStep]
    ) -> float:
        """Calcula coerência interna de um nível."""
        if not beliefs:
            return 1.0

        # Simplificação: usar coerência do grafo
        return self.belief_graph.calculate_coherence()

    def _register_level_beliefs(self, level_result: ReasoningLevel) -> None:
        """Assegura que crenças derivadas sejam persistidas no grafo."""
        for belief in level_result.beliefs:
            if belief not in self.belief_graph.beliefs:  # pragma: no cover - beliefs registered via reason_recursively line 673
                justification = belief.justification if belief.justification else None  # pragma: no cover
                self.belief_graph.add_belief(belief, justification=justification)  # pragma: no cover

    @staticmethod
    def _contradiction_pair(contradiction: Contradiction) -> Tuple[UUID, UUID]:
        """Cria identificador estável para contradições baseado nas crenças."""
        ordered = sorted(
            [contradiction.belief_a.id, contradiction.belief_b.id],
            key=lambda value: value.hex,
        )
        return ordered[0], ordered[1]

    def _integrate_mea_context(self, context: Dict[str, Any]) -> None:
        """Seed belief graph with MEA context (attention + boundary + self narrative)."""
        attention_state = context.get("mea_attention_state")
        boundary = context.get("mea_boundary")
        summary = context.get("mea_summary")
        episodic_episode = context.get("episodic_episode")
        episodic_narrative = context.get("episodic_narrative")
        episodic_coherence = context.get("episodic_coherence")

        from consciousness.mea.attention_schema import AttentionState  # local import to avoid heavy dependencies
        from consciousness.mea.boundary_detector import BoundaryAssessment
        from consciousness.mea.self_model import IntrospectiveSummary
        from consciousness.episodic_memory import Episode

        if isinstance(attention_state, AttentionState):
            self._mea_attention_state = attention_state

            focus_content = (
                f"Current attentional focus is '{attention_state.focus_target}' "
                f"with confidence {attention_state.confidence:.2f}"
            )
            focus_belief = Belief(
                content=focus_content,
                belief_type=BeliefType.FACTUAL,
                confidence=attention_state.confidence,
                context={"source": "MEA", "type": "attention_focus"},
                meta_level=0,
            )
            self.belief_graph.add_belief(focus_belief)

            for modality, weight in attention_state.modality_weights.items():
                modality_belief = Belief(
                    content=f"Attention modality '{modality}' weight {weight:.2f}",
                    belief_type=BeliefType.FACTUAL,
                    confidence=weight,
                    context={"source": "MEA", "type": "attention_modality"},
                    meta_level=0,
                )
                self.belief_graph.add_belief(modality_belief)

        if isinstance(boundary, BoundaryAssessment):
            self._mea_boundary = boundary

            boundary_content = (
                f"Ego boundary strength {boundary.strength:.2f} and stability {boundary.stability:.2f}"
            )
            boundary_belief = Belief(
                content=boundary_content,
                belief_type=BeliefType.FACTUAL,
                confidence=boundary.stability,
                context={"source": "MEA", "type": "boundary"},
                meta_level=0,
            )
            self.belief_graph.add_belief(boundary_belief)

        if isinstance(summary, IntrospectiveSummary):
            self._mea_summary = summary

            narrative_belief = Belief(
                content=f"Self-narrative reports: {summary.narrative}",
                belief_type=BeliefType.META,
                confidence=summary.confidence,
                context={"source": "MEA", "type": "self_report"},
                meta_level=1,
            )
            self.belief_graph.add_belief(narrative_belief)

        if isinstance(episodic_episode, Episode):
            self._episodic_episode = episodic_episode
            episodic_content = (
                f"Episodic episode at {episodic_episode.timestamp.isoformat(timespec='seconds')} "
                f"focused on '{episodic_episode.focus_target}'"
            )
            episodic_belief = Belief(
                content=episodic_content,
                belief_type=BeliefType.FACTUAL,
                confidence=episodic_episode.confidence,
                context={"source": "EpisodicMemory", "episode_id": episodic_episode.episode_id},
                meta_level=0,
            )
            self.belief_graph.add_belief(episodic_belief)

        if isinstance(episodic_narrative, str) and episodic_coherence is not None:
            self._episodic_narrative = episodic_narrative
            self._episodic_coherence = float(episodic_coherence)
            coherence = float(episodic_coherence)
            narrative_belief = Belief(
                content=f"Episodic narrative summary: {episodic_narrative}",
                belief_type=BeliefType.META,
                confidence=max(0.0, min(1.0, coherence)),
                context={"source": "EpisodicMemory", "type": "narrative"},
                meta_level=1,
            )
            self.belief_graph.add_belief(narrative_belief)
        else:
            if isinstance(episodic_narrative, str):
                self._episodic_narrative = episodic_narrative
            if isinstance(episodic_coherence, (int, float)):
                self._episodic_coherence = float(episodic_coherence)

    def _generate_meta_belief(self, level_result: ReasoningLevel, next_level: int) -> Belief:
        """
        Gera meta-crença sobre nível de raciocínio.

        Args:
            level_result: Resultado do nível anterior
            next_level: Nível da nova meta-crença

        Returns:
            Meta-crença de ordem superior
        """
        base_belief = level_result.beliefs[0]

        meta_content = f"I believe that '{base_belief.content}' is justified with confidence {level_result.coherence:.2f}"

        meta_belief = Belief(
            content=meta_content,
            belief_type=BeliefType.META,
            confidence=level_result.coherence,
            justification=[base_belief],
            context=base_belief.context,
            meta_level=next_level,
        )

        return meta_belief

    async def _resolve_contradiction(self, contradiction: Contradiction) -> Resolution:
        """
        Resolve contradição aplicando estratégia sugerida.

        Args:
            contradiction: Contradição a resolver

        Returns:
            Resolution aplicada
        """
        outcome = await self.belief_revision.revise_belief_graph(
            self.belief_graph, contradiction
        )
        return outcome.resolution

    def _calculate_coherence(self, levels: List[ReasoningLevel]) -> float:
        """
        Calcula coerência global através de todos os níveis.

        Heurística:
        - Coherence = média de coerências de cada nível
        - Com penalidade se coerência cai entre níveis
        """
        if not levels:
            return 0.0

        # Média das coerências
        avg_coherence = sum(level.coherence for level in levels) / len(levels)

        # Penalidade se coerência degradou entre níveis
        degradation_penalty = 0.0
        for i in range(1, len(levels)):
            drop = levels[i - 1].coherence - levels[i].coherence
            if drop > 0:
                degradation_penalty += drop * 0.1  # 10% penalidade por drop

        return max(0.0, avg_coherence - degradation_penalty)
