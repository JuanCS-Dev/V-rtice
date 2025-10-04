"""Immunis System - B Cell Core Logic.

This module simulates the function of B lymphocytes (B cells) in the adaptive
immune system. Its primary roles are antibody production and the formation of
immunological memory.

Biological Analogy:
-   **Antigen Recognition**: A B cell recognizes a specific antigen (a threat).
-   **Activation & Differentiation**: It becomes a plasma cell, a factory for antibodies.
-   **Antibody Production**: It produces antibodies (signatures like YARA or Snort rules)
    that are specific to the antigen.
-   **Affinity Maturation**: The antibodies are refined over time to improve their
    specificity and effectiveness (reducing false positives).
-   **Memory Formation**: Some B cells become long-lived memory cells, allowing for a
    faster and stronger response to future encounters with the same threat.
"""

import logging
import time
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AntibodyIsotype(str, Enum):
    """Enumeration for antibody classes, analogous to signature specificity."""
    IGM = "igm"  # Early, broad-spectrum signature (low specificity).
    IGG = "igg"  # Mature, refined signature (high specificity).
    IGA = "iga"  # Network-level signature.


class SignatureType(str, Enum):
    """Enumeration for the format of the detection signature."""
    YARA = "yara"
    SNORT = "snort"
    SIGMA = "sigma"


@dataclass
class Antibody:
    """Represents a detection signature, analogous to a biological antibody.

    Attributes:
        antibody_id (str): A unique identifier for the antibody.
        antigen_id (str): The ID of the antigen that this antibody targets.
        isotype (AntibodyIsotype): The class or specificity level of the antibody.
        signature_type (SignatureType): The format of the signature (e.g., YARA).
        signature_content (str): The actual detection rule or signature.
        version (int): The version of the antibody, incremented during affinity maturation.
    """
    antibody_id: str
    antigen_id: str
    isotype: AntibodyIsotype
    signature_type: SignatureType
    signature_content: str
    version: int = 1
    true_positives: int = 0
    false_positives: int = 0

    @property
    def precision(self) -> float:
        """Calculates the precision of the antibody (TP / (TP + FP))."""
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0


class BCellCore:
    """Simulates a B cell, responsible for antibody production and memory.

    This class manages the lifecycle of generating, refining, and storing detection
    signatures (antibodies) in response to threats (antigens).
    """

    def __init__(self, bcell_id: str):
        """Initializes the BCellCore.

        Args:
            bcell_id (str): A unique identifier for this B cell instance.
        """
        self.bcell_id = bcell_id
        self.antibodies: Dict[str, Antibody] = {}
        self.memory_cells: Dict[str, Antibody] = {}
        logger.info(f"B Cell {bcell_id} initialized.")

    def generate_antibodies(self, antigen: Dict) -> List[Antibody]:
        """Generates a set of initial antibodies (signatures) for a given antigen.

        This process is analogous to clonal selection, where a B cell produces
        initial, low-affinity antibodies (IgM) upon first encountering an antigen.

        Args:
            antigen (Dict): A dictionary of features describing the threat.

        Returns:
            List[Antibody]: A list of newly generated Antibody objects.
        """
        logger.info(f"Generating antibodies for antigen {antigen.get('antigen_id')}")
        new_antibodies = []
        for sig_type in [SignatureType.YARA, SignatureType.SNORT]:
            content = self._create_signature_content(antigen, sig_type)
            if content:
                antibody_id = f"ab_{sig_type.value}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
                antibody = Antibody(
                    antibody_id=antibody_id,
                    antigen_id=antigen.get('antigen_id', 'unknown'),
                    isotype=AntibodyIsotype.IGM, # Start with low-affinity IgM
                    signature_type=sig_type,
                    signature_content=content
                )
                self.antibodies[antibody_id] = antibody
                new_antibodies.append(antibody)
        return new_antibodies

    def _create_signature_content(self, antigen: Dict, sig_type: SignatureType) -> Optional[str]:
        """Creates the specific rule content for a given signature type."""
        iocs = antigen.get('iocs', [])
        if not iocs: return None

        if sig_type == SignatureType.YARA:
            string_conditions = " or ".join([f'$ioc{i}' for i in range(len(iocs))])
            return f'rule gen_{antigen["antigen_id"]} {{ strings: ... condition: {string_conditions} }}'
        elif sig_type == SignatureType.SNORT:
            ip_ioc = next((ioc['value'] for ioc in iocs if ioc['ioc_type'] == 'ip'), None)
            if ip_ioc: return f'alert ip any any -> {ip_ioc} any (msg:"Threat detected"; sid:{1000000 + len(self.antibodies)}; rev:1;)'
        return None

    def affinity_maturation(self, antibody: Antibody, test_results: Dict) -> Optional[Antibody]:
        """Refines an antibody to improve its precision, analogous to somatic hypermutation.

        If an antibody has poor performance (low precision), this method attempts
        to generate a new, more specific version.

        Args:
            antibody (Antibody): The antibody to mature.
            test_results (Dict): A dictionary with 'true_positives' and 'false_positives'.

        Returns:
            Optional[Antibody]: A new, improved antibody if maturation was successful,
                otherwise None.
        """
        antibody.true_positives += test_results.get('true_positives', 0)
        antibody.false_positives += test_results.get('false_positives', 0)

        if antibody.precision < 0.8:
            logger.info(f"Maturing antibody {antibody.antibody_id} due to low precision ({antibody.precision:.2f})")
            # In a real system, this would involve complex rule refinement.
            # Here, we simulate by creating a new version with a more specific isotype.
            new_content = antibody.signature_content + " and some_new_condition"
            new_id = f"{antibody.antibody_id}_v{antibody.version + 1}"
            improved_antibody = Antibody(
                antibody_id=new_id,
                antigen_id=antibody.antigen_id,
                isotype=AntibodyIsotype.IGG, # Switch to high-affinity IgG
                signature_type=antibody.signature_type,
                signature_content=new_content,
                version=antibody.version + 1
            )
            self.antibodies[new_id] = improved_antibody
            return improved_antibody
        return None

    def form_memory(self, antibody: Antibody):
        """Stores a high-affinity antibody as a memory cell for long-term immunity."""
        if antibody.precision > 0.95:
            logger.info(f"Forming memory cell for antibody {antibody.antibody_id}")
            self.memory_cells[antibody.antigen_id] = antibody