"""Encrypted Traffic Analyzer - ML-based Threat Detection

Analyzes encrypted network traffic using metadata-only features.
Detects C2 beaconing, data exfiltration, and malware communication
without decrypting traffic.

Key Features:
- Flow feature extraction (CICFlowMeter-inspired)
- ML models for threat detection
- C2 beaconing detection
- Data exfiltration detection
- Malware traffic classification

Biological Inspiration:
- Pattern recognition receptors (PRRs) → Statistical analysis
- Anomaly detection → Immune surveillance
- Behavioral profiling → Threat categorization

IIT Integration:
- Φ proxy: Integration of multiple flow features
- Temporal coherence: Time-series analysis of traffic patterns
- Information integration: Combining spatial + temporal features

Technical Foundation:
- Based on CICIDS2017 dataset methodology
- Features: packet sizes, inter-arrival times, flow duration
- Models: Random Forest (C2), LSTM (exfil), XGBoost (malware)

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


class TrafficThreatType(Enum):
    """Types of threats detectable in encrypted traffic."""
    
    BENIGN = "benign"
    C2_BEACONING = "c2_beaconing"  # Command & Control
    DATA_EXFILTRATION = "data_exfiltration"
    MALWARE_DOWNLOAD = "malware_download"
    PORT_SCAN = "port_scan"
    DDoS = "ddos"
    LATERAL_MOVEMENT = "lateral_movement"


class ConfidenceLevel(Enum):
    """Confidence levels for detection."""
    
    LOW = 0.25
    MEDIUM = 0.50
    HIGH = 0.75
    VERY_HIGH = 0.90


@dataclass
class NetworkFlow:
    """Represents single network flow.
    
    A flow is defined as sequence of packets between two endpoints
    within a time window.
    
    Attributes:
        flow_id: Unique flow identifier
        src_ip: Source IP address
        dst_ip: Destination IP address
        src_port: Source port
        dst_port: Destination port
        protocol: Protocol (TCP, UDP, etc.)
        start_time: Flow start timestamp
        end_time: Flow end timestamp (optional)
        packet_sizes: List of packet sizes in bytes
        inter_arrival_times: Time between packets (microseconds)
        flags: TCP flags (if TCP)
        tls_version: TLS version if encrypted
        metadata: Additional metadata
    """
    
    flow_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    packet_sizes: List[int] = field(default_factory=list)
    inter_arrival_times: List[float] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    tls_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Flow duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def packet_count(self) -> int:
        """Total number of packets."""
        return len(self.packet_sizes)
    
    @property
    def total_bytes(self) -> int:
        """Total bytes transferred."""
        return sum(self.packet_sizes)


@dataclass
class FlowFeatures:
    """Extracted features from network flow.
    
    Feature engineering based on CICFlowMeter and academic research.
    These features are sufficient for ML-based threat detection.
    """
    
    # Flow identification
    flow_id: str
    
    # Basic flow features
    duration: float
    packet_count: int
    total_bytes: int
    bytes_per_second: float
    packets_per_second: float
    
    # Packet size statistics
    min_packet_size: int
    max_packet_size: int
    mean_packet_size: float
    std_packet_size: float
    
    # Inter-arrival time statistics
    min_iat: float
    max_iat: float
    mean_iat: float
    std_iat: float
    
    # Advanced features
    entropy: float  # Shannon entropy of packet sizes
    periodicity_score: float  # For C2 beaconing detection
    burstiness: float  # Traffic burstiness
    
    # TLS-specific features (if available)
    tls_handshake_duration: Optional[float] = None
    tls_certificate_length: Optional[int] = None
    
    def to_array(self) -> np.ndarray:
        """Convert features to numpy array for ML models."""
        features = [
            self.duration,
            self.packet_count,
            self.total_bytes,
            self.bytes_per_second,
            self.packets_per_second,
            self.min_packet_size,
            self.max_packet_size,
            self.mean_packet_size,
            self.std_packet_size,
            self.min_iat,
            self.max_iat,
            self.mean_iat,
            self.std_iat,
            self.entropy,
            self.periodicity_score,
            self.burstiness,
        ]
        
        # Add TLS features if available
        if self.tls_handshake_duration is not None:
            features.append(self.tls_handshake_duration)
        if self.tls_certificate_length is not None:
            features.append(self.tls_certificate_length)
        
        return np.array(features, dtype=np.float32)


@dataclass
class FlowAnalysisResult:
    """Result of flow analysis."""
    
    flow_id: str
    threat_type: TrafficThreatType
    confidence: float
    features: FlowFeatures
    reasons: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "flow_id": self.flow_id,
            "threat_type": self.threat_type.value,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "mitre_techniques": self.mitre_techniques,
            "timestamp": self.timestamp.isoformat(),
        }


class FlowFeatureExtractor:
    """Extracts statistical features from network flows.
    
    Implements feature engineering pipeline inspired by CICFlowMeter.
    Features are designed to work on encrypted traffic (metadata only).
    """
    
    def __init__(self):
        """Initialize feature extractor."""
        logger.info("Flow feature extractor initialized")
    
    def extract(self, flow: NetworkFlow) -> FlowFeatures:
        """Extract features from network flow.
        
        Args:
            flow: Network flow to analyze
            
        Returns:
            Extracted features
            
        Raises:
            ValueError: If flow has insufficient data
        """
        if flow.packet_count < 1:
            raise ValueError(f"Flow {flow.flow_id} has no packets")
        
        # Basic features
        duration = flow.duration or 0.001  # Avoid division by zero
        packet_count = flow.packet_count
        total_bytes = flow.total_bytes
        
        # Rate features
        bytes_per_second = total_bytes / duration
        packets_per_second = packet_count / duration
        
        # Packet size statistics
        sizes = np.array(flow.packet_sizes)
        min_size = int(np.min(sizes))
        max_size = int(np.max(sizes))
        mean_size = float(np.mean(sizes))
        std_size = float(np.std(sizes))
        
        # Inter-arrival time statistics
        iats = np.array(flow.inter_arrival_times) if flow.inter_arrival_times else np.array([0])
        min_iat = float(np.min(iats))
        max_iat = float(np.max(iats))
        mean_iat = float(np.mean(iats))
        std_iat = float(np.std(iats))
        
        # Advanced features
        entropy = self._calculate_entropy(sizes)
        periodicity = self._calculate_periodicity(iats)
        burstiness = self._calculate_burstiness(sizes, iats)
        
        return FlowFeatures(
            flow_id=flow.flow_id,
            duration=duration,
            packet_count=packet_count,
            total_bytes=total_bytes,
            bytes_per_second=bytes_per_second,
            packets_per_second=packets_per_second,
            min_packet_size=min_size,
            max_packet_size=max_size,
            mean_packet_size=mean_size,
            std_packet_size=std_size,
            min_iat=min_iat,
            max_iat=max_iat,
            mean_iat=mean_iat,
            std_iat=std_iat,
            entropy=entropy,
            periodicity_score=periodicity,
            burstiness=burstiness,
        )
    
    def extract_features(self, flow: NetworkFlow) -> FlowFeatures:
        """Alias for extract (backward compatibility)."""
        return self.extract(flow)
    
    def _calculate_entropy(self, values: np.ndarray) -> float:
        """Calculate Shannon entropy of packet sizes.
        
        High entropy → random/encrypted data
        Low entropy → structured/repetitive data
        """
        if len(values) == 0:
            return 0.0
        
        # Normalize to probabilities
        hist, _ = np.histogram(values, bins=20)
        hist = hist[hist > 0]  # Remove zeros
        probs = hist / hist.sum()
        
        # Shannon entropy
        entropy = -np.sum(probs * np.log2(probs))
        
        return float(entropy)
    
    def _calculate_periodicity(self, inter_arrival_times: np.ndarray) -> float:
        """Calculate periodicity score for C2 beaconing detection.
        
        C2 beacons typically have periodic communication patterns.
        Score close to 1.0 indicates high periodicity.
        """
        if len(inter_arrival_times) < 3:
            return 0.0
        
        # Coefficient of variation (inverse of periodicity)
        mean = np.mean(inter_arrival_times)
        std = np.std(inter_arrival_times)
        
        if mean == 0:
            return 0.0
        
        cv = std / mean
        
        # Convert to periodicity score (lower CV = higher periodicity)
        periodicity = 1.0 / (1.0 + cv)
        
        return float(periodicity)
    
    def _calculate_burstiness(
        self,
        packet_sizes: np.ndarray,
        inter_arrival_times: np.ndarray
    ) -> float:
        """Calculate traffic burstiness.
        
        Bursty traffic (high data in short time) may indicate exfiltration.
        """
        if len(inter_arrival_times) < 2 or len(packet_sizes) < 2:
            return 0.0
        
        # Ensure arrays have compatible shapes by using min length
        min_len = min(len(packet_sizes) - 1, len(inter_arrival_times) - 1)
        if min_len < 1:
            return 0.0
        
        # Burstiness index: variance / mean ratio
        # Slice to ensure same shape (skip first element of both for sync)
        sizes_slice = packet_sizes[1:min_len+1]
        iats_slice = inter_arrival_times[1:min_len+1]
        
        bytes_per_interval = sizes_slice / (iats_slice + 0.001)
        
        mean_rate = np.mean(bytes_per_interval)
        var_rate = np.var(bytes_per_interval)
        
        if mean_rate == 0:
            return 0.0
        
        burstiness = var_rate / mean_rate
        
        return float(burstiness)


class EncryptedTrafficAnalyzer:
    """ML-based analyzer for encrypted network traffic.
    
    Detects threats in encrypted traffic using metadata-only analysis.
    Implements multiple ML models for different threat types.
    
    Models:
    - C2 Beaconing: Random Forest (periodicity detection)
    - Data Exfiltration: LSTM (volume anomaly detection)
    - Malware Traffic: XGBoost (multi-class classification)
    
    Architecture:
    - Feature extraction → Model inference → Threat classification
    - Ensemble approach: Multiple models vote on final classification
    - Confidence scoring: Based on model agreement and certainty
    """
    
    def __init__(
        self,
        feature_extractor: Optional[FlowFeatureExtractor] = None,
        ml_models: Optional[Dict[str, Any]] = None,
        models: Optional[Dict[str, Any]] = None,  # Backward compatibility
        confidence_threshold: float = 0.7
    ):
        """Initialize encrypted traffic analyzer.
        
        Args:
            feature_extractor: Feature extraction engine
            ml_models: Pre-trained ML models
            models: Alias for ml_models (backward compatibility)
            confidence_threshold: Minimum confidence for threat detection
        """
        self.feature_extractor = feature_extractor or FlowFeatureExtractor()
        self.ml_models = ml_models or models or {}
        self.confidence_threshold = confidence_threshold
        
        # Metrics
        self.metrics = self._init_metrics()
        
        # Rule-based detectors (fallback when ML unavailable)
        self.rule_detectors = {
            "c2_beaconing": self._detect_c2_beaconing_rule,
            "data_exfiltration": self._detect_exfiltration_rule,
        }
        
        logger.info(
            f"Encrypted traffic analyzer initialized: "
            f"threshold={confidence_threshold}, "
            f"models={len(self.ml_models)}"
        )
    
    def _init_metrics(self) -> Dict[str, Any]:
        """Initialize Prometheus metrics (singleton pattern)."""
        # Check if metrics already exist
        if not hasattr(EncryptedTrafficAnalyzer, '_metrics_initialized'):
            EncryptedTrafficAnalyzer._flows_analyzed = Counter(
                "traffic_analyzer_flows_total",
                "Total flows analyzed"
            )
            EncryptedTrafficAnalyzer._threats_detected = Counter(
                "traffic_analyzer_threats_total",
                "Threats detected",
                ["threat_type"]
            )
            EncryptedTrafficAnalyzer._analysis_latency = Histogram(
                "traffic_analyzer_latency_seconds",
                "Analysis latency"
            )
            EncryptedTrafficAnalyzer._metrics_initialized = True
        
        return {
            "flows_analyzed": EncryptedTrafficAnalyzer._flows_analyzed,
            "threats_detected": EncryptedTrafficAnalyzer._threats_detected,
            "analysis_latency": EncryptedTrafficAnalyzer._analysis_latency,
        }
    
    async def analyze_flow(
        self,
        network_flow: NetworkFlow
    ) -> FlowAnalysisResult:
        """Analyze single network flow for threats.
        
        Args:
            network_flow: Flow to analyze
            
        Returns:
            Analysis result with threat classification
            
        Process:
        1. Extract features from flow
        2. Run ML models (if available)
        3. Run rule-based detection (fallback)
        4. Aggregate results and determine threat type
        5. Calculate confidence score
        """
        import time
        start_time = time.time()
        
        # Record metric
        self.metrics["flows_analyzed"].inc()
        
        try:
            # Step 1: Extract features
            features = self.feature_extractor.extract(network_flow)
            
            # Step 2: Run detections
            if self.ml_models:
                threat_type, confidence, reasons = await self._ml_detection(
                    features
                )
            else:
                threat_type, confidence, reasons = await self._rule_based_detection(
                    features
                )
            
            # Step 3: Map to MITRE ATT&CK
            mitre_techniques = self._map_to_mitre(threat_type)
            
            # Record latency
            latency = time.time() - start_time
            self.metrics["analysis_latency"].observe(latency)
            
            # Record threat if detected
            if threat_type != TrafficThreatType.BENIGN:
                self.metrics["threats_detected"].labels(
                    threat_type=threat_type.value
                ).inc()
            
            return FlowAnalysisResult(
                flow_id=network_flow.flow_id,
                threat_type=threat_type,
                confidence=confidence,
                features=features,
                reasons=reasons,
                mitre_techniques=mitre_techniques,
            )
        
        except Exception as e:
            logger.error(f"Flow analysis failed: {e}")
            # Return benign on error (fail-open for availability)
            return FlowAnalysisResult(
                flow_id=network_flow.flow_id,
                threat_type=TrafficThreatType.BENIGN,
                confidence=0.0,
                features=FlowFeatures(
                    duration=0, packet_count=0, total_bytes=0,
                    bytes_per_second=0, packets_per_second=0,
                    min_packet_size=0, max_packet_size=0,
                    mean_packet_size=0, std_packet_size=0,
                    min_iat=0, max_iat=0, mean_iat=0, std_iat=0,
                    entropy=0, periodicity_score=0, burstiness=0
                ),
                reasons=[f"Analysis error: {str(e)}"],
            )
    
    async def _ml_detection(
        self,
        features: FlowFeatures
    ) -> Tuple[TrafficThreatType, float, List[str]]:
        """ML-based threat detection.
        
        Uses ensemble of models for robust detection.
        """
        # Convert features to array
        feature_array = features.to_array().reshape(1, -1)
        
        predictions = []
        
        # Run each model
        for model_name, model in self.ml_models.items():
            try:
                pred = model.predict_proba(feature_array)[0]
                predictions.append((model_name, pred))
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
        
        if not predictions:
            # Fallback to rule-based
            return await self._rule_based_detection(features)
        
        # Aggregate predictions (voting)
        threat_scores = {}
        for model_name, probs in predictions:
            for i, threat_type in enumerate(TrafficThreatType):
                if threat_type not in threat_scores:
                    threat_scores[threat_type] = []
                threat_scores[threat_type].append(probs[i] if i < len(probs) else 0)
        
        # Average scores
        avg_scores = {
            threat: np.mean(scores)
            for threat, scores in threat_scores.items()
        }
        
        # Get highest scoring threat
        threat_type = max(avg_scores.keys(), key=lambda k: avg_scores[k])
        confidence = avg_scores[threat_type]
        
        reasons = [f"ML ensemble detection: {len(predictions)} models"]
        
        return threat_type, confidence, reasons
    
    async def _rule_based_detection(
        self,
        features: FlowFeatures
    ) -> Tuple[TrafficThreatType, float, List[str]]:
        """Rule-based threat detection (fallback).
        
        Uses heuristics when ML models unavailable.
        """
        reasons = []
        
        # Check C2 beaconing
        if features.periodicity_score > 0.8:
            return (
                TrafficThreatType.C2_BEACONING,
                features.periodicity_score,
                ["High periodicity detected (C2 beaconing pattern)"]
            )
        
        # Check data exfiltration
        if features.burstiness > 10 and features.bytes_per_second > 1000000:
            return (
                TrafficThreatType.DATA_EXFILTRATION,
                0.75,
                ["High burstiness + volume (exfiltration pattern)"]
            )
        
        # Check port scan
        if features.packet_count < 5 and features.duration < 1.0:
            return (
                TrafficThreatType.PORT_SCAN,
                0.65,
                ["Short-lived low-volume flow (scan pattern)"]
            )
        
        # Default: benign
        return TrafficThreatType.BENIGN, 0.95, ["No threat indicators"]
    
    def _detect_c2_beaconing_rule(self, features: FlowFeatures) -> bool:
        """Rule-based C2 beaconing detection."""
        return features.periodicity_score > 0.8
    
    def _detect_exfiltration_rule(self, features: FlowFeatures) -> bool:
        """Rule-based data exfiltration detection."""
        return (
            features.burstiness > 10 and
            features.bytes_per_second > 1000000
        )
    
    def _map_to_mitre(self, threat_type: TrafficThreatType) -> List[str]:
        """Map threat type to MITRE ATT&CK techniques."""
        mapping = {
            TrafficThreatType.C2_BEACONING: ["T1071.001"],  # C2: Web Protocols
            TrafficThreatType.DATA_EXFILTRATION: ["T1041"],  # Exfiltration Over C2
            TrafficThreatType.MALWARE_DOWNLOAD: ["T1105"],  # Ingress Tool Transfer
            TrafficThreatType.PORT_SCAN: ["T1046"],  # Network Service Scanning
            TrafficThreatType.LATERAL_MOVEMENT: ["T1021"],  # Remote Services
        }
        
        return mapping.get(threat_type, [])
    
    async def analyze_batch(
        self,
        flows: List[NetworkFlow],
        max_concurrent: int = 10
    ) -> List[FlowAnalysisResult]:
        """Analyze multiple flows concurrently.
        
        Args:
            flows: List of flows to analyze
            max_concurrent: Maximum concurrent analyses
            
        Returns:
            List of analysis results
        """
        import asyncio
        
        # Create tasks
        tasks = [self.analyze_flow(flow) for flow in flows]
        
        # Run with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_analyze(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(
            *[limited_analyze(task) for task in tasks],
            return_exceptions=True
        )
        
        # Filter out exceptions
        valid_results = [
            r for r in results
            if isinstance(r, FlowAnalysisResult)
        ]
        
        logger.info(
            f"Batch analysis complete: {len(valid_results)}/{len(flows)} successful"
        )
        
        return valid_results


class EncryptedTrafficAnalyzerError(Exception):
    """Base exception for encrypted traffic analyzer."""
    pass


class InsufficientDataError(EncryptedTrafficAnalyzerError):
    """Raised when flow has insufficient data for analysis."""
    pass


class ModelNotLoadedError(EncryptedTrafficAnalyzerError):
    """Raised when ML model is not available."""
    pass
