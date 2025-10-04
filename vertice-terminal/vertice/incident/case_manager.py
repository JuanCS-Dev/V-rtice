"""
🔎 Case Manager - Gerenciamento de investigações

Cases são investigações mais profundas de incidentes.
Diferença:
- Incident: Evento de segurança que requer resposta
- Case: Investigação detalhada (pode ter múltiplos incidentes)

Features:
- Case lifecycle management
- Evidence tracking
- Finding documentation
- Investigator assignment
- Timeline integration
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CaseStatus(Enum):
    """Status do case"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CasePriority(Enum):
    """Prioridade do case"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingSeverity(Enum):
    """Severidade de finding"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


@dataclass
class Finding:
    """
    Finding de investigação
    """
    id: str
    title: str
    description: str
    severity: FindingSeverity
    category: str  # vulnerability, misconfiguration, evidence_of_compromise, etc

    # Evidence
    evidence_ids: List[str] = field(default_factory=list)
    iocs: List[str] = field(default_factory=list)

    # MITRE ATT&CK mapping
    mitre_tactics: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    # Remediation
    recommendation: str = ""
    remediation_steps: List[str] = field(default_factory=list)

    # Metadata
    discovered_by: str = ""
    discovered_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class CaseNote:
    """
    Nota de investigação
    """
    id: str
    author: str
    timestamp: datetime
    content: str
    is_private: bool = False  # Se True, apenas investigators veem
    attachments: List[str] = field(default_factory=list)


