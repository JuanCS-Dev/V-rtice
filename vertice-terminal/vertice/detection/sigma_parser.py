"""
📊 Sigma Parser - Log detection rules

Integra com backend log_analysis_service para matching distribuído.

Sigma: https://github.com/SigmaHQ/sigma
Format: YAML-based detection rules para logs (Windows Event, Sysmon, Linux, etc)

Exemplo Sigma rule:
```yaml
title: Suspicious PowerShell Download
status: experimental
logsource:
    product: windows
    service: powershell
detection:
    selection:
        EventID: 4104
        ScriptBlockText|contains:
            - 'System.Net.WebClient'
            - 'DownloadFile'
    condition: selection
level: medium
```
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import yaml
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class SigmaRule:
    """
    Regra Sigma parseada
    """
    name: str  # title
    id: str
    description: str
    status: str  # experimental, test, stable
    level: str  # informational, low, medium, high, critical

    # Logsource
    logsource: Dict[str, str] = field(default_factory=dict)

    # Detection logic
    detection: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    references: List[str] = field(default_factory=list)
    falsepositives: List[str] = field(default_factory=list)

    # Original YAML
    raw_rule: Dict[str, Any] = field(default_factory=dict)


class SigmaParser:
    """
    Parser de regras Sigma com integração backend

    Features:
    - Parse de regras Sigma YAML
    - Match contra log events
    - Backend integration para scale
    - Condition evaluation
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do log_analysis_service
            use_backend: Se True, usa backend para matching (recomendado)
        """
        self.backend_url = backend_url or "http://localhost:8002"
        self.use_backend = use_backend

        # Regras carregadas
        self.rules: Dict[str, SigmaRule] = {}

    def load_rule(self, rule_path: Path) -> SigmaRule:
        """
        Carrega regra Sigma de arquivo YAML

        Args:
            rule_path: Path para .yml/.yaml

        Returns:
            SigmaRule parseada

        Raises:
            ValueError: Se regra inválida
        """
        with open(rule_path, "r") as f:
            data = yaml.safe_load(f)

        rule = self._parse_rule(data)
        self.rules[rule.id] = rule

        logger.info(f"Loaded Sigma rule: {rule.name}")
        return rule

    def _parse_rule(self, data: Dict[str, Any]) -> SigmaRule:
        """
        Parse de dicionário YAML para SigmaRule

        Args:
            data: Dicionário do YAML

        Returns:
            SigmaRule object
        """
        # Required fields
        title = data.get("title", "Unnamed Rule")
        rule_id = data.get("id", f"sigma_{hash(title)}")
        description = data.get("description", "")
        status = data.get("status", "experimental")
        level = data.get("level", "medium")

        # Logsource
        logsource = data.get("logsource", {})

        # Detection
        detection = data.get("detection", {})

        # Metadata
        tags = data.get("tags", [])
        author = data.get("author")
        references = data.get("references", [])
        falsepositives = data.get("falsepositives", [])

        rule = SigmaRule(
            name=title,
            id=rule_id,
            description=description,
            status=status,
            level=level,
            logsource=logsource,
            detection=detection,
            tags=tags,
            author=author,
            references=references,
            falsepositives=falsepositives,
            raw_rule=data,
        )

        return rule

    def match(self, log_entry: Dict[str, Any]) -> List[SigmaRule]:
        """
        Testa log entry contra todas as regras carregadas

        Args:
            log_entry: Dicionário com campos do log

        Returns:
            Lista de regras que matcharam
        """
        if self.use_backend:
            try:
                return self._match_backend(log_entry)
            except Exception as e:
                logger.warning(f"Backend match failed, falling back to local: {e}")

        # Fallback: match local
        return self._match_local(log_entry)

    def _match_local(self, log_entry: Dict[str, Any]) -> List[SigmaRule]:
        """
        Match local (sem backend)

        Args:
            log_entry: Log event

        Returns:
            Lista de SigmaRule que matcharam
        """
        matches = []

        for rule in self.rules.values():
            if self._evaluate_rule(rule, log_entry):
                matches.append(rule)

        return matches

    def _match_backend(self, log_entry: Dict[str, Any]) -> List[SigmaRule]:
        """
        Match via log_analysis_service backend

        Args:
            log_entry: Log event

        Returns:
            Lista de SigmaRule que matcharam
        """
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/logs/sigma-match",
                    json={
                        "log_entry": log_entry,
                        "rules": [rule.raw_rule for rule in self.rules.values()],
                    }
                )
                response.raise_for_status()

                result = response.json()

                # Parse matched rule IDs
                matched_rule_ids = result.get("matched_rules", [])

                matches = [
                    self.rules[rule_id]
                    for rule_id in matched_rule_ids
                    if rule_id in self.rules
                ]

                return matches

        except Exception as e:
            logger.error(f"Backend Sigma match failed: {e}")
            raise

    def _evaluate_rule(self, rule: SigmaRule, log_entry: Dict[str, Any]) -> bool:
        """
        Avalia regra contra log entry (local evaluation)

        Args:
            rule: SigmaRule
            log_entry: Log event

        Returns:
            True se match
        """
        detection = rule.detection

        # Get condition
        condition = detection.get("condition")
        if not condition:
            logger.warning(f"Rule {rule.name} has no condition")
            return False

        # Evaluate selections
        selections = {}
        for key, value in detection.items():
            if key == "condition":
                continue

            # Cada selection é um dict de field: value
            if isinstance(value, dict):
                selections[key] = self._evaluate_selection(value, log_entry)
            else:
                selections[key] = False

        # Evaluate condition expression
        return self._evaluate_condition(condition, selections)

    def _evaluate_selection(
        self,
        selection: Dict[str, Any],
        log_entry: Dict[str, Any]
    ) -> bool:
        """
        Avalia selection (AND entre campos)

        Args:
            selection: Dict de field: value
            log_entry: Log event

        Returns:
            True se todos os campos matcham
        """
        for field, expected_value in selection.items():
            # Get actual value from log
            actual_value = self._get_field_value(log_entry, field)

            if actual_value is None:
                return False

            # Check match
            if not self._field_matches(field, actual_value, expected_value):
                return False

        return True

    def _get_field_value(self, log_entry: Dict[str, Any], field: str) -> Any:
        """
        Obtém valor de campo do log (suporta nested)

        Args:
            log_entry: Log event
            field: Campo (pode ter modifiers: EventID, ScriptBlockText|contains)

        Returns:
            Valor do campo ou None
        """
        # Remove modifiers
        base_field = field.split("|")[0]

        # Nested fields
        parts = base_field.split(".")
        value = log_entry

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _field_matches(self, field: str, actual_value: Any, expected_value: Any) -> bool:
        """
        Verifica se field value matcha expected value

        Suporta modifiers:
        - contains: substring match
        - startswith: prefix match
        - endswith: suffix match
        - re: regex match

        Args:
            field: Nome do campo com optional modifier
            actual_value: Valor atual
            expected_value: Valor esperado (pode ser list)

        Returns:
            True se matcha
        """
        # Parse modifier
        modifier = None
        if "|" in field:
            modifier = field.split("|")[1]

        # Expected value pode ser lista (OR)
        if isinstance(expected_value, list):
            return any(
                self._value_matches(actual_value, val, modifier)
                for val in expected_value
            )

        return self._value_matches(actual_value, expected_value, modifier)

    def _value_matches(self, actual: Any, expected: Any, modifier: Optional[str]) -> bool:
        """
        Compara valores com modifier

        Args:
            actual: Valor atual
            expected: Valor esperado
            modifier: Modifier (contains, startswith, etc)

        Returns:
            True se matcha
        """
        # Convert to string for comparison
        actual_str = str(actual).lower() if actual else ""
        expected_str = str(expected).lower()

        if modifier == "contains":
            return expected_str in actual_str

        elif modifier == "startswith":
            return actual_str.startswith(expected_str)

        elif modifier == "endswith":
            return actual_str.endswith(expected_str)

        elif modifier == "re":
            return re.search(expected_str, actual_str, re.IGNORECASE) is not None

        else:
            # Exact match (case insensitive)
            return actual_str == expected_str

    def _evaluate_condition(self, condition: str, selections: Dict[str, bool]) -> bool:
        """
        Avalia condition expression

        Suporta:
        - selection
        - selection1 and selection2
        - selection1 or selection2
        - not selection
        - 1 of selection*  (any)
        - all of selection*

        Args:
            condition: Expressão
            selections: Dict {selection_name: bool}

        Returns:
            True se condition passou
        """
        # Simple cases
        if condition in selections:
            return selections[condition]

        # AND
        if " and " in condition:
            parts = condition.split(" and ")
            return all(self._evaluate_condition(p.strip(), selections) for p in parts)

        # OR
        if " or " in condition:
            parts = condition.split(" or ")
            return any(self._evaluate_condition(p.strip(), selections) for p in parts)

        # NOT
        if condition.startswith("not "):
            inner = condition[4:].strip()
            return not self._evaluate_condition(inner, selections)

        # 1 of selection*
        if condition.startswith("1 of "):
            pattern = condition[5:].strip()
            matching = self._get_matching_selections(pattern, selections)
            return any(matching.values())

        # all of selection*
        if condition.startswith("all of "):
            pattern = condition[7:].strip()
            matching = self._get_matching_selections(pattern, selections)
            return all(matching.values()) if matching else False

        logger.warning(f"Unknown condition format: {condition}")
        return False

    def _get_matching_selections(
        self,
        pattern: str,
        selections: Dict[str, bool]
    ) -> Dict[str, bool]:
        """
        Retorna selections que matcham pattern (wildcard)

        Args:
            pattern: Pattern (ex: "selection*")
            selections: Todas as selections

        Returns:
            Dict de selections que matcham
        """
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return {
                name: value
                for name, value in selections.items()
                if name.startswith(prefix)
            }

        return {pattern: selections.get(pattern, False)}

    def get_rules_by_logsource(
        self,
        product: Optional[str] = None,
        service: Optional[str] = None,
    ) -> List[SigmaRule]:
        """
        Filtra regras por logsource

        Args:
            product: Produto (windows, linux, etc)
            service: Service (sysmon, powershell, etc)

        Returns:
            Lista de SigmaRule
        """
        matching_rules = []

        for rule in self.rules.values():
            logsource = rule.logsource

            if product and logsource.get("product") != product:
                continue

            if service and logsource.get("service") != service:
                continue

            matching_rules.append(rule)

        return matching_rules

    def get_rule(self, rule_id: str) -> Optional[SigmaRule]:
        """
        Retorna regra por ID

        Args:
            rule_id: ID da regra

        Returns:
            SigmaRule ou None
        """
        return self.rules.get(rule_id)

    def list_rules(self) -> List[SigmaRule]:
        """
        Lista todas as regras carregadas

        Returns:
            Lista de SigmaRule
        """
        return list(self.rules.values())
