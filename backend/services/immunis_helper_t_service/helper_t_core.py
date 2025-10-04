"""Immunis System - Helper T Cell Core Logic.

This module simulates the function of Helper T Lymphocytes (CD4+ T cells), which
are the central coordinators of the adaptive immune response. They are activated
by antigen-presenting cells (like Dendritic Cells) and, in turn, activate and
direct other immune cells like B cells and Cytotoxic T cells.

Biological Analogy:
-   **Antigen Recognition**: A Helper T cell's T-cell receptor (TCR) recognizes an
    antigen presented on an MHC-II molecule by an APC.
-   **Differentiation**: Based on the cytokine environment, the naive Helper T cell
    differentiates into a specific subset (e.g., Th1, Th2, Treg).
-   **Orchestration**: The differentiated cell secretes its own cytokines to
    activate and direct the appropriate type of immune response (e.g., Th1
    activates CTLs for cellular immunity; Th2 activates B cells for humoral immunity).
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HelperSubset(str, Enum):
    """Enumeration for the different functional subsets of Helper T cells."""
    TH0 = "th0"  # Naive, undifferentiated
    TH1 = "th1"  # Promotes cellular immunity (activates Cytotoxic T cells)
    TH2 = "th2"  # Promotes humoral immunity (activates B cells)
    TREG = "treg" # Suppresses the immune response


class ResponseStrategy(str, Enum):
    """Enumeration for the high-level immune response strategies."""
    AGGRESSIVE_CELLULAR = "aggressive_cellular"
    BALANCED_HUMORAL = "balanced_humoral"
    REGULATORY = "regulatory"


@dataclass
class AntigenPresentation:
    """Represents an antigen presented by a Dendritic Cell to a Helper T cell.

    Attributes:
        antigen_id (str): The unique ID of the antigen.
        dc_id (str): The ID of the Dendritic Cell presenting the antigen.
        malware_family (str): The malware family associated with the antigen.
        recommended_response (str): The response type recommended by the DC.
    """
    antigen_id: str
    dc_id: str
    malware_family: str
    severity: str
    confidence: float
    recommended_response: str


@dataclass
class ImmuneResponse:
    """Represents an orchestrated immune response plan.

    Attributes:
        response_id (str): A unique ID for this response plan.
        strategy (ResponseStrategy): The high-level strategy being employed.
        b_cells_activated (List[str]): A list of B cell IDs activated.
        ctl_cells_activated (List[str]): A list of Cytotoxic T cell IDs activated.
    """
    response_id: str
    strategy: ResponseStrategy
    helper_subset: HelperSubset
    b_cells_activated: List[str]
    ctl_cells_activated: List[str]


class HelperTCore:
    """Simulates a Helper T Cell, the orchestrator of the adaptive immune response.

    This class receives antigen presentations, decides on an appropriate response
    strategy (cellular vs. humoral), and issues activation signals to other
    immune cells (B cells and Cytotoxic T cells).
    """

    def __init__(self, helper_id: str):
        """Initializes the HelperTCore.

        Args:
            helper_id (str): A unique identifier for this Helper T cell instance.
        """
        self.helper_id = helper_id
        self.current_subset = HelperSubset.TH0
        self.active_responses: Dict[str, ImmuneResponse] = {}
        self.stats = {"antigens_received": 0, "responses_orchestrated": 0}

    async def receive_antigen(self, presentation: AntigenPresentation) -> ImmuneResponse:
        """Receives an antigen presentation and orchestrates a response.

        This is the main entry point. It simulates the TCR binding to the MHC-II
        complex, leading to T cell differentiation and the selection and execution
        of an immune strategy.

        Args:
            presentation (AntigenPresentation): The antigen being presented.

        Returns:
            ImmuneResponse: The orchestrated response plan.
        """
        logger.info(f"Helper T cell {self.helper_id} received antigen {presentation.antigen_id}")
        self.stats["antigens_received"] += 1

        self._differentiate(presentation.recommended_response)
        strategy = self._select_strategy(presentation)
        response = await self._orchestrate_response(presentation, strategy)
        
        self.active_responses[response.response_id] = response
        self.stats["responses_orchestrated"] += 1
        return response

    def _differentiate(self, recommendation: str):
        """Differentiates the T cell into a specific subset (Th1, Th2, etc.)."""
        if self.current_subset == HelperSubset.TH0:
            if recommendation == "th1": self.current_subset = HelperSubset.TH1
            elif recommendation == "th2": self.current_subset = HelperSubset.TH2
            else: self.current_subset = HelperSubset.TREG
            logger.info(f"Differentiated to {self.current_subset.value}")

    def _select_strategy(self, presentation: AntigenPresentation) -> ResponseStrategy:
        """Selects a response strategy based on the threat context."""
        if self.current_subset == HelperSubset.TH1: return ResponseStrategy.AGGRESSIVE_CELLULAR
        if self.current_subset == HelperSubset.TH2: return ResponseStrategy.BALANCED_HUMORAL
        return ResponseStrategy.REGULATORY

    async def _orchestrate_response(self, presentation: AntigenPresentation, strategy: ResponseStrategy) -> ImmuneResponse:
        """Orchestrates the activation of other immune cells based on the strategy."""
        logger.info(f"Orchestrating a {strategy.value} response.")
        b_cells, ctl_cells = [], []
        if strategy == ResponseStrategy.AGGRESSIVE_CELLULAR:
            ctl_cells = await self._activate_cells("cytotoxic_t", 5)
        elif strategy == ResponseStrategy.BALANCED_HUMORAL:
            b_cells = await self._activate_cells("b_cell", 3)
        
        return ImmuneResponse(
            response_id=f"resp_{int(time.time())}",
            strategy=strategy,
            helper_subset=self.current_subset,
            b_cells_activated=b_cells,
            ctl_cells_activated=ctl_cells
        )

    async def _activate_cells(self, cell_type: str, count: int) -> List[str]:
        """Simulates the activation of a number of immune cells."""
        # In a real system, this would publish activation messages to Kafka.
        logger.info(f"Activating {count} {cell_type}(s)...")
        await asyncio.sleep(0.01)
        return [f"{cell_type}_{i}" for i in range(count)]

    def get_stats(self) -> Dict[str, Any]:
        """Returns performance statistics for this Helper T cell."""
        return self.stats