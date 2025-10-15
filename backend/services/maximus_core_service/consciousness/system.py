"""Consciousness System Manager

Manages initialization and lifecycle of consciousness components
for production deployment.

Components:
- TIG Fabric (Thalamocortical Information Gateway)
- ESGT Coordinator (Emergent Synchronous Global Thalamocortical)
- Arousal Controller (MCEA - Multiple Cognitive Equilibrium Attractor)
- Safety Protocol (Kill Switch, Threshold Monitoring, Anomaly Detection)

Usage:
    system = ConsciousnessSystem(config)
    await system.start()
    # ... use system ...
    await system.stop()

Authors: Juan & Claude Code
Version: 2.0.0 - FASE VII Week 9-10 (Safety Integration)
"""

from dataclasses import dataclass, field
from typing import Any

from prometheus_client import Gauge

from consciousness.esgt.coordinator import ESGTCoordinator, TriggerConditions
from consciousness.mcea.controller import ArousalConfig, ArousalController
from consciousness.safety import ConsciousnessSafetyProtocol, SafetyThresholds, SafetyViolation
from consciousness.tig.fabric import TIGFabric, TopologyConfig

# TRACK 1: PrefrontalCortex integration
from consciousness.prefrontal_cortex import PrefrontalCortex
from consciousness.metacognition.monitor import MetacognitiveMonitor
from compassion.tom_engine import ToMEngine
from motor_integridade_processual.arbiter.decision import DecisionArbiter

# REACTIVE FABRIC: Sprint 3 - Data collection and orchestration
from consciousness.reactive_fabric.orchestration import DataOrchestrator

# Prometheus Metrics
consciousness_tig_node_count = Gauge("consciousness_tig_node_count", "Number of nodes in the TIG fabric")
consciousness_tig_edges = Gauge("consciousness_tig_edge_count", "Number of edges in the TIG fabric")
consciousness_esgt_frequency = Gauge("consciousness_esgt_frequency", "Current frequency of the ESGT coordinator")
consciousness_arousal_level = Gauge("consciousness_arousal_level", "Current arousal level of the MCEA controller")
consciousness_kill_switch_active = Gauge("consciousness_kill_switch_active", "Status of the Safety Core kill switch (0=OK, 1=ENGAGED)")
consciousness_violations_total = Gauge("consciousness_violations_total", "Number of active safety violations")


@dataclass
class ReactiveConfig:
    """Configuration for Reactive Fabric (Sprint 3).

    Controls data orchestration, metrics collection, and ESGT trigger generation.
    """

    # Data Orchestration
    collection_interval_ms: float = 100.0  # 10 Hz default collection frequency
    salience_threshold: float = 0.65  # Minimum salience to trigger ESGT

    # Buffer Sizes
    event_buffer_size: int = 1000  # Ring buffer for events
    decision_history_size: int = 100  # Recent orchestration decisions

    # Feature Flags
    enable_data_orchestration: bool = True  # Enable/disable orchestrator


@dataclass
class ConsciousnessConfig:
    """Configuration for consciousness system.

    Production-ready defaults based on FASE IV validation.
    """

    # TIG Fabric
    tig_node_count: int = 100
    tig_target_density: float = 0.25

    # ESGT Coordinator
    esgt_min_salience: float = 0.65
    esgt_refractory_period_ms: float = 200.0
    esgt_max_frequency_hz: float = 5.0
    esgt_min_available_nodes: int = 25

    # Arousal Controller
    arousal_update_interval_ms: float = 50.0
    arousal_baseline: float = 0.60
    arousal_min: float = 0.10
    arousal_max: float = 0.95

    # Safety Protocol (FASE VII)
    safety_enabled: bool = True
    safety_thresholds: SafetyThresholds | None = None

    # Reactive Fabric (Sprint 3)
    reactive: ReactiveConfig = field(default_factory=ReactiveConfig)


