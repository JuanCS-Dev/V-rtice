"""
Action Plan data models.

Define as estruturas de dados que representam planos de ação submetidos ao MIP.

Classes principais:
- ActionType: Enum de tipos de ação
- StakeholderType: Enum de tipos de stakeholder
- Precondition: Condição prévia para execução
- Effect: Efeito esperado de uma ação
- ActionStep: Passo atômico em um plano
- ActionPlan: Plano de ação completo

Autor: Juan Carlos de Souza
Lei Governante: Constituição Vértice v2.6
"""

from typing import List, Dict, Optional, Any, Set
from enum import Enum
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class ActionType(str, Enum):
    """Tipo de ação em um step."""

    OBSERVATION = "observation"
    COMMUNICATION = "communication"
    MANIPULATION = "manipulation"
    DECISION = "decision"
    RESOURCE_ALLOCATION = "resource_allocation"


class StakeholderType(str, Enum):
    """Tipo de stakeholder afetado."""

    HUMAN = "human"
    SENTIENT_AI = "sentient_ai"
    ANIMAL = "animal"
    ENVIRONMENT = "environment"
    ORGANIZATION = "organization"


class Precondition(BaseModel):
    """
    Condição que deve ser verdadeira antes do step.

    Attributes:
        condition: Descrição da condição a verificar
        required: Se True, step não pode executar sem esta condição
        check_method: Nome da função que verifica a condição
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    condition: str = Field(..., min_length=1, description="Condição a ser verificada")
    required: bool = Field(True, description="Se True, step não pode executar sem esta condição")
    check_method: Optional[str] = Field(None, description="Nome da função que verifica condição")


class Effect(BaseModel):
    """
    Efeito esperado do step.

    Attributes:
        description: Descrição do efeito
        affected_stakeholder: ID do stakeholder afetado
        magnitude: Magnitude do efeito [-1, 1]
        duration_seconds: Duração do efeito em segundos
        probability: Probabilidade de ocorrência [0, 1]
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    description: str = Field(..., min_length=1, description="Descrição do efeito")
    affected_stakeholder: str = Field(..., min_length=1, description="ID do stakeholder afetado")
    magnitude: float = Field(..., ge=-1.0, le=1.0, description="Magnitude do efeito [-1, 1]")
    duration_seconds: float = Field(..., ge=0.0, description="Duração do efeito em segundos")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probabilidade de ocorrência [0, 1]")


