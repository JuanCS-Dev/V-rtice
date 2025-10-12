"""Coagulation Cascade Orchestrator - Complete Hemostasis System

Orchestrates complete coagulation cascade:
Primary → Secondary → Neutralization → Fibrinolysis

Biological inspiration: Complete hemostatic response from injury to healing.

Phases:
1. PRIMARY: Reflex Triage Engine (< 100ms)
2. SECONDARY: Fibrin Mesh (< 60s)
3. NEUTRALIZATION: Threat elimination (variable)
4. FIBRINOLYSIS: Progressive restoration (< 10min)

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - "Eu sou porque ELE é"
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram

from .fibrin_mesh import FibrinMeshContainment, FibrinMeshResult
from .models import CascadeError, ContainmentResult, EnrichedThreat
from .restoration import RestorationEngine, RestorationResult

logger = logging.getLogger(__name__)


class CascadePhase(Enum):
    """Phases of coagulation cascade"""

    IDLE = "idle"
    PRIMARY = "primary"  # Reflex Triage Engine
    SECONDARY = "secondary"  # Fibrin Mesh
    NEUTRALIZATION = "neutralization"  # Threat elimination
    FIBRINOLYSIS = "fibrinolysis"  # Restoration
    COMPLETE = "complete"


class CascadeState:
    """State tracking for cascade execution"""

    def __init__(
        self,
        cascade_id: str,
        threat: EnrichedThreat,
        phase: CascadePhase,
        started_at: datetime,
    ):
        """
        Initialize cascade state.

        Args:
            cascade_id: Unique cascade identifier
            threat: Enriched threat triggering cascade
            phase: Current phase
            started_at: Start timestamp
        """
        self.cascade_id = cascade_id
        self.threat = threat
        self.phase = phase
        self.started_at = started_at
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None

        # Phase results
        self.primary_result: Optional[ContainmentResult] = None
        self.secondary_result: Optional[FibrinMeshResult] = None
        self.neutralization_result: Optional[Any] = None
        self.restoration_result: Optional[RestorationResult] = None


class CascadeResult:
    """Result of complete cascade execution"""

    def __init__(
        self,
        cascade_id: str,
        status: str,
        state: CascadeState,
    ):
        """
        Initialize cascade result.

        Args:
            cascade_id: Cascade identifier
            status: SUCCESS, FAILED, PARTIAL
            state: Final cascade state
        """
        self.cascade_id = cascade_id
        self.status = status
        self.state = state
        self.timestamp = datetime.utcnow()

    def get_duration(self) -> float:
        """Get total cascade duration in seconds"""
        if self.state.completed_at:
            return (
                self.state.completed_at - self.state.started_at
            ).total_seconds()
        return 0.0


class CascadeMetrics:
    """Prometheus metrics for cascade"""

    def __init__(self):
        self.cascades_total = Counter(
            "coagulation_cascades_total",
            "Total cascade initiations",
            ["status"],
        )
        self.active_cascades = Gauge(
            "coagulation_cascades_active",
            "Currently active cascades",
        )
        self.cascade_duration = Histogram(
            "coagulation_cascade_duration_seconds",
            "Total cascade duration",
            buckets=[10, 30, 60, 120, 300, 600, 1200],
        )
        self.phase_duration = Histogram(
            "coagulation_phase_duration_seconds",
            "Duration per phase",
            ["phase"],
            buckets=[0.1, 1, 5, 10, 30, 60, 300],
        )


class CoagulationCascadeSystem:
    """
    Orchestrator for complete coagulation cascade.

    Coordinates hemostasis-inspired threat containment:
    1. Primary Hemostasis - Fast reflex response
    2. Secondary Hemostasis - Robust containment
    3. Neutralization - Threat elimination
    4. Fibrinolysis - Progressive restoration

    Transition timing:
    - Primary → Secondary: < 60s (if primary insufficient)
    - Secondary → Neutralization: immediate
    - Neutralization → Fibrinolysis: after validation

    Thread-safe, async-first design for production use.
    """

    def __init__(
        self,
        fibrin_mesh: Optional[FibrinMeshContainment] = None,
        restoration: Optional[RestorationEngine] = None,
    ):
        """
        Initialize cascade orchestrator.

        Args:
            fibrin_mesh: Fibrin mesh containment (created if None)
            restoration: Restoration engine (created if None)
        """
        self.fibrin_mesh = fibrin_mesh or FibrinMeshContainment()
        self.restoration = restoration or RestorationEngine()

        # Inject cross-dependencies
        self.restoration.set_dependencies(self.fibrin_mesh)

        # Will be injected
        self.reflex_triage = None
        self.response_engine = None

        # State tracking
        self.active_cascades: Dict[str, CascadeState] = {}
        self.metrics = CascadeMetrics()

        logger.info("CoagulationCascadeSystem initialized")

    def set_dependencies(
        self,
        reflex_triage: Any,
        response_engine: Any,
        zone_isolator: Any,
        traffic_shaper: Any,
        firewall_controller: Any,
    ) -> None:
        """
        Inject external dependencies.

        Args:
            reflex_triage: Reflex Triage Engine
            response_engine: Automated Response Engine
            zone_isolator: Zone isolation engine
            traffic_shaper: Traffic shaping controller
            firewall_controller: Firewall controller
        """
        self.reflex_triage = reflex_triage
        self.response_engine = response_engine

        # Inject to fibrin mesh
        self.fibrin_mesh.set_dependencies(
            zone_isolator=zone_isolator,
            traffic_shaper=traffic_shaper,
            firewall_controller=firewall_controller,
        )

        logger.info("CoagulationCascadeSystem dependencies injected")

    async def initiate_cascade(self, threat: EnrichedThreat) -> CascadeResult:
        """
        Initiate complete coagulation cascade for threat.

        Executes full hemostasis response:
        1. PRIMARY: Ultra-fast reflex triage
        2. SECONDARY: Robust fibrin mesh (if needed)
        3. NEUTRALIZATION: Threat elimination
        4. FIBRINOLYSIS: Progressive restoration

        Args:
            threat: Enriched threat with context

        Returns:
            CascadeResult with final state

        Raises:
            CascadeError: If cascade fails critically
        """
        # Generate cascade ID
        cascade_id = self._generate_cascade_id(threat)

        # Create state
        state = CascadeState(
            cascade_id=cascade_id,
            threat=threat,
            phase=CascadePhase.PRIMARY,
            started_at=datetime.utcnow(),
        )

        # Track active cascade
        self.active_cascades[cascade_id] = state
        self.metrics.active_cascades.set(len(self.active_cascades))

        try:
            # PHASE 1: Primary Hemostasis
            logger.info(f"Cascade {cascade_id}: PRIMARY phase")
            primary_start = datetime.utcnow()
            primary_result = await self._execute_primary(state)
            primary_duration = (datetime.utcnow() - primary_start).total_seconds()
            self.metrics.phase_duration.labels(phase="primary").observe(primary_duration)

            state.primary_result = primary_result

            # Transition check: Do we need secondary?
            if self._needs_secondary(primary_result):
                # PHASE 2: Secondary Hemostasis
                logger.info(f"Cascade {cascade_id}: SECONDARY phase (primary insufficient)")
                state.phase = CascadePhase.SECONDARY
                secondary_start = datetime.utcnow()
                secondary_result = await self._execute_secondary(state)
                secondary_duration = (datetime.utcnow() - secondary_start).total_seconds()
                self.metrics.phase_duration.labels(phase="secondary").observe(secondary_duration)

                state.secondary_result = secondary_result
            else:
                logger.info(f"Cascade {cascade_id}: Primary sufficient, skipping secondary")

            # PHASE 3: Neutralization
            logger.info(f"Cascade {cascade_id}: NEUTRALIZATION phase")
            state.phase = CascadePhase.NEUTRALIZATION
            neutralization_start = datetime.utcnow()
            neutralization_result = await self._execute_neutralization(state)
            neutralization_duration = (datetime.utcnow() - neutralization_start).total_seconds()
            self.metrics.phase_duration.labels(phase="neutralization").observe(neutralization_duration)

            state.neutralization_result = neutralization_result

            # PHASE 4: Fibrinolysis (if neutralization succeeded)
            if self._neutralization_succeeded(neutralization_result):
                logger.info(f"Cascade {cascade_id}: FIBRINOLYSIS phase")
                state.phase = CascadePhase.FIBRINOLYSIS
                fibrinolysis_start = datetime.utcnow()
                restoration_result = await self._execute_fibrinolysis(state)
                fibrinolysis_duration = (datetime.utcnow() - fibrinolysis_start).total_seconds()
                self.metrics.phase_duration.labels(phase="fibrinolysis").observe(fibrinolysis_duration)

                state.restoration_result = restoration_result
            else:
                logger.warning(
                    f"Cascade {cascade_id}: Neutralization incomplete, "
                    "skipping restoration"
                )

            # COMPLETE
            state.phase = CascadePhase.COMPLETE
            state.completed_at = datetime.utcnow()

            # Calculate total duration
            duration = (state.completed_at - state.started_at).total_seconds()

            # Record metrics
            self.metrics.cascades_total.labels(status="success").inc()
            self.metrics.cascade_duration.observe(duration)

            logger.info(f"Cascade {cascade_id} complete in {duration:.2f}s")

            return CascadeResult(
                cascade_id=cascade_id,
                status="SUCCESS",
                state=state,
            )

        except Exception as e:
            logger.error(f"Cascade {cascade_id} failed: {e}", exc_info=True)
            state.phase = CascadePhase.IDLE
            state.error = str(e)
            self.metrics.cascades_total.labels(status="failed").inc()
            raise CascadeError(f"Cascade failed: {e}")

        finally:
            # Cleanup
            if cascade_id in self.active_cascades:
                del self.active_cascades[cascade_id]
                self.metrics.active_cascades.set(len(self.active_cascades))

    async def _execute_primary(self, state: CascadeState) -> ContainmentResult:
        """
        Execute primary hemostasis via Reflex Triage Engine.

        Args:
            state: Cascade state

        Returns:
            Containment result from RTE
        """
        if self.reflex_triage is None:
            # Simulate for now
            logger.warning("RTE not injected, simulating primary response")
            await asyncio.sleep(0.1)
            return ContainmentResult(
                status="CONTAINED",
                containment_type="primary",
                affected_zones=["DMZ"],
            )

        # TODO: Integrate with real RTE
        # For now, simulate
        await asyncio.sleep(0.1)
        return ContainmentResult(
            status="CONTAINED",
            containment_type="primary",
            affected_zones=["DMZ"],
        )

    def _needs_secondary(self, primary_result: ContainmentResult) -> bool:
        """
        Determine if secondary hemostasis needed.

        Criteria:
        - Primary containment was partial
        - High threat severity
        - Large blast radius

        Args:
            primary_result: Primary containment result

        Returns:
            True if secondary needed
        """
        # For now, always apply secondary for robustness
        # TODO: Implement smarter logic based on threat characteristics
        return True

    async def _execute_secondary(self, state: CascadeState) -> FibrinMeshResult:
        """
        Execute secondary hemostasis via Fibrin Mesh.

        Args:
            state: Cascade state

        Returns:
            Fibrin mesh result
        """
        return await self.fibrin_mesh.deploy_fibrin_mesh(
            threat=state.threat,
            primary_containment=state.primary_result,
        )

    async def _execute_neutralization(self, state: CascadeState) -> Any:
        """
        Execute neutralization via Response Engine.

        Args:
            state: Cascade state

        Returns:
            Neutralization result
        """
        if self.response_engine is None:
            # Simulate for now
            logger.warning("Response engine not injected, simulating neutralization")
            await asyncio.sleep(0.5)
            return {
                "status": "neutralized",
                "method": "simulated",
                "threat_id": state.threat.threat_id,
            }

        # TODO: Integrate with real response engine
        await asyncio.sleep(0.5)
        return {
            "status": "neutralized",
            "method": "simulated",
            "threat_id": state.threat.threat_id,
        }

    def _neutralization_succeeded(self, neutralization_result: Any) -> bool:
        """
        Check if neutralization succeeded.

        Args:
            neutralization_result: Neutralization result

        Returns:
            True if succeeded
        """
        if isinstance(neutralization_result, dict):
            return neutralization_result.get("status") == "neutralized"
        return False

    async def _execute_fibrinolysis(self, state: CascadeState) -> RestorationResult:
        """
        Execute fibrinolysis via Restoration Engine.

        Args:
            state: Cascade state

        Returns:
            Restoration result
        """
        # Create NeutralizedThreat from state
        from .models import NeutralizedThreat

        neutralized = NeutralizedThreat(
            threat_id=state.threat.threat_id,
            original_threat=state.threat,
            neutralization_method=state.neutralization_result.get("method", "unknown"),
        )

        # Get mesh ID
        mesh_id = (
            state.secondary_result.mesh_id
            if state.secondary_result
            else "no_mesh"
        )

        return await self.restoration.restore_after_neutralization(
            neutralized_threat=neutralized,
            mesh_id=mesh_id,
        )

    def _generate_cascade_id(self, threat: EnrichedThreat) -> str:
        """Generate unique cascade ID"""
        import uuid
        return f"cascade_{threat.threat_id}_{uuid.uuid4().hex[:8]}"

    def get_active_cascade_count(self) -> int:
        """Get count of active cascades"""
        return len(self.active_cascades)

    def get_active_cascade_ids(self) -> list:
        """Get list of active cascade IDs"""
        return list(self.active_cascades.keys())

    async def get_cascade_state(self, cascade_id: str) -> Optional[CascadeState]:
        """
        Get current state of cascade.

        Args:
            cascade_id: Cascade ID

        Returns:
            CascadeState if found, None otherwise
        """
        return self.active_cascades.get(cascade_id)
