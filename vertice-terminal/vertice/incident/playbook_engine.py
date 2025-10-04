"""
📖 Playbook Engine - Automação de resposta a incidentes

Executa playbooks (runbooks) de resposta automatizada.

Playbook structure (YAML):
```yaml
name: Ransomware Response
trigger: incident.category == "ransomware"
steps:
  - name: Isolate affected systems
    action: isolate_endpoint
    parameters:
      endpoint_id: "{{ incident.affected_systems[0] }}"
  - name: Create SOAR incident
    action: create_soar_incident
    parameters:
      severity: critical
  - name: Notify security team
    action: send_notification
    parameters:
      channel: slack
      message: "Ransomware detected!"
```
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
import yaml
import asyncio
import logging

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status de execução de step"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlaybookStatus(Enum):
    """Status de execução de playbook"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class PlaybookStep:
    """
    Step individual de playbook
    """
    name: str
    action: str  # Action type (isolate_endpoint, create_incident, etc)
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Execution
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)

    # Conditional execution
    condition: Optional[str] = None  # Expression to evaluate
    on_failure: str = "stop"  # stop, continue, retry

    # Retry config
    max_retries: int = 0
    retry_count: int = 0
    retry_delay_seconds: int = 10


@dataclass
class PlaybookExecution:
    """
    Execução de playbook
    """
    id: str
    playbook_name: str
    status: PlaybookStatus
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Context
    incident_id: Optional[str] = None
    triggered_by: str = "manual"
    context: Dict[str, Any] = field(default_factory=dict)

    # Steps execution
    steps: List[PlaybookStep] = field(default_factory=list)
    current_step_index: int = 0

    # Results
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0


@dataclass
class Playbook:
    """
    Playbook de resposta
    """
    name: str
    description: str
    version: str = "1.0"

    # Trigger conditions
    trigger_conditions: List[str] = field(default_factory=list)
    trigger_events: List[str] = field(default_factory=list)

    # Steps
    steps: List[PlaybookStep] = field(default_factory=list)

    # Metadata
    author: str = ""
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    # Approval requirements
    requires_approval: bool = False
    approved_by: Optional[str] = None


