"""
📝 Policy Parser - Parse YAML policies

Schema YAML:
```yaml
name: Auto-Block Ransomware
trigger:
  - event: file_encryption_detected
  - event: shadow_copy_deletion
conditions:
  - process.name IN ['vssadmin.exe', 'wmic.exe']
  - file.extension IN ['.encrypted', '.locked']
actions:
  - isolate_endpoint
  - kill_process
  - create_incident:
      severity: critical
```
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum


class TriggerType(Enum):
    """Tipo de trigger"""
    EVENT = "event"  # Evento detectado
    SCHEDULE = "schedule"  # Agendado (cron)
    MANUAL = "manual"  # Trigger manual


@dataclass
class Trigger:
    """Trigger de policy"""
    type: TriggerType
    value: str  # Nome do evento ou cron expression
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Condition:
    """Condição de policy"""
    expression: str  # Ex: "process.name = 'cmd.exe'"
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None


@dataclass
class Action:
    """Ação de policy"""
    name: str  # Nome da ação (isolate_endpoint, block_ip, etc)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """Policy completa"""
    name: str
    description: str
    enabled: bool
    triggers: List[Trigger]
    conditions: List[Condition]
    actions: List[Action]
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyParser:
    """
    Parser de policies YAML
    """

    @staticmethod
    def parse_file(policy_path: Path) -> Policy:
        """
        Parse policy de arquivo YAML

        Args:
            policy_path: Caminho do arquivo YAML

        Returns:
            Policy parseada

        Raises:
            ValueError: Se YAML inválido
        """
        with open(policy_path, "r") as f:
            data = yaml.safe_load(f)

        return PolicyParser.parse_dict(data)

    @staticmethod
    def parse_dict(data: Dict[str, Any]) -> Policy:
        """
        Parse policy de dicionário

        Args:
            data: Dicionário com policy

        Returns:
            Policy parseada
        """
        # Parse triggers
        triggers = []
        for trigger_data in data.get("trigger", []):
            if isinstance(trigger_data, dict):
                # Formato: {event: "name"}
                if "event" in trigger_data:
                    triggers.append(Trigger(
                        type=TriggerType.EVENT,
                        value=trigger_data["event"],
                    ))
                elif "schedule" in trigger_data:
                    triggers.append(Trigger(
                        type=TriggerType.SCHEDULE,
                        value=trigger_data["schedule"],
                    ))
            elif isinstance(trigger_data, str):
                # Formato simples: "event_name"
                triggers.append(Trigger(
                    type=TriggerType.EVENT,
                    value=trigger_data,
                ))

        # Parse conditions
        conditions = []
        for cond_expr in data.get("conditions", []):
            conditions.append(Condition(expression=cond_expr))

        # Parse actions
        actions = []
        for action_data in data.get("actions", []):
            if isinstance(action_data, str):
                # Ação simples: "isolate_endpoint"
                actions.append(Action(name=action_data))
            elif isinstance(action_data, dict):
                # Ação com parâmetros: {create_incident: {severity: critical}}
                for action_name, params in action_data.items():
                    actions.append(Action(
                        name=action_name,
                        parameters=params if isinstance(params, dict) else {},
                    ))

        # Cria policy
        policy = Policy(
            name=data.get("name", "Unnamed Policy"),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            triggers=triggers,
            conditions=conditions,
            actions=actions,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

        return policy

    @staticmethod
    def validate(policy: Policy) -> List[str]:
        """
        Valida policy

        Args:
            policy: Policy para validar

        Returns:
            Lista de erros (vazia se válida)
        """
        errors = []

        if not policy.name:
            errors.append("Policy must have a name")

        if not policy.triggers:
            errors.append("Policy must have at least one trigger")

        if not policy.actions:
            errors.append("Policy must have at least one action")

        # Valida expressões de condições
        for i, condition in enumerate(policy.conditions):
            if not condition.expression:
                errors.append(f"Condition {i} has empty expression")

        return errors
