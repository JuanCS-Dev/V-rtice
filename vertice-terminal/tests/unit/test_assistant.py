"""
Tests for Maximus Assistant
============================

Test coverage:
- NaturalLanguageQueryParser: Pattern matching and query parsing
- CVECorrelator: CVE/ExploitDB correlation
- SuggestionEngine: Context-aware suggestions
- ReportGenerator: Multi-format report generation
- MaximusAssistant: Integration and workflow tests
"""

import pytest
from datetime import datetime
import json

from vertice.ai.assistant import (
    MaximusAssistant,
    NaturalLanguageQueryParser,
    CVECorrelator,
    SuggestionEngine,
    ReportGenerator
)


class TestNaturalLanguageQueryParser:
    """Test NL query parsing capabilities."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return NaturalLanguageQueryParser()

    def test_parse_web_servers_query(self, parser):
        """Test parsing 'show all web servers'."""
        result = parser.parse("show all web servers")

        assert result is not None
        assert result["type"] == "filter"
        assert result["service"] == ["http", "https"]

    def test_parse_http_servers_query(self, parser):
        """Test parsing 'show all http servers'."""
        result = parser.parse("show all http servers")

        assert result is not None
        assert result["type"] == "filter"
        assert result["service"] == ["http", "https"]

    def test_parse_https_servers_query(self, parser):
        """Test parsing 'show all https servers'."""
        result = parser.parse("show all https servers")

        assert result is not None
        assert result["type"] == "filter"
        assert result["service"] == ["http", "https"]

    def test_parse_ssh_servers_query(self, parser):
        """Test parsing 'show all ssh servers'."""
        result = parser.parse("show all ssh servers")

        assert result is not None
        assert result["type"] == "filter"
        assert result["service"] == "ssh"

    def test_parse_critical_vulns_query(self, parser):
        """Test parsing 'what hosts have critical vulns?'."""
        result = parser.parse("what hosts have critical vulns?")

        assert result is not None
        assert result["type"] == "filter"
        assert result["entity"] == "hosts"
        assert result["has_vulns"] is True
        assert result["severity"] == "critical"

    def test_parse_high_vulns_query(self, parser):
        """Test parsing 'what hosts have high vulns?'."""
        result = parser.parse("what hosts have high vulns?")

        assert result is not None
        assert result["severity"] == "high"

    def test_parse_medium_vulns_query(self, parser):
        """Test parsing 'what hosts have medium vulns?'."""
        result = parser.parse("what hosts have medium vulns?")

        assert result is not None
        assert result["severity"] == "medium"

    def test_parse_low_vulns_query(self, parser):
        """Test parsing 'what hosts have low vulns?'."""
        result = parser.parse("what hosts have low vulns?")

        assert result is not None
        assert result["severity"] == "low"

    def test_parse_weak_ssh_query(self, parser):
        """Test parsing 'find ssh with weak auth'."""
        result = parser.parse("find ssh with weak auth")

        assert result is not None
        assert result["type"] == "filter"
        assert result["service"] == "ssh"
        assert result["weak_auth"] is True

    def test_parse_host_count_query(self, parser):
        """Test parsing 'how many hosts are up?'."""
        result = parser.parse("how many hosts are up?")

        assert result is not None
        assert result["type"] == "aggregate"
        assert result["field"] == "hosts"
        assert result["function"] == "count"

    def test_parse_list_vulns_query(self, parser):
        """Test parsing 'list all vulnerabilities'."""
        result = parser.parse("list all vulnerabilities")

        assert result is not None
        assert result["type"] == "filter"
        assert result["entity"] == "vulnerabilities"

    def test_parse_port_filter_query(self, parser):
        """Test parsing 'show hosts with port 22 open'."""
        result = parser.parse("show hosts with port 22 open")

        assert result is not None
        assert result["type"] == "filter"
        assert result["entity"] == "hosts"
        assert result["port"] == 22
        assert result["port_state"] == "open"

    def test_parse_port_filter_with_different_port(self, parser):
        """Test parsing port filter with different port number."""
        result = parser.parse("show hosts with port 443 open")

        assert result is not None
        assert result["port"] == 443

    def test_parse_unknown_query(self, parser):
        """Test parsing an unknown/unsupported query."""
        result = parser.parse("this is not a valid query")

        assert result is None

    def test_parse_case_insensitive(self, parser):
        """Test that parsing is case-insensitive."""
        result1 = parser.parse("SHOW ALL WEB SERVERS")
        result2 = parser.parse("Show All Web Servers")
        result3 = parser.parse("show all web servers")

        assert result1 == result2 == result3

    def test_parse_with_extra_whitespace(self, parser):
        """Test parsing with extra whitespace."""
        result = parser.parse("  show all web servers  ")

        assert result is not None
        assert result["type"] == "filter"


class TestCVECorrelator:
    """Test CVE/ExploitDB correlation."""

    @pytest.fixture
    def correlator(self):
        """Create correlator instance."""
        return CVECorrelator()

    def test_find_cves_for_apache_2_4(self, correlator):
        """Test finding CVEs for Apache 2.4.x."""
        cves = correlator.find_cves("Apache", "2.4.41")

        assert len(cves) > 0
        assert cves[0]["cve_id"] == "CVE-2021-44228"
        assert cves[0]["severity"] == "critical"
        assert cves[0]["cvss"] == 10.0

    def test_find_cves_with_exploits(self, correlator):
        """Test that CVEs include exploit information."""
        cves = correlator.find_cves("Apache", "2.4.50")

        assert len(cves) > 0
        assert "exploits" in cves[0]
        assert len(cves[0]["exploits"]) > 0

    def test_find_cves_exploitdb_source(self, correlator):
        """Test ExploitDB exploit information."""
        cves = correlator.find_cves("Apache", "2.4.41")

        exploits = cves[0]["exploits"]
        exploitdb = [e for e in exploits if e["source"] == "ExploitDB"]

        assert len(exploitdb) > 0
        assert "id" in exploitdb[0]
        assert "title" in exploitdb[0]
        assert "url" in exploitdb[0]

    def test_find_cves_metasploit_source(self, correlator):
        """Test Metasploit exploit information."""
        cves = correlator.find_cves("Apache", "2.4.41")

        exploits = cves[0]["exploits"]
        metasploit = [e for e in exploits if e["source"] == "Metasploit"]

        assert len(metasploit) > 0
        assert "module" in metasploit[0]
        assert "rank" in metasploit[0]

    def test_find_cves_no_results(self, correlator):
        """Test finding CVEs for unknown service."""
        cves = correlator.find_cves("UnknownService", "1.0.0")

        assert len(cves) == 0

    def test_find_cves_apache_case_insensitive(self, correlator):
        """Test that service name matching is case-insensitive."""
        cves1 = correlator.find_cves("Apache", "2.4.41")
        cves2 = correlator.find_cves("apache", "2.4.41")
        cves3 = correlator.find_cves("APACHE", "2.4.41")

        assert len(cves1) == len(cves2) == len(cves3)


class TestSuggestionEngine:
    """Test context-aware suggestion generation."""

    @pytest.fixture
    def engine(self):
        """Create suggestion engine instance."""
        return SuggestionEngine()

    def test_generate_empty_context(self, engine):
        """Test generating suggestions with empty context."""
        suggestions = engine.generate({})

        assert isinstance(suggestions, list)
        # Empty context should result in no suggestions
        assert len(suggestions) == 0

    def test_suggest_deeper_scanning(self, engine):
        """Test suggestion for deeper scanning when coverage is low."""
        context = {
            "total_hosts": 100,
            "scanned_hosts": 10,  # Only 10% scanned
            "total_vulns": 0,
            "critical_vulns": 0
        }

        suggestions = engine.generate(context)

        assert len(suggestions) > 0
        # Should suggest scanning more hosts
        scan_suggestions = [s for s in suggestions if "autopilot pentest" in s["action"]]
        assert len(scan_suggestions) > 0
        assert scan_suggestions[0]["priority"] == "medium"

    def test_suggest_critical_vuln_scanning(self, engine):
        """Test suggestion when critical vulnerabilities are found."""
        context = {
            "total_hosts": 10,
            "scanned_hosts": 10,
            "total_vulns": 5,
            "critical_vulns": 3
        }

        suggestions = engine.generate(context)

        assert len(suggestions) > 0
        # Should suggest scanning for critical vulns
        vuln_suggestions = [s for s in suggestions if "nuclei" in s["action"]]
        assert len(vuln_suggestions) > 0
        assert vuln_suggestions[0]["priority"] == "high"

    def test_suggest_siem_integration(self, engine):
        """Test suggestion for SIEM integration when many findings."""
        context = {
            "total_hosts": 10,
            "scanned_hosts": 10,
            "total_vulns": 50,  # Many vulnerabilities
            "critical_vulns": 0
        }

        suggestions = engine.generate(context)

        assert len(suggestions) > 0
        # Should suggest SIEM integration
        siem_suggestions = [s for s in suggestions if "siem" in s["action"]]
        assert len(siem_suggestions) > 0
        assert siem_suggestions[0]["priority"] == "low"

    def test_suggestion_structure(self, engine):
        """Test that suggestions have required fields."""
        context = {
            "total_hosts": 100,
            "scanned_hosts": 10,
            "total_vulns": 15,
            "critical_vulns": 5
        }

        suggestions = engine.generate(context)

        for suggestion in suggestions:
            assert "action" in suggestion
            assert "reason" in suggestion
            assert "priority" in suggestion
            assert "estimated_time" in suggestion

    def test_multiple_suggestions(self, engine):
        """Test generating multiple suggestions."""
        context = {
            "total_hosts": 100,
            "scanned_hosts": 30,  # Triggers scan suggestion
            "total_vulns": 20,  # Triggers SIEM suggestion
            "critical_vulns": 5  # Triggers vuln scan suggestion
        }

        suggestions = engine.generate(context)

        # Should generate multiple suggestions
        assert len(suggestions) >= 2


class TestReportGenerator:
    """Test multi-format report generation."""

    @pytest.fixture
    def generator(self):
        """Create report generator instance."""
        return ReportGenerator()

    @pytest.fixture
    def sample_data(self):
        """Sample workspace data for testing."""
        return {
            "hosts": [
                {"ip": "10.10.1.5", "status": "up"},
                {"ip": "10.10.1.6", "status": "up"}
            ],
            "vulnerabilities": [
                {"cve": "CVE-2021-44228", "severity": "critical"},
                {"cve": "CVE-2021-3156", "severity": "high"},
                {"cve": "CVE-2020-1472", "severity": "critical"}
            ],
            "services": [
                {"port": 80, "service": "http"},
                {"port": 443, "service": "https"},
                {"port": 22, "service": "ssh"}
            ]
        }

    def test_generate_markdown_report(self, generator, sample_data):
        """Test generating Markdown report."""
        report = generator.generate(sample_data, format="markdown")

        assert isinstance(report, str)
        assert "# Penetration Test Report" in report
        assert "## Executive Summary" in report
        assert "Hosts scanned" in report
        assert "Vulnerabilities found" in report

    def test_generate_markdown_with_all_sections(self, generator, sample_data):
        """Test Markdown report includes all sections."""
        report = generator.generate(sample_data, format="markdown")

        assert "## Executive Summary" in report
        assert "## Findings by Severity" in report
        assert "## Recommendations" in report

    def test_generate_markdown_with_specific_sections(self, generator, sample_data):
        """Test Markdown report with specific sections only."""
        report = generator.generate(
            sample_data,
            format="markdown",
            include_sections=["summary"]
        )

        assert "## Executive Summary" in report
        # Should not include other sections
        assert "## Findings by Severity" not in report

    def test_generate_markdown_severity_counts(self, generator, sample_data):
        """Test Markdown report includes severity counts."""
        report = generator.generate(sample_data, format="markdown")

        assert "critical" in report.lower()
        assert "high" in report.lower()
        assert "medium" in report.lower()
        assert "low" in report.lower()

    def test_generate_html_report(self, generator, sample_data):
        """Test generating HTML report."""
        report = generator.generate(sample_data, format="html")

        assert isinstance(report, str)
        assert "<!DOCTYPE html>" in report
        assert "<html>" in report
        assert "<body>" in report
        assert "Penetration Test Report" in report

    def test_generate_html_with_css(self, generator, sample_data):
        """Test HTML report includes CSS styling."""
        report = generator.generate(sample_data, format="html")

        assert "<style>" in report
        assert "font-family" in report

    def test_generate_json_report(self, generator, sample_data):
        """Test generating JSON report."""
        report = generator.generate(sample_data, format="json")

        assert isinstance(report, str)
        # Should be valid JSON
        data = json.loads(report)
        assert "generated_at" in data
        assert "hosts" in data
        assert "vulnerabilities" in data
        assert "services" in data

    def test_generate_json_structure(self, generator, sample_data):
        """Test JSON report structure matches input data."""
        report = generator.generate(sample_data, format="json")
        data = json.loads(report)

        assert len(data["hosts"]) == len(sample_data["hosts"])
        assert len(data["vulnerabilities"]) == len(sample_data["vulnerabilities"])
        assert len(data["services"]) == len(sample_data["services"])

    def test_generate_unsupported_format(self, generator, sample_data):
        """Test error handling for unsupported format."""
        with pytest.raises(ValueError, match="Unsupported format"):
            generator.generate(sample_data, format="pdf")

    def test_generate_markdown_timestamp(self, generator, sample_data):
        """Test Markdown report includes timestamp."""
        report = generator.generate(sample_data, format="markdown")

        assert "Generated" in report
        # Should include current year
        current_year = datetime.now().year
        assert str(current_year) in report

    def test_generate_json_timestamp_format(self, generator, sample_data):
        """Test JSON report timestamp is ISO format."""
        report = generator.generate(sample_data, format="json")
        data = json.loads(report)

        # Should be valid ISO timestamp
        timestamp = data["generated_at"]
        assert "T" in timestamp
        datetime.fromisoformat(timestamp)  # Should not raise


class TestMaximusAssistant:
    """Test MaximusAssistant integration."""

    @pytest.fixture
    def assistant(self):
        """Create assistant instance."""
        return MaximusAssistant(workspace_manager=None)

    def test_assistant_initialization(self, assistant):
        """Test assistant initializes all components."""
        assert assistant.query_parser is not None
        assert assistant.cve_correlator is not None
        assert assistant.suggestion_engine is not None
        assert assistant.report_generator is not None

    def test_query_nl_web_servers(self, assistant):
        """Test NL query for web servers."""
        result = assistant.query_nl("show all web servers")

        assert result["question"] == "show all web servers"
        assert result["parsed_query"]["type"] == "filter"
        assert result["parsed_query"]["service"] == ["http", "https"]
        assert "results" in result
        assert "count" in result

    def test_query_nl_critical_vulns(self, assistant):
        """Test NL query for critical vulnerabilities."""
        result = assistant.query_nl("what hosts have critical vulns?")

        assert result["question"] == "what hosts have critical vulns?"
        assert result["parsed_query"]["severity"] == "critical"
        assert isinstance(result["results"], list)

    def test_query_nl_unparseable_question(self, assistant):
        """Test NL query with unparseable question."""
        result = assistant.query_nl("this is not a valid question")

        assert "error" in result
        assert result["error"] == "Could not understand question"
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    def test_correlate_vulns_apache(self, assistant):
        """Test CVE correlation for Apache."""
        vulns = assistant.correlate_vulns("Apache", "2.4.41")

        assert len(vulns) > 0
        assert vulns[0]["cve_id"] == "CVE-2021-44228"
        assert "exploits" in vulns[0]

    def test_correlate_vulns_unknown_service(self, assistant):
        """Test CVE correlation for unknown service."""
        vulns = assistant.correlate_vulns("UnknownService", "1.0.0")

        assert len(vulns) == 0

    def test_suggest_next_steps_no_context(self, assistant):
        """Test suggestions with no context."""
        suggestions = assistant.suggest_next_steps()

        assert isinstance(suggestions, list)

    def test_suggest_next_steps_with_context(self, assistant):
        """Test suggestions with specific context."""
        context = {
            "total_hosts": 100,
            "scanned_hosts": 10,
            "total_vulns": 5,
            "critical_vulns": 2
        }

        suggestions = assistant.suggest_next_steps(context)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_generate_report_markdown(self, assistant):
        """Test report generation in Markdown format."""
        report = assistant.generate_report(format="markdown")

        assert isinstance(report, str)
        assert "# Penetration Test Report" in report

    def test_generate_report_html(self, assistant):
        """Test report generation in HTML format."""
        report = assistant.generate_report(format="html")

        assert isinstance(report, str)
        assert "<!DOCTYPE html>" in report

    def test_generate_report_json(self, assistant):
        """Test report generation in JSON format."""
        report = assistant.generate_report(format="json")

        assert isinstance(report, str)
        data = json.loads(report)
        assert "generated_at" in data

    def test_generate_report_with_sections(self, assistant):
        """Test report generation with specific sections."""
        report = assistant.generate_report(
            format="markdown",
            include_sections=["summary", "findings"]
        )

        assert "## Executive Summary" in report
        assert "## Findings by Severity" in report
