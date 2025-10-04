"""Immunis System - Macrophage Core Logic.

This module simulates the function of a Macrophage, a type of phagocytic cell
in the innate immune system. Macrophages engulf and digest cellular debris,
pathogens, and other foreign substances. They also play a critical role as
antigen-presenting cells (APCs) to initiate the adaptive immune response.

Biological Analogy:
-   **Phagocytosis**: Ingesting a file (the "pathogen").
-   **Digestion**: Performing static and dynamic analysis to break down the file's
    components and behavior.
-   **Antigen Presentation**: Extracting key features (IOCs, behavioral patterns)
    and packaging them as an "antigen" to be sent to other immune cells.
"""

import logging
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

import yara
import pefile

logger = logging.getLogger(__name__)


class MalwareFamily(str, Enum):
    """Enumeration for known malware families."""
    RANSOMWARE = "ransomware"
    TROJAN = "trojan"
    UNKNOWN = "unknown"


class ThreatSeverity(str, Enum):
    """Enumeration for threat severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    BENIGN = "benign"


@dataclass
class IOC:
    """Represents a single Indicator of Compromise (IOC)."""
    ioc_type: str
    value: str


@dataclass
class Antigen:
    """Represents a processed antigen ready for presentation to the adaptive immune system.

    Attributes:
        antigen_id (str): A unique ID for the antigen.
        sample_hash (str): The SHA256 hash of the original file.
        malware_family (MalwareFamily): The classified malware family.
        iocs (List[IOC]): A list of extracted Indicators of Compromise.
    """
    antigen_id: str
    sample_hash: str
    malware_family: MalwareFamily
    severity: ThreatSeverity
    iocs: List[IOC]


@dataclass
class PhagocytosisResult:
    """Represents the result of phagocytosing and analyzing a file sample."""
    success: bool
    sample_hash: str
    antigen: Optional[Antigen]
    analysis_time_ms: float


class MacrophageCore:
    """Simulates a Macrophage, performing deep analysis of potential threats.

    This class provides the core functionality to "phagocytose" (ingest and analyze)
    a file, perform static and dynamic analysis, extract IOCs, and generate an
    antigen for the adaptive immune system.
    """

    def __init__(self, yara_rules_path: Optional[Path] = None):
        """Initializes the MacrophageCore.

        Args:
            yara_rules_path (Optional[Path]): The path to a file containing YARA rules.
        """
        self.yara_rules = yara.compile(filepath=str(yara_rules_path)) if yara_rules_path else None
        self.stats = {"samples_analyzed": 0, "malware_detected": 0}

    async def phagocytose(self, sample_path: Path) -> PhagocytosisResult:
        """Engulfs and analyzes a file sample to identify threats.

        This method orchestrates the entire analysis pipeline, from hashing and
        static analysis to classification and antigen generation.

        Args:
            sample_path (Path): The path to the file sample to be analyzed.

        Returns:
            PhagocytosisResult: An object containing the analysis results and the
                generated antigen, if any.
        """
        start_time = time.time()
        try:
            if not sample_path.exists(): raise FileNotFoundError(f"Sample not found: {sample_path}")
            
            sample_hash = self._compute_hash(sample_path)
            static_features = self._static_analysis(sample_path)
            iocs = self._extract_iocs(static_features)
            family, severity, confidence = self._classify(static_features, iocs)

            antigen = None
            if severity != ThreatSeverity.BENIGN:
                antigen = Antigen(
                    antigen_id=f"ag_{sample_hash[:12]}",
                    sample_hash=sample_hash,
                    malware_family=family,
                    severity=severity,
                    iocs=iocs
                )
                self.stats["malware_detected"] += 1
            
            self.stats["samples_analyzed"] += 1
            return PhagocytosisResult(True, sample_hash, antigen, (time.time() - start_time) * 1000)

        except Exception as e:
            logger.error(f"Phagocytosis failed for {sample_path}: {e}")
            return PhagocytosisResult(False, "", None, (time.time() - start_time) * 1000)

    def _compute_hash(self, file_path: Path) -> str:
        """Computes the SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _static_analysis(self, sample_path: Path) -> Dict:
        """Performs static analysis on a file, extracting features like entropy and strings."""
        # Simplified static analysis for demonstration
        return {"entropy": 7.5, "strings": ["kernel32.dll", "CreateFileA"]}

    def _extract_iocs(self, static_features: Dict) -> List[IOC]:
        """Extracts Indicators of Compromise from static analysis features."""
        # Simplified IOC extraction
        return [IOC(ioc_type="dll", value=s) for s in static_features.get("strings", [])]

    def _classify(self, static_features: Dict, iocs: List[IOC]) -> Tuple[MalwareFamily, ThreatSeverity, float]:
        """Classifies the sample based on its features.

        Returns:
            A tuple containing the malware family, threat severity, and confidence score.
        """
        if static_features.get("entropy", 0) > 7.0: 
            return (MalwareFamily.RANSOMWARE, ThreatSeverity.CRITICAL, 0.8)
        return (MalwareFamily.UNKNOWN, ThreatSeverity.BENIGN, 0.9)

    def get_stats(self) -> Dict[str, int]:
        """Returns a dictionary of performance statistics."""
        return self.stats