"""
📜 Policy Engine - Motor de políticas DLP

Define e executa políticas de prevenção de perda de dados.

Policy Types:
- Content-based (tipo de conteúdo detectado)
- Classification-based (nível de classificação)
- Context-based (localização, hora, usuário)
- Action-based (upload, download, email, print)

Actions:
- Block (bloquear completamente)
- Alert (permitir mas alertar)
- Quarantine (mover para quarentena)
- Encrypt (forçar encriptação)
- Watermark (adicionar marca d'água)
- Audit (apenas auditar)

Features:
- Rule-based policies
- Condition evaluation
- Action execution
- Exception handling
- Policy inheritance
- Audit logging
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime, time as dt_time
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """Ações de política DLP"""
    ALLOW = "allow"  # Permitir
    BLOCK = "block"  # Bloquear
    ALERT = "alert"  # Alertar (permitir mas notificar)
    QUARANTINE = "quarantine"  # Quarentena
    ENCRYPT = "encrypt"  # Forçar encriptação
    WATERMARK = "watermark"  # Adicionar marca d'água
    AUDIT = "audit"  # Apenas auditar
    REQUIRE_JUSTIFICATION = "require_justification"  # Requerer justificativa


class PolicyScope(Enum):
    """Escopo da política"""
    EMAIL = "email"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    PRINT = "print"
    USB_TRANSFER = "usb_transfer"
    CLOUD_STORAGE = "cloud_storage"
    CLIPBOARD = "clipboard"
    SCREEN_CAPTURE = "screen_capture"
    ALL = "all"


class ConditionOperator(Enum):
    """Operadores de condição"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    MATCHES_REGEX = "matches_regex"


@dataclass
class PolicyCondition:
    """
    Condição de política

    Attributes:
        field: Campo a verificar (classification_level, data_type, user, etc)
        operator: Operador de comparação
        value: Valor para comparar
        negate: Se True, nega a condição
    """
    field: str
    operator: ConditionOperator
    value: Any
    negate: bool = False


@dataclass
class DLPPolicy:
    """
    Política DLP

    Attributes:
        id: Policy ID
        name: Policy name
        description: Policy description
        scope: Policy scope
        action: Action to take
        conditions: Conditions to match
        exceptions: Exception conditions
        enabled: If policy is enabled
        priority: Priority (higher = evaluated first)
        notify_users: Users to notify
        notify_groups: Groups to notify
        require_approval: If action requires approval
        justification_required: If justification is required
    """
    id: str
    name: str
    description: str
    scope: PolicyScope
    action: PolicyAction

    # Conditions
    conditions: List[PolicyCondition] = field(default_factory=list)
    exceptions: List[PolicyCondition] = field(default_factory=list)

    # Configuration
    enabled: bool = True
    priority: int = 0

    # Notifications
    notify_users: List[str] = field(default_factory=list)
    notify_groups: List[str] = field(default_factory=list)

    # Approval workflow
    require_approval: bool = False
    approvers: List[str] = field(default_factory=list)

    # Justification
    justification_required: bool = False

    # Time-based
    active_hours_start: Optional[dt_time] = None
    active_hours_end: Optional[dt_time] = None
    active_days: List[int] = field(default_factory=list)  # 0=Monday, 6=Sunday

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)


