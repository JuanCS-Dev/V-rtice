"""
Evidence Collector

Automated evidence collection system for compliance verification. Collects
evidence from multiple sources (logs, configs, tests, docs) and packages
them for audit and compliance checking.

Features:
- Multi-source evidence collection (logs, configs, tests, docs)
- Automated evidence discovery
- Evidence integrity verification (SHA-256 hashing)
- Evidence packaging for auditors
- Evidence expiration tracking
- Evidence validation and verification

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import hashlib
import json
import logging
import os
import shutil
import uuid

from .base import (
    ComplianceConfig,
    Control,
    Evidence,
    EvidenceType,
    RegulationType,
)

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    """
    Single evidence item with metadata and integrity information.
    """

    evidence: Evidence
    file_size: int = 0
    collected_from: str = ""  # Source path/system
    integrity_verified: bool = False
    verification_timestamp: Optional[datetime] = None

    def verify_integrity(self, file_path: str) -> bool:
        """
        Verify evidence file integrity using SHA-256 hash.

        Args:
            file_path: Path to evidence file

        Returns:
            True if integrity verified
        """
        if not os.path.exists(file_path):
            logger.error(f"Evidence file not found: {file_path}")
            return False

        # Calculate current hash
        current_hash = self._calculate_file_hash(file_path)

        # Compare with stored hash
        if self.evidence.file_hash == current_hash:
            self.integrity_verified = True
            self.verification_timestamp = datetime.utcnow()
            return True
        else:
            logger.warning(
                f"Evidence integrity check failed for {self.evidence.evidence_id}: "
                f"expected {self.evidence.file_hash}, got {current_hash}"
            )
            return False

    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


@dataclass
class EvidencePackage:
    """
    Package of evidence for audit/compliance check.
    """

    package_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    regulation_type: RegulationType = RegulationType.ISO_27001
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "evidence_collector"
    control_ids: List[str] = field(default_factory=list)
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    package_path: Optional[str] = None
    total_size_bytes: int = 0
    manifest: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate package metadata."""
        self.total_size_bytes = sum(item.file_size for item in self.evidence_items)

        # Build manifest
        self.manifest = {
            "package_id": self.package_id,
            "regulation": self.regulation_type.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "total_evidence_items": len(self.evidence_items),
            "total_size_bytes": self.total_size_bytes,
            "controls": self.control_ids,
            "evidence": [
                {
                    "evidence_id": item.evidence.evidence_id,
                    "type": item.evidence.evidence_type.value,
                    "control_id": item.evidence.control_id,
                    "title": item.evidence.title,
                    "collected_at": item.evidence.collected_at.isoformat(),
                    "file_path": item.evidence.file_path,
                    "file_hash": item.evidence.file_hash,
                    "file_size": item.file_size,
                }
                for item in self.evidence_items
            ],
        }

    def get_evidence_for_control(self, control_id: str) -> List[EvidenceItem]:
        """Get all evidence for specific control."""
        return [
            item
            for item in self.evidence_items
            if item.evidence.control_id == control_id
        ]


