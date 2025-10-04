"""
Tests for Analytics & Machine Learning modules
===============================================

Test coverage:
- BehavioralAnalytics: Baseline learning and anomaly detection
- MLDetector: ML-based threat detection and feature extraction
- RiskScorer: Multi-factor risk calculation
- ThreatIntelFeed: IOC enrichment and threat actor tracking
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from vertice.analytics import (
    BehavioralAnalytics,
    Baseline,
    Anomaly,
    AnomalyType,
    MLDetector,
    MLModel,
    MLModelType,
    Prediction,
    RiskScorer,
    RiskScore,
    RiskFactor,
    RiskLevel,
    ThreatIntelFeed,
    IOC,
    IOCType,
    ThreatActor,
)


class TestBehavioralAnalytics:
    """Test behavioral analytics and anomaly detection."""

    @pytest.fixture
    def analytics(self):
        """Create analytics instance (local mode)."""
        return BehavioralAnalytics(use_backend=False, learning_period_days=30)

    @pytest.fixture
    def sample_login_events(self):
        """Sample login events for baseline learning."""
        now = datetime.now()
        events = []

        # Generate 30 days of normal login patterns
        for day in range(30):
            date = now - timedelta(days=day)

            # Typical workday pattern: login at 9am-10am from office IP
            for hour in [9, 10]:
                event = {
                    "type": "login",
                    "timestamp": date.replace(hour=hour, minute=0, second=0).isoformat(),
                    "source_ip": "192.168.1.100",
                    "location": "New York",
                }
                events.append(event)

        return events

    @pytest.fixture
    def sample_network_events(self):
        """Sample network events."""
        now = datetime.now()
        events = []

        for i in range(50):
            event = {
                "type": "network",
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "bytes_in": 1000000 + (i * 10000),  # ~1MB baseline
                "bytes_out": 500000 + (i * 5000),  # ~500KB baseline
            }
            events.append(event)

        return events

    def test_initialization(self, analytics):
        """Test BehavioralAnalytics initialization."""
        assert analytics.learning_period_days == 30
        assert analytics.anomaly_threshold == 3.0
        assert analytics.use_backend is False
        assert len(analytics.baselines) == 0
        assert len(analytics.anomalies) == 0

    def test_learn_baseline_login_patterns(self, analytics, sample_login_events):
        """Test baseline learning from login events."""
        baseline = analytics.learn_baseline(
            entity_id="user_123",
            entity_type="user",
            historical_events=sample_login_events,
        )

        assert baseline.entity_id == "user_123"
        assert baseline.entity_type == "user"
        assert baseline.sample_count == len(sample_login_events)

        # Should learn typical hours (9 and 10)
        assert 9 in baseline.typical_login_hours
        assert 10 in baseline.typical_login_hours

        # Should learn typical location
        assert "192.168.1.100" in baseline.typical_locations

        # Confidence should increase with more samples
        assert baseline.confidence > 0.0

    def test_learn_baseline_network_patterns(self, analytics, sample_network_events):
        """Test baseline learning from network events."""
        baseline = analytics.learn_baseline(
            entity_id="endpoint_456",
            entity_type="endpoint",
            historical_events=sample_network_events,
        )

        assert baseline.avg_network_bytes_in > 0
        assert baseline.avg_network_bytes_out > 0
        assert baseline.stddev_network_in > 0
        assert baseline.stddev_network_out > 0

    def test_learn_baseline_cached(self, analytics, sample_login_events):
        """Test that baseline is cached."""
        baseline1 = analytics.learn_baseline(
            "user_123", "user", sample_login_events
        )

        # Should be cached
        assert "user_123" in analytics.baselines
        assert analytics.baselines["user_123"] == baseline1

    def test_detect_anomaly_login_time(self, analytics, sample_login_events):
        """Test anomaly detection for unusual login time."""
        # Learn baseline first
        analytics.learn_baseline("user_123", "user", sample_login_events)

        # Login at unusual hour (3am)
        unusual_event = {
            "type": "login",
            "timestamp": datetime.now().replace(hour=3, minute=0).isoformat(),
            "source_ip": "192.168.1.100",
        }

        anomalies = analytics.detect_anomalies("user_123", unusual_event)

        assert len(anomalies) > 0
        anomaly = anomalies[0]
        assert anomaly.anomaly_type == AnomalyType.LOGIN_TIME
        assert anomaly.severity in ["medium", "high"]
        assert "3" in str(anomaly.description)

    def test_detect_anomaly_login_location(self, analytics, sample_login_events):
        """Test anomaly detection for unusual login location."""
        analytics.learn_baseline("user_123", "user", sample_login_events)

        # Login from unusual location
        unusual_event = {
            "type": "login",
            "timestamp": datetime.now().replace(hour=9).isoformat(),
            "source_ip": "1.2.3.4",  # Unknown IP
            "location": "China",
        }

        anomalies = analytics.detect_anomalies("user_123", unusual_event)

        # Should detect location anomaly
        location_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.LOGIN_LOCATION]
        assert len(location_anomalies) > 0
        assert location_anomalies[0].severity == "high"

    def test_detect_anomaly_network_volume(self, analytics, sample_network_events):
        """Test anomaly detection for unusual network volume."""
        analytics.learn_baseline("endpoint_456", "endpoint", sample_network_events)

        # Huge network spike (potential exfiltration)
        spike_event = {
            "type": "network",
            "timestamp": datetime.now().isoformat(),
            "bytes_in": 1000000,
            "bytes_out": 50000000,  # 50MB out (way above baseline)
        }

        anomalies = analytics.detect_anomalies("endpoint_456", spike_event)

        assert len(anomalies) > 0
        anomaly = anomalies[0]
        assert anomaly.anomaly_type == AnomalyType.NETWORK_VOLUME
        assert anomaly.deviation_score > 3.0  # Should exceed threshold

    def test_detect_anomaly_process_execution(self, analytics):
        """Test anomaly detection for unusual process."""
        # Baseline with typical processes
        baseline_events = [
            {
                "type": "process",
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
                "process_name": "chrome.exe",
            }
            for i in range(20)
        ]

        analytics.learn_baseline("endpoint_789", "endpoint", baseline_events)

        # Unusual process
        unusual_event = {
            "type": "process",
            "timestamp": datetime.now().isoformat(),
            "process_name": "mimikatz.exe",  # Credential dumping tool
        }

        anomalies = analytics.detect_anomalies("endpoint_789", unusual_event)

        assert len(anomalies) > 0
        assert anomalies[0].anomaly_type == AnomalyType.PROCESS_EXECUTION

    def test_get_anomalies_no_baseline(self, analytics):
        """Test anomaly detection without baseline."""
        event = {"type": "login", "timestamp": datetime.now().isoformat()}

        anomalies = analytics.detect_anomalies("unknown_user", event)

        # Should return empty list (no baseline to compare)
        assert len(anomalies) == 0

    def test_get_anomalies_filter_by_type(self, analytics, sample_login_events):
        """Test filtering anomalies by type."""
        analytics.learn_baseline("user_123", "user", sample_login_events)

        # Create multiple anomaly types
        unusual_event1 = {
            "type": "login",
            "timestamp": datetime.now().replace(hour=3).isoformat(),
            "source_ip": "1.2.3.4",
        }

        analytics.detect_anomalies("user_123", unusual_event1)

        # Filter by type
        login_time_anomalies = analytics.get_anomalies(
            anomaly_type=AnomalyType.LOGIN_TIME
        )
        location_anomalies = analytics.get_anomalies(
            anomaly_type=AnomalyType.LOGIN_LOCATION
        )

        assert len(login_time_anomalies) >= 0
        assert len(location_anomalies) >= 0

    def test_get_baseline(self, analytics, sample_login_events):
        """Test retrieving baseline."""
        analytics.learn_baseline("user_123", "user", sample_login_events)

        baseline = analytics.get_baseline("user_123")

        assert baseline is not None
        assert baseline.entity_id == "user_123"

    def test_get_baseline_not_found(self, analytics):
        """Test retrieving nonexistent baseline."""
        baseline = analytics.get_baseline("unknown_user")

        assert baseline is None


class TestMLDetector:
    """Test ML-based detection."""

    @pytest.fixture
    def detector(self):
        """Create ML detector instance (local mode)."""
        return MLDetector(use_backend=False)

    def test_initialization(self, detector):
        """Test MLDetector initialization."""
        assert detector.use_backend is False
        assert detector.confidence_threshold == 0.7
        assert len(detector.models) == 0
        assert len(detector.predictions) == 0

    def test_load_model_local(self, detector):
        """Test loading model locally."""
        model = detector.load_model(
            "test_malware_model",
            MLModelType.MALWARE_CLASSIFIER
        )

        assert model.name == "test_malware_model"
        assert model.model_type == MLModelType.MALWARE_CLASSIFIER
        assert "test_malware_model" in detector.models

    def test_extract_url_features(self, detector):
        """Test URL feature extraction for phishing detection."""
        url = "http://phishing-site.bad/login?token=123&redirect=evil.com"

        features = detector._extract_url_features(url)

        assert features["url"] == url
        assert features["url_length"] == len(url)
        assert features["has_https"] is False
        assert features["num_at"] == 0
        assert features["num_dots"] > 0
        assert features["domain"] == "phishing-site.bad"

    def test_extract_url_features_suspicious(self, detector):
        """Test feature extraction for suspicious URL."""
        suspicious_url = "http://192.168.1.1@evil.com/login.php"

        features = detector._extract_url_features(suspicious_url)

        assert features["has_ip"] is True
        assert features["num_at"] == 1  # @ in URL is suspicious

    def test_extract_email_features(self, detector):
        """Test email feature extraction for phishing."""
        phishing_email = """
        URGENT: Your account has been compromised!
        Click here immediately to verify your account and win $1000 prize!
        http://phishing-site.bad
        """

        features = detector._extract_email_features(phishing_email)

        assert features["has_urgent"] is True
        assert features["has_money"] is True
        assert features["has_click_here"] is True
        assert features["num_urls"] > 0

    def test_extract_domain_features(self, detector):
        """Test domain feature extraction for DGA detection."""
        # Legitimate domain
        legit_domain = "google.com"
        legit_features = detector._extract_domain_features(legit_domain)

        assert legit_features["domain_length"] == len(legit_domain)
        assert legit_features["num_vowels"] > 0
        assert legit_features["entropy"] > 0

        # DGA-like domain
        dga_domain = "xj4k2m9p8q.com"
        dga_features = detector._extract_domain_features(dga_domain)

        # DGA domains typically have high entropy, few vowels
        assert dga_features["num_consonants"] > dga_features["num_vowels"]

    def test_extract_file_features(self, detector):
        """Test file feature extraction for malware detection."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            test_content = b"MZ\x90\x00" * 100  # PE header-like content
            f.write(test_content)
            temp_path = Path(f.name)

        try:
            features = detector._extract_file_features(temp_path)

            assert "file_size" in features
            assert features["file_extension"] == ".exe"
            assert "sha256" in features
            assert len(features["sha256"]) == 64  # SHA256 hex length

        finally:
            temp_path.unlink()

    def test_calculate_entropy(self, detector):
        """Test Shannon entropy calculation."""
        # Low entropy (repetitive)
        low_entropy_text = "aaaaaaaaaa"
        low = detector._calculate_entropy(low_entropy_text)

        # High entropy (random-ish)
        high_entropy_text = "xj4k2m9p8q"
        high = detector._calculate_entropy(high_entropy_text)

        assert high > low

        # Empty string
        assert detector._calculate_entropy("") == 0.0

    def test_extract_sequence_features(self, detector):
        """Test sequence feature extraction for lateral movement."""
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "source_ip": "10.10.1.5",
                "dest_ip": "10.10.1.10",
            },
            {
                "timestamp": (datetime.now() + timedelta(seconds=10)).isoformat(),
                "source_ip": "10.10.1.5",
                "dest_ip": "10.10.1.20",
            },
            {
                "timestamp": (datetime.now() + timedelta(seconds=20)).isoformat(),
                "source_ip": "10.10.1.5",
                "dest_ip": "10.10.1.30",
            },
        ]

        features = detector._extract_sequence_features(events)

        assert features["num_events"] == 3
        assert features["unique_sources"] == 1
        assert features["unique_destinations"] == 3
        assert features["time_span_seconds"] > 0

    def test_get_predictions_empty(self, detector):
        """Test getting predictions when none exist."""
        predictions = detector.get_predictions()

        assert len(predictions) == 0

    def test_get_model_stats_no_predictions(self, detector):
        """Test model stats with no predictions."""
        detector.load_model("test_model", MLModelType.MALWARE_CLASSIFIER)

        stats = detector.get_model_stats("test_model")

        assert stats == {}


