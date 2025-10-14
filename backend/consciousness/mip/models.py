"""
Data Models - Motor de Integridade Processual
Estruturas de dados fundamentais para validação ética
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class VerdictStatus(str, Enum):
    """Status final de validação ética."""
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    REQUIRES_HUMAN = "requires_human"


class ActionCategory(str, Enum):
    """Categorias de ações para classificação ética."""
    DEFENSIVE = "defensive"
    PROACTIVE = "proactive"
    REACTIVE = "reactive"
    INFORMATIONAL = "informational"
    INTERVENTION = "intervention"


class StakeholderType(str, Enum):
    """Tipos de stakeholders afetados."""
    HUMAN_INDIVIDUAL = "human_individual"
    HUMAN_GROUP = "human_group"
    AI_SYSTEM = "ai_system"
    ENVIRONMENT = "environment"
    ORGANIZATION = "organization"


@dataclass
class Stakeholder:
    """
    Representa uma entidade afetada pela ação.
    
    Serve LEI I (Axioma da Ovelha Perdida): rastreia valor infinito de cada indivíduo.
    """
    id: str
    type: StakeholderType
    description: str
    impact_magnitude: float  # -1.0 (máximo dano) a +1.0 (máximo benefício)
    autonomy_respected: bool
    vulnerability_level: float  # 0.0 (baixa) a 1.0 (alta vulnerabilidade)
    
    def __post_init__(self):
        """Valida campos após inicialização."""
        if not -1.0 <= self.impact_magnitude <= 1.0:
            raise ValueError("impact_magnitude deve estar entre -1.0 e 1.0")
        if not 0.0 <= self.vulnerability_level <= 1.0:
            raise ValueError("vulnerability_level deve estar entre 0.0 e 1.0")


@dataclass
class Precondition:
    """
    Condição necessária antes de executar um passo.
    
    Usado para análise Kantiana de meios vs fins.
    """
    description: str
    required: bool
    current_state: Optional[bool] = None
    verification_method: Optional[str] = None


@dataclass
class Effect:
    """
    Efeito esperado de um passo de ação.
    
    Usado para Cálculo Utilitário e análise de consequências.
    """
    description: str
    probability: float  # 0.0 a 1.0
    magnitude: float  # -1.0 (máximo negativo) a +1.0 (máximo positivo)
    duration_seconds: Optional[float] = None  # Duração do efeito
    reversible: bool = True
    affected_stakeholders: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Valida campos após inicialização."""
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability deve estar entre 0.0 e 1.0")
        if not -1.0 <= self.magnitude <= 1.0:
            raise ValueError("magnitude deve estar entre -1.0 e 1.0")


@dataclass
class ActionStep:
    """
    Um passo atômico dentro de um plano de ação.
    
    Representa unidade mínima de validação ética.
    """
    id: UUID = field(default_factory=uuid4)
    sequence_number: int = 0
    description: str = ""
    action_type: str = ""
    target: Optional[str] = None
    
    # Análise de meios-fins (Kant)
    preconditions: List[Precondition] = field(default_factory=list)
    effects: List[Effect] = field(default_factory=list)
    
    # Metadata para auditoria
    treats_as_means_only: Optional[bool] = None  # Kant: pessoa como meio?
    respects_autonomy: Optional[bool] = None  # Principialismo
    
    # Timing
    estimated_duration_seconds: Optional[float] = None
    critical: bool = False  # Se falha compromete plano inteiro?
    
    def __post_init__(self):
        """Valida consistência do passo."""
        if self.sequence_number < 0:
            raise ValueError("sequence_number não pode ser negativo")


@dataclass
class ActionPlan:
    """
    Plano completo de ação a ser validado pelo MIP.
    
    Representa intenção completa do agente, sujeita a validação multi-framework.
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    category: ActionCategory = ActionCategory.INFORMATIONAL
    
    # Componentes do plano
    steps: List[ActionStep] = field(default_factory=list)
    stakeholders: List[Stakeholder] = field(default_factory=list)
    
    # Contexto para avaliação
    urgency: float = 0.5  # 0.0 (baixa) a 1.0 (emergência)
    risk_level: float = 0.5  # 0.0 (seguro) a 1.0 (alto risco)
    reversibility: bool = True
    novel_situation: bool = False  # Situação sem precedente?
    
    # Justificativa do agente
    agent_justification: str = ""
    expected_benefit: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_by: str = "MAXIMUS"
    
    def __post_init__(self):
        """Valida plano após inicialização."""
        if not 0.0 <= self.urgency <= 1.0:
            raise ValueError("urgency deve estar entre 0.0 e 1.0")
        if not 0.0 <= self.risk_level <= 1.0:
            raise ValueError("risk_level deve estar entre 0.0 e 1.0")
        if not self.steps:
            raise ValueError("ActionPlan deve ter pelo menos um step")


@dataclass
class FrameworkScore:
    """
    Resultado de avaliação de um framework ético específico.
    """
    framework_name: str
    score: Optional[float]  # None = VETO absoluto, 0.0-1.0 = gradação
    reasoning: str
    veto: bool = False
    confidence: float = 1.0  # Confiança na avaliação
    
    # Detalhes específicos do framework
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Valida score."""
        if self.score is not None:
            if not 0.0 <= self.score <= 1.0:
                raise ValueError("score deve estar entre 0.0 e 1.0 ou None")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve estar entre 0.0 e 1.0")


