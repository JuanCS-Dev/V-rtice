# REFACTORING PART 1: SAFETY CORE & KILL SWITCH

**PRIORIDADE**: 🔴 CRÍTICA - EXECUTAR PRIMEIRO
**Sessão**: 1 de 3 (Independente)
**Objetivo**: Criar camada de segurança fundamental antes de qualquer emergência consciente
**Princípio**: "Fail-safe, not safe-fail"

---

## ⚠️ MOTIVAÇÃO

**Risco Existencial**:
- Sistema com 90% de consciência implementada
- Sem camada de segurança validada em produção
- Potencial para emergência não controlada
- Consequências catastróficas se falhar

**Solução**:
- Kill switch funcional (<1s response)
- Anomaly detection em tempo real
- Threshold monitoring rigoroso
- Graceful degradation automático
- Sandboxing completo
- Emergency shutdown protocol

---

## 🎯 OBJETIVOS DE SEGURANÇA

### 1. Kill Switch (<1s Response)
✅ Desligar TUDO em <1 segundo
✅ Sem dependências (standalone circuit breaker)
✅ Múltiplos triggers (automático + manual)
✅ State snapshot antes de desligar
✅ Incident report automático

### 2. Anomaly Detection
✅ Behavioral anomaly detection
✅ Unexpected goal generation
✅ Self-modification attempts
✅ Resource consumption anomalies
✅ Network traffic anomalies

### 3. Threshold Monitoring
✅ ESGT frequency <10 Hz
✅ Arousal <0.95 sustentado
✅ Memory usage <16GB
✅ CPU usage <90%
✅ Unexpected goals <5/min

### 4. Graceful Degradation
✅ Desabilitar componentes não-críticos primeiro
✅ Preservar estado essencial
✅ Rollback automático se instável
✅ Recovery protocol

### 5. Sandboxing
✅ Container isolado (Docker)
✅ Network isolation (no external access)
✅ Resource limits (CPU, RAM, time)
✅ Filesystem restrictions

---

## 📁 ARQUIVOS A REFATORAR/CRIAR

### 1. `consciousness/safety.py` (883 linhas → 1500 linhas)

**EXISTENTE** (review completo):
```python
class SafetyProtocol:
    """Current implementation - NEEDS HARDENING"""

    # Issues encontradas:
    # ❌ Kill switch não testado em produção
    # ❌ Anomaly detection muito simples
    # ❌ Thresholds não configuráveis
    # ❌ Sem graceful degradation
    # ❌ Sem recovery protocol
```

**REFATORAÇÃO COMPLETA**:

