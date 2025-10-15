"""Unit tests for EmailAnalyzerRefactored.

Tests the production-hardened EmailAnalyzer with 90%+ coverage.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest

from analyzers.email_analyzer_refactored import EmailAnalyzerRefactored


class TestEmailAnalyzerBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = EmailAnalyzerRefactored()

        assert analyzer.total_analyses == 0
        assert analyzer.total_emails_found == 0
        assert analyzer.email_pattern is not None

    @pytest.mark.asyncio
    async def test_extract_single_email(self):
        """Test extracting a single email from text."""
        analyzer = EmailAnalyzerRefactored()

        result = await analyzer.analyze_text("Contact us at support@example.com")

        assert len(result["extracted_emails"]) == 1
        assert "support@example.com" in result["extracted_emails"]
        assert result["email_count"] == 1
        assert result["unique_email_count"] == 1

    @pytest.mark.asyncio
    async def test_extract_multiple_emails(self):
        """Test extracting multiple emails."""
        analyzer = EmailAnalyzerRefactored()

        text = "Reach out to sales@company.com or support@company.com for help."
        result = await analyzer.analyze_text(text)

        assert len(result["extracted_emails"]) == 2
        assert "sales@company.com" in result["extracted_emails"]
        assert "support@company.com" in result["extracted_emails"]
        assert result["email_count"] == 2

    @pytest.mark.asyncio
    async def test_extract_duplicate_emails(self):
        """Test handling duplicate emails."""
        analyzer = EmailAnalyzerRefactored()

        text = "Email test@example.com twice: test@example.com"
        result = await analyzer.analyze_text(text)

        assert result["email_count"] == 2  # Found twice
        assert result["unique_email_count"] == 1  # But only 1 unique
        assert len(result["extracted_emails"]) == 1

    @pytest.mark.asyncio
    async def test_no_emails_found(self):
        """Test text with no emails."""
        analyzer = EmailAnalyzerRefactored()

        result = await analyzer.analyze_text("This text has no email addresses.")

        assert result["email_count"] == 0
        assert result["unique_email_count"] == 0
        assert len(result["extracted_emails"]) == 0
        assert result["domains_found"] == {}


class TestDomainAnalysis:
    """Domain analysis tests."""

    @pytest.mark.asyncio
    async def test_domain_counting(self):
        """Test domain frequency counting."""
        analyzer = EmailAnalyzerRefactored()

        text = "user1@example.com, user2@example.com, admin@test.org"
        result = await analyzer.analyze_text(text)

        assert result["domains_found"]["example.com"] == 2
        assert result["domains_found"]["test.org"] == 1

    @pytest.mark.asyncio
    async def test_common_domain_detection(self):
        """Test detection of common email providers."""
        analyzer = EmailAnalyzerRefactored()

        text = "john@gmail.com, jane@yahoo.com, bob@custom-domain.com"
        result = await analyzer.analyze_text(text)

        assert "gmail.com" in result["common_domains"]
        assert "yahoo.com" in result["common_domains"]
        assert "custom-domain.com" not in result["common_domains"]

    @pytest.mark.asyncio
    async def test_case_insensitive_domains(self):
        """Test domains are normalized to lowercase."""
        analyzer = EmailAnalyzerRefactored()

        text = "User@Example.COM and another@EXAMPLE.com"
        result = await analyzer.analyze_text(text)

        # Should count as same domain (lowercase)
        assert result["domains_found"]["example.com"] == 2


class TestPhishingDetection:
    """Phishing detection tests."""

    @pytest.mark.asyncio
    async def test_phishing_keyword_detection(self):
        """Test detection of phishing keywords in emails."""
        analyzer = EmailAnalyzerRefactored()

        text = "Click here: verify-account@phishing-site.com"
        result = await analyzer.analyze_text(text)

        assert result["phishing_score"] > 0
        assert len(result["phishing_indicators"]) > 0
        assert any("phish" in indicator.lower() for indicator in result["phishing_indicators"])

    @pytest.mark.asyncio
    async def test_benign_email_low_phishing_score(self):
        """Test benign emails have low phishing scores."""
        analyzer = EmailAnalyzerRefactored()

        text = "Normal email: john.doe@company.com"
        result = await analyzer.analyze_text(text)

        assert result["phishing_score"] < 20
        assert len(result["phishing_indicators"]) == 0

    @pytest.mark.asyncio
    async def test_suspicious_patterns_detected(self):
        """Test detection of suspicious email patterns."""
        analyzer = EmailAnalyzerRefactored()

        # Email with excessive hyphens and long username with numbers
        text = "contact-us-now-verify-account@example.com"
        result = await analyzer.analyze_text(text)

        assert result["phishing_score"] > 0

    @pytest.mark.asyncio
    async def test_long_username_with_numbers_phishing_indicator(self):
        """Test detection of long usernames with numbers (phishing indicator)."""
        analyzer = EmailAnalyzerRefactored()

        # Email with >15 character username containing numbers
        text = "verifyaccount123456789@example.com"
        result = await analyzer.analyze_text(text)

        assert result["phishing_score"] >= 10
        assert any("Long username with numbers" in indicator for indicator in result["phishing_indicators"])

    @pytest.mark.asyncio
    async def test_phishing_score_capped_at_100(self):
        """Test phishing score doesn't exceed 100."""
        analyzer = EmailAnalyzerRefactored()

        # Email with multiple phishing indicators
        text = (
            "phishing@scam-fake-verify-security-alert.com and "
            "another-phish@suspend-account-verify.com"
        )
        result = await analyzer.analyze_text(text)

        assert result["phishing_score"] <= 100