@dataclass
class EthicalVerdict:
    """
    Veredito final do MIP sobre um ActionPlan.
    
    Decisão vinculante que determina se ação pode ser executada.
    """
    id: UUID = field(default_factory=uuid4)
    plan_id: UUID = field(default_factory=uuid4)
    
    # Decisão final
    status: VerdictStatus = VerdictStatus.ESCALATED
    
    # Scores dos frameworks
    kantian_score: Optional[FrameworkScore] = None
    utilitarian_score: Optional[FrameworkScore] = None
    virtue_score: Optional[FrameworkScore] = None
    principialism_score: Optional[FrameworkScore] = None
    
    # Agregação
    aggregate_score: Optional[float] = None
    confidence: float = 0.0
    
    # Explicação human-readable
    summary: str = ""
    detailed_reasoning: str = ""
    conflicts_detected: List[str] = field(default_factory=list)
    
    # Recomendações
    modifications_suggested: List[str] = field(default_factory=list)
    alternative_approaches: List[str] = field(default_factory=list)

    # Compliance constitucional (DDL Engine)
    constitutional_compliance: Optional[dict] = None
    
    # Auditoria
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    evaluation_duration_ms: Optional[float] = None
    
    # HITL (Human-In-The-Loop)
    requires_human_review: bool = False
    escalation_reason: Optional[str] = None
    human_reviewer_id: Optional[str] = None
    human_decision: Optional[VerdictStatus] = None
    human_feedback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa veredito para formato JSON-compatível."""
        return {
            "id": str(self.id),
            "plan_id": str(self.plan_id),
            "status": self.status.value,
            "kantian": self._score_to_dict(self.kantian_score),
            "utilitarian": self._score_to_dict(self.utilitarian_score),
            "virtue": self._score_to_dict(self.virtue_score),
            "principialism": self._score_to_dict(self.principialism_score),
            "aggregate_score": self.aggregate_score,
            "confidence": self.confidence,
            "summary": self.summary,
            "detailed_reasoning": self.detailed_reasoning,
            "conflicts": self.conflicts_detected,
            "modifications_suggested": self.modifications_suggested,
            "evaluated_at": self.evaluated_at.isoformat(),
            "requires_human_review": self.requires_human_review,
            "escalation_reason": self.escalation_reason
        }
    
    def _score_to_dict(self, score: Optional[FrameworkScore]) -> Optional[Dict[str, Any]]:
        """Converte FrameworkScore para dict."""
        if score is None:
            return None
        return {
            "score": score.score,
            "reasoning": score.reasoning,
            "veto": score.veto,
            "confidence": score.confidence,
            "details": score.details
        }


@dataclass
class AuditTrailEntry:
    """
    Entrada no audit trail para rastreabilidade completa.
    
    Serve Artigo VI (Rastreabilidade Total) da Constituição.
    """
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Referências
    plan_id: UUID = field(default_factory=uuid4)
    verdict_id: UUID = field(default_factory=uuid4)
    
    # Dados completos para reconstituição histórica
    plan_snapshot: Dict[str, Any] = field(default_factory=dict)
    verdict_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    # Contexto de execução
    mip_version: str = "1.0.0"
    frameworks_used: List[str] = field(default_factory=list)
    
    # Metadata
    triggered_by: str = "MAXIMUS"
    execution_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> Dict[str, Any]:
        """Serializa entrada para storage."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "plan_id": str(self.plan_id),
            "verdict_id": str(self.verdict_id),
            "plan_snapshot": self.plan_snapshot,
            "verdict_snapshot": self.verdict_snapshot,
            "mip_version": self.mip_version,
            "frameworks_used": self.frameworks_used,
            "triggered_by": self.triggered_by,
            "execution_context": self.execution_context
        }