class PlaybookEngine:
    """
    Playbook Execution Engine

    Features:
    - YAML playbook loading
    - Conditional execution
    - Error handling and retries
    - Variable substitution
    - Approval workflows
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        dry_run: bool = False,
    ):
        """
        Args:
            backend_url: URL do playbook_service
            use_backend: Se True, usa backend
            dry_run: Se True, não executa ações reais
        """
        self.backend_url = backend_url or "http://localhost:8010"
        self.use_backend = use_backend
        self.dry_run = dry_run

        # Loaded playbooks
        self.playbooks: Dict[str, Playbook] = {}

        # Action handlers
        self.action_handlers: Dict[str, Callable] = {}
        self._register_default_actions()

        # Execution history
        self.executions: List[PlaybookExecution] = []

    def load_playbook(self, playbook_path: Path) -> Playbook:
        """
        Carrega playbook de arquivo YAML

        Args:
            playbook_path: Path para .yaml

        Returns:
            Playbook object
        """
        with open(playbook_path, "r") as f:
            data = yaml.safe_load(f)

        playbook = self._parse_playbook(data)
        self.playbooks[playbook.name] = playbook

        logger.info(f"Playbook loaded: {playbook.name} ({len(playbook.steps)} steps)")

        return playbook

    def _parse_playbook(self, data: Dict[str, Any]) -> Playbook:
        """
        Parse YAML data para Playbook object

        Args:
            data: YAML dict

        Returns:
            Playbook
        """
        # Parse steps
        steps = []
        for step_data in data.get("steps", []):
            step = PlaybookStep(
                name=step_data.get("name", "Unnamed Step"),
                action=step_data.get("action"),
                parameters=step_data.get("parameters", {}),
                condition=step_data.get("condition"),
                on_failure=step_data.get("on_failure", "stop"),
                max_retries=step_data.get("max_retries", 0),
                retry_delay_seconds=step_data.get("retry_delay", 10),
            )
            steps.append(step)

        playbook = Playbook(
            name=data.get("name", "Unnamed Playbook"),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            trigger_conditions=data.get("trigger_conditions", []),
            trigger_events=data.get("trigger_events", []),
            steps=steps,
            author=data.get("author", ""),
            tags=data.get("tags", []),
            enabled=data.get("enabled", True),
            requires_approval=data.get("requires_approval", False),
        )

        return playbook

    async def execute_playbook(
        self,
        playbook_name: str,
        context: Dict[str, Any],
        incident_id: Optional[str] = None,
    ) -> PlaybookExecution:
        """
        Executa playbook

        Args:
            playbook_name: Nome do playbook
            context: Contexto de execução (variáveis)
            incident_id: ID do incidente relacionado

        Returns:
            PlaybookExecution object
        """
        playbook = self.playbooks.get(playbook_name)

        if not playbook:
            raise ValueError(f"Playbook not found: {playbook_name}")

        if not playbook.enabled:
            raise ValueError(f"Playbook is disabled: {playbook_name}")

        # Check approval
        if playbook.requires_approval and not playbook.approved_by:
            raise ValueError(f"Playbook requires approval: {playbook_name}")

        # Create execution
        import uuid

        execution = PlaybookExecution(
            id=f"exec-{uuid.uuid4().hex[:8]}",
            playbook_name=playbook_name,
            status=PlaybookStatus.RUNNING,
            started_at=datetime.now(),
            incident_id=incident_id,
            context=context,
            steps=[
                PlaybookStep(
                    name=s.name,
                    action=s.action,
                    parameters=s.parameters.copy(),
                    condition=s.condition,
                    on_failure=s.on_failure,
                    max_retries=s.max_retries,
                )
                for s in playbook.steps
            ],
        )

        logger.info(
            f"Executing playbook: {playbook_name} "
            f"(execution_id: {execution.id}, dry_run: {self.dry_run})"
        )

        # Execute steps sequentially
        for idx, step in enumerate(execution.steps):
            execution.current_step_index = idx

            # Check condition
            if step.condition:
                if not self._evaluate_condition(step.condition, context):
                    step.status = StepStatus.SKIPPED
                    execution.skipped_count += 1
                    logger.info(f"Step skipped (condition not met): {step.name}")
                    continue

            # Execute step with retries
            step.status = StepStatus.RUNNING
            step.started_at = datetime.now()

            success = await self._execute_step(step, context)

            if success:
                step.status = StepStatus.SUCCESS
                execution.success_count += 1
                step.completed_at = datetime.now()
            else:
                step.status = StepStatus.FAILED
                execution.failed_count += 1
                step.completed_at = datetime.now()

                # Handle failure
                if step.on_failure == "stop":
                    logger.error(f"Step failed, stopping playbook: {step.name}")
                    execution.status = PlaybookStatus.FAILED
                    break
                elif step.on_failure == "continue":
                    logger.warning(f"Step failed, continuing: {step.name}")
                    continue
                # retry handled in _execute_step

        # Finalize execution
        if execution.status != PlaybookStatus.FAILED:
            execution.status = PlaybookStatus.COMPLETED

        execution.completed_at = datetime.now()

        self.executions.append(execution)

        logger.info(
            f"Playbook execution completed: {playbook_name} "
            f"(success: {execution.success_count}, failed: {execution.failed_count})"
        )

        return execution

    async def _execute_step(
        self,
        step: PlaybookStep,
        context: Dict[str, Any]
    ) -> bool:
        """
        Executa step individual com retries

        Args:
            step: PlaybookStep
            context: Execution context

        Returns:
            True se sucesso
        """
        for attempt in range(step.max_retries + 1):
            if attempt > 0:
                logger.info(f"Retrying step: {step.name} (attempt {attempt + 1})")
                await asyncio.sleep(step.retry_delay_seconds)

            try:
                # Substitute variables
                parameters = self._substitute_variables(step.parameters, context)

                # Dry run check
                if self.dry_run:
                    logger.info(f"DRY RUN: Would execute {step.action} with {parameters}")
                    step.result = {"dry_run": True, "action": step.action}
                    return True

                # Get action handler
                handler = self.action_handlers.get(step.action)

                if not handler:
                    step.error = f"Unknown action: {step.action}"
                    return False

                # Execute action
                result = await handler(parameters)

                step.result = result
                return True

            except Exception as e:
                step.error = str(e)
                logger.error(f"Step execution error: {step.name} - {e}")

                step.retry_count = attempt + 1

                if attempt >= step.max_retries:
                    return False

        return False

    def _substitute_variables(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Substitui variáveis em parameters ({{ var }})

        Args:
            parameters: Parameters dict
            context: Context variables

        Returns:
            Parameters with substituted values
        """
        import re
        import json

        # Serialize to JSON for regex replacement
        params_json = json.dumps(parameters)

        # Find all {{ variable }} patterns
        pattern = r'\{\{\s*([^}]+)\s*\}\}'

        def replace_var(match):
            var_path = match.group(1).strip()

            # Navigate nested context
            value = context
            for key in var_path.split("."):
                # Handle array indexing
                if "[" in key:
                    key_name = key.split("[")[0]
                    index = int(key.split("[")[1].rstrip("]"))
                    value = value.get(key_name, [])[index]
                else:
                    value = value.get(key, "")

            return json.dumps(value) if not isinstance(value, str) else value

        params_json = re.sub(pattern, replace_var, params_json)

        return json.loads(params_json)

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Avalia condição (expression simples)

        Args:
            condition: Condition expression
            context: Context variables

        Returns:
            True se condição verdadeira
        """
        # Simple condition evaluation
        # TODO: Implement safe expression evaluator

        try:
            # Very basic evaluation (UNSAFE - for demo only)
            # In production, use ast.literal_eval or safe parser

            # Replace variables
            for key, value in context.items():
                condition = condition.replace(f"${key}", repr(value))

            # Evaluate (UNSAFE!)
            # result = eval(condition)

            # For now, always return True (placeholder)
            return True

        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False

    def _register_default_actions(self):
        """Registra action handlers padrão"""
        self.register_action("isolate_endpoint", self._action_isolate_endpoint)
        self.register_action("block_ip", self._action_block_ip)
        self.register_action("create_soar_incident", self._action_create_soar_incident)
        self.register_action("send_notification", self._action_send_notification)
        self.register_action("collect_evidence", self._action_collect_evidence)
        self.register_action("run_query", self._action_run_query)

    def register_action(self, action_name: str, handler: Callable):
        """
        Registra custom action handler

        Args:
            action_name: Action name
            handler: Async function
        """
        self.action_handlers[action_name] = handler

    # Default action handlers

    async def _action_isolate_endpoint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Isola endpoint da rede"""
        endpoint_id = params.get("endpoint_id")

        logger.info(f"Isolating endpoint: {endpoint_id}")

        # TODO: Integrate com endpoint agent
        return {"status": "isolated", "endpoint_id": endpoint_id}

    async def _action_block_ip(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Bloqueia IP no firewall"""
        ip_address = params.get("ip_address")

        logger.info(f"Blocking IP: {ip_address}")

        # TODO: Integrate com firewall API
        return {"status": "blocked", "ip": ip_address}

    async def _action_create_soar_incident(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cria incidente no SOAR"""
        severity = params.get("severity", "medium")
        title = params.get("title", "Automated Incident")

        logger.info(f"Creating SOAR incident: {title}")

        # TODO: Integrate com SOAR connectors
        return {"incident_id": "SOAR-12345", "title": title}

    async def _action_send_notification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Envia notificação"""
        channel = params.get("channel", "slack")
        message = params.get("message", "Alert from playbook")

        logger.info(f"Sending notification to {channel}: {message}")

        # TODO: Integrate com notification service
        return {"status": "sent", "channel": channel}

    async def _action_collect_evidence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Coleta evidências"""
        endpoint_id = params.get("endpoint_id")
        evidence_types = params.get("types", ["memory", "disk", "logs"])

        logger.info(f"Collecting evidence from {endpoint_id}: {evidence_types}")

        # TODO: Integrate com evidence collector
        return {"evidence_collected": evidence_types, "endpoint": endpoint_id}

    async def _action_run_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa query VeQL"""
        query = params.get("query")

        logger.info(f"Running query: {query}")

        # TODO: Integrate com Query Engine
        return {"results": [], "query": query}

    def get_execution(self, execution_id: str) -> Optional[PlaybookExecution]:
        """Retorna execução por ID"""
        for execution in self.executions:
            if execution.id == execution_id:
                return execution
        return None

    def list_executions(
        self,
        playbook_name: Optional[str] = None,
        status: Optional[PlaybookStatus] = None,
        limit: int = 50,
    ) -> List[PlaybookExecution]:
        """Lista execuções"""
        executions = self.executions

        if playbook_name:
            executions = [e for e in executions if e.playbook_name == playbook_name]

        if status:
            executions = [e for e in executions if e.status == status]

        # Sort by start time (most recent first)
        executions = sorted(executions, key=lambda e: e.started_at, reverse=True)

        return executions[:limit]
