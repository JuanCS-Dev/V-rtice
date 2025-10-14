"""Unit tests for PhoneAnalyzerRefactored.

Tests the production-hardened PhoneAnalyzer with 90%+ coverage.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest

from analyzers.phone_analyzer_refactored import PhoneAnalyzerRefactored


class TestPhoneAnalyzerBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = PhoneAnalyzerRefactored()

        assert analyzer.total_analyses == 0
        assert analyzer.total_phones_found == 0
        assert analyzer.phone_pattern is not None

    @pytest.mark.asyncio
    async def test_extract_single_phone(self):
        """Test extracting a single phone number."""
        analyzer = PhoneAnalyzerRefactored()

        result = await analyzer.analyze_text("Call us at +1-555-123-4567")

        assert len(result["extracted_phone_numbers"]) == 1
        assert "+1-555-123-4567" in result["extracted_phone_numbers"]
        assert result["number_count"] == 1

    @pytest.mark.asyncio
    async def test_extract_multiple_phones(self):
        """Test extracting multiple phone numbers."""
        analyzer = PhoneAnalyzerRefactored()

        text = "US: +1-555-123-4567, UK: +44-20-1234-5678"
        result = await analyzer.analyze_text(text)

        assert len(result["extracted_phone_numbers"]) == 2
        assert result["number_count"] == 2

    @pytest.mark.asyncio
    async def test_extract_duplicate_phones(self):
        """Test handling duplicate phone numbers."""
        analyzer = PhoneAnalyzerRefactored()

        text = "Call +1-555-123-4567 or +1-555-123-4567 again"
        result = await analyzer.analyze_text(text)

        assert result["number_count"] == 2  # Found twice
        assert result["unique_number_count"] == 1  # But only 1 unique

    @pytest.mark.asyncio
    async def test_no_phones_found(self):
        """Test text with no phone numbers."""
        analyzer = PhoneAnalyzerRefactored()

        result = await analyzer.analyze_text("This text has no phones.")

        assert result["number_count"] == 0
        assert len(result["extracted_phone_numbers"]) == 0


class TestCountryDetection:
    """Country detection tests."""

    @pytest.mark.asyncio
    async def test_detect_usa_number(self):
        """Test detection of USA phone numbers."""
        analyzer = PhoneAnalyzerRefactored()

        result = await analyzer.analyze_text("+1-555-123-4567")

        assert "USA/Canada" in result["countries_found"]
        assert result["countries_found"]["USA/Canada"] == 1

    @pytest.mark.asyncio
    async def test_detect_uk_number(self):
        """Test detection of UK phone numbers."""
        analyzer = PhoneAnalyzerRefactored()

        result = await analyzer.analyze_text("+44-20-1234-5678")

        assert "UK" in result["countries_found"]

    @pytest.mark.asyncio
    async def test_detect_multiple_countries(self):
        """Test detection of phones from multiple countries."""
        analyzer = PhoneAnalyzerRefactored()

        text = "+1-555-1234, +44-20-1234, +49-30-12345"
        result = await analyzer.analyze_text(text)

        assert len(result["countries_found"]) >= 3
        assert "USA/Canada" in result["countries_found"]
        assert "UK" in result["countries_found"]
        assert "Germany" in result["countries_found"]

    @pytest.mark.asyncio
    async def test_unknown_country_code(self):
        """Test handling of unknown country codes."""
        analyzer = PhoneAnalyzerRefactored()

        # Use a number that matches the regex but has unknown country
        result = await analyzer.analyze_text("+999-555-123-4567")  # Unknown country code

        assert "Unknown" in result["countries_found"]


class TestPhoneNormalization:
    """Phone normalization tests."""

    @pytest.mark.asyncio
    async def test_normalize_removes_formatting(self):
        """Test normalization removes formatting characters."""
        analyzer = PhoneAnalyzerRefactored()

        result = await analyzer.analyze_text("+1 (555) 123-4567")

        # Normalized version should be in results
        assert "+15551234567" in result["normalized_numbers"]

    @pytest.mark.asyncio
    async def test_normalize_multiple_formats(self):
        """Test normalization handles different formats."""
        analyzer = PhoneAnalyzerRefactored()

        # Same number, different formats
        text = "+1-555-123-4567 and +1.555.123.4567 and (555) 123-4567"
        result = await analyzer.analyze_text(text)

        # Should find normalized versions
        assert len(result["normalized_numbers"]) >= 1


class TestSocialEngineeringDetection:
    """Social engineering risk detection tests."""

    @pytest.mark.asyncio
    async def test_detect_urgent_keyword(self):
        """Test detection of urgent keyword."""
        analyzer = PhoneAnalyzerRefactored()

        text = "URGENT: Call +1-555-123-4567 immediately!"
        result = await analyzer.analyze_text(text)

        assert result["social_engineering_score"] > 0
        assert len(result["risk_indicators"]) > 0

    @pytest.mark.asyncio
    async def test_detect_verify_account_keyword(self):
        """Test detection of verify account keyword."""
        analyzer = PhoneAnalyzerRefactored()

        text = "Verify your account by calling +1-555-123-4567"
        result = await analyzer.analyze_text(text)

        assert result["social_engineering_score"] > 0

    @pytest.mark.asyncio
    async def test_benign_text_low_risk_score(self):
        """Test benign text has low risk score."""
        analyzer = PhoneAnalyzerRefactored()

        text = "For customer service, call +1-555-123-4567"
        result = await analyzer.analyze_text(text)

        assert result["social_engineering_score"] < 30

    @pytest.mark.asyncio
    async def test_high_phone_count_increases_risk(self):
        """Test many phone numbers increases risk score."""
        analyzer = PhoneAnalyzerRefactored()

        # 6 different phone numbers
        text = "+1-555-0001, +1-555-0002, +1-555-0003, +1-555-0004, +1-555-0005, +1-555-0006"
        result = await analyzer.analyze_text(text)

        assert result["social_engineering_score"] > 0
        assert any("High phone count" in indicator for indicator in result["risk_indicators"])

    @pytest.mark.asyncio
    async def test_premium_rate_number_detected(self):
        """Test detection of premium rate numbers."""
        analyzer = PhoneAnalyzerRefactored()

        text = "Call 1-900-123-4567 for more info"
        result = await analyzer.analyze_text(text)

        assert result["social_engineering_score"] > 0
        assert any("Premium rate" in indicator for indicator in result["risk_indicators"])

    @pytest.mark.asyncio
    async def test_risk_score_capped_at_100(self):
        """Test risk score doesn't exceed 100."""
        analyzer = PhoneAnalyzerRefactored()

        # Text with many risk indicators
        text = (
            "URGENT! IMMEDIATELY verify your account at 1-900-555-1234 or "
            "security alert suspended prize winner confirm now act now "
            "+1-555-0001 +44-20-1234 +49-30-5678 +33-1-2345 +39-06-7890"
        )
        result = await analyzer.analyze_text(text)

        assert result["social_engineering_score"] <= 100


