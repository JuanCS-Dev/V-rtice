"""
Intrusion Detection System Tests - MAXIMUS Vértice

Validates AI-driven IDS capabilities including:
- Network traffic analysis
- Anomaly detection
- Pattern matching
- Real-time alerting

Test Coverage:
- Traffic parsing and feature extraction
- ML model predictions
- Alert generation
- Integration with SIEM
"""

import pytest
from datetime import datetime
from typing import Dict, List
import asyncio

from backend.security.ids import (
    IntrusionDetectionSystem,
    NetworkPacket,
    IDSAlert,
    AlertSeverity,
    TrafficAnalyzer,
    AnomalyDetector
)


class TestNetworkPacket:
    """Test NetworkPacket data structure."""
    
    def test_packet_creation(self):
        """Test basic packet creation and attributes."""
        packet = NetworkPacket(
            timestamp=datetime.now(),
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            payload_size=1024,
            flags=["SYN"],
            payload=b"test payload"
        )
        
        assert packet.src_ip == "192.168.1.100"
        assert packet.dst_ip == "10.0.0.50"
        assert packet.protocol == "TCP"
        assert packet.payload_size == 1024
        assert "SYN" in packet.flags
    
    def test_packet_validation(self):
        """Test packet validation logic."""
        with pytest.raises(ValueError):
            NetworkPacket(
                timestamp=datetime.now(),
                src_ip="invalid_ip",
                dst_ip="10.0.0.50",
                src_port=54321,
                dst_port=443,
                protocol="TCP",
                payload_size=1024
            )
    
    def test_packet_serialization(self):
        """Test packet to dict conversion."""
        packet = NetworkPacket(
            timestamp=datetime.now(),
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            payload_size=1024
        )
        
        data = packet.to_dict()
        assert data["src_ip"] == "192.168.1.100"
        assert data["protocol"] == "TCP"
        assert isinstance(data["timestamp"], str)


class TestTrafficAnalyzer:
    """Test traffic analysis capabilities."""
    
    @pytest.fixture
    def analyzer(self):
        """Create TrafficAnalyzer instance."""
        return TrafficAnalyzer()
    
    @pytest.fixture
    def sample_packets(self) -> List[NetworkPacket]:
        """Generate sample network packets."""
        packets = []
        base_time = datetime.now()
        
        for i in range(10):
            packet = NetworkPacket(
                timestamp=base_time,
                src_ip=f"192.168.1.{100+i}",
                dst_ip="10.0.0.50",
                src_port=50000 + i,
                dst_port=443,
                protocol="TCP",
                payload_size=512 + i * 100
            )
            packets.append(packet)
        
        return packets
    
    def test_extract_features(self, analyzer, sample_packets):
        """Test feature extraction from packets."""
        packet = sample_packets[0]
        features = analyzer.extract_features(packet)
        
        assert "src_ip_encoded" in features
        assert "dst_port" in features
        assert "payload_size" in features
        assert "protocol_encoded" in features
        assert isinstance(features["payload_size"], (int, float))
    
    def test_analyze_traffic_flow(self, analyzer, sample_packets):
        """Test traffic flow analysis."""
        flow_stats = analyzer.analyze_flow(sample_packets)
        
        assert "total_packets" in flow_stats
        assert "unique_sources" in flow_stats
        assert "avg_packet_size" in flow_stats
        assert flow_stats["total_packets"] == len(sample_packets)
        assert flow_stats["unique_sources"] > 0
    
    def test_detect_port_scan(self, analyzer):
        """Test port scanning detection."""
        # Simulate port scan: same source, multiple destination ports
        scan_packets = []
        base_time = datetime.now()
        
        for port in range(20, 100):
            packet = NetworkPacket(
                timestamp=base_time,
                src_ip="192.168.1.100",
                dst_ip="10.0.0.50",
                src_port=54321,
                dst_port=port,
                protocol="TCP",
                payload_size=64,
                flags=["SYN"]
            )
            scan_packets.append(packet)
        
        is_scan = analyzer.detect_port_scan(scan_packets)
        assert is_scan is True
    
    def test_detect_ddos_pattern(self, analyzer):
        """Test DDoS pattern detection."""
        # Simulate DDoS: multiple sources, same destination, high rate
        ddos_packets = []
        base_time = datetime.now()
        
        for i in range(1000):
            packet = NetworkPacket(
                timestamp=base_time,
                src_ip=f"192.168.{i//256}.{i%256}",
                dst_ip="10.0.0.50",
                src_port=50000 + (i % 10000),
                dst_port=80,
                protocol="TCP",
                payload_size=512
            )
            ddos_packets.append(packet)
        
        is_ddos = analyzer.detect_ddos_pattern(ddos_packets, time_window=1.0)
        assert is_ddos is True


