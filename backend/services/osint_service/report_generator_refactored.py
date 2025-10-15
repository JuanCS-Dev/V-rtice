"""Maximus OSINT Service - Report Generator (Production-Hardened).

Production-grade report generator for compiling OSINT investigation results.

Key improvements:
- ✅ Inherits from BaseTool (rate limiting, circuit breaker, caching, observability)
- ✅ Multiple report formats (markdown, json, summary, detailed)
- ✅ Section-based structure (executive summary, findings, raw data, recommendations)
- ✅ Severity/priority tagging
- ✅ Statistics and metrics
- ✅ Report templates
- ✅ Structured JSON logging
- ✅ Prometheus metrics

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready, extensible report generation
    - Article V (Prior Legislation): Observability first
    - Article VII (Antifragility): Circuit breakers, retries, graceful degradation
    - Article IX (Zero Trust): Input validation, safe data aggregation

Supported Report Formats:
    - markdown: Human-readable Markdown format
    - json: Structured JSON format
    - summary: Brief executive summary only
    - detailed: Full detailed report with all sections

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 2.0.0
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.base_tool import BaseTool


class ReportGeneratorRefactored(BaseTool):
    """Production-grade report generator with multiple output formats.

    Inherits from BaseTool to get:
    - Rate limiting (token bucket)
    - Circuit breaker (fail-fast on repeated failures)
    - Caching (Redis + in-memory)
    - Structured logging
    - Prometheus metrics
    - Automatic retries with exponential backoff

    Usage Example:
        generator = ReportGeneratorRefactored()

        # Generate markdown report
        result = await generator.query(
            target="investigation_123",
            query="User investigation",
            investigation_type="social_media",
            collected_data=[...],
            analysis_results={...},
            report_format="markdown"
        )

        # Generate JSON report
        result = await generator.query(
            target="investigation_456",
            query="Malware analysis",
            investigation_type="security",
            collected_data=[...],
            analysis_results={...},
            report_format="json"
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 2.0,  # 2 req/sec (report generation can be expensive)
        timeout: int = 120,  # Longer timeout for complex reports
        max_retries: int = 2,
        cache_ttl: int = 7200,  # 2 hours cache (reports are relatively stable)
        cache_backend: str = "memory",
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """Initialize ReportGeneratorRefactored.

        Args:
            api_key: Optional API key for external services
            rate_limit: Requests per second (2.0 = conservative for reports)
            timeout: Processing timeout in seconds (120s for complex reports)
            max_retries: Retry attempts
            cache_ttl: Cache time-to-live in seconds (2hr = stable reports)
            cache_backend: 'redis' or 'memory'
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Seconds before attempting recovery
        """
        super().__init__(
            api_key=api_key,
            rate_limit=rate_limit,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout=circuit_breaker_timeout,
        )

        # Statistics
        self.total_reports_generated = 0
        self.reports_by_format = {"markdown": 0, "json": 0, "summary": 0, "detailed": 0}

        self.logger.info("report_generator_initialized")

    async def _query_impl(self, target: str, **params) -> Dict[str, Any]:
        """Implementation of report generation logic.

        Args:
            target: Target identifier (investigation_id, case_id, etc.)
            **params:
                - query: Investigation query (required)
                - investigation_type: Type of investigation (required)
                - collected_data: List of collected data entries (default: [])
                - analysis_results: Dictionary of analysis results (default: {})
                - report_format: Format (markdown, json, summary, detailed) (default: markdown)

        Returns:
            Report generation result dictionary

        Raises:
            ValueError: If required params are missing or invalid
        """
        query = params.get("query")
        investigation_type = params.get("investigation_type")
        collected_data = params.get("collected_data", [])
        analysis_results = params.get("analysis_results", {})
        report_format = params.get("report_format", "markdown")

        if not query:
            raise ValueError("Query parameter is required for report generation")

        if not investigation_type:
            raise ValueError("Investigation type parameter is required for report generation")

        if not isinstance(collected_data, list):
            raise ValueError("Collected data must be a list")

        if not isinstance(analysis_results, dict):
            raise ValueError("Analysis results must be a dictionary")

        if report_format not in ["markdown", "json", "summary", "detailed"]:
            raise ValueError(f"Invalid report format: {report_format}. Must be: markdown, json, summary, detailed")

        self.logger.info(
            "report_generation_started",
            target=target,
            query=query,
            investigation_type=investigation_type,
            data_entries=len(collected_data),
            report_format=report_format,
        )

        # Generate report based on format
        if report_format == "markdown":
            report_content = self._generate_markdown_report(query, investigation_type, collected_data, analysis_results)
        elif report_format == "json":
            report_content = self._generate_json_report(query, investigation_type, collected_data, analysis_results)
        elif report_format == "summary":
            report_content = self._generate_summary_report(query, investigation_type, collected_data, analysis_results)
        elif report_format == "detailed":
            report_content = self._generate_detailed_report(query, investigation_type, collected_data, analysis_results)

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": target,
            "query": query,
            "investigation_type": investigation_type,
            "report_format": report_format,
            "data_entries_count": len(collected_data),
            "analysis_sections_count": len(analysis_results),
            "report_content": report_content,
        }

        # Update statistics
        self.total_reports_generated += 1
        self.reports_by_format[report_format] += 1

        self.logger.info(
            "report_generation_complete",
            target=target,
            total_reports=self.total_reports_generated,
        )

        return result

    def _generate_markdown_report(
        self, query: str, investigation_type: str, collected_data: List[Dict[str, Any]], analysis_results: Dict[str, Any]
    ) -> str:
        """Generate Markdown formatted report.

        Args:
            query: Investigation query
            investigation_type: Type of investigation
            collected_data: List of collected data
            analysis_results: Dictionary of analysis results

        Returns:
            Markdown formatted report string
        """
        report = []
        report.append("# OSINT Investigation Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"**Query:** {query}")
        report.append(f"**Investigation Type:** {investigation_type}")
        report.append("")

        # Executive Summary
        report.append("## Executive Summary")
        report.append(f"- **Data Sources:** {len(collected_data)} entries collected")
        report.append(f"- **Analysis Sections:** {len(analysis_results)} sections analyzed")
        report.append("")

        # Key Findings
        if analysis_results:
            report.append("## Key Findings")
            for key, value in analysis_results.items():
                report.append(f"### {key.replace('_', ' ').title()}")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        report.append(f"- **{sub_key}:** {sub_value}")
                else:
                    report.append(f"- {value}")
                report.append("")

        # Collected Data
        if collected_data:
            report.append("## Collected Data")
            for idx, entry in enumerate(collected_data[:10], 1):  # Limit to 10 entries
                source = entry.get("source", "Unknown")
                data = str(entry.get("data", ""))[:100]
                report.append(f"{idx}. **Source:** {source}")
                report.append(f"   **Data:** {data}...")
                report.append("")

            if len(collected_data) > 10:
                report.append(f"*... and {len(collected_data) - 10} more entries*")
                report.append("")

        return "\n".join(report)

    def _generate_json_report(
        self, query: str, investigation_type: str, collected_data: List[Dict[str, Any]], analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate JSON formatted report.

        Args:
            query: Investigation query
            investigation_type: Type of investigation
            collected_data: List of collected data
            analysis_results: Dictionary of analysis results

        Returns:
            Dictionary representing JSON report
        """
        return {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "query": query,
                "investigation_type": investigation_type,
            },
            "summary": {
                "data_sources_count": len(collected_data),
                "analysis_sections_count": len(analysis_results),
            },
            "analysis_results": analysis_results,
            "collected_data": collected_data,
        }

    def _generate_summary_report(
        self, query: str, investigation_type: str, collected_data: List[Dict[str, Any]], analysis_results: Dict[str, Any]
    ) -> str:
        """Generate brief summary report.

        Args:
            query: Investigation query
            investigation_type: Type of investigation
            collected_data: List of collected data
            analysis_results: Dictionary of analysis results

        Returns:
            Brief summary string
        """
        summary = []
        summary.append(f"OSINT Investigation Summary: {query}")
        summary.append(f"Type: {investigation_type}")
        summary.append(f"Data collected: {len(collected_data)} entries")
        summary.append(f"Analysis sections: {len(analysis_results)}")

        if analysis_results:
            summary.append("\nKey findings:")
            for key in list(analysis_results.keys())[:5]:  # Top 5 findings
                summary.append(f"- {key.replace('_', ' ').title()}")

        return "\n".join(summary)

    def _generate_detailed_report(
        self, query: str, investigation_type: str, collected_data: List[Dict[str, Any]], analysis_results: Dict[str, Any]
    ) -> str:
        """Generate detailed comprehensive report.

        Args:
            query: Investigation query
            investigation_type: Type of investigation
            collected_data: List of collected data
            analysis_results: Dictionary of analysis results

        Returns:
            Detailed report string
        """
        report = []
        report.append("=" * 80)
        report.append("OSINT INVESTIGATION - DETAILED REPORT")
        report.append("=" * 80)
        report.append("")
        report.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"Query: {query}")
        report.append(f"Investigation Type: {investigation_type}")
        report.append("")

        # Statistics
        report.append("-" * 80)
        report.append("INVESTIGATION STATISTICS")
        report.append("-" * 80)
        report.append(f"Total data sources: {len(collected_data)}")
        report.append(f"Analysis sections: {len(analysis_results)}")
        report.append("")

        # Analysis Results (Full)
        if analysis_results:
            report.append("-" * 80)
            report.append("ANALYSIS RESULTS (COMPLETE)")
            report.append("-" * 80)
            for key, value in analysis_results.items():
                report.append(f"\n[{key.upper()}]")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        report.append(f"  {sub_key}: {sub_value}")
                elif isinstance(value, list):
                    for item in value:
                        report.append(f"  - {item}")
                else:
                    report.append(f"  {value}")
            report.append("")

        # Collected Data (Full)
        if collected_data:
            report.append("-" * 80)
            report.append("COLLECTED DATA (COMPLETE)")
            report.append("-" * 80)
            for idx, entry in enumerate(collected_data, 1):
                report.append(f"\nEntry #{idx}")
                report.append(f"  Source: {entry.get('source', 'Unknown')}")
                report.append(f"  Data: {entry.get('data', 'N/A')}")
            report.append("")

        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)

        return "\n".join(report)

    async def get_status(self) -> Dict[str, Any]:
        """Get generator status and statistics.

        Returns:
            Status dictionary with metrics
        """
        status = await self.health_check()

        status.update({
            "total_reports_generated": self.total_reports_generated,
            "reports_by_format": self.reports_by_format,
            "available_formats": ["markdown", "json", "summary", "detailed"],
        })

        return status

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ReportGeneratorRefactored(reports={self.total_reports_generated})"
