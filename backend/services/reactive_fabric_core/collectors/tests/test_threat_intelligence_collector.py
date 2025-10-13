"""
Tests for Threat Intelligence Collector.

Tests integration with external threat intelligence feeds and APIs.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses

from ..base_collector import CollectorHealth
from ..threat_intelligence_collector import (
    ThreatIntelligenceCollector,
    ThreatIntelligenceConfig,
    ThreatIndicator
)


@pytest.fixture
def config():
    """Create a test configuration."""
    return ThreatIntelligenceConfig(
        virustotal_api_key="test_vt_key",
        abuseipdb_api_key="test_abuse_key",
        alienvault_api_key="test_otx_key",
        misp_url="https://misp.test.com",
        misp_api_key="test_misp_key",
        collection_interval_seconds=1,
        requests_per_minute=10,
        min_reputation_score=0.3
    )


@pytest.fixture
def collector(config):
    """Create a test collector instance."""
    return ThreatIntelligenceCollector(config)


class TestThreatIntelligenceCollector:
    """Test suite for ThreatIntelligenceCollector."""

    @pytest.mark.asyncio
    async def test_initialize(self, collector):
        """Test collector initialization."""
        await collector.initialize()

        assert collector.session is not None
        assert collector.metrics.collector_type == "ThreatIntelligenceCollector"
        assert len(collector.cache) == 0
        assert len(collector.false_positives) == 0

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_validate_source_virustotal(self, collector):
        """Test VirusTotal source validation."""
        await collector.initialize()

        with aioresponses() as mock:
            mock.get(
                "https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8",
                status=200,
                payload={"data": {"type": "ip_address"}}
            )

            is_valid = await collector.validate_source()
            assert is_valid is True

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_validate_source_abuseipdb(self, config):
        """Test AbuseIPDB source validation."""
        # Only configure AbuseIPDB
        config.virustotal_api_key = None
        config.alienvault_api_key = None
        config.misp_api_key = None
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        with aioresponses() as mock:
            mock.get(
                "https://api.abuseipdb.com/api/v2/check?ipAddress=8.8.8.8",
                status=200,
                payload={"data": {"ipAddress": "8.8.8.8"}}
            )

            is_valid = await collector.validate_source()
            assert is_valid is True

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_validate_source_alienvault(self, config):
        """Test AlienVault OTX source validation."""
        # Only configure AlienVault
        config.virustotal_api_key = None
        config.abuseipdb_api_key = None
        config.misp_api_key = None
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        with aioresponses() as mock:
            mock.get(
                "https://otx.alienvault.com/api/v1/indicators/IPv4/8.8.8.8/general",
                status=200,
                payload={"indicator": "8.8.8.8"}
            )

            is_valid = await collector.validate_source()
            assert is_valid is True

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_validate_source_misp(self, config):
        """Test MISP source validation."""
        # Only configure MISP
        config.virustotal_api_key = None
        config.abuseipdb_api_key = None
        config.alienvault_api_key = None
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        with aioresponses() as mock:
            mock.get(
                "https://misp.test.com/servers/getVersion",
                status=200,
                payload={"version": "2.4"}
            )

            is_valid = await collector.validate_source()
            assert is_valid is True

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_validate_source_no_apis(self):
        """Test validation with no APIs configured."""
        config = ThreatIntelligenceConfig()
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        is_valid = await collector.validate_source()
        assert is_valid is False

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_ip_malicious(self, collector):
        """Test checking malicious IP address."""
        await collector.initialize()

        with aioresponses() as mock:
            # Mock VirusTotal response
            mock.get(
                "https://www.virustotal.com/api/v3/ip_addresses/192.168.1.100",
                status=200,
                payload={
                    "data": {
                        "attributes": {
                            "last_analysis_stats": {
                                "malicious": 8,
                                "suspicious": 2,
                                "clean": 10,
                                "undetected": 80
                            }
                        }
                    }
                }
            )

            # Mock AbuseIPDB response
            mock.get(
                "https://api.abuseipdb.com/api/v2/check?ipAddress=192.168.1.100&maxAgeInDays=90",
                status=200,
                payload={
                    "data": {
                        "ipAddress": "192.168.1.100",
                        "abuseConfidenceScore": 75
                    }
                }
            )

            indicator = await collector.check_ip("192.168.1.100")

            assert indicator is not None
            assert indicator.indicator_type == "ip"
            assert indicator.value == "192.168.1.100"
            assert indicator.confidence > 0.3
            assert indicator.severity in ["low", "medium", "high", "critical"]

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_ip_clean(self, collector):
        """Test checking clean IP address."""
        await collector.initialize()

        with aioresponses() as mock:
            # Mock VirusTotal response - clean IP
            mock.get(
                "https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8",
                status=200,
                payload={
                    "data": {
                        "attributes": {
                            "last_analysis_stats": {
                                "malicious": 0,
                                "suspicious": 0,
                                "clean": 90,
                                "undetected": 10
                            }
                        }
                    }
                }
            )

            # Mock AbuseIPDB response - clean IP
            mock.get(
                "https://api.abuseipdb.com/api/v2/check?ipAddress=8.8.8.8&maxAgeInDays=90",
                status=200,
                payload={
                    "data": {
                        "ipAddress": "8.8.8.8",
                        "abuseConfidenceScore": 0
                    }
                }
            )

            indicator = await collector.check_ip("8.8.8.8")

            assert indicator is None  # Clean IP shouldn't create indicator

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_domain_malicious(self, collector):
        """Test checking malicious domain."""
        await collector.initialize()

        with aioresponses() as mock:
            # Mock VirusTotal response with high malicious score
            mock.get(
                "https://www.virustotal.com/api/v3/domains/malicious.com",
                status=200,
                payload={
                    "data": {
                        "attributes": {
                            "last_analysis_stats": {
                                "malicious": 40,  # 40/100 = 0.4 > 0.3 threshold
                                "suspicious": 10,
                                "clean": 30,
                                "undetected": 20
                            }
                        }
                    }
                }
            )

            indicator = await collector.check_domain("malicious.com")

            assert indicator is not None
            assert indicator.indicator_type == "domain"
            assert indicator.value == "malicious.com"
            assert indicator.confidence >= 0.3

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_hash_malicious(self, collector):
        """Test checking malicious file hash."""
        await collector.initialize()

        test_hash = "a" * 64  # SHA256 format

        with aioresponses() as mock:
            # Mock VirusTotal response
            mock.get(
                f"https://www.virustotal.com/api/v3/files/{test_hash}",
                status=200,
                payload={
                    "data": {
                        "attributes": {
                            "last_analysis_stats": {
                                "malicious": 45,
                                "suspicious": 10,
                                "clean": 15,
                                "undetected": 30
                            }
                        }
                    }
                }
            )

            indicator = await collector.check_hash(test_hash)

            assert indicator is not None
            assert indicator.indicator_type == "hash"
            assert indicator.value == test_hash
            assert indicator.confidence > 0.4

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_cache_functionality(self, collector):
        """Test caching of threat indicators."""
        await collector.initialize()

        with aioresponses() as mock:
            # First check - should hit API
            mock.get(
                "https://www.virustotal.com/api/v3/ip_addresses/192.168.1.1",
                status=200,
                payload={
                    "data": {
                        "attributes": {
                            "last_analysis_stats": {
                                "malicious": 10,
                                "clean": 90
                            }
                        }
                    }
                }
            )
            mock.get(
                "https://api.abuseipdb.com/api/v2/check?ipAddress=192.168.1.1&maxAgeInDays=90",
                status=200,
                payload={
                    "data": {
                        "abuseConfidenceScore": 80
                    }
                }
            )

            indicator1 = await collector.check_ip("192.168.1.1")
            assert indicator1 is not None

            # Second check - should use cache, no API call
            indicator2 = await collector.check_ip("192.168.1.1")
            assert indicator2 is not None
            assert indicator2.value == indicator1.value
            assert indicator2.confidence == indicator1.confidence

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_rate_limiting(self, collector):
        """Test rate limiting functionality."""
        collector.config.requests_per_minute = 2  # Low limit for testing
        await collector.initialize()

        # Make two requests (within limit)
        assert await collector._check_rate_limit() is True
        assert await collector._check_rate_limit() is True

        # Third request should be blocked
        assert await collector._check_rate_limit() is False

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_collect_alienvault(self, collector):
        """Test collecting from AlienVault OTX."""
        await collector.initialize()

        with aioresponses() as mock:
            mock.get(
                "https://otx.alienvault.com/api/v1/pulses/subscribed?limit=10&page=1",
                status=200,
                payload={
                    "results": [
                        {
                            "id": "pulse1",
                            "name": "Test Pulse",
                            "tags": ["malware", "ransomware"],
                            "indicators": [
                                {
                                    "type": "IPv4",
                                    "indicator": "192.168.1.100"
                                },
                                {
                                    "type": "domain",
                                    "indicator": "evil.com"
                                }
                            ]
                        }
                    ]
                }
            )

            events = []
            async for event in collector.collect():
                events.append(event)

            assert len(events) == 2
            assert events[0].collector_type == "ThreatIntelligence"
            assert events[0].source == "threatintel:alienvault"

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_collect_misp(self, collector):
        """Test collecting from MISP."""
        await collector.initialize()

        with aioresponses() as mock:
            # Mock events list
            mock.get(
                "https://misp.test.com/events/index?limit=10&published=1",
                status=200,
                payload=[
                    {
                        "Event": {
                            "id": "1001",
                            "info": "Test Event"
                        }
                    }
                ]
            )

            # Mock event details
            mock.get(
                "https://misp.test.com/events/view/1001",
                status=200,
                payload={
                    "Event": {
                        "id": "1001",
                        "info": "Test Event",
                        "Attribute": [
                            {
                                "type": "ip-dst",
                                "value": "192.168.1.200",
                                "category": "Network activity"
                            }
                        ]
                    }
                }
            )

            events = []
            async for event in collector.collect():
                events.append(event)

            assert len(events) == 1
            assert events[0].source == "threatintel:misp"
            assert events[0].severity == "high"

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_invalid_ip_format(self, collector):
        """Test handling of invalid IP format."""
        await collector.initialize()

        indicator = await collector.check_ip("not-an-ip")
        assert indicator is None

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_api_failure_handling(self, collector):
        """Test handling of API failures."""
        await collector.initialize()

        with aioresponses() as mock:
            # Mock API failure
            mock.get(
                "https://www.virustotal.com/api/v3/ip_addresses/192.168.1.1",
                status=500,
                body="Internal Server Error"
            )
            mock.get(
                "https://api.abuseipdb.com/api/v2/check?ipAddress=192.168.1.1&maxAgeInDays=90",
                status=500,
                body="Internal Server Error"
            )

            indicator = await collector.check_ip("192.168.1.1")
            assert indicator is None

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_clean_cache(self, collector):
        """Test cache cleaning functionality."""
        await collector.initialize()

        # Add old entry to cache
        old_indicator = ThreatIndicator(
            indicator_type="ip",
            value="192.168.1.1",
            source="test",
            severity="high",
            confidence=0.9,
            last_seen=datetime.utcnow() - timedelta(hours=2)
        )
        collector.cache["ip:192.168.1.1"] = old_indicator

        # Add recent entry to cache
        new_indicator = ThreatIndicator(
            indicator_type="ip",
            value="192.168.1.2",
            source="test",
            severity="high",
            confidence=0.9,
            last_seen=datetime.utcnow()
        )
        collector.cache["ip:192.168.1.2"] = new_indicator

        # Clean cache
        collector._clean_cache()

        # Old entry should be removed
        assert "ip:192.168.1.1" not in collector.cache
        # Recent entry should remain
        assert "ip:192.168.1.2" in collector.cache

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_score_to_severity(self, collector):
        """Test score to severity conversion."""
        assert collector._score_to_severity(0.9) == "critical"
        assert collector._score_to_severity(0.7) == "high"
        assert collector._score_to_severity(0.5) == "medium"
        assert collector._score_to_severity(0.2) == "low"

    @pytest.mark.asyncio
    async def test_false_positives_filtering(self, collector):
        """Test filtering of false positives."""
        await collector.initialize()

        # Add to false positives
        collector.false_positives.add("192.168.1.1")

        # Create indicator
        indicator = ThreatIndicator(
            indicator_type="ip",
            value="192.168.1.1",
            source="test",
            severity="high",
            confidence=0.9
        )

        # Should not report due to false positive
        should_report = await collector._should_report(indicator)
        assert should_report is False

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_start_stop(self, collector):
        """Test collector start and stop."""
        await collector.start()
        assert collector._running is True
        assert collector.metrics.health == CollectorHealth.HEALTHY

        await collector.stop()
        assert collector._running is False
        assert collector.metrics.health == CollectorHealth.OFFLINE

    def test_repr(self, collector):
        """Test string representation."""
        repr_str = repr(collector)
        assert "ThreatIntelligenceCollector" in repr_str
        assert "health=" in repr_str
        assert "events=" in repr_str