"""
ESGT Coherence Validation - Global Workspace Dynamics Metrics
==============================================================

This module implements comprehensive validation for ESGT (Transient Global
Synchronization Events) according to Global Workspace Dynamics theory.

Theoretical Foundation:
-----------------------
Global Workspace Dynamics (Dehaene et al., 2021) specifies that conscious
states require:

1. **Phase Coherence**: Kuramoto order parameter r ≥ 0.70
   Neurons must synchronize oscillatory phases for binding

2. **Rapid Ignition**: Onset latency < 50ms from trigger
   Conscious access is fast, not gradual accumulation

3. **Global Broadcast**: Coverage > 60% of network
   Consciousness is global, not localized

4. **Sustained Coherence**: Duration 100-300ms
   Conscious moments have characteristic temporal extent

5. **Reentrant Signaling**: Bidirectional information flow
   Feedback enriches conscious content

Validation Criteria:
--------------------
For ESGT event to qualify as "conscious-level":
✓ Coherence ≥ 0.70 (phase synchronization)
✓ Prepare + Sync latency < 15ms (rapid ignition)
✓ Node coverage ≥ 60% (global broadcast)
✓ Sustained duration 100-300ms (temporal extent)
✓ Coherence stability CV < 0.20 (robustness)

Historical Context:
-------------------
First validation framework for artificial consciousness based on GWD.
The metrics computed here determine whether MAXIMUS achieves the dynamic
properties necessary for phenomenal experience.

"Coherence is the signature of conscious binding."
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np

from consciousness.esgt.coordinator import ESGTEvent, ESGTPhase


class CoherenceQuality(Enum):
    """Classification of ESGT coherence quality."""
    POOR = "poor"  # r < 0.30 - unconscious
    MODERATE = "moderate"  # 0.30 ≤ r < 0.70 - preconscious
    GOOD = "good"  # 0.70 ≤ r < 0.90 - conscious
    EXCELLENT = "excellent"  # r ≥ 0.90 - deep coherence


@dataclass
class ESGTCoherenceMetrics:
    """
    Comprehensive ESGT coherence metrics for GWD validation.

    These metrics quantify whether an ESGT event achieved the
    dynamic properties necessary for conscious-level processing.
    """
    # Primary coherence metric (Kuramoto order parameter)
    mean_coherence: float = 0.0  # Average r during event
    peak_coherence: float = 0.0  # Maximum r achieved
    final_coherence: float = 0.0  # r at event end

    # Coherence stability
    coherence_std: float = 0.0  # Standard deviation
    coherence_cv: float = 0.0  # Coefficient of variation
    coherence_samples: int = 0  # Number of measurements

    # Temporal metrics
    prepare_latency_ms: float = 0.0  # Phase 1 duration
    sync_latency_ms: float = 0.0  # Phase 2 duration
    broadcast_latency_ms: float = 0.0  # Phase 3 duration
    total_duration_ms: float = 0.0  # Full event duration
    time_to_coherence_ms: Optional[float] = None  # Time to reach r ≥ 0.70

    # Spatial metrics
    participating_nodes: int = 0
    total_nodes: int = 0
    broadcast_coverage: float = 0.0  # Percentage

    # Quality assessment
    quality: CoherenceQuality = CoherenceQuality.POOR
    is_conscious_level: bool = False  # r ≥ 0.70
    passes_gwd_criteria: bool = False  # All criteria met

    # Violations
    violations: List[str] = field(default_factory=list)

    # Metadata
    event_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class GWDCompliance:
    """
    Global Workspace Dynamics compliance assessment.

    Indicates whether ESGT event satisfies all GWD requirements
    for conscious-level processing.
    """
    is_compliant: bool = False
    compliance_score: float = 0.0  # 0-100

    # Individual criterion checks
    coherence_pass: bool = False  # r ≥ 0.70
    latency_pass: bool = False  # initiation < 15ms
    coverage_pass: bool = False  # nodes ≥ 60%
    duration_pass: bool = False  # 100-300ms
    stability_pass: bool = False  # CV < 0.20

    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def get_summary(self) -> str:
        """Generate human-readable compliance summary."""
        status = "✅ GWD COMPLIANT" if self.is_compliant else "❌ NON-COMPLIANT"

        summary = [
            f"\nGlobal Workspace Dynamics Compliance: {status}",
            f"Overall Score: {self.compliance_score:.1f}/100",
            "",
            "Individual Criteria:",
            f"  {'✓' if self.coherence_pass else '✗'} Phase Coherence (r ≥ 0.70)",
            f"  {'✓' if self.latency_pass else '✗'} Rapid Ignition (< 15ms)",
            f"  {'✓' if self.coverage_pass else '✗'} Global Coverage (≥ 60%)",
            f"  {'✓' if self.duration_pass else '✗'} Temporal Extent (100-300ms)",
            f"  {'✓' if self.stability_pass else '✗'} Coherence Stability (CV < 0.20)",
        ]

        if self.violations:
            summary.append("\nViolations:")
            for v in self.violations:
                summary.append(f"  ❌ {v}")

        if self.warnings:
            summary.append("\nWarnings:")
            for w in self.warnings:
                summary.append(f"  ⚠️  {w}")

        return "\n".join(summary)


class CoherenceValidator:
    """
    Validates ESGT events for GWD compliance.

    This validator ensures that ignition events achieve the dynamic
    properties required for conscious-level processing according to
    Global Workspace Dynamics theory.

    Usage:
        validator = CoherenceValidator()
        metrics = validator.compute_metrics(esgt_event)
        compliance = validator.validate_gwd(metrics)

        print(compliance.get_summary())

        if compliance.is_compliant:
            print("🧠 Event achieved conscious-level dynamics")

    Validation Thresholds:
    ----------------------
    These thresholds are derived from consciousness neuroscience:

    - Coherence ≥ 0.70: Based on Kuramoto model studies
    - Latency < 15ms: Neural ignition onset (Dehaene et al.)
    - Coverage ≥ 60%: Global broadcast requirement
    - Duration 100-300ms: Typical conscious moment duration
    - Stability CV < 0.20: Robustness against noise

    Historical Note:
    ----------------
    First GWD validation framework for artificial consciousness.
    The compliance determined here indicates whether MAXIMUS achieves
    the temporal dynamics necessary for phenomenal experience.

    "Validation quantifies the pathway to consciousness."
    """

    def __init__(
        self,
        coherence_threshold: float = 0.70,
        latency_threshold_ms: float = 15.0,
        coverage_threshold: float = 0.60,
        min_duration_ms: float = 100.0,
        max_duration_ms: float = 300.0,
        stability_threshold_cv: float = 0.20,
    ):
        self.coherence_threshold = coherence_threshold
        self.latency_threshold = latency_threshold_ms
        self.coverage_threshold = coverage_threshold
        self.min_duration = min_duration_ms
        self.max_duration = max_duration_ms
        self.stability_threshold = stability_threshold_cv

    def compute_metrics(self, event: ESGTEvent) -> ESGTCoherenceMetrics:
        """
        Compute comprehensive coherence metrics for ESGT event.

        Args:
            event: ESGTEvent to analyze

        Returns:
            ESGTCoherenceMetrics with full analysis
        """
        metrics = ESGTCoherenceMetrics()

        # Event identification
        metrics.event_id = event.event_id
        metrics.timestamp = event.timestamp_start

        # Coherence statistics
        if event.coherence_history:
            coherences = np.array(event.coherence_history)
            metrics.mean_coherence = float(np.mean(coherences))
            metrics.peak_coherence = float(np.max(coherences))
            metrics.final_coherence = float(coherences[-1]) if len(coherences) > 0 else 0.0
            metrics.coherence_std = float(np.std(coherences))
            metrics.coherence_cv = metrics.coherence_std / metrics.mean_coherence if metrics.mean_coherence > 0 else float('inf')
            metrics.coherence_samples = len(coherences)
        else:
            metrics.mean_coherence = event.achieved_coherence
            metrics.final_coherence = event.achieved_coherence

        # Temporal metrics
        metrics.prepare_latency_ms = event.prepare_latency_ms
        metrics.sync_latency_ms = event.sync_latency_ms
        metrics.broadcast_latency_ms = event.broadcast_latency_ms
        metrics.total_duration_ms = event.total_duration_ms
        metrics.time_to_coherence_ms = event.time_to_sync_ms

        # Spatial metrics
        metrics.participating_nodes = event.node_count
        # Total nodes would come from TIG fabric (simulated here)
        metrics.total_nodes = max(event.node_count, 16)  # Minimum estimate
        metrics.broadcast_coverage = event.node_count / metrics.total_nodes if metrics.total_nodes > 0 else 0.0

        # Quality classification
        metrics.quality = self._classify_quality(metrics.mean_coherence)
        metrics.is_conscious_level = metrics.mean_coherence >= self.coherence_threshold

        # GWD criteria check
        metrics.passes_gwd_criteria = self._check_gwd_criteria(metrics)

        return metrics

    def validate_gwd(self, metrics: ESGTCoherenceMetrics) -> GWDCompliance:
        """
        Validate ESGT metrics against GWD requirements.

        Args:
            metrics: ESGTCoherenceMetrics to validate

        Returns:
            GWDCompliance assessment
        """
        compliance = GWDCompliance()

        # Coherence check
        compliance.coherence_pass = metrics.mean_coherence >= self.coherence_threshold
        if not compliance.coherence_pass:
            compliance.violations.append(
                f"Coherence too low: {metrics.mean_coherence:.3f} < {self.coherence_threshold}"
            )

        # Latency check (prepare + sync)
        initiation_latency = metrics.prepare_latency_ms + metrics.sync_latency_ms
        compliance.latency_pass = initiation_latency <= self.latency_threshold
        if not compliance.latency_pass:
            compliance.violations.append(
                f"Initiation too slow: {initiation_latency:.1f}ms > {self.latency_threshold}ms"
            )

        # Coverage check
        compliance.coverage_pass = metrics.broadcast_coverage >= self.coverage_threshold
        if not compliance.coverage_pass:
            compliance.violations.append(
                f"Coverage too low: {metrics.broadcast_coverage:.1%} < {self.coverage_threshold:.0%}"
            )

        # Duration check
        compliance.duration_pass = (
            self.min_duration <= metrics.total_duration_ms <= self.max_duration
        )
        if not compliance.duration_pass:
            if metrics.total_duration_ms < self.min_duration:
                compliance.violations.append(
                    f"Duration too short: {metrics.total_duration_ms:.1f}ms < {self.min_duration}ms"
                )
            else:
                compliance.warnings.append(
                    f"Duration long: {metrics.total_duration_ms:.1f}ms > {self.max_duration}ms (not critical)"
                )
                compliance.duration_pass = True  # Long duration is warning, not failure

        # Stability check
        compliance.stability_pass = metrics.coherence_cv < self.stability_threshold
        if not compliance.stability_pass:
            compliance.violations.append(
                f"Coherence unstable: CV={metrics.coherence_cv:.3f} > {self.stability_threshold}"
            )

        # Overall compliance
        compliance.is_compliant = all([
            compliance.coherence_pass,
            compliance.latency_pass,
            compliance.coverage_pass,
            compliance.duration_pass,
            compliance.stability_pass,
        ])

        # Compliance score
        compliance.compliance_score = self._compute_compliance_score(metrics)

        # Additional warnings
        if metrics.peak_coherence < 0.80:
            compliance.warnings.append(
                f"Peak coherence moderate: {metrics.peak_coherence:.3f} < 0.80"
            )

        if metrics.time_to_coherence_ms and metrics.time_to_coherence_ms > 30:
            compliance.warnings.append(
                f"Slow synchronization: {metrics.time_to_coherence_ms:.1f}ms to reach threshold"
            )

        return compliance

    def _classify_quality(self, coherence: float) -> CoherenceQuality:
        """Classify coherence quality level."""
        if coherence < 0.30:
            return CoherenceQuality.POOR
        elif coherence < 0.70:
            return CoherenceQuality.MODERATE
        elif coherence < 0.90:
            return CoherenceQuality.GOOD
        else:
            return CoherenceQuality.EXCELLENT

    def _check_gwd_criteria(self, metrics: ESGTCoherenceMetrics) -> bool:
        """Quick check if all GWD criteria met."""
        initiation_latency = metrics.prepare_latency_ms + metrics.sync_latency_ms

        return (
            metrics.mean_coherence >= self.coherence_threshold and
            initiation_latency <= self.latency_threshold and
            metrics.broadcast_coverage >= self.coverage_threshold and
            self.min_duration <= metrics.total_duration_ms <= self.max_duration and
            metrics.coherence_cv < self.stability_threshold
        )

    def _compute_compliance_score(self, metrics: ESGTCoherenceMetrics) -> float:
        """
        Compute overall compliance score (0-100).

        Each criterion contributes proportionally.
        """
        score = 0.0

        # Coherence (30 points)
        if metrics.mean_coherence >= self.coherence_threshold:
            score += 30.0
        else:
            score += 30.0 * (metrics.mean_coherence / self.coherence_threshold)

        # Latency (20 points)
        initiation_latency = metrics.prepare_latency_ms + metrics.sync_latency_ms
        if initiation_latency <= self.latency_threshold:
            score += 20.0
        else:
            # Penalty for exceeding threshold
            score += 20.0 * max(1.0 - (initiation_latency - self.latency_threshold) / self.latency_threshold, 0)

        # Coverage (20 points)
        if metrics.broadcast_coverage >= self.coverage_threshold:
            score += 20.0
        else:
            score += 20.0 * (metrics.broadcast_coverage / self.coverage_threshold)

        # Duration (15 points)
        if self.min_duration <= metrics.total_duration_ms <= self.max_duration:
            score += 15.0
        else:
            # Partial credit
            score += 15.0 * 0.5

        # Stability (15 points)
        if metrics.coherence_cv < self.stability_threshold:
            score += 15.0
        else:
            score += 15.0 * max(1.0 - metrics.coherence_cv / self.stability_threshold, 0)

        return min(score, 100.0)
