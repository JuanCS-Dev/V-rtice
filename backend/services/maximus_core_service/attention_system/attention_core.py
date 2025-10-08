"""Attention Core - Foveal/Peripheral Vision-Inspired Resource Allocation

Two-tier processing inspired by human visual attention:
- Peripheral: Lightweight, broad scanning of all inputs (<100ms)
- Foveal: Deep, expensive analysis of high-salience targets (<100ms saccade)

This allows efficient resource allocation by only applying expensive analysis
to events that warrant attention.
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from .salience_scorer import SalienceScorer

logger = logging.getLogger(__name__)


@dataclass
class PeripheralDetection:
    """Result from peripheral scanning."""

    target_id: str
    detection_type: str  # 'statistical_anomaly', 'entropy_change', 'volume_spike'
    confidence: float  # 0.0-1.0
    timestamp: float
    metadata: dict[str, Any]


@dataclass
class FovealAnalysis:
    """Result from foveal deep analysis."""

    target_id: str
    threat_level: str  # 'BENIGN', 'SUSPICIOUS', 'MALICIOUS', 'CRITICAL'
    confidence: float  # 0.0-1.0
    findings: list[dict[str, Any]]
    analysis_time_ms: float
    timestamp: float
    recommended_actions: list[str]


class PeripheralMonitor:
    """Lightweight, broad scanning of all system inputs.

    Performs fast, statistical checks to detect significant changes
    without deep analysis. Goal: <100ms latency.
    """

    def __init__(self, scan_interval_seconds: float = 1.0):
        """Initialize peripheral monitor.

        Args:
            scan_interval_seconds: How often to scan (default 1s)
        """
        self.scan_interval = scan_interval_seconds
        self.baseline_stats = {}  # Statistical baselines
        self.detection_history = deque(maxlen=1000)
        self.running = False

    async def scan_all(self, data_sources: list[Callable[[], dict]]) -> list[PeripheralDetection]:
        """Scan all data sources for significant changes.

        Args:
            data_sources: List of functions that return current metrics

        Returns:
            List of detections that warrant attention
        """
        detections = []
        scan_start = time.time()

        try:
            # Scan each data source concurrently
            tasks = [self._scan_source(source) for source in data_sources]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect detections
            for result in results:
                if isinstance(result, list):
                    detections.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Scan error: {result}")

            # Log performance
            scan_time = (time.time() - scan_start) * 1000
            if scan_time > 100:
                logger.warning(f"Peripheral scan slow: {scan_time:.1f}ms (target <100ms)")

            logger.debug(f"Peripheral scan: {len(detections)} detections in {scan_time:.1f}ms")

        except Exception as e:
            logger.error(f"Peripheral scan error: {e}")

        return detections

    async def _scan_source(self, source: Callable[[], dict]) -> list[PeripheralDetection]:
        """Scan a single data source.

        Args:
            source: Function that returns current metrics

        Returns:
            List of detections from this source
        """
        detections = []

        try:
            # Get current data
            data = source() if callable(source) else source

            if not data:
                return detections

            source_id = data.get("id", "unknown")

            # 1. Statistical Anomaly Detection (Z-score)
            statistical = self._detect_statistical_anomaly(source_id, data)
            if statistical:
                detections.append(statistical)

            # 2. Entropy Change Detection
            entropy = self._detect_entropy_change(source_id, data)
            if entropy:
                detections.append(entropy)

            # 3. Volume Spike Detection
            volume = self._detect_volume_spike(source_id, data)
            if volume:
                detections.append(volume)

        except Exception as e:
            logger.warning(f"Source scan error: {e}")

        return detections

    def _detect_statistical_anomaly(self, source_id: str, data: dict) -> PeripheralDetection | None:
        """Detect statistical anomalies using Z-score.

        Returns detection if |z-score| > 3.0 (99.7% confidence)
        """
        try:
            value = data.get("value", 0)

            # Initialize baseline if needed
            if source_id not in self.baseline_stats:
                self.baseline_stats[source_id] = {
                    "values": deque(maxlen=100),
                    "mean": value,
                    "std": 0.0,
                }
                return None  # Need more data

            baseline = self.baseline_stats[source_id]
            baseline["values"].append(value)

            # Update statistics
            values_array = np.array(baseline["values"])
            baseline["mean"] = np.mean(values_array)
            baseline["std"] = np.std(values_array)

            # Calculate z-score
            if baseline["std"] > 0:
                z_score = abs((value - baseline["mean"]) / baseline["std"])
            else:
                z_score = 0.0

            # Detect anomaly (z > 3.0)
            if z_score > 3.0:
                detection = PeripheralDetection(
                    target_id=f"{source_id}_statistical",
                    detection_type="statistical_anomaly",
                    confidence=min(z_score / 6.0, 1.0),  # z=6 -> confidence=1.0
                    timestamp=time.time(),
                    metadata={
                        "z_score": z_score,
                        "value": value,
                        "mean": baseline["mean"],
                        "std": baseline["std"],
                    },
                )

                self.detection_history.append(detection)
                return detection

        except Exception as e:
            logger.debug(f"Statistical anomaly check error: {e}")

        return None

    def _detect_entropy_change(self, source_id: str, data: dict) -> PeripheralDetection | None:
        """Detect significant entropy changes.

        Sudden changes in data distribution may indicate attacks or failures.
        """
        try:
            # Get byte distribution or value distribution
            distribution = data.get("distribution", [])

            if not distribution or len(distribution) < 10:
                return None  # Insufficient data

            # Calculate Shannon entropy
            distribution = np.array(distribution)
            distribution = distribution / distribution.sum()  # Normalize
            entropy = -np.sum(distribution * np.log2(distribution + 1e-10))

            # Track entropy baseline
            entropy_key = f"{source_id}_entropy"
            if entropy_key not in self.baseline_stats:
                self.baseline_stats[entropy_key] = {
                    "values": deque(maxlen=50),
                    "mean": entropy,
                }
                return None

            baseline = self.baseline_stats[entropy_key]
            baseline["values"].append(entropy)
            baseline["mean"] = np.mean(baseline["values"])

            # Detect significant change (>30% deviation)
            if baseline["mean"] > 0:
                deviation = abs(entropy - baseline["mean"]) / baseline["mean"]

                if deviation > 0.30:  # >30% change
                    return PeripheralDetection(
                        target_id=f"{source_id}_entropy",
                        detection_type="entropy_change",
                        confidence=min(deviation / 0.60, 1.0),  # 60% deviation -> confidence=1.0
                        timestamp=time.time(),
                        metadata={
                            "current_entropy": entropy,
                            "baseline_entropy": baseline["mean"],
                            "deviation": deviation,
                        },
                    )

        except Exception as e:
            logger.debug(f"Entropy check error: {e}")

        return None

    def _detect_volume_spike(self, source_id: str, data: dict) -> PeripheralDetection | None:
        """Detect volume spikes (sudden increases in event rate).

        DDoS attacks, port scans, and failures often show volume spikes.
        """
        try:
            count = data.get("event_count", 0)
            time_window = data.get("time_window_seconds", 60)

            # Calculate rate (events per second)
            rate = count / time_window if time_window > 0 else 0

            # Track rate baseline
            rate_key = f"{source_id}_rate"
            if rate_key not in self.baseline_stats:
                self.baseline_stats[rate_key] = {
                    "values": deque(maxlen=100),
                    "mean": rate,
                    "p95": rate,
                }
                return None

            baseline = self.baseline_stats[rate_key]
            baseline["values"].append(rate)
            baseline["mean"] = np.mean(baseline["values"])
            baseline["p95"] = np.percentile(baseline["values"], 95)

            # Detect spike (>5x baseline)
            if baseline["mean"] > 0 and rate > baseline["mean"] * 5:
                return PeripheralDetection(
                    target_id=f"{source_id}_volume",
                    detection_type="volume_spike",
                    confidence=min((rate / baseline["mean"]) / 10.0, 1.0),  # 10x -> confidence=1.0
                    timestamp=time.time(),
                    metadata={
                        "current_rate": rate,
                        "baseline_rate": baseline["mean"],
                        "spike_factor": rate / baseline["mean"],
                    },
                )

        except Exception as e:
            logger.debug(f"Volume spike check error: {e}")

        return None


class FovealAnalyzer:
    """Deep, expensive analysis for high-salience targets.

    Applies full analytical power when peripheral monitor detects
    something worth investigating. Goal: <100ms saccade latency.
    """

    def __init__(self):
        """Initialize foveal analyzer."""
        self.analysis_history = deque(maxlen=500)
        self.total_analyses = 0
        self.total_analysis_time_ms = 0

    async def deep_analyze(self, target: PeripheralDetection, full_data: dict | None = None) -> FovealAnalysis:
        """Perform deep analysis on a high-salience target.

        Args:
            target: Detection from peripheral monitor
            full_data: Complete data for deep analysis (optional)

        Returns:
            FovealAnalysis with detailed findings
        """
        analysis_start = time.time()

        try:
            logger.info(f"Foveal analysis: {target.target_id} ({target.detection_type})")

            # Perform analysis based on detection type
            if target.detection_type == "statistical_anomaly":
                findings = await self._analyze_statistical_anomaly(target, full_data)
            elif target.detection_type == "entropy_change":
                findings = await self._analyze_entropy_change(target, full_data)
            elif target.detection_type == "volume_spike":
                findings = await self._analyze_volume_spike(target, full_data)
            else:
                findings = await self._generic_deep_analysis(target, full_data)

            # Determine threat level from findings
            threat_level = self._assess_threat_level(findings)

            # Generate recommended actions
            actions = self._generate_actions(threat_level, findings)

            analysis_time = (time.time() - analysis_start) * 1000

            analysis = FovealAnalysis(
                target_id=target.target_id,
                threat_level=threat_level,
                confidence=target.confidence,
                findings=findings,
                analysis_time_ms=analysis_time,
                timestamp=time.time(),
                recommended_actions=actions,
            )

            # Track performance
            self.total_analyses += 1
            self.total_analysis_time_ms += analysis_time
            self.analysis_history.append(analysis)

            if analysis_time > 100:
                logger.warning(f"Foveal analysis slow: {analysis_time:.1f}ms (target <100ms)")

            logger.info(f"Foveal complete: {target.target_id} -> {threat_level} ({analysis_time:.1f}ms)")

            return analysis

        except Exception as e:
            logger.error(f"Foveal analysis error: {e}")

            # Return safe fallback
            return FovealAnalysis(
                target_id=target.target_id,
                threat_level="UNKNOWN",
                confidence=0.0,
                findings=[{"error": str(e)}],
                analysis_time_ms=(time.time() - analysis_start) * 1000,
                timestamp=time.time(),
                recommended_actions=["ESCALATE_TO_HUMAN"],
            )

    async def _analyze_statistical_anomaly(self, target: PeripheralDetection, full_data: dict | None) -> list[dict]:
        """Analyze statistical anomaly in detail."""
        findings = []

        z_score = target.metadata.get("z_score", 0)

        findings.append(
            {
                "type": "statistical_deviation",
                "severity": "HIGH" if z_score > 5 else "MEDIUM",
                "details": f"Z-score: {z_score:.2f} (p < 0.001)",
                "value": target.metadata.get("value"),
                "expected_range": f"{target.metadata.get('mean', 0):.2f} ± {target.metadata.get('std', 0):.2f}",
            }
        )

        # Check for attack patterns
        if z_score > 6:
            findings.append(
                {
                    "type": "potential_attack",
                    "severity": "CRITICAL",
                    "details": "Extreme deviation suggests possible attack or critical failure",
                }
            )

        return findings

    async def _analyze_entropy_change(self, target: PeripheralDetection, full_data: dict | None) -> list[dict]:
        """Analyze entropy change in detail."""
        findings = []

        current_entropy = target.metadata.get("current_entropy", 0)
        baseline_entropy = target.metadata.get("baseline_entropy", 0)
        deviation = target.metadata.get("deviation", 0)

        findings.append(
            {
                "type": "entropy_anomaly",
                "severity": "HIGH" if deviation > 0.5 else "MEDIUM",
                "details": f"Entropy changed by {deviation * 100:.1f}%",
                "current": current_entropy,
                "baseline": baseline_entropy,
            }
        )

        # Low entropy might indicate encryption/compression
        if current_entropy < 2.0:
            findings.append(
                {
                    "type": "low_entropy",
                    "severity": "MEDIUM",
                    "details": "Low entropy may indicate encrypted/compressed data or homogeneous traffic",
                }
            )

        # High entropy might indicate randomness (encryption or noise)
        if current_entropy > 7.0:
            findings.append(
                {
                    "type": "high_entropy",
                    "severity": "MEDIUM",
                    "details": "High entropy may indicate encrypted traffic or randomized attacks",
                }
            )

        return findings

    async def _analyze_volume_spike(self, target: PeripheralDetection, full_data: dict | None) -> list[dict]:
        """Analyze volume spike in detail."""
        findings = []

        spike_factor = target.metadata.get("spike_factor", 0)
        current_rate = target.metadata.get("current_rate", 0)

        findings.append(
            {
                "type": "volume_anomaly",
                "severity": "CRITICAL" if spike_factor > 10 else "HIGH",
                "details": f"Traffic volume increased {spike_factor:.1f}x baseline",
                "current_rate": current_rate,
                "spike_factor": spike_factor,
            }
        )

        # Check for DDoS indicators
        if spike_factor > 10:
            findings.append(
                {
                    "type": "ddos_indicator",
                    "severity": "CRITICAL",
                    "details": "Extreme volume spike consistent with DDoS attack",
                }
            )

        return findings

    async def _generic_deep_analysis(self, target: PeripheralDetection, full_data: dict | None) -> list[dict]:
        """Generic deep analysis fallback."""
        return [
            {
                "type": "generic_analysis",
                "severity": "MEDIUM",
                "details": f"Detection: {target.detection_type}",
                "confidence": target.confidence,
            }
        ]

    def _assess_threat_level(self, findings: list[dict]) -> str:
        """Assess overall threat level from findings.

        Returns: 'BENIGN', 'SUSPICIOUS', 'MALICIOUS', 'CRITICAL'
        """
        if not findings:
            return "BENIGN"

        # Count severity levels
        severities = [f.get("severity", "LOW") for f in findings]
        severity_counts = {
            "CRITICAL": severities.count("CRITICAL"),
            "HIGH": severities.count("HIGH"),
            "MEDIUM": severities.count("MEDIUM"),
        }

        # Determine overall threat
        if severity_counts["CRITICAL"] > 0:
            return "CRITICAL"
        if severity_counts["HIGH"] >= 2:
            return "MALICIOUS"
        if severity_counts["HIGH"] >= 1 or severity_counts["MEDIUM"] >= 3:
            return "SUSPICIOUS"
        return "BENIGN"

    def _generate_actions(self, threat_level: str, findings: list[dict]) -> list[str]:
        """Generate recommended actions based on threat level."""
        actions = []

        if threat_level == "CRITICAL":
            actions.extend(
                [
                    "ACTIVATE_INCIDENT_RESPONSE",
                    "ALERT_SECURITY_TEAM",
                    "ENABLE_CIRCUIT_BREAKER",
                    "ISOLATE_AFFECTED_SERVICES",
                ]
            )
        elif threat_level == "MALICIOUS":
            actions.extend(
                [
                    "ALERT_SECURITY_TEAM",
                    "INCREASE_MONITORING",
                    "PREPARE_COUNTERMEASURES",
                ]
            )
        elif threat_level == "SUSPICIOUS":
            actions.extend(["INCREASE_MONITORING", "LOG_DETAILED_EVIDENCE", "NOTIFY_ON_CALL"])
        else:
            actions.append("CONTINUE_MONITORING")

        return actions

    def get_average_analysis_time(self) -> float:
        """Get average foveal analysis time in milliseconds."""
        if self.total_analyses == 0:
            return 0.0
        return self.total_analysis_time_ms / self.total_analyses


class AttentionSystem:
    """Two-tier attention system with peripheral/foveal processing.

    Coordinates lightweight peripheral scanning with deep foveal analysis,
    using salience scoring to allocate attention efficiently.
    """

    def __init__(self, foveal_threshold: float = 0.6, scan_interval: float = 1.0):
        """Initialize attention system.

        Args:
            foveal_threshold: Minimum salience score for foveal analysis
            scan_interval: Peripheral scan interval in seconds
        """
        self.peripheral = PeripheralMonitor(scan_interval_seconds=scan_interval)
        self.foveal = FovealAnalyzer()
        self.salience_scorer = SalienceScorer(foveal_threshold=foveal_threshold)

        self.running = False
        self.attention_log = deque(maxlen=1000)

    async def monitor(
        self,
        data_sources: list[Callable[[], dict]],
        on_critical_finding: Callable[[FovealAnalysis], None] | None = None,
    ):
        """Continuous attention-driven monitoring.

        Args:
            data_sources: List of data source functions
            on_critical_finding: Callback for critical findings
        """
        self.running = True
        logger.info("Attention system started")

        while self.running:
            try:
                # 1. Peripheral scan - broad, fast
                detections = await self.peripheral.scan_all(data_sources)

                logger.debug(f"Peripheral scan: {len(detections)} detections")

                # 2. Score salience for each detection
                scored_targets = []
                for detection in detections:
                    # Convert detection to event format for scorer
                    event = {
                        "id": detection.target_id,
                        "value": detection.confidence,
                        "metric": detection.detection_type,
                        "anomaly_score": detection.confidence,
                    }

                    salience = self.salience_scorer.calculate_salience(event)
                    scored_targets.append((detection, salience))

                # 3. Foveal analysis for high-salience targets
                foveal_analyses = []
                for detection, salience in scored_targets:
                    if salience.requires_foveal:
                        logger.info(f"Foveal saccade: {detection.target_id} (salience={salience.score:.3f})")

                        analysis = await self.foveal.deep_analyze(detection)
                        foveal_analyses.append(analysis)

                        # Log attention event
                        self.attention_log.append(
                            {
                                "timestamp": time.time(),
                                "target": detection.target_id,
                                "salience": salience.score,
                                "threat_level": analysis.threat_level,
                            }
                        )

                        # Callback for critical findings
                        if on_critical_finding and analysis.threat_level == "CRITICAL":
                            on_critical_finding(analysis)

                # 4. Log summary
                if foveal_analyses:
                    critical_count = sum(1 for a in foveal_analyses if a.threat_level == "CRITICAL")
                    logger.info(
                        f"Attention cycle: {len(detections)} detections, "
                        f"{len(foveal_analyses)} foveal analyses, "
                        f"{critical_count} critical findings"
                    )

                # 5. Wait for next scan
                await asyncio.sleep(self.peripheral.scan_interval)

            except Exception as e:
                logger.error(f"Attention system error: {e}", exc_info=True)
                await asyncio.sleep(self.peripheral.scan_interval)

        logger.info("Attention system stopped")

    async def stop(self):
        """Stop the attention system."""
        self.running = False
        logger.info("Attention system stop requested")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get attention system performance statistics."""
        return {
            "peripheral": {"detections_total": len(self.peripheral.detection_history)},
            "foveal": {
                "analyses_total": self.foveal.total_analyses,
                "avg_analysis_time_ms": self.foveal.get_average_analysis_time(),
            },
            "attention": {
                "events_total": len(self.attention_log),
                "top_targets": self.salience_scorer.get_top_salient_targets(10),
            },
        }
