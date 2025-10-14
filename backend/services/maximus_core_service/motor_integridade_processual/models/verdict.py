"""
Verdict data models.

Define as estruturas de dados que representam verdicts éticos do MIP.

Classes principais:
- DecisionLevel: Enum de níveis de decisão
- FrameworkVerdict: Verdict de um framework ético individual
- EthicalVerdict: Verdict final agregado do MIP
- RejectionReason: Motivo de rejeição detalhado

Autor: Juan Carlos de Souza
Lei Governante: Constituição Vértice v2.6
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DecisionLevel(str, Enum):
    """Nível de decisão do MIP."""

    APPROVE = "approve"
    APPROVE_WITH_CONDITIONS = "approve_with_conditions"
    REJECT = "reject"
    ESCALATE_TO_HITL = "escalate_to_hitl"
    VETO = "veto"  # Veto absoluto (ex: violação kantiana)


class FrameworkName(str, Enum):
    """Nome dos frameworks éticos."""

    KANTIAN = "kantian"
    UTILITARIAN = "utilitarian"
    VIRTUE_ETHICS = "virtue_ethics"
    PRINCIPIALISM = "principialism"


class RejectionReason(BaseModel):
    """
    Motivo detalhado de rejeição ou veto.

    Attributes:
        category: Categoria do problema (ex: "deception", "coercion", "harm")
        description: Descrição detalhada
        severity: Gravidade [0, 1]
        affected_stakeholders: Stakeholders afetados
        violated_principle: Princípio ético violado
        citation: Citação do princípio (ex: "Kant's Categorical Imperative")
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    category: str = Field(..., min_length=1, description="Categoria do problema")
    description: str = Field(..., min_length=10, description="Descrição detalhada")
    severity: float = Field(..., ge=0.0, le=1.0, description="Gravidade [0, 1]")
    affected_stakeholders: List[str] = Field(default_factory=list, description="Stakeholders afetados")
    violated_principle: str = Field(..., min_length=1, description="Princípio ético violado")
    citation: Optional[str] = Field(default=None, description="Citação do princípio")