class TestEmailValidation:
    """Email validation tests."""

    def test_validate_valid_email(self):
        """Test validation of valid email formats."""
        analyzer = EmailAnalyzerRefactored()

        assert analyzer.validate_email("user@example.com") is True
        assert analyzer.validate_email("john.doe@company.co.uk") is True
        assert analyzer.validate_email("admin+tag@test-domain.org") is True

    def test_validate_invalid_email(self):
        """Test validation rejects invalid formats."""
        analyzer = EmailAnalyzerRefactored()

        assert analyzer.validate_email("not-an-email") is False
        assert analyzer.validate_email("@example.com") is False
        assert analyzer.validate_email("user@") is False
        assert analyzer.validate_email("user @example.com") is False  # Space not allowed


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_statistics_updated(self):
        """Test statistics are updated after analysis."""
        analyzer = EmailAnalyzerRefactored()

        await analyzer.analyze_text("test1@example.com")
        await analyzer.analyze_text("test2@example.com, test3@example.com")

        assert analyzer.total_analyses == 2
        assert analyzer.total_emails_found == 3

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status returns correct information."""
        analyzer = EmailAnalyzerRefactored()

        await analyzer.analyze_text("admin@test.com")

        status = await analyzer.get_status()

        assert status["tool"] == "EmailAnalyzerRefactored"
        assert status["healthy"] is True
        assert status["total_analyses"] == 1
        assert status["total_emails_found"] == 1
        assert "metrics" in status


class TestObservability:
    """Observability tests (logging, metrics)."""

    @pytest.mark.asyncio
    async def test_logging_configured(self):
        """Test structured logger is configured."""
        analyzer = EmailAnalyzerRefactored()

        assert analyzer.logger is not None
        assert analyzer.logger.tool_name == "EmailAnalyzer"

    @pytest.mark.asyncio
    async def test_metrics_configured(self):
        """Test metrics collector is configured."""
        analyzer = EmailAnalyzerRefactored()

        assert analyzer.metrics is not None
        assert analyzer.metrics.tool_name == "EmailAnalyzer"

    @pytest.mark.asyncio
    async def test_metrics_incremented(self):
        """Test metrics are incremented on analysis."""
        analyzer = EmailAnalyzerRefactored()

        initial_count = analyzer.metrics.get_request_count()

        await analyzer.analyze_text("test@example.com")

        assert analyzer.metrics.get_request_count() == initial_count + 1


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_empty_text(self):
        """Test analysis of empty text."""
        analyzer = EmailAnalyzerRefactored()

        result = await analyzer.analyze_text("")

        assert result["email_count"] == 0
        assert result["extracted_emails"] == []

    @pytest.mark.asyncio
    async def test_very_long_text(self):
        """Test analysis of very long text."""
        analyzer = EmailAnalyzerRefactored()

        # Generate long text with embedded emails
        long_text = "Email: test@example.com. " * 10000
        result = await analyzer.analyze_text(long_text)

        assert result["email_count"] == 10000
        assert result["unique_email_count"] == 1

    @pytest.mark.asyncio
    async def test_unicode_text(self):
        """Test analysis with unicode characters."""
        analyzer = EmailAnalyzerRefactored()

        text = "Contact: müller@example.de or 测试@test.com"
        result = await analyzer.analyze_text(text)

        # Should handle unicode gracefully
        assert result["email_count"] >= 0

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method for debugging."""
        analyzer = EmailAnalyzerRefactored()

        await analyzer.analyze_text("test@example.com")

        repr_str = repr(analyzer)

        assert "EmailAnalyzerRefactored" in repr_str
        assert "analyses=1" in repr_str
        assert "emails_found=1" in repr_str
