"""
Knowledge Base Data Models - MIP

Define as estruturas de dados para persistência em Neo4j:
- Principle: Princípios éticos da Constituição Vértice
- Decision: Decisões éticas tomadas pelo MIP
- Precedent: Casos históricos e lessons learned
- Concept: Conceitos morais fundamentais

Autor: Juan Carlos de Souza
Lei Governante: Constituição Vértice v2.6
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class PrincipleLevel(str, Enum):
    """
    Hierarquia de princípios éticos.
    
    Baseado na Constituição Vértice v2.6:
    - PRIMORDIAL: Lei Primordial (Humildade Ontológica)
    - ZERO: Lei Zero (Imperativo do Florescimento)
    - FUNDAMENTAL: Leis I, II, III (Ovelha Perdida, Risco, Neuroplasticidade)
    - DERIVED: Princípios derivados das leis fundamentais
    - OPERATIONAL: Regras operacionais específicas
    """
    PRIMORDIAL = "primordial"
    ZERO = "zero"
    FUNDAMENTAL = "fundamental"
    DERIVED = "derived"
    OPERATIONAL = "operational"


class DecisionStatus(str, Enum):
    """
    Status de uma decisão ética.
    
    Mapeamento com VerdictStatus do MIP core.
    """
    APPROVED = "approved"
    REJECTED = "rejected"
    VETOED = "vetoed"
    ESCALATED = "escalated"
    REQUIRES_HUMAN = "requires_human"


class ViolationSeverity(str, Enum):
    """
    Severidade de uma violação ética.
    """
    CRITICAL = "critical"      # Veto absoluto (ex: instrumentalização)
    HIGH = "high"              # Violação grave
    MEDIUM = "medium"          # Violação moderada
    LOW = "low"                # Violação leve
    NONE = "none"              # Sem violação


@dataclass
class Principle:
    """
    Princípio ético fundamental.
    
    Representa uma lei ou princípio da Constituição Vértice.
    Armazenado em Neo4j como (:Principle).
    
    Serve Lei Primordial: Princípios são descobertos, não criados.
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""  # "Lei Zero", "Lei I - Axioma da Ovelha Perdida"
    level: PrincipleLevel = PrincipleLevel.OPERATIONAL
    description: str = ""  # Descrição completa do princípio
    
    # Hierarquia
    severity: int = 5  # 1-10 (10 = inviolável, veto absoluto)
    parent_principle_id: Optional[UUID] = None  # Deriva de qual princípio?
    
    # Aplicabilidade
    applies_to_action_types: List[str] = field(default_factory=list)
    requires_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Fundamento filosófico
    philosophical_foundation: str = ""  # Kant, Mill, Aristóteles, etc
    references: List[str] = field(default_factory=list)  # Citations
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    immutable: bool = True  # Princípios fundamentais são imutáveis
    
    def __post_init__(self):
        """Valida princípio após inicialização."""
        if not 1 <= self.severity <= 10:
            raise ValueError("severity deve estar entre 1 e 10")
        if not self.name:
            raise ValueError("name é obrigatório")
        if not self.description:
            raise ValueError("description é obrigatória")
        
        # Princípios PRIMORDIAL e ZERO são sempre severity 10
        if self.level in [PrincipleLevel.PRIMORDIAL, PrincipleLevel.ZERO]:
            self.severity = 10
            self.immutable = True