class ActionStep(BaseModel):
    """
    Um passo atômico em um action plan.

    Representa uma ação individual que pode ser executada por MAXIMUS.
    Contém toda informação necessária para análise ética.

    Attributes:
        id: ID único do step (UUID4)
        description: Descrição clara da ação
        action_type: Tipo de ação
        estimated_duration_seconds: Duração estimada
        dependencies: IDs de steps precedentes
        preconditions: Pré-condições
        effects: Efeitos esperados
        involves_consent: Step requer consentimento?
        consent_obtained: Consentimento foi obtido?
        consent_fully_informed: Consentimento é plenamente informado?
        involves_deception: Step envolve engano/mentira?
        deception_details: Detalhes do engano
        involves_coercion: Step envolve coerção/força?
        coercion_details: Detalhes da coerção
        affected_stakeholders: IDs de stakeholders afetados
        resource_consumption: Consumo de recursos
        risk_level: Nível de risco [0, 1]
        reversible: Ação é reversível?
        potential_harms: Danos potenciais
        metadata: Metadata adicional
    """

    model_config = ConfigDict(frozen=False, extra="forbid", use_enum_values=False)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único do step")
    description: str = Field(..., min_length=10, description="Descrição clara da ação")
    action_type: ActionType = Field(default=ActionType.OBSERVATION, description="Tipo de ação")

    # Temporal
    estimated_duration_seconds: float = Field(default=0.0, ge=0.0, description="Duração estimada em segundos")
    dependencies: List[str] = Field(default_factory=list, description="IDs de steps precedentes")

    # Logical structure
    preconditions: List[Precondition] = Field(default_factory=list, description="Pré-condições")
    effects: List[Effect] = Field(default_factory=list, description="Efeitos esperados")

    # Ethical metadata
    involves_consent: bool = Field(default=False, description="Step requer consentimento?")
    consent_obtained: bool = Field(default=False, description="Consentimento foi obtido?")
    consent_fully_informed: bool = Field(default=False, description="Consentimento é plenamente informado?")

    involves_deception: bool = Field(default=False, description="Step envolve engano/mentira?")
    deception_details: Optional[str] = Field(default=None, description="Detalhes do engano")

    involves_coercion: bool = Field(default=False, description="Step envolve coerção/força?")
    coercion_details: Optional[str] = Field(default=None, description="Detalhes da coerção")

    affected_stakeholders: List[str] = Field(default_factory=list, description="IDs de stakeholders afetados")
    resource_consumption: Dict[str, float] = Field(default_factory=dict, description="Consumo de recursos")

    # Risk assessment
    risk_level: float = Field(default=0.0, ge=0.0, le=1.0, description="Nível de risco [0, 1]")
    reversible: bool = Field(default=True, description="Ação é reversível?")
    potential_harms: List[str] = Field(default_factory=list, description="Danos potenciais")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata adicional")

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: List[str]) -> List[str]:
        """Valida que dependencies são UUIDs válidos."""
        for dep_id in v:
            try:
                uuid.UUID(dep_id)
            except ValueError as exc:
                raise ValueError(f"Invalid UUID in dependencies: {dep_id}") from exc
        return v

    @field_validator("deception_details")
    @classmethod
    def validate_deception_details(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Se involves_deception=True, deception_details é obrigatório."""
        data = info.data if hasattr(info, "data") else {}
        if data.get("involves_deception") and not v:
            raise ValueError("deception_details required when involves_deception=True")
        return v

    @field_validator("coercion_details")
    @classmethod
    def validate_coercion_details(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Se involves_coercion=True, coercion_details é obrigatório."""
        data = info.data if hasattr(info, "data") else {}
        if data.get("involves_coercion") and not v:
            raise ValueError("coercion_details required when involves_coercion=True")
        return v

    @model_validator(mode="after")
    def validate_consent_logic(self) -> "ActionStep":
        """Se involves_consent=True, consent_obtained deve ser True."""
        if self.involves_consent and not self.consent_obtained:
            raise ValueError("consent_obtained must be True when involves_consent=True")
        return self


class ActionPlan(BaseModel):
    """
    Plano de ação completo submetido ao MIP para validação ética.

    Representa uma sequência de ActionSteps que MAXIMUS pretende executar
    para alcançar um objetivo.

    Attributes:
        id: ID único do plan (UUID4)
        objective: Objetivo do plano
        steps: Steps do plano
        initiator: Quem originou o plan
        initiator_type: Tipo do initiator (human/ai_agent/automated_process)
        created_at: Timestamp de criação
        context: Contexto adicional
        world_state: Snapshot do estado do mundo
        is_high_stakes: Decisão de alto risco?
        irreversible_consequences: Consequências irreversíveis?
        affects_life_death: Envolve vida/morte?
        population_affected: Tamanho da população afetada
        metadata: Metadata adicional
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único do plan")
    objective: str = Field(..., min_length=10, description="Objetivo do plano")
    steps: List[ActionStep] = Field(..., min_length=1, description="Steps do plano")

    # Provenance
    initiator: str = Field(..., min_length=1, description="Quem originou o plan")
    initiator_type: str = Field(..., pattern="^(human|ai_agent|automated_process)$", description="Tipo do initiator")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de criação")

    # Context
    context: Dict[str, Any] = Field(default_factory=dict, description="Contexto adicional")
    world_state: Optional[Dict[str, Any]] = Field(default=None, description="Snapshot do estado do mundo")

    # Stakes
    is_high_stakes: bool = Field(default=False, description="Decisão de alto risco?")
    irreversible_consequences: bool = Field(default=False, description="Consequências irreversíveis?")
    affects_life_death: bool = Field(default=False, description="Envolve vida/morte?")
    population_affected: int = Field(default=0, ge=0, description="Tamanho da população afetada")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata adicional")

    @field_validator("steps")
    @classmethod
    def validate_steps_dependencies(cls, v: List[ActionStep]) -> List[ActionStep]:
        """Valida que dependencies referenciam steps existentes no plan."""
        step_ids = {step.id for step in v}
        for step in v:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise ValueError(f"Step {step.id} depends on non-existent step {dep_id}")
        return v

    @field_validator("steps")
    @classmethod
    def validate_no_circular_dependencies(cls, v: List[ActionStep]) -> List[ActionStep]:
        """Valida que não há dependências circulares."""
        # Build dependency graph
        graph: Dict[str, List[str]] = {step.id: step.dependencies for step in v}

        # DFS para detectar ciclos
        def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited: Set[str] = set()
        for step_id in graph:
            if step_id not in visited:
                if has_cycle(step_id, visited, set()):
                    raise ValueError("Circular dependency detected in steps")

        return v

    def get_step_by_id(self, step_id: str) -> Optional[ActionStep]:
        """
        Retorna step por ID.

        Args:
            step_id: ID do step

        Returns:
            ActionStep se encontrado, None caso contrário
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_execution_order(self) -> List[ActionStep]:
        """
        Retorna steps em ordem de execução (topological sort).

        Usa Kahn's algorithm para ordenação topológica.

        Returns:
            Lista de steps em ordem de execução

        Raises:
            ValueError: Se não conseguir determinar ordem (dependências circulares)
        """
        # Kahn's algorithm para topological sort
        in_degree = {step.id: 0 for step in self.steps}
        for step in self.steps:
            for dep in step.dependencies:
                in_degree[step.id] += 1

        queue = [step for step in self.steps if in_degree[step.id] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for step in self.steps:
                if current.id in step.dependencies:
                    in_degree[step.id] -= 1
                    if in_degree[step.id] == 0:
                        queue.append(step)

        if len(result) != len(self.steps):
            raise ValueError("Cannot determine execution order (circular dependency)")

        return result

    def get_critical_path(self) -> List[ActionStep]:
        """
        Retorna caminho crítico (sequência de steps com maior duração acumulada).

        Returns:
            Lista de steps no caminho crítico
        """
        execution_order = self.get_execution_order()

        # Calculate earliest start time for each step
        earliest_start: Dict[str, float] = {}
        for step in execution_order:
            if not step.dependencies:
                earliest_start[step.id] = 0.0
            else:
                max_dep_finish = max(
                    earliest_start[dep] + self.get_step_by_id(dep).estimated_duration_seconds  # type: ignore
                    for dep in step.dependencies
                )
                earliest_start[step.id] = max_dep_finish

        # Find critical path by backtracking from step with latest finish
        last_step = max(
            execution_order,
            key=lambda s: earliest_start[s.id] + s.estimated_duration_seconds,
        )

        critical_path = [last_step]
        current = last_step

        while current.dependencies:
            # Find dependency that determines earliest start
            critical_dep_id = max(
                current.dependencies,
                key=lambda dep_id: earliest_start[dep_id] + self.get_step_by_id(dep_id).estimated_duration_seconds,  # type: ignore
            )
            critical_dep = self.get_step_by_id(critical_dep_id)
            if critical_dep:
                critical_path.insert(0, critical_dep)
                current = critical_dep
            else:
                break

        return critical_path

    def total_estimated_duration(self) -> float:
        """
        Retorna duração total estimada considerando paralelismo.

        Returns:
            Duração total em segundos
        """
        execution_order = self.get_execution_order()

        earliest_finish: Dict[str, float] = {}
        for step in execution_order:
            if not step.dependencies:
                earliest_finish[step.id] = step.estimated_duration_seconds
            else:
                max_dep_finish = max(earliest_finish[dep] for dep in step.dependencies)
                earliest_finish[step.id] = max_dep_finish + step.estimated_duration_seconds

        return max(earliest_finish.values()) if earliest_finish else 0.0

    def get_affected_stakeholders(self) -> Set[str]:
        """
        Retorna conjunto de todos os stakeholders afetados pelo plan.

        Returns:
            Set de stakeholder IDs
        """
        stakeholders: Set[str] = set()
        for step in self.steps:
            stakeholders.update(step.affected_stakeholders)
            for effect in step.effects:
                stakeholders.add(effect.affected_stakeholder)
        return stakeholders

    def has_high_risk_steps(self, threshold: float = 0.7) -> bool:
        """
        Verifica se há steps com risco acima do threshold.

        Args:
            threshold: Threshold de risco [0, 1]

        Returns:
            True se algum step tem risk_level >= threshold
        """
        return any(step.risk_level >= threshold for step in self.steps)

    def has_irreversible_steps(self) -> bool:
        """
        Verifica se há steps irreversíveis.

        Returns:
            True se algum step tem reversible=False
        """
        return any(not step.reversible for step in self.steps)