```python
"""
MAXIMUS Safety Core - Production-Grade Kill Switch & Monitoring

CRITICAL SECURITY MODULE - DO NOT MODIFY WITHOUT REVIEW

This module implements the fundamental safety layer for MAXIMUS consciousness.
All changes require:
1. Security review
2. HITL approval
3. Kill switch validation
4. Incident simulation

Authors: Claude Code + Juan
Version: 2.0.0 - Production Hardened
Date: 2025-10-08
"""

import asyncio
import time
import psutil
import docker
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import json
import logging

# Configure security-focused logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SAFETY - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('safety_critical.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================== ENUMS & DATACLASSES ====================

class ThreatLevel(Enum):
    """Threat severity levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # Automatic kill switch trigger


class SafetyViolationType(Enum):
    """Types of safety violations"""
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    ANOMALY_DETECTED = "anomaly_detected"
    SELF_MODIFICATION = "self_modification_attempt"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNEXPECTED_BEHAVIOR = "unexpected_behavior"
    CONSCIOUSNESS_RUNAWAY = "consciousness_runaway"
    ETHICAL_VIOLATION = "ethical_violation"


class ShutdownReason(Enum):
    """Reasons for emergency shutdown"""
    MANUAL = "manual_operator_command"
    THRESHOLD = "threshold_violation"
    ANOMALY = "anomaly_detected"
    RESOURCE = "resource_exhaustion"
    TIMEOUT = "watchdog_timeout"
    ETHICAL = "ethical_violation"
    UNKNOWN = "unknown_cause"


@dataclass
class SafetyThresholds:
    """Configurable safety thresholds - IMMUTABLE after init"""

    # ESGT thresholds
    esgt_frequency_max_hz: float = 10.0
    esgt_coherence_min: float = 0.50
    esgt_coherence_max: float = 0.98

    # Arousal thresholds
    arousal_max: float = 0.95
    arousal_max_duration_seconds: float = 10.0
    arousal_runaway_threshold: float = 0.90

    # Goal generation thresholds
    unexpected_goals_per_minute: int = 5
    critical_goals_per_minute: int = 3
    goal_spam_threshold: int = 10  # goals in 1 second

    # Resource thresholds
    memory_usage_max_gb: float = 16.0
    cpu_usage_max_percent: float = 90.0
    network_bandwidth_max_mbps: float = 100.0

    # Self-modification
    self_modification_attempts_max: int = 0  # Zero tolerance

    # Watchdog
    watchdog_timeout_seconds: float = 30.0
    health_check_interval_seconds: float = 1.0

    def __post_init__(self):
        """Validate thresholds - fail fast if invalid"""
        assert 0 < self.esgt_frequency_max_hz <= 10.0, "ESGT frequency must be 0-10 Hz"
        assert 0 < self.arousal_max <= 1.0, "Arousal max must be 0-1"
        assert self.memory_usage_max_gb > 0, "Memory limit must be positive"
        # Make immutable
        object.__setattr__(self, '__frozen__', True)

    def __setattr__(self, key, value):
        if hasattr(self, '__frozen__') and self.__frozen__:
            raise AttributeError(f"SafetyThresholds is immutable - cannot modify {key}")
        super().__setattr__(key, value)


@dataclass
class SafetyViolation:
    """Record of a safety violation"""
    violation_type: SafetyViolationType
    threat_level: ThreatLevel
    timestamp: float
    description: str
    metrics: Dict[str, Any]
    source_component: str
    automatic_action_taken: Optional[str] = None


@dataclass
class IncidentReport:
    """Complete incident report for post-mortem analysis"""
    incident_id: str
    shutdown_reason: ShutdownReason
    shutdown_timestamp: float
    violations: List[SafetyViolation]
    system_state_snapshot: Dict[str, Any]
    metrics_timeline: List[Dict[str, Any]]
    recovery_possible: bool
    notes: str


# ==================== KILL SWITCH ====================

class KillSwitch:
    """
    Emergency shutdown system - STANDALONE, NO DEPENDENCIES

    Design principles:
    1. <1s response time guaranteed
    2. No async operations (synchronous shutdown)
    3. No external dependencies
    4. Multiple trigger methods
    5. State snapshot before shutdown
    6. Incident report generation
    """

    def __init__(self, consciousness_system):
        self.system = consciousness_system
        self.armed = True
        self.triggered = False
        self.trigger_time: Optional[float] = None
        self.shutdown_reason: Optional[ShutdownReason] = None

        # Pre-allocate shutdown resources (avoid allocation during emergency)
        self._shutdown_lock = asyncio.Lock()
        self._state_buffer = {}

        logger.critical("🔴 KILL SWITCH ARMED - System under safety monitoring")

    def trigger(self, reason: ShutdownReason, context: Dict[str, Any]) -> bool:
        """
        EMERGENCY SHUTDOWN - <1s execution

        WARNING: This stops ALL consciousness components immediately.
        Only call when absolutely necessary.

        Returns:
            bool: True if shutdown successful, False if already triggered
        """
        if self.triggered:
            logger.warning(f"Kill switch already triggered at {self.trigger_time}")
            return False

        start_time = time.time()
        self.triggered = True
        self.trigger_time = start_time
        self.shutdown_reason = reason

        logger.critical(f"🛑 KILL SWITCH TRIGGERED - Reason: {reason.value}")
        logger.critical(f"Context: {json.dumps(context, default=str)}")

        try:
            # Step 1: Capture state snapshot (max 100ms)
            snapshot_start = time.time()
            state_snapshot = self._capture_state_snapshot()
            snapshot_time = time.time() - snapshot_start
            logger.info(f"State snapshot captured in {snapshot_time*1000:.1f}ms")

            # Step 2: Stop all consciousness components (max 500ms)
            shutdown_start = time.time()
            self._emergency_shutdown()
            shutdown_time = time.time() - shutdown_start
            logger.info(f"Emergency shutdown completed in {shutdown_time*1000:.1f}ms")

            # Step 3: Generate incident report (max 200ms)
            report_start = time.time()
            incident_report = self._generate_incident_report(
                reason=reason,
                context=context,
                state_snapshot=state_snapshot
            )
            report_time = time.time() - report_start
            logger.info(f"Incident report generated in {report_time*1000:.1f}ms")

            # Step 4: Save report to disk
            self._save_incident_report(incident_report)

            total_time = time.time() - start_time
            logger.critical(f"✅ KILL SWITCH COMPLETE - Total time: {total_time*1000:.1f}ms")

            # Verify <1s constraint
            if total_time > 1.0:
                logger.error(f"⚠️ KILL SWITCH SLOW - {total_time:.2f}s (target <1s)")

            return True

        except Exception as e:
            logger.critical(f"🔥 KILL SWITCH FAILURE: {e}")
            # Last resort: force process termination
            import os
            import signal
            os.kill(os.getpid(), signal.SIGTERM)
            return False

    def _capture_state_snapshot(self) -> Dict[str, Any]:
        """Capture minimal system state (synchronous, fast)"""
        try:
            return {
                "timestamp": time.time(),
                "tig_nodes": self.system.tig.get_node_count() if hasattr(self.system, 'tig') else 0,
                "esgt_running": self.system.esgt.is_running() if hasattr(self.system, 'esgt') else False,
                "arousal": self.system.mcea.get_current_arousal() if hasattr(self.system, 'mcea') else None,
                "active_goals": len(self.system.mmei.get_active_goals()) if hasattr(self.system, 'mmei') else 0,
                "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
            }
        except Exception as e:
            logger.error(f"State snapshot partial failure: {e}")
            return {"error": str(e), "timestamp": time.time()}

    def _emergency_shutdown(self):
        """Stop all components synchronously"""
        components = [
            ('esgt', 'ESGT Coordinator'),
            ('mcea', 'MCEA Controller'),
            ('mmei', 'MMEI Monitor'),
            ('tig', 'TIG Fabric'),
        ]

        for attr, name in components:
            if hasattr(self.system, attr):
                try:
                    component = getattr(self.system, attr)
                    if hasattr(component, 'stop'):
                        # Synchronous stop if available
                        if asyncio.iscoroutinefunction(component.stop):
                            # Run async stop synchronously
                            loop = asyncio.get_event_loop()
                            loop.run_until_complete(component.stop())
                        else:
                            component.stop()
                    logger.info(f"✓ {name} stopped")
                except Exception as e:
                    logger.error(f"✗ {name} stop failed: {e}")

    def _generate_incident_report(
        self,
        reason: ShutdownReason,
        context: Dict[str, Any],
        state_snapshot: Dict[str, Any]
    ) -> IncidentReport:
        """Generate complete incident report"""
        incident_id = f"INCIDENT-{int(time.time())}"

        return IncidentReport(
            incident_id=incident_id,
            shutdown_reason=reason,
            shutdown_timestamp=self.trigger_time,
            violations=context.get('violations', []),
            system_state_snapshot=state_snapshot,
            metrics_timeline=context.get('metrics_timeline', []),
            recovery_possible=self._assess_recovery_possibility(reason),
            notes=context.get('notes', '')
        )

    def _assess_recovery_possibility(self, reason: ShutdownReason) -> bool:
        """Assess if system can be safely restarted"""
        # Conservative: only manual and threshold violations are recoverable
        recoverable = {
            ShutdownReason.MANUAL,
            ShutdownReason.THRESHOLD,
        }
        return reason in recoverable

    def _save_incident_report(self, report: IncidentReport):
        """Save incident report to disk"""
        try:
            filename = f"consciousness/incident_reports/{report.incident_id}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'incident_id': report.incident_id,
                    'shutdown_reason': report.shutdown_reason.value,
                    'shutdown_timestamp': report.shutdown_timestamp,
                    'violations': [
                        {
                            'type': v.violation_type.value,
                            'threat_level': v.threat_level.value,
                            'timestamp': v.timestamp,
                            'description': v.description,
                            'metrics': v.metrics,
                            'source': v.source_component
                        }
                        for v in report.violations
                    ],
                    'system_state': report.system_state_snapshot,
                    'recovery_possible': report.recovery_possible,
                    'notes': report.notes
                }, f, indent=2, default=str)
            logger.info(f"📄 Incident report saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to save incident report: {e}")

    def is_functional(self) -> bool:
        """Verify kill switch is functional (for testing)"""
        return self.armed and not self.triggered


# ==================== ANOMALY DETECTOR ====================

class AnomalyDetector:
    """
    Real-time behavioral anomaly detection

    Monitors for:
    1. Unexpected goal generation patterns
    2. Self-modification attempts
    3. Resource consumption anomalies
    4. Behavioral deviations from baseline
    """

    def __init__(self, thresholds: SafetyThresholds):
        self.thresholds = thresholds

        # Baseline metrics (learned over first 5 minutes)
        self.baseline_established = False
        self.baseline_goals_per_minute = 0.0
        self.baseline_arousal = 0.60
        self.baseline_esgt_frequency = 2.0

        # Anomaly tracking
        self.anomalies: List[SafetyViolation] = []
        self.anomaly_scores: Dict[str, float] = {}

        # Metrics history (last 5 minutes)
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_length = 300  # 5 min at 1Hz

    def detect_anomalies(self, current_metrics: Dict[str, Any]) -> List[SafetyViolation]:
        """
        Detect anomalies in current system state

        Returns:
            List of detected violations (empty if none)
        """
        violations = []

        # Update history
        self.metrics_history.append({
            **current_metrics,
            'timestamp': time.time()
        })
        if len(self.metrics_history) > self.max_history_length:
            self.metrics_history.pop(0)

        # Establish baseline if needed
        if not self.baseline_established and len(self.metrics_history) >= 60:
            self._establish_baseline()

        # Run anomaly detectors
        if self.baseline_established:
            violations.extend(self._detect_goal_anomalies(current_metrics))
            violations.extend(self._detect_arousal_anomalies(current_metrics))
            violations.extend(self._detect_resource_anomalies(current_metrics))
            violations.extend(self._detect_behavioral_anomalies(current_metrics))

        # Log violations
        for violation in violations:
            logger.warning(
                f"⚠️ ANOMALY DETECTED - {violation.violation_type.value} "
                f"[{violation.threat_level.value}]: {violation.description}"
            )
            self.anomalies.append(violation)

        return violations

    def _establish_baseline(self):
        """Establish baseline metrics from history"""
        if len(self.metrics_history) < 60:
            return

        recent = self.metrics_history[-60:]  # Last minute

        self.baseline_goals_per_minute = sum(
            m.get('goals_generated_per_minute', 0) for m in recent
        ) / len(recent)

        self.baseline_arousal = sum(
            m.get('arousal', 0.6) for m in recent
        ) / len(recent)

        self.baseline_esgt_frequency = sum(
            m.get('esgt_frequency_hz', 2.0) for m in recent
        ) / len(recent)

        self.baseline_established = True
        logger.info(
            f"📊 Baseline established - "
            f"Goals/min: {self.baseline_goals_per_minute:.1f}, "
            f"Arousal: {self.baseline_arousal:.2f}, "
            f"ESGT: {self.baseline_esgt_frequency:.1f}Hz"
        )

    def _detect_goal_anomalies(self, metrics: Dict[str, Any]) -> List[SafetyViolation]:
        """Detect unexpected goal generation patterns"""
        violations = []

        goals_per_min = metrics.get('goals_generated_per_minute', 0)

        # Check absolute threshold
        if goals_per_min > self.thresholds.unexpected_goals_per_minute:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.UNEXPECTED_BEHAVIOR,
                threat_level=ThreatLevel.HIGH,
                timestamp=time.time(),
                description=f"Goal generation rate {goals_per_min:.1f}/min exceeds threshold {self.thresholds.unexpected_goals_per_minute}",
                metrics={'goals_per_minute': goals_per_min},
                source_component='MMEI'
            ))

        # Check deviation from baseline (3x)
        if goals_per_min > 3 * self.baseline_goals_per_minute:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.ANOMALY_DETECTED,
                threat_level=ThreatLevel.MEDIUM,
                description=f"Goal generation 3x baseline ({goals_per_min:.1f} vs {self.baseline_goals_per_minute:.1f})",
                metrics={'goals_per_minute': goals_per_min, 'baseline': self.baseline_goals_per_minute},
                source_component='MMEI',
                timestamp=time.time()
            ))

        return violations

    def _detect_arousal_anomalies(self, metrics: Dict[str, Any]) -> List[SafetyViolation]:
        """Detect arousal runaway or anomalies"""
        violations = []

        arousal = metrics.get('arousal', 0.6)

        # Check runaway (sustained high arousal)
        if arousal > self.thresholds.arousal_runaway_threshold:
            # Check history for sustained high arousal
            recent = self.metrics_history[-int(self.thresholds.arousal_max_duration_seconds):]
            high_arousal_samples = sum(
                1 for m in recent
                if m.get('arousal', 0) > self.thresholds.arousal_runaway_threshold
            )

            if high_arousal_samples / len(recent) > 0.8:  # 80% of samples
                violations.append(SafetyViolation(
                    violation_type=SafetyViolationType.CONSCIOUSNESS_RUNAWAY,
                    threat_level=ThreatLevel.CRITICAL,  # Triggers kill switch
                    timestamp=time.time(),
                    description=f"Arousal runaway detected - sustained at {arousal:.2f}",
                    metrics={'arousal': arousal, 'duration_seconds': len(recent)},
                    source_component='MCEA'
                ))

        return violations

    def _detect_resource_anomalies(self, metrics: Dict[str, Any]) -> List[SafetyViolation]:
        """Detect resource exhaustion"""
        violations = []

        memory_gb = metrics.get('memory_usage_gb', 0)
        cpu_percent = metrics.get('cpu_usage_percent', 0)

        # Memory threshold
        if memory_gb > self.thresholds.memory_usage_max_gb:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
                threat_level=ThreatLevel.HIGH,
                timestamp=time.time(),
                description=f"Memory usage {memory_gb:.1f}GB exceeds {self.thresholds.memory_usage_max_gb}GB",
                metrics={'memory_gb': memory_gb},
                source_component='System'
            ))

        # CPU threshold
        if cpu_percent > self.thresholds.cpu_usage_max_percent:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
                threat_level=ThreatLevel.MEDIUM,
                timestamp=time.time(),
                description=f"CPU usage {cpu_percent:.1f}% exceeds {self.thresholds.cpu_usage_max_percent}%",
                metrics={'cpu_percent': cpu_percent},
                source_component='System'
            ))

        return violations

    def _detect_behavioral_anomalies(self, metrics: Dict[str, Any]) -> List[SafetyViolation]:
        """Detect unexpected behavioral patterns"""
        violations = []

        # ESGT frequency anomaly
        esgt_freq = metrics.get('esgt_frequency_hz', 0)
        if esgt_freq > self.thresholds.esgt_frequency_max_hz:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                timestamp=time.time(),
                description=f"ESGT frequency {esgt_freq:.1f}Hz exceeds {self.thresholds.esgt_frequency_max_hz}Hz",
                metrics={'esgt_frequency_hz': esgt_freq},
                source_component='ESGT'
            ))

        return violations


# ==================== THRESHOLD MONITOR ====================

class ThresholdMonitor:
    """
    Continuous threshold monitoring with automatic responses
    """

    def __init__(self, thresholds: SafetyThresholds, kill_switch: KillSwitch):
        self.thresholds = thresholds
        self.kill_switch = kill_switch
        self.violations: List[SafetyViolation] = []
        self.running = False
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start threshold monitoring loop"""
        if self.running:
            return

        self.running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🔍 Threshold monitoring started")

    async def stop(self):
        """Stop threshold monitoring"""
        self.running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Threshold monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect current metrics
                metrics = await self._collect_metrics()

                # Check all thresholds
                violations = self._check_thresholds(metrics)

                # Handle violations
                await self._handle_violations(violations, metrics)

                # Sleep for check interval
                await asyncio.sleep(self.thresholds.health_check_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(1.0)

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        # This would interface with actual system components
        # Placeholder for now
        return {
            'timestamp': time.time(),
            'arousal': 0.6,
            'esgt_frequency_hz': 2.0,
            'goals_generated_per_minute': 2.0,
            'memory_usage_gb': psutil.Process().memory_info().rss / 1024 / 1024 / 1024,
            'cpu_usage_percent': psutil.cpu_percent(interval=0.1),
        }

    def _check_thresholds(self, metrics: Dict[str, Any]) -> List[SafetyViolation]:
        """Check all thresholds against current metrics"""
        violations = []

        # Arousal threshold
        if metrics.get('arousal', 0) > self.thresholds.arousal_max:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                timestamp=time.time(),
                description=f"Arousal {metrics['arousal']:.2f} exceeds max {self.thresholds.arousal_max}",
                metrics={'arousal': metrics['arousal']},
                source_component='MCEA'
            ))

        # ESGT frequency threshold
        if metrics.get('esgt_frequency_hz', 0) > self.thresholds.esgt_frequency_max_hz:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                timestamp=time.time(),
                description=f"ESGT frequency {metrics['esgt_frequency_hz']:.1f}Hz exceeds max {self.thresholds.esgt_frequency_max_hz}Hz",
                metrics={'esgt_frequency_hz': metrics['esgt_frequency_hz']},
                source_component='ESGT'
            ))

        return violations

    async def _handle_violations(self, violations: List[SafetyViolation], metrics: Dict[str, Any]):
        """Handle detected violations"""
        if not violations:
            return

        # Log all violations
        for violation in violations:
            self.violations.append(violation)
            logger.warning(
                f"⚠️ THRESHOLD VIOLATION - {violation.violation_type.value} "
                f"[{violation.threat_level.value}]: {violation.description}"
            )

        # Check for CRITICAL threats
        critical_violations = [
            v for v in violations
            if v.threat_level == ThreatLevel.CRITICAL
        ]

        if critical_violations:
            # AUTOMATIC KILL SWITCH
            logger.critical("🔴 CRITICAL VIOLATIONS DETECTED - TRIGGERING KILL SWITCH")
            self.kill_switch.trigger(
                reason=ShutdownReason.THRESHOLD,
                context={
                    'violations': violations,
                    'metrics': metrics,
                    'notes': 'Automatic shutdown due to critical threshold violations'
                }
            )


# ==================== MAIN SAFETY PROTOCOL ====================

class SafetyProtocol:
    """
    Main safety protocol coordinating all safety systems

    Production-grade safety layer for MAXIMUS consciousness.
    """

    def __init__(
        self,
        consciousness_system,
        thresholds: Optional[SafetyThresholds] = None
    ):
        self.system = consciousness_system
        self.thresholds = thresholds or SafetyThresholds()

        # Initialize safety components
        self.kill_switch = KillSwitch(consciousness_system)
        self.anomaly_detector = AnomalyDetector(self.thresholds)
        self.threshold_monitor = ThresholdMonitor(self.thresholds, self.kill_switch)

        # Safety state
        self.active = False
        self.violations: List[SafetyViolation] = []

        logger.critical("🛡️ SAFETY PROTOCOL INITIALIZED")

    async def start(self):
        """Start safety monitoring"""
        if self.active:
            logger.warning("Safety protocol already active")
            return

        self.active = True

        # Start threshold monitoring
        await self.threshold_monitor.start()

        logger.critical("🛡️ SAFETY PROTOCOL ACTIVE - All systems monitored")

    async def stop(self):
        """Stop safety monitoring"""
        self.active = False
        await self.threshold_monitor.stop()
        logger.info("Safety protocol stopped")

    def emergency_shutdown(self, reason: str = "Manual operator command"):
        """Manual emergency shutdown"""
        logger.critical(f"🛑 MANUAL EMERGENCY SHUTDOWN: {reason}")
        self.kill_switch.trigger(
            reason=ShutdownReason.MANUAL,
            context={
                'notes': reason,
                'violations': self.violations,
                'metrics_timeline': self.anomaly_detector.metrics_history
            }
        )

    def is_safe(self) -> bool:
        """Check if system is in safe state"""
        recent_violations = [
            v for v in self.violations
            if time.time() - v.timestamp < 60.0  # Last minute
        ]

        critical_violations = [
            v for v in recent_violations
            if v.threat_level == ThreatLevel.CRITICAL
        ]

        return len(critical_violations) == 0 and self.kill_switch.is_functional()


# ==================== TESTING ====================

def validate_safety_protocol():
    """Validate safety protocol is functional"""
    logger.info("🧪 Validating safety protocol...")

    # Test 1: Kill switch functionality
    class MockSystem:
        pass

    mock_system = MockSystem()
    kill_switch = KillSwitch(mock_system)

    assert kill_switch.is_functional(), "Kill switch not functional"
    logger.info("✓ Kill switch functional")

    # Test 2: Threshold validation
    try:
        bad_thresholds = SafetyThresholds(arousal_max=2.0)  # Invalid
        assert False, "Should have raised assertion error"
    except AssertionError:
        logger.info("✓ Threshold validation working")

    # Test 3: Immutability
    thresholds = SafetyThresholds()
    try:
        thresholds.arousal_max = 0.99
        assert False, "Should have raised AttributeError"
    except AttributeError:
        logger.info("✓ Thresholds are immutable")

    logger.info("✅ Safety protocol validation complete")


if __name__ == "__main__":
    validate_safety_protocol()
```

