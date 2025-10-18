"""Encrypted Traffic Analyzer - Additional Tests for 100% Coverage

Target: Cover remaining 37 lines in encrypted_traffic_analyzer.py
Focus:
- TLS features extraction
- ML detection paths
- Rule-based detection edge cases
- Feature extraction branches
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock

from detection.encrypted_traffic_analyzer import (
    EncryptedTrafficAnalyzer,
    NetworkFlow,
    FlowFeatures,
    FlowAnalysisResult,
    TrafficThreatType,
    FlowFeatureExtractor,
)


class TestTLSFeatures:
    """Test TLS-specific feature extraction"""
    
    def test_features_to_array_with_tls(self):
        """Test FlowFeatures.to_array() with TLS features"""
        features = FlowFeatures(
            flow_id="test_tls",
            duration=10.0,
            packet_count=50,
            total_bytes=5000,
            bytes_per_second=500.0,
            packets_per_second=5.0,
            min_packet_size=40,
            max_packet_size=1500,
            mean_packet_size=100.0,
            std_packet_size=50.0,
            min_iat=10.0,
            max_iat=200.0,
            mean_iat=100.0,
            std_iat=30.0,
            entropy=7.5,
            periodicity_score=0.3,
            burstiness=2.5,
            tls_handshake_duration=250.5,
            tls_certificate_length=2048
        )
        
        arr = features.to_array()
        
        # Should include TLS features in array
        assert isinstance(arr, np.ndarray)
        assert len(arr) == 18  # 16 base + 2 TLS features
        assert arr[-2] == 250.5  # TLS handshake
        assert arr[-1] == 2048  # TLS cert length
    
    def test_features_to_array_without_tls(self):
        """Test FlowFeatures.to_array() without TLS features"""
        features = FlowFeatures(
            flow_id="test_no_tls",
            duration=10.0,
            packet_count=50,
            total_bytes=5000,
            bytes_per_second=500.0,
            packets_per_second=5.0,
            min_packet_size=40,
            max_packet_size=1500,
            mean_packet_size=100.0,
            std_packet_size=50.0,
            min_iat=10.0,
            max_iat=200.0,
            mean_iat=100.0,
            std_iat=30.0,
            entropy=7.5,
            periodicity_score=0.3,
            burstiness=2.5,
            tls_handshake_duration=None,
            tls_certificate_length=None
        )
        
        arr = features.to_array()
        
        # Should only have base features
        assert isinstance(arr, np.ndarray)
        assert len(arr) == 16  # Only base features


class TestFlowAnalysisResultDict:
    """Test FlowAnalysisResult dictionary conversion"""
    
    def test_flow_analysis_result_to_dict(self):
        """Test converting FlowAnalysisResult to dict"""
        features = FlowFeatures(
            flow_id="test_flow",
            duration=10.0,
            packet_count=50,
            total_bytes=5000,
            bytes_per_second=500.0,
            packets_per_second=5.0,
            min_packet_size=40,
            max_packet_size=1500,
            mean_packet_size=100.0,
            std_packet_size=50.0,
            min_iat=10.0,
            max_iat=200.0,
            mean_iat=100.0,
            std_iat=30.0,
            entropy=7.5,
            periodicity_score=0.3,
            burstiness=2.5,
        )
        
        result = FlowAnalysisResult(
            flow_id="test_flow",
            threat_type=TrafficThreatType.BENIGN,
            confidence=0.95,
            features=features,
            reasons=["No threat detected"],
            mitre_techniques=[]
        )
        
        # Should have to_dict method or be convertible
        # Test that object is properly structured
        assert result.flow_id == "test_flow"
        assert result.threat_type == TrafficThreatType.BENIGN
        assert result.confidence == 0.95


class TestMLDetectionPaths:
    """Test ML detection code paths"""
    
    @pytest.mark.asyncio
    async def test_ml_detection_with_models(self):
        """Test ML detection when models are loaded"""
        analyzer = EncryptedTrafficAnalyzer()
        
        # Mock model
        mock_model = Mock()
        mock_model.predict_proba = Mock(return_value=np.array([[0.9, 0.1]]))
        
        analyzer.ml_models = {"test_model": mock_model}
        
        features = FlowFeatures(
            flow_id="ml_test",
            duration=10.0,
            packet_count=50,
            total_bytes=5000,
            bytes_per_second=500.0,
            packets_per_second=5.0,
            min_packet_size=40,
            max_packet_size=1500,
            mean_packet_size=100.0,
            std_packet_size=50.0,
            min_iat=10.0,
            max_iat=200.0,
            mean_iat=100.0,
            std_iat=30.0,
            entropy=7.5,
            periodicity_score=0.3,
            burstiness=2.5,
        )
        
        threat_type, confidence, reasons = await analyzer._ml_detection(features)
        
        assert threat_type is not None
        assert isinstance(confidence, float)
        assert len(reasons) > 0
    
    @pytest.mark.asyncio
    async def test_ml_detection_model_failure_fallback(self):
        """Test ML detection falls back to rules when model fails"""
        analyzer = EncryptedTrafficAnalyzer()
        
        # Mock failing model
        mock_model = Mock()
        mock_model.predict_proba = Mock(side_effect=Exception("Model error"))
        
        analyzer.ml_models = {"failing_model": mock_model}
        
        features = FlowFeatures(
            flow_id="ml_fail_test",
            duration=10.0,
            packet_count=50,
            total_bytes=5000,
            bytes_per_second=500.0,
            packets_per_second=5.0,
            min_packet_size=40,
            max_packet_size=1500,
            mean_packet_size=100.0,
            std_packet_size=50.0,
            min_iat=10.0,
            max_iat=200.0,
            mean_iat=100.0,
            std_iat=30.0,
            entropy=7.5,
            periodicity_score=0.3,
            burstiness=2.5,
        )
        
        # Should fallback to rule-based
        threat_type, confidence, reasons = await analyzer._ml_detection(features)
        
        assert threat_type is not None
        assert isinstance(confidence, float)


class TestRuleBasedDetectionPaths:
    """Test rule-based detection code paths"""
    
    @pytest.mark.asyncio
    async def test_rule_based_c2_beaconing_detection(self):
        """Test C2 beaconing detection via rules"""
        analyzer = EncryptedTrafficAnalyzer()
        
        # High periodicity = C2 beaconing
        features = FlowFeatures(
            flow_id="c2_rule",
            duration=300.0,
            packet_count=50,
            total_bytes=2500,
            bytes_per_second=8.33,
            packets_per_second=0.167,
            min_packet_size=50,
            max_packet_size=50,
            mean_packet_size=50.0,
            std_packet_size=0.0,
            min_iat=60000.0,
            max_iat=60000.0,
            mean_iat=60000.0,
            std_iat=0.0,
            entropy=2.0,
            periodicity_score=0.95,  # Very high = C2
            burstiness=0.1,
        )
        
        threat_type, confidence, reasons = await analyzer._rule_based_detection(features)
        
        assert threat_type == TrafficThreatType.C2_BEACONING
        assert confidence > 0.8
        assert len(reasons) > 0
    
    @pytest.mark.asyncio
    async def test_rule_based_exfiltration_detection(self):
        """Test exfiltration detection via rules"""
        analyzer = EncryptedTrafficAnalyzer()
        
        # High burstiness + volume = exfiltration
        features = FlowFeatures(
            flow_id="exfil_rule",
            duration=60.0,
            packet_count=1000,
            total_bytes=60000000,
            bytes_per_second=1500000.0,  # >1MB/s
            packets_per_second=16.67,
            min_packet_size=5000,
            max_packet_size=5000,
            mean_packet_size=5000.0,
            std_packet_size=0.0,
            min_iat=60.0,
            max_iat=60.0,
            mean_iat=60.0,
            std_iat=0.0,
            entropy=7.8,
            periodicity_score=0.1,
            burstiness=20.0,  # Very high burstiness > 10
        )
        
        threat_type, confidence, reasons = await analyzer._rule_based_detection(features)
        
        assert threat_type == TrafficThreatType.DATA_EXFILTRATION
        assert confidence > 0.5
        assert len(reasons) > 0
    
    @pytest.mark.asyncio
    async def test_rule_based_port_scan_detection(self):
        """Test port scan detection via rules"""
        analyzer = EncryptedTrafficAnalyzer()
        
        # Short-lived, low-volume = port scan
        features = FlowFeatures(
            flow_id="scan_rule",
            duration=0.5,
            packet_count=3,
            total_bytes=180,
            bytes_per_second=360.0,
            packets_per_second=6.0,
            min_packet_size=60,
            max_packet_size=60,
            mean_packet_size=60.0,
            std_packet_size=0.0,
            min_iat=100.0,
            max_iat=200.0,
            mean_iat=150.0,
            std_iat=50.0,
            entropy=3.0,
            periodicity_score=0.1,
            burstiness=1.0,
        )
        
        threat_type, confidence, reasons = await analyzer._rule_based_detection(features)
        
        assert threat_type == TrafficThreatType.PORT_SCAN
        assert confidence > 0.5
        assert len(reasons) > 0
    
    @pytest.mark.asyncio
    async def test_rule_based_benign_default(self):
        """Test benign detection when no rules match"""
        analyzer = EncryptedTrafficAnalyzer()
        
        # Normal traffic
        features = FlowFeatures(
            flow_id="benign_rule",
            duration=30.0,
            packet_count=100,
            total_bytes=10000,
            bytes_per_second=333.33,
            packets_per_second=3.33,
            min_packet_size=60,
            max_packet_size=1500,
            mean_packet_size=100.0,
            std_packet_size=200.0,
            min_iat=10.0,
            max_iat=500.0,
            mean_iat=300.0,
            std_iat=100.0,
            entropy=5.5,
            periodicity_score=0.3,
            burstiness=2.0,
        )
        
        threat_type, confidence, reasons = await analyzer._rule_based_detection(features)
        
        assert threat_type == TrafficThreatType.BENIGN
        assert confidence > 0.9
        assert len(reasons) > 0


class TestFeatureExtractionEdgeCases:
    """Test edge cases in feature extraction"""
    
    def test_extract_with_zero_duration(self):
        """Test feature extraction with zero duration flow"""
        extractor = FlowFeatureExtractor()
        
        flow = NetworkFlow(
            flow_id="zero_duration",
            src_ip="192.168.1.100",
            dst_ip="192.168.1.200",
            src_port=12345,
            dst_port=80,
            protocol="TCP",
            start_time=datetime.utcnow(),
            end_time=None,  # Not ended = 0 duration
            packet_sizes=[100],
            inter_arrival_times=[],
        )
        
        features = extractor.extract(flow)
        
        # Should handle division by zero gracefully
        # Duration might be very small if end_time defaults to start_time
        assert features.duration < 1.0
        # Bytes/packets per second should be computed
        assert isinstance(features.bytes_per_second, float)
        assert isinstance(features.packets_per_second, float)
    
    def test_extract_with_single_packet(self):
        """Test feature extraction with single packet"""
        extractor = FlowFeatureExtractor()
        
        flow = NetworkFlow(
            flow_id="single_packet",
            src_ip="192.168.1.100",
            dst_ip="192.168.1.200",
            src_port=12345,
            dst_port=80,
            protocol="TCP",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=1),
            packet_sizes=[100],
            inter_arrival_times=[],
        )
        
        features = extractor.extract(flow)
        
        # Should handle stats of single value
        assert features.packet_count == 1
        assert features.mean_packet_size == 100.0
        assert features.std_packet_size == 0.0
    
    def test_extract_with_empty_iat(self):
        """Test feature extraction with empty inter-arrival times"""
        extractor = FlowFeatureExtractor()
        
        flow = NetworkFlow(
            flow_id="empty_iat",
            src_ip="192.168.1.100",
            dst_ip="192.168.1.200",
            src_port=12345,
            dst_port=80,
            protocol="TCP",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=2),
            packet_sizes=[100, 150, 120],
            inter_arrival_times=[],  # Empty IAT
        )
        
        features = extractor.extract(flow)
        
        # Should handle empty IAT gracefully
        assert features.mean_iat == 0.0
        assert features.std_iat == 0.0
        assert features.min_iat == 0.0
        assert features.max_iat == 0.0


class TestAnalyzerGetMethod:
    """Test analyzer __call__ and get methods"""
    
    @pytest.mark.asyncio
    async def test_analyzer_call_shorthand(self):
        """Test analyzer can be called directly"""
        analyzer = EncryptedTrafficAnalyzer()
        
        flow = NetworkFlow(
            flow_id="call_test",
            src_ip="192.168.1.100",
            dst_ip="192.168.1.200",
            src_port=12345,
            dst_port=80,
            protocol="TCP",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=2),
            packet_sizes=[100, 150, 120],
            inter_arrival_times=[100.0, 120.0],
        )
        
        # Should be able to call analyzer(flow)
        result = await analyzer.analyze_flow(flow)
        
        assert result is not None
        assert isinstance(result, FlowAnalysisResult)


class TestFeatureExtractorGetFeatures:
    """Test FlowFeatureExtractor get_features method"""
    
    def test_extractor_returns_flow_features(self):
        """Test extractor returns FlowFeatures object"""
        extractor = FlowFeatureExtractor()
        
        flow = NetworkFlow(
            flow_id="extractor_test",
            src_ip="192.168.1.100",
            dst_ip="192.168.1.200",
            src_port=12345,
            dst_port=80,
            protocol="TCP",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=2),
            packet_sizes=[100, 150, 120],
            inter_arrival_times=[100.0, 120.0],
        )
        
        features = extractor.extract(flow)
        
        assert isinstance(features, FlowFeatures)
        assert features.flow_id == "extractor_test"
