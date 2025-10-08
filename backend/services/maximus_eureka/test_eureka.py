"""Maximus Eureka Service - Test Eureka.

This module contains unit tests for the Maximus AI's Eureka Service. It ensures
that the Eureka Engine, Pattern Detector, IoC Extractor, and Playbook Generator
components function as expected, correctly identifying insights, patterns,
extracting indicators, and generating appropriate response playbooks.

These tests cover various aspects of data analysis, pattern recognition,
IoC extraction logic, and playbook generation rules, validating the robustness
and accuracy of the Eureka Service's discovery capabilities.
"""

import pytest

from maximus_eureka.eureka import EurekaEngine
from maximus_eureka.ioc_extractor import IoCExtractor
from maximus_eureka.pattern_detector import PatternDetector
from maximus_eureka.playbook_generator import PlaybookGenerator


@pytest.fixture
def eureka_engine():
    """Fixture for EurekaEngine."""
    return EurekaEngine()


@pytest.fixture
def pattern_detector():
    """Fixture for PatternDetector."""
    return PatternDetector()


@pytest.fixture
def ioc_extractor():
    """Fixture for IoCExtractor."""
    return IoCExtractor()


@pytest.fixture
def playbook_generator():
    """Fixture for PlaybookGenerator."""
    return PlaybookGenerator()


@pytest.mark.asyncio
async def test_eureka_engine_no_novel_discovery(eureka_engine):
    """Tests EurekaEngine when no novel discovery is made."""
    data = {"log": "normal activity"}
    result = await eureka_engine.analyze_data(data, "logs")
    assert result["status"] == "completed"
    assert "No significant novel insights" in result["analysis_notes"]
    assert result["novel_discovery"] is None


@pytest.mark.asyncio
async def test_eureka_engine_novel_discovery(eureka_engine):
    """Tests EurekaEngine when a novel discovery is made."""
    data = {"network_traffic": "unusual_pattern_zero_day_exploit"}
    result = await eureka_engine.analyze_data(data, "network_traffic")
    assert result["status"] == "completed"
    assert "Critical novel discovery made!" in result["analysis_notes"]
    assert result["novel_discovery"] is not None
    assert result["novel_discovery"]["severity"] == "critical"


def test_ioc_extractor_extract_ips(ioc_extractor):
    """Tests IoCExtractor for IP address extraction."""
    data = {"log_entry": "Connection from 192.168.1.10 to 10.0.0.5"}
    iocs = ioc_extractor.extract_iocs(data)
    assert "192.168.1.10" in iocs["ips"]
    assert "10.0.0.5" in iocs["ips"]


def test_ioc_extractor_extract_domains(ioc_extractor):
    """Tests IoCExtractor for domain extraction."""
    data = {"url": "http://malicious.com/phish?user=test", "domain": "legit-site.org"}
    iocs = ioc_extractor.extract_iocs(data)
    assert "malicious.com" in iocs["domains"]
    assert "legit-site.org" in iocs["domains"]


def test_pattern_detector_high_cpu_anomaly(pattern_detector):
    """Tests PatternDetector for high CPU anomaly detection."""
    data = {"cpu_usage": 95, "memory_usage": 50}
    pattern_def = {"type": "statistical", "metric": "cpu_usage"}
    detected = pattern_detector.detect_patterns(data, pattern_def)
    assert len(detected) == 1
    assert detected[0]["pattern_id"] == "high_cpu_anomaly"


def test_playbook_generator_critical_insight(playbook_generator):
    """Tests PlaybookGenerator for critical insight playbook generation."""
    insight = {
        "id": "exploit_001",
        "type": "zero_day_exploit_potential",
        "severity": "critical",
        "description": "New exploit found",
        "related_data": {"host": "server_1"},
    }
    playbook = playbook_generator.generate_playbook(insight)
    assert playbook["name"] == "Response to zero_day_exploit_potential"
    assert any(step["action"] == "isolate_affected_systems" for step in playbook["steps"])