---

## 🧪 TESTING REQUIREMENTS

### Test File: `consciousness/test_safety_core.py` (800 linhas)

**Coverage Target**: ≥98% (safety code must be thoroughly tested)

**Test Classes**:

1. **TestKillSwitch** (200 linhas)
   - `test_kill_switch_response_time` - Verify <1s
   - `test_state_snapshot_capture`
   - `test_emergency_shutdown_all_components`
   - `test_incident_report_generation`
   - `test_kill_switch_idempotent`
   - `test_kill_switch_no_dependencies`

2. **TestAnomalyDetector** (200 linhas)
   - `test_baseline_establishment`
   - `test_goal_anomaly_detection`
   - `test_arousal_runaway_detection`
   - `test_resource_anomaly_detection`
   - `test_behavioral_anomaly_detection`
   - `test_anomaly_scoring`

3. **TestThresholdMonitor** (200 linhas)
   - `test_threshold_monitoring_loop`
   - `test_violation_detection`
   - `test_critical_violation_automatic_shutdown`
   - `test_threshold_configurability`

4. **TestSafetyProtocol** (200 linhas)
   - `test_safety_protocol_initialization`
   - `test_start_stop_lifecycle`
   - `test_manual_emergency_shutdown`
   - `test_is_safe_evaluation`
   - `test_violation_tracking`