@dataclass
class Case:
    """
    Case de investigação
    """
    id: str
    title: str
    description: str
    priority: CasePriority
    status: CaseStatus

    # Assignment
    lead_investigator: Optional[str] = None
    investigators: List[str] = field(default_factory=list)

    # Timing
    opened_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

    # Related items
    related_incidents: List[str] = field(default_factory=list)
    related_cases: List[str] = field(default_factory=list)

    # Investigation
    findings: List[Finding] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    timeline_id: Optional[str] = None

    # Notes
    notes: List[CaseNote] = field(default_factory=list)

    # Hypothesis
    hypothesis: str = ""
    conclusion: str = ""

    # Attribution
    attributed_threat_actors: List[str] = field(default_factory=list)
    attributed_campaigns: List[str] = field(default_factory=list)

    # Tags and metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CaseManager:
    """
    Case Management System

    Features:
    - Case lifecycle management
    - Finding tracking
    - Evidence linking
    - Collaboration tools
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do case_service
            use_backend: Se True, persiste no backend
        """
        self.backend_url = backend_url or "http://localhost:8011"
        self.use_backend = use_backend

        # Cases cache
        self.cases: Dict[str, Case] = {}

    def create_case(self, case: Case) -> str:
        """
        Cria novo case

        Args:
            case: Case object

        Returns:
            Case ID
        """
        if not case.id:
            import uuid
            case.id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        # Store
        self.cases[case.id] = case

        # Persist
        if self.use_backend:
            try:
                self._create_case_backend(case)
            except Exception as e:
                logger.error(f"Backend case creation failed: {e}")

        logger.info(f"Case created: {case.id} - {case.title}")

        return case.id

    def add_finding(
        self,
        case_id: str,
        finding: Finding,
    ) -> bool:
        """
        Adiciona finding ao case

        Args:
            case_id: Case ID
            finding: Finding object

        Returns:
            True se sucesso
        """
        case = self.get_case(case_id)

        if not case:
            return False

        if not finding.id:
            import uuid
            finding.id = f"FIND-{uuid.uuid4().hex[:8]}"

        case.findings.append(finding)

        logger.info(f"Finding added to case {case_id}: {finding.title}")

        # Update backend
        if self.use_backend:
            try:
                self._update_case_backend(case)
            except Exception as e:
                logger.error(f"Backend update failed: {e}")

        return True

    def add_note(
        self,
        case_id: str,
        content: str,
        author: str,
        is_private: bool = False,
    ) -> bool:
        """
        Adiciona nota ao case

        Args:
            case_id: Case ID
            content: Note content
            author: Author
            is_private: Private note

        Returns:
            True se sucesso
        """
        case = self.get_case(case_id)

        if not case:
            return False

        import uuid

        note = CaseNote(
            id=str(uuid.uuid4())[:8],
            author=author,
            timestamp=datetime.now(),
            content=content,
            is_private=is_private,
        )

        case.notes.append(note)

        # Update backend
        if self.use_backend:
            try:
                self._update_case_backend(case)
            except Exception as e:
                logger.error(f"Backend update failed: {e}")

        return True

    def link_evidence(
        self,
        case_id: str,
        evidence_id: str,
    ) -> bool:
        """
        Linka evidência ao case

        Args:
            case_id: Case ID
            evidence_id: Evidence ID

        Returns:
            True se sucesso
        """
        case = self.get_case(case_id)

        if not case:
            return False

        if evidence_id not in case.evidence_ids:
            case.evidence_ids.append(evidence_id)

            logger.info(f"Evidence {evidence_id} linked to case {case_id}")

        return True

    def update_status(
        self,
        case_id: str,
        new_status: CaseStatus,
        author: str = "system",
    ) -> bool:
        """
        Atualiza status do case

        Args:
            case_id: Case ID
            new_status: New status
            author: Who changed

        Returns:
            True se sucesso
        """
        case = self.get_case(case_id)

        if not case:
            return False

        old_status = case.status
        case.status = new_status

        # Set closed_at
        if new_status in [CaseStatus.CLOSED, CaseStatus.ARCHIVED]:
            if not case.closed_at:
                case.closed_at = datetime.now()

        # Add status change note
        self.add_note(
            case_id,
            f"Status changed: {old_status.value} → {new_status.value}",
            author,
            is_private=False,
        )

        logger.info(f"Case {case_id}: {old_status.value} → {new_status.value}")

        return True

    def get_case(self, case_id: str) -> Optional[Case]:
        """
        Retorna case por ID

        Args:
            case_id: Case ID

        Returns:
            Case ou None
        """
        # Check cache
        if case_id in self.cases:
            return self.cases[case_id]

        # Try backend
        if self.use_backend:
            try:
                return self._get_case_backend(case_id)
            except Exception as e:
                logger.error(f"Backend retrieval failed: {e}")

        return None

    def list_cases(
        self,
        status: Optional[CaseStatus] = None,
        priority: Optional[CasePriority] = None,
        investigator: Optional[str] = None,
        limit: int = 100,
    ) -> List[Case]:
        """
        Lista cases com filtros

        Args:
            status: Filter by status
            priority: Filter by priority
            investigator: Filter by investigator
            limit: Max cases

        Returns:
            List of Case
        """
        cases = list(self.cases.values())

        if status:
            cases = [c for c in cases if c.status == status]

        if priority:
            cases = [c for c in cases if c.priority == priority]

        if investigator:
            cases = [
                c for c in cases
                if c.lead_investigator == investigator or investigator in c.investigators
            ]

        # Sort by priority and opened date
        priority_order = {
            CasePriority.CRITICAL: 0,
            CasePriority.HIGH: 1,
            CasePriority.MEDIUM: 2,
            CasePriority.LOW: 3,
        }

        cases = sorted(
            cases,
            key=lambda c: (priority_order[c.priority], c.opened_at),
            reverse=False,
        )

        return cases[:limit]

    def search_cases(
        self,
        query: str,
        search_in: List[str] = ["title", "description", "notes"],
    ) -> List[Case]:
        """
        Busca cases por texto

        Args:
            query: Search query
            search_in: Fields to search in

        Returns:
            List of matching Case
        """
        query_lower = query.lower()
        matching_cases = []

        for case in self.cases.values():
            # Search in title
            if "title" in search_in and query_lower in case.title.lower():
                matching_cases.append(case)
                continue

            # Search in description
            if "description" in search_in and query_lower in case.description.lower():
                matching_cases.append(case)
                continue

            # Search in notes
            if "notes" in search_in:
                for note in case.notes:
                    if query_lower in note.content.lower():
                        matching_cases.append(case)
                        break

        return matching_cases

    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """
        Retorna summary do case

        Args:
            case_id: Case ID

        Returns:
            Summary dict
        """
        case = self.get_case(case_id)

        if not case:
            return {}

        # Calculate duration
        duration_days = 0
        if case.closed_at:
            duration_days = (case.closed_at - case.opened_at).days
        else:
            duration_days = (datetime.now() - case.opened_at).days

        # Group findings by severity
        findings_by_severity = {}
        for sev in FindingSeverity:
            findings_by_severity[sev.value] = len(
                [f for f in case.findings if f.severity == sev]
            )

        return {
            "case_id": case.id,
            "title": case.title,
            "status": case.status.value,
            "priority": case.priority.value,
            "duration_days": duration_days,
            "total_findings": len(case.findings),
            "findings_by_severity": findings_by_severity,
            "evidence_count": len(case.evidence_ids),
            "related_incidents": len(case.related_incidents),
            "investigator_count": len(case.investigators) + (1 if case.lead_investigator else 0),
            "notes_count": len(case.notes),
        }

    # Backend integration methods

    def _create_case_backend(self, case: Case) -> bool:
        """Cria case no backend"""
        import httpx

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/cases",
                    json={
                        "id": case.id,
                        "title": case.title,
                        "description": case.description,
                        "priority": case.priority.value,
                        "status": case.status.value,
                        "lead_investigator": case.lead_investigator,
                        "opened_at": case.opened_at.isoformat(),
                    }
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Backend case creation failed: {e}")
            raise

    def _update_case_backend(self, case: Case) -> bool:
        """Atualiza case no backend"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.put(
                    f"{self.backend_url}/api/cases/{case.id}",
                    json={
                        "status": case.status.value,
                        "findings_count": len(case.findings),
                        "evidence_count": len(case.evidence_ids),
                        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
                    }
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Backend update failed: {e}")
            return False

    def _get_case_backend(self, case_id: str) -> Optional[Case]:
        """Busca case no backend"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.backend_url}/api/cases/{case_id}")

                if response.status_code == 404:
                    return None

                response.raise_for_status()

                # TODO: Parse response to Case
                return None  # Placeholder

        except Exception as e:
            logger.error(f"Backend retrieval failed: {e}")
            return None
