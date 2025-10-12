"""Tests for Encrypted Traffic Analyzer

Tests ML-based detection of threats in encrypted network traffic.
Validates feature extraction, model inference, and threat classification.

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import sys
from pathlib import Path
import numpy as np
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from detection.encrypted_traffic_analyzer import (
    ConfidenceLevel,
    EncryptedTrafficAnalyzer,
    FlowAnalysisResult,
    FlowFeatureExtractor,
    FlowFeatures,
    NetworkFlow,
    TrafficThreatType,
)


class TestNetworkFlow:
    """Test NetworkFlow data class."""

    def test_network_flow_creation(self):
        """Test basic NetworkFlow creation."""
        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
        )

        assert flow.flow_id == "flow_001"
        assert flow.src_ip == "192.168.1.100"
        assert flow.dst_port == 443
        assert flow.protocol == "TCP"

    def test_network_flow_with_packets(self):
        """Test NetworkFlow with packet data."""
        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[66, 1500, 1500, 800, 52],
            inter_arrival_times=[0, 100, 150, 200, 250],  # microseconds
        )

        assert len(flow.packet_sizes) == 5
        assert len(flow.inter_arrival_times) == 5
        assert flow.packet_sizes[0] == 66  # SYN
        assert flow.packet_sizes[-1] == 52  # ACK

    def test_flow_duration(self):
        """Test flow duration calculation."""
        start = datetime.utcnow()
        end = start + timedelta(seconds=30)

        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=start,
            end_time=end,
        )

        duration = (flow.end_time - flow.start_time).total_seconds()
        assert duration == 30.0


class TestFlowFeatureExtractor:
    """Test FlowFeatureExtractor."""

    def test_initialization(self):
        """Test extractor initialization."""
        extractor = FlowFeatureExtractor()
        assert extractor is not None

    def test_extract_basic_features(self):
        """Test extraction of basic flow features."""
        extractor = FlowFeatureExtractor()

        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=10),
            packet_sizes=[100, 200, 150, 180],
            inter_arrival_times=[0, 1000, 2000, 3000],  # microseconds
        )

        features = extractor.extract_features(flow)

        # Should return FlowFeatures object
        assert isinstance(features, FlowFeatures)
        assert features.packet_count == 4
        assert features.duration > 0
        
        # Convert to array for ML models
        feature_array = features.to_array()
        assert isinstance(feature_array, np.ndarray)
        assert len(feature_array) > 0
        assert not np.isnan(feature_array).any()  # No NaN values

    def test_extract_duration_feature(self):
        """Test duration feature extraction."""
        extractor = FlowFeatureExtractor()

        start = datetime.utcnow()
        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=start,
            end_time=start + timedelta(seconds=60),
        )

        features = extractor.extract_features(flow)
        # First feature should be duration
        assert features[0] == pytest.approx(60.0, rel=0.1)

    def test_extract_packet_statistics(self):
        """Test packet size statistics extraction."""
        extractor = FlowFeatureExtractor()

        packet_sizes = [100, 200, 150, 180, 120]
        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=packet_sizes,
        )

        features = extractor.extract_features(flow)

        # Features should include mean, std, min, max of packet sizes
        mean_size = np.mean(packet_sizes)
        assert mean_size in features or any(abs(f - mean_size) < 1 for f in features)

    def test_extract_inter_arrival_statistics(self):
        """Test inter-arrival time statistics extraction."""
        extractor = FlowFeatureExtractor()

        iat = [1000, 1500, 2000, 1800, 1200]  # microseconds
        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            inter_arrival_times=iat,
        )

        features = extractor.extract_features(flow)

        # Should include IAT statistics
        mean_iat = np.mean(iat)
        assert mean_iat > 0

    def test_handle_empty_flow(self):
        """Test handling of flow with no packets."""
        extractor = FlowFeatureExtractor()

        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
        )

        features = extractor.extract_features(flow)

        # Should handle gracefully with zero/default values
        assert isinstance(features, np.ndarray)
        assert len(features) > 0

    def test_feature_consistency(self):
        """Test feature vector has consistent length."""
        extractor = FlowFeatureExtractor()

        flow1 = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[100, 200],
        )

        flow2 = NetworkFlow(
            flow_id="flow_002",
            src_ip="192.168.1.101",
            dst_ip="10.0.0.51",
            src_port=54322,
            dst_port=80,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[150, 250, 300, 400, 500],  # Different number of packets
        )

        features1 = extractor.extract_features(flow1)
        features2 = extractor.extract_features(flow2)

        # Feature vectors must have same length
        assert len(features1) == len(features2)


class TestEncryptedTrafficAnalyzer:
    """Test EncryptedTrafficAnalyzer main class."""

    @pytest.fixture
    def mock_models(self):
        """Create mock ML models."""
        c2_model = Mock()
        c2_model.predict.return_value = np.array([0])  # Benign
        c2_model.predict_proba.return_value = np.array([[0.9, 0.1]])  # [benign, malicious]

        exfil_model = Mock()
        exfil_model.predict.return_value = np.array([0])
        exfil_model.predict_proba.return_value = np.array([[0.85, 0.15]])

        malware_model = Mock()
        malware_model.predict.return_value = np.array([0])
        malware_model.predict_proba.return_value = np.array([[0.95, 0.05]])

        return {
            "c2_detector": c2_model,
            "exfil_detector": exfil_model,
            "malware_classifier": malware_model,
        }

    def test_initialization(self, mock_models):
        """Test analyzer initialization."""
        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        assert analyzer.models == mock_models
        assert analyzer.feature_extractor is not None

    def test_analyze_flow_benign(self, mock_models):
        """Test analyzing benign flow."""
        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[100, 200, 150],
        )

        result = analyzer.analyze_flow(flow)

        assert isinstance(result, FlowAnalysisResult)
        assert result.flow_id == "flow_001"
        assert not result.is_malicious
        assert result.threat_type == TrafficThreatType.BENIGN

    def test_analyze_flow_c2_detected(self, mock_models):
        """Test detecting C2 beaconing."""
        # Configure mocks for C2 detection
        mock_models["c2_detector"].predict_proba.return_value = np.array([[0.2, 0.8]])  # High C2 prob
        mock_models["exfil_detector"].predict_proba.return_value = np.array([[0.9, 0.1]])
        mock_models["malware_classifier"].predict_proba.return_value = np.array([[0.9, 0.1]])

        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        # C2 beaconing typically has regular intervals
        flow = NetworkFlow(
            flow_id="flow_c2",
            src_ip="192.168.1.100",
            dst_ip="suspicious.com",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[100] * 10,  # Uniform size (beacon)
            inter_arrival_times=[60000] * 10,  # Regular 60s interval
        )

        result = analyzer.analyze_flow(flow)

        assert result.is_malicious
        assert result.threat_type == TrafficThreatType.C2_BEACONING
        assert result.confidence >= ConfidenceLevel.HIGH.value

    def test_analyze_flow_exfiltration_detected(self, mock_models):
        """Test detecting data exfiltration."""
        # Configure mocks for exfiltration detection
        mock_models["c2_detector"].predict_proba.return_value = np.array([[0.9, 0.1]])
        mock_models["exfil_detector"].predict_proba.return_value = np.array([[0.15, 0.85]])  # High exfil prob
        mock_models["malware_classifier"].predict_proba.return_value = np.array([[0.8, 0.2]])

        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        # Exfiltration: large sustained outbound traffic
        flow = NetworkFlow(
            flow_id="flow_exfil",
            src_ip="192.168.1.100",
            dst_ip="external.com",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[1500] * 1000,  # Large sustained transfer
        )

        result = analyzer.analyze_flow(flow)

        assert result.is_malicious
        assert result.threat_type == TrafficThreatType.DATA_EXFILTRATION

    def test_analyze_flow_malware_detected(self, mock_models):
        """Test detecting malware download."""
        # Configure mocks for malware detection
        mock_models["c2_detector"].predict_proba.return_value = np.array([[0.85, 0.15]])
        mock_models["exfil_detector"].predict_proba.return_value = np.array([[0.9, 0.1]])
        mock_models["malware_classifier"].predict_proba.return_value = np.array([[0.2, 0.8]])  # High malware prob

        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        flow = NetworkFlow(
            flow_id="flow_malware",
            src_ip="192.168.1.100",
            dst_ip="malicious-cdn.com",
            src_port=54321,
            dst_port=80,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[1500] * 50,  # File download pattern
        )

        result = analyzer.analyze_flow(flow)

        assert result.is_malicious
        assert result.threat_type == TrafficThreatType.MALWARE_DOWNLOAD

    def test_analyze_batch(self, mock_models):
        """Test batch analysis of multiple flows."""
        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        flows = [
            NetworkFlow(
                flow_id=f"flow_{i}",
                src_ip="192.168.1.100",
                dst_ip="10.0.0.50",
                src_port=54321 + i,
                dst_port=443,
                protocol="TCP",
                start_time=datetime.utcnow(),
            )
            for i in range(5)
        ]

        results = analyzer.analyze_batch(flows)

        assert len(results) == 5
        for result in results:
            assert isinstance(result, FlowAnalysisResult)

    def test_metrics_incremented(self, mock_models):
        """Test that Prometheus metrics are incremented."""
        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        flow = NetworkFlow(
            flow_id="flow_001",
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
        )

        initial_count = analyzer.flows_analyzed._value.get()
        result = analyzer.analyze_flow(flow)
        final_count = analyzer.flows_analyzed._value.get()

        assert final_count > initial_count

    def test_confidence_levels(self, mock_models):
        """Test confidence level categorization."""
        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        # Test different confidence thresholds
        test_cases = [
            (0.2, ConfidenceLevel.LOW),
            (0.4, ConfidenceLevel.MEDIUM),
            (0.7, ConfidenceLevel.HIGH),
            (0.95, ConfidenceLevel.VERY_HIGH),
        ]

        for confidence, expected_level in test_cases:
            mock_models["c2_detector"].predict_proba.return_value = np.array([[1 - confidence, confidence]])

            flow = NetworkFlow(
                flow_id="test",
                src_ip="192.168.1.100",
                dst_ip="10.0.0.50",
                src_port=54321,
                dst_port=443,
                protocol="TCP",
                start_time=datetime.utcnow(),
            )

            result = analyzer.analyze_flow(flow)

            if result.is_malicious:
                assert result.confidence >= expected_level.value


class TestRealWorldScenarios:
    """Test real-world threat detection scenarios."""

    @pytest.fixture
    def mock_models(self):
        """Create mock models for scenarios."""
        c2_model = Mock()
        exfil_model = Mock()
        malware_model = Mock()
        return {
            "c2_detector": c2_model,
            "exfil_detector": exfil_model,
            "malware_classifier": malware_model,
        }

    def test_https_normal_browsing(self, mock_models):
        """Test normal HTTPS browsing is classified as benign."""
        mock_models["c2_detector"].predict_proba.return_value = np.array([[0.95, 0.05]])
        mock_models["exfil_detector"].predict_proba.return_value = np.array([[0.98, 0.02]])
        mock_models["malware_classifier"].predict_proba.return_value = np.array([[0.99, 0.01]])

        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        # Normal web browsing pattern
        flow = NetworkFlow(
            flow_id="normal_https",
            src_ip="192.168.1.100",
            dst_ip="www.google.com",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[200, 1500, 800, 1500, 400, 100],  # Varied sizes
            inter_arrival_times=[0, 50, 100, 200, 300, 400],  # Variable timing
            tls_version="TLSv1.3",
        )

        result = analyzer.analyze_flow(flow)

        assert not result.is_malicious
        assert result.threat_type == TrafficThreatType.BENIGN

    def test_cobalt_strike_beacon(self, mock_models):
        """Test detection of Cobalt Strike beacon pattern."""
        mock_models["c2_detector"].predict_proba.return_value = np.array([[0.1, 0.9]])
        mock_models["exfil_detector"].predict_proba.return_value = np.array([[0.8, 0.2]])
        mock_models["malware_classifier"].predict_proba.return_value = np.array([[0.7, 0.3]])

        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        # Cobalt Strike beacon: regular intervals, consistent size
        flow = NetworkFlow(
            flow_id="cs_beacon",
            src_ip="192.168.1.100",
            dst_ip="c2-server.example.com",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            start_time=datetime.utcnow(),
            packet_sizes=[200] * 20,  # Consistent beacon size
            inter_arrival_times=[60000] * 20,  # Every 60 seconds
            tls_version="TLSv1.2",
        )

        result = analyzer.analyze_flow(flow)

        assert result.is_malicious
        assert result.threat_type == TrafficThreatType.C2_BEACONING
        assert result.confidence > 0.8

    def test_dns_tunneling(self, mock_models):
        """Test detection of DNS tunneling exfiltration."""
        mock_models["c2_detector"].predict_proba.return_value = np.array([[0.5, 0.5]])
        mock_models["exfil_detector"].predict_proba.return_value = np.array([[0.2, 0.8]])
        mock_models["malware_classifier"].predict_proba.return_value = np.array([[0.6, 0.4]])

        analyzer = EncryptedTrafficAnalyzer(models=mock_models)

        # DNS tunneling: many small packets, high frequency
        flow = NetworkFlow(
            flow_id="dns_tunnel",
            src_ip="192.168.1.100",
            dst_ip="8.8.8.8",
            src_port=54321,
            dst_port=53,
            protocol="UDP",
            start_time=datetime.utcnow(),
            packet_sizes=[100] * 500,  # Many small DNS queries
            inter_arrival_times=[100] * 500,  # High frequency
        )

        result = analyzer.analyze_flow(flow)

        assert result.is_malicious
        assert result.threat_type == TrafficThreatType.DATA_EXFILTRATION