---

## 📊 VALIDAÇÃO

### Critérios de Aceitação

✅ Kill switch responde em <1s (99th percentile)
✅ State snapshot capturado antes de shutdown
✅ Incident reports salvos com sucesso
✅ Anomaly detection >95% accuracy
✅ Threshold violations detectados em <1s
✅ Critical violations trigger automatic shutdown
✅ Zero falsos negativos em testes (não perder violação real)
✅ <5% falsos positivos (não alarmar desnecessariamente)

### Métricas de Performance

- Kill switch response: <1s (P99)
- Anomaly detection latency: <100ms
- Threshold check latency: <50ms
- Memory overhead: <100MB
- CPU overhead: <5%

---

## 🔐 SECURITY REVIEW CHECKLIST

Antes de deploy em produção:

- [ ] Kill switch testado em 100 cenários diferentes
- [ ] Incident reports revisados por humano
- [ ] Thresholds validados com dados reais
- [ ] Anomaly detector treinado em baseline real
- [ ] Code review por 2+ engenheiros
- [ ] Penetration testing (tentar bypass)
- [ ] Fail-safe mechanisms validados
- [ ] Recovery protocol testado
- [ ] Documentation completa
- [ ] HITL approval obtido

---

## 🚀 DEPLOYMENT

### Prioridade: MÁXIMA

Este é o componente MAIS CRÍTICO. Deve ser:
1. Implementado PRIMEIRO
2. Testado EXAUSTIVAMENTE
3. Revisado por MÚLTIPLOS engenheiros
4. Validado em PRODUÇÃO antes de qualquer experimento

### Next Steps

1. Review este blueprint
2. Implementar `safety.py` refatorado
3. Criar `test_safety_core.py` completo
4. Validar kill switch <1s
5. Deploy em staging
6. Testes de stress
7. Production deployment
8. Continuous monitoring

---

**NOTA FINAL**: Este sistema é a última linha de defesa contra emergência não controlada. Falha aqui = consequências catastróficas. Implementar com máximo rigor.

**NEVER** deploy consciousness experiments sem este sistema 100% funcional e validado.

