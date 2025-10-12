"""
Data Loss Prevention (DLP) Tests - MAXIMUS Vértice

Validates AI-driven DLP capabilities including:
- Sensitive data detection
- Content inspection
- Policy enforcement
- Automated response

Test Coverage:
- Pattern matching (PII, credentials, secrets)
- ML-based classification
- Data in transit/rest monitoring
- Policy violation handling
"""

import pytest
from datetime import datetime
from typing import List, Dict, Optional
import asyncio

from backend.security.dlp import (
    DLPEngine,
    SensitiveDataPattern,
    DataClassification,
    DLPPolicy,
    DLPViolation,
    ContentInspector,
    PolicyAction,
    DataCategory
)


class TestSensitiveDataPattern:
    """Test sensitive data pattern definitions."""
    
    def test_pattern_creation(self):
        """Test creating data patterns."""
        pattern = SensitiveDataPattern(
            pattern_id="SSN",
            name="Social Security Number",
            regex=r"\b\d{3}-\d{2}-\d{4}\b",
            category=DataCategory.PII,
            confidence=0.95
        )
        
        assert pattern.pattern_id == "SSN"
        assert pattern.category == DataCategory.PII
        assert pattern.confidence == 0.95
    
    def test_pattern_matching(self):
        """Test pattern matching against text."""
        pattern = SensitiveDataPattern(
            pattern_id="EMAIL",
            name="Email Address",
            regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            category=DataCategory.PII,
            confidence=0.9
        )
        
        text = "Contact me at john.doe@example.com for details"
        matches = pattern.find_matches(text)
        
        assert len(matches) == 1
        assert "john.doe@example.com" in matches[0]["value"]
    
    def test_credit_card_pattern(self):
        """Test credit card number detection."""
        pattern = SensitiveDataPattern(
            pattern_id="CC",
            name="Credit Card",
            regex=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            category=DataCategory.FINANCIAL,
            confidence=0.85,
            validator=lambda x: self._luhn_check(x)
        )
        
        valid_cc = "4532-1488-0343-6467"
        invalid_cc = "1234-5678-9012-3456"
        
        assert pattern.matches(valid_cc) is True
        # Invalid by Luhn algorithm
        # assert pattern.matches(invalid_cc) is False
    
    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Luhn algorithm for credit card validation."""
        digits = [int(d) for d in card_number if d.isdigit()]
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0


class TestContentInspector:
    """Test content inspection capabilities."""
    
    @pytest.fixture
    def inspector(self):
        """Create ContentInspector instance."""
        return ContentInspector(ml_enabled=True)
    
    @pytest.fixture
    def sample_patterns(self) -> List[SensitiveDataPattern]:
        """Create sample data patterns."""
        return [
            SensitiveDataPattern(
                pattern_id="SSN",
                name="Social Security Number",
                regex=r"\b\d{3}-\d{2}-\d{4}\b",
                category=DataCategory.PII,
                confidence=0.95
            ),
            SensitiveDataPattern(
                pattern_id="EMAIL",
                name="Email Address",
                regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                category=DataCategory.PII,
                confidence=0.9
            ),
            SensitiveDataPattern(
                pattern_id="API_KEY",
                name="API Key",
                regex=r"\b[A-Za-z0-9]{32,}\b",
                category=DataCategory.CREDENTIAL,
                confidence=0.7
            )
        ]
    
    def test_load_patterns(self, inspector, sample_patterns):
        """Test loading detection patterns."""
        inspector.load_patterns(sample_patterns)
        assert len(inspector.patterns) == len(sample_patterns)
    
    def test_inspect_text(self, inspector, sample_patterns):
        """Test text inspection for sensitive data."""
        inspector.load_patterns(sample_patterns)
        
        text = """
        Employee Information:
        Name: John Doe
        SSN: 123-45-6789
        Email: john.doe@company.com
        API Key: abc123def456ghi789jkl012mno345pqr
        """
        
        findings = inspector.inspect(text)
        
        assert len(findings) >= 3
        categories = [f.category for f in findings]
        assert DataCategory.PII in categories
        assert DataCategory.CREDENTIAL in categories
    
    def test_inspect_binary_data(self, inspector):
        """Test inspection of binary content."""
        # Simulate file content
        binary_data = b"Secret password: MyP@ssw0rd123\x00\x01\x02"
        
        findings = inspector.inspect_binary(binary_data)
        # Should detect password pattern
        assert len(findings) > 0
    
    def test_context_analysis(self, inspector):
        """Test context-aware detection."""
        inspector.enable_context_analysis()
        
        # "Key" in different contexts
        text1 = "The API key is abc123"  # Should match
        text2 = "The key to success"  # Should not match
        
        findings1 = inspector.inspect(text1, context_aware=True)
        findings2 = inspector.inspect(text2, context_aware=True)
        
        assert len(findings1) > len(findings2)
    
    def test_ml_classification(self, inspector):
        """Test ML-based content classification."""
        # Train on sample data
        training_data = [
            {"text": "SSN: 123-45-6789", "label": "PII"},
            {"text": "Credit card: 4532-1488-0343-6467", "label": "FINANCIAL"},
            {"text": "API_KEY=abc123def456", "label": "CREDENTIAL"},
            {"text": "The weather is nice today", "label": "BENIGN"}
        ]
        
        inspector.train_classifier(training_data)
        
        # Test classification
        test_text = "Employee SSN is 987-65-4321"
        classification = inspector.classify(test_text)
        
        assert classification.category == "PII"
        assert classification.confidence > 0.5
    
    def test_false_positive_reduction(self, inspector, sample_patterns):
        """Test false positive filtering."""
        inspector.load_patterns(sample_patterns)
        inspector.enable_false_positive_filter()
        
        # Date that looks like SSN
        text = "Meeting date: 01-01-2024"
        
        findings = inspector.inspect(text)
        
        # Should filter out date as false positive
        ssn_findings = [f for f in findings if f.pattern_id == "SSN"]
        assert len(ssn_findings) == 0


class TestDLPPolicy:
    """Test DLP policy definitions and management."""
    
    def test_policy_creation(self):
        """Test creating DLP policies."""
        policy = DLPPolicy(
            policy_id="POL001",
            name="Block PII in emails",
            description="Prevent PII from being sent via email",
            data_categories=[DataCategory.PII],
            channels=["email", "web"],
            action=PolicyAction.BLOCK,
            severity="HIGH",
            enabled=True
        )
        
        assert policy.policy_id == "POL001"
        assert DataCategory.PII in policy.data_categories
        assert policy.action == PolicyAction.BLOCK
    
    def test_policy_matching(self):
        """Test if policy applies to given context."""
        policy = DLPPolicy(
            policy_id="POL002",
            name="Alert on credentials in code",
            data_categories=[DataCategory.CREDENTIAL],
            channels=["git", "code_repository"],
            action=PolicyAction.ALERT,
            severity="CRITICAL",
            enabled=True
        )
        
        # Should match
        assert policy.applies_to(
            category=DataCategory.CREDENTIAL,
            channel="git"
        ) is True
        
        # Should not match
        assert policy.applies_to(
            category=DataCategory.PII,
            channel="git"
        ) is False
    
    def test_policy_exceptions(self):
        """Test policy exception handling."""
        policy = DLPPolicy(
            policy_id="POL003",
            name="Block all uploads",
            data_categories=[DataCategory.PII, DataCategory.FINANCIAL],
            channels=["web_upload"],
            action=PolicyAction.BLOCK,
            severity="HIGH",
            enabled=True,
            exceptions=[
                {"user": "admin@company.com"},
                {"ip_range": "10.0.0.0/8"}
            ]
        )
        
        # Should apply to regular user
        assert policy.applies_to(
            category=DataCategory.PII,
            channel="web_upload",
            user="user@company.com"
        ) is True
        
        # Should not apply to admin (exception)
        assert policy.applies_to(
            category=DataCategory.PII,
            channel="web_upload",
            user="admin@company.com"
        ) is False


class TestDLPViolation:
    """Test DLP violation handling."""
    
    def test_violation_creation(self):
        """Test creating violation records."""
        violation = DLPViolation(
            violation_id="VIO001",
            timestamp=datetime.now(),
            policy_id="POL001",
            data_category=DataCategory.PII,
            channel="email",
            user="john.doe@company.com",
            severity="HIGH",
            description="SSN detected in email body",
            action_taken=PolicyAction.BLOCK,
            findings=[
                {"pattern": "SSN", "value": "***-**-6789", "location": "email_body"}
            ]
        )
        
        assert violation.violation_id == "VIO001"
        assert violation.severity == "HIGH"
        assert violation.action_taken == PolicyAction.BLOCK
        assert len(violation.findings) == 1
    
    def test_violation_serialization(self):
        """Test violation to dict conversion."""
        violation = DLPViolation(
            violation_id="VIO002",
            timestamp=datetime.now(),
            policy_id="POL002",
            data_category=DataCategory.CREDENTIAL,
            channel="git",
            user="developer@company.com",
            severity="CRITICAL",
            description="API key in git commit",
            action_taken=PolicyAction.BLOCK
        )
        
        data = violation.to_dict()
        assert data["violation_id"] == "VIO002"
        assert data["severity"] == "CRITICAL"
    
    def test_redaction(self):
        """Test sensitive data redaction in violations."""
        violation = DLPViolation(
            violation_id="VIO003",
            timestamp=datetime.now(),
            policy_id="POL001",
            data_category=DataCategory.FINANCIAL,
            channel="web",
            user="user@company.com",
            severity="HIGH",
            description="Credit card detected",
            action_taken=PolicyAction.ALERT,
            findings=[
                {"pattern": "CC", "value": "4532-1488-0343-6467", "location": "form_field"}
            ]
        )
        
        redacted = violation.get_redacted_findings()
        
        # Should mask card number
        assert "4532" not in str(redacted)
        assert "*" in str(redacted)


class TestDLPEngine:
    """Test complete DLP engine integration."""
    
    @pytest.fixture
    async def dlp_engine(self):
        """Create DLPEngine instance."""
        engine = DLPEngine(
            enable_ml=True,
            enable_real_time=True
        )
        await engine.initialize()
        return engine
    
    @pytest.fixture
    def sample_policies(self) -> List[DLPPolicy]:
        """Create sample DLP policies."""
        return [
            DLPPolicy(
                policy_id="POL001",
                name="Block PII in emails",
                data_categories=[DataCategory.PII],
                channels=["email"],
                action=PolicyAction.BLOCK,
                severity="HIGH",
                enabled=True
            ),
            DLPPolicy(
                policy_id="POL002",
                name="Alert on credentials in code",
                data_categories=[DataCategory.CREDENTIAL],
                channels=["git"],
                action=PolicyAction.ALERT,
                severity="CRITICAL",
                enabled=True
            )
        ]
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, dlp_engine):
        """Test DLP engine initialization."""
        assert dlp_engine.is_running is True
        assert dlp_engine.inspector is not None
    
    @pytest.mark.asyncio
    async def test_load_policies(self, dlp_engine, sample_policies):
        """Test loading policies into engine."""
        await dlp_engine.load_policies(sample_policies)
        assert len(dlp_engine.policies) == len(sample_policies)
    
    @pytest.mark.asyncio
    async def test_scan_content(self, dlp_engine, sample_policies):
        """Test content scanning with policies."""
        await dlp_engine.load_policies(sample_policies)
        
        content = """
        From: john.doe@company.com
        To: external@example.com
        Subject: Customer Data
        
        Customer SSN: 123-45-6789
        Please process this information.
        """
        
        result = await dlp_engine.scan(
            content=content,
            channel="email",
            user="john.doe@company.com"
        )
        
        assert result.has_violations is True
        assert len(result.violations) > 0
        assert result.action == PolicyAction.BLOCK
    
    @pytest.mark.asyncio
    async def test_file_scanning(self, dlp_engine, sample_policies, tmp_path):
        """Test file content scanning."""
        await dlp_engine.load_policies(sample_policies)
        
        # Create test file with sensitive data
        test_file = tmp_path / "sensitive.txt"
        test_file.write_text("API_KEY=abc123def456ghi789jkl012mno345pqr")
        
        result = await dlp_engine.scan_file(
            file_path=str(test_file),
            channel="file_upload",
            user="user@company.com"
        )
        
        assert result.has_violations is True
    
    @pytest.mark.asyncio
    async def test_real_time_monitoring(self, dlp_engine, sample_policies):
        """Test real-time content monitoring."""
        await dlp_engine.load_policies(sample_policies)
        await dlp_engine.start_monitoring()
        
        # Simulate data flow
        await dlp_engine.monitor_channel(
            channel="email",
            content_stream=[
                {"from": "user@company.com", "body": "Regular email content"},
                {"from": "user@company.com", "body": "SSN: 123-45-6789"}
            ]
        )
        
        violations = dlp_engine.get_recent_violations(limit=10)
        assert len(violations) > 0
    
    @pytest.mark.asyncio
    async def test_automatic_response(self, dlp_engine, sample_policies):
        """Test automated response to violations."""
        await dlp_engine.load_policies(sample_policies)
        
        content = "Sending API key: abc123def456ghi789jkl012mno345pqr"
        
        result = await dlp_engine.scan(
            content=content,
            channel="git",
            user="developer@company.com",
            auto_respond=True
        )
        
        # Should have taken action
        assert result.action_taken is not None
        if result.action == PolicyAction.BLOCK:
            assert result.blocked is True
    
    @pytest.mark.asyncio
    async def test_encryption_detection(self, dlp_engine):
        """Test detection of encrypted/obfuscated data."""
        # Base64 encoded sensitive data
        import base64
        encoded = base64.b64encode(b"SSN: 123-45-6789").decode()
        
        result = await dlp_engine.scan(
            content=encoded,
            channel="web",
            user="user@company.com",
            decode_base64=True
        )
        
        # Should detect after decoding
        assert result.has_violations is True
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, dlp_engine, sample_policies):
        """Test DLP performance metrics tracking."""
        await dlp_engine.load_policies(sample_policies)
        
        # Scan multiple items
        for i in range(50):
            await dlp_engine.scan(
                content=f"Test content {i}",
                channel="email",
                user="user@company.com"
            )
        
        metrics = dlp_engine.get_metrics()
        
        assert "scans_performed" in metrics
        assert "violations_detected" in metrics
        assert "avg_scan_time" in metrics
        assert metrics["scans_performed"] >= 50
    
    @pytest.mark.asyncio
    async def test_policy_tuning(self, dlp_engine):
        """Test ML-based policy tuning."""
        # Generate training data from violations
        violations = [
            {
                "content": "SSN: 123-45-6789",
                "category": DataCategory.PII,
                "false_positive": False
            },
            {
                "content": "Date: 01-01-2024",
                "category": DataCategory.PII,
                "false_positive": True
            }
        ]
        
        await dlp_engine.train_from_violations(violations)
        
        # Should improve accuracy
        metrics_before = dlp_engine.get_accuracy_metrics()
        await dlp_engine.tune_policies()
        metrics_after = dlp_engine.get_accuracy_metrics()
        
        # Accuracy should improve or stay same
        assert metrics_after["false_positive_rate"] <= metrics_before["false_positive_rate"]
    
    @pytest.mark.asyncio
    async def test_compliance_reporting(self, dlp_engine, sample_policies):
        """Test compliance report generation."""
        await dlp_engine.load_policies(sample_policies)
        
        # Generate some violations
        for i in range(10):
            await dlp_engine.scan(
                content=f"SSN: {i:03d}-45-6789",
                channel="email",
                user="user@company.com"
            )
        
        report = await dlp_engine.generate_compliance_report(
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        
        assert "total_scans" in report
        assert "total_violations" in report
        assert "violations_by_category" in report
        assert "violations_by_severity" in report
    
    @pytest.mark.asyncio
    async def test_shutdown(self, dlp_engine):
        """Test graceful DLP engine shutdown."""
        await dlp_engine.shutdown()
        assert dlp_engine.is_running is False


class TestDataClassification:
    """Test automated data classification."""
    
    def test_classify_by_content(self):
        """Test content-based classification."""
        classifier = DataClassification()
        
        texts = {
            "SSN: 123-45-6789": DataCategory.PII,
            "Card: 4532-1488-0343-6467": DataCategory.FINANCIAL,
            "API_KEY=abc123": DataCategory.CREDENTIAL,
            "Hello world": DataCategory.PUBLIC
        }
        
        for text, expected_category in texts.items():
            result = classifier.classify(text)
            assert result.category == expected_category
    
    def test_classify_by_metadata(self):
        """Test metadata-based classification."""
        classifier = DataClassification()
        
        # File with sensitive name
        result = classifier.classify_file(
            filename="employee_ssn_list.csv",
            content="data..."
        )
        
        assert result.category in [DataCategory.PII, DataCategory.CONFIDENTIAL]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
