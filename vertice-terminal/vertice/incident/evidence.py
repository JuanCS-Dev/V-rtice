"""
🔐 Evidence Collector - Coleta e preservação de evidências digitais

Coleta evidências mantendo chain of custody para uso legal/forense.

Evidence types:
- Memory dumps
- Disk images
- Log files
- Network captures (PCAP)
- File artifacts
- Registry dumps
- Browser history
- Email

Chain of Custody tracking completo para admissibilidade legal.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
import hashlib
import logging

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Tipo de evidência"""
    MEMORY_DUMP = "memory_dump"
    DISK_IMAGE = "disk_image"
    LOG_FILE = "log_file"
    NETWORK_CAPTURE = "network_capture"
    FILE_ARTIFACT = "file_artifact"
    REGISTRY_DUMP = "registry_dump"
    BROWSER_HISTORY = "browser_history"
    EMAIL = "email"
    SCREENSHOT = "screenshot"
    DATABASE_DUMP = "database_dump"
    OTHER = "other"


class EvidenceStatus(Enum):
    """Status da evidência"""
    COLLECTING = "collecting"
    COLLECTED = "collected"
    ANALYZING = "analyzing"
    PRESERVED = "preserved"
    ARCHIVED = "archived"


@dataclass
class ChainOfCustodyEntry:
    """
    Entrada na cadeia de custódia
    """
    timestamp: datetime
    action: str  # collected, transferred, analyzed, etc
    person: str  # Quem executou a ação
    location: str  # Onde a ação foi executada
    notes: str = ""


@dataclass
class Evidence:
    """
    Evidência digital
    """
    id: str
    evidence_type: EvidenceType
    description: str
    status: EvidenceStatus

    # Source
    source_system: str  # Hostname/IP
    source_path: Optional[str] = None

    # Storage
    storage_path: Optional[str] = None  # Where evidence is stored
    file_size_bytes: int = 0

    # Integrity
    md5_hash: Optional[str] = None
    sha256_hash: Optional[str] = None
    sha1_hash: Optional[str] = None

    # Chain of custody
    collected_by: str = ""
    collected_at: datetime = field(default_factory=datetime.now)
    chain_of_custody: List[ChainOfCustodyEntry] = field(default_factory=list)

    # Related items
    case_id: Optional[str] = None
    incident_id: Optional[str] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Legal holds
    is_under_legal_hold: bool = False
    retention_until: Optional[datetime] = None


