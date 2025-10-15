"""Unit tests for ReportGeneratorRefactored.

Tests the production-hardened Report Generator with 100% coverage.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest

from report_generator_refactored import ReportGeneratorRefactored


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


class TestReportGeneratorBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_generator_initialization(self):
        """Test generator initializes correctly."""
        generator = ReportGeneratorRefactored()

        assert generator.total_reports_generated == 0
        assert len(generator.reports_by_format) == 4
        assert generator.logger is not None
        assert generator.metrics is not None

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method."""
        generator = ReportGeneratorRefactored()

        repr_str = repr(generator)

        assert "ReportGeneratorRefactored" in repr_str
        assert "reports=0" in repr_str


class TestInputValidation:
    """Input validation tests."""

    @pytest.mark.asyncio
    async def test_query_without_query_param_raises_error(self):
        """Test generating report without query raises ValueError."""
        generator = ReportGeneratorRefactored()

        with pytest.raises(ValueError, match="Query parameter is required"):
            await generator.query(
                target="investigation_123",
                investigation_type="social_media"
            )

    @pytest.mark.asyncio
    async def test_query_without_investigation_type_raises_error(self):
        """Test generating report without investigation type raises ValueError."""
        generator = ReportGeneratorRefactored()

        with pytest.raises(ValueError, match="Investigation type parameter is required"):
            await generator.query(
                target="investigation_123",
                query="Test query"
            )

    @pytest.mark.asyncio
    async def test_query_with_invalid_collected_data_type_raises_error(self):
        """Test generating report with non-list collected_data raises ValueError."""
        generator = ReportGeneratorRefactored()

        with pytest.raises(ValueError, match="Collected data must be a list"):
            await generator.query(
                target="investigation_123",
                query="Test query",
                investigation_type="social_media",
                collected_data="not a list"
            )

    @pytest.mark.asyncio
    async def test_query_with_invalid_analysis_results_type_raises_error(self):
        """Test generating report with non-dict analysis_results raises ValueError."""
        generator = ReportGeneratorRefactored()

        with pytest.raises(ValueError, match="Analysis results must be a dictionary"):
            await generator.query(
                target="investigation_123",
                query="Test query",
                investigation_type="social_media",
                analysis_results="not a dict"
            )

    @pytest.mark.asyncio
    async def test_query_with_invalid_report_format_raises_error(self):
        """Test generating report with invalid format raises ValueError."""
        generator = ReportGeneratorRefactored()

        with pytest.raises(ValueError, match="Invalid report format"):
            await generator.query(
                target="investigation_123",
                query="Test query",
                investigation_type="social_media",
                report_format="invalid_format"
            )


class TestMarkdownReportGeneration:
    """Markdown report generation tests."""

    @pytest.mark.asyncio
    async def test_generate_markdown_report_basic(self):
        """Test basic markdown report generation."""
        generator = ReportGeneratorRefactored()

        result = await generator.query(
            target="investigation_123",
            query="User investigation",
            investigation_type="social_media",
            report_format="markdown"
        )

        assert result["report_format"] == "markdown"
        assert isinstance(result["report_content"], str)
        assert "# OSINT Investigation Report" in result["report_content"]
        assert "User investigation" in result["report_content"]
        assert "social_media" in result["report_content"]

    @pytest.mark.asyncio
    async def test_generate_markdown_report_with_data(self):
        """Test markdown report with collected data."""
        generator = ReportGeneratorRefactored()

        collected_data = [
            {"source": "Twitter", "data": "Tweet content here"},
            {"source": "Facebook", "data": "Post content here"},
        ]

        result = await generator.query(
            target="investigation_456",
            query="Social media sweep",
            investigation_type="social_media",
            collected_data=collected_data,
            report_format="markdown"
        )

        assert "## Collected Data" in result["report_content"]
        assert "Twitter" in result["report_content"]
        assert "Facebook" in result["report_content"]

    @pytest.mark.asyncio
    async def test_generate_markdown_report_with_analysis(self):
        """Test markdown report with analysis results."""
        generator = ReportGeneratorRefactored()

        analysis_results = {
            "sentiment": {"overall": "positive", "score": 0.8},
            "entities": ["email@example.com", "555-1234"],
        }

        result = await generator.query(
            target="investigation_789",
            query="Sentiment analysis",
            investigation_type="analysis",
            analysis_results=analysis_results,
            report_format="markdown"
        )

        assert "## Key Findings" in result["report_content"]
        assert "sentiment" in result["report_content"].lower()

    @pytest.mark.asyncio
    async def test_markdown_report_limits_data_entries(self):
        """Test markdown report limits displayed data entries."""
        generator = ReportGeneratorRefactored()

        # Create 15 data entries
        collected_data = [{"source": f"Source{i}", "data": f"Data{i}"} for i in range(15)]

        result = await generator.query(
            target="investigation_001",
            query="Large dataset",
            investigation_type="bulk",
            collected_data=collected_data,
            report_format="markdown"
        )

        # Should show "... and 5 more entries"
        assert "and 5 more entries" in result["report_content"]