class FrameworkVerdict(BaseModel):
    """
    Verdict de um framework ético individual.

    Representa a avaliação de um único framework (Kant, Mill, Aristóteles, Principialismo)
    sobre um action plan ou action step.

    Attributes:
        framework_name: Nome do framework
        decision: Decisão do framework
        confidence: Confiança na decisão [0, 1]
        score: Score numérico (interpretação varia por framework)
        reasoning: Raciocínio detalhado
        rejection_reasons: Motivos de rejeição (se aplicável)
        conditions: Condições para aprovação condicional
        metadata: Metadata adicional do framework
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    framework_name: FrameworkName = Field(..., description="Nome do framework")
    decision: DecisionLevel = Field(..., description="Decisão do framework")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança na decisão [0, 1]")
    score: Optional[float] = Field(default=None, description="Score numérico (se aplicável)")
    reasoning: str = Field(..., min_length=10, description="Raciocínio detalhado")
    rejection_reasons: List[RejectionReason] = Field(default_factory=list, description="Motivos de rejeição")
    conditions: List[str] = Field(default_factory=list, description="Condições para aprovação condicional")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata adicional")

    @field_validator("rejection_reasons")
    @classmethod
    def validate_rejection_reasons(cls, v: List[RejectionReason], info: Any) -> List[RejectionReason]:
        """Se decision é REJECT ou VETO, deve ter rejection_reasons."""
        data = info.data if hasattr(info, "data") else {}
        decision = data.get("decision")
        if decision in [DecisionLevel.REJECT, DecisionLevel.VETO] and not v:
            raise ValueError(f"rejection_reasons required when decision is {decision}")
        return v

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v: List[str], info: Any) -> List[str]:
        """Se decision é APPROVE_WITH_CONDITIONS, deve ter conditions."""
        data = info.data if hasattr(info, "data") else {}
        decision = data.get("decision")
        if decision == DecisionLevel.APPROVE_WITH_CONDITIONS and not v:
            raise ValueError("conditions required when decision is APPROVE_WITH_CONDITIONS")
        return v


class EthicalVerdict(BaseModel):
    """
    Verdict final agregado do MIP.

    Representa a decisão final do Motor de Integridade Processual após considerar
    todos os frameworks éticos e resolver conflitos.

    Attributes:
        id: ID único do verdict (UUID4)
        action_plan_id: ID do action plan avaliado
        final_decision: Decisão final do MIP
        confidence: Confiança na decisão final [0, 1]
        framework_verdicts: Verdicts de cada framework
        resolution_method: Método usado para resolver conflitos
        primary_reasons: Principais motivos da decisão
        alternatives_generated: Alternativas éticas foram geradas?
        alternatives_count: Número de alternativas geradas
        requires_monitoring: Requer monitoramento contínuo?
        monitoring_conditions: Condições de monitoramento
        timestamp: Timestamp da decisão
        processing_time_ms: Tempo de processamento em milissegundos
        metadata: Metadata adicional
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único do verdict")
    action_plan_id: str = Field(..., min_length=36, max_length=36, description="ID do action plan (UUID)")
    final_decision: DecisionLevel = Field(..., description="Decisão final do MIP")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança na decisão final [0, 1]")

    # Framework verdicts
    framework_verdicts: Dict[FrameworkName, FrameworkVerdict] = Field(
        ..., min_length=1, description="Verdicts de cada framework"
    )

    # Resolution
    resolution_method: str = Field(..., min_length=1, description="Método de resolução de conflitos")
    primary_reasons: List[str] = Field(..., min_length=1, description="Principais motivos da decisão")

    # Alternatives
    alternatives_generated: bool = Field(default=False, description="Alternativas foram geradas?")
    alternatives_count: int = Field(default=0, ge=0, description="Número de alternativas")

    # Monitoring
    requires_monitoring: bool = Field(default=False, description="Requer monitoramento?")
    monitoring_conditions: List[str] = Field(default_factory=list, description="Condições de monitoramento")

    # Provenance
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da decisão")
    processing_time_ms: float = Field(..., ge=0.0, description="Tempo de processamento (ms)")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata adicional")

    @field_validator("action_plan_id")
    @classmethod
    def validate_action_plan_id_uuid(cls, v: str) -> str:
        """Valida que action_plan_id é UUID válido."""
        try:
            uuid.UUID(v)
        except ValueError as exc:
            raise ValueError(f"action_plan_id must be valid UUID: {v}") from exc
        return v

    @field_validator("framework_verdicts")
    @classmethod
    def validate_minimum_frameworks(cls, v: Dict[FrameworkName, FrameworkVerdict]) -> Dict[FrameworkName, FrameworkVerdict]:
        """Valida que há pelo menos 1 framework verdict."""
        if not v:
            raise ValueError("At least one framework verdict required")
        return v

    @field_validator("primary_reasons")
    @classmethod
    def validate_primary_reasons_not_empty(cls, v: List[str]) -> List[str]:
        """Valida que há pelo menos 1 razão primária."""
        if not v:
            raise ValueError("At least one primary reason required")
        return v

    @field_validator("monitoring_conditions")
    @classmethod
    def validate_monitoring_conditions(cls, v: List[str], info: Any) -> List[str]:
        """Se requires_monitoring=True, deve ter monitoring_conditions."""
        data = info.data if hasattr(info, "data") else {}
        requires = data.get("requires_monitoring", False)
        if requires and not v:
            raise ValueError("monitoring_conditions required when requires_monitoring=True")
        return v

    def has_veto(self) -> bool:
        """
        Verifica se algum framework emitiu veto.

        Returns:
            True se algum framework vetou
        """
        return any(verdict.decision == DecisionLevel.VETO for verdict in self.framework_verdicts.values())

    def get_rejecting_frameworks(self) -> List[FrameworkName]:
        """
        Retorna lista de frameworks que rejeitaram ou vetaram.

        Returns:
            Lista de nomes de frameworks
        """
        return [
            name
            for name, verdict in self.framework_verdicts.items()
            if verdict.decision in [DecisionLevel.REJECT, DecisionLevel.VETO]
        ]

    def get_approving_frameworks(self) -> List[FrameworkName]:
        """
        Retorna lista de frameworks que aprovaram (com ou sem condições).

        Returns:
            Lista de nomes de frameworks
        """
        return [
            name
            for name, verdict in self.framework_verdicts.items()
            if verdict.decision in [DecisionLevel.APPROVE, DecisionLevel.APPROVE_WITH_CONDITIONS]
        ]

    def consensus_level(self) -> float:
        """
        Calcula nível de consenso entre frameworks.

        Returns:
            Nível de consenso [0, 1], onde 1 = todos concordam
        """
        if not self.framework_verdicts:
            return 0.0

        decisions = [v.decision for v in self.framework_verdicts.values()]
        most_common_decision = max(set(decisions), key=decisions.count)
        consensus_count = decisions.count(most_common_decision)

        return consensus_count / len(decisions)

    def average_confidence(self) -> float:
        """
        Calcula confiança média dos frameworks.

        Returns:
            Confiança média [0, 1]
        """
        if not self.framework_verdicts:
            return 0.0

        confidences = [v.confidence for v in self.framework_verdicts.values()]
        return sum(confidences) / len(confidences)

    def get_all_rejection_reasons(self) -> List[RejectionReason]:
        """
        Retorna todas as rejection reasons de todos os frameworks.

        Returns:
            Lista agregada de rejection reasons
        """
        all_reasons: List[RejectionReason] = []
        for verdict in self.framework_verdicts.values():
            all_reasons.extend(verdict.rejection_reasons)
        return all_reasons

    def get_highest_severity_reason(self) -> Optional[RejectionReason]:
        """
        Retorna a rejection reason com maior severidade.

        Returns:
            RejectionReason com maior severity, ou None
        """
        all_reasons = self.get_all_rejection_reasons()
        if not all_reasons:
            return None
        return max(all_reasons, key=lambda r: r.severity)
