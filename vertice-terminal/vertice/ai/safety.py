"""
🛡️ Safety Guard - Valida e protege comandos perigosos

Previne execução de comandos maliciosos ou destrutivos.
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Nível de risco de um comando"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyCheck:
    """Resultado de validação de segurança"""
    is_safe: bool
    risk_level: RiskLevel
    warnings: List[str]
    blocked_reasons: List[str]


class SafetyGuard:
    """
    Guard de segurança para comandos da IA
    """

    # Palavras-chave perigosas
    DANGEROUS_KEYWORDS = [
        "rm -rf",
        "delete",
        "drop table",
        "truncate",
        "format",
        "shutdown",
        "reboot",
        "--force",
        "sudo rm",
    ]

    # Comandos destrutivos
    DESTRUCTIVE_COMMANDS = [
        "isolate",
        "block",
        "kill",
        "terminate",
        "disable",
        "quarantine",
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Args:
            strict_mode: Se True, bloqueia comandos arriscados
        """
        self.strict_mode = strict_mode
        self.audit_log: List[dict] = []

    def validate_query(self, veql_query: str) -> SafetyCheck:
        """
        Valida query VeQL

        Args:
            veql_query: Query VeQL para validar

        Returns:
            SafetyCheck com resultado
        """
        warnings = []
        blocked = []

        query_lower = veql_query.lower()

        # VeQL é read-only, então é sempre seguro
        risk_level = RiskLevel.SAFE

        # Verifica se é muito ampla (pode sobrecarregar)
        if "select *" in query_lower and "limit" not in query_lower:
            warnings.append("Query selects all fields without LIMIT - may return many results")
            risk_level = RiskLevel.LOW

        # Verifica se tem WHERE (filtros)
        if "where" not in query_lower:
            warnings.append("Query has no WHERE clause - will scan all endpoints")
            risk_level = RiskLevel.LOW

        is_safe = len(blocked) == 0

        return SafetyCheck(
            is_safe=is_safe,
            risk_level=risk_level,
            warnings=warnings,
            blocked_reasons=blocked,
        )

    def validate_command(
        self,
        command: str,
        parameters: dict
    ) -> SafetyCheck:
        """
        Valida comando antes de executar

        Args:
            command: Nome do comando
            parameters: Parâmetros do comando

        Returns:
            SafetyCheck com resultado
        """
        warnings = []
        blocked = []

        command_lower = command.lower()

        # Verifica se é destrutivo
        is_destructive = any(
            danger in command_lower
            for danger in self.DESTRUCTIVE_COMMANDS
        )

        if is_destructive:
            risk_level = RiskLevel.HIGH
            warnings.append(f"Command '{command}' is DESTRUCTIVE")

            if self.strict_mode:
                blocked.append("Destructive commands require explicit user approval")

        else:
            risk_level = RiskLevel.SAFE

        # Verifica parâmetros perigosos
        params_str = str(parameters).lower()

        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in params_str:
                risk_level = RiskLevel.CRITICAL
                warnings.append(f"Dangerous keyword detected: {keyword}")
                blocked.append(f"Blocked due to dangerous keyword: {keyword}")

        is_safe = len(blocked) == 0

        # Audit log
        self.audit_log.append({
            "command": command,
            "parameters": parameters,
            "risk_level": risk_level.value,
            "is_safe": is_safe,
            "warnings": warnings,
        })

        return SafetyCheck(
            is_safe=is_safe,
            risk_level=risk_level,
            warnings=warnings,
            blocked_reasons=blocked,
        )

    def validate_tool_call(
        self,
        tool_name: str,
        parameters: dict
    ) -> SafetyCheck:
        """
        Valida chamada de ferramenta

        Args:
            tool_name: Nome da ferramenta
            parameters: Parâmetros

        Returns:
            SafetyCheck com resultado
        """
        # Por enquanto, delegate para validate_command
        return self.validate_command(tool_name, parameters)

    def get_audit_log(self) -> List[dict]:
        """Retorna audit log completo"""
        return self.audit_log.copy()

    def clear_audit_log(self) -> None:
        """Limpa audit log"""
        self.audit_log.clear()