class TestAnomalyDetector:
    """Test ML-based anomaly detection."""
    
    @pytest.fixture
    def detector(self):
        """Create AnomalyDetector instance."""
        return AnomalyDetector(model_type="isolation_forest")
    
    @pytest.fixture
    def training_data(self) -> List[Dict]:
        """Generate normal traffic for training."""
        data = []
        for i in range(100):
            features = {
                "packet_size": 500 + (i % 100),
                "packets_per_second": 10 + (i % 5),
                "unique_ports": 2 + (i % 3),
                "protocol_distribution": 0.8 + (i % 10) * 0.01
            }
            data.append(features)
        return data
    
    @pytest.fixture
    def anomalous_data(self) -> List[Dict]:
        """Generate anomalous traffic patterns."""
        data = []
        for i in range(10):
            features = {
                "packet_size": 10000 + i * 1000,  # Unusually large
                "packets_per_second": 1000 + i * 100,  # Unusually high rate
                "unique_ports": 100 + i * 10,  # Port scanning
                "protocol_distribution": 0.1  # Unusual protocol mix
            }
            data.append(features)
        return data
    
    def test_train_model(self, detector, training_data):
        """Test model training on normal traffic."""
        detector.train(training_data)
        assert detector.is_trained is True
        assert detector.model is not None
    
    def test_detect_anomaly(self, detector, training_data, anomalous_data):
        """Test anomaly detection after training."""
        detector.train(training_data)
        
        # Normal traffic should not be flagged
        normal_sample = training_data[0]
        is_anomaly, score = detector.predict(normal_sample)
        assert is_anomaly is False
        
        # Anomalous traffic should be flagged
        anomalous_sample = anomalous_data[0]
        is_anomaly, score = detector.predict(anomalous_sample)
        assert is_anomaly is True
        assert score > detector.threshold
    
    def test_update_model(self, detector, training_data):
        """Test online learning / model updates."""
        detector.train(training_data[:50])
        initial_model_state = detector.get_model_state()
        
        detector.update(training_data[50:])
        updated_model_state = detector.get_model_state()
        
        assert initial_model_state != updated_model_state
    
    def test_model_persistence(self, detector, training_data, tmp_path):
        """Test model save and load."""
        detector.train(training_data)
        model_path = tmp_path / "ids_model.pkl"
        
        detector.save_model(str(model_path))
        assert model_path.exists()
        
        new_detector = AnomalyDetector(model_type="isolation_forest")
        new_detector.load_model(str(model_path))
        
        # Both should produce same predictions
        sample = training_data[0]
        result1 = detector.predict(sample)
        result2 = new_detector.predict(sample)
        assert result1 == result2


class TestIDSAlert:
    """Test IDS alert generation and management."""
    
    def test_alert_creation(self):
        """Test basic alert creation."""
        alert = IDSAlert(
            timestamp=datetime.now(),
            severity=AlertSeverity.HIGH,
            alert_type="port_scan",
            source_ip="192.168.1.100",
            destination_ip="10.0.0.50",
            description="Potential port scan detected",
            confidence=0.95,
            metadata={"scanned_ports": 80}
        )
        
        assert alert.severity == AlertSeverity.HIGH
        assert alert.alert_type == "port_scan"
        assert alert.confidence == 0.95
        assert alert.metadata["scanned_ports"] == 80
    
    def test_alert_serialization(self):
        """Test alert to dict conversion."""
        alert = IDSAlert(
            timestamp=datetime.now(),
            severity=AlertSeverity.CRITICAL,
            alert_type="ddos",
            source_ip="multiple",
            destination_ip="10.0.0.50",
            description="DDoS attack detected",
            confidence=0.99
        )
        
        data = alert.to_dict()
        assert data["severity"] == "CRITICAL"
        assert data["alert_type"] == "ddos"
        assert data["confidence"] == 0.99
    
    def test_alert_priority_calculation(self):
        """Test alert priority based on severity and confidence."""
        alert_high = IDSAlert(
            timestamp=datetime.now(),
            severity=AlertSeverity.HIGH,
            alert_type="intrusion",
            source_ip="192.168.1.100",
            destination_ip="10.0.0.50",
            description="Intrusion attempt",
            confidence=0.9
        )
        
        alert_medium = IDSAlert(
            timestamp=datetime.now(),
            severity=AlertSeverity.MEDIUM,
            alert_type="scan",
            source_ip="192.168.1.101",
            destination_ip="10.0.0.50",
            description="Network scan",
            confidence=0.7
        )
        
        assert alert_high.get_priority() > alert_medium.get_priority()


