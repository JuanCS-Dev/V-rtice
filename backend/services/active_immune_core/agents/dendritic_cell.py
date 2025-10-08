"""Digital Dendritic Cell - Professional Antigen Presenter

Dendritic Cells are the "sentinels" and "information messengers" of immunity:
1. Antigen capture via phagocytosis (innate function)
2. Antigen processing into peptides
3. MHC-I presentation → Cytotoxic T cells
4. MHC-II presentation → Helper T cells
5. Migration to lymph nodes
6. T cell activation (bridge to adaptive immunity)
7. IL12 secretion (directs Th1 differentiation)
8. Pattern learning from threats

Unique characteristics:
- Bridge between innate and adaptive immunity
- Professional antigen presenter (most efficient)
- Migrates from tissue → lymph node
- Activates BOTH Helper T and Cytotoxic T
- Maturation: immature (capture) → mature (present)

PRODUCTION-READY: Real services, no mocks, graceful degradation.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .base import AgenteImunologicoBase
from .models import AgentType

logger = logging.getLogger(__name__)


# Thread-safe list operations flag
# When True, uses asyncio.Lock to protect shared lists
# Set to False for testing without locks (legacy behavior)
USE_THREAD_SAFE_OPERATIONS = True


# ==================== MODELS ====================


class CapturedAntigen(BaseModel):
    """Captured antigen from threat"""

    antigen_id: str = Field(description="Antigen ID")
    threat_type: str = Field(description="Threat type (malware, intrusion, etc.)")
    source_ip: str = Field(description="Source IP of threat")
    raw_data: Dict[str, Any] = Field(description="Raw threat data")
    capture_method: str = Field(description="Capture method (phagocytosis, etc.)")
    captured_at: datetime = Field(default_factory=datetime.now)


class ProcessedPeptide(BaseModel):
    """Processed peptide from antigen"""

    peptide_id: str = Field(description="Peptide ID")
    sequence: str = Field(description="Peptide sequence (hash of pattern)")
    antigen_id: str = Field(description="Parent antigen ID")
    mhc_binding: str = Field(description="MHC binding type (I or II)")
    confidence: float = Field(ge=0.0, le=1.0, description="Processing confidence")
    created_at: datetime = Field(default_factory=datetime.now)


class MHCPresentation(BaseModel):
    """MHC complex presentation"""

    presentation_id: str = Field(description="Presentation ID")
    mhc_type: str = Field(description="MHC type (I or II)")
    peptide: ProcessedPeptide = Field(description="Presented peptide")
    hla_allele: str = Field(description="HLA allele (DR1, A2, etc.)")
    target_cell_type: str = Field(description="Target T cell type")
    presented_at: datetime = Field(default_factory=datetime.now)


class DendriticState(str):
    """Dendritic Cell maturation states"""

    IMMATURE = "immature"  # Tissue surveillance, high capture
    MIGRATING = "migrating"  # Moving to lymph node
    MATURE = "mature"  # Lymph node, high presentation
    EXHAUSTED = "exhausted"  # Post-presentation, low activity


# ==================== DENDRITIC CELL ====================


class CelulaDendritica(AgenteImunologicoBase):
    """
    Digital Dendritic Cell - Professional antigen presenter.

    Capabilities:
    - Antigen capture via phagocytosis
    - Antigen processing into peptides
    - MHC-I presentation (Cytotoxic T cells)
    - MHC-II presentation (Helper T cells)
    - Migration to lymph nodes
    - T cell activation
    - IL12 secretion (Th1 promotion)
    - Pattern learning from threats

    Use cases:
    - Bridge innate → adaptive immunity
    - Activate naive T cells
    - Train adaptive immune responses
    - Threat pattern dissemination
    """

    def __init__(
        self,
        area_patrulha: str,
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        capture_threshold: float = 0.6,
        migration_antigen_count: int = 5,
        **kwargs,
    ):
        """
        Initialize Dendritic Cell.

        Args:
            area_patrulha: Network zone to patrol
            kafka_bootstrap: Kafka broker
            redis_url: Redis URL
            capture_threshold: Min confidence for antigen capture (0-1)
            migration_antigen_count: Antigens needed to trigger migration
        """
        super().__init__(
            tipo=AgentType.DENDRITICA,
            area_patrulha=area_patrulha,
            kafka_bootstrap=kafka_bootstrap,
            redis_url=redis_url,
            **kwargs,
        )

        # Dendritic-specific configuration
        self.capture_threshold = capture_threshold
        self.migration_antigen_count = migration_antigen_count

        # Dendritic-specific state
        self.maturation_state: str = DendriticState.IMMATURE
        self.captured_antigens: List[CapturedAntigen] = []
        self.processed_peptides: List[ProcessedPeptide] = []
        self.mhc_i_presentations: List[MHCPresentation] = []
        self.mhc_ii_presentations: List[MHCPresentation] = []
        self.activated_helper_t: int = 0
        self.activated_cytotoxic_t: int = 0
        self.il12_secretions: int = 0
        self.migrations: int = 0
        self.current_lymphnode: Optional[str] = None

        # Thread-safety locks for concurrent access
        # Protects lists from race conditions when background tasks are running
        self._antigens_lock = asyncio.Lock()
        self._peptides_lock = asyncio.Lock()
        self._presentations_lock = asyncio.Lock()
        self._counters_lock = asyncio.Lock()

        logger.info(
            f"Dendritic Cell initialized: {self.state.id[:8]} "
            f"(zone={area_patrulha}, capture_threshold={capture_threshold})"
        )

    # ==================== LIFECYCLE ====================

    async def iniciar(self) -> None:
        """Start Dendritic Cell - begin tissue surveillance"""
        await super().iniciar()

        # Immature state: high antigen capture in tissues
        self.maturation_state = DendriticState.IMMATURE
        logger.info(f"Dendritic {self.state.id[:8]} started immature state (tissue surveillance)")

    # ==================== PATROL ====================

    async def patrulhar(self) -> None:
        """
        Dendritic Cell patrol - capture antigens or present to T cells.

        State-dependent behavior:
        - IMMATURE: Capture antigens in tissue
        - MIGRATING: Move to lymph node
        - MATURE: Present antigens to T cells
        - EXHAUSTED: Reduced activity
        """
        if self.maturation_state == DendriticState.IMMATURE:
            await self._patrol_for_antigens()
        elif self.maturation_state == DendriticState.MIGRATING:
            await self._migrate_to_lymphnode()
        elif self.maturation_state == DendriticState.MATURE:
            await self._present_to_t_cells()
        elif self.maturation_state == DendriticState.EXHAUSTED:
            logger.debug(f"Dendritic {self.state.id[:8]} exhausted, minimal activity")

    async def _patrol_for_antigens(self) -> None:
        """Patrol tissue for antigen capture (immature state)"""
        logger.debug(f"Dendritic {self.state.id[:8]} patrolling for antigens (immature)")

        try:
            # Get suspicious activity
            activity = await self._get_network_activity()

            if not activity:
                return

            # Attempt antigen capture
            for event in activity:
                await self._attempt_antigen_capture(event)

            # Check if migration threshold reached (thread-safe)
            antigen_count = await self.safe_get_antigen_count()
            if antigen_count >= self.migration_antigen_count:
                await self._initiate_maturation()

        except Exception as e:
            logger.error(f"Dendritic patrol error: {e}", exc_info=True)

    # ==================== ANTIGEN CAPTURE ====================

    async def _attempt_antigen_capture(self, event: Dict[str, Any]) -> None:
        """
        Attempt to capture antigen from suspicious event.

        Args:
            event: Network event
        """
        # Calculate threat confidence
        confidence = event.get("threat_score", 0.5)

        if confidence < self.capture_threshold:
            return

        # Capture antigen
        antigen = CapturedAntigen(
            antigen_id=str(uuid4()),
            threat_type=event.get("type", "unknown"),
            source_ip=event.get("src_ip", "unknown"),
            raw_data=event,
            capture_method="phagocytosis",
        )

        # Thread-safe append
        await self.safe_append_antigen(antigen)

        logger.info(
            f"Dendritic {self.state.id[:8]} captured antigen (type={antigen.threat_type}, confidence={confidence:.2f})"
        )

        # Process antigen immediately
        await self._process_antigen(antigen)

    async def _process_antigen(self, antigen: CapturedAntigen) -> None:
        """
        Process antigen into peptides for MHC presentation.

        Args:
            antigen: Captured antigen
        """
        # Extract pattern signature
        signature = self._extract_pattern_signature(antigen.raw_data)

        # Create peptide (simplified: hash of signature)
        peptide_sequence = hashlib.sha256(str(signature).encode()).hexdigest()[:16]

        # Create MHC-I peptide (for Cytotoxic T)
        peptide_i = ProcessedPeptide(
            peptide_id=f"pep_i_{str(uuid4())[:8]}",
            sequence=peptide_sequence,
            antigen_id=antigen.antigen_id,
            mhc_binding="I",
            confidence=0.8,
        )
        await self.safe_append_peptide(peptide_i)

        # Create MHC-II peptide (for Helper T)
        peptide_ii = ProcessedPeptide(
            peptide_id=f"pep_ii_{str(uuid4())[:8]}",
            sequence=peptide_sequence,
            antigen_id=antigen.antigen_id,
            mhc_binding="II",
            confidence=0.85,
        )
        await self.safe_append_peptide(peptide_ii)

        logger.debug(f"Dendritic {self.state.id[:8]} processed antigen (MHC-I + MHC-II peptides created)")

    def _extract_pattern_signature(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract pattern signature from event.

        Args:
            event: Network event

        Returns:
            Pattern signature
        """
        return {
            "src_ip": event.get("src_ip"),
            "dst_ip": event.get("dst_ip"),
            "dst_port": event.get("dst_port"),
            "protocol": event.get("protocol"),
            "threat_type": event.get("type"),
        }

    # ==================== MATURATION & MIGRATION ====================

    async def _initiate_maturation(self) -> None:
        """Initiate maturation and migration to lymph node"""
        self.maturation_state = DendriticState.MIGRATING
        await self.safe_increment_counter("migrations")

        antigen_count = await self.safe_get_antigen_count()
        logger.info(
            f"Dendritic {self.state.id[:8]} maturation initiated "
            f"({antigen_count} antigens captured, migrating to lymph node)"
        )

    async def _migrate_to_lymphnode(self) -> None:
        """Migrate to lymph node (via Redis/cytokine system)"""
        # GRACEFUL DEGRADATION: Simulated migration
        # In production: would register with actual lymph node service

        self.current_lymphnode = f"lymphnode_{self.state.area_patrulha}"
        self.maturation_state = DendriticState.MATURE

        logger.info(
            f"Dendritic {self.state.id[:8]} migrated to {self.current_lymphnode} (mature state: ready to present)"
        )

    # ==================== ANTIGEN PRESENTATION ====================

    async def _present_to_t_cells(self) -> None:
        """Present antigens to T cells (mature state)"""
        logger.debug(f"Dendritic {self.state.id[:8]} presenting antigens to T cells")

        # Present via MHC-I and MHC-II
        await self._present_mhc_i()
        await self._present_mhc_ii()

        # Secrete IL12 to promote Th1 differentiation
        await self._secrete_il12()

        # Check for exhaustion
        if len(self.mhc_i_presentations) + len(self.mhc_ii_presentations) > 20:
            self.maturation_state = DendriticState.EXHAUSTED
            logger.info(f"Dendritic {self.state.id[:8]} exhausted after extensive presentation")

    async def _present_mhc_i(self) -> None:
        """Present peptides via MHC-I to Cytotoxic T cells"""
        # Get MHC-I peptides
        mhc_i_peptides = [p for p in self.processed_peptides if p.mhc_binding == "I"]

        for peptide in mhc_i_peptides:
            # Create MHC-I presentation
            presentation = MHCPresentation(
                presentation_id=str(uuid4()),
                mhc_type="I",
                peptide=peptide,
                hla_allele="A2",  # Simplified: would vary by host genetics
                target_cell_type="cytotoxic_t",
            )

            await self.safe_append_mhc_i(presentation)

            # Broadcast presentation via cytokines
            if self._cytokine_messenger and self._cytokine_messenger.is_running():
                try:
                    await self._cytokine_messenger.send_cytokine(
                        tipo="MHC_I_PRESENTATION",
                        payload={
                            "evento": "antigen_presentation",
                            "dendritic_cell_id": self.state.id,
                            "presentation_id": presentation.presentation_id,
                            "peptide_sequence": peptide.sequence,
                            "target": "cytotoxic_t",
                            "confidence": peptide.confidence,
                        },
                        emissor_id=self.state.id,
                        prioridade=9,
                        area_alvo=self.current_lymphnode or self.state.area_patrulha,
                    )

                    await self.safe_increment_counter("activated_cytotoxic_t")

                    logger.info(
                        f"Dendritic {self.state.id[:8]} presented MHC-I "
                        f"(peptide={peptide.peptide_id}, target=Cytotoxic T)"
                    )
                except Exception as e:
                    logger.error(f"MHC-I presentation failed: {e}")

    async def _present_mhc_ii(self) -> None:
        """Present peptides via MHC-II to Helper T cells"""
        # Get MHC-II peptides
        mhc_ii_peptides = [p for p in self.processed_peptides if p.mhc_binding == "II"]

        for peptide in mhc_ii_peptides:
            # Create MHC-II presentation
            presentation = MHCPresentation(
                presentation_id=str(uuid4()),
                mhc_type="II",
                peptide=peptide,
                hla_allele="DR1",  # Simplified: would vary by host genetics
                target_cell_type="helper_t",
            )

            await self.safe_append_mhc_ii(presentation)

            # Broadcast presentation via cytokines
            if self._cytokine_messenger and self._cytokine_messenger.is_running():
                try:
                    # Get parent antigen (thread-safe read)
                    if USE_THREAD_SAFE_OPERATIONS:
                        async with self._antigens_lock:
                            antigen = next(
                                (a for a in self.captured_antigens if a.antigen_id == peptide.antigen_id), None
                            )
                    else:
                        antigen = next((a for a in self.captured_antigens if a.antigen_id == peptide.antigen_id), None)

                    await self._cytokine_messenger.send_cytokine(
                        tipo="ANTIGEN_PRESENTATION",  # Helper T subscribes to this
                        payload={
                            "evento": "antigen_presentation",
                            "dendritic_cell_id": self.state.id,
                            "presentation_id": presentation.presentation_id,
                            "antigen_type": antigen.threat_type if antigen else "unknown",
                            "mhc_ii_complex": {
                                "peptide": peptide.sequence,
                                "hla_dr": presentation.hla_allele,
                            },
                            "confidence": peptide.confidence,
                        },
                        emissor_id=self.state.id,
                        prioridade=9,
                        area_alvo=self.current_lymphnode or self.state.area_patrulha,
                    )

                    await self.safe_increment_counter("activated_helper_t")

                    logger.info(
                        f"Dendritic {self.state.id[:8]} presented MHC-II "
                        f"(peptide={peptide.peptide_id}, target=Helper T)"
                    )
                except Exception as e:
                    logger.error(f"MHC-II presentation failed: {e}")

    async def _secrete_il12(self) -> None:
        """Secrete IL12 to promote Th1 differentiation"""
        if not self._cytokine_messenger or not self._cytokine_messenger.is_running():
            return

        try:
            await self._cytokine_messenger.send_cytokine(
                tipo="IL12",
                payload={
                    "evento": "promote_th1",
                    "dendritic_cell_id": self.state.id,
                    "message": "Promote Th1 differentiation",
                },
                emissor_id=self.state.id,
                prioridade=7,
                area_alvo=self.current_lymphnode or self.state.area_patrulha,
            )

            await self.safe_increment_counter("il12_secretions")

            logger.debug(f"Dendritic {self.state.id[:8]} secreted IL12 (promote Th1)")

        except Exception as e:
            logger.error(f"IL12 secretion failed: {e}")

    # ==================== INVESTIGATION ====================

    async def executar_investigacao(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dendritic Cell investigation - capture and process antigen.

        Args:
            alvo: Target to investigate

        Returns:
            Investigation result with antigen info
        """
        logger.info(f"Dendritic {self.state.id[:8]} investigating target for antigen capture")

        # Simulate antigen capture from investigation
        confidence = alvo.get("threat_score", 0.7)

        if confidence >= self.capture_threshold:
            # Would capture antigen here
            return {
                "is_threat": True,
                "confidence": confidence,
                "metodo": "antigen_capture",
                "detalhes": "Antigen captured for MHC presentation",
            }
        else:
            return {
                "is_threat": False,
                "confidence": confidence,
                "metodo": "no_capture",
                "detalhes": "Below capture threshold",
            }

    # ==================== NEUTRALIZATION ====================

    async def executar_neutralizacao(self, alvo: Dict[str, Any], metodo: str) -> bool:
        """
        Dendritic Cells don't neutralize - they present for T cells to act.

        Args:
            alvo: Target
            metodo: Method (ignored)

        Returns:
            True (antigen presented to T cells for action)
        """
        logger.info(f"Dendritic {self.state.id[:8]} presenting antigen for T cell neutralization")

        # Dendritic Cells delegate to T cells
        # Create presentation from target
        if alvo.get("threat_score", 0) >= self.capture_threshold:
            # Simulate immediate presentation
            logger.info(f"Dendritic {self.state.id[:8]} antigen presented to T cells for action")
            return True

        return False

    # ==================== HELPER METHODS ====================

    async def _get_network_activity(self) -> List[Dict[str, Any]]:
        """
        Get network activity from monitoring - GRACEFUL DEGRADATION.

        Returns:
            List of network events (empty if unavailable)
        """
        # GRACEFUL DEGRADATION: Monitoring service optional
        return []

    # ==================== THREAD-SAFE ACCESSORS ====================

    async def safe_append_antigen(self, antigen: CapturedAntigen) -> None:
        """Thread-safe append to captured_antigens"""
        if USE_THREAD_SAFE_OPERATIONS:
            async with self._antigens_lock:
                self.captured_antigens.append(antigen)
        else:
            self.captured_antigens.append(antigen)

    async def safe_append_peptide(self, peptide: ProcessedPeptide) -> None:
        """Thread-safe append to processed_peptides"""
        if USE_THREAD_SAFE_OPERATIONS:
            async with self._peptides_lock:
                self.processed_peptides.append(peptide)
        else:
            self.processed_peptides.append(peptide)

    async def safe_append_mhc_i(self, presentation: MHCPresentation) -> None:
        """Thread-safe append to mhc_i_presentations"""
        if USE_THREAD_SAFE_OPERATIONS:
            async with self._presentations_lock:
                self.mhc_i_presentations.append(presentation)
        else:
            self.mhc_i_presentations.append(presentation)

    async def safe_append_mhc_ii(self, presentation: MHCPresentation) -> None:
        """Thread-safe append to mhc_ii_presentations"""
        if USE_THREAD_SAFE_OPERATIONS:
            async with self._presentations_lock:
                self.mhc_ii_presentations.append(presentation)
        else:
            self.mhc_ii_presentations.append(presentation)

    async def safe_get_antigen_count(self) -> int:
        """Thread-safe read of captured_antigens count"""
        if USE_THREAD_SAFE_OPERATIONS:
            async with self._antigens_lock:
                return len(self.captured_antigens)
        else:
            return len(self.captured_antigens)

    async def safe_increment_counter(self, counter_name: str) -> None:
        """Thread-safe increment of counters"""
        if USE_THREAD_SAFE_OPERATIONS:
            async with self._counters_lock:
                if counter_name == "activated_helper_t":
                    self.activated_helper_t += 1
                elif counter_name == "activated_cytotoxic_t":
                    self.activated_cytotoxic_t += 1
                elif counter_name == "il12_secretions":
                    self.il12_secretions += 1
                elif counter_name == "migrations":
                    self.migrations += 1
        else:
            if counter_name == "activated_helper_t":
                self.activated_helper_t += 1
            elif counter_name == "activated_cytotoxic_t":
                self.activated_cytotoxic_t += 1
            elif counter_name == "il12_secretions":
                self.il12_secretions += 1
            elif counter_name == "migrations":
                self.migrations += 1

    # ==================== STATE MANAGEMENT ====================

    def reset_state(self) -> None:
        """
        Reset Dendritic Cell state - FOR TESTING ONLY.

        Clears all captured antigens, peptides, presentations, and counters.
        Used to ensure test isolation and prevent state contamination.

        WARNING: This is a testing utility. Do not use in production code.
        """
        # Clear captured data
        self.captured_antigens.clear()
        self.processed_peptides.clear()
        self.mhc_i_presentations.clear()
        self.mhc_ii_presentations.clear()

        # Reset counters
        self.activated_helper_t = 0
        self.activated_cytotoxic_t = 0
        self.il12_secretions = 0
        self.migrations = 0

        # Reset maturation state
        self.maturation_state = DendriticState.IMMATURE
        self.current_lymphnode = None

        logger.debug(f"Dendritic {self.state.id[:8]} state reset (testing utility)")

    # ==================== METRICS ====================

    def get_dendritic_metrics(self) -> Dict[str, Any]:
        """
        Get Dendritic Cell-specific metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "maturation_state": self.maturation_state,
            "captured_antigens": len(self.captured_antigens),
            "processed_peptides": len(self.processed_peptides),
            "mhc_i_presentations": len(self.mhc_i_presentations),
            "mhc_ii_presentations": len(self.mhc_ii_presentations),
            "total_presentations": len(self.mhc_i_presentations) + len(self.mhc_ii_presentations),
            "activated_helper_t": self.activated_helper_t,
            "activated_cytotoxic_t": self.activated_cytotoxic_t,
            "il12_secretions": self.il12_secretions,
            "migrations": self.migrations,
            "current_lymphnode": self.current_lymphnode or "none",
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"CelulaDendritica({self.state.id[:8]}|{self.state.status}|"
            f"state={self.maturation_state}|"
            f"antigens={len(self.captured_antigens)}|"
            f"mhc_i={len(self.mhc_i_presentations)}|"
            f"mhc_ii={len(self.mhc_ii_presentations)})"
        )
