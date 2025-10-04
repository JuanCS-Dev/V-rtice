"""
💬 Conversation Engine - Investigações multi-turn

Mantém contexto de conversas e permite investigações iterativas.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class InvestigationStatus(Enum):
    """Status de uma investigação"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class Turn:
    """Um turno de conversa"""
    timestamp: datetime
    user_input: str
    veql_query: Optional[str]
    results_count: int
    threat_level: str
    suggestions: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Investigation:
    """Uma investigação multi-turn"""
    id: str
    name: str
    status: InvestigationStatus
    created_at: datetime
    turns: List[Turn] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    iocs: List[str] = field(default_factory=list)

    def add_turn(self, turn: Turn) -> None:
        """Adiciona turno à investigação"""
        self.turns.append(turn)

    def add_finding(self, finding: str) -> None:
        """Adiciona descoberta"""
        self.findings.append(finding)

    def add_ioc(self, ioc: str) -> None:
        """Adiciona IOC descoberto"""
        if ioc not in self.iocs:
            self.iocs.append(ioc)

    def get_context(self, last_n: int = 3) -> List[str]:
        """
        Retorna contexto das últimas N interações

        Args:
            last_n: Número de turnos para incluir

        Returns:
            Lista de strings de contexto
        """
        context = []
        for turn in self.turns[-last_n:]:
            context.append(f"Q: {turn.user_input}")
            if turn.veql_query:
                context.append(f"VeQL: {turn.veql_query}")
            context.append(f"Results: {turn.results_count} rows, Threat: {turn.threat_level}")

        return context

    def summary(self) -> str:
        """Retorna resumo da investigação"""
        total_turns = len(self.turns)
        total_findings = len(self.findings)
        total_iocs = len(self.iocs)

        # Threat level mais alto
        max_threat = "LOW"
        for turn in self.turns:
            if turn.threat_level == "CRITICAL":
                max_threat = "CRITICAL"
            elif turn.threat_level == "HIGH" and max_threat not in ["CRITICAL"]:
                max_threat = "HIGH"
            elif turn.threat_level == "MEDIUM" and max_threat not in ["CRITICAL", "HIGH"]:
                max_threat = "MEDIUM"

        summary = f"""Investigation Summary:
  ID: {self.id}
  Name: {self.name}
  Status: {self.status.value}
  Turns: {total_turns}
  Max Threat Level: {max_threat}
  Findings: {total_findings}
  IOCs Discovered: {total_iocs}
  Duration: {datetime.now() - self.created_at}
"""
        return summary


class ConversationEngine:
    """
    Engine de conversação para investigações multi-turn
    """

    def __init__(self):
        self.current_investigation: Optional[Investigation] = None
        self.investigations: Dict[str, Investigation] = {}

    def start_investigation(self, name: str) -> Investigation:
        """
        Inicia nova investigação

        Args:
            name: Nome da investigação

        Returns:
            Investigation criada
        """
        inv_id = f"INV-{len(self.investigations) + 1:04d}"

        investigation = Investigation(
            id=inv_id,
            name=name,
            status=InvestigationStatus.ACTIVE,
            created_at=datetime.now(),
        )

        self.investigations[inv_id] = investigation
        self.current_investigation = investigation

        return investigation

    def add_turn(
        self,
        user_input: str,
        veql_query: Optional[str] = None,
        results_count: int = 0,
        threat_level: str = "LOW",
        suggestions: Optional[List[str]] = None,
    ) -> Turn:
        """
        Adiciona turno à investigação atual

        Args:
            user_input: Input do usuário
            veql_query: Query VeQL gerada (se houver)
            results_count: Número de resultados
            threat_level: Nível de ameaça detectado
            suggestions: Sugestões de próximos passos

        Returns:
            Turn criado
        """
        if not self.current_investigation:
            raise ValueError("No active investigation. Start one first.")

        turn = Turn(
            timestamp=datetime.now(),
            user_input=user_input,
            veql_query=veql_query,
            results_count=results_count,
            threat_level=threat_level,
            suggestions=suggestions or [],
        )

        self.current_investigation.add_turn(turn)

        return turn

    def complete_investigation(self, summary: Optional[str] = None) -> Investigation:
        """
        Completa investigação atual

        Args:
            summary: Resumo final (opcional)

        Returns:
            Investigation completada
        """
        if not self.current_investigation:
            raise ValueError("No active investigation")

        self.current_investigation.status = InvestigationStatus.COMPLETED

        if summary:
            self.current_investigation.add_finding(f"Final Summary: {summary}")

        completed = self.current_investigation
        self.current_investigation = None

        return completed

    def get_context(self) -> List[str]:
        """
        Retorna contexto da investigação atual

        Returns:
            Lista de strings de contexto
        """
        if not self.current_investigation:
            return []

        return self.current_investigation.get_context()

    def list_investigations(
        self,
        status: Optional[InvestigationStatus] = None
    ) -> List[Investigation]:
        """
        Lista investigações

        Args:
            status: Filtrar por status

        Returns:
            Lista de investigações
        """
        investigations = list(self.investigations.values())

        if status:
            investigations = [inv for inv in investigations if inv.status == status]

        return sorted(investigations, key=lambda inv: inv.created_at, reverse=True)