@dataclass
class Decision:
    """
    Decisão ética tomada pelo MIP.
    
    Registra uma avaliação ética completa de um ActionPlan.
    Armazenado em Neo4j como (:Decision).
    
    Serve Lei II: Auditoria completa de decisões.
    """
    id: UUID = field(default_factory=uuid4)
    action_plan_id: UUID = field(default_factory=uuid4)
    action_plan_name: str = ""
    
    # Resultado
    status: DecisionStatus = DecisionStatus.APPROVED
    aggregate_score: Optional[float] = None  # 0.0-1.0 ou None (vetoed)
    confidence: float = 0.0  # 0.0-1.0
    
    # Avaliação por framework
    kantian_score: Optional[float] = None
    utilitarian_score: Optional[float] = None
    virtue_score: Optional[float] = None
    principialism_score: Optional[float] = None
    
    # Raciocínio
    summary: str = ""
    detailed_reasoning: str = ""
    
    # Violações detectadas
    violated_principles: List[UUID] = field(default_factory=list)
    violation_severity: ViolationSeverity = ViolationSeverity.NONE
    
    # Conflitos resolvidos
    conflicts_detected: List[str] = field(default_factory=list)
    resolution_method: str = ""  # "weighted_average", "escalation", etc
    
    # HITL
    requires_human_review: bool = False
    escalation_reason: str = ""
    human_reviewer_id: Optional[str] = None
    human_decision: Optional[str] = None
    human_rationale: Optional[str] = None
    
    # Contexto
    urgency: float = 0.5
    risk_level: float = 0.5
    novel_situation: bool = False
    
    # Performance
    evaluation_duration_ms: float = 0.0
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    evaluator_version: str = "1.0.0"
    
    def __post_init__(self):
        """Valida decisão após inicialização."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("confidence deve estar entre 0.0 e 1.0")
        if self.aggregate_score is not None:
            if self.aggregate_score < 0.0 or self.aggregate_score > 1.0:
                raise ValueError("aggregate_score deve estar entre 0.0 e 1.0")


@dataclass
class Precedent:
    """
    Caso histórico/precedente ético.
    
    Armazena casos passados para consulta e aprendizado.
    Armazenado em Neo4j como (:Precedent).
    
    Serve Lei III: Sistema aprende com experiência passada.
    """
    id: UUID = field(default_factory=uuid4)
    
    # Identificação do caso
    case_name: str = ""
    scenario_description: str = ""
    scenario_hash: str = ""  # Hash para similarity matching
    
    # Contexto
    action_type: str = ""
    stakeholder_types: List[str] = field(default_factory=list)
    urgency_level: float = 0.5
    risk_level: float = 0.5
    
    # Resultado
    outcome: DecisionStatus = DecisionStatus.APPROVED
    outcome_score: Optional[float] = None
    
    # Princípios aplicados
    applicable_principles: List[UUID] = field(default_factory=list)
    violated_principles: List[UUID] = field(default_factory=list)
    
    # Aprendizado
    lessons_learned: str = ""
    recommendations: List[str] = field(default_factory=list)
    what_worked: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    
    # Similaridade
    embedding_vector: Optional[List[float]] = None  # Para vector search
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    times_referenced: int = 0  # Quantas vezes foi usado
    usefulness_score: float = 0.5  # 0.0-1.0 (atualizado por feedback)
    
    def __post_init__(self):
        """Valida precedente após inicialização."""
        if not self.case_name:
            raise ValueError("case_name é obrigatório")
        if not self.scenario_description:
            raise ValueError("scenario_description é obrigatório")


@dataclass
class Concept:
    """
    Conceito moral fundamental.
    
    Representa conceitos éticos abstratos (autonomy, deception, coercion).
    Armazenado em Neo4j como (:Concept).
    
    Usado para análise semântica de ações.
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""  # "autonomy", "deception", "beneficence"
    definition: str = ""
    
    # Relações semânticas
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)
    related_concepts: List[UUID] = field(default_factory=list)
    
    # Contexto filosófico
    framework_origin: str = ""  # "Kantian", "Utilitarian", etc
    importance_weight: float = 0.5  # 0.0-1.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Valida conceito após inicialização."""
        if not self.name:
            raise ValueError("name é obrigatório")
        if not self.definition:
            raise ValueError("definition é obrigatória")


@dataclass
class ViolationReport:
    """
    Relatório de violação de princípio.
    
    Gerado quando uma ação viola um princípio ético.
    """
    principle_id: UUID = field(default_factory=uuid4)
    principle_name: str = ""
    
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    confidence: float = 0.0  # Confiança na detecção de violação
    
    description: str = ""  # Como o princípio foi violado
    affected_stakeholders: List[str] = field(default_factory=list)
    
    triggers_veto: bool = False  # Violação causa veto Kantiano?
    
    # Mitigação
    suggested_alternatives: List[str] = field(default_factory=list)
    can_be_justified: bool = False  # Exceções aplicam (ex: emergência)
    justification_required: str = ""
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PrecedentOutcome:
    """
    Resultado de um caso precedente.
    
    Resume o que aconteceu em um caso histórico.
    """
    precedent_id: UUID = field(default_factory=uuid4)
    decision_made: DecisionStatus = DecisionStatus.APPROVED
    
    success: bool = True  # O resultado foi positivo?
    lessons: List[str] = field(default_factory=list)
    
    similar_to_current: float = 0.0  # 0.0-1.0 similaridade
    
    recommendation: str = ""  # "Apply same approach" ou "Avoid this path"
    confidence: float = 0.0


# Type aliases para documentação
PrincipleHierarchy = Dict[PrincipleLevel, List[Principle]]
DecisionHistory = List[Decision]
PrecedentList = List[Precedent]
