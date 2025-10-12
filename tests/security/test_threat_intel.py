"""
Threat Intelligence Integration Tests - MAXIMUS Vértice

Validates threat intelligence feed integration including:
- Feed ingestion and parsing
- IOC (Indicators of Compromise) management
- Threat enrichment
- Integration with defensive tools

Test Coverage:
- Multiple feed formats (STIX, TAXII, JSON, CSV)
- Real-time threat updates
- IOC correlation
- Automated response integration
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

from backend.security.threat_intel import (
    ThreatIntelligenceEngine,
    ThreatFeed,
    IOC,
    IOCType,
    ThreatActor,
    ThreatEnrichment,
    FeedParser,
    IOCMatcher
)


class TestIOC:
    """Test Indicator of Compromise data structures."""
    
    def test_ioc_creation(self):
        """Test basic IOC creation."""
        ioc = IOC(
            ioc_id="IOC001",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.1",
            threat_type="malware_c2",
            severity="HIGH",
            confidence=0.95,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            source="AlienVault"
        )
        
        assert ioc.ioc_id == "IOC001"
        assert ioc.ioc_type == IOCType.IP_ADDRESS
        assert ioc.value == "203.0.113.1"
        assert ioc.confidence == 0.95
    
    def test_ioc_types(self):
        """Test different IOC types."""
        ioc_types = [
            (IOCType.IP_ADDRESS, "192.168.1.1"),
            (IOCType.DOMAIN, "malicious.example.com"),
            (IOCType.URL, "http://evil.com/payload"),
            (IOCType.FILE_HASH, "44d88612fea8a8f36de82e1278abb02f"),
            (IOCType.EMAIL, "attacker@evil.com")
        ]
        
        for ioc_type, value in ioc_types:
            ioc = IOC(
                ioc_id=f"IOC_{ioc_type.value}",
                ioc_type=ioc_type,
                value=value,
                threat_type="test",
                severity="MEDIUM",
                confidence=0.8,
                first_seen=datetime.now()
            )
            assert ioc.ioc_type == ioc_type
            assert ioc.value == value
    
    def test_ioc_validation(self):
        """Test IOC validation logic."""
        with pytest.raises(ValueError):
            IOC(
                ioc_id="INVALID",
                ioc_type=IOCType.IP_ADDRESS,
                value="invalid_ip",
                threat_type="test",
                severity="MEDIUM",
                confidence=0.8,
                first_seen=datetime.now()
            )
    
    def test_ioc_expiration(self):
        """Test IOC expiration logic."""
        old_ioc = IOC(
            ioc_id="IOC_OLD",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.1",
            threat_type="malware",
            severity="HIGH",
            confidence=0.9,
            first_seen=datetime.now() - timedelta(days=365),
            last_seen=datetime.now() - timedelta(days=90),
            ttl=30  # 30 days TTL
        )
        
        assert old_ioc.is_expired() is True
        
        fresh_ioc = IOC(
            ioc_id="IOC_FRESH",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.2",
            threat_type="malware",
            severity="HIGH",
            confidence=0.9,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            ttl=30
        )
        
        assert fresh_ioc.is_expired() is False


class TestThreatFeed:
    """Test threat intelligence feed management."""
    
    def test_feed_creation(self):
        """Test creating threat feed configuration."""
        feed = ThreatFeed(
            feed_id="FEED001",
            name="AlienVault OTX",
            url="https://otx.alienvault.com/api/v1/pulses/subscribed",
            feed_type="json",
            update_interval=3600,  # 1 hour
            enabled=True,
            requires_auth=True,
            api_key="secret_key"
        )
        
        assert feed.feed_id == "FEED001"
        assert feed.name == "AlienVault OTX"
        assert feed.update_interval == 3600
        assert feed.enabled is True
    
    def test_feed_authentication(self):
        """Test feed authentication configuration."""
        feed = ThreatFeed(
            feed_id="FEED002",
            name="Private Feed",
            url="https://private-intel.example.com/feed",
            feed_type="json",
            update_interval=1800,
            enabled=True,
            requires_auth=True,
            auth_type="bearer",
            api_key="bearer_token"
        )
        
        headers = feed.get_auth_headers()
        assert "Authorization" in headers
        assert "bearer_token" in headers["Authorization"]


class TestFeedParser:
    """Test threat feed parsing capabilities."""
    
    @pytest.fixture
    def parser(self):
        """Create FeedParser instance."""
        return FeedParser()
    
    def test_parse_json_feed(self, parser):
        """Test parsing JSON format feed."""
        json_data = {
            "indicators": [
                {
                    "type": "ip",
                    "value": "203.0.113.1",
                    "threat_type": "malware_c2",
                    "confidence": 95
                },
                {
                    "type": "domain",
                    "value": "evil.example.com",
                    "threat_type": "phishing",
                    "confidence": 87
                }
            ]
        }
        
        iocs = parser.parse_json(json_data)
        
        assert len(iocs) == 2
        assert iocs[0].ioc_type == IOCType.IP_ADDRESS
        assert iocs[1].ioc_type == IOCType.DOMAIN
    
    def test_parse_csv_feed(self, parser):
        """Test parsing CSV format feed."""
        csv_data = """ip,threat_type,confidence