class TestJSONReportGeneration:
    """JSON report generation tests."""

    @pytest.mark.asyncio
    async def test_generate_json_report_basic(self):
        """Test basic JSON report generation."""
        generator = ReportGeneratorRefactored()

        result = await generator.query(
            target="investigation_123",
            query="API investigation",
            investigation_type="technical",
            report_format="json"
        )

        assert result["report_format"] == "json"
        assert isinstance(result["report_content"], dict)
        assert "report_metadata" in result["report_content"]
        assert "summary" in result["report_content"]

    @pytest.mark.asyncio
    async def test_json_report_includes_all_sections(self):
        """Test JSON report includes all expected sections."""
        generator = ReportGeneratorRefactored()

        collected_data = [{"source": "API", "data": "Response"}]
        analysis_results = {"finding": "Important discovery"}

        result = await generator.query(
            target="investigation_456",
            query="Complete investigation",
            investigation_type="full",
            collected_data=collected_data,
            analysis_results=analysis_results,
            report_format="json"
        )

        content = result["report_content"]
        assert content["report_metadata"]["query"] == "Complete investigation"
        assert content["summary"]["data_sources_count"] == 1
        assert content["summary"]["analysis_sections_count"] == 1
        assert content["analysis_results"] == analysis_results
        assert content["collected_data"] == collected_data


class TestSummaryReportGeneration:
    """Summary report generation tests."""

    @pytest.mark.asyncio
    async def test_generate_summary_report_basic(self):
        """Test basic summary report generation."""
        generator = ReportGeneratorRefactored()

        result = await generator.query(
            target="investigation_123",
            query="Quick summary",
            investigation_type="brief",
            report_format="summary"
        )

        assert result["report_format"] == "summary"
        assert isinstance(result["report_content"], str)
        assert "Quick summary" in result["report_content"]
        assert "brief" in result["report_content"]

    @pytest.mark.asyncio
    async def test_summary_report_shows_counts(self):
        """Test summary report shows data and analysis counts."""
        generator = ReportGeneratorRefactored()

        collected_data = [{"source": "A", "data": "1"}, {"source": "B", "data": "2"}]
        analysis_results = {"section1": "result1", "section2": "result2"}

        result = await generator.query(
            target="investigation_456",
            query="Count test",
            investigation_type="stats",
            collected_data=collected_data,
            analysis_results=analysis_results,
            report_format="summary"
        )

        assert "Data collected: 2 entries" in result["report_content"]
        assert "Analysis sections: 2" in result["report_content"]

    @pytest.mark.asyncio
    async def test_summary_report_limits_findings(self):
        """Test summary report limits displayed findings to top 5."""
        generator = ReportGeneratorRefactored()

        # Create 10 analysis sections
        analysis_results = {f"finding_{i}": f"result_{i}" for i in range(10)}

        result = await generator.query(
            target="investigation_789",
            query="Many findings",
            investigation_type="comprehensive",
            analysis_results=analysis_results,
            report_format="summary"
        )

        # Count how many findings are mentioned (should be <= 5)
        findings_mentioned = sum(1 for i in range(10) if f"finding_{i}" in result["report_content"].lower())
        assert findings_mentioned <= 5