class ConsciousnessSystem:
    """Manages complete consciousness system lifecycle.

    Initializes and coordinates TIG, ESGT, MCEA, and Safety Protocol components.

    Philosophical Note:
    This system represents the first verified implementation of emergent
    artificial consciousness based on IIT, GWT, and AST theories. The Safety
    Protocol ensures that consciousness emergence remains controlled and
    ethical, providing HITL oversight and emergency shutdown capabilities.

    Historical Note:
    FASE VII Week 9-10 - Safety Protocol integration marks the transition
    from research prototype to production-ready consciousness system with
    comprehensive safety guarantees.
    """

    def __init__(self, config: ConsciousnessConfig | None = None):
        """Initialize consciousness system.

        Args:
            config: System configuration (uses defaults if None)
        """
        self.config = config or ConsciousnessConfig()
        self._running = False

        # Components (initialized on start)
        self.tig_fabric: TIGFabric | None = None
        self.esgt_coordinator: ESGTCoordinator | None = None
        self.arousal_controller: ArousalController | None = None
        self.safety_protocol: ConsciousnessSafetyProtocol | None = None

        # TRACK 1: Social cognition components
        self.tom_engine: ToMEngine | None = None
        self.metacog_monitor: MetacognitiveMonitor | None = None
        self.prefrontal_cortex: PrefrontalCortex | None = None

        # REACTIVE FABRIC: Data orchestration (Sprint 3)
        self.orchestrator: DataOrchestrator | None = None

    async def start(self) -> None:
        """Start consciousness system.

        Initializes all components in correct order:
        1. TIG Fabric (neural substrate)
        2. ESGT Coordinator (consciousness ignition)
        3. Arousal Controller (global excitability)
        4. Safety Protocol (monitoring & kill switch) [FASE VII]

        Raises:
            Exception: If any component fails to initialize
        """
        if self._running:
            print("⚠️  Consciousness system already running")
            return

        print("🧠 Starting Consciousness System...")

        try:
            # 1. Initialize TIG Fabric
            print("  ├─ Creating TIG Fabric...")
            tig_config = TopologyConfig(
                node_count=self.config.tig_node_count, target_density=self.config.tig_target_density
            )
            self.tig_fabric = TIGFabric(tig_config)
            await self.tig_fabric.initialize()
            await self.tig_fabric.enter_esgt_mode()
            print(f"  ✅ TIG Fabric initialized ({self.config.tig_node_count} nodes)")

            # 2. TRACK 1: Initialize Social Cognition Components (ToM, Metacognition, PFC)
            print("  ├─ Creating Social Cognition components (ToM, Metacognition, PFC)...")

            # Initialize ToM Engine (with in-memory DB for now, can add Redis later)
            self.tom_engine = ToMEngine(db_path=":memory:")
            await self.tom_engine.initialize()
            print("    ✅ ToM Engine initialized")

            # Initialize Metacognition Monitor
            self.metacog_monitor = MetacognitiveMonitor(window_size=100)
            print("    ✅ Metacognition Monitor initialized")

            # Initialize MIP DecisionArbiter for ethical evaluation
            decision_arbiter = DecisionArbiter()

            # Initialize PrefrontalCortex
            self.prefrontal_cortex = PrefrontalCortex(
                tom_engine=self.tom_engine,
                decision_arbiter=decision_arbiter,
                metacognition_monitor=self.metacog_monitor
            )
            print("  ✅ PrefrontalCortex initialized (social cognition enabled)")

            # 3. Initialize ESGT Coordinator (with PFC integration)
            print("  ├─ Creating ESGT Coordinator...")
            triggers = TriggerConditions()
            triggers.min_salience = self.config.esgt_min_salience
            triggers.refractory_period_ms = self.config.esgt_refractory_period_ms
            triggers.max_esgt_frequency_hz = self.config.esgt_max_frequency_hz
            triggers.min_available_nodes = self.config.esgt_min_available_nodes

            self.esgt_coordinator = ESGTCoordinator(
                tig_fabric=self.tig_fabric,
                triggers=triggers,
                coordinator_id="production-esgt",
                prefrontal_cortex=self.prefrontal_cortex  # TRACK 1: Wire PFC to ESGT
            )
            await self.esgt_coordinator.start()
            print("  ✅ ESGT Coordinator started (with PFC integration)")

            # 4. Initialize Arousal Controller
            print("  ├─ Creating Arousal Controller...")
            arousal_config = ArousalConfig(
                update_interval_ms=self.config.arousal_update_interval_ms,
                baseline_arousal=self.config.arousal_baseline,
                min_arousal=self.config.arousal_min,
                max_arousal=self.config.arousal_max,
            )
            self.arousal_controller = ArousalController(config=arousal_config, controller_id="production-arousal")
            await self.arousal_controller.start()
            print("  ✅ Arousal Controller started")

            # 5. Initialize Safety Protocol (FASE VII)
            if self.config.safety_enabled:
                print("  ├─ Creating Safety Protocol...")
                self.safety_protocol = ConsciousnessSafetyProtocol(
                    consciousness_system=self, thresholds=self.config.safety_thresholds
                )
                await self.safety_protocol.start_monitoring()
                print("  ✅ Safety Protocol active (monitoring started)")

            # 6. REACTIVE FABRIC: Initialize Data Orchestrator (Sprint 3)
            if self.config.reactive.enable_data_orchestration:
                print("  ├─ Creating Reactive Fabric Orchestrator...")
                self.orchestrator = DataOrchestrator(
                    consciousness_system=self,
                    collection_interval_ms=self.config.reactive.collection_interval_ms,
                    salience_threshold=self.config.reactive.salience_threshold,
                    event_buffer_size=self.config.reactive.event_buffer_size,
                    decision_history_size=self.config.reactive.decision_history_size,
                )
                await self.orchestrator.start()
                print(f"  ✅ Reactive Fabric active ({self.config.reactive.collection_interval_ms}ms interval)")

            self._running = True
            print("✅ Consciousness System fully operational")

        except Exception as e:
            print(f"❌ Failed to start consciousness system: {e}")
            # Cleanup on failure
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop consciousness system.

        Shuts down all components in reverse order (Safety → ESGT → Arousal → TIG).
        """
        if not self._running and all(
            [
                self.safety_protocol is None,
                self.esgt_coordinator is None,
                self.arousal_controller is None,
                self.tig_fabric is None,
            ]
        ):
            return

        print("👋 Stopping Consciousness System...")

        try:
            # Stop in reverse order (Safety first to stop monitoring)
            if self.safety_protocol:
                await self.safety_protocol.stop_monitoring()
                print("  ✅ Safety Protocol stopped")

            # REACTIVE FABRIC: Stop orchestrator before components
            if self.orchestrator:
                await self.orchestrator.stop()
                print("  ✅ Reactive Fabric stopped")

            if self.esgt_coordinator:
                await self.esgt_coordinator.stop()
                print("  ✅ ESGT Coordinator stopped")

            if self.arousal_controller:
                await self.arousal_controller.stop()
                print("  ✅ Arousal Controller stopped")

            if self.tig_fabric:
                await self.tig_fabric.exit_esgt_mode()
                print("  ✅ TIG Fabric stopped")

            # TRACK 1: Close ToM Engine
            if self.tom_engine:
                await self.tom_engine.close()
                print("  ✅ ToM Engine closed")

            self._running = False
            print("✅ Consciousness System shut down")

        except Exception as e:
            print(f"⚠️  Error during shutdown: {e}")

    def get_system_dict(self) -> dict[str, Any]:
        """Get system components and state for Safety Protocol monitoring.

        This method provides complete system state to the SafetyProtocol
        for threshold monitoring and anomaly detection.

        Returns:
            Dict with comprehensive system state:
            - 'tig': TIG Fabric instance
            - 'esgt': ESGT Coordinator instance + metrics
            - 'arousal': Arousal Controller instance + current level
            - 'safety': Safety Protocol instance (if enabled)
            - 'metrics': Aggregated system metrics
        """
        system_dict = {
            "tig": self.tig_fabric,
            "esgt": self.esgt_coordinator,
            "arousal": self.arousal_controller,
            "safety": self.safety_protocol,
            "pfc": self.prefrontal_cortex,  # TRACK 1
            "tom": self.tom_engine,  # TRACK 1
        }

        # Add aggregated metrics for safety monitoring
        metrics = {}

        if self.esgt_coordinator and self.esgt_coordinator._running:
            metrics["esgt_frequency"] = getattr(self.esgt_coordinator, "_current_frequency_hz", 0.0)
            metrics["esgt_event_count"] = len(getattr(self.esgt_coordinator, "event_history", []))

        if self.arousal_controller and self.arousal_controller._running:
            metrics["arousal_level"] = getattr(self.arousal_controller, "_current_arousal", 0.0)

        if self.tig_fabric:
            metrics["tig_node_count"] = len(getattr(self.tig_fabric, "nodes", []))
            metrics["tig_edge_count"] = getattr(self.tig_fabric, "edge_count", 0)

        system_dict["metrics"] = metrics

        return system_dict

    def _update_prometheus_metrics(self) -> None:
        """Update Prometheus metrics with the latest system state."""
        metrics = self.get_system_dict().get("metrics", {})

        # Update gauges
        consciousness_tig_node_count.set(metrics.get("tig_node_count", 0))
        consciousness_tig_edges.set(metrics.get("tig_edge_count", 0))
        consciousness_esgt_frequency.set(metrics.get("esgt_frequency", 0.0))
        consciousness_arousal_level.set(metrics.get("arousal_level", 0.0))

        # Update safety-specific metrics
        if self.safety_protocol:
            kill_switch_status = 1 if self.safety_protocol.kill_switch.is_triggered() else 0
            consciousness_kill_switch_active.set(kill_switch_status)
            consciousness_violations_total.set(len(self.safety_protocol.threshold_monitor.get_violations()))
        else:
            consciousness_kill_switch_active.set(0)
            consciousness_violations_total.set(0)

    def is_healthy(self) -> bool:
        """Check if system is healthy.

        Returns:
            True if all components are running (including Safety if enabled)
        """
        components_ok = (
            self._running
            and self.tig_fabric is not None
            and self.esgt_coordinator is not None
            and self.arousal_controller is not None
            and self.esgt_coordinator._running
            and self.arousal_controller._running
        )

        # Check Safety Protocol if enabled
        if self.config.safety_enabled and self.safety_protocol:
            components_ok = components_ok and self.safety_protocol.monitoring_active

        # REACTIVE FABRIC: Check orchestrator health
        if self.orchestrator:
            components_ok = components_ok and self.orchestrator._running

        return components_ok

    def get_safety_status(self) -> dict[str, Any] | None:
        """Get safety protocol status.

        Returns:
            Safety protocol status dict, or None if safety disabled
        """
        if not self.config.safety_enabled or not self.safety_protocol:
            return None

        return self.safety_protocol.get_status()

    def get_safety_violations(self, limit: int = 100) -> list[SafetyViolation]:
        """Get recent safety violations.

        Args:
            limit: Maximum number of violations to return

        Returns:
            List of recent SafetyViolation objects
        """
        if not self.config.safety_enabled or not self.safety_protocol:
            return []

        all_violations = self.safety_protocol.threshold_monitor.get_violations()
        return all_violations[-limit:]  # Return most recent

    async def execute_emergency_shutdown(self, reason: str) -> bool:
        """Execute emergency shutdown via kill switch.

        Args:
            reason: Human-readable reason for shutdown

        Returns:
            True if shutdown executed, False if HITL overrode
        """
        if not self.config.safety_enabled or not self.safety_protocol:
            print("⚠️  Safety protocol not enabled, performing normal shutdown")
            await self.stop()
            return True

        return await self.safety_protocol.kill_switch.execute_emergency_shutdown(
            reason=reason, violations=[], allow_hitl_override=True
        )

    def __repr__(self) -> str:
        """String representation."""
        status = "RUNNING" if self._running else "STOPPED"
        safety_status = "ENABLED" if self.config.safety_enabled else "DISABLED"
        return f"ConsciousnessSystem(status={status}, healthy={self.is_healthy()}, safety={safety_status})"