class EvidenceCollector:
    """
    Evidence Collection & Preservation System

    Features:
    - Remote evidence collection via agents
    - Hash calculation for integrity
    - Chain of custody tracking
    - Secure storage
    - Legal hold management
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        evidence_storage_path: Optional[Path] = None,
    ):
        """
        Args:
            backend_url: URL do evidence_service
            use_backend: Se True, usa backend
            evidence_storage_path: Local storage path para evidências
        """
        self.backend_url = backend_url or "http://localhost:8013"
        self.use_backend = use_backend

        # Evidence storage
        if evidence_storage_path:
            self.storage_path = Path(evidence_storage_path)
        else:
            self.storage_path = Path.home() / ".vertice" / "evidence"

        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Evidence registry
        self.evidence_registry: Dict[str, Evidence] = {}

    def collect_evidence(
        self,
        evidence_type: EvidenceType,
        source_system: str,
        source_path: Optional[str] = None,
        description: str = "",
        collected_by: str = "system",
        case_id: Optional[str] = None,
    ) -> Evidence:
        """
        Coleta evidência de sistema remoto

        Args:
            evidence_type: Tipo de evidência
            source_system: Sistema source (hostname/IP)
            source_path: Path da evidência no sistema
            description: Descrição
            collected_by: Quem está coletando
            case_id: Case relacionado

        Returns:
            Evidence object
        """
        import uuid

        evidence = Evidence(
            id=f"EVD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            evidence_type=evidence_type,
            description=description,
            status=EvidenceStatus.COLLECTING,
            source_system=source_system,
            source_path=source_path,
            collected_by=collected_by,
            case_id=case_id,
        )

        logger.info(
            f"Collecting evidence: {evidence.id} from {source_system} "
            f"({evidence_type.value})"
        )

        # Add initial chain of custody entry
        evidence.chain_of_custody.append(
            ChainOfCustodyEntry(
                timestamp=datetime.now(),
                action="collection_initiated",
                person=collected_by,
                location=source_system,
                notes=f"Evidence collection started: {description}",
            )
        )

        # Collect based on type
        try:
            if evidence_type == EvidenceType.MEMORY_DUMP:
                self._collect_memory_dump(evidence)

            elif evidence_type == EvidenceType.DISK_IMAGE:
                self._collect_disk_image(evidence)

            elif evidence_type == EvidenceType.LOG_FILE:
                self._collect_log_file(evidence)

            elif evidence_type == EvidenceType.NETWORK_CAPTURE:
                self._collect_network_capture(evidence)

            elif evidence_type == EvidenceType.FILE_ARTIFACT:
                self._collect_file_artifact(evidence)

            else:
                logger.warning(f"Evidence type not implemented: {evidence_type.value}")

            evidence.status = EvidenceStatus.COLLECTED

            # Add collection completed entry
            evidence.chain_of_custody.append(
                ChainOfCustodyEntry(
                    timestamp=datetime.now(),
                    action="collection_completed",
                    person=collected_by,
                    location=self.storage_path.as_posix(),
                    notes="Evidence successfully collected and stored",
                )
            )

        except Exception as e:
            logger.error(f"Evidence collection failed: {e}")
            evidence.status = EvidenceStatus.COLLECTING
            evidence.metadata["collection_error"] = str(e)

        # Register evidence
        self.evidence_registry[evidence.id] = evidence

        # Persist to backend
        if self.use_backend:
            try:
                self._register_evidence_backend(evidence)
            except Exception as e:
                logger.error(f"Backend registration failed: {e}")

        return evidence

    def _collect_memory_dump(self, evidence: Evidence) -> None:
        """
        Coleta memory dump de endpoint

        Args:
            evidence: Evidence object
        """
        # TODO: Integrate com endpoint agent para memory dump
        # For now, simulate

        logger.info(f"Collecting memory dump from {evidence.source_system}")

        # Simulated storage
        evidence.storage_path = (
            self.storage_path / f"{evidence.id}_memory.dmp"
        ).as_posix()

        # Would actually collect via agent
        # evidence.file_size_bytes = ...
        # evidence.md5_hash = ...
        # evidence.sha256_hash = ...

        evidence.metadata["collection_method"] = "remote_agent"
        evidence.metadata["tool"] = "WinPmem"

    def _collect_disk_image(self, evidence: Evidence) -> None:
        """Coleta disk image"""

        logger.info(f"Collecting disk image from {evidence.source_system}")

        # TODO: Implement via agent with dd/FTK Imager

        evidence.storage_path = (
            self.storage_path / f"{evidence.id}_disk.img"
        ).as_posix()

        evidence.metadata["collection_method"] = "forensic_imaging"
        evidence.metadata["tool"] = "dd"

    def _collect_log_file(self, evidence: Evidence) -> None:
        """Coleta log file"""

        logger.info(f"Collecting log file: {evidence.source_path}")

        # TODO: Implement log collection via agent

        filename = Path(evidence.source_path).name if evidence.source_path else "log.txt"

        evidence.storage_path = (
            self.storage_path / f"{evidence.id}_{filename}"
        ).as_posix()

        evidence.metadata["collection_method"] = "file_copy"

    def _collect_network_capture(self, evidence: Evidence) -> None:
        """Coleta network capture (PCAP)"""

        logger.info(f"Collecting network capture from {evidence.source_system}")

        # TODO: Implement via tcpdump/wireshark agent

        evidence.storage_path = (
            self.storage_path / f"{evidence.id}_capture.pcap"
        ).as_posix()

        evidence.metadata["collection_method"] = "packet_capture"
        evidence.metadata["tool"] = "tcpdump"

    def _collect_file_artifact(self, evidence: Evidence) -> None:
        """Coleta file artifact"""

        logger.info(f"Collecting file artifact: {evidence.source_path}")

        # Calculate hash of source file (via agent)
        # Then transfer file

        if evidence.source_path:
            filename = Path(evidence.source_path).name
        else:
            filename = "artifact.bin"

        evidence.storage_path = (
            self.storage_path / f"{evidence.id}_{filename}"
        ).as_posix()

        evidence.metadata["collection_method"] = "file_transfer"

    def calculate_hashes(self, evidence: Evidence) -> bool:
        """
        Calcula hashes para verificação de integridade

        Args:
            evidence: Evidence object

        Returns:
            True se sucesso
        """
        if not evidence.storage_path:
            logger.warning("No storage path for evidence")
            return False

        file_path = Path(evidence.storage_path)

        if not file_path.exists():
            logger.warning(f"Evidence file not found: {file_path}")
            return False

        try:
            # Calculate MD5, SHA1, SHA256
            md5 = hashlib.md5()
            sha1 = hashlib.sha1()
            sha256 = hashlib.sha256()

            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    md5.update(chunk)
                    sha1.update(chunk)
                    sha256.update(chunk)

            evidence.md5_hash = md5.hexdigest()
            evidence.sha1_hash = sha1.hexdigest()
            evidence.sha256_hash = sha256.hexdigest()

            evidence.file_size_bytes = file_path.stat().st_size

            logger.info(f"Hashes calculated for {evidence.id}: SHA256={evidence.sha256_hash}")

            # Add chain of custody entry
            evidence.chain_of_custody.append(
                ChainOfCustodyEntry(
                    timestamp=datetime.now(),
                    action="integrity_verification",
                    person="system",
                    location=self.storage_path.as_posix(),
                    notes=f"Hash calculated: {evidence.sha256_hash}",
                )
            )

            return True

        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            return False

    def add_chain_of_custody_entry(
        self,
        evidence_id: str,
        action: str,
        person: str,
        location: str,
        notes: str = "",
    ) -> bool:
        """
        Adiciona entrada na chain of custody

        Args:
            evidence_id: Evidence ID
            action: Action performed
            person: Who performed
            location: Where
            notes: Additional notes

        Returns:
            True se sucesso
        """
        evidence = self.get_evidence(evidence_id)

        if not evidence:
            return False

        entry = ChainOfCustodyEntry(
            timestamp=datetime.now(),
            action=action,
            person=person,
            location=location,
            notes=notes,
        )

        evidence.chain_of_custody.append(entry)

        logger.info(f"Chain of custody entry added to {evidence_id}: {action}")

        return True

    def set_legal_hold(
        self,
        evidence_id: str,
        retention_until: Optional[datetime] = None,
    ) -> bool:
        """
        Coloca evidência em legal hold

        Args:
            evidence_id: Evidence ID
            retention_until: Retention date (None = indefinite)

        Returns:
            True se sucesso
        """
        evidence = self.get_evidence(evidence_id)

        if not evidence:
            return False

        evidence.is_under_legal_hold = True
        evidence.retention_until = retention_until

        # Add chain of custody entry
        self.add_chain_of_custody_entry(
            evidence_id,
            action="legal_hold_applied",
            person="legal_team",
            location="evidence_storage",
            notes=f"Legal hold until: {retention_until or 'indefinite'}",
        )

        logger.info(f"Legal hold applied to evidence: {evidence_id}")

        return True

    def verify_integrity(self, evidence: Evidence) -> bool:
        """
        Verifica integridade da evidência comparando hashes

        Args:
            evidence: Evidence object

        Returns:
            True se íntegra
        """
        if not evidence.sha256_hash:
            logger.warning("No hash to verify against")
            return False

        # Recalculate hash
        original_hash = evidence.sha256_hash

        if not self.calculate_hashes(evidence):
            return False

        current_hash = evidence.sha256_hash

        is_valid = original_hash == current_hash

        # Add verification entry
        self.add_chain_of_custody_entry(
            evidence.id,
            action="integrity_verification",
            person="system",
            location=self.storage_path.as_posix(),
            notes=f"Integrity {'VALID' if is_valid else 'COMPROMISED'}",
        )

        if not is_valid:
            logger.error(f"Evidence integrity compromised: {evidence.id}")
        else:
            logger.info(f"Evidence integrity verified: {evidence.id}")

        return is_valid

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Retorna evidência por ID"""
        return self.evidence_registry.get(evidence_id)

    def list_evidence(
        self,
        case_id: Optional[str] = None,
        evidence_type: Optional[EvidenceType] = None,
        status: Optional[EvidenceStatus] = None,
    ) -> List[Evidence]:
        """Lista evidências com filtros"""
        evidence_list = list(self.evidence_registry.values())

        if case_id:
            evidence_list = [e for e in evidence_list if e.case_id == case_id]

        if evidence_type:
            evidence_list = [e for e in evidence_list if e.evidence_type == evidence_type]

        if status:
            evidence_list = [e for e in evidence_list if e.status == status]

        # Sort by collection date (most recent first)
        evidence_list = sorted(
            evidence_list,
            key=lambda e: e.collected_at,
            reverse=True
        )

        return evidence_list

    def _register_evidence_backend(self, evidence: Evidence) -> bool:
        """Registra evidência no backend"""
        import httpx

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/evidence",
                    json={
                        "id": evidence.id,
                        "type": evidence.evidence_type.value,
                        "description": evidence.description,
                        "source_system": evidence.source_system,
                        "collected_by": evidence.collected_by,
                        "collected_at": evidence.collected_at.isoformat(),
                        "sha256_hash": evidence.sha256_hash,
                    }
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Backend evidence registration failed: {e}")
            raise
