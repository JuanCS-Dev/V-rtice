"""Unit tests for AIProcessorRefactored.

Tests the production-hardened AI Processor with 100% coverage.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest

from ai_processor_refactored import AIProcessorRefactored


@pytest.fixture(autouse=True)
def mock_cache_globally(monkeypatch):
    """Global fixture to mock cache operations."""
    async def get_mock(self, key):
        return None

    async def set_mock(self, key, value):
        pass

    from core.cache_manager import CacheManager
    monkeypatch.setattr(CacheManager, "get", get_mock)
    monkeypatch.setattr(CacheManager, "set", set_mock)


class TestAIProcessorBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_processor_initialization(self):
        """Test processor initializes correctly."""
        processor = AIProcessorRefactored()

        assert processor.total_processing_tasks == 0
        assert processor.total_entities_extracted == 0
        assert len(processor.entity_patterns) > 0
        assert len(processor.sentiment_keywords) > 0
        assert processor.logger is not None
        assert processor.metrics is not None

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method."""
        processor = AIProcessorRefactored()

        repr_str = repr(processor)

        assert "AIProcessorRefactored" in repr_str
        assert "tasks=0" in repr_str
        assert "entities=0" in repr_str


class TestInputValidation:
    """Input validation tests."""

    @pytest.mark.asyncio
    async def test_query_without_text_raises_error(self):
        """Test querying without text raises ValueError."""
        processor = AIProcessorRefactored()

        with pytest.raises(ValueError, match="Text parameter is required"):
            await processor.query(target="investigation_123")

    @pytest.mark.asyncio
    async def test_query_with_invalid_text_type_raises_error(self):
        """Test querying with non-string text raises ValueError."""
        processor = AIProcessorRefactored()

        with pytest.raises(ValueError, match="Text must be a string"):
            await processor.query(target="investigation_123", text=12345)


class TestTextSummarization:
    """Text summarization tests."""

    @pytest.mark.asyncio
    async def test_summarize_simple_text(self):
        """Test text summarization with simple text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_123",
            text="Hello world. This is a test. Testing summarization.",
            processing_types=["summarize"]
        )

        assert "summary" in result
        assert result["summary"]["word_count"] == 8
        assert result["summary"]["sentence_count"] == 3
        assert result["summary"]["character_count"] > 0
        assert "key_words" in result["summary"]

    @pytest.mark.asyncio
    async def test_summarize_long_text_preview(self):
        """Test summarization creates preview for long text."""
        processor = AIProcessorRefactored()

        long_text = "word " * 100  # 500 characters

        result = await processor.query(
            target="case_456",
            text=long_text,
            processing_types=["summarize"]
        )

        assert len(result["summary"]["preview"]) == 203  # 200 + "..."
        assert result["summary"]["preview"].endswith("...")

    @pytest.mark.asyncio
    async def test_summarize_empty_text(self):
        """Test summarization handles empty text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_789",
            text="",
            processing_types=["summarize"]
        )

        assert result["summary"]["word_count"] == 0
        assert result["summary"]["sentence_count"] == 1


class TestEntityExtraction:
    """Entity extraction tests."""

    @pytest.mark.asyncio
    async def test_extract_email_addresses(self):
        """Test extraction of email addresses."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="investigation_123",
            text="Contact user@example.com or admin@test.org for details",
            processing_types=["extract_entities"]
        )

        assert "entities" in result
        assert "email" in result["entities"]
        assert len(result["entities"]["email"]) == 2

        emails = [e["value"] for e in result["entities"]["email"]]
        assert "user@example.com" in emails
        assert "admin@test.org" in emails

    @pytest.mark.asyncio
    async def test_extract_phone_numbers(self):
        """Test extraction of phone numbers."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="investigation_456",
            text="Call 555-123-4567 or 555.987.6543 for support",
            processing_types=["extract_entities"]
        )

        assert "phone" in result["entities"]
        assert len(result["entities"]["phone"]) >= 1

    @pytest.mark.asyncio
    async def test_extract_urls(self):
        """Test extraction of URLs."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="investigation_789",
            text="Visit https://example.com or http://test.org for more info",
            processing_types=["extract_entities"]
        )

        assert "url" in result["entities"]
        assert len(result["entities"]["url"]) == 2

    @pytest.mark.asyncio
    async def test_extract_ipv4_addresses(self):
        """Test extraction of IPv4 addresses."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="investigation_001",
            text="Server at 192.168.1.1 and 10.0.0.1 are down",
            processing_types=["extract_entities"]
        )

        assert "ipv4" in result["entities"]
        assert len(result["entities"]["ipv4"]) == 2

    @pytest.mark.asyncio
    async def test_extract_md5_hashes(self):
        """Test extraction of MD5 hashes."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="investigation_002",
            text="MD5: 5d41402abc4b2a76b9719d911017c592",
            processing_types=["extract_entities"]
        )

        assert "md5" in result["entities"]
        assert len(result["entities"]["md5"]) == 1
        assert result["entities"]["md5"][0]["value"] == "5d41402abc4b2a76b9719d911017c592"
        assert result["entities"]["md5"][0]["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_extract_sha256_hashes(self):
        """Test extraction of SHA256 hashes."""
        processor = AIProcessorRefactored()

        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        result = await processor.query(
            target="investigation_003",
            text=f"SHA256: {sha256}",
            processing_types=["extract_entities"]
        )

        assert "sha256" in result["entities"]
        assert len(result["entities"]["sha256"]) == 1

    @pytest.mark.asyncio
    async def test_extract_no_entities(self):
        """Test extraction when no entities are present."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="investigation_004",
            text="This is plain text with no special entities",
            processing_types=["extract_entities"]
        )

        assert result["entities"] == {}


