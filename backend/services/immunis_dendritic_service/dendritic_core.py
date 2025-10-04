"""Immunis System - Dendritic Cell Core Logic.

This module simulates the function of Dendritic Cells (DCs), which act as the
primary antigen-presenting cells (APCs) and form a crucial bridge between the
inmate and adaptive immune systems.

Biological Analogy:
-   **Antigen Capture**: A DC in the tissue captures antigens from pathogens.
-   **Processing & Maturation**: It processes these antigens and matures while
    migrating to a lymph node.
-   **Antigen Presentation**: In the lymph node, the mature DC presents the processed
    antigen on its MHC-II molecules to Helper T cells, initiating the adaptive
    immune response.
-   **Cytokine Secretion**: It secretes signaling molecules (cytokines) like IL-12
    to direct the type of T cell response (e.g., cellular vs. humoral).
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class DendriticState(str, Enum):
    """Enumeration for the maturation states of a Dendritic Cell."""
    IMMATURE = "immature"
    SEMI_MATURE = "semi_mature"
    MATURE = "mature"


class AntigenType(str, Enum):
    """Enumeration for the types of antigens."""
    VIRAL = "viral"
    BACTERIAL = "bacterial"
    MALWARE_SIGNATURE = "malware_signature"


@dataclass
class Antigen:
    """Represents an antigen captured from a pathogen or threat.

    Attributes:
        antigen_id (str): A unique identifier for the antigen.
        source_cell (str): The innate immune cell that provided the antigen.
        malware_family (str): The family of malware this antigen is associated with.
        iocs (List[Dict]): A list of Indicators of Compromise.
    """
    antigen_id: str
    source_cell: str
    malware_family: str
    iocs: List[Dict]


@dataclass
class ProcessedAntigen:
    """Represents an antigen that has been processed and is ready for presentation.

    This is analogous to a peptide fragment loaded onto an MHC-II molecule.

    Attributes:
        antigen_id (str): The ID of the original antigen.
        feature_vector (np.ndarray): A numerical vector representing the antigen's key features.
        recommended_response (str): The recommended type of adaptive response ('th1' or 'th2').
    """
    antigen_id: str
    feature_vector: np.ndarray
    recommended_response: str


class DendriticCellCore:
    """Simulates a Dendritic Cell, bridging innate and adaptive immunity.

    This class is responsible for capturing antigens, processing them by correlating
    related events, and then presenting them to the adaptive immune system to
    initiate a targeted response.
    """

    def __init__(self, dc_id: str, maturation_threshold: int = 3):
        """Initializes the DendriticCellCore.

        Args:
            dc_id (str): A unique identifier for this DC instance.
            maturation_threshold (int): The number of antigens required to trigger maturation.
        """
        self.dc_id = dc_id
        self.maturation_threshold = maturation_threshold
        self.state = DendriticState.IMMATURE
        self.captured_antigens: List[Antigen] = []
        self.presentation_queue: List[ProcessedAntigen] = []

    async def capture_antigen(self, antigen: Antigen):
        """Captures an antigen provided by an innate immune cell.

        Args:
            antigen (Antigen): The antigen to be captured and processed.
        """
        logger.info(f"DC {self.dc_id} captured antigen {antigen.antigen_id}.")
        self.captured_antigens.append(antigen)
        if len(self.captured_antigens) >= self.maturation_threshold:
            await self._mature()

    async def _mature(self):
        """Transitions the DC to a mature state and processes captured antigens."""
        if self.state == DendriticState.IMMATURE:
            self.state = DendriticState.MATURE
            logger.info(f"DC {self.dc_id} is maturing and processing antigens.")
            await self.process_antigens()

    async def process_antigens(self) -> List[ProcessedAntigen]:
        """Processes captured antigens to prepare them for presentation.

        This involves extracting features and recommending a response type.

        Returns:
            List[ProcessedAntigen]: A list of processed antigens ready for presentation.
        """
        processed_list = []
        for antigen in self.captured_antigens:
            # Simplified feature extraction and response recommendation
            feature_vector = np.array([len(antigen.iocs), hash(antigen.malware_family) % 100])
            recommended_response = "th1" if "critical" in antigen.malware_family else "th2"
            
            processed = ProcessedAntigen(
                antigen_id=antigen.antigen_id,
                feature_vector=feature_vector,
                recommended_response=recommended_response
            )
            processed_list.append(processed)
            self.presentation_queue.append(processed)
        
        self.captured_antigens.clear() # Antigens are processed
        return processed_list

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the DC's activity."""
        return {
            "state": self.state.value,
            "captured_antigens_count": len(self.captured_antigens),
            "presentation_queue_size": len(self.presentation_queue)
        }