@dataclass
class PolicyEvaluationResult:
    """
    Resultado de avaliação de política

    Attributes:
        policy_id: Policy ID
        matched: If policy matched
        action: Action to take
        reason: Reason for decision
        conditions_matched: Conditions that matched
        exceptions_matched: Exceptions that matched
        requires_approval: If approval is required
        requires_justification: If justification is required
    """
    policy_id: str
    matched: bool
    action: PolicyAction
    reason: str

    conditions_matched: List[str] = field(default_factory=list)
    exceptions_matched: List[str] = field(default_factory=list)

    requires_approval: bool = False
    requires_justification: bool = False
    approvers: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """
    DLP Policy Engine

    Features:
    - Policy evaluation
    - Condition matching
    - Action execution
    - Exception handling
    - Approval workflows
    - Audit logging
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do dlp_service
            use_backend: Se True, usa backend
        """
        self.backend_url = backend_url or "http://localhost:8022"
        self.use_backend = use_backend

        # Policy registry
        self.policies: Dict[str, DLPPolicy] = {}

        # Policy execution history
        self.execution_history: List[Dict[str, Any]] = []

        # Load default policies
        self._load_default_policies()

    def _load_default_policies(self):
        """Carrega políticas padrão"""

        from vertice.dlp.data_classifier import ClassificationLevel
        from vertice.dlp.content_inspector import SensitiveDataType

        default_policies = [
            DLPPolicy(
                id="policy-block-top-secret-email",
                name="Block Top Secret via Email",
                description="Block sending top secret documents via email",
                scope=PolicyScope.EMAIL,
                action=PolicyAction.BLOCK,
                conditions=[
                    PolicyCondition(
                        field="classification_level",
                        operator=ConditionOperator.EQUALS,
                        value=ClassificationLevel.TOP_SECRET.value,
                    ),
                ],
                priority=100,
                notify_users=["security-team"],
            ),
            DLPPolicy(
                id="policy-alert-restricted-upload",
                name="Alert on Restricted Data Upload",
                description="Alert when restricted data is uploaded to cloud",
                scope=PolicyScope.CLOUD_STORAGE,
                action=PolicyAction.ALERT,
                conditions=[
                    PolicyCondition(
                        field="classification_level",
                        operator=ConditionOperator.IN_LIST,
                        value=[
                            ClassificationLevel.RESTRICTED.value,
                            ClassificationLevel.CONFIDENTIAL.value,
                        ],
                    ),
                ],
                priority=80,
                notify_users=["security-team", "data-owner"],
            ),
            DLPPolicy(
                id="policy-block-credit-cards",
                name="Block Credit Card Transmission",
                description="Block transmission of credit card numbers",
                scope=PolicyScope.ALL,
                action=PolicyAction.BLOCK,
                conditions=[
                    PolicyCondition(
                        field="sensitive_data_type",
                        operator=ConditionOperator.CONTAINS,
                        value=SensitiveDataType.CREDIT_CARD.value,
                    ),
                ],
                priority=95,
                notify_users=["compliance-team"],
            ),
            DLPPolicy(
                id="policy-encrypt-pii-email",
                name="Require Encryption for PII",
                description="Require encryption when emailing PII",
                scope=PolicyScope.EMAIL,
                action=PolicyAction.ENCRYPT,
                conditions=[
                    PolicyCondition(
                        field="sensitive_data_type",
                        operator=ConditionOperator.IN_LIST,
                        value=[
                            SensitiveDataType.SSN.value,
                            SensitiveDataType.CPF.value,
                        ],
                    ),
                ],
                priority=85,
            ),
            DLPPolicy(
                id="policy-justify-confidential-usb",
                name="Require Justification for USB Transfer",
                description="Require justification when copying confidential data to USB",
                scope=PolicyScope.USB_TRANSFER,
                action=PolicyAction.REQUIRE_JUSTIFICATION,
                conditions=[
                    PolicyCondition(
                        field="classification_level",
                        operator=ConditionOperator.IN_LIST,
                        value=[
                            ClassificationLevel.CONFIDENTIAL.value,
                            ClassificationLevel.RESTRICTED.value,
                        ],
                    ),
                ],
                priority=70,
                justification_required=True,
            ),
        ]

        for policy in default_policies:
            self.policies[policy.id] = policy

        logger.info(f"Loaded {len(default_policies)} default DLP policies")

    def add_policy(self, policy: DLPPolicy) -> None:
        """
        Adiciona política

        Args:
            policy: DLPPolicy object
        """
        self.policies[policy.id] = policy
        logger.info(f"Added DLP policy: {policy.name} ({policy.id})")

    def remove_policy(self, policy_id: str) -> bool:
        """Remove política"""
        if policy_id in self.policies:
            del self.policies[policy_id]
            logger.info(f"Removed DLP policy: {policy_id}")
            return True
        return False

    def evaluate_policies(
        self,
        scope: PolicyScope,
        context: Dict[str, Any],
    ) -> List[PolicyEvaluationResult]:
        """
        Avalia políticas para um contexto

        Args:
            scope: Policy scope
            context: Context dictionary with fields to evaluate

        Returns:
            List of PolicyEvaluationResult (matched policies)
        """
        results = []

        # Get applicable policies
        applicable_policies = [
            p for p in self.policies.values()
            if p.enabled and (p.scope == scope or p.scope == PolicyScope.ALL)
        ]

        # Sort by priority
        applicable_policies = sorted(
            applicable_policies,
            key=lambda p: p.priority,
            reverse=True
        )

        logger.info(
            f"Evaluating {len(applicable_policies)} policies for scope: {scope.value}"
        )

        for policy in applicable_policies:
            result = self._evaluate_policy(policy, context)

            if result.matched:
                results.append(result)

                # If policy action is BLOCK, stop evaluation
                if policy.action == PolicyAction.BLOCK:
                    logger.info(f"Policy BLOCK action triggered, stopping evaluation")
                    break

        logger.info(f"Policy evaluation complete: {len(results)} policies matched")

        # Record execution
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "scope": scope.value,
            "policies_evaluated": len(applicable_policies),
            "policies_matched": len(results),
            "context": context,
        })

        return results

    def _evaluate_policy(
        self,
        policy: DLPPolicy,
        context: Dict[str, Any],
    ) -> PolicyEvaluationResult:
        """
        Avalia política individual

        Args:
            policy: DLPPolicy to evaluate
            context: Context data

        Returns:
            PolicyEvaluationResult
        """
        # Check time-based restrictions
        if not self._check_time_restrictions(policy):
            return PolicyEvaluationResult(
                policy_id=policy.id,
                matched=False,
                action=PolicyAction.ALLOW,
                reason="Policy not active at this time",
            )

        # Evaluate conditions
        conditions_matched = []
        all_conditions_met = True

        for condition in policy.conditions:
            if self._evaluate_condition(condition, context):
                conditions_matched.append(f"{condition.field} {condition.operator.value}")
            else:
                all_conditions_met = False
                break

        if not all_conditions_met:
            return PolicyEvaluationResult(
                policy_id=policy.id,
                matched=False,
                action=PolicyAction.ALLOW,
                reason="Policy conditions not met",
            )

        # Check exceptions
        exceptions_matched = []
        for exception in policy.exceptions:
            if self._evaluate_condition(exception, context):
                exceptions_matched.append(f"{exception.field} {exception.operator.value}")
                # Exception matched, policy doesn't apply
                return PolicyEvaluationResult(
                    policy_id=policy.id,
                    matched=False,
                    action=PolicyAction.ALLOW,
                    reason="Policy exception matched",
                    exceptions_matched=exceptions_matched,
                )

        # Policy matched
        result = PolicyEvaluationResult(
            policy_id=policy.id,
            matched=True,
            action=policy.action,
            reason=f"Policy matched: {policy.name}",
            conditions_matched=conditions_matched,
            requires_approval=policy.require_approval,
            requires_justification=policy.justification_required,
            approvers=policy.approvers,
        )

        logger.info(
            f"Policy matched: {policy.name} -> Action: {policy.action.value}"
        )

        return result

    def _evaluate_condition(
        self,
        condition: PolicyCondition,
        context: Dict[str, Any],
    ) -> bool:
        """Avalia condição individual"""

        field_value = context.get(condition.field)

        if field_value is None:
            return False

        result = False

        # Evaluate based on operator
        if condition.operator == ConditionOperator.EQUALS:
            result = field_value == condition.value

        elif condition.operator == ConditionOperator.NOT_EQUALS:
            result = field_value != condition.value

        elif condition.operator == ConditionOperator.CONTAINS:
            if isinstance(field_value, (list, set)):
                result = condition.value in field_value
            elif isinstance(field_value, str):
                result = condition.value in field_value
            else:
                result = False

        elif condition.operator == ConditionOperator.NOT_CONTAINS:
            if isinstance(field_value, (list, set)):
                result = condition.value not in field_value
            elif isinstance(field_value, str):
                result = condition.value not in field_value
            else:
                result = True

        elif condition.operator == ConditionOperator.IN_LIST:
            result = field_value in condition.value

        elif condition.operator == ConditionOperator.NOT_IN_LIST:
            result = field_value not in condition.value

        elif condition.operator == ConditionOperator.GREATER_THAN:
            try:
                result = float(field_value) > float(condition.value)
            except (ValueError, TypeError):
                result = False

        elif condition.operator == ConditionOperator.LESS_THAN:
            try:
                result = float(field_value) < float(condition.value)
            except (ValueError, TypeError):
                result = False

        # Apply negation if needed
        if condition.negate:
            result = not result

        return result

    def _check_time_restrictions(self, policy: DLPPolicy) -> bool:
        """Verifica restrições de horário"""

        now = datetime.now()

        # Check active hours
        if policy.active_hours_start and policy.active_hours_end:
            current_time = now.time()

            if not (policy.active_hours_start <= current_time <= policy.active_hours_end):
                return False

        # Check active days
        if policy.active_days:
            current_day = now.weekday()  # 0=Monday, 6=Sunday

            if current_day not in policy.active_days:
                return False

        return True

    def get_policy(self, policy_id: str) -> Optional[DLPPolicy]:
        """Retorna política por ID"""
        return self.policies.get(policy_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas"""

        # Count by action
        by_action = {}
        for policy in self.policies.values():
            action = policy.action.value
            by_action[action] = by_action.get(action, 0) + 1

        # Count by scope
        by_scope = {}
        for policy in self.policies.values():
            scope = policy.scope.value
            by_scope[scope] = by_scope.get(scope, 0) + 1

        enabled_count = len([p for p in self.policies.values() if p.enabled])

        return {
            "total_policies": len(self.policies),
            "enabled_policies": enabled_count,
            "by_action": by_action,
            "by_scope": by_scope,
            "total_executions": len(self.execution_history),
        }

    def list_policies(
        self,
        scope: Optional[PolicyScope] = None,
        action: Optional[PolicyAction] = None,
        enabled_only: bool = False,
    ) -> List[DLPPolicy]:
        """
        Lista políticas com filtros

        Args:
            scope: Filter by scope
            action: Filter by action
            enabled_only: Only enabled policies

        Returns:
            List of DLPPolicy
        """
        policies = list(self.policies.values())

        if scope:
            policies = [p for p in policies if p.scope == scope or p.scope == PolicyScope.ALL]

        if action:
            policies = [p for p in policies if p.action == action]

        if enabled_only:
            policies = [p for p in policies if p.enabled]

        # Sort by priority
        policies = sorted(policies, key=lambda p: p.priority, reverse=True)

        return policies