class EvidenceCollector:
    """
    Automated evidence collection system.

    Collects evidence from multiple sources and organizes by control.
    """

    def __init__(self, config: Optional[ComplianceConfig] = None):
        """
        Initialize evidence collector.

        Args:
            config: Compliance configuration
        """
        self.config = config or ComplianceConfig()
        self._evidence_cache: Dict[str, List[EvidenceItem]] = {}  # control_id -> evidence

        # Ensure storage paths exist
        os.makedirs(self.config.evidence_storage_path, exist_ok=True)

        logger.info(f"Evidence collector initialized, storage: {self.config.evidence_storage_path}")

    def collect_log_evidence(
        self,
        control: Control,
        log_path: str,
        title: str,
        description: str,
        expiration_days: int = 90,
    ) -> Optional[EvidenceItem]:
        """
        Collect log file as evidence.

        Args:
            control: Control this evidence supports
            log_path: Path to log file
            title: Evidence title
            description: Evidence description
            expiration_days: Days until evidence expires

        Returns:
            Evidence item or None if collection failed
        """
        if not os.path.exists(log_path):
            logger.warning(f"Log file not found: {log_path}")
            return None

        # Copy log to evidence storage
        evidence_filename = f"{control.control_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_log.txt"
        evidence_path = os.path.join(self.config.evidence_storage_path, evidence_filename)

        try:
            shutil.copy2(log_path, evidence_path)
        except Exception as e:
            logger.error(f"Failed to copy log file: {e}")
            return None

        # Calculate file hash and size
        file_hash = self._calculate_file_hash(evidence_path)
        file_size = os.path.getsize(evidence_path)

        # Create evidence
        evidence = Evidence(
            evidence_type=EvidenceType.LOG,
            control_id=control.control_id,
            title=title,
            description=description,
            collected_by="evidence_collector",
            file_path=evidence_path,
            file_hash=file_hash,
            expiration_date=datetime.utcnow() + timedelta(days=expiration_days),
        )

        evidence_item = EvidenceItem(
            evidence=evidence,
            file_size=file_size,
            collected_from=log_path,
            integrity_verified=True,
            verification_timestamp=datetime.utcnow(),
        )

        # Cache evidence
        if control.control_id not in self._evidence_cache:
            self._evidence_cache[control.control_id] = []
        self._evidence_cache[control.control_id].append(evidence_item)

        logger.info(f"Collected log evidence for {control.control_id}: {title}")

        return evidence_item

    def collect_configuration_evidence(
        self,
        control: Control,
        config_path: str,
        title: str,
        description: str,
        expiration_days: int = 180,
    ) -> Optional[EvidenceItem]:
        """
        Collect configuration file as evidence.

        Args:
            control: Control this evidence supports
            config_path: Path to configuration file
            title: Evidence title
            description: Evidence description
            expiration_days: Days until evidence expires

        Returns:
            Evidence item or None if collection failed
        """
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found: {config_path}")
            return None

        # Copy config to evidence storage
        evidence_filename = f"{control.control_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_config.txt"
        evidence_path = os.path.join(self.config.evidence_storage_path, evidence_filename)

        try:
            shutil.copy2(config_path, evidence_path)
        except Exception as e:
            logger.error(f"Failed to copy configuration file: {e}")
            return None

        # Calculate file hash and size
        file_hash = self._calculate_file_hash(evidence_path)
        file_size = os.path.getsize(evidence_path)

        # Create evidence
        evidence = Evidence(
            evidence_type=EvidenceType.CONFIGURATION,
            control_id=control.control_id,
            title=title,
            description=description,
            collected_by="evidence_collector",
            file_path=evidence_path,
            file_hash=file_hash,
            expiration_date=datetime.utcnow() + timedelta(days=expiration_days),
        )

        evidence_item = EvidenceItem(
            evidence=evidence,
            file_size=file_size,
            collected_from=config_path,
            integrity_verified=True,
            verification_timestamp=datetime.utcnow(),
        )

        # Cache evidence
        if control.control_id not in self._evidence_cache:
            self._evidence_cache[control.control_id] = []
        self._evidence_cache[control.control_id].append(evidence_item)

        logger.info(f"Collected configuration evidence for {control.control_id}: {title}")

        return evidence_item

    def collect_test_evidence(
        self,
        control: Control,
        test_result_path: str,
        title: str,
        description: str,
        expiration_days: int = 90,
    ) -> Optional[EvidenceItem]:
        """
        Collect test results as evidence.

        Args:
            control: Control this evidence supports
            test_result_path: Path to test results file
            title: Evidence title
            description: Evidence description
            expiration_days: Days until evidence expires

        Returns:
            Evidence item or None if collection failed
        """
        if not os.path.exists(test_result_path):
            logger.warning(f"Test results file not found: {test_result_path}")
            return None

        # Copy test results to evidence storage
        evidence_filename = f"{control.control_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_test.txt"
        evidence_path = os.path.join(self.config.evidence_storage_path, evidence_filename)

        try:
            shutil.copy2(test_result_path, evidence_path)
        except Exception as e:
            logger.error(f"Failed to copy test results file: {e}")
            return None

        # Calculate file hash and size
        file_hash = self._calculate_file_hash(evidence_path)
        file_size = os.path.getsize(evidence_path)

        # Create evidence
        evidence = Evidence(
            evidence_type=EvidenceType.TEST_RESULT,
            control_id=control.control_id,
            title=title,
            description=description,
            collected_by="evidence_collector",
            file_path=evidence_path,
            file_hash=file_hash,
            expiration_date=datetime.utcnow() + timedelta(days=expiration_days),
        )

        evidence_item = EvidenceItem(
            evidence=evidence,
            file_size=file_size,
            collected_from=test_result_path,
            integrity_verified=True,
            verification_timestamp=datetime.utcnow(),
        )

        # Cache evidence
        if control.control_id not in self._evidence_cache:
            self._evidence_cache[control.control_id] = []
        self._evidence_cache[control.control_id].append(evidence_item)

        logger.info(f"Collected test evidence for {control.control_id}: {title}")

        return evidence_item

    def collect_document_evidence(
        self,
        control: Control,
        doc_path: str,
        title: str,
        description: str,
        expiration_days: int = 365,
    ) -> Optional[EvidenceItem]:
        """
        Collect document as evidence (policy, procedure, manual, etc).

        Args:
            control: Control this evidence supports
            doc_path: Path to document
            title: Evidence title
            description: Evidence description
            expiration_days: Days until evidence expires

        Returns:
            Evidence item or None if collection failed
        """
        if not os.path.exists(doc_path):
            logger.warning(f"Document not found: {doc_path}")
            return None

        # Copy document to evidence storage
        file_ext = Path(doc_path).suffix
        evidence_filename = f"{control.control_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_doc{file_ext}"
        evidence_path = os.path.join(self.config.evidence_storage_path, evidence_filename)

        try:
            shutil.copy2(doc_path, evidence_path)
        except Exception as e:
            logger.error(f"Failed to copy document: {e}")
            return None

        # Calculate file hash and size
        file_hash = self._calculate_file_hash(evidence_path)
        file_size = os.path.getsize(evidence_path)

        # Create evidence
        evidence = Evidence(
            evidence_type=EvidenceType.DOCUMENT,
            control_id=control.control_id,
            title=title,
            description=description,
            collected_by="evidence_collector",
            file_path=evidence_path,
            file_hash=file_hash,
            expiration_date=datetime.utcnow() + timedelta(days=expiration_days),
        )

        evidence_item = EvidenceItem(
            evidence=evidence,
            file_size=file_size,
            collected_from=doc_path,
            integrity_verified=True,
            verification_timestamp=datetime.utcnow(),
        )

        # Cache evidence
        if control.control_id not in self._evidence_cache:
            self._evidence_cache[control.control_id] = []
        self._evidence_cache[control.control_id].append(evidence_item)

        logger.info(f"Collected document evidence for {control.control_id}: {title}")

        return evidence_item

    def collect_policy_evidence(
        self,
        control: Control,
        policy_path: str,
        title: str,
        description: str,
    ) -> Optional[EvidenceItem]:
        """
        Collect organizational policy as evidence.

        Args:
            control: Control this evidence supports
            policy_path: Path to policy document
            title: Evidence title
            description: Evidence description

        Returns:
            Evidence item or None if collection failed
        """
        if not os.path.exists(policy_path):
            logger.warning(f"Policy document not found: {policy_path}")
            return None

        # Copy policy to evidence storage
        file_ext = Path(policy_path).suffix
        evidence_filename = f"{control.control_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_policy{file_ext}"
        evidence_path = os.path.join(self.config.evidence_storage_path, evidence_filename)

        try:
            shutil.copy2(policy_path, evidence_path)
        except Exception as e:
            logger.error(f"Failed to copy policy document: {e}")
            return None

        # Calculate file hash and size
        file_hash = self._calculate_file_hash(evidence_path)
        file_size = os.path.getsize(evidence_path)

        # Policies typically don't expire (annual review)
        expiration_date = datetime.utcnow() + timedelta(days=365)

        # Create evidence
        evidence = Evidence(
            evidence_type=EvidenceType.POLICY,
            control_id=control.control_id,
            title=title,
            description=description,
            collected_by="evidence_collector",
            file_path=evidence_path,
            file_hash=file_hash,
            expiration_date=expiration_date,
        )

        evidence_item = EvidenceItem(
            evidence=evidence,
            file_size=file_size,
            collected_from=policy_path,
            integrity_verified=True,
            verification_timestamp=datetime.utcnow(),
        )

        # Cache evidence
        if control.control_id not in self._evidence_cache:
            self._evidence_cache[control.control_id] = []
        self._evidence_cache[control.control_id].append(evidence_item)

        logger.info(f"Collected policy evidence for {control.control_id}: {title}")

        return evidence_item

    def get_evidence_for_control(self, control_id: str) -> List[Evidence]:
        """
        Get all collected evidence for a control.

        Args:
            control_id: Control ID

        Returns:
            List of evidence items
        """
        if control_id not in self._evidence_cache:
            return []

        return [item.evidence for item in self._evidence_cache[control_id]]

    def get_all_evidence(self) -> Dict[str, List[Evidence]]:
        """
        Get all collected evidence organized by control.

        Returns:
            Dict mapping control_id -> evidence list
        """
        return {
            control_id: [item.evidence for item in items]
            for control_id, items in self._evidence_cache.items()
        }

    def create_evidence_package(
        self,
        regulation_type: RegulationType,
        control_ids: Optional[List[str]] = None,
    ) -> EvidencePackage:
        """
        Create evidence package for audit.

        Args:
            regulation_type: Regulation type
            control_ids: Optional list of control IDs (all if None)

        Returns:
            Evidence package
        """
        logger.info(f"Creating evidence package for {regulation_type.value}")

        # Filter evidence
        if control_ids:
            evidence_items = [
                item
                for control_id, items in self._evidence_cache.items()
                if control_id in control_ids
                for item in items
            ]
            included_controls = control_ids
        else:
            evidence_items = [
                item
                for items in self._evidence_cache.values()
                for item in items
            ]
            included_controls = list(self._evidence_cache.keys())

        # Create package
        package = EvidencePackage(
            regulation_type=regulation_type,
            control_ids=included_controls,
            evidence_items=evidence_items,
        )

        logger.info(
            f"Evidence package created: {package.package_id}, "
            f"{len(evidence_items)} items, {package.total_size_bytes} bytes"
        )

        return package

    def export_evidence_package(
        self,
        package: EvidencePackage,
        export_path: str,
    ) -> bool:
        """
        Export evidence package to directory for auditor.

        Args:
            package: Evidence package to export
            export_path: Directory to export to

        Returns:
            True if export successful
        """
        logger.info(f"Exporting evidence package {package.package_id} to {export_path}")

        try:
            # Create export directory
            os.makedirs(export_path, exist_ok=True)

            # Copy evidence files
            for item in package.evidence_items:
                if item.evidence.file_path and os.path.exists(item.evidence.file_path):
                    filename = os.path.basename(item.evidence.file_path)
                    dest_path = os.path.join(export_path, filename)
                    shutil.copy2(item.evidence.file_path, dest_path)

            # Write manifest
            manifest_path = os.path.join(export_path, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(package.manifest, f, indent=2)

            # Update package path
            package.package_path = export_path

            logger.info(f"Evidence package exported successfully to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export evidence package: {e}")
            return False

    def verify_all_evidence(self) -> Dict[str, bool]:
        """
        Verify integrity of all collected evidence.

        Returns:
            Dict mapping evidence_id -> verification result
        """
        logger.info("Verifying integrity of all collected evidence")

        results: Dict[str, bool] = {}

        for items in self._evidence_cache.values():
            for item in items:
                if item.evidence.file_path:
                    verified = item.verify_integrity(item.evidence.file_path)
                    results[item.evidence.evidence_id] = verified

        passed = sum(1 for v in results.values() if v)
        logger.info(f"Evidence integrity verification complete: {passed}/{len(results)} passed")

        return results

    def get_expired_evidence(self) -> List[Evidence]:
        """
        Get all evidence that has expired.

        Returns:
            List of expired evidence
        """
        expired = []

        for items in self._evidence_cache.values():
            for item in items:
                if item.evidence.is_expired():
                    expired.append(item.evidence)

        return expired

    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