class TestSentimentAnalysis:
    """Sentiment analysis tests."""

    @pytest.mark.asyncio
    async def test_analyze_positive_sentiment(self):
        """Test analysis of positive sentiment text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_123",
            text="This is great excellent good positive success happy love",
            processing_types=["sentiment"]
        )

        assert "sentiment" in result
        assert result["sentiment"]["overall"] == "positive"
        assert result["sentiment"]["positive"] > result["sentiment"]["negative"]
        assert result["sentiment"]["positive_keywords_found"] > 0

    @pytest.mark.asyncio
    async def test_analyze_negative_sentiment(self):
        """Test analysis of negative sentiment text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_456",
            text="This is bad terrible negative fail worst sad hate",
            processing_types=["sentiment"]
        )

        assert result["sentiment"]["overall"] == "negative"
        assert result["sentiment"]["negative"] > result["sentiment"]["positive"]
        assert result["sentiment"]["negative_keywords_found"] > 0

    @pytest.mark.asyncio
    async def test_analyze_neutral_sentiment(self):
        """Test analysis of neutral sentiment text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_789",
            text="The system operates normally and processes data efficiently",
            processing_types=["sentiment"]
        )

        assert result["sentiment"]["overall"] == "neutral"
        assert result["sentiment"]["neutral"] > 0.9

    @pytest.mark.asyncio
    async def test_analyze_empty_text_sentiment(self):
        """Test sentiment analysis on empty text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_000",
            text="",
            processing_types=["sentiment"]
        )

        assert result["sentiment"]["neutral"] == 1.0
        assert result["sentiment"]["positive"] == 0.0
        assert result["sentiment"]["negative"] == 0.0

    @pytest.mark.asyncio
    async def test_sentiment_score_rounding(self):
        """Test sentiment scores are properly rounded."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_001",
            text="good great excellent",
            processing_types=["sentiment"]
        )

        # Check scores are rounded to 3 decimal places
        assert isinstance(result["sentiment"]["positive"], float)
        assert len(str(result["sentiment"]["positive"]).split('.')[-1]) <= 3


class TestTextClassification:
    """Text classification tests."""

    @pytest.mark.asyncio
    async def test_classify_security_text(self):
        """Test classification of security-related text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_123",
            text="Malware detected with vulnerability exploit threat attack breach",
            processing_types=["classify"]
        )

        assert "classification" in result
        assert result["classification"]["primary_category"] == "security"
        assert result["classification"]["confidence"] > 0
        assert "security" in result["classification"]["all_categories"]

    @pytest.mark.asyncio
    async def test_classify_technical_text(self):
        """Test classification of technical text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_456",
            text="The API connects to the server database system using code and software",
            processing_types=["classify"]
        )

        assert result["classification"]["primary_category"] == "technical"

    @pytest.mark.asyncio
    async def test_classify_social_text(self):
        """Test classification of social text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_789",
            text="User profile in social network community with people",
            processing_types=["classify"]
        )

        assert result["classification"]["primary_category"] == "social"

    @pytest.mark.asyncio
    async def test_classify_business_text(self):
        """Test classification of business text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_001",
            text="Company business market revenue customer sale",
            processing_types=["classify"]
        )

        assert result["classification"]["primary_category"] == "business"

    @pytest.mark.asyncio
    async def test_classify_legal_text(self):
        """Test classification of legal text."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_002",
            text="Law legal court attorney regulation compliance",
            processing_types=["classify"]
        )

        assert result["classification"]["primary_category"] == "legal"

    @pytest.mark.asyncio
    async def test_classify_general_text(self):
        """Test classification of text with no specific category."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_003",
            text="Random unrelated content without specific keywords",
            processing_types=["classify"]
        )

        assert result["classification"]["primary_category"] == "general"
        assert result["classification"]["confidence"] == 0.0


class TestMultipleProcessingTypes:
    """Multiple processing type tests."""

    @pytest.mark.asyncio
    async def test_process_all_types(self):
        """Test processing with all types."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_123",
            text="Contact user@example.com about the excellent malware analysis",
            processing_types=["all"]
        )

        assert "summary" in result
        assert "entities" in result
        assert "sentiment" in result
        assert "classification" in result

    @pytest.mark.asyncio
    async def test_process_default_types(self):
        """Test processing with default types (all)."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_456",
            text="Test text"
        )

        # Default should process all types
        assert "summary" in result
        assert "entities" in result
        assert "sentiment" in result
        assert "classification" in result

    @pytest.mark.asyncio
    async def test_process_multiple_specific_types(self):
        """Test processing with multiple specific types."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_789",
            text="Good news from user@example.com",
            processing_types=["extract_entities", "sentiment"]
        )

        assert "entities" in result
        assert "sentiment" in result
        assert "summary" not in result
        assert "classification" not in result


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_statistics_updated_after_processing(self):
        """Test statistics are updated after processing."""
        processor = AIProcessorRefactored()

        await processor.query(
            target="case_123",
            text="Contact user@example.com",
            processing_types=["extract_entities"]
        )

        assert processor.total_processing_tasks == 1
        assert processor.total_entities_extracted >= 1

        first_count = processor.total_entities_extracted

        await processor.query(
            target="case_456",
            text="Email admin@test.org or call 555-1234",
            processing_types=["extract_entities"]
        )

        assert processor.total_processing_tasks == 2
        assert processor.total_entities_extracted > first_count  # Should have more entities

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status returns correct information."""
        processor = AIProcessorRefactored()

        status = await processor.get_status()

        assert status["tool"] == "AIProcessorRefactored"
        assert status["total_processing_tasks"] == 0
        assert status["total_entities_extracted"] == 0
        assert "available_entity_types" in status
        assert "available_processing_types" in status
        assert len(status["available_entity_types"]) == 6  # email, phone, url, ipv4, md5, sha256
        assert len(status["available_processing_types"]) == 4  # summarize, extract_entities, sentiment, classify


class TestObservability:
    """Observability tests."""

    @pytest.mark.asyncio
    async def test_logging_configured(self):
        """Test structured logger is configured."""
        processor = AIProcessorRefactored()

        assert processor.logger is not None
        assert processor.logger.tool_name == "AIProcessorRefactored"

    @pytest.mark.asyncio
    async def test_metrics_configured(self):
        """Test metrics collector is configured."""
        processor = AIProcessorRefactored()

        assert processor.metrics is not None
        assert processor.metrics.tool_name == "AIProcessorRefactored"


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_result_structure_complete(self):
        """Test result dictionary has all expected fields."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_123",
            text="Test text",
            query_context="Test investigation"
        )

        # Verify core fields
        assert "timestamp" in result
        assert "target" in result
        assert "query_context" in result
        assert "text_length" in result
        assert "processing_types" in result

    @pytest.mark.asyncio
    async def test_query_context_optional(self):
        """Test query_context is optional."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_456",
            text="Test text without context",
            processing_types=["summarize"]
        )

        assert result["query_context"] == ""

    @pytest.mark.asyncio
    async def test_text_length_recorded(self):
        """Test text length is recorded in result."""
        processor = AIProcessorRefactored()

        text = "Hello world"
        result = await processor.query(
            target="case_789",
            text=text,
            processing_types=["summarize"]
        )

        assert result["text_length"] == len(text)

    @pytest.mark.asyncio
    async def test_entity_confidence_scores(self):
        """Test extracted entities have confidence scores."""
        processor = AIProcessorRefactored()

        result = await processor.query(
            target="case_001",
            text="Email: user@example.com",
            processing_types=["extract_entities"]
        )

        assert result["entities"]["email"][0]["confidence"] == 1.0
        assert result["entities"]["email"][0]["type"] == "email"