class TestIntrusionDetectionSystem:
    """Test complete IDS system integration."""
    
    @pytest.fixture
    async def ids(self):
        """Create IDS instance."""
        ids = IntrusionDetectionSystem(
            enable_ml=True,
            enable_signatures=True,
            alert_threshold=0.7
        )
        await ids.initialize()
        return ids
    
    @pytest.fixture
    def attack_packets(self) -> List[NetworkPacket]:
        """Generate attack traffic patterns."""
        packets = []
        base_time = datetime.now()
        
        # SQL injection attempt
        sql_packet = NetworkPacket(
            timestamp=base_time,
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=80,
            protocol="TCP",
            payload_size=256,
            payload=b"' OR '1'='1"
        )
        packets.append(sql_packet)
        
        return packets
    
    @pytest.mark.asyncio
    async def test_ids_initialization(self, ids):
        """Test IDS system initialization."""
        assert ids.is_running is True
        assert ids.analyzer is not None
        assert ids.detector is not None
    
    @pytest.mark.asyncio
    async def test_process_packet(self, ids, attack_packets):
        """Test packet processing and alert generation."""
        packet = attack_packets[0]
        alerts = await ids.process_packet(packet)
        
        assert len(alerts) > 0
        assert any(alert.alert_type == "sql_injection" for alert in alerts)
    
    @pytest.mark.asyncio
    async def test_process_packet_stream(self, ids, attack_packets):
        """Test continuous packet stream processing."""
        alert_count = 0
        
        async for alerts in ids.process_stream(attack_packets):
            alert_count += len(alerts)
        
        assert alert_count > 0
    
    @pytest.mark.asyncio
    async def test_signature_matching(self, ids, attack_packets):
        """Test signature-based detection."""
        packet = attack_packets[0]
        matches = ids.match_signatures(packet)
        
        assert len(matches) > 0
        assert any("sql_injection" in match["signature_id"] for match in matches)
    
    @pytest.mark.asyncio
    async def test_alert_correlation(self, ids):
        """Test alert correlation across multiple events."""
        # Generate related events
        packets = []
        base_time = datetime.now()
        
        for i in range(5):
            packet = NetworkPacket(
                timestamp=base_time,
                src_ip="192.168.1.100",
                dst_ip="10.0.0.50",
                src_port=50000 + i,
                dst_port=80,
                protocol="TCP",
                payload_size=512
            )
            packets.append(packet)
        
        alerts = []
        for packet in packets:
            packet_alerts = await ids.process_packet(packet)
            alerts.extend(packet_alerts)
        
        correlated = ids.correlate_alerts(alerts)
        assert len(correlated) <= len(alerts)
    
    @pytest.mark.asyncio
    async def test_false_positive_handling(self, ids):
        """Test false positive reduction mechanisms."""
        # Normal HTTPS traffic
        normal_packet = NetworkPacket(
            timestamp=datetime.now(),
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            payload_size=1024
        )
        
        alerts = await ids.process_packet(normal_packet)
        
        # Should not generate high-severity alerts for normal traffic
        high_severity_alerts = [a for a in alerts if a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]]
        assert len(high_severity_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, ids, attack_packets):
        """Test IDS performance metrics tracking."""
        for packet in attack_packets:
            await ids.process_packet(packet)
        
        metrics = ids.get_metrics()
        
        assert "packets_processed" in metrics
        assert "alerts_generated" in metrics
        assert "processing_time_avg" in metrics
        assert "detection_rate" in metrics
        assert metrics["packets_processed"] > 0
    
    @pytest.mark.asyncio
    async def test_shutdown(self, ids):
        """Test graceful IDS shutdown."""
        await ids.shutdown()
        assert ids.is_running is False


class TestIDSIntegration:
    """Test IDS integration with other security components."""
    
    @pytest.mark.asyncio
    async def test_siem_integration(self):
        """Test IDS alert forwarding to SIEM."""
        # This would test integration with SIEM system
        # Implementation depends on SIEM architecture
        pass
    
    @pytest.mark.asyncio
    async def test_firewall_integration(self):
        """Test automatic firewall rule creation from IDS alerts."""
        # This would test IDS -> Firewall automation
        # Implementation depends on firewall architecture
        pass
    
    @pytest.mark.asyncio
    async def test_threat_intel_integration(self):
        """Test IDS enrichment with threat intelligence."""
        # This would test threat intel feed integration
        # Implementation depends on threat intel sources
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
