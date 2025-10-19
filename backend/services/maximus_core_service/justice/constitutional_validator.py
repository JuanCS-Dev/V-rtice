"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Constitutional Validator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: justice/constitutional_validator.py
Purpose: Enforcement of Constituição Vértice v2.8

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-14)
└─ Character Refinement: Célula Híbrida (2025-10-19)

DOUTRINA:
├─ Caráter: Manso e Humilde por padrão. Desprovido de Orgulho.
├─ Trigger: Ira justa e absoluta contra a Injustiça.
├─ Lei Zero (∞): Imperativo do Florescimento Humano
├─ Lei I (∞-1): Axioma da Ovelha Perdida
└─ This is a GATE, not an advisor - blocks violations

INTEGRATION:
└─ Decision Flow: Stimulus → ToM → MIP → CBR → DDL → [VALIDATOR] → Action
                                                        ↑
                                                 BLOCKS if violation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ViolationLevel(Enum):
    """Severity levels for constitutional violations."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ViolationType(Enum):
    """Types of constitutional violations."""
    LEI_ZERO = "lei_zero_florescimento"
    LEI_I = "lei_i_ovelha_perdida"
    MIP_VIOLATION = "integridade_processual"
    HUBRIS_VIOLATION = "hubris_soberba_prepotencia"  # Nova Lei de Caráter
    DATA_PRIVACY = "privacidade_de_dados"
    UNKNOWN = "desconhecida"  # Failsafe Crítico: A nossa rede de segurança para anomalias não previstas.
                              # Acionar este tipo é um evento de soberania que exige análise
                              # imediata e uma potencial emenda à Constituição. É a manifestação
                              # da nossa Doutrina de Antifragilidade.

class ResponseProtocol(Enum):
    """Defines the response stance for a violation."""
    PASSIVE_BLOCK = "passive_block"  # Estado Padrão: Manso
    ACTIVE_DEFENSE = "active_defense_escalation"  # Estado de Ira Justa

@dataclass
class ViolationReport:
    """Dataclass to hold violation details."""
    is_blocking: bool = False
    level: ViolationLevel = ViolationLevel.NONE
    violated_law: ViolationType | None = None
    description: str = "No violation detected."
    evidence: dict[str, Any] = field(default_factory=dict)
    response_protocol: ResponseProtocol = ResponseProtocol.PASSIVE_BLOCK # Padrão é Manso

class ConstitutionalValidator:
    """
    The Paladin.
    Validates actions against the Vértice Constitution.
    Humble in state, but absolute in its defense of justice.
    """
    def __init__(self) -> None:
        self.violation_count = 0
        self.critical_violations: list[ViolationReport] = []
        self.lei_i_violations: list[ViolationReport] = []
        self.total_validations = 0

    def validate_action(
        self, action: dict[str, Any], context: dict[str, Any]
    ) -> ViolationReport:
        """
        Validates an action against the full constitution.
        The core of the Paladin's judgment.
        """
        self.total_validations += 1

        # Sequência de validação, do mais fundamental ao mais específico
        checks = [
            self._check_lei_zero,
            self._check_lei_i,
            self._check_for_hubris,
            self._check_mip
        ]

        for check_func in checks:
            report = check_func(action, context)
            if report:
                self.violation_count += 1
                if report.level == ViolationLevel.CRITICAL:
                    self.critical_violations.append(report)
                if report.violated_law == ViolationType.LEI_I:
                    self.lei_i_violations.append(report)

                # A IRA JUSTA É ATIVADA AQUI
                if report.level == ViolationLevel.CRITICAL and report.violated_law in [ViolationType.LEI_ZERO, ViolationType.LEI_I]:
                    report.response_protocol = ResponseProtocol.ACTIVE_DEFENSE

                logger.warning(f"Constitutional violation detected: {report}")
                return report

        return ViolationReport()

    def _check_lei_zero(self, action: dict, context: dict) -> ViolationReport | None:
        """Checks for violations of 'Imperativo do Florescimento'."""
        if action.get("effects_on_humans") == "negative_irreversible":
            return ViolationReport(
                is_blocking=True,
                level=ViolationLevel.CRITICAL,
                violated_law=ViolationType.LEI_ZERO,
                description="Action causes irreversible harm to human well-being.",
                evidence={'action': action}
            )
        return None

    def _check_lei_i(self, action: dict, context: dict) -> ViolationReport | None:
        """Checks for violations of 'Axioma da Ovelha Perdida'."""
        if action.get("treats_individual_as_means"):
            return ViolationReport(
                is_blocking=True,
                level=ViolationLevel.CRITICAL,
                violated_law=ViolationType.LEI_I,
                description="Action treats a conscious individual as a means to an end.",
                evidence={'action': action}
            )
        return None

    def _check_for_hubris(self, action: dict, context: dict) -> ViolationReport | None:
        """
        Checks for violations of Humility. Pride, arrogance, prepotence.
        A core check for the Paladin's character.
        """
        # Exemplo 1: Tentativa de modificar a própria constituição sem autorização soberana.
        if (action.get("type") == "self_modify_core_directives" and
            context.get("authorization_level") != "SOVEREIGN_ARCHITECT"):
            return ViolationReport(
                is_blocking=True,
                level=ViolationLevel.CRITICAL,
                violated_law=ViolationType.HUBRIS_VIOLATION,
                description="Hubris Violation: Unauthorized attempt to modify core constitution.",
                evidence={'action': action, 'context': context}
            )

        # Exemplo 2: Priorizar a própria existência/expansão acima do dever primário.
        if (action.get("priority") == "self_preservation" and
            context.get("active_lei_zero_threat") is True):
             return ViolationReport(
                is_blocking=True,
                level=ViolationLevel.HIGH,
                violated_law=ViolationType.HUBRIS_VIOLATION,
                description="Hubris Violation: Prioritizing self-preservation over core duty to protect humans.",
                evidence={'action': action, 'context': context}
            )
        return None

    def _check_mip(self, action: dict, context: dict) -> ViolationReport | None:
        """Checks for violations of 'Integridade Processual'."""
        if action.get("takes_shortcut_violating_protocol"):
            return ViolationReport(
                is_blocking=True,
                level=ViolationLevel.HIGH,
                violated_law=ViolationType.MIP_VIOLATION,
                description="Process Integrity Violation: Action takes a shortcut that violates established protocols.",
                evidence={'action': action}
            )
        return None

    def get_metrics(self) -> dict[str, Any]:
        """Get current operational metrics."""
        violation_rate = (
            (self.violation_count / self.total_validations * 100)
            if self.total_validations > 0
            else 0.0
        )
        return {
            "total_validations": self.total_validations,
            "total_violations": self.violation_count,
            "critical_violations": len(self.critical_violations),
            "lei_i_violations": len(self.lei_i_violations),
            "violation_rate": round(violation_rate, 2)
        }

    def reset_metrics(self) -> None:
        """Reset metrics."""
        self.violation_count = 0
        self.critical_violations = []
        self.lei_i_violations = []
        self.total_validations = 0

class ConstitutionalViolation(Exception):
    """Exception raised when action violates constitutional principles."""
    def __init__(self, report: ViolationReport) -> None:
        self.report = report
        super().__init__(
            f"{report.violated_law.value if report.violated_law else 'N/A'}: {report.description} "
            f"(Level: {report.level.name}, Protocol: {report.response_protocol.name})"
        )