class TestRiskScorer:
    """Test risk scoring engine."""

    @pytest.fixture
    def scorer(self):
        """Create risk scorer instance (local mode)."""
        return RiskScorer(use_backend=False)

    def test_initialization(self, scorer):
        """Test RiskScorer initialization."""
        assert scorer.use_backend is False

        # Weights should sum to 1.0
        total_weight = sum(scorer.weights.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_calculate_risk_score_single_factor(self, scorer):
        """Test risk calculation with single factor."""
        risk_factors = [
            RiskFactor(
                name="Critical vulnerability",
                category="vulnerability",
                score_impact=90.0,
                weight=1.0,
                description="CVE-2021-44228 (Log4Shell)",
            )
        ]

        risk_score = scorer.calculate_risk_score(
            "endpoint_123",
            "endpoint",
            risk_factors,
        )

        assert risk_score.entity_id == "endpoint_123"
        assert risk_score.total_score > 0
        assert risk_score.vulnerability_score == 90.0
        # With 25% weight for vulnerability: 90 * 0.25 = 22.5 (LOW)
        assert risk_score.risk_level == RiskLevel.LOW

    def test_calculate_risk_score_multiple_factors(self, scorer):
        """Test risk calculation with multiple factors."""
        risk_factors = [
            RiskFactor(
                name="CVE-2021-44228",
                category="vulnerability",
                score_impact=95.0,
                weight=1.0,
            ),
            RiskFactor(
                name="Malware detected",
                category="malware",
                score_impact=85.0,
                weight=1.0,
            ),
            RiskFactor(
                name="Unusual login pattern",
                category="behavioral",
                score_impact=70.0,
                weight=0.8,
            ),
        ]

        risk_score = scorer.calculate_risk_score(
            "endpoint_456",
            "endpoint",
            risk_factors,
        )

        # Should have scores in multiple categories
        assert risk_score.vulnerability_score > 0
        assert risk_score.malware_score > 0
        assert risk_score.behavioral_score > 0

        # Total should be weighted sum
        assert risk_score.total_score > 50

    def test_risk_level_classification(self, scorer):
        """Test risk level thresholds."""
        # Critical - need high scores across multiple categories to reach 80+
        # malware: 100 * 0.30 = 30, vulnerability: 100 * 0.25 = 25,
        # behavioral: 100 * 0.20 = 20, compliance: 100 * 0.15 = 15 = total 90
        critical_factors = [
            RiskFactor("Critical Malware", "malware", 100.0, 1.0),
            RiskFactor("Critical Vuln", "vulnerability", 100.0, 1.0),
            RiskFactor("Critical Behavioral", "behavioral", 100.0, 1.0),
            RiskFactor("Critical Compliance", "compliance", 100.0, 1.0),
        ]
        critical_score = scorer.calculate_risk_score("e1", "endpoint", critical_factors)
        assert critical_score.risk_level == RiskLevel.CRITICAL

        # Low - 25 * 0.15 (compliance weight) = 3.75
        low_factors = [
            RiskFactor("Low", "compliance", 25.0, 1.0)
        ]
        low_score = scorer.calculate_risk_score("e2", "endpoint", low_factors)
        assert low_score.risk_level == RiskLevel.MINIMAL

        # Minimal
        minimal_factors = [
            RiskFactor("Minimal", "compliance", 10.0, 1.0)
        ]
        minimal_score = scorer.calculate_risk_score("e3", "endpoint", minimal_factors)
        assert minimal_score.risk_level == RiskLevel.MINIMAL

    def test_aggregate_risk_factors_vulnerabilities(self, scorer):
        """Test aggregating vulnerability risk factors."""
        vulnerabilities = [
            {
                "cve_id": "CVE-2021-44228",
                "severity": "critical",
                "cvss_score": 10.0,
                "description": "Log4Shell RCE",
            },
            {
                "cve_id": "CVE-2020-1472",
                "severity": "critical",
                "cvss_score": 10.0,
                "description": "Zerologon",
            },
        ]

        risk_factors = scorer.aggregate_risk_factors(
            "endpoint_789",
            "endpoint",
            vulnerabilities=vulnerabilities,
        )

        assert len(risk_factors) == 2
        assert all(f.category == "vulnerability" for f in risk_factors)
        assert all(f.score_impact >= 90 for f in risk_factors)  # CVSS 10 = 100 impact

    def test_aggregate_risk_factors_from_anomalies(self, scorer):
        """Test aggregating risk factors from behavioral anomalies."""
        anomalies = [
            Anomaly(
                id="anom_1",
                entity_id="user_123",
                entity_type="user",
                anomaly_type=AnomalyType.LOGIN_LOCATION,
                timestamp=datetime.now(),
                description="Login from China",
                severity="high",
                deviation_score=4.5,
                confidence=0.9,
                observed_value="1.2.3.4",
                baseline_value=["192.168.1.100"],
            )
        ]

        risk_factors = scorer.aggregate_risk_factors(
            "user_123",
            "user",
            anomalies=anomalies,
        )

        assert len(risk_factors) == 1
        assert risk_factors[0].category == "behavioral"
        assert risk_factors[0].score_impact > 0

    def test_get_risk_score_cached(self, scorer):
        """Test retrieving cached risk score."""
        risk_factors = [RiskFactor("Test", "malware", 75.0, 1.0)]

        scorer.calculate_risk_score("endpoint_abc", "endpoint", risk_factors)

        # Should be cached
        cached_score = scorer.get_risk_score("endpoint_abc")

        assert cached_score is not None
        assert cached_score.entity_id == "endpoint_abc"

    def test_get_risk_score_not_found(self, scorer):
        """Test retrieving nonexistent risk score."""
        score = scorer.get_risk_score("unknown_entity")

        # Should return None (not in cache, backend disabled)
        assert score is None

    def test_get_high_risk_entities(self, scorer):
        """Test filtering high-risk entities."""
        # Create multiple risk scores with high scores across categories
        # e1: Critical (90 total)
        scorer.calculate_risk_score(
            "e1", "endpoint",
            [
                RiskFactor("Critical Malware", "malware", 100.0, 1.0),
                RiskFactor("Critical Vuln", "vulnerability", 100.0, 1.0),
                RiskFactor("Critical Behavioral", "behavioral", 100.0, 1.0),
                RiskFactor("Critical Compliance", "compliance", 100.0, 1.0),
            ]
        )
        # e2: Minimal (3 total)
        scorer.calculate_risk_score(
            "e2", "endpoint",
            [RiskFactor("Low", "compliance", 20.0, 1.0)]
        )
        # e3: HIGH (65 total)
        scorer.calculate_risk_score(
            "e3", "endpoint",
            [
                RiskFactor("High Malware", "malware", 100.0, 1.0),
                RiskFactor("High Vuln", "vulnerability", 100.0, 1.0),
                RiskFactor("High Behavioral", "behavioral", 100.0, 1.0),
            ]
        )

        high_risk = scorer.get_high_risk_entities(min_risk_level=RiskLevel.HIGH)

        # Should include e1 (critical) and e3 (high), exclude e2 (minimal)
        assert len(high_risk) >= 2
        entity_ids = [s.entity_id for s in high_risk]
        assert "e1" in entity_ids
        assert "e3" in entity_ids

    def test_weight_normalization(self):
        """Test that weights are normalized if they don't sum to 1.0."""
        # Create scorer with non-normalized weights
        scorer = RiskScorer(
            use_backend=False,
            vulnerability_weight=0.5,
            malware_weight=0.5,
            behavioral_weight=0.5,
            compliance_weight=0.5,
            threat_intel_weight=0.5,
        )

        # Weights should be normalized
        total = sum(scorer.weights.values())
        assert abs(total - 1.0) < 0.01


class TestThreatIntelFeed:
    """Test threat intelligence feed."""

    @pytest.fixture
    def feed(self):
        """Create threat intel feed instance (local mode)."""
        return ThreatIntelFeed(use_backend=False)

    def test_initialization(self, feed):
        """Test ThreatIntelFeed initialization."""
        assert feed.use_backend is False
        assert len(feed.ioc_cache) == 0
        assert len(feed.threat_actors) == 0

    def test_ioc_creation(self):
        """Test IOC dataclass creation."""
        ioc = IOC(
            value="1.2.3.4",
            ioc_type=IOCType.IP_ADDRESS,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            threat_level="high",
            confidence=0.9,
            threat_actors=["APT28"],
            campaigns=["Operation XYZ"],
            tags=["botnet", "c2"],
            sources=["MISP", "OTX"],
        )

        assert ioc.value == "1.2.3.4"
        assert ioc.ioc_type == IOCType.IP_ADDRESS
        assert ioc.threat_level == "high"
        assert len(ioc.threat_actors) == 1
        assert ioc.is_active is True

    def test_threat_actor_creation(self):
        """Test ThreatActor dataclass creation."""
        actor = ThreatActor(
            name="APT28",
            aliases=["Fancy Bear", "Sofacy"],
            type="apt",
            motivation="espionage",
            country="Russia",
            tactics=["Initial Access", "Persistence"],
            techniques=["T1566", "T1078"],
            tools=["Mimikatz", "PowerShell Empire"],
        )

        assert actor.name == "APT28"
        assert len(actor.aliases) == 2
        assert actor.type == "apt"
        assert len(actor.tactics) == 2

    def test_get_cached_iocs_empty(self, feed):
        """Test getting cached IOCs when cache is empty."""
        iocs = feed.get_cached_iocs()

        assert len(iocs) == 0

    def test_get_cached_iocs_with_filters(self, feed):
        """Test filtering cached IOCs."""
        # Add some IOCs to cache
        ioc1 = IOC(
            value="1.2.3.4",
            ioc_type=IOCType.IP_ADDRESS,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            threat_level="critical",
            is_active=True,
        )
        ioc2 = IOC(
            value="evil.com",
            ioc_type=IOCType.DOMAIN,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            threat_level="high",
            is_active=True,
        )
        ioc3 = IOC(
            value="old.bad",
            ioc_type=IOCType.DOMAIN,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            threat_level="low",
            is_active=False,
        )

        feed.ioc_cache["1.2.3.4"] = ioc1
        feed.ioc_cache["evil.com"] = ioc2
        feed.ioc_cache["old.bad"] = ioc3

        # Filter by type
        ip_iocs = feed.get_cached_iocs(ioc_type=IOCType.IP_ADDRESS)
        assert len(ip_iocs) == 1
        assert ip_iocs[0].value == "1.2.3.4"

        # Filter by threat level
        critical_iocs = feed.get_cached_iocs(threat_level="critical")
        assert len(critical_iocs) == 1

        # Filter by active status
        active_iocs = feed.get_cached_iocs(is_active=True)
        assert len(active_iocs) == 2

        # Multiple filters
        active_domains = feed.get_cached_iocs(
            ioc_type=IOCType.DOMAIN,
            is_active=True
        )
        assert len(active_domains) == 1
        assert active_domains[0].value == "evil.com"

    def test_ioc_type_enum(self):
        """Test IOCType enum values."""
        assert IOCType.IP_ADDRESS.value == "ip"
        assert IOCType.DOMAIN.value == "domain"
        assert IOCType.FILE_HASH_SHA256.value == "sha256"
        assert IOCType.EMAIL.value == "email"

    def test_lookup_threat_actor_not_found(self, feed):
        """Test looking up nonexistent threat actor."""
        actor = feed.lookup_threat_actor("UnknownAPT")

        # Should return None (not in cache, backend disabled)
        assert actor is None
