"""
📋 Compliance Engine - Framework de compliance multi-regulatório

Suporta frameworks:
- PCI-DSS (Payment Card Industry Data Security Standard)
- HIPAA (Health Insurance Portability and Accountability Act)
- ISO 27001 (Information Security Management)
- NIST CSF (Cybersecurity Framework)
- LGPD (Lei Geral de Proteção de Dados - Brasil)
- GDPR (General Data Protection Regulation - EU)
- SOC 2 (Service Organization Control)

Features:
- Control mapping
- Automated assessments
- Gap analysis
- Evidence collection
- Continuous compliance monitoring
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Frameworks de compliance suportados"""
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    NIST_CSF = "nist_csf"
    LGPD = "lgpd"
    GDPR = "gdpr"
    SOC2 = "soc2"


class ControlStatus(Enum):
    """Status de controle"""
    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    IMPLEMENTED = "implemented"
    NOT_APPLICABLE = "not_applicable"
    NEEDS_REVIEW = "needs_review"


@dataclass
class Control:
    """
    Controle de compliance
    """
    id: str
    framework: ComplianceFramework
    title: str
    description: str
    requirement: str

    # Implementation
    status: ControlStatus = ControlStatus.NOT_IMPLEMENTED
    implementation_notes: str = ""

    # Evidence
    evidence_ids: List[str] = field(default_factory=list)
    automated_check: Optional[str] = None  # Nome do check automatizado

    # Responsibility
    owner: Optional[str] = None
    responsible_team: Optional[str] = None

    # Timing
    last_assessed: Optional[datetime] = None
    next_review_due: Optional[datetime] = None

    # Related controls (outros frameworks)
    mapped_controls: Dict[str, str] = field(default_factory=dict)  # framework -> control_id

    # Metadata
    tags: List[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high, critical


@dataclass
class Assessment:
    """
    Assessment de compliance
    """
    id: str
    framework: ComplianceFramework
    assessment_date: datetime
    assessor: str

    # Scope
    controls_assessed: List[str] = field(default_factory=list)

    # Results
    total_controls: int = 0
    implemented: int = 0
    partially_implemented: int = 0
    not_implemented: int = 0
    not_applicable: int = 0

    # Compliance score
    compliance_score: float = 0.0  # 0-100%

    # Findings
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Report
    report_path: Optional[str] = None

    # Metadata
    notes: str = ""


class ComplianceEngine:
    """
    Compliance Framework Engine

    Features:
    - Multi-framework support
    - Control library
    - Automated assessments
    - Gap analysis
    - Evidence linking
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do compliance_service
            use_backend: Se True, usa backend
        """
        self.backend_url = backend_url or "http://localhost:8014"
        self.use_backend = use_backend

        # Control library
        self.controls: Dict[str, Control] = {}

        # Assessments history
        self.assessments: List[Assessment] = []

        # Load default control libraries
        self._load_default_controls()

    def _load_default_controls(self):
        """Carrega bibliotecas de controles padrão"""

        # PCI-DSS controls (exemplo de alguns)
        pci_controls = [
            Control(
                id="PCI-DSS-1.1",
                framework=ComplianceFramework.PCI_DSS,
                title="Firewall configuration standards",
                description="Establish and implement firewall and router configuration standards",
                requirement="Requirement 1: Install and maintain a firewall configuration to protect cardholder data",
                priority="critical",
                tags=["network", "firewall"],
            ),
            Control(
                id="PCI-DSS-2.1",
                framework=ComplianceFramework.PCI_DSS,
                title="Change vendor-supplied defaults",
                description="Always change vendor-supplied defaults and remove or disable unnecessary default accounts",
                requirement="Requirement 2: Do not use vendor-supplied defaults for system passwords and other security parameters",
                priority="critical",
                tags=["authentication", "hardening"],
            ),
            Control(
                id="PCI-DSS-3.4",
                framework=ComplianceFramework.PCI_DSS,
                title="Render PAN unreadable",
                description="Render PAN unreadable anywhere it is stored",
                requirement="Requirement 3: Protect stored cardholder data",
                priority="critical",
                tags=["encryption", "data_protection"],
            ),
            Control(
                id="PCI-DSS-8.1",
                framework=ComplianceFramework.PCI_DSS,
                title="Unique user IDs",
                description="Assign all users a unique ID before allowing them to access system components",
                requirement="Requirement 8: Identify and authenticate access to system components",
                priority="high",
                tags=["authentication", "identity"],
            ),
            Control(
                id="PCI-DSS-10.1",
                framework=ComplianceFramework.PCI_DSS,
                title="Audit trails",
                description="Implement audit trails to link all access to system components to each individual user",
                requirement="Requirement 10: Track and monitor all access to network resources and cardholder data",
                priority="high",
                tags=["logging", "audit"],
            ),
        ]

        # ISO 27001 controls (exemplo)
        iso_controls = [
            Control(
                id="ISO27001-A.5.1",
                framework=ComplianceFramework.ISO27001,
                title="Policies for information security",
                description="Management direction for information security",
                requirement="Annex A.5: Information security policies",
                priority="high",
                tags=["policy", "governance"],
            ),
            Control(
                id="ISO27001-A.9.1",
                framework=ComplianceFramework.ISO27001,
                title="Access control policy",
                description="Business requirements for access control",
                requirement="Annex A.9: Access control",
                priority="high",
                tags=["access_control", "policy"],
            ),
            Control(
                id="ISO27001-A.12.1",
                framework=ComplianceFramework.ISO27001,
                title="Operational procedures",
                description="Documented operating procedures",
                requirement="Annex A.12: Operations security",
                priority="medium",
                tags=["operations", "procedures"],
            ),
        ]

        # LGPD controls (exemplo)
        lgpd_controls = [
            Control(
                id="LGPD-ART.6",
                framework=ComplianceFramework.LGPD,
                title="Princípios de tratamento de dados",
                description="Observância dos princípios: finalidade, adequação, necessidade, livre acesso, qualidade, transparência, segurança, prevenção, não discriminação, responsabilização",
                requirement="Art. 6º - Princípios",
                priority="critical",
                tags=["princípios", "fundamentos"],
            ),
            Control(
                id="LGPD-ART.46",
                framework=ComplianceFramework.LGPD,
                title="Medidas de segurança",
                description="Adoção de medidas de segurança técnicas e administrativas aptas a proteger os dados pessoais",
                requirement="Art. 46 - Segurança e boas práticas",
                priority="critical",
                tags=["segurança", "proteção"],
            ),
            Control(
                id="LGPD-ART.48",
                framework=ComplianceFramework.LGPD,
                title="Comunicação de incidentes",
                description="Comunicar à ANPD e ao titular a ocorrência de incidente de segurança",
                requirement="Art. 48 - Comunicação de incidente",
                priority="high",
                tags=["incidente", "notificação"],
            ),
        ]

        # Register all controls
        for control in pci_controls + iso_controls + lgpd_controls:
            self.controls[control.id] = control

        logger.info(f"Loaded {len(self.controls)} default compliance controls")

    def add_control(self, control: Control) -> None:
        """
        Adiciona controle customizado

        Args:
            control: Control object
        """
        self.controls[control.id] = control
        logger.info(f"Control added: {control.id}")

    def update_control_status(
        self,
        control_id: str,
        status: ControlStatus,
        implementation_notes: str = "",
        evidence_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Atualiza status de controle

        Args:
            control_id: Control ID
            status: New status
            implementation_notes: Implementation notes
            evidence_ids: Evidence IDs

        Returns:
            True se atualizado
        """
        control = self.controls.get(control_id)

        if not control:
            logger.warning(f"Control not found: {control_id}")
            return False

        control.status = status
        control.implementation_notes = implementation_notes
        control.last_assessed = datetime.now()

        if evidence_ids:
            control.evidence_ids.extend(evidence_ids)

        # Set next review (90 days)
        control.next_review_due = datetime.now() + timedelta(days=90)

        logger.info(f"Control {control_id} updated: {status.value}")

        return True

    def assess_framework(
        self,
        framework: ComplianceFramework,
        assessor: str = "system",
    ) -> Assessment:
        """
        Executa assessment de framework

        Args:
            framework: Framework to assess
            assessor: Assessor name

        Returns:
            Assessment object
        """
        import uuid

        # Get all controls for framework
        framework_controls = [
            c for c in self.controls.values()
            if c.framework == framework
        ]

        if not framework_controls:
            raise ValueError(f"No controls found for framework: {framework.value}")

        # Count by status
        implemented = 0
        partially_implemented = 0
        not_implemented = 0
        not_applicable = 0

        gaps = []
        recommendations = []

        for control in framework_controls:
            if control.status == ControlStatus.IMPLEMENTED:
                implemented += 1
            elif control.status == ControlStatus.PARTIALLY_IMPLEMENTED:
                partially_implemented += 1
                gaps.append(f"{control.id}: {control.title} - Partially implemented")
                recommendations.append(f"Complete implementation of {control.id}")
            elif control.status == ControlStatus.NOT_IMPLEMENTED:
                not_implemented += 1
                gaps.append(f"{control.id}: {control.title} - Not implemented")
                recommendations.append(f"Implement {control.id}: {control.title}")
            elif control.status == ControlStatus.NOT_APPLICABLE:
                not_applicable += 1

        # Calculate compliance score
        # Score = (implemented + 0.5 * partially_implemented) / (total - not_applicable)
        total = len(framework_controls)
        applicable = total - not_applicable

        if applicable > 0:
            compliance_score = ((implemented + 0.5 * partially_implemented) / applicable) * 100
        else:
            compliance_score = 100.0

        assessment = Assessment(
            id=f"ASSESS-{uuid.uuid4().hex[:8]}",
            framework=framework,
            assessment_date=datetime.now(),
            assessor=assessor,
            controls_assessed=[c.id for c in framework_controls],
            total_controls=total,
            implemented=implemented,
            partially_implemented=partially_implemented,
            not_implemented=not_implemented,
            not_applicable=not_applicable,
            compliance_score=compliance_score,
            gaps=gaps,
            recommendations=recommendations,
        )

        self.assessments.append(assessment)

        logger.info(
            f"Assessment completed for {framework.value}: "
            f"{compliance_score:.1f}% compliant"
        )

        return assessment

    def get_controls_by_framework(
        self,
        framework: ComplianceFramework,
        status: Optional[ControlStatus] = None,
    ) -> List[Control]:
        """
        Retorna controles por framework

        Args:
            framework: Framework
            status: Filter by status

        Returns:
            List of Control
        """
        controls = [
            c for c in self.controls.values()
            if c.framework == framework
        ]

        if status:
            controls = [c for c in controls if c.status == status]

        return sorted(controls, key=lambda c: c.id)

    def get_gap_analysis(
        self,
        framework: ComplianceFramework,
    ) -> Dict[str, Any]:
        """
        Retorna gap analysis de framework

        Args:
            framework: Framework

        Returns:
            Gap analysis dict
        """
        controls = self.get_controls_by_framework(framework)

        gaps = []
        critical_gaps = []

        for control in controls:
            if control.status in [ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED]:
                gap = {
                    "control_id": control.id,
                    "title": control.title,
                    "status": control.status.value,
                    "priority": control.priority,
                }

                gaps.append(gap)

                if control.priority in ["critical", "high"]:
                    critical_gaps.append(gap)

        return {
            "framework": framework.value,
            "total_gaps": len(gaps),
            "critical_gaps": len(critical_gaps),
            "gaps": gaps,
            "critical_gaps_list": critical_gaps,
        }

    def get_controls_needing_review(self) -> List[Control]:
        """
        Retorna controles que precisam de revisão

        Returns:
            List of Control
        """
        now = datetime.now()

        needing_review = []

        for control in self.controls.values():
            # Never assessed
            if not control.last_assessed:
                needing_review.append(control)
                continue

            # Past due date
            if control.next_review_due and control.next_review_due < now:
                needing_review.append(control)
                continue

        return sorted(needing_review, key=lambda c: c.priority, reverse=True)

    def map_control(
        self,
        control_id: str,
        target_framework: ComplianceFramework,
        target_control_id: str,
    ) -> bool:
        """
        Mapeia controle para controle de outro framework

        Args:
            control_id: Source control ID
            target_framework: Target framework
            target_control_id: Target control ID

        Returns:
            True se mapeado
        """
        control = self.controls.get(control_id)

        if not control:
            return False

        control.mapped_controls[target_framework.value] = target_control_id

        logger.info(
            f"Mapped {control_id} -> {target_framework.value}:{target_control_id}"
        )

        return True

    def get_framework_summary(
        self,
        framework: ComplianceFramework,
    ) -> Dict[str, Any]:
        """
        Retorna summary de framework

        Args:
            framework: Framework

        Returns:
            Summary dict
        """
        controls = self.get_controls_by_framework(framework)

        # Count by status
        status_counts = {}
        for status in ControlStatus:
            status_counts[status.value] = len(
                [c for c in controls if c.status == status]
            )

        # Get latest assessment
        framework_assessments = [
            a for a in self.assessments
            if a.framework == framework
        ]

        latest_assessment = None
        if framework_assessments:
            latest_assessment = max(framework_assessments, key=lambda a: a.assessment_date)

        return {
            "framework": framework.value,
            "total_controls": len(controls),
            "status_breakdown": status_counts,
            "latest_assessment": {
                "date": latest_assessment.assessment_date.isoformat() if latest_assessment else None,
                "score": latest_assessment.compliance_score if latest_assessment else None,
                "gaps": len(latest_assessment.gaps) if latest_assessment else None,
            } if latest_assessment else None,
            "controls_needing_review": len([
                c for c in controls
                if not c.last_assessed or (c.next_review_due and c.next_review_due < datetime.now())
            ]),
        }
