"""
🎯 Policy Engine - Orquestra avaliação e execução de policies

Pipeline:
1. Load policies (YAML)
2. Match triggers (event-based, scheduled)
3. Evaluate conditions
4. Execute actions
5. Log audit trail
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from datetime import datetime
from enum import Enum
import asyncio
import logging

from .parser import PolicyParser, Policy, TriggerType
from .executor import ActionExecutor, ActionResult, ActionStatus


logger = logging.getLogger(__name__)


class PolicyStatus(Enum):
    """Status de execução de policy"""
    TRIGGERED = "triggered"
    CONDITIONS_MET = "conditions_met"
    CONDITIONS_FAILED = "conditions_failed"
    ACTIONS_EXECUTED = "actions_executed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PolicyExecution:
    """Registro de execução de policy"""
    policy_name: str
    status: PolicyStatus
    triggered_at: datetime
    trigger_event: str
    conditions_evaluated: int
    conditions_passed: int
    actions_executed: List[ActionResult] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """
    Engine principal que orquestra policies

    Features:
    - Load policies de YAML
    - Trigger matching (events, schedules)
    - Condition evaluation
    - Action execution via ActionExecutor
    - Audit logging
    - Dry-run mode
    """

    def __init__(
        self,
        dry_run: bool = False,
        executor: Optional[ActionExecutor] = None,
    ):
        """
        Args:
            dry_run: Se True, não executa ações reais
            executor: ActionExecutor customizado (opcional)
        """
        self.dry_run = dry_run
        self.executor = executor or ActionExecutor(dry_run=dry_run)

        # Políticas carregadas
        self.policies: Dict[str, Policy] = {}

        # Event triggers registrados
        self.event_triggers: Dict[str, List[str]] = {}  # event_name -> [policy_names]

        # Histórico de execuções
        self.execution_history: List[PolicyExecution] = []

        # Custom condition evaluators
        self.condition_evaluators: Dict[str, Callable] = {}

    def load_policy(self, policy_path: Path) -> None:
        """
        Carrega policy de arquivo YAML

        Args:
            policy_path: Path para arquivo .yaml

        Raises:
            ValueError: Se policy inválida
        """
        policy = PolicyParser.parse_file(policy_path)

        # Valida
        errors = PolicyParser.validate(policy)
        if errors:
            raise ValueError(f"Invalid policy {policy.name}: {', '.join(errors)}")

        # Registra
        self.policies[policy.name] = policy

        # Indexa triggers
        for trigger in policy.triggers:
            if trigger.type == TriggerType.EVENT:
                event_name = trigger.value
                if event_name not in self.event_triggers:
                    self.event_triggers[event_name] = []
                self.event_triggers[event_name].append(policy.name)

        logger.info(f"Policy loaded: {policy.name}")

    def load_policies_from_dir(self, policies_dir: Path) -> int:
        """
        Carrega todas as policies de um diretório

        Args:
            policies_dir: Diretório com arquivos .yaml

        Returns:
            Número de policies carregadas
        """
        count = 0

        for policy_file in policies_dir.glob("*.yaml"):
            try:
                self.load_policy(policy_file)
                count += 1
            except Exception as e:
                logger.error(f"Failed to load policy {policy_file}: {e}")

        logger.info(f"Loaded {count} policies from {policies_dir}")
        return count

    def trigger_event(
        self,
        event_name: str,
        event_data: Dict[str, Any],
    ) -> List[PolicyExecution]:
        """
        Triggera policies baseado em evento

        Args:
            event_name: Nome do evento (ex: "file_encryption_detected")
            event_data: Dados do evento para avaliar condições

        Returns:
            Lista de PolicyExecution com resultados
        """
        matching_policies = self.event_triggers.get(event_name, [])

        if not matching_policies:
            logger.debug(f"No policies registered for event: {event_name}")
            return []

        # Executa todas as policies que matcham
        executions = []
        for policy_name in matching_policies:
            policy = self.policies[policy_name]

            if not policy.enabled:
                logger.debug(f"Policy {policy_name} is disabled, skipping")
                continue

            execution = self._execute_policy(policy, event_name, event_data)
            executions.append(execution)
            self.execution_history.append(execution)

        return executions

    def _execute_policy(
        self,
        policy: Policy,
        event_name: str,
        event_data: Dict[str, Any],
    ) -> PolicyExecution:
        """
        Executa policy completa: avalia condições e executa ações

        Args:
            policy: Policy para executar
            event_name: Nome do evento que triggerou
            event_data: Dados do evento

        Returns:
            PolicyExecution com resultado
        """
        execution = PolicyExecution(
            policy_name=policy.name,
            status=PolicyStatus.TRIGGERED,
            triggered_at=datetime.now(),
            trigger_event=event_name,
            conditions_evaluated=len(policy.conditions),
            conditions_passed=0,
        )

        try:
            # Avalia condições
            if policy.conditions:
                conditions_met = self._evaluate_conditions(policy.conditions, event_data)
                execution.conditions_passed = conditions_met

                if conditions_met < len(policy.conditions):
                    execution.status = PolicyStatus.CONDITIONS_FAILED
                    logger.info(
                        f"Policy {policy.name} conditions not met "
                        f"({conditions_met}/{len(policy.conditions)})"
                    )
                    return execution

                execution.status = PolicyStatus.CONDITIONS_MET

            # Executa ações
            logger.info(f"Executing policy {policy.name}: {len(policy.actions)} actions")

            for action in policy.actions:
                action_result = self.executor.execute(action.name, action.parameters)
                execution.actions_executed.append(action_result)

                logger.info(
                    f"Action {action.name}: {action_result.status.value} - "
                    f"{action_result.message}"
                )

            execution.status = PolicyStatus.ACTIONS_EXECUTED

        except Exception as e:
            execution.status = PolicyStatus.FAILED
            execution.error = str(e)
            logger.error(f"Policy {policy.name} failed: {e}")

        return execution

    def _evaluate_conditions(
        self,
        conditions: List,
        event_data: Dict[str, Any],
    ) -> int:
        """
        Avalia condições da policy

        Args:
            conditions: Lista de Condition objects
            event_data: Dados do evento

        Returns:
            Número de condições que passaram
        """
        passed = 0

        for condition in conditions:
            if self._evaluate_single_condition(condition.expression, event_data):
                passed += 1

        return passed

    def _evaluate_single_condition(
        self,
        expression: str,
        event_data: Dict[str, Any],
    ) -> bool:
        """
        Avalia uma condição individual

        Suporta expressões simples:
        - process.name = 'cmd.exe'
        - process.name IN ['vssadmin.exe', 'wmic.exe']
        - file.extension IN ['.encrypted', '.locked']

        Args:
            expression: Expressão da condição
            event_data: Dados do evento

        Returns:
            True se condição passou
        """
        try:
            # Parse expressão
            # Format: "field operator value"

            # Suporta IN operator
            if " IN " in expression:
                parts = expression.split(" IN ")
                field = parts[0].strip()
                values_str = parts[1].strip()

                # Parse list: ['value1', 'value2']
                values = eval(values_str)  # Safe porque é YAML trusted

                # Get field value from event_data
                field_value = self._get_nested_field(event_data, field)

                return field_value in values

            # Suporta = operator
            elif "=" in expression:
                parts = expression.split("=")
                field = parts[0].strip()
                expected_value = parts[1].strip().strip("'\"")

                field_value = self._get_nested_field(event_data, field)

                return str(field_value) == expected_value

            # Custom evaluator registrado
            elif expression in self.condition_evaluators:
                evaluator = self.condition_evaluators[expression]
                return evaluator(event_data)

            else:
                logger.warning(f"Unknown condition format: {expression}")
                return False

        except Exception as e:
            logger.error(f"Failed to evaluate condition '{expression}': {e}")
            return False

    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        Obtém valor de campo nested (ex: "process.name")

        Args:
            data: Dicionário com dados
            field_path: Path do campo (ex: "process.name")

        Returns:
            Valor do campo ou None
        """
        parts = field_path.split(".")
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def register_condition_evaluator(
        self,
        condition_name: str,
        evaluator: Callable[[Dict[str, Any]], bool],
    ) -> None:
        """
        Registra evaluator customizado para condições

        Args:
            condition_name: Nome da condição
            evaluator: Função que recebe event_data e retorna bool
        """
        self.condition_evaluators[condition_name] = evaluator

    def get_policy(self, policy_name: str) -> Optional[Policy]:
        """Retorna policy por nome"""
        return self.policies.get(policy_name)

    def list_policies(self, enabled_only: bool = False) -> List[Policy]:
        """
        Lista policies carregadas

        Args:
            enabled_only: Se True, retorna apenas policies habilitadas

        Returns:
            Lista de Policy objects
        """
        policies = list(self.policies.values())

        if enabled_only:
            policies = [p for p in policies if p.enabled]

        return policies

    def get_execution_history(
        self,
        policy_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[PolicyExecution]:
        """
        Retorna histórico de execuções

        Args:
            policy_name: Filtrar por policy específica
            limit: Máximo de execuções

        Returns:
            Lista de PolicyExecution
        """
        history = self.execution_history

        if policy_name:
            history = [ex for ex in history if ex.policy_name == policy_name]

        # Mais recentes primeiro
        history = sorted(history, key=lambda ex: ex.triggered_at, reverse=True)

        return history[:limit]

    def clear_history(self) -> None:
        """Limpa histórico de execuções"""
        self.execution_history.clear()