203.0.113.1,malware,95
203.0.113.2,botnet,87
"""
        
        iocs = parser.parse_csv(csv_data)
        
        assert len(iocs) == 2
        assert all(ioc.ioc_type == IOCType.IP_ADDRESS for ioc in iocs)
    
    def test_parse_stix_feed(self, parser):
        """Test parsing STIX format feed."""
        stix_data = {
            "type": "bundle",
            "objects": [
                {
                    "type": "indicator",
                    "pattern": "[ipv4-addr:value = '203.0.113.1']",
                    "labels": ["malicious-activity"],
                    "valid_from": "2024-01-01T00:00:00Z"
                }
            ]
        }
        
        iocs = parser.parse_stix(stix_data)
        
        assert len(iocs) > 0
        assert iocs[0].ioc_type == IOCType.IP_ADDRESS
    
    def test_parse_invalid_data(self, parser):
        """Test handling of invalid feed data."""
        invalid_data = "not a valid format"
        
        with pytest.raises(ValueError):
            parser.parse(invalid_data, format="json")


class TestIOCMatcher:
    """Test IOC matching capabilities."""
    
    @pytest.fixture
    def matcher(self):
        """Create IOCMatcher instance."""
        return IOCMatcher()
    
    @pytest.fixture
    def sample_iocs(self) -> List[IOC]:
        """Create sample IOCs for testing."""
        return [
            IOC(
                ioc_id="IOC001",
                ioc_type=IOCType.IP_ADDRESS,
                value="203.0.113.1",
                threat_type="malware_c2",
                severity="HIGH",
                confidence=0.95,
                first_seen=datetime.now()
            ),
            IOC(
                ioc_id="IOC002",
                ioc_type=IOCType.DOMAIN,
                value="evil.example.com",
                threat_type="phishing",
                severity="HIGH",
                confidence=0.92,
                first_seen=datetime.now()
            ),
            IOC(
                ioc_id="IOC003",
                ioc_type=IOCType.FILE_HASH,
                value="44d88612fea8a8f36de82e1278abb02f",
                threat_type="ransomware",
                severity="CRITICAL",
                confidence=0.98,
                first_seen=datetime.now()
            )
        ]
    
    def test_load_iocs(self, matcher, sample_iocs):
        """Test loading IOCs into matcher."""
        matcher.load_iocs(sample_iocs)
        assert len(matcher.iocs) == len(sample_iocs)
    
    def test_match_ip(self, matcher, sample_iocs):
        """Test IP address matching."""
        matcher.load_iocs(sample_iocs)
        
        matches = matcher.match_ip("203.0.113.1")
        
        assert len(matches) == 1
        assert matches[0].ioc_type == IOCType.IP_ADDRESS
        assert matches[0].threat_type == "malware_c2"
    
    def test_match_domain(self, matcher, sample_iocs):
        """Test domain matching."""
        matcher.load_iocs(sample_iocs)
        
        matches = matcher.match_domain("evil.example.com")
        
        assert len(matches) == 1
        assert matches[0].ioc_type == IOCType.DOMAIN
    
    def test_match_file_hash(self, matcher, sample_iocs):
        """Test file hash matching."""
        matcher.load_iocs(sample_iocs)
        
        matches = matcher.match_hash("44d88612fea8a8f36de82e1278abb02f")
        
        assert len(matches) == 1
        assert matches[0].severity == "CRITICAL"
    
    def test_bulk_matching(self, matcher, sample_iocs):
        """Test bulk matching of multiple indicators."""
        matcher.load_iocs(sample_iocs)
        
        test_data = [
            "203.0.113.1",
            "evil.example.com",
            "benign.example.com",
            "44d88612fea8a8f36de82e1278abb02f"
        ]
        
        results = matcher.match_bulk(test_data)
        
        assert len(results) >= 3  # Should match 3 IOCs
    
    def test_subnet_matching(self, matcher):
        """Test subnet-based IP matching."""
        subnet_ioc = IOC(
            ioc_id="IOC_SUBNET",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.0/24",
            threat_type="malware_network",
            severity="HIGH",
            confidence=0.9,
            first_seen=datetime.now()
        )
        
        matcher.load_iocs([subnet_ioc])
        
        # Should match IPs in subnet
        matches = matcher.match_ip("203.0.113.50")
        assert len(matches) > 0


class TestThreatEnrichment:
    """Test threat intelligence enrichment."""
    
    @pytest.fixture
    def enrichment(self):
        """Create ThreatEnrichment instance."""
        return ThreatEnrichment()
    
    def test_enrich_ip(self, enrichment):
        """Test IP address enrichment."""
        ip = "203.0.113.1"
        
        enriched = enrichment.enrich_ip(ip)
        
        assert "geolocation" in enriched
        assert "asn" in enriched
        assert "reputation" in enriched
    
    def test_enrich_domain(self, enrichment):
        """Test domain enrichment."""
        domain = "example.com"
        
        enriched = enrichment.enrich_domain(domain)
        
        assert "whois" in enriched
        assert "dns_records" in enriched
        assert "reputation" in enriched
    
    def test_enrich_file_hash(self, enrichment):
        """Test file hash enrichment."""
        file_hash = "44d88612fea8a8f36de82e1278abb02f"
        
        enriched = enrichment.enrich_hash(file_hash)
        
        assert "file_name" in enriched or "not_found" in enriched
        # Enrichment might return "not found" for test hashes
    
    def test_bulk_enrichment(self, enrichment):
        """Test bulk enrichment of multiple indicators."""
        indicators = [
            {"type": "ip", "value": "203.0.113.1"},
            {"type": "domain", "value": "example.com"}
        ]
        
        enriched = enrichment.enrich_bulk(indicators)
        
        assert len(enriched) == len(indicators)


class TestThreatActor:
    """Test threat actor tracking."""
    
    def test_actor_creation(self):
        """Test creating threat actor profile."""
        actor = ThreatActor(
            actor_id="APT001",
            name="Advanced Persistent Threat 1",
            aliases=["APT-X", "Fancy Bear"],
            origin_country="Unknown",
            motivation=["espionage", "sabotage"],
            targets=["government", "defense"],
            ttps=["spear_phishing", "zero_day_exploits"],
            associated_malware=["APT1_Backdoor"],
            first_seen=datetime.now() - timedelta(days=365),
            last_activity=datetime.now()
        )
        
        assert actor.actor_id == "APT001"
        assert "espionage" in actor.motivation
        assert len(actor.ttps) > 0
    
    def test_actor_attribution(self):
        """Test attributing indicators to threat actors."""
        actor = ThreatActor(
            actor_id="APT002",
            name="APT Group 2",
            associated_iocs=[
                "203.0.113.1",
                "evil.example.com"
            ]
        )
        
        assert actor.is_associated_with("203.0.113.1") is True
        assert actor.is_associated_with("benign.com") is False


class TestThreatIntelligenceEngine:
    """Test complete threat intelligence engine."""
    
    @pytest.fixture
    async def engine(self):
        """Create ThreatIntelligenceEngine instance."""
        engine = ThreatIntelligenceEngine(
            enable_auto_update=True,
            update_interval=3600
        )
        await engine.initialize()
        return engine
    
    @pytest.fixture
    def sample_feeds(self) -> List[ThreatFeed]:
        """Create sample feed configurations."""
        return [
            ThreatFeed(
                feed_id="FEED001",
                name="Test Feed 1",
                url="https://test-feed1.example.com/iocs.json",
                feed_type="json",
                update_interval=3600,
                enabled=True
            )
        ]
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.is_running is True
        assert engine.parser is not None
        assert engine.matcher is not None
    
    @pytest.mark.asyncio
    async def test_add_feed(self, engine, sample_feeds):
        """Test adding threat intelligence feeds."""
        feed = sample_feeds[0]
        await engine.add_feed(feed)
        
        assert feed.feed_id in engine.get_feed_ids()
    
    @pytest.mark.asyncio
    async def test_update_feeds(self, engine, sample_feeds):
        """Test updating feeds from sources."""
        feed = sample_feeds[0]
        await engine.add_feed(feed)
        
        # Mock feed update
        mock_data = {
            "indicators": [
                {"type": "ip", "value": "203.0.113.1", "threat_type": "malware"}
            ]
        }
        
        await engine.update_feed(feed.feed_id, mock_data)
        
        # Should have loaded IOCs
        iocs = engine.get_iocs()
        assert len(iocs) > 0
    
    @pytest.mark.asyncio
    async def test_query_ioc(self, engine):
        """Test querying IOC database."""
        # Add test IOC
        test_ioc = IOC(
            ioc_id="TEST001",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.1",
            threat_type="test",
            severity="MEDIUM",
            confidence=0.8,
            first_seen=datetime.now()
        )
        
        await engine.add_ioc(test_ioc)
        
        # Query
        results = engine.query("203.0.113.1")
        
        assert len(results) > 0
        assert results[0].value == "203.0.113.1"
    
    @pytest.mark.asyncio
    async def test_threat_lookup(self, engine):
        """Test threat intelligence lookup."""
        test_ip = "203.0.113.1"
        
        result = await engine.lookup(test_ip, ioc_type=IOCType.IP_ADDRESS)
        
        assert result is not None
        assert "threat_score" in result
        assert "matches" in result
    
    @pytest.mark.asyncio
    async def test_integration_with_ids(self, engine):
        """Test integration with IDS."""
        # Simulate IDS alert
        alert = {
            "src_ip": "203.0.113.1",
            "dst_ip": "10.0.0.50",
            "alert_type": "suspicious_traffic"
        }
        
        enriched = await engine.enrich_alert(alert)
        
        assert "threat_intel" in enriched
        # Should include threat intelligence data if IP matches IOC
    
    @pytest.mark.asyncio
    async def test_integration_with_firewall(self, engine):
        """Test integration with firewall."""
        # Add malicious IOC
        malicious_ioc = IOC(
            ioc_id="MAL001",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.1",
            threat_type="malware_c2",
            severity="HIGH",
            confidence=0.95,
            first_seen=datetime.now()
        )
        
        await engine.add_ioc(malicious_ioc)
        
        # Get firewall rules
        firewall_rules = await engine.generate_firewall_rules(
            severity_threshold="MEDIUM"
        )
        
        assert len(firewall_rules) > 0
        assert any("203.0.113.1" in rule["source_ip"] for rule in firewall_rules)
    
    @pytest.mark.asyncio
    async def test_ioc_aging(self, engine):
        """Test automatic IOC aging and expiration."""
        old_ioc = IOC(
            ioc_id="OLD001",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.99",
            threat_type="malware",
            severity="MEDIUM",
            confidence=0.8,
            first_seen=datetime.now() - timedelta(days=365),
            last_seen=datetime.now() - timedelta(days=180),
            ttl=30
        )
        
        await engine.add_ioc(old_ioc)
        
        # Run aging process
        await engine.age_iocs()
        
        # Old IOC should be expired
        active_iocs = engine.get_active_iocs()
        assert not any(ioc.ioc_id == "OLD001" for ioc in active_iocs)
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, engine):
        """Test performance metrics tracking."""
        # Perform some lookups
        for i in range(50):
            await engine.lookup(f"192.168.1.{i}", ioc_type=IOCType.IP_ADDRESS)
        
        metrics = engine.get_metrics()
        
        assert "total_lookups" in metrics
        assert "cache_hit_rate" in metrics
        assert "avg_lookup_time" in metrics
        assert metrics["total_lookups"] >= 50
    
    @pytest.mark.asyncio
    async def test_threat_scoring(self, engine):
        """Test threat scoring algorithm."""
        # Add IOCs with different confidences
        await engine.add_ioc(IOC(
            ioc_id="HIGH001",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.1",
            threat_type="malware",
            severity="CRITICAL",
            confidence=0.98,
            first_seen=datetime.now()
        ))
        
        score = engine.calculate_threat_score("203.0.113.1")
        
        assert score > 0
        assert score <= 100
    
    @pytest.mark.asyncio
    async def test_false_positive_handling(self, engine):
        """Test false positive feedback mechanism."""
        ioc = IOC(
            ioc_id="FP001",
            ioc_type=IOCType.IP_ADDRESS,
            value="203.0.113.1",
            threat_type="suspicious",
            severity="LOW",
            confidence=0.6,
            first_seen=datetime.now()
        )
        
        await engine.add_ioc(ioc)
        
        # Mark as false positive
        await engine.mark_false_positive("FP001", reason="Legitimate service")
        
        # Should be removed or flagged
        ioc_data = engine.get_ioc("FP001")
        assert ioc_data.is_false_positive is True or ioc_data is None
    
    @pytest.mark.asyncio
    async def test_shutdown(self, engine):
        """Test graceful engine shutdown."""
        await engine.shutdown()
        assert engine.is_running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