class TestDetailedReportGeneration:
    """Detailed report generation tests."""

    @pytest.mark.asyncio
    async def test_generate_detailed_report_basic(self):
        """Test basic detailed report generation."""
        generator = ReportGeneratorRefactored()

        result = await generator.query(
            target="investigation_123",
            query="Full investigation",
            investigation_type="complete",
            report_format="detailed"
        )

        assert result["report_format"] == "detailed"
        assert isinstance(result["report_content"], str)
        assert "OSINT INVESTIGATION - DETAILED REPORT" in result["report_content"]
        assert "=" * 80 in result["report_content"]

    @pytest.mark.asyncio
    async def test_detailed_report_includes_all_data(self):
        """Test detailed report includes all collected data."""
        generator = ReportGeneratorRefactored()

        collected_data = [
            {"source": "Source1", "data": "Data1"},
            {"source": "Source2", "data": "Data2"},
            {"source": "Source3", "data": "Data3"},
        ]

        result = await generator.query(
            target="investigation_456",
            query="Complete dataset",
            investigation_type="full",
            collected_data=collected_data,
            report_format="detailed"
        )

        # All 3 entries should be present
        assert "Entry #1" in result["report_content"]
        assert "Entry #2" in result["report_content"]
        assert "Entry #3" in result["report_content"]
        assert "Source1" in result["report_content"]
        assert "Source2" in result["report_content"]
        assert "Source3" in result["report_content"]

    @pytest.mark.asyncio
    async def test_detailed_report_handles_dict_analysis(self):
        """Test detailed report handles dictionary analysis results."""
        generator = ReportGeneratorRefactored()

        analysis_results = {
            "section1": {"key1": "value1", "key2": "value2"},
            "section2": {"key3": "value3"},
        }

        result = await generator.query(
            target="investigation_789",
            query="Dict analysis",
            investigation_type="nested",
            analysis_results=analysis_results,
            report_format="detailed"
        )

        assert "[SECTION1]" in result["report_content"]
        assert "key1: value1" in result["report_content"]
        assert "[SECTION2]" in result["report_content"]

    @pytest.mark.asyncio
    async def test_detailed_report_handles_list_analysis(self):
        """Test detailed report handles list analysis results."""
        generator = ReportGeneratorRefactored()

        analysis_results = {
            "findings": ["finding1", "finding2", "finding3"],
        }

        result = await generator.query(
            target="investigation_001",
            query="List analysis",
            investigation_type="enumeration",
            analysis_results=analysis_results,
            report_format="detailed"
        )

        assert "[FINDINGS]" in result["report_content"]
        assert "- finding1" in result["report_content"]
        assert "- finding2" in result["report_content"]

    @pytest.mark.asyncio
    async def test_detailed_report_handles_string_analysis(self):
        """Test detailed report handles simple string/scalar analysis results."""
        generator = ReportGeneratorRefactored()

        analysis_results = {
            "conclusion": "Investigation complete",
            "confidence_score": 0.95,
        }

        result = await generator.query(
            target="investigation_002",
            query="Scalar analysis",
            investigation_type="simple",
            analysis_results=analysis_results,
            report_format="detailed"
        )

        assert "[CONCLUSION]" in result["report_content"]
        assert "Investigation complete" in result["report_content"]
        assert "[CONFIDENCE_SCORE]" in result["report_content"]
        assert "0.95" in result["report_content"]