class TestPhoneValidation:
    """Phone number validation tests."""

    def test_validate_valid_phone(self):
        """Test validation of valid phone formats."""
        analyzer = PhoneAnalyzerRefactored()

        assert analyzer.validate_phone_number("+1-555-123-4567") is True
        assert analyzer.validate_phone_number("+44 20 1234 5678") is True
        assert analyzer.validate_phone_number("1-555-123-4567") is True

    def test_validate_invalid_phone(self):
        """Test validation rejects invalid formats."""
        analyzer = PhoneAnalyzerRefactored()

        assert analyzer.validate_phone_number("not-a-phone") is False
        assert analyzer.validate_phone_number("123") is False
        assert analyzer.validate_phone_number("abc-def-ghij") is False


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_statistics_updated(self):
        """Test statistics are updated after analysis."""
        analyzer = PhoneAnalyzerRefactored()

        await analyzer.analyze_text("+1-555-1234")
        await analyzer.analyze_text("+44-20-1234 +49-30-5678")

        assert analyzer.total_analyses == 2
        assert analyzer.total_phones_found == 3

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status returns correct information."""
        analyzer = PhoneAnalyzerRefactored()

        await analyzer.analyze_text("+1-555-1234")

        status = await analyzer.get_status()

        assert status["tool"] == "PhoneAnalyzerRefactored"
        assert status["healthy"] is True
        assert status["total_analyses"] == 1
        assert status["total_phones_found"] == 1


class TestObservability:
    """Observability tests (logging, metrics)."""

    @pytest.mark.asyncio
    async def test_logging_configured(self):
        """Test structured logger is configured."""
        analyzer = PhoneAnalyzerRefactored()

        assert analyzer.logger is not None
        assert analyzer.logger.tool_name == "PhoneAnalyzer"

    @pytest.mark.asyncio
    async def test_metrics_configured(self):
        """Test metrics collector is configured."""
        analyzer = PhoneAnalyzerRefactored()

        assert analyzer.metrics is not None

    @pytest.mark.asyncio
    async def test_metrics_incremented(self):
        """Test metrics are incremented on analysis."""
        analyzer = PhoneAnalyzerRefactored()

        initial_count = analyzer.metrics.get_request_count()

        await analyzer.analyze_text("+1-555-1234")

        assert analyzer.metrics.get_request_count() == initial_count + 1


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_empty_text(self):
        """Test analysis of empty text."""
        analyzer = PhoneAnalyzerRefactored()

        result = await analyzer.analyze_text("")

        assert result["number_count"] == 0

    @pytest.mark.asyncio
    async def test_very_long_text(self):
        """Test analysis of very long text."""
        analyzer = PhoneAnalyzerRefactored()

        long_text = "Phone: +1-555-1234. " * 5000
        result = await analyzer.analyze_text(long_text)

        assert result["number_count"] == 5000
        assert result["unique_number_count"] == 1

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method for debugging."""
        analyzer = PhoneAnalyzerRefactored()

        await analyzer.analyze_text("+1-555-1234")

        repr_str = repr(analyzer)

        assert "PhoneAnalyzerRefactored" in repr_str
        assert "analyses=1" in repr_str
        assert "phones_found=1" in repr_str
