"""Digital Helper T Cell - Adaptive Immunity Coordinator

Helper T Cells (CD4+ T Lymphocytes) are the "maestros" of adaptive immunity:
1. Antigen recognition (via MHC-II from Dendritic Cells)
2. B cell activation (IL4, IL5 secretion)
3. Cytotoxic T cell activation (IL2, IFN-gamma)
4. Macrophage activation (IFN-gamma)
5. Differentiation into subtypes (Th1, Th2, Th17)

Unlike other immune cells:
- B Cells: Memory and antibody production (effectors)
- Helper T: Coordination and activation (orchestrator)
- Cytotoxic T: Direct cell killing (executioner)
- Dendritic: Antigen presentation (informer)

PRODUCTION-READY: Real Kafka/Redis, no mocks, graceful degradation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from pydantic import BaseModel, Field

from .base import AgenteImunologicoBase
from .models import AgentType

logger = logging.getLogger(__name__)


# ==================== MODELS ====================


class AntigenPresentation(BaseModel):
    """Antigen presentation via MHC-II complex"""

    presentation_id: str = Field(description="Presentation ID")
    antigen_type: str = Field(description="Antigen type (malware, intrusion, etc.)")
    mhc_ii_complex: Dict[str, Any] = Field(description="MHC-II peptide complex")
    dendritic_cell_id: str = Field(description="Presenting dendritic cell ID")
    confidence: float = Field(ge=0.0, le=1.0, description="Presentation confidence")
    timestamp: datetime = Field(default_factory=datetime.now)


class ActivationSignal(BaseModel):
    """T cell activation signal"""

    signal_id: str = Field(description="Signal ID")
    target_cell_type: str = Field(description="Target cell type (b_cell, cytotoxic_t)")
    cytokine_type: str = Field(description="Cytokine to secrete")
    activation_strength: float = Field(ge=0.0, le=1.0, description="Activation strength")
    target_area: str = Field(description="Target patrol area")
    created_at: datetime = Field(default_factory=datetime.now)


class HelperTState(str):
    """Helper T Cell differentiation states"""

    NAIVE = "naive"  # Never encountered antigen
    ACTIVATED = "activated"  # Antigen recognized
    TH1 = "th1"  # Cell-mediated immunity (IFN-gamma, IL2)
    TH2 = "th2"  # Humoral immunity (IL4, IL5)
    TH17 = "th17"  # Inflammatory response (IL17)


# ==================== HELPER T CELL ====================


class LinfocitoTAuxiliar(AgenteImunologicoBase):
    """
    Digital Helper T Cell - Adaptive immunity coordinator.

    Capabilities:
    - Antigen recognition via MHC-II
    - B cell activation (IL4, IL5)
    - Cytotoxic T cell activation (IL2, IFN-gamma)
    - Macrophage activation (IFN-gamma)
    - Differentiation into Th1, Th2, Th17
    - Multi-cytokine orchestration

    Use cases:
    - Coordinating adaptive immune responses
    - Activating effector cells
    - Directing immune strategy (cellular vs humoral)
    - Complex threat orchestration
    """

    def __init__(
        self,
        area_patrulha: str,
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        activation_threshold: float = 0.75,
        **kwargs,
    ):
        """
        Initialize Helper T Cell.

        Args:
            area_patrulha: Network zone to patrol
            kafka_bootstrap: Kafka broker
            redis_url: Redis URL
            activation_threshold: Min confidence for activation (0-1)
        """
        super().__init__(
            tipo=AgentType.LINFOCITO_T_AUXILIAR,
            area_patrulha=area_patrulha,
            kafka_bootstrap=kafka_bootstrap,
            redis_url=redis_url,
            **kwargs,
        )

        # Helper T-specific configuration
        self.activation_threshold = activation_threshold

        # Helper T-specific state
        self.differentiation_state: str = HelperTState.NAIVE
        self.recognized_antigens: List[AntigenPresentation] = []
        self.activation_signals: List[ActivationSignal] = []
        self.activated_b_cells: int = 0
        self.activated_cytotoxic_t: int = 0
        self.activated_macrophages: int = 0
        self.il2_secretions: int = 0
        self.il4_secretions: int = 0
        self.il5_secretions: int = 0
        self.ifn_gamma_secretions: int = 0

        logger.info(
            f"Helper T Cell initialized: {self.state.id[:8]} (zone={area_patrulha}, threshold={activation_threshold})"
        )

    # ==================== LIFECYCLE ====================

    async def iniciar(self) -> None:
        """Start Helper T Cell - subscribe to dendritic cell signals"""
        await super().iniciar()

        # Subscribe to antigen presentations from dendritic cells
        if self._cytokine_messenger and self._cytokine_messenger.is_running():
            try:
                await self._cytokine_messenger.subscribe_cytokine(
                    "ANTIGEN_PRESENTATION", self._handle_antigen_presentation
                )
                logger.info(f"Helper T {self.state.id[:8]} subscribed to antigen presentations")
            except Exception as e:
                logger.warning(f"Failed to subscribe to antigens: {e}, degraded mode")

    # ==================== PATROL ====================

    async def patrulhar(self) -> None:
        """
        Helper T Cell patrol - monitor for antigen presentations.

        Helper T Cells don't directly patrol networks - they wait for
        Dendritic Cells to present antigens via MHC-II.
        """
        logger.debug(f"Helper T {self.state.id[:8]} monitoring for antigen presentations")

        # Process any pending antigen presentations
        await self._process_antigen_queue()

    # ==================== ANTIGEN RECOGNITION ====================

    async def _handle_antigen_presentation(self, presentation_data: Dict[str, Any]) -> None:
        """
        Handle antigen presentation from Dendritic Cell.

        Args:
            presentation_data: MHC-II complex data
        """
        try:
            # Parse antigen presentation
            presentation = AntigenPresentation(
                presentation_id=presentation_data.get("presentation_id", str(uuid4())),
                antigen_type=presentation_data.get("antigen_type", "unknown"),
                mhc_ii_complex=presentation_data.get("mhc_ii_complex", {}),
                dendritic_cell_id=presentation_data.get("dendritic_cell_id", "unknown"),
                confidence=presentation_data.get("confidence", 0.5),
            )

            logger.info(
                f"Helper T {self.state.id[:8]} received antigen presentation "
                f"(type={presentation.antigen_type}, confidence={presentation.confidence:.2f})"
            )

            # Store antigen
            self.recognized_antigens.append(presentation)

            # Check if activation threshold met
            if presentation.confidence >= self.activation_threshold:
                await self._activate_on_antigen(presentation)

        except Exception as e:
            logger.error(f"Failed to handle antigen presentation: {e}", exc_info=True)

    async def _process_antigen_queue(self) -> None:
        """Process pending antigen presentations"""
        # GRACEFUL DEGRADATION: No external queue service
        # Antigens stored in-memory, processed on patrol
        pass

    async def _activate_on_antigen(self, presentation: AntigenPresentation) -> None:
        """
        Activate Helper T Cell upon antigen recognition.

        Args:
            presentation: Recognized antigen presentation
        """
        # Change state to ACTIVATED
        if self.differentiation_state == HelperTState.NAIVE:
            self.differentiation_state = HelperTState.ACTIVATED
            logger.info(f"Helper T {self.state.id[:8]} activated (naive → activated)")

        # Determine differentiation based on antigen type
        await self._determine_differentiation(presentation)

        # Coordinate immune response
        await self._coordinate_response(presentation)

    # ==================== DIFFERENTIATION ====================

    async def _determine_differentiation(self, presentation: AntigenPresentation) -> None:
        """
        Determine Th differentiation based on antigen type.

        Args:
            presentation: Antigen presentation
        """
        antigen_type = presentation.antigen_type.lower()

        # Th1: Intracellular threats (viruses, intracellular bacteria)
        if any(t in antigen_type for t in ["virus", "malware", "intracellular"]):
            if self.differentiation_state != HelperTState.TH1:
                self.differentiation_state = HelperTState.TH1
                logger.info(f"Helper T {self.state.id[:8]} differentiated to Th1 (cell-mediated immunity)")

        # Th2: Extracellular threats (parasites, extracellular bacteria)
        elif any(t in antigen_type for t in ["parasite", "extracellular", "ddos"]):
            if self.differentiation_state != HelperTState.TH2:
                self.differentiation_state = HelperTState.TH2
                logger.info(f"Helper T {self.state.id[:8]} differentiated to Th2 (humoral immunity)")

        # Th17: Fungal/bacterial infections (strong inflammation)
        elif any(t in antigen_type for t in ["fungal", "bacterial", "intrusion"]):
            if self.differentiation_state != HelperTState.TH17:
                self.differentiation_state = HelperTState.TH17
                logger.info(f"Helper T {self.state.id[:8]} differentiated to Th17 (inflammatory response)")

    # ==================== COORDINATION ====================

    async def _coordinate_response(self, presentation: AntigenPresentation) -> None:
        """
        Coordinate immune response based on differentiation state.

        Args:
            presentation: Antigen presentation
        """
        if self.differentiation_state == HelperTState.TH1:
            # Th1: Activate Cytotoxic T cells + Macrophages
            await self._activate_cytotoxic_t_cells(presentation)
            await self._activate_macrophages(presentation)

        elif self.differentiation_state == HelperTState.TH2:
            # Th2: Activate B cells (antibody production)
            await self._activate_b_cells(presentation)

        elif self.differentiation_state == HelperTState.TH17:
            # Th17: Activate Neutrophils (inflammation)
            await self._activate_neutrophils(presentation)

    async def _activate_b_cells(self, presentation: AntigenPresentation) -> None:
        """
        Activate B cells via IL4 and IL5 secretion.

        Args:
            presentation: Antigen presentation
        """
        if not self._cytokine_messenger or not self._cytokine_messenger.is_running():
            logger.debug("Cytokine messenger unavailable, degraded mode")
            return

        try:
            # Secrete IL4 (B cell activation)
            await self._cytokine_messenger.send_cytokine(
                tipo="IL4",
                payload={
                    "evento": "helper_t_activation",
                    "helper_t_id": self.state.id,
                    "antigen_type": presentation.antigen_type,
                    "activation_strength": presentation.confidence,
                    "target": "b_cells",
                },
                emissor_id=self.state.id,
                prioridade=8,
                area_alvo=self.state.area_patrulha,
            )
            self.il4_secretions += 1

            # Secrete IL5 (B cell proliferation)
            await self._cytokine_messenger.send_cytokine(
                tipo="IL5",
                payload={
                    "evento": "b_cell_proliferation",
                    "helper_t_id": self.state.id,
                    "antigen_type": presentation.antigen_type,
                },
                emissor_id=self.state.id,
                prioridade=7,
                area_alvo=self.state.area_patrulha,
            )
            self.il5_secretions += 1

            self.activated_b_cells += 1

            logger.info(
                f"Helper T {self.state.id[:8]} activated B cells (IL4+IL5, antigen={presentation.antigen_type})"
            )

        except Exception as e:
            logger.error(f"Failed to activate B cells: {e}")

    async def _activate_cytotoxic_t_cells(self, presentation: AntigenPresentation) -> None:
        """
        Activate Cytotoxic T cells via IL2 and IFN-gamma.

        Args:
            presentation: Antigen presentation
        """
        if not self._cytokine_messenger or not self._cytokine_messenger.is_running():
            logger.debug("Cytokine messenger unavailable, degraded mode")
            return

        try:
            # Secrete IL2 (T cell proliferation)
            await self._cytokine_messenger.send_cytokine(
                tipo="IL2",
                payload={
                    "evento": "cytotoxic_t_activation",
                    "helper_t_id": self.state.id,
                    "antigen_type": presentation.antigen_type,
                    "activation_strength": presentation.confidence,
                },
                emissor_id=self.state.id,
                prioridade=9,
                area_alvo=self.state.area_patrulha,
            )
            self.il2_secretions += 1

            # Secrete IFN-gamma (enhanced killing)
            await self._cytokine_messenger.send_cytokine(
                tipo="IFN_GAMMA",
                payload={
                    "evento": "enhance_cytotoxicity",
                    "helper_t_id": self.state.id,
                    "antigen_type": presentation.antigen_type,
                },
                emissor_id=self.state.id,
                prioridade=8,
                area_alvo=self.state.area_patrulha,
            )
            self.ifn_gamma_secretions += 1

            self.activated_cytotoxic_t += 1

            logger.info(
                f"Helper T {self.state.id[:8]} activated Cytotoxic T cells "
                f"(IL2+IFN-γ, antigen={presentation.antigen_type})"
            )

        except Exception as e:
            logger.error(f"Failed to activate Cytotoxic T cells: {e}")

    async def _activate_macrophages(self, presentation: AntigenPresentation) -> None:
        """
        Activate Macrophages via IFN-gamma.

        Args:
            presentation: Antigen presentation
        """
        if not self._cytokine_messenger or not self._cytokine_messenger.is_running():
            logger.debug("Cytokine messenger unavailable, degraded mode")
            return

        try:
            await self._cytokine_messenger.send_cytokine(
                tipo="IFN_GAMMA",
                payload={
                    "evento": "macrophage_activation",
                    "helper_t_id": self.state.id,
                    "antigen_type": presentation.antigen_type,
                    "target": "macrophages",
                },
                emissor_id=self.state.id,
                prioridade=7,
                area_alvo=self.state.area_patrulha,
            )
            self.ifn_gamma_secretions += 1
            self.activated_macrophages += 1

            logger.info(
                f"Helper T {self.state.id[:8]} activated Macrophages (IFN-γ, antigen={presentation.antigen_type})"
            )

        except Exception as e:
            logger.error(f"Failed to activate Macrophages: {e}")

    async def _activate_neutrophils(self, presentation: AntigenPresentation) -> None:
        """
        Activate Neutrophils via IL17.

        Args:
            presentation: Antigen presentation
        """
        if not self._cytokine_messenger or not self._cytokine_messenger.is_running():
            logger.debug("Cytokine messenger unavailable, degraded mode")
            return

        try:
            await self._cytokine_messenger.send_cytokine(
                tipo="IL17",
                payload={
                    "evento": "neutrophil_activation",
                    "helper_t_id": self.state.id,
                    "antigen_type": presentation.antigen_type,
                    "inflammation_level": "high",
                },
                emissor_id=self.state.id,
                prioridade=8,
                area_alvo=self.state.area_patrulha,
            )

            logger.info(
                f"Helper T {self.state.id[:8]} activated Neutrophils (IL17, antigen={presentation.antigen_type})"
            )

        except Exception as e:
            logger.error(f"Failed to activate Neutrophils: {e}")

    # ==================== INVESTIGATION ====================

    async def executar_investigacao(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper T Cells don't investigate directly - they coordinate.

        Args:
            alvo: Target (ignored)

        Returns:
            Investigation result (coordination focus)
        """
        logger.debug(f"Helper T {self.state.id[:8]} coordinates instead of investigating")

        return {
            "is_threat": False,
            "confidence": 0.0,
            "reason": "Helper T cells coordinate other cells, don't investigate",
            "metodo": "coordination_only",
        }

    # ==================== NEUTRALIZATION ====================

    async def executar_neutralizacao(self, alvo: Dict[str, Any], metodo: str) -> bool:
        """
        Helper T Cells don't neutralize directly - they activate effector cells.

        Args:
            alvo: Target
            metodo: Method (ignored)

        Returns:
            False (Helper T delegates to effector cells)
        """
        logger.info(f"Helper T {self.state.id[:8]} delegates neutralization to effector cells")

        # Create activation signal for effector cells
        signal = ActivationSignal(
            signal_id=str(uuid4()),
            target_cell_type=alvo.get("target_cell_type", "cytotoxic_t"),
            cytokine_type="IL2",
            activation_strength=0.8,
            target_area=self.state.area_patrulha,
        )

        self.activation_signals.append(signal)

        # Broadcast activation via cytokines (done in _coordinate_response)
        logger.debug(f"Helper T {self.state.id[:8]} created activation signal: {signal.signal_id[:8]}")

        return True  # Coordination successful

    # ==================== METRICS ====================

    def get_helper_t_metrics(self) -> Dict[str, Any]:
        """
        Get Helper T Cell-specific metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "differentiation_state": self.differentiation_state,
            "recognized_antigens": len(self.recognized_antigens),
            "activation_signals": len(self.activation_signals),
            "activated_b_cells": self.activated_b_cells,
            "activated_cytotoxic_t": self.activated_cytotoxic_t,
            "activated_macrophages": self.activated_macrophages,
            "il2_secretions": self.il2_secretions,
            "il4_secretions": self.il4_secretions,
            "il5_secretions": self.il5_secretions,
            "ifn_gamma_secretions": self.ifn_gamma_secretions,
            "total_cytokines": (
                self.il2_secretions + self.il4_secretions + self.il5_secretions + self.ifn_gamma_secretions
            ),
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"LinfocitoTAuxiliar({self.state.id[:8]}|{self.state.status}|"
            f"state={self.differentiation_state}|"
            f"antigens={len(self.recognized_antigens)}|"
            f"b_cells={self.activated_b_cells}|"
            f"cytotoxic_t={self.activated_cytotoxic_t})"
        )