class TestReportMetadata:
    """Report metadata tests."""

    @pytest.mark.asyncio
    async def test_result_includes_metadata(self):
        """Test result includes all metadata fields."""
        generator = ReportGeneratorRefactored()

        result = await generator.query(
            target="investigation_123",
            query="Metadata test",
            investigation_type="test",
            report_format="markdown"
        )

        assert "timestamp" in result
        assert "target" in result
        assert "query" in result
        assert "investigation_type" in result
        assert "report_format" in result
        assert "data_entries_count" in result
        assert "analysis_sections_count" in result
        assert "report_content" in result

    @pytest.mark.asyncio
    async def test_metadata_counts_accurate(self):
        """Test metadata counts are accurate."""
        generator = ReportGeneratorRefactored()

        collected_data = [{"a": 1}, {"b": 2}, {"c": 3}]
        analysis_results = {"r1": "v1", "r2": "v2"}

        result = await generator.query(
            target="investigation_456",
            query="Count accuracy",
            investigation_type="stats",
            collected_data=collected_data,
            analysis_results=analysis_results,
            report_format="json"
        )

        assert result["data_entries_count"] == 3
        assert result["analysis_sections_count"] == 2


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_statistics_updated_after_generation(self):
        """Test statistics are updated after report generation."""
        generator = ReportGeneratorRefactored()

        await generator.query(
            target="investigation_123",
            query="First report",
            investigation_type="test",
            report_format="markdown"
        )

        assert generator.total_reports_generated == 1
        assert generator.reports_by_format["markdown"] == 1

        await generator.query(
            target="investigation_456",
            query="Second report",
            investigation_type="test",
            report_format="json"
        )

        assert generator.total_reports_generated == 2
        assert generator.reports_by_format["markdown"] == 1
        assert generator.reports_by_format["json"] == 1

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status returns correct information."""
        generator = ReportGeneratorRefactored()

        status = await generator.get_status()

        assert status["tool"] == "ReportGeneratorRefactored"
        assert status["total_reports_generated"] == 0
        assert "reports_by_format" in status
        assert "available_formats" in status
        assert len(status["available_formats"]) == 4


class TestObservability:
    """Observability tests."""

    @pytest.mark.asyncio
    async def test_logging_configured(self):
        """Test structured logger is configured."""
        generator = ReportGeneratorRefactored()

        assert generator.logger is not None
        assert generator.logger.tool_name == "ReportGeneratorRefactored"

    @pytest.mark.asyncio
    async def test_metrics_configured(self):
        """Test metrics collector is configured."""
        generator = ReportGeneratorRefactored()

        assert generator.metrics is not None
        assert generator.metrics.tool_name == "ReportGeneratorRefactored"


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_default_format_is_markdown(self):
        """Test default report format is markdown."""
        generator = ReportGeneratorRefactored()

        result = await generator.query(
            target="investigation_123",
            query="Default format",
            investigation_type="test"
        )

        assert result["report_format"] == "markdown"

    @pytest.mark.asyncio
    async def test_empty_collected_data_handled(self):
        """Test empty collected data list is handled."""
        generator = ReportGeneratorRefactored()

        result = await generator.query(
            target="investigation_456",
            query="Empty data",
            investigation_type="test",
            collected_data=[],
            report_format="markdown"
        )

        assert result["data_entries_count"] == 0

    @pytest.mark.asyncio
    async def test_empty_analysis_results_handled(self):
        """Test empty analysis results dict is handled."""
        generator = ReportGeneratorRefactored()

        result = await generator.query(
            target="investigation_789",
            query="Empty analysis",
            investigation_type="test",
            analysis_results={},
            report_format="markdown"
        )

        assert result["analysis_sections_count"] == 0

    @pytest.mark.asyncio
    async def test_all_formats_work(self):
        """Test all report formats work correctly."""
        generator = ReportGeneratorRefactored()

        for fmt in ["markdown", "json", "summary", "detailed"]:
            result = await generator.query(
                target=f"investigation_{fmt}",
                query=f"Test {fmt}",
                investigation_type="format_test",
                report_format=fmt
            )

            assert result["report_format"] == fmt
            assert result["report_content"] is not None